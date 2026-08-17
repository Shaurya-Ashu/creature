#!/usr/bin/env python3
"""
GUI for posing the robot by hand.

- Drag sliders to set each leg's rotation/lift angle -- moves the real
  servo live so you can see the effect immediately.
- Save the current pose as a named "pattern".
- Chain patterns into a named "action" (ordered sequence, each step
  holds for N seconds before the next), then play it back.

Run (needs sudo pigpiod running first):
    python3 gui.py

If tkinter isn't installed:
    sudo apt install python3-tk

Storage (created automatically, plain JSON, editable by hand too):
    patterns.json -- {name: {"FL": [rot, lift], "FR": [...], ...}}
    actions.json  -- {name: [{"pattern": name, "delay": seconds}, ...]}
"""
import json
import os
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from robot import Robot
from config import SERVO_CONFIG

LEG_NAMES = ["FL", "FR", "BL", "BR"]
PATTERNS_PATH = os.path.join(os.path.dirname(__file__), "patterns.json")
ACTIONS_PATH = os.path.join(os.path.dirname(__file__), "actions.json")


def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


class RobotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Quadruped Pose / Pattern / Action Builder")

        try:
            self.robot = Robot()
        except Exception as e:
            messagebox.showerror("Connection failed", str(e))
            root.destroy()
            raise

        self.patterns = load_json(PATTERNS_PATH)
        self.actions = load_json(ACTIONS_PATH)
        self.playing = False
        self._pending_steps = []  # steps being built for a new action
        self.sliders = {}         # (leg, joint) -> (Scale, DoubleVar)

        self._build_ui()
        self._go_to_centers()

    # ---------- UI ----------

    def _build_ui(self):
        legs_frame = ttk.Frame(self.root, padding=10)
        legs_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

        for col, leg in enumerate(LEG_NAMES):
            frame = ttk.LabelFrame(legs_frame, text=leg, padding=8)
            frame.grid(row=0, column=col, padx=6, sticky="n")
            self._add_slider(frame, leg, "rotation", 0)
            self._add_slider(frame, leg, "lift", 1)

        pat_frame = ttk.LabelFrame(self.root, text="Patterns (single pose)", padding=8)
        pat_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.pattern_name_var = tk.StringVar()
        ttk.Entry(pat_frame, textvariable=self.pattern_name_var, width=20).grid(row=0, column=0, padx=4)
        ttk.Button(pat_frame, text="Save current pose",
                   command=self._save_pattern).grid(row=0, column=1, padx=4)

        self.pattern_list = tk.Listbox(pat_frame, height=8, width=28)
        self.pattern_list.grid(row=1, column=0, columnspan=2, pady=6)
        self._refresh_pattern_list()

        btn_row = ttk.Frame(pat_frame)
        btn_row.grid(row=2, column=0, columnspan=2)
        ttk.Button(btn_row, text="Load", command=self._load_selected_pattern).grid(row=0, column=0, padx=3)
        ttk.Button(btn_row, text="Delete", command=self._delete_selected_pattern).grid(row=0, column=1, padx=3)
        ttk.Button(btn_row, text="Add to action", command=self._add_pattern_to_action).grid(row=0, column=2, padx=3)

        act_frame = ttk.LabelFrame(self.root, text="Actions (sequence of patterns)", padding=8)
        act_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.action_name_var = tk.StringVar()
        ttk.Entry(act_frame, textvariable=self.action_name_var, width=20).grid(row=0, column=0, padx=4)
        ttk.Button(act_frame, text="Save as action",
                   command=self._save_action).grid(row=0, column=1, padx=4)

        ttk.Label(act_frame, text="Steps in new action:").grid(row=1, column=0, columnspan=2, sticky="w")
        self.steps_list = tk.Listbox(act_frame, height=6, width=28)
        self.steps_list.grid(row=2, column=0, columnspan=2, pady=4)

        step_btns = ttk.Frame(act_frame)
        step_btns.grid(row=3, column=0, columnspan=2)
        ttk.Button(step_btns, text="Remove step", command=self._remove_step).grid(row=0, column=0, padx=3)
        ttk.Button(step_btns, text="Clear steps", command=self._clear_steps).grid(row=0, column=1, padx=3)

        ttk.Label(act_frame, text="Saved actions:").grid(row=4, column=0, columnspan=2, sticky="w")
        self.action_list = tk.Listbox(act_frame, height=6, width=28)
        self.action_list.grid(row=5, column=0, columnspan=2, pady=4)
        self._refresh_action_list()

        act_btns = ttk.Frame(act_frame)
        act_btns.grid(row=6, column=0, columnspan=2)
        ttk.Button(act_btns, text="Play", command=self._play_selected_action).grid(row=0, column=0, padx=3)
        ttk.Button(act_btns, text="Delete", command=self._delete_selected_action).grid(row=0, column=1, padx=3)

        bottom = ttk.Frame(self.root, padding=10)
        bottom.grid(row=2, column=0, columnspan=2)
        ttk.Button(bottom, text="Center All", command=self._go_to_centers).grid(row=0, column=0, padx=6)
        ttk.Button(bottom, text="Relax All", command=self._relax_all).grid(row=0, column=1, padx=6)

        self.status_var = tk.StringVar(value="ready")
        ttk.Label(self.root, textvariable=self.status_var).grid(row=3, column=0, columnspan=2, pady=4)

    def _add_slider(self, parent, leg, joint, row):
        cfg = SERVO_CONFIG[leg + ("1" if joint == "rotation" else "2")]
        var = tk.DoubleVar(value=cfg["center"])
        ttk.Label(parent, text=f"{joint} ({cfg['min']}-{cfg['max']})").grid(row=row * 2, column=0)
        scale = tk.Scale(parent, from_=cfg["min"], to=cfg["max"], orient="horizontal",
                          variable=var, length=160,
                          command=lambda val, l=leg, j=joint: self._on_slider(l, j, val))
        scale.grid(row=row * 2 + 1, column=0, pady=4)
        self.sliders[(leg, joint)] = (scale, var)

    # ---------- live slider control ----------

    def _on_slider(self, leg, joint, val):
        if self.playing:
            return  # don't fight an action that's currently playing
        angle = float(val)
        servo = self.robot.legs[leg].rot if joint == "rotation" else self.robot.legs[leg].lift
        servo.set_angle(angle)
        self.status_var.set(f"{leg} {joint} -> {angle:.0f} deg")

    def _current_pose(self):
        pose = {}
        for leg in LEG_NAMES:
            _, rot_var = self.sliders[(leg, "rotation")]
            _, lift_var = self.sliders[(leg, "lift")]
            pose[leg] = [rot_var.get(), lift_var.get()]
        return pose

    def _apply_pose(self, pose, steps=30, delay=0.02):
        """Moves hardware (safe from any thread) then schedules slider
        sync back on the main thread via root.after."""
        targets = {leg: (pose[leg][0], pose[leg][1]) for leg in pose}
        self.robot.move_joints(targets, steps=steps, delay=delay)
        self.root.after(0, lambda: self._sync_sliders(pose))

    def _sync_sliders(self, pose):
        for leg in pose:
            self.sliders[(leg, "rotation")][1].set(pose[leg][0])
            self.sliders[(leg, "lift")][1].set(pose[leg][1])

    def _go_to_centers(self):
        pose = {leg: [self.robot.legs[leg].rot.center, self.robot.legs[leg].lift.center]
                for leg in LEG_NAMES}
        self._apply_pose(pose)
        self.status_var.set("centered")

    def _relax_all(self):
        self.robot.relax_all()
        self.status_var.set("relaxed")

    # ---------- patterns ----------

    def _save_pattern(self):
        name = self.pattern_name_var.get().strip()
        if not name:
            messagebox.showwarning("Name needed", "Type a pattern name first.")
            return
        self.patterns[name] = self._current_pose()
        save_json(PATTERNS_PATH, self.patterns)
        self._refresh_pattern_list()
        self.status_var.set(f"saved pattern '{name}'")

    def _refresh_pattern_list(self):
        self.pattern_list.delete(0, tk.END)
        for name in self.patterns:
            self.pattern_list.insert(tk.END, name)

    def _selected_pattern_name(self):
        sel = self.pattern_list.curselection()
        return self.pattern_list.get(sel[0]) if sel else None

    def _load_selected_pattern(self):
        name = self._selected_pattern_name()
        if not name:
            return
        self._apply_pose(self.patterns[name])
        self.status_var.set(f"loaded pattern '{name}'")

    def _delete_selected_pattern(self):
        name = self._selected_pattern_name()
        if not name:
            return
        del self.patterns[name]
        save_json(PATTERNS_PATH, self.patterns)
        self._refresh_pattern_list()
        self.status_var.set(f"deleted pattern '{name}'")

    # ---------- actions ----------

    def _add_pattern_to_action(self):
        name = self._selected_pattern_name()
        if not name:
            messagebox.showwarning("Pick a pattern", "Select a pattern from the list first.")
            return
        delay = simpledialog.askfloat("Step hold time",
                                       f"Seconds to hold after moving to '{name}':",
                                       initialvalue=1.0, minvalue=0.0)
        if delay is None:
            return
        self._pending_steps.append({"pattern": name, "delay": delay})
        self.steps_list.insert(tk.END, f"{name}  (+{delay}s)")

    def _remove_step(self):
        sel = self.steps_list.curselection()
        if not sel:
            return
        idx = sel[0]
        self.steps_list.delete(idx)
        del self._pending_steps[idx]

    def _clear_steps(self):
        self.steps_list.delete(0, tk.END)
        self._pending_steps = []

    def _save_action(self):
        name = self.action_name_var.get().strip()
        if not name:
            messagebox.showwarning("Name needed", "Type an action name first.")
            return
        if not self._pending_steps:
            messagebox.showwarning("No steps", "Add at least one pattern step first.")
            return
        self.actions[name] = list(self._pending_steps)
        save_json(ACTIONS_PATH, self.actions)
        self._refresh_action_list()
        self._clear_steps()
        self.action_name_var.set("")
        self.status_var.set(f"saved action '{name}'")

    def _refresh_action_list(self):
        self.action_list.delete(0, tk.END)
        for name in self.actions:
            self.action_list.insert(tk.END, name)

    def _selected_action_name(self):
        sel = self.action_list.curselection()
        return self.action_list.get(sel[0]) if sel else None

    def _delete_selected_action(self):
        name = self._selected_action_name()
        if not name:
            return
        del self.actions[name]
        save_json(ACTIONS_PATH, self.actions)
        self._refresh_action_list()
        self.status_var.set(f"deleted action '{name}'")

    def _play_selected_action(self):
        name = self._selected_action_name()
        if not name or self.playing:
            return
        steps = self.actions[name]
        threading.Thread(target=self._play_action_thread, args=(name, steps), daemon=True).start()

    def _play_action_thread(self, name, steps):
        self.playing = True
        self.status_var.set(f"playing '{name}'...")
        for step in steps:
            pose = self.patterns.get(step["pattern"])
            if pose is None:
                continue
            self._apply_pose(pose)
            time.sleep(step["delay"])
        self.playing = False
        self.status_var.set(f"finished '{name}'")


def main():
    root = tk.Tk()
    try:
        app = RobotGUI(root)
    except Exception:
        return

    def on_close():
        try:
            app.robot.shutdown()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
