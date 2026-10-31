#!/usr/bin/env python3
"""Demo: SVAN walks laps around the conference table in the lab world (Gazebo only).

Follows an oval through the free lane between the table chairs and the counters
(straight sides at y = +-2.2, round ends of radius 2.2 m), clockwise seen from above,
steering with pure pursuit on Gazebo's ground-truth pose. If the robot falls or gets
stuck it is put back on the path (reset_robot.py) and carries on.
Ctrl+C stops it and the robot stands still.
    rosrun mahadev_svan_tasks circle_table.py            # loop forever
    rosrun mahadev_svan_tasks circle_table.py _laps:=2   # stop after 2 laps
    roslaunch mahadev_svan_tasks lab_sim.launch circle:=true   # everything in one go

Measured gait (mcp.py): forward 0.2 ~ 0.12 m/s, 0.3 ~ 0.22 m/s, 0.5 ~ 0.45 m/s. The yaw input
only twists the body, so SVAN turns while walking (radius ~1.5 m at forward 0.2, ~1.8 m at 0.3, full yaw)
and can't turn on the spot - hence round ends instead of corners.
"""
import math
import subprocess

import rospy
from gazebo_msgs.msg import ModelStates

from svan_cmd import Svan, STOP, TROT

# oval around the table (x -3.0..3.2, y +-0.9, chairs to y +-1.65)
X_BACK, X_FRONT, R = -2.9, 3.0, 2.2
LOOKAHEAD = 1.0     # m ahead on the path to steer towards
FAST, SLOW = 0.5, 0.2  # forward command on straights / in (and just before) curves
PREVIEW = 2.0       # m ahead to look for a curve, to slow down in time
K_YAW = 2.5         # yaw command per rad of heading error (+yaw = clockwise)
STUCK_TIME = 20.0   # s without 0.5 m of progress -> put back on the path


def angle_diff(a, b):
    return math.atan2(math.sin(a - b), math.cos(a - b))


def oval(n_arc=24):
    """Clockwise loop as a list of points: back straight at y=+R towards +x, front arc, ..."""
    pts = [(X_BACK, R), (X_FRONT, R)]
    for k in range(1, n_arc):  # front end, from +y round to -y via +x
        t = math.pi / 2 - math.pi * k / n_arc
        pts.append((X_FRONT + R * math.cos(t), R * math.sin(t)))
    pts += [(X_FRONT, -R), (X_BACK, -R)]
    for k in range(1, n_arc):  # back end, from -y round to +y via -x
        t = -math.pi / 2 - math.pi * k / n_arc
        pts.append((X_BACK + R * math.cos(t), R * math.sin(t)))
    return pts


class Loop:
    def __init__(self, pts):
        self.pts = pts
        self.segs = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
        self.lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in self.segs]
        self.total = sum(self.lens)

    def project(self, x, y):
        """Arc length s of the closest point on the loop, and distance to it."""
        best, s0 = (1e9, 0.0), 0.0
        for (a, b), L in zip(self.segs, self.lens):
            t = ((x - a[0]) * (b[0] - a[0]) + (y - a[1]) * (b[1] - a[1])) / L ** 2
            t = min(max(t, 0.0), 1.0)
            d = math.hypot(a[0] + t * (b[0] - a[0]) - x, a[1] + t * (b[1] - a[1]) - y)
            if d < best[0]:
                best = (d, s0 + t * L)
            s0 += L
        return best[1], best[0]

    def point(self, s):
        s %= self.total
        for (a, b), L in zip(self.segs, self.lens):
            if s <= L:
                t = s / L
                return a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
            s -= L
        return self.pts[0]

    def heading(self, s):
        (x0, y0), (x1, y1) = self.point(s), self.point(s + 0.1)
        return math.atan2(y1 - y0, x1 - x0)


