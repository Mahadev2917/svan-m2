#!/usr/bin/env python3
"""Extra camera views of SVAN in Gazebo: bird's eye, robot POV and chase cam.

Spawns small invisible camera models in Gazebo and moves them with the robot every
simulation tick (the robot's URDF is not touched). Images are published on
    /mahadev/birdseye/image_raw   straight down from above, robot's front = top of image
    /mahadev/pov/image_raw        from the robot's head, looking where it walks
    /mahadev/chase/image_raw      third-person, behind and above the robot
View them with image_view / rqt_image_view (lab_sim.launch opens the windows).
Params: ~views (e.g. "birdseye,pov"), ~model (default svan), ~birdseye_height (m).
"""
import math

import rospy
from gazebo_msgs.msg import ModelState, ModelStates
from gazebo_msgs.srv import GetModelProperties, SpawnModel
from geometry_msgs.msg import Pose, Quaternion

# name: (offset in robot frame x, y, z), camera pitch (rad, + = look down), hfov, size
VIEWS = {
    "birdseye": ((0.0, 0.0, None), math.pi / 2, 1.2, (640, 480)),
    "pov": ((0.32, 0.0, 0.06), 0.15, 1.5, (640, 480)),
    "chase": ((-1.6, 0.0, 0.9), 0.45, 1.3, (640, 480)),
}

CAMERA_SDF = """<?xml version='1.0'?>
<sdf version='1.6'>
  <model name='{model}'>
    <link name='link'>
      <gravity>false</gravity>
      <inertial><mass>0.01</mass><inertia><ixx>1e-5</ixx><iyy>1e-5</iyy><izz>1e-5</izz></inertia></inertial>
      <sensor name='cam' type='camera'>
        <update_rate>15</update_rate>
        <camera>
          <horizontal_fov>{hfov}</horizontal_fov>
          <image><width>{w}</width><height>{h}</height><format>R8G8B8</format></image>
          <clip><near>0.05</near><far>40</far></clip>
        </camera>
        <plugin name='cam_plugin' filename='libgazebo_ros_camera.so'>
          <cameraName>mahadev/{name}</cameraName>
          <imageTopicName>image_raw</imageTopicName>
          <cameraInfoTopicName>camera_info</cameraInfoTopicName>
          <frameName>{model}</frameName>
        </plugin>
      </sensor>
    </link>
  </model>
</sdf>"""


def quat_from_pitch_yaw(pitch, yaw):
    cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
    return Quaternion(x=-sy * sp, y=cy * sp, z=sy * cp, w=cy * cp)


class CameraViews:
    def __init__(self):
        rospy.init_node("camera_views")
        self.model = rospy.get_param("~model", "svan")
        self.height = rospy.get_param("~birdseye_height", 4.0)
        names = rospy.get_param("~views", "birdseye,pov,chase")
        self.views = [v.strip() for v in names.split(",") if v.strip() in VIEWS]
        self.robot = None

        self.wait_for_robot()
        spawn = rospy.ServiceProxy("/gazebo/spawn_sdf_model", SpawnModel)
        for name in self.views:
            _, _, hfov, (w, h) = VIEWS[name]
            sdf = CAMERA_SDF.format(model=self.cam_model(name), name=name, hfov=hfov, w=w, h=h)
            spawn(self.cam_model(name), sdf, "", Pose(), "world")
        rospy.loginfo("camera views: %s", ", ".join(self.views))

        self.pub = rospy.Publisher("/gazebo/set_model_state", ModelState, queue_size=len(self.views))
        rospy.Subscriber("/gazebo/model_states", ModelStates, self.on_states, queue_size=1)

    @staticmethod
    def cam_model(name):
        return "mahadev_cam_" + name

    def wait_for_robot(self):
        rospy.wait_for_service("/gazebo/spawn_sdf_model")
        props = rospy.ServiceProxy("/gazebo/get_model_properties", GetModelProperties)
        while not rospy.is_shutdown() and not props(self.model).success:
            rospy.sleep(0.5)

    def on_states(self, msg):
        if self.model not in msg.name:
            return
        p = msg.pose[msg.name.index(self.model)]
        q = p.orientation
        self.robot = (p.position.x, p.position.y, p.position.z,
                      math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2)))

    def update(self):
        if self.robot is None:
            return
        rx, ry, rz, yaw = self.robot
        c, s = math.cos(yaw), math.sin(yaw)
        for name in self.views:
            (dx, dy, dz), pitch, _, _ = VIEWS[name]
            st = ModelState(model_name=self.cam_model(name), reference_frame="world")
            st.pose.position.x = rx + c * dx - s * dy
            st.pose.position.y = ry + s * dx + c * dy
            st.pose.position.z = self.height if dz is None else rz + dz
            st.pose.orientation = quat_from_pitch_yaw(pitch, yaw)
            self.pub.publish(st)

    def spin(self):
        rate = rospy.Rate(60)
        while not rospy.is_shutdown():
            self.update()
            rate.sleep()


if __name__ == "__main__":
    try:
        CameraViews().spin()
    except rospy.ROSInterruptException:
        pass
