import sys
sys.path.append("../../api/gen/python/v1alpha")

import grpc
import numpy as np
from env_pb2 import *
from env_pb2_grpc import EnvironmentAPIStub as env_grpc


class Env(object):
    def __init__(self, address):
        self.channel = grpc.insecure_channel(address)
        self.sphere = env_grpc(self.channel)

    def close(self):
        self.channel.close()

    def make(self, name):
        print("making env ", name)
        req = CreateEnvRequest(model_name=name)
        resp = self.sphere.CreateEnv(req)
        print(resp.environment)
        self.name = resp.environment.model_name
        self.id = resp.environment.id
        self.action_space = resp.environment.action_space
        self.observation_space = resp.environment.observation_space
        self.num_actions = resp.environment.num_actions
        self.max_episode_steps = resp.environment.max_episode_steps
        return resp.environment

    def step(self, action):
        req = StepEnvRequest(id=self.id,action=action)
        resp = self.sphere.StepEnv(req)
        return self._decode_tensor(resp.observation), resp.reward, resp.done, resp.info
    
    def reset(self):
        req = ResetEnvRequest(id=self.id)
        resp = self.sphere.ResetEnv(req)
        return self._decode_tensor(resp.observation)
    
    def sample(self):
        req = SampleActionRequest(id=self.id)
        resp = self.sphere.SampleAction(req)
        return resp.value
    
    def results(self):
        req = ResultsRequest(id=self.id)
        resp = self.sphere.Results(req)
        return resp

    def _decode_tensor(self, tensor):
        if not tensor.data:
            return
        return np.asarray(tensor.data).reshape(tensor.shape)