class TableDemo:
    def __init__(self):
        self.svan = Svan("circle_table")
        self.laps = rospy.get_param("~laps", 0)  # 0 = forever
        self.loop = Loop(oval())
        self.state = None  # x, y, yaw, z, upright (body z-axis . world z)
        rospy.Subscriber("/gazebo/model_states", ModelStates, self.on_states, queue_size=1)

    def on_states(self, msg):
        if "svan" not in msg.name:
            return
        p = msg.pose[msg.name.index("svan")]
        q = p.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))
        up = 1 - 2 * (q.x ** 2 + q.y ** 2)
        self.state = (p.position.x, p.position.y, yaw, p.position.z, up)

    def fallen(self):
        _, _, _, z, up = self.state
        return up < 0.5 or z < 0.15

    def recover(self, why):
        """Put the robot on the path a little ahead of where it was, facing along it."""
        x, y = self.state[:2]
        s, _ = self.loop.project(x, y)
        px, py = self.loop.point(s + 0.5)
        rospy.logwarn("%s - putting it back on the path at (%.1f, %.1f)", why, px, py)
        self.svan.stop(1.0)
        subprocess.call(["rosrun", "mahadev_svan_tasks", "reset_robot.py",
                         "_x:=%f" % px, "_y:=%f" % py, "_yaw:=%f" % self.loop.heading(s + 0.5)])
        self.svan.stop(1.0)
        self.svan.trot(2.0)

    def run(self):
        # wait until mcp.py has stood the robot up (when started together with lab_sim.launch)
        t0 = rospy.Time.now()
        while not rospy.is_shutdown() and (self.state is None or self.state[3] < 0.28) \
                and (rospy.Time.now() - t0).to_sec() < 30:
            rospy.sleep(0.2)
        rospy.sleep(1.0)
        loop = self.loop
        rospy.loginfo("circling the table (loop %.1f m)%s", loop.total,
                      "" if not self.laps else ", %d laps" % self.laps)
        if self.fallen():
            self.recover("robot is lying down")
        self.svan.stop(1.5)
        self.svan.trot(2.0)

        s_prev, travelled = None, 0.0
        mark, mark_time = 0.0, rospy.Time.now()
        while not rospy.is_shutdown():
            x, y, yaw, _, _ = self.state
            s, dist = loop.project(x, y)
            if s_prev is not None and dist < 0.8:  # progress along the loop (handles wrap-around)
                ds = (s - s_prev + loop.total / 2) % loop.total - loop.total / 2
                before = int(travelled // loop.total)
                travelled += max(0.0, ds)
                if int(travelled // loop.total) > before:
                    rospy.loginfo("lap %d done", int(travelled // loop.total))
            s_prev = s
            if self.laps and travelled >= self.laps * loop.total:
                break

            if travelled - mark > 0.5:
                mark, mark_time = travelled, rospy.Time.now()
            if self.fallen() or (rospy.Time.now() - mark_time).to_sec() > STUCK_TIME:
                self.recover("robot fell" if self.fallen() else "robot is stuck")
                s_prev, mark_time = None, rospy.Time.now()
                continue

            tx, ty = loop.point(s + LOOKAHEAD)
            err = angle_diff(math.atan2(ty - y, tx - x), yaw)
            yaw_cmd = max(-1.0, min(1.0, -K_YAW * err))
            bend = abs(angle_diff(loop.heading(s + PREVIEW), loop.heading(s)))
            fwd = FAST if abs(err) < 0.15 and bend < 0.1 else SLOW
            self.svan.send(mode=TROT, forward=fwd, yaw=yaw_cmd)
            self.svan.rate.sleep()

        rospy.loginfo("done: %.1f m walked", travelled)
        self.svan.hold(1.0, mode=TROT)
        self.svan.stop(2.0)


if __name__ == "__main__":
    demo = TableDemo()
    rospy.on_shutdown(lambda: demo.svan.send(mode=STOP))
    try:
        demo.run()
    except rospy.ROSInterruptException:
        pass
