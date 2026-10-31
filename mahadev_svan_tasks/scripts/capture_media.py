#!/usr/bin/env python3
"""Records the README pictures while circle_table.py runs: stills, GIFs and a path plot.

Start the demo first (roslaunch mahadev_svan_tasks lab_sim.launch circle:=true chase:=true windows:=false),
then:  rosrun mahadev_svan_tasks capture_media.py _out:=/path/to/docs/images _laps:=1
Spawns a few fixed cameras (top-down room, two room corners) next to the follow cameras
from camera_views.py, and writes:
    topdown_lap.gif   whole room from above, one lap sped up
    chase.gif         chase cam, a few seconds
    sim_overview_*.png, sim_chase.png, sim_pov.png, sim_birdseye.png, sim_topdown.png
    trajectory.png    planned oval vs. the path the robot really walked
"""
import math
import os

import numpy as np
import rospy
from cv_bridge import CvBridge
from gazebo_msgs.msg import ModelStates
from gazebo_msgs.srv import SpawnModel
from geometry_msgs.msg import Pose, Point
from PIL import Image as PImage
from sensor_msgs.msg import Image

from camera_views import quat_from_pitch_yaw
from circle_table import Loop, oval

# name: (x, y, z), pitch, yaw, hfov, size
FIXED = {
    "topdown": ((0.0, 0.0, 14.0), math.pi / 2, 0.0, 0.95, (1040, 720)),
    "overview_window": ((-6.2, -3.7, 1.9), 0.25, 0.5, 1.45, (1280, 720)),
    "overview_tv": ((6.3, 3.8, 2.8), 0.42, -2.6, 1.45, (1280, 720)),
}
STATIC_SDF = """<?xml version='1.0'?>
<sdf version='1.6'><model name='{model}'><static>true</static><link name='link'>
  <sensor name='cam' type='camera'><update_rate>5</update_rate>
    <camera><horizontal_fov>{hfov}</horizontal_fov>
      <image><width>{w}</width><height>{h}</height><format>R8G8B8</format></image>
      <clip><near>0.1</near><far>40</far></clip></camera>
    <plugin name='p' filename='libgazebo_ros_camera.so'><cameraName>mahadev/{name}</cameraName>
      <imageTopicName>image_raw</imageTopicName><cameraInfoTopicName>camera_info</cameraInfoTopicName>
      <frameName>{model}</frameName></plugin>
  </sensor></link></model></sdf>"""


class Capture:
    def __init__(self):
        rospy.init_node("capture_media")
        self.out = os.path.expanduser(rospy.get_param("~out", "~/svan_media"))
        self.laps = rospy.get_param("~laps", 1)
        os.makedirs(self.out, exist_ok=True)
        self.bridge = CvBridge()
        self.latest = {}
        self.track = []  # (t, x, y)
        rospy.wait_for_service("/gazebo/spawn_sdf_model")
        spawn = rospy.ServiceProxy("/gazebo/spawn_sdf_model", SpawnModel)
        for name, ((x, y, z), pitch, yaw, hfov, (w, h)) in FIXED.items():
            model = "mahadev_fixed_" + name
            sdf = STATIC_SDF.format(model=model, name=name, hfov=hfov, w=w, h=h)
            spawn(model, sdf, "", Pose(Point(x, y, z), quat_from_pitch_yaw(pitch, yaw)), "world")
        for name in list(FIXED) + ["chase", "pov", "birdseye"]:
            rospy.Subscriber("/mahadev/%s/image_raw" % name, Image, self.on_image, name,
                             queue_size=1, buff_size=2 ** 24)
        rospy.Subscriber("/gazebo/model_states", ModelStates, self.on_states, queue_size=1)

    def on_image(self, msg, name):
        self.latest[name] = msg

    def on_states(self, msg):
        if "svan" in msg.name:
            p = msg.pose[msg.name.index("svan")].position
            t = rospy.Time.now().to_sec()
            if not self.track or t - self.track[-1][0] > 0.2:
                self.track.append((t, p.x, p.y))

    def frame(self, name, scale=1.0):
        img = PImage.fromarray(self.bridge.imgmsg_to_cv2(self.latest[name], "rgb8"))
        if scale != 1.0:
            img = img.resize((int(img.width * scale), int(img.height * scale)), PImage.LANCZOS)
        return img

    def save(self, name, file):
        self.frame(name).save(os.path.join(self.out, file))
        rospy.loginfo("saved %s", file)

    def run(self):
        while not rospy.is_shutdown() and (len(self.latest) < 6 or len(self.track) < 5):
            rospy.sleep(0.5)
        loop = Loop(oval())
        s_prev, travelled = None, 0.0
        top, chase, stills = [], [], set()
        last_top = 0.0
        while not rospy.is_shutdown() and travelled < self.laps * loop.total:
            _, x, y = self.track[-1]
            s, dist = loop.project(x, y)
            if s_prev is not None and dist < 0.8:
                travelled += max(0.0, (s - s_prev + loop.total / 2) % loop.total - loop.total / 2)
            s_prev = s
            now = rospy.Time.now().to_sec()
            if now - last_top > 2.0:  # one top-down frame every 2 s of sim time
                top.append(self.frame("topdown", 0.6))
                last_top = now
            # chase GIF and the stills on the long straight at y=-2.2 (good view of the table)
            if y < -1.8 and -1.5 < x < 1.5:
                if len(chase) < 50:
                    chase.append(self.frame("chase", 0.6))
                if "straight" not in stills:
                    for n in ("chase", "pov", "birdseye", "overview_window", "overview_tv", "topdown"):
                        self.save(n, "sim_%s.png" % n)
                    stills.add("straight")
            rospy.sleep(0.15)

        self.save_gif(top, "topdown_lap.gif", 120)
        self.save_gif(chase, "chase.gif", 150)
        self.plot(loop)

    def save_gif(self, frames, file, ms):
        if frames:
            frames = [f.convert("P", palette=PImage.ADAPTIVE, colors=128) for f in frames]
            frames[0].save(os.path.join(self.out, file), save_all=True, append_images=frames[1:],
                           duration=ms, loop=0, optimize=True)
            rospy.loginfo("saved %s (%d frames)", file, len(frames))

    def plot(self, loop):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        fig, ax = plt.subplots(figsize=(9, 6.2))
        ax.add_patch(Rectangle((-6.5, -4.5), 13, 9, fill=False, lw=2, color="0.3"))
        ax.add_patch(Rectangle((-3.0, -0.9), 6.2, 1.8, color="#d9b98c", label="conference table"))
        ax.add_patch(Rectangle((-3.0, -1.65), 6.2, 3.3, fill=False, ls=":", color="#a07a4a",
                               label="chairs"))
        px, py = zip(*(loop.pts + loop.pts[:1]))
        ax.plot(px, py, "--", color="#1f77b4", lw=1.5, label="planned oval (25.6 m)")
        tx, ty = [p[1] for p in self.track], [p[2] for p in self.track]
        ax.plot(tx, ty, color="#d62728", lw=1.2, label="robot path (Gazebo ground truth)")
        ax.plot(tx[0], ty[0], "o", color="#d62728")
        ax.set_aspect("equal")
        ax.set_xlim(-6.8, 6.8)
        ax.set_ylim(-4.8, 4.8)
        ax.set_xlabel("x [m]  (TV wall at +x)")
        ax.set_ylabel("y [m]")
        ax.set_title("circle_table.py: pure-pursuit laps around the table")
        ax.legend(loc="upper left", fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(self.out, "trajectory.png"), dpi=110)
        rospy.loginfo("saved trajectory.png")


if __name__ == "__main__":
    Capture().run()
