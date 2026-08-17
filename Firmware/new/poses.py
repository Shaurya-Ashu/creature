"""
Hardcoded poses. Every angle here is raw -- same 0-180 space as
center/min/max in robot_config.json (already invert-corrected).
Find good numbers with set_angles.py, then hardcode them here.
"""
import time
from robot import Robot


def stand(robot):
    robot.stand()  # = calibrated centers


def sit(robot):
    """Numbers below are placeholders -- use set_angles.py to find good
    lift angles for your robot's crouch, then update these."""
    robot.move_joints({
        "FL": (None, 40),
        "FR": (None, 40),
        "BL": (None, 30),
        "BR": (None, 30),
    }, steps=40, delay=0.02)


def bow(robot):
    """Front legs fold down, back legs stay standing. Placeholder angles."""
    robot.move_joints({
        "FL": (None, 40),
        "FR": (None, 40),
    }, steps=40, delay=0.02)


def hello(robot, leg_name="FR", waves=3):
    """Lift one leg to its max and swing it side to side, then return."""
    leg = robot.legs[leg_name]
    leg.move_to(lift=leg.lift.max_angle, steps=25, delay=0.02)
    for _ in range(waves):
        leg.move_to(rotation=leg.rot.min_angle, steps=15, delay=0.02)
        leg.move_to(rotation=leg.rot.max_angle, steps=15, delay=0.02)
    leg.center(steps=25, delay=0.02)


if __name__ == "__main__":
    robot = Robot()
    try:
        print("stand"); stand(robot); time.sleep(1)
        print("hello"); hello(robot); time.sleep(1)
        print("bow"); bow(robot); time.sleep(1)
        print("stand"); stand(robot); time.sleep(1)
        print("sit"); sit(robot); time.sleep(1)

        input("press enter to relax...")
    finally:
        robot.shutdown()
