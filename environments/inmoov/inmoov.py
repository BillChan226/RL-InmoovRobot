import os
from collections import Counter

import numpy as np
from matplotlib import pyplot as plt
import pybullet as p
from ipdb import set_trace as tt

from mpl_toolkits.mplot3d import Axes3D

from util.color_print import printGreen, printBlue, printRed, printYellow
from environments.inmoov.joints_registry import joint_registry, control_joint
URDF_PATH = "/home/tete/work/SJTU/kuka_play/robotics-rl-srl/urdf_robot/"
GRAVITY = -9.8
RENDER_WIDTH, RENDER_HEIGHT = 512, 512
CONTROL_JOINT = list(control_joint.keys())
CONTROL_JOINT.sort()


class Inmoov:
    def __init__(self, urdf_path=URDF_PATH, debug_mode=False):
        self.urdf_path = urdf_path
        self._renders = True
        self.debug_mode = debug_mode
        self.inmoov_id = -1
        self.num_joints = -1
        self.robot_base_pos = [0, 0, 0]

        # constraint
        self.max_force = 200.
        self.max_velocity = 3.
        # joint information
        self.joint_info = {}

        # camera position
        self.camera_target_pos = (0.0, 0.0, 1.0)
        if self.debug_mode:
            client_id = p.connect(p.SHARED_MEMORY)
            if client_id < 0:
                p.connect(p.GUI)
            p.resetDebugVisualizerCamera(5., 180, -41, [0.52, -0.2, -0.33])

            # To debug the joints of the Inmoov robot
            debug_joints = []
            self.joints_key = []
            for joint_index in joint_registry:
                self.joints_key.append(joint_index)
                debug_joints.append(p.addUserDebugParameter(joint_registry[joint_index], -1., 1., 0))
            self.debug_joints = debug_joints

            # To debug the camera position
            debug_camera = 0
        else:
            self.joints_key = list(joint_registry.keys())
            p.connect(p.DIRECT)

        self.reset()

    def get_action_dimension(self):
        """
        To know how many joint can be controlled
        :return: int
        """
        return len(CONTROL_JOINT)

    def apply_action(self, motor_commands):
        """
        Apply the action to the inmoov robot joint
        If the length of commands is inferior to the length of controlable joint, then we only control the first joints
        :param motor_commands:
        """
        joint_poses = motor_commands
        # TODO: i is what?
        num_control = min((len(joint_poses), len(CONTROL_JOINT)))

        targetVelocities = [0] * num_control
        forces = [self.max_force] * num_control
        positionGains = [0.3] * num_control
        velocityGains = [1] * num_control
        p.setJointMotorControlArray(bodyUniqueId=self.inmoov_id,
                                    controlMode=p.POSITION_CONTROL,
                                    jointIndices=CONTROL_JOINT[:num_control],
                                    targetPositions=motor_commands[:num_control],
                                    targetVelocities=targetVelocities,
                                    forces=forces,
                                    positionGains=positionGains,
                                    velocityGains=velocityGains
                                    )

        #### Same functionality, but upper lines works better
        # for i in range(num_control):
        #     # p.setJointMotorControl2(bodyUniqueId=self.inmoov_id, jointIndex=CONTROL_JOINT[i],
        #     #                         controlMode=p.POSITION_CONTROL, targetPosition=joint_poses[i],
        #     #                         targetVelocity=0, force=self.max_force,
        #     #                         maxVelocity=self.max_velocity, positionGain=0.3, velocityGain=1)
        #     p.setJointMotorControl2(bodyUniqueId=self.inmoov_id, jointIndex=CONTROL_JOINT[i],
        #                             controlMode=p.POSITION_CONTROL, targetPosition=joint_poses[i],
        #                             targetVelocity=0, force=self.max_force,
        #                             maxVelocity=4., positionGain=0.3, velocityGain=1)
        p.stepSimulation()

    def apply_action_link(self, motor_commands):
        """
        Apply the action to the inmoov robot joint
        If the length of commands is inferior to the length of controlable joint, then we only control the first joints
        :param motor_commands:
        """
        dx = 0
        dy = 0
        dz = - 0.1
        hand_index = 28
        # TODO: this is an inefficient way to get the current position, we should use a traker of the position
        joint_position = p.getLinkState(self.inmoov_id, hand_index)

        current_state = joint_position[0]
        target_pos = (current_state[0] + dx, current_state[1] + dy, current_state[2] + dz)
        printGreen("Current hand positioin: {}".format(joint_position[0]))

        joint_poses = p.calculateInverseKinematics(self.inmoov_id, hand_index, target_pos)
        tt()
        for i, index in enumerate(self.joints_key):
            p.setJointMotorControl2(bodyUniqueId=self.inmoov_id, jointIndex=index, controlMode=p.POSITION_CONTROL,
                                    targetPosition=joint_poses[i], targetVelocity=0, force=self.max_force,
                                    maxVelocity=self.max_velocity, positionGain=0.3, velocityGain=1)


        p.stepSimulation()


    def step(self, action):
        assert len(action) == len(control_joint)
        # TODO
        return

    def reset(self):
        """
        Reset the environment
        """
        p.setGravity(0., 0., -10.)
        self.inmoov_id = p.loadURDF(os.path.join(self.urdf_path, 'inmoov_col.urdf'), self.robot_base_pos)
        self.num_joints = p.getNumJoints(self.inmoov_id)
        # tmp1 = p.getNumBodies(self.inmoov_id)  # Equal to 1, only one body
        # tmp2 = p.getNumConstraints(self.inmoov_id)  # Equal to 0, no constraint?
        # tmp3 = p.getBodyUniqueId(self.inmoov_id)  # res = 0, do not understand
        for jointIndex in self.joints_key:
            p.resetJointState(self.inmoov_id, jointIndex, 0.)
        # get joint information
        self.get_joint_info()


        ######################## debug part #######################
        # link_position = []
        # p.getBasePositionAndOrientation(self.inmoov_id)
        # for i in range(100):
        #     print("linkWorldPosition, , , , workldLinkFramePosition", i)
        #     link_state = p.getLinkState(self.inmoov_id, i)
        #     if link_state is not None:
        #         link_position.append(link_state[0])
        #
        # link_position = np.array(link_position).T
        # print(link_position.shape)
        #
        # fig = plt.figure("3D link plot")
        # ax = fig.add_subplot(111, projection='3d')
        # ax.scatter(link_position[0], link_position[1], link_position[2], c='r', marker='o')
        # for i in range(link_position.shape[1]):
        #     # ax.annotate(str(i), (link_position[0,i], link_position[1,i], link_position[2,i]) )
        #     ax.text(link_position[0,i], link_position[1,i], link_position[2,i], str(i))
        # # ax.set_xlim([-1, 1])
        # # ax.set_ylim([-1, 1])
        # ax.set_xlim([-.25, .25])
        # ax.set_ylim([-.25, .25])
        # ax.set_zlim([1, 2])
        # plt.show()
        ######################## debug part #######################
        
    def get_joint_info(self):
        """
        From this we can see the fact that:
        - no joint damping is set
        - some of the joints are reserved???
        - none of them has joint Friction
        - we have 53 revo
        :return:
        """
        for i in range(self.num_joints):
            info = p.getJointInfo(self.inmoov_id, i)
            # if info[7] != 0:
            #     print(info[1], "has friction")
            # if info[6] != 0:
            #     print(info[1], "has damping")
            if info[2] == p.JOINT_REVOLUTE:
                self.joint_info[i] = (info[1], (info[8], info[9]), info[12], info[13], info[16])
        return

    def debugger_step(self):

        if self.debug_mode:
            current_joints = []
            # The order is as the same as the self.joint_key
            for j in self.debug_joints:
                tmp_joint_control = p.readUserDebugParameter(j)
                current_joints.append(tmp_joint_control)
            for joint_state, joint_key in zip(current_joints, self.joints_key):
                p.resetJointState(self.inmoov_id, joint_key, targetValue=joint_state)
            p.stepSimulation()

    def debugger_camera(self):
        if self.debug_mode:
            tete = "Stupid"

    def robot_render(self):
        """
        The image from the robot eye
        :return:
        """
        # TODO


    def render(self, num_camera=1):
        if self._renders:
            plt.ion()
            if num_camera == 1:
                figsize = np.array([3, 1]) * 5
            else:
                figsize = np.array([3, 2]) * 5
            fig = plt.figure("Inmoov",figsize=figsize)

            camera_target_position = self.camera_target_pos

            # view_matrix2 = p.computeViewMatrixFromYawPitchRoll(
            #     cameraTargetPosition=(0.316, 0.316, 1.0),
            #     distance=1.2,
            #     yaw=90,  # 145 degree
            #     pitch=-13,  # -36 degree
            #     roll=0,
            #     upAxisIndex=2
            # )
            # proj_matrix2 = p.computeProjectionMatrixFOV(
            #     fov=60, aspect=float(RENDER_WIDTH) / RENDER_HEIGHT,
            #     nearVal=0.1, farVal=100.0)
            # (_, _, px2, depth2, mask2) = p.getCameraImage(
            #     width=RENDER_WIDTH, height=RENDER_HEIGHT, viewMatrix=view_matrix2,
            #     projectionMatrix=proj_matrix2, renderer=p.ER_TINY_RENDERER)


            view_matrix1 = p.computeViewMatrixFromYawPitchRoll(
                cameraTargetPosition=camera_target_position,
                distance=2.,
                yaw=145,  # 145 degree
                pitch=-36,  # -36 degree
                roll=0,
                upAxisIndex=2
            )

            proj_matrix1 = p.computeProjectionMatrixFOV(
                fov=60, aspect=float(RENDER_WIDTH) / RENDER_HEIGHT,
                nearVal=0.1, farVal=100.0)

            (_, _, px, depth, mask) = p.getCameraImage(
                width=RENDER_WIDTH, height=RENDER_HEIGHT, viewMatrix=view_matrix1,
                projectionMatrix=proj_matrix1, renderer=p.ER_TINY_RENDERER)
            px, depth, mask = np.array(px), np.array(depth), np.array(mask)
            if num_camera == 2:
                view_matrix2 = p.computeViewMatrixFromYawPitchRoll(
                    cameraTargetPosition=(0.316, 0.316, 1.0),
                    distance=1.2,
                    yaw=90,  # 145 degree
                    pitch=-13,  # -36 degree
                    roll=0,
                    upAxisIndex=2
                )
                proj_matrix2 = p.computeProjectionMatrixFOV(
                    fov=60, aspect=float(RENDER_WIDTH) / RENDER_HEIGHT,
                    nearVal=0.1, farVal=100.0)
                (_, _, px2, depth2, mask2) = p.getCameraImage(
                    width=RENDER_WIDTH, height=RENDER_HEIGHT, viewMatrix=view_matrix2,
                    projectionMatrix=proj_matrix2, renderer=p.ER_TINY_RENDERER)
                ax1 = fig.add_subplot(231)
                ax1.imshow(px)
                ax1.set_title("rgb_1")
                ax2 = fig.add_subplot(232)
                ax2.imshow(depth)
                ax2.set_title("depth_1")
                ax3 = fig.add_subplot(233)
                ax3.imshow(mask)
                ax3.set_title("mask_1")
                ax1 = fig.add_subplot(234)
                ax1.imshow(px2)
                ax1.set_title("rgb_2")
                ax2 = fig.add_subplot(235)
                ax2.imshow(depth2)
                ax2.set_title("depth_2")
                ax3 = fig.add_subplot(236)
                ax3.imshow(mask2)
                ax3.set_title("mask_2")
            else:  # only one camera
                ax1 = fig.add_subplot(131)
                ax1.imshow(px)
                ax1.set_title("rgb_1")
                ax2 = fig.add_subplot(132)
                ax2.imshow(depth)
                ax2.set_title("depth_1")
                ax3 = fig.add_subplot(133)
                ax3.imshow(mask)
                ax3.set_title("mask_1")
            # rgb_array = np.array(px)
            # self.image_plot = plt.imshow(rgb_array)
            # self.image_plot.axes.grid(False)
            # plt.title("Inmoov Robot Simulation")
            fig.suptitle('Inmoov Simulation: Two Cameras View', fontsize=32 )
            plt.draw()
            plt.pause(0.00001)


