# SVAN M2 environment. Use in every new terminal:
#   source ~/mahadev_svan/env.sh
# Only affects the current terminal; does not touch ~/.bashrc or other users' workspaces.
source /opt/ros/noetic/setup.bash
source ~/mahadev_svan/xMo/devel/setup.bash
export GAZEBO_PLUGIN_PATH=~/mahadev_svan/xMo/src/svan_gazebo/plugins/build
cd ~/mahadev_svan/xMo
echo "[mahadev_svan] environment ready ($(pwd))"
