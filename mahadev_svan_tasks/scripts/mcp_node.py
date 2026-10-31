#!/usr/bin/env python3
"""Run svan_control's mcp.py from a launch file.

mcp.py is not an installed node (it sits in svan_control/src and isn't executable),
so this wrapper waits until Gazebo has spawned the robot, then runs it unchanged.
Usage (from a launch file): mcp_node.py <path/to/mcp.py> [model_name]
"""
import os
import runpy
import sys
import time

import rospy
from gazebo_msgs.srv import GetModelProperties


def wait_for_model(model):
    rospy.wait_for_service("/gazebo/get_model_properties")
    get_props = rospy.ServiceProxy("/gazebo/get_model_properties", GetModelProperties)
    while not get_props(model).success:
        time.sleep(0.5)


def main():
    args = rospy.myargv(sys.argv)
    mcp_path = args[1]
    model = args[2] if len(args) > 2 else "svan"

    wait_for_model(model)
    time.sleep(2.0)  # let pd_controller connect and the robot settle on the floor

    mcp_dir = os.path.dirname(os.path.abspath(mcp_path))
    sys.path.insert(0, mcp_dir)  # for `from mcp_helper import *`
    os.chdir(mcp_dir)
    runpy.run_path(mcp_path, run_name="__main__")


if __name__ == "__main__":
    main()
