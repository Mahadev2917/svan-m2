#!/usr/bin/env python3
"""First test: stand -> trot forward -> back -> sideways -> turn -> stop.
Run after Gazebo + mcp.py are up (see ~/mahadev_svan/README_MAHADEV.md)."""
import rospy

from svan_cmd import Svan


def report(svan, label):
    p = svan.pose()
    if p:
        rospy.loginfo("%-10s x=%.2f y=%.2f yaw=%.0f deg", label, p[0], p[1], p[2] * 57.3)


def main():
    svan = Svan("demo_moves")
    report(svan, "start")

    rospy.loginfo("Stop / stand")
    svan.stop(2)
    rospy.loginfo("Trot in place")
    svan.trot(2)

    rospy.loginfo("Forward")
    svan.walk(4, forward=0.6)
    report(svan, "forward")

    rospy.loginfo("Backward")
    svan.walk(4, forward=-0.6)
    report(svan, "backward")

    rospy.loginfo("Sideways")
    svan.walk(3, right=1.0)
    report(svan, "sideways")

    rospy.loginfo("Turn")
    svan.walk(4, forward=0.2, yaw=1.0)
    report(svan, "turn")

    rospy.loginfo("Stop")
    svan.stop(2)
    report(svan, "end")


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
