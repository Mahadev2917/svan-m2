cmake_minimum_required(VERSION 3.0.2)
project(mahadev_svan_tasks)
find_package(catkin REQUIRED COMPONENTS rospy std_msgs)
catkin_package()
# Scripts are run straight from scripts/ with rosrun (they import svan_cmd.py next to them).
