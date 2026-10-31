#!/bin/bash
# One-time setup on a PC with ROS Noetic + Gazebo 11 and the lab's xMo release zip:
#   git clone https://github.com/Mahadev2917/svan-m2.git ~/mahadev_svan
#   ~/mahadev_svan/setup.sh            # or: XMO_ZIP=/path/to/xMo-release-ws-rait.zip ~/mahadev_svan/setup.sh
# Unpacks a clean copy of the xMo workspace (xTerra's SVAN stack, not included in this repo),
# links mahadev_svan_tasks into it and builds everything. Nothing outside ~/mahadev_svan is changed.
set -e
ROOT=~/mahadev_svan
ZIP=${XMO_ZIP:-~/Downloads/xMo-release-ws-rait.zip}
[ "$(cd "$(dirname "$0")" && pwd)" = "$ROOT" ] || { echo "Clone this repo to $ROOT first."; exit 1; }
cd $ROOT
if [ ! -d xMo ]; then
  [ -f "$ZIP" ] || { echo "xMo release zip not found: $ZIP (set XMO_ZIP=...)"; exit 1; }
  unzip -q "$ZIP" -d $ROOT
  rm -rf xMo/build xMo/devel xMo/logs
fi
# optional community helper package (same copy the lab PC has)
if [ ! -d xMo/src/svan_simple_control ] && [ -d ~/xMo/src/svan_simple_control/.git ]; then
  git clone -q ~/xMo/src/svan_simple_control xMo/src/svan_simple_control
fi
ln -sfn $ROOT/mahadev_svan_tasks xMo/src/mahadev_svan_tasks
$ROOT/build.sh
