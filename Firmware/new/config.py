import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "robot_config.json")

LEGS = ["FL", "FR", "BL", "BR"]


def load_config():
    """robot_config.json -> SERVO_CONFIG["FL1"]/["FL2"]/... (gpio/center/min/max/invert)"""
    with open(CONFIG_PATH) as f:
        raw = json.load(f)

    servo_cfg = {}
    for leg in LEGS:
        servo_cfg[leg + "1"] = raw[leg]["rotation"]
        servo_cfg[leg + "2"] = raw[leg]["lift"]
    return servo_cfg


def save_config(servo_cfg):
    raw = {}
    for leg in LEGS:
        raw[leg] = {
            "rotation": servo_cfg[leg + "1"],
            "lift": servo_cfg[leg + "2"],
        }
    with open(CONFIG_PATH, "w") as f:
        json.dump(raw, f, indent=2)


SERVO_CONFIG = load_config()
