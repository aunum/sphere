from concurrent import futures
from time import sleep
import gym
import grpc
import uuid

from . import config
from ../../api/gen/python/env_pb2 import *
from ../../api/gen/python/env_pb2_grpc import EnvironmentAPIServicer, add_EnvironmentAPIServicer_to_server as register


def encode_observation(observation):
    return Observation(data=observation.ravel(), shape=observation.shape)


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

    # relevent https://stackoverflow.com/questions/40195740/how-to-run-openai-gym-render-over-a-server
    def Results(self, request, context):
        """Results from the environment.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Videos(self, request, context):
        """Stream result videos.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteEnv(self, request, context):
        """Delete environment
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Make(self, name, _):
        name = name.value
        if not hasattr(self, 'env') or self.env.spec.id != name:
            self.env = gym.make(name)
        return Info(observation_shape=self.env.observation_space.shape,
                    num_actions=self.env.action_space.n,
                    max_episode_steps=self.env._max_episode_steps)

    def Reset(self, empty, _):
        return encode_observation(self.env.reset())

    def Step(self, action, _):
        observation, reward, done, _ = self.env.step(action.value)
        observation = encode_observation(observation)
        next_episode = encode_observation(self.env.reset()) if done else None
        return Transition(observation=observation,
                          reward=reward,
                          next_episode=next_episode)


def serve(address=config.address):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    register(Env(), server)
    server.add_insecure_port(address)
    server.start()
    try:
        while True:
            sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)