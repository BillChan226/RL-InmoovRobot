import os
from stable_baselines import PPO2
import pybullet as p
import numpy as np
from gym import spaces
import gym
from ipdb import set_trace as tt
from environments.inmoov import inmoov
GRAVITY = -9.8
URDF_PATH = "/home/tete/work/SJTU/inmoov/robotics-rl-srl/urdf_robot/"

class InmoovGymEnv(gym.Env):
    def __init__(self, urdf_path=URDF_PATH, multi_view=False, seed=0, debug_mode=False):
        self.seed(seed)
        self.urdf_path = URDF_PATH

        self._observation = None
        self.debug_mode = debug_mode
        self._inmoov = None
        self.reset()

    def reset(self):
        self.terminated = False
        self.n_contacts = 0
        self.n_steps_outside = 0
        p.resetSimulation()
        p.setPhysicsEngineParameter(numSolverIterations=150)
        p.loadURDF(os.path.join("/home/tete/work/SJTU/inmoov/robotics-rl-srl/pybullet_data", "plane.urdf"), [0, 0, -1])
        p.setGravity(0, 0, -10)

        self._inmoov = inmoov.Inmoov(urdf_path=self.urdf_path, positional_control=True)
        # p.resetSimulation()
        # p.setPhysicsEngineParameter(numSolverIterations=150)
        # p.setGravity(0., 0., GRAVITY)


    def _reward(self):
        # TODO
        return

    def _termination(self):
        # TODO
        return

    def step(self, action):
        self._inmoov.apply_action_pos(action)
        # tt()
        # self._observation = self.render(mode='rgb')
        # reward = self._reward()
        # done = self._termination()
        # self.obs[:], rewards, self.dones, infos
        # return np.array(self._observation), reward, done, {}

    def render(self, mode='rgb'):
        # TODO
        return np.array([])

    def close(self):
        return