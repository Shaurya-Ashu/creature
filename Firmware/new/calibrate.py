#!/usr/bin/env python3
"""
Stage 2: interactive servo calibration.

Setup (once):
    sudo apt install pigpio python3-pigpio
    sudo pigpiod

Run:
    python3 calibrate.py

Commands per servo:
    +N / -N   nudge angle by N degrees, e.g. +5  -1
    c         mark current angle as CENTER
    lo        mark current angle as MIN safe limit
    hi        mark current angle as MAX safe limit
    inv       toggle inversion
    r         go to raw 90 (uncalibrated reference)
    n / p     save this servo, go to next / previous
    s         save all + exit
    q         exit without writing to disk
"""
import sys
import pigpio
from config import SERVO_CONFIG, save_config

ORDER = ["FL1", "FL2", "FR1", "FR2", "BL1", "BL2", "BR1", "BR2"]


def pulse(angle):
    return int(500 + (angle / 180) * 2000)


def send(pi, cfg, angle):
    """Apply invert before sending, same transform servo.py uses live."""
    physical = 180 - angle if cfg.get("invert", False) else angle
    pi.set_servo_pulsewidth(cfg["gpio"], pulse(physical))


def main():
    pi = pigpio.pi()
    if not pi.connected:
        print("pigpiod not running. Run: sudo pigpiod")
        sys.exit(1)

    idx = 0
    last_cmd = None
    while 0 <= idx < len(ORDER):
        name = ORDER[idx]
        cfg = SERVO_CONFIG[name]
        gpio = cfg["gpio"]
        angle = cfg.get("center", 90)
        send(pi, cfg, angle)

        print(f"\n=== {name} (GPIO {gpio}) === {cfg}")

        while True:
            inv_flag = "INV" if cfg.get("invert", False) else "normal"
            cmd = input(f"[{name}] angle={angle} ({inv_flag}) > ").strip().lower()
            if cmd in ("n", "p", "s", "q"):
                last_cmd = cmd
                break
            elif cmd == "c":
                cfg["center"] = angle
            elif cmd == "lo":
                cfg["min"] = angle
            elif cmd == "hi":
                cfg["max"] = angle
            elif cmd == "inv":
                cfg["invert"] = not cfg.get("invert", False)
                send(pi, cfg, angle)  # re-send same logical angle, now flipped
                print(f"invert -> {cfg['invert']} (watch which way it just moved)")
            elif cmd == "r":
                angle = 90
                send(pi, cfg, angle)
            elif cmd and cmd[0] in "+-":
                try:
                    angle = max(0, min(180, angle + int(cmd)))
                except ValueError:
                    print("bad input")
                    continue
                send(pi, cfg, angle)
            else:
                print("unknown cmd")

        pi.set_servo_pulsewidth(gpio, 0)  # release, avoid holding/heat
        cfg["calibrated"] = True

        if last_cmd == "n":
            idx += 1
        elif last_cmd == "p":
            idx -= 1
        elif last_cmd == "s":
            save_config(SERVO_CONFIG)
            print("saved all, exiting.")
            pi.stop()
            return
        elif last_cmd == "q":
            print("exiting without saving.")
            pi.stop()
            return

    yn = input("\nReached end of list. Save all to disk? (y/n) ").strip().lower()
    if yn == "y":
        save_config(SERVO_CONFIG)
        print("saved.")
    pi.stop()


if __name__ == "__main__":
    main()
