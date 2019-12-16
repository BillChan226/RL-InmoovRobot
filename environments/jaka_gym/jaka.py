import os
import numpy as np
from matplotlib import pyplot as plt
import pybullet as p
import pybullet_data

from ipdb import set_trace as tt
from util.color_print import printGreen, printBlue, printRed, printYellow

URDF_PATH = "/urdf_robot/jaka_urdf/jaka_local.urdf"
GRAVITY = -9.8

class Jaka:
    def __init__(self, urdf_path, debug_mode=False):
        self.urdf_path = urdf_path
        self.debug_mode = debug_mode
        self.jaka_id = -1
        self.num_joints = -1
        self.robot_base_pos = [0, 0, 0]
        self.joint_lower_limits, self.joint_upper_limits, self.jointMaxForce, self.jointMaxVelocity = None, None, None, None
        self.joint_name = {}
        self.debug_joints = []
        self.joints_key = []
        if self.debug_mode:
            client_id = p.connect(p.SHARED_MEMORY)
            if client_id < 0:
                p.connect(p.GUI)
            # The camera information for debug (GUI graphical interface)
            p.resetDebugVisualizerCamera(2., 180, -41, [0.52, -0.2, -0.33])
            debug_joints = []
            self.debug_joints = debug_joints
        else:
            client_id = p.connect(p.SHARED_MEMORY)
            if client_id < 0:
                p.connect(p.DIRECT)
        self.reset()

    def reset(self):
        self.jaka_id = p.loadURDF(self.urdf_path)
        self.num_joints = p.getNumJoints(self.jaka_id)
        self.get_joint_info()
        for jointIndex in self.joints_key:
            p.resetJointState(self.jaka_id, jointIndex, 0.)

    def get_joint_info(self):
        self.joints_key = []
        self.joint_lower_limits, self.joint_upper_limits, self.jointMaxForce, self.jointMaxVelocity = [], [], [], []
        for i in range(self.num_joints):
            info = p.getJointInfo(self.jaka_id, i)
            if info[2] == p.JOINT_REVOLUTE:
                self.joint_name[i] = info[1]
                self.joint_lower_limits.append(info[8])
                self.joint_upper_limits.append(info[9])
                self.jointMaxForce.append(info[10])
                self.jointMaxVelocity.append(info[11])
                self.joints_key.append(i)
        if self.debug_mode:
            keys = list(self.joint_name.keys())
            keys.sort()
            for i, key in enumerate(keys):
                self.debug_joints.append(p.addUserDebugParameter(self.joint_name[key].decode(), self.joint_lower_limits[i],
                                                                 self.joint_upper_limits[i], 0.))

    def debugger_step(self):
        assert self.debug_mode, "Error: the debugger_step is only allowed in debug mode"

        current_joints = []
        for j in self.debug_joints:
            tmp_joint_control = p.readUserDebugParameter(j)
            current_joints.append(tmp_joint_control)
        for joint_state, joint_key in zip(current_joints, self.joints_key):
            p.resetJointState(self.jaka_id, joint_key, targetValue=joint_state)
        p.stepSimulation()

if __name__ == '__main__':
    jaka = Jaka(URDF_PATH, True)
    _urdf_path = pybullet_data.getDataPath()
    planeId = p.loadURDF(os.path.join(_urdf_path, "plane.urdf"))
    while True:
        jaka.debugger_step()