#!/bin/bash
# Builds the workspace in dependency order (the xMo packages don't declare
# their deps, so a plain parallel `catkin build` fails), then the Gazebo plugins.
set -e
source /opt/ros/noetic/setup.bash
cd ~/mahadev_svan/xMo
for p in svan_msgs svan_utils svan_dynamics svan_control \
         "svan_gazebo svan_m2_description svan_hw" svan_bringup \
         svan_simple_control mahadev_svan_tasks; do
  [ "$p" = svan_simple_control ] && [ ! -d src/svan_simple_control ] && continue
  catkin build --no-status $p
  source devel/setup.bash
done
cd src/svan_gazebo/plugins && rm -rf build && mkdir build && cd build
cmake .. > /dev/null && make -j4
echo "Build done. Now: source ~/mahadev_svan/env.sh"
