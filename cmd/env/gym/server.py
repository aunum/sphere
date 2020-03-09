from concurrent import futures
from time import sleep
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.struct_pb2 import Struct
from google.rpc import code_pb2, status_pb2, error_details_pb2
from grpc_status import rpc_status
import gym
import gym_BitFlipper
from gym import wrappers
import grpc
import math
import shutil
import traceback
import json
import logging
import uuid
import sys
import os
import numpy as np

import sys
sys.path.append("../../../api/gen/python/v1alpha")

from env_pb2 import *
from env_pb2_grpc import EnvironmentAPIServicer, add_EnvironmentAPIServicer_to_server as register

results_base_dir = "./results" 

def get_results_dir(env_id):
    return os.path.join(results_base_dir, env_id)

def get_results(env_id):
    dir = get_results_dir(env_id)
    videos = {}
    episodes = {}
    for (root, _, filenames) in os.walk(dir):
        for i, f in enumerate(filenames):
            print(f)
            if "stats.json" in f:
                stats_file = os.path.join(root, f)
                with open(stats_file) as json_file:
                    data = json.load(json_file)
                    timestamps = data["timestamps"]
                    for i, t in enumerate(timestamps):
                        nanos, seconds = math.modf(t)
                        ts = Timestamp(seconds=int(seconds), nanos=int(nanos))
                        er = EpisodeResult(episode_id=i, timestamp=ts)
                        episodes[i] = er
                    ep_lengths = data["episode_lengths"]
                    for i, l in enumerate(ep_lengths):
                        episodes[i].episode_length = l
                    ep_rewards = data["episode_rewards"]
                    for i, r in enumerate(ep_rewards):
                        episodes[i].reward = r
            if "meta.json" in f:
                video_file = os.path.join(root, f)
                with open(video_file) as json_file:
                    data = json.load(json_file)
                    videos[data["episode_id"]] = Video(episode_id=data["episode_id"], content_type=data["content_type"])
    return ResultsResponse(videos=videos,episode_results=episodes)

def encode_tensor(tensor):
    return Tensor(data=tensor.ravel(), shape=tensor.shape)

def encode_image(tensor):
    return Image(data=tensor.ravel(), shape=tensor.shape)

