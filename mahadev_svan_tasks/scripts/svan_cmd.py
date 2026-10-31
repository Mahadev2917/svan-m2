#!/usr/bin/env python3
"""
Small helper for commanding SVAN M2 through mcp.py.

mcp.py listens on /svan/io_interface (std_msgs/Float32MultiArray, 9 values):
    [0] mode     1=STOP 2=TWIRL 3=PUSHUP 4=TROT 6=CLOSE(sleep)
    [1] right    -1..1  sideways  (scaled by -0.10 inside mcp.py)
    [2] forward  -1..1  forward   (scaled by  0.25 inside mcp.py)
    [3] roll     [4] pitch
    [5] [6]      yaw: send(yaw=+1) turns clockwise/right, -1 anticlockwise (tested in Gazebo)
    [7] unused   [8] height step  (+1 up, -1 down, 0 none)

Note: once in TROT, mcp.py only accepts STOP (1) or CLOSE (6) as a mode change.
Works the same in Gazebo and on the real robot. pose() only works in Gazebo.
"""
import math

import rospy
from std_msgs.msg import Float32MultiArray

STOP, TWIRL, PUSHUP, TROT, CLOSE = 1, 2, 3, 4, 6


class Svan:
    def __init__(self, node_name="mahadev_svan", rate_hz=50):
        rospy.init_node(node_name, anonymous=True)
        self.pub = rospy.Publisher("/svan/io_interface", Float32MultiArray, queue_size=1)
        self.rate = rospy.Rate(rate_hz)
        self._pose = None
        rospy.sleep(1.0)  # let the publisher connect to mcp.py

    # ---------- low level ----------
    def send(self, mode=0, right=0.0, forward=0.0, roll=0.0, pitch=0.0, yaw=0.0, height=0):
        yaw_l, yaw_r = (yaw, 0.0) if yaw >= 0 else (0.0, -yaw)
        msg = Float32MultiArray()
        msg.data = [mode, right, forward, roll, pitch, yaw_l, yaw_r, 0, height]
        self.pub.publish(msg)

    def hold(self, seconds, **cmd):
        """Keep sending the same command for `seconds`."""
        end = rospy.Time.now() + rospy.Duration(seconds)
        while not rospy.is_shutdown() and rospy.Time.now() < end:
            self.send(**cmd)
            self.rate.sleep()

    # ---------- high level ----------
    def stop(self, seconds=2.0):
        self.hold(seconds, mode=STOP)

    def trot(self, seconds=2.0):
        """Start trotting in place."""
        self.hold(seconds, mode=TROT)

    def walk(self, seconds, forward=0.0, right=0.0, yaw=0.0):
        self.hold(seconds, mode=TROT, forward=forward, right=right, yaw=yaw)
        self.hold(1.0, mode=TROT)  # settle with zero velocity

    def pushup(self, seconds=6.0):
        self.hold(seconds, mode=PUSHUP)

    def twirl(self, seconds=6.0):
        self.hold(seconds, mode=TWIRL)

    # ---------- Gazebo-only ground truth ----------
    def pose(self, model="svan"):
        """Return (x, y, yaw) of the robot from Gazebo, or None if not in sim."""
        if self._pose is None:
            from gazebo_msgs.msg import ModelStates

            def cb(msg):
                if model in msg.name:
                    p = msg.pose[msg.name.index(model)]
                    q = p.orientation
                    yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))
                    self._pose = (p.position.x, p.position.y, yaw)

            rospy.Subscriber("/gazebo/model_states", ModelStates, cb, queue_size=1)
            try:
                rospy.wait_for_message("/gazebo/model_states", ModelStates, timeout=3.0)
                rospy.sleep(0.1)
            except rospy.ROSException:
                return None
        return self._pose
