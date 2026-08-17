import time
import pigpio
from config import SERVO_CONFIG

LEG_NAMES = ["FL", "FR", "BL", "BR"]

MIN_PULSE_US = 500
MAX_PULSE_US = 2500
MAX_ANGLE = 180


class Servo:
    """One physical servo: angle -> pulse, clamped to this servo's
    calibrated min/max, corrected for invert."""

    def __init__(self, pi, name, cfg):
        self.pi = pi
        self.name = name
        self.gpio = cfg["gpio"]
        self.center = cfg.get("center", 90)
        self.min_angle = cfg.get("min", 60)
        self.max_angle = cfg.get("max", 120)
        self.invert = cfg.get("invert", False)
        self.current_angle = None

    def _angle_to_pulse(self, angle):
        angle = max(0, min(MAX_ANGLE, angle))
        return int(MIN_PULSE_US + (angle / MAX_ANGLE) * (MAX_PULSE_US - MIN_PULSE_US))

    def set_angle(self, angle, clamp=True):
        if clamp:
            angle = max(self.min_angle, min(self.max_angle, angle))
        physical = MAX_ANGLE - angle if self.invert else angle
        self.pi.set_servo_pulsewidth(self.gpio, self._angle_to_pulse(physical))
        self.current_angle = angle

    def go_center(self):
        self.set_angle(self.center, clamp=False)

    def off(self):
        self.pi.set_servo_pulsewidth(self.gpio, 0)


class Leg:
    """One leg = rotation servo + lift servo. Angles only, no IK."""

    def __init__(self, rot_servo, lift_servo):
        self.rot = rot_servo
        self.lift = lift_servo

    def move_to(self, rotation=None, lift=None, steps=20, delay=0.015):
        """Move rotation and/or lift to a raw angle (0-180, calibrated
        space), interpolated smoothly. Both move together if both given."""
        targets = {}
        if rotation is not None:
            targets[self.rot] = max(self.rot.min_angle, min(self.rot.max_angle, rotation))
        if lift is not None:
            targets[self.lift] = max(self.lift.min_angle, min(self.lift.max_angle, lift))
        if not targets:
            return

        starts = {s: (s.current_angle if s.current_angle is not None else s.center)
                  for s in targets}

        for i in range(1, steps + 1):
            frac = i / steps
            for s, target in targets.items():
                s.set_angle(starts[s] + (target - starts[s]) * frac, clamp=False)
            time.sleep(delay)

    def center(self, **kw):
        self.move_to(rotation=self.rot.center, lift=self.lift.center, **kw)

    def relax(self):
        self.rot.off()
        self.lift.off()


class Robot:
    def __init__(self):
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("pigpiod not running. Run: sudo pigpiod")

        self.legs = {}
        for name in LEG_NAMES:
            rot = Servo(self.pi, name + "1", SERVO_CONFIG[name + "1"])
            lift = Servo(self.pi, name + "2", SERVO_CONFIG[name + "2"])
            self.legs[name] = Leg(rot, lift)

    def move_joints(self, targets, steps=30, delay=0.02):
        """Hardcode raw servo angles directly.
        targets: dict leg_name -> (rotation_angle, lift_angle), either
        can be None to leave that servo untouched. Angles are 0-180,
        calibrated space (same as center/min/max in robot_config.json).
        Synchronized across every servo listed.

        Example: robot.move_joints({"FL": (100, 60), "FR": (None, 40)})
        """
        servo_targets = {}
        for name, (rot_angle, lift_angle) in targets.items():
            leg = self.legs[name]
            if rot_angle is not None:
                a = max(leg.rot.min_angle, min(leg.rot.max_angle, rot_angle))
                servo_targets[leg.rot] = a
            if lift_angle is not None:
                a = max(leg.lift.min_angle, min(leg.lift.max_angle, lift_angle))
                servo_targets[leg.lift] = a

        starts = {s: (s.current_angle if s.current_angle is not None else s.center)
                  for s in servo_targets}

        for i in range(1, steps + 1):
            frac = i / steps
            for s, target in servo_targets.items():
                s.set_angle(starts[s] + (target - starts[s]) * frac, clamp=False)
            time.sleep(delay)

    def center_all(self, **kw):
        for leg in self.legs.values():
            leg.center(**kw)

    def stand(self, **kw):
        """Alias -- calibrated centers are your standing pose."""
        self.center_all(**kw)

    def relax_all(self):
        for leg in self.legs.values():
            leg.relax()

    def shutdown(self):
        self.relax_all()
        self.pi.stop()
