from concurrent import futures
from time import sleep
import gym
import grpc
import json
import uuid
import os

import sys
sys.path.append("../../../api/gen/python/v1alpha")

from env_pb2 import *
from env_pb2_grpc import EnvironmentAPIServicer, add_EnvironmentAPIServicer_to_server as register

results_base_dir = "./results" 

def encode_observation(observation):
    return Observation(data=observation.ravel(), shape=observation.shape)

def get_results_dir(env_id):
    return os.path.join(results_base_dir, env_id)

def get_results(env_id):
    dir = get_results_dir(env_id)
    results = ResultsResponse()
    videos = {}
    for (root, _, filenames) in os.walk(dir):
        for i, f in enumerate(filenames):
            if "stats.json" in f:
                episodes = {}
                stats_file = os.path.join(root, f)
                with open(stats_file) as json_file:
                    data = json.load(json_file)
                    timestamps = data["timestamps"]
                    for i, t in enumerate(timestamps):
                        er = EpisodeResult(episode_id=i, timestamp=t)
                        episodes[i] = er
                    ep_lengths = data["episode_lengths"]
                    for i, l in enumerate(ep_lengths):
                        episodes[i].episode_length = l
                    ep_rewards = data["episode_rewards"]
                    for i, r in enumerate(ep_rewards):
                        episodes[i].reward = r
                results.episode_results = episodes
            if "meta.json" in f:
                video_file = os.path.join(root, f)
                with open(video_file) as json_file:
                    data = json.load(json_file)
                    videos[data.episode_id] = Video(episode_id=data.episode_id, content_type=data.content_type)
    return results

class EnvironmentServer(EnvironmentAPIServicer):
    def __init__(self):
        self.envs = {}

    def Info(self, request, context):
        return InfoResponse(server_name="gym")

    def CreateEnv(self, request, context):
        id = uuid.uuid4()
        self.envs[id] = gym.make(request.model_name)
        return CreateEnvResponse(observation_shape=self.envs[id].observation_space.shape,
                    num_actions=self.envs[id].action_space.n,
                    max_episode_steps=self.envs[id]._max_episode_steps)

    def ListEnvs(self, request, context):
        envs = []
        for id in self.envs:
            env = self.envs[id]
            envs.append(Environment(id=id,model_name=env.env.spec.id))
        return ListEnvsResponse(envs=envs)

    def ListModels(self, request, context):
        resp = []
        for k in gym.envs.registry.env_specs:
            resp.append(Model(name=k))
        return ListModelsResponse(models=resp)

    def GetEnv(self, request, context):
        env = self.envs[request.id]
        return Environment(id=id,model_name=env.env.spec.id)

    def ResetEnv(self, request, context):
        env = self.envs[request.id]
        observation = env.reset()
        return ResetEnvResponse(observation=Observation(data=observation.ravel(), shape=observation.shape))

    def StepEnv(self, request, context):
        env = self.envs[request.id]
        observation, reward, done, _ = env.step(action.value)
        observation = encode_observation(observation)
        next_episode = encode_observation(env.reset()) if done else None
        return StepEnvResponse(transition=Transition(observation=observation,
                          reward=reward,
                          next_episode=next_episode))

    def StartRecordEnv(self, request, context):
        env = self.envs[request.id]
        switcher={
            0: None,
            1: lambda episode_id: False,
            2: lambda episode_id: True,
            3: lambda episode_id: episode_id%10==0,
            4: lambda episode_id: episode_id%100==0,
        }
        val = StartRecordRequest.VideoSamplingRate.Value(request.video_sampling_rate)
        rate = switcher.get(val,"Invalid sample rate")
        results_dir = get_results_dir(request.id)
        self.envs[request.id] = gym.wrappers.Monitor(env, results_dir, force=request.force, resume=request.resume, video_callable=rate, uid=request.id) 

    def StopRecordEnv(self, request, context):
        env = self.envs[request.id]
        env.close()

    # relevent https://stackoverflow.com/questions/40195740/how-to-run-openai-gym-render-over-a-server
    def Results(self, request, context):
        return get_results(request.env_id)

    def GetVideo(self, request, context):
        chunk_size=1024
        dir = get_results_dir(request.env_id)
        video_file = ""
        for (root, _, filenames) in os.walk(dir):
            for f in filenames:
                filesuffix = "video" + str(request.episode_id).zfill(6) + ".mp4"
                if filesuffix in f:
                    video_file = os.path.join(root, f)

        if video_file == "":
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Video not found!')
            return
        with open(video_file) as file_object:
            while True:
                data = file_object.read(chunk_size)
                if not data:
                    break
                yield data

    def DeleteVideo(self, request, context):
        dir = get_results_dir(request.env_id)
        video_file = ""
        for (root, _, filenames) in os.walk(dir):
            for f in filenames:
                filesuffix = "video" + str(request.episode_id).zfill(6) + ".mp4"
                if filesuffix in f:
                    video_file = os.path.join(root, f)
                    os.remove(video_file)

    def DeleteEnv(self, request, context):
        env = self.envs[request.id]
        env.close()
        res_dir = get_results_dir(request.id)
        os.rmdir(res_dir)
        del self.envs[request.id]


def serve(address='[::]:50051'):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    register(EnvironmentServer(), server)
    server.add_insecure_port(address)
    print('starting server at address ' + address)
    server.start()
    try:
        while True:
            sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()