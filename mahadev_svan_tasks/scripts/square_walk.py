#!/usr/bin/env python3
"""Closed-loop square in Gazebo: walks each side until it has covered SIDE metres
and turns until heading changed by 90 deg, using Gazebo's ground-truth pose.
(On the real robot there is no Gazebo pose; that needs odometry/IMU instead.)"""
import math

import rospy

from svan_cmd import Svan

SIDE = 1.0          # metres per side
FORWARD = 0.6       # forward command (-1..1)
YAW_CMD = 1.0       # turn command
TURN_FORWARD = 0.2  # small forward speed helps the trot gait turn
TIMEOUT = 30.0      # safety limit per segment (s)


def angle_diff(a, b):
    return math.atan2(math.sin(a - b), math.cos(a - b))


def main():
    svan = Svan("square_walk")
    if svan.pose() is None:
        rospy.logerr("No /gazebo/model_states - this script is simulation-only.")
        return

    svan.stop(2)
    svan.trot(2)

    for side in range(4):
        x0, y0, _ = svan.pose()
        t0 = rospy.Time.now()
        while not rospy.is_shutdown():
            x, y, _ = svan.pose()
            if math.hypot(x - x0, y - y0) >= SIDE or (rospy.Time.now() - t0).to_sec() > TIMEOUT:
                break
            svan.send(mode=4, forward=FORWARD)
            svan.rate.sleep()
        rospy.loginfo("side %d done: %.2f m", side + 1, math.hypot(x - x0, y - y0))
        svan.hold(1.0, mode=4)

        _, _, yaw0 = svan.pose()
        t0 = rospy.Time.now()
        while not rospy.is_shutdown():
            turned = abs(angle_diff(svan.pose()[2], yaw0))
            if turned >= math.radians(88) or (rospy.Time.now() - t0).to_sec() > TIMEOUT:
                break
            svan.send(mode=4, forward=TURN_FORWARD, yaw=YAW_CMD)
            svan.rate.sleep()
        rospy.loginfo("turn %d done: %.0f deg", side + 1, math.degrees(turned))
        svan.hold(1.0, mode=4)

    svan.stop(2)
    x, y, yaw = svan.pose()
    rospy.loginfo("Finished at x=%.2f y=%.2f yaw=%.0f deg", x, y, math.degrees(yaw))


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
