#!/usr/bin/env python3
"""Put a fallen SVAN back on its feet in Gazebo (simulation only).

The keyboard Space key only zeroes the commands; it can't flip the robot over.
This sends STOP, then lifts the robot upright where it is (or to --spawn) and lets
pd_controller pull the legs back into the stance pose that mcp.py is holding.
    rosrun mahadev_svan_tasks reset_robot.py            # stand up where it fell
    rosrun mahadev_svan_tasks reset_robot.py --spawn    # back to the orange mat
"""
import math
import sys

import rospy
from gazebo_msgs.msg import ModelState
from gazebo_msgs.srv import GetModelState, SetModelState
from std_msgs.msg import Float32MultiArray
from std_srvs.srv import Empty

SPAWN = (-5.45, -2.4, 1.5708)  # same as lab_sim.launch defaults
LIFT_Z = 0.45


def yaw_of(q):
    # heading of the body x-axis projected on the ground (works even when upside down)
    fx = 1 - 2 * (q.y ** 2 + q.z ** 2)
    fy = 2 * (q.x * q.y + q.w * q.z)
    return math.atan2(fy, fx)


def main():
    rospy.init_node("reset_robot")
    model = rospy.get_param("~model", "svan")

    # 1) STOP so mcp.py leaves trot and holds the stance pose
    pub = rospy.Publisher("/svan/io_interface", Float32MultiArray, queue_size=1)
    rospy.sleep(0.5)
    for _ in range(5):
        pub.publish(Float32MultiArray(data=[1] + [0] * 8))
        rospy.sleep(0.1)

    for srv in ("/gazebo/get_model_state", "/gazebo/set_model_state", "/gazebo/pause_physics"):
        rospy.wait_for_service(srv)
    get_state = rospy.ServiceProxy("/gazebo/get_model_state", GetModelState)
    set_state = rospy.ServiceProxy("/gazebo/set_model_state", SetModelState)
    pause = rospy.ServiceProxy("/gazebo/pause_physics", Empty)
    unpause = rospy.ServiceProxy("/gazebo/unpause_physics", Empty)

    if "--spawn" in rospy.myargv(sys.argv):
        x, y, yaw = SPAWN
    else:
        p = get_state(model, "world").pose
        x, y, yaw = p.position.x, p.position.y, yaw_of(p.orientation)

    # 2) lift it upright, give the legs time to fold into stance in the air, then drop
    st = ModelState(model_name=model, reference_frame="world")
    st.pose.position.x, st.pose.position.y, st.pose.position.z = x, y, LIFT_Z
    st.pose.orientation.z, st.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
    pause()
    set_state(st)
    unpause()
    end = rospy.Time.now() + rospy.Duration(1.5)
    while rospy.Time.now() < end and not rospy.is_shutdown():
        set_state(st)  # hold it in the air while the legs settle
        rospy.sleep(0.02)

    rospy.sleep(2.0)
    z = get_state(model, "world").pose.position.z
    rospy.loginfo("reset done at x=%.2f y=%.2f, body height %.2f m%s", x, y, z,
                  "" if z > 0.2 else " - still low, run again or press 3/4 after a moment")


if __name__ == "__main__":
    main()
