#!/usr/bin/env python3
"""
Hardcode one leg's rotation and/or lift servo to an explicit angle.
Angle is raw -- same space as center/min/max in robot_config.json
(0-180, already invert-corrected). Bypasses IK entirely.

Usage:
    python3 set_angles.py FL rotation 100
    python3 set_angles.py FL lift 60
    python3 set_angles.py FL rotation 100 lift 60
"""
import sys
from robot import Robot


def usage():
    print(__doc__)
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if len(args) < 3 or args[0] not in ("FL", "FR", "BL", "BR"):
        usage()

    leg_name = args[0]
    kwargs = {}
    i = 1
    while i < len(args):
        joint = args[i]
        if joint not in ("rotation", "lift") or i + 1 >= len(args):
            usage()
        try:
            angle = float(args[i + 1])
        except ValueError:
            usage()
        kwargs[joint] = angle
        i += 2

    robot = Robot()
    leg = robot.legs[leg_name]
    try:
        print(f"{leg_name}: moving to {kwargs}")
        leg.move_to(**kwargs, steps=30, delay=0.02)
        print("done. current -> rotation:", leg.rot.current_angle,
              "lift:", leg.lift.current_angle)
        input("press enter to relax this leg...")
        leg.relax()
    finally:
        robot.pi.stop()


if __name__ == "__main__":
    main()