class EnvironmentServer(EnvironmentAPIServicer):
    def __init__(self, logger):
        self.envs = {}
        self.record = False

        self.logger = logger

    def Info(self, request, context):
        return InfoResponse(server_name="gym")

    def _get_env(self, env_id):
        env = self.envs[env_id]
        observation_space = self._get_space_info(env.observation_space)
        action_space = self._get_space_info(env.action_space)
        return Environment(id=env_id,
                    model_name=env.spec.id,
                    observation_space=observation_space,
                    action_space=action_space,
                    num_actions=self.envs[env_id].action_space.n,
                    max_episode_steps=self.envs[env_id].spec.max_episode_steps)

    def _get_space_info(self, space):
        name = space.__class__.__name__
        info = Space(name=name)
        if name == 'Discrete':
            info.discrete.CopyFrom(DiscreteSpace(n=space.n))
        elif name == 'Box':
            info.box.CopyFrom(BoxSpace(shape=space.shape))
            info.box.low.extend([(x if x != -np.inf else -1e100) for x in np.array(space.low ).flatten()])
            info.box.high.extend([(x if x != +np.inf else +1e100) for x in np.array(space.high).flatten()])
        elif name == 'MultiBinary':
            info.multi_binary.CopyFrom(MultiBinarySpace(n=space.n))
        return info

    def CreateEnv(self, request, context):
        self.logger.info("creating env")
        id = str(uuid.uuid4())
        try:
            self.envs[id] = gym.make(request.model_name)
        except IndexError:
            traceback.print_exc()
        env = self._get_env(id)
        print(env)
        return CreateEnvResponse(environment=env)

    def ListEnvs(self, request, context):
        envs = []
        for id in self.envs:
            envs.append(self._get_env(id))
        return ListEnvsResponse(envs=envs)

    def ListModels(self, request, context):
        resp = []
        for k in gym.envs.registry.env_specs:
            resp.append(Model(name=k))
        return ListModelsResponse(models=resp)

    def GetEnv(self, request, context):
        return GetEnvResponse(environment=self._get_env(request.id))

    def ResetEnv(self, request, context):
        self.logger.info("resetting env")
        env = self.envs[request.id]
        observation = env.reset()
        if not isinstance(observation, np.ndarray):
            self.logger.debug("reshaping observation to tensor")
            observation = np.array(observation)
        goal = Tensor()
        if hasattr(env, "goal"):
            goal = encode_tensor(env.goal)
        return ResetEnvResponse(observation=encode_tensor(observation), goal=goal)

    def StepEnv(self, request, context):
        self.logger.info("stepping")
        env = self.envs[request.id]
        env.render()
        observation, reward, done, info = env.step(request.action)
        if not isinstance(observation, np.ndarray):
            self.logger.debug("reshaping observation to tensor")
            observation = np.array(observation)
        self.logger.info("observation")
        self.logger.info(observation)
        observation = encode_tensor(observation)
        goal = Tensor()
        if hasattr(env, "goal"):
            self.logger.info("goal")
            self.logger.info(goal)
            goal = encode_tensor(env.goal)
        s = Struct()
        s.update(info)
        return StepEnvResponse(observation=observation,
                          reward=reward,
                          done=done,
                          goal=goal,
                          info=s)

    def SampleAction(self, request, context):
        env = self.envs[request.id]
        return SampleActionResponse(value=env.action_space.sample())

    def RenderEnv(self, request, context):
        env = self.envs[request.id]
        self.logger.info("rendering frame")
        frame = env.render(mode='rgb_array')
        self.logger.info("returning frame")
        return RenderEnvResponse(image=encode_tensor(frame))

    def StartRecordEnv(self, request, context):
        env = self.envs[request.id]
        switcher={
            0: None,
            1: lambda episode_id: False,
            2: lambda episode_id: True,
            3: lambda episode_id: episode_id%10==0,
            4: lambda episode_id: episode_id%100==0,
        }
        rate = switcher.get(request.video_sampling_rate, "Invalid sample rate")
        results_dir = get_results_dir(request.id)
        self.envs[request.id] = wrappers.Monitor(env, results_dir, force=request.force, resume=request.resume, video_callable=rate, uid=request.id, write_upon_reset=True) 
        self.record = True
        return StartRecordEnvResponse(message="recording environment")

    def StopRecordEnv(self, request, context):
        env = self.envs[request.id]
        env.close()
        self.record = False
        return StopRecordEnvResponse(message="stopped recording environment")

    # relevent https://stackoverflow.com/questions/40195740/how-to-run-openai-gym-render-over-a-server
    def Results(self, request, context):
        return get_results(request.id)

    def GetVideo(self, request, context):
        self.logger.info("getting video")
        chunk_size=1024
        dir = get_results_dir(request.id)
        video_file = ""
        for (root, _, filenames) in os.walk(dir):
            for f in filenames:
                filesuffix = "video" + str(request.episode_id).zfill(6) + ".mp4"
                if filesuffix in f:
                    video_file = os.path.join(root, f)
        # print(video_file)
        if video_file == "":
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Video not found!')
            return
        with open(video_file, "rb") as file_object:
            while True:
                data = file_object.read(chunk_size)
                if not data:
                    break
                yield GetVideoResponse(chunk=data)

    def DeleteVideo(self, request, context):
        dir = get_results_dir(request.id)
        video_file = ""
        for (root, _, filenames) in os.walk(dir):
            for f in filenames:
                filesuffix = "video" + str(request.episode_id).zfill(6) + ".mp4"
                if filesuffix in f:
                    video_file = os.path.join(root, f)
                    os.remove(video_file)
        return DeleteVideoResponse(message="deleted video")

    def DeleteEnv(self, request, context):
        env = self.envs[request.id]
        env.close()
        res_dir = get_results_dir(request.id)
        shutil.rmtree(res_dir, ignore_errors=True)
        del self.envs[request.id]
        return DeleteEnvResponse(message="deleted env")

def serve(address='[::]:50051'):
    logger = logging.getLogger('sphere')
    str_hdlr = logging.StreamHandler(sys.stdout)
    file_hdlr = logging.FileHandler('/var/tmp/sphere.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_hdlr.setFormatter(formatter)
    str_hdlr.setFormatter(formatter)
    logger.addHandler(file_hdlr)
    logger.addHandler(str_hdlr)
    logger.setLevel(logging.DEBUG)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    register(EnvironmentServer(logger), server)
    server.add_insecure_port(address)
    logger.info('starting server at address ' + address)
    server.start()
    try:
        while True:
            sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()