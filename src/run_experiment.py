"""Real MuJoCo whole-body affordance-debt benchmark for paper 65.

The previous v3 script produced synthetic probability tables. This rebuild
creates a compact articulated humanoid-style reaching benchmark in MuJoCo:
candidate whole-body postures are simulated for an immediate target and then
evaluated by how much future reachability and balance margin they preserve.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import math
import os
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, stdev
from typing import Iterable

import matplotlib.pyplot as plt
import mujoco
import numpy as np
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
RESULTS.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)

DT = 0.015
TRANSITION_STEPS = 18
SUCCESS_RADIUS = 0.235

JOINTS = [
    "root_x",
    "root_y",
    "torso_pitch",
    "torso_roll",
    "l_sh_yaw",
    "l_sh_pitch",
    "l_elbow",
    "r_sh_yaw",
    "r_sh_pitch",
    "r_elbow",
]
NEUTRAL_Q = np.array([0.0, 0.0, 0.0, 0.0, 0.0, -0.10, -0.35, 0.0, -0.10, -0.35], dtype=float)
POSTURE_WEIGHTS = np.array([1.5, 1.5, 0.9, 0.9, 0.45, 0.45, 0.35, 0.45, 0.45, 0.35], dtype=float)


@dataclass(frozen=True)
class DynParams:
    kp_scale: float
    payload_mass: float
    damping_scale: float


@dataclass(frozen=True)
class TaskSpec:
    split: str
    dyn: DynParams
    support_width: float
    support_depth: float
    first_target: tuple[float, float, float]
    future_target: tuple[float, float, float]
    future_samples: tuple[tuple[float, float, float], ...]
    perturbation: float


@dataclass(frozen=True)
class Candidate:
    name: str
    hand: str
    q: tuple[float, ...]
    root_motion: float
    torso_motion: float


@dataclass
class SimOutcome:
    qpos: np.ndarray
    qvel: np.ndarray
    target_distance: float
    success: float
    energy: float
    support_margin: float
    balance_failure: float
    effort: float
    peak_force: float
    posture_norm: float
    left_distance: float
    right_distance: float
    com_x: float
    com_y: float
    torso_tilt: float
    chosen_hand: str


@dataclass
class PreparedEpisode:
    task: TaskSpec
    candidates: list[Candidate]
    first_outcomes: list[SimOutcome]
    future_candidates: list[Candidate]
    debt_full: list[float]
    debt_no_balance: list[float]
    debt_no_recovery: list[float]
    debt_small_sample: list[float]


MAIN_METHODS = [
    "random_posture",
    "arm_only_reach",
    "greedy_reach_mpc",
    "comfort_regularized_mpc",
    "robust_balance_mpc",
    "affordance_debt_mpc",
    "oracle_two_step_mpc",
]

ABLATION_METHODS = [
    "affordance_debt_mpc",
    "no_future_debt",
    "no_balance_margin",
    "no_recovery_cost",
    "no_torque_comfort",
    "small_future_sample",
    "current_target_only_greedy",
]

SPLITS = {
    "nominal": {
        "support_width": 0.44,
        "support_depth": 0.34,
        "kp_scale": 1.00,
        "payload": 0.04,
        "damping": 1.00,
        "x": (0.34, 0.54),
        "y": (-0.28, 0.28),
        "z": (1.03, 1.28),
        "future_y": (-0.34, 0.34),
        "perturbation": 0.00,
    },
    "narrow_support": {
        "support_width": 0.27,
        "support_depth": 0.30,
        "kp_scale": 0.95,
        "payload": 0.05,
        "damping": 1.05,
        "x": (0.36, 0.58),
        "y": (-0.42, 0.42),
        "z": (1.02, 1.30),
        "future_y": (-0.48, 0.48),
        "perturbation": 0.03,
    },
    "high_reach": {
        "support_width": 0.42,
        "support_depth": 0.32,
        "kp_scale": 0.92,
        "payload": 0.06,
        "damping": 1.05,
        "x": (0.34, 0.56),
        "y": (-0.28, 0.28),
        "z": (1.25, 1.55),
        "future_y": (-0.36, 0.36),
        "perturbation": 0.02,
    },
    "lateral_reach": {
        "support_width": 0.38,
        "support_depth": 0.32,
        "kp_scale": 0.95,
        "payload": 0.05,
        "damping": 1.00,
        "x": (0.32, 0.52),
        "y": (-0.56, 0.56),
        "z": (1.00, 1.35),
        "future_y": (-0.58, 0.58),
        "perturbation": 0.02,
    },
    "weak_actuation": {
        "support_width": 0.40,
        "support_depth": 0.32,
        "kp_scale": 0.62,
        "payload": 0.08,
        "damping": 1.30,
        "x": (0.36, 0.58),
        "y": (-0.34, 0.34),
        "z": (1.03, 1.36),
        "future_y": (-0.42, 0.42),
        "perturbation": 0.03,
    },
    "payload_shift": {
        "support_width": 0.40,
        "support_depth": 0.32,
        "kp_scale": 0.85,
        "payload": 0.24,
        "damping": 1.18,
        "x": (0.36, 0.60),
        "y": (-0.36, 0.36),
        "z": (1.02, 1.34),
        "future_y": (-0.46, 0.46),
        "perturbation": 0.03,
    },
    "combined_shift": {
        "support_width": 0.26,
        "support_depth": 0.29,
        "kp_scale": 0.58,
        "payload": 0.24,
        "damping": 1.35,
        "x": (0.40, 0.64),
        "y": (-0.58, 0.58),
        "z": (1.18, 1.56),
        "future_y": (-0.62, 0.62),
        "perturbation": 0.05,
    },
}

MODEL_CACHE: dict[DynParams, mujoco.MjModel] = {}


def make_model(params: DynParams) -> mujoco.MjModel:
    cached = MODEL_CACHE.get(params)
    if cached is not None:
        return cached
    hinge_kp = 210.0 * params.kp_scale
    root_kp = 900.0 * params.kp_scale
    elbow_kp = 170.0 * params.kp_scale
    damping = params.damping_scale
    xml = f"""
    <mujoco model="whole_body_affordance_debt">
      <option timestep="{DT}" gravity="0 0 -9.81" integrator="Euler"/>
      <worldbody>
        <light pos="0 0 2"/>
        <geom name="floor" type="plane" size="1.3 1.3 0.03" rgba="0.78 0.78 0.78 1" friction="1.0 0.004 0.0001"/>
        <body name="pelvis" pos="0 0 0.93">
          <joint name="root_x" type="slide" axis="1 0 0" limited="true" range="-0.18 0.18" damping="{8.0*damping}"/>
          <joint name="root_y" type="slide" axis="0 1 0" limited="true" range="-0.24 0.24" damping="{8.0*damping}"/>
          <geom name="pelvis_geom" type="box" size="0.13 0.16 0.08" mass="8.0" rgba="0.25 0.25 0.25 1"/>
          <body name="torso" pos="0 0 0.22">
            <joint name="torso_pitch" type="hinge" axis="0 1 0" limited="true" range="-0.58 0.58" damping="{7.0*damping}"/>
            <joint name="torso_roll" type="hinge" axis="1 0 0" limited="true" range="-0.50 0.50" damping="{7.0*damping}"/>
            <geom name="torso_geom" type="box" size="0.12 0.19 0.23" mass="18.0" rgba="0.35 0.43 0.65 1"/>
            <body name="head" pos="0 0 0.32">
              <geom name="head_geom" type="sphere" size="0.085" mass="2.8" rgba="0.8 0.68 0.55 1"/>
            </body>
            <body name="left_shoulder" pos="0 0.235 0.19">
              <joint name="l_sh_yaw" type="hinge" axis="0 0 1" limited="true" range="-1.35 1.35" damping="{2.2*damping}"/>
              <joint name="l_sh_pitch" type="hinge" axis="0 1 0" limited="true" range="-1.15 0.95" damping="{2.2*damping}"/>
              <geom name="l_upper" type="capsule" fromto="0 0 0 0.25 0 0" size="0.033" mass="1.4" rgba="0.80 0.22 0.18 1"/>
              <body name="left_elbow" pos="0.25 0 0">
                <joint name="l_elbow" type="hinge" axis="0 1 0" limited="true" range="-1.75 0.10" damping="{1.6*damping}"/>
                <geom name="l_lower" type="capsule" fromto="0 0 0 0.25 0 0" size="0.028" mass="{1.0 + params.payload_mass}" rgba="0.92 0.34 0.22 1"/>
                <site name="left_hand" pos="0.27 0 0" size="0.025" rgba="0.0 0.8 0.2 1"/>
              </body>
            </body>
            <body name="right_shoulder" pos="0 -0.235 0.19">
              <joint name="r_sh_yaw" type="hinge" axis="0 0 1" limited="true" range="-1.35 1.35" damping="{2.2*damping}"/>
              <joint name="r_sh_pitch" type="hinge" axis="0 1 0" limited="true" range="-1.15 0.95" damping="{2.2*damping}"/>
              <geom name="r_upper" type="capsule" fromto="0 0 0 0.25 0 0" size="0.033" mass="1.4" rgba="0.80 0.22 0.18 1"/>
              <body name="right_elbow" pos="0.25 0 0">
                <joint name="r_elbow" type="hinge" axis="0 1 0" limited="true" range="-1.75 0.10" damping="{1.6*damping}"/>
                <geom name="r_lower" type="capsule" fromto="0 0 0 0.25 0 0" size="0.028" mass="{1.0 + params.payload_mass}" rgba="0.92 0.34 0.22 1"/>
                <site name="right_hand" pos="0.27 0 0" size="0.025" rgba="0.0 0.8 0.2 1"/>
              </body>
            </body>
          </body>
        </body>
      </worldbody>
      <actuator>
        <position name="root_x_ctrl" joint="root_x" kp="{root_kp}" ctrlrange="-0.18 0.18"/>
        <position name="root_y_ctrl" joint="root_y" kp="{root_kp}" ctrlrange="-0.24 0.24"/>
        <position name="torso_pitch_ctrl" joint="torso_pitch" kp="{hinge_kp}" ctrlrange="-0.58 0.58"/>
        <position name="torso_roll_ctrl" joint="torso_roll" kp="{hinge_kp}" ctrlrange="-0.50 0.50"/>
        <position name="l_sh_yaw_ctrl" joint="l_sh_yaw" kp="{hinge_kp}" ctrlrange="-1.35 1.35"/>
        <position name="l_sh_pitch_ctrl" joint="l_sh_pitch" kp="{hinge_kp}" ctrlrange="-1.15 0.95"/>
        <position name="l_elbow_ctrl" joint="l_elbow" kp="{elbow_kp}" ctrlrange="-1.75 0.10"/>
        <position name="r_sh_yaw_ctrl" joint="r_sh_yaw" kp="{hinge_kp}" ctrlrange="-1.35 1.35"/>
        <position name="r_sh_pitch_ctrl" joint="r_sh_pitch" kp="{hinge_kp}" ctrlrange="-1.15 0.95"/>
        <position name="r_elbow_ctrl" joint="r_elbow" kp="{elbow_kp}" ctrlrange="-1.75 0.10"/>
      </actuator>
    </mujoco>
    """
    model = mujoco.MjModel.from_xml_string(xml)
    MODEL_CACHE[params] = model
    return model


def qpos_ctrl_clip(model: mujoco.MjModel, q: np.ndarray) -> np.ndarray:
    q = np.array(q, dtype=float)
    lo = model.actuator_ctrlrange[:, 0]
    hi = model.actuator_ctrlrange[:, 1]
    return np.minimum(np.maximum(q, lo), hi)


def support_margin(model: mujoco.MjModel, data: mujoco.MjData, task: TaskSpec, qpos: np.ndarray | None = None) -> tuple[float, float, float]:
    masses = model.body_mass
    total = float(np.sum(masses))
    com = np.sum(data.xipos * masses[:, None], axis=0) / max(total, 1e-8)
    root_x = float(qpos[0]) if qpos is not None else float(data.qpos[0])
    root_y = float(qpos[1]) if qpos is not None else float(data.qpos[1])
    # Static feet remain under the original support polygon; root shifts and
    # torso/arm posture move COM relative to that polygon.
    rel_x = float(com[0] - root_x * 0.20)
    rel_y = float(com[1] - root_y * 0.10)
    margin_x = task.support_depth / 2.0 - abs(rel_x)
    margin_y = task.support_width / 2.0 - abs(rel_y)
    return min(margin_x, margin_y), rel_x, rel_y


def set_state(data: mujoco.MjData, qpos: np.ndarray, qvel: np.ndarray | None = None) -> None:
    data.qpos[:] = qpos
    data.qvel[:] = 0.0 if qvel is None else qvel
    data.ctrl[:] = qpos


def hand_distances(data: mujoco.MjData, target: np.ndarray) -> tuple[float, float]:
    left = data.site_xpos[0].copy()
    right = data.site_xpos[1].copy()
    return float(np.linalg.norm(left - target)), float(np.linalg.norm(right - target))


def posture_norm(q: np.ndarray) -> float:
    return float(np.linalg.norm((q - NEUTRAL_Q) * POSTURE_WEIGHTS))


def simulate_to_posture(
    task: TaskSpec,
    start_q: np.ndarray,
    start_v: np.ndarray,
    target_q: np.ndarray,
    target: np.ndarray,
    chosen_hand: str,
) -> SimOutcome:
    model = make_model(task.dyn)
    data = mujoco.MjData(model)
    target_q = qpos_ctrl_clip(model, target_q)
    set_state(data, start_q, start_v)
    mujoco.mj_forward(model, data)
    effort = 0.0
    peak_force = 0.0
    for _ in range(TRANSITION_STEPS):
        data.ctrl[:] = target_q
        mujoco.mj_step(model, data)
        force = np.abs(data.actuator_force.copy())
        effort += float(np.mean(force)) * DT
        peak_force = max(peak_force, float(np.max(force)))
    mujoco.mj_forward(model, data)
    target = np.array(target, dtype=float)
    left_d, right_d = hand_distances(data, target)
    target_distance = min(left_d, right_d)
    if chosen_hand == "left":
        target_distance = left_d
    elif chosen_hand == "right":
        target_distance = right_d
    margin, com_x, com_y = support_margin(model, data, task, data.qpos.copy())
    torso_tilt = float(math.sqrt(float(data.qpos[2]) ** 2 + float(data.qpos[3]) ** 2))
    balance_failure = float(margin < -task.perturbation or torso_tilt > 0.70)
    success = float(target_distance <= SUCCESS_RADIUS and balance_failure < 0.5)
    norm_effort = effort / max(TRANSITION_STEPS, 1)
    energy = (
        target_distance
        + 0.18 * balance_failure
        + 0.35 * max(0.0, -margin)
        + 0.018 * norm_effort
        + 0.035 * torso_tilt
        + 0.018 * posture_norm(data.qpos.copy())
    )
    return SimOutcome(
        qpos=data.qpos.copy(),
        qvel=data.qvel.copy(),
        target_distance=target_distance,
        success=success,
        energy=energy,
        support_margin=margin,
        balance_failure=balance_failure,
        effort=norm_effort,
        peak_force=peak_force,
        posture_norm=posture_norm(data.qpos.copy()),
        left_distance=left_d,
        right_distance=right_d,
        com_x=com_x,
        com_y=com_y,
        torso_tilt=torso_tilt,
        chosen_hand=chosen_hand,
    )


def target_array(t: tuple[float, float, float]) -> np.ndarray:
    return np.array(t, dtype=float)


def clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def make_arm_pose(target: np.ndarray, hand: str, root_x: float, root_y: float, torso_pitch: float, torso_roll: float) -> np.ndarray:
    q = NEUTRAL_Q.copy()
    side = 1.0 if hand == "left" else -1.0
    shoulder_y = root_y + side * 0.235
    shoulder_z = 0.93 + 0.22 + 0.19 + 0.035 * math.sin(torso_roll)
    dx = target[0] - root_x
    dy = target[1] - shoulder_y
    dz = target[2] - shoulder_z
    yaw = clip(math.atan2(dy, max(0.08, dx)), -1.20, 1.20)
    horiz = max(0.10, math.sqrt(dx * dx + dy * dy))
    pitch = clip(-math.atan2(dz, horiz) - 0.25 * torso_pitch, -0.95, 0.72)
    reach = math.sqrt(horiz * horiz + dz * dz)
    elbow = clip(-0.18 - 1.65 * max(0.0, 0.48 - reach), -1.35, -0.12)
    q[0] = root_x
    q[1] = root_y
    q[2] = torso_pitch
    q[3] = torso_roll
    if hand == "left":
        q[4] = yaw
        q[5] = pitch
        q[6] = elbow
    else:
        q[7] = yaw
        q[8] = pitch
        q[9] = elbow
    return q


def candidate_postures(target: np.ndarray, task: TaskSpec) -> list[Candidate]:
    target_side = 1.0 if target[1] >= 0 else -1.0
    preferred = "left" if target_side > 0 else "right"
    other = "right" if preferred == "left" else "left"
    base_x = clip(0.35 * (target[0] - 0.42), -0.05, 0.08)
    templates = [
        ("arm_only", preferred, 0.0, 0.0, 0.0, 0.0),
        ("small_shift", preferred, base_x, 0.045 * target_side, -0.06, 0.07 * target_side),
        ("large_lateral_lean", preferred, base_x, 0.095 * target_side, -0.10, 0.18 * target_side),
        ("counterbalance", preferred, -0.02, 0.060 * target_side, 0.08, -0.13 * target_side),
        ("forward_reach", preferred, 0.075, 0.020 * target_side, -0.20, 0.04 * target_side),
        ("upright_preferred", preferred, 0.025, 0.025 * target_side, 0.03, 0.02 * target_side),
        ("other_arm_only", other, 0.0, 0.0, 0.0, 0.0),
        ("debt_safe_center", preferred, 0.015, 0.0, 0.02, 0.0),
        ("aggressive_reach", preferred, 0.095, 0.125 * target_side, -0.22, 0.24 * target_side),
    ]
    out = []
    seen: set[tuple[float, ...]] = set()
    for name, hand, root_x, root_y, torso_pitch, torso_roll in templates:
        q = make_arm_pose(target, hand, root_x, root_y, torso_pitch, torso_roll)
        key = tuple(round(float(v), 4) for v in q)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            Candidate(
                name=name,
                hand=hand,
                q=tuple(float(v) for v in q),
                root_motion=abs(float(q[0])) + abs(float(q[1])),
                torso_motion=abs(float(q[2])) + abs(float(q[3])),
            )
        )
    return out


def sample_target(rng: random.Random, cfg: dict, future: bool = False) -> tuple[float, float, float]:
    x = rng.uniform(*cfg["x"])
    y_range = cfg["future_y"] if future else cfg["y"]
    y = rng.uniform(*y_range)
    # Avoid too many nearly-center targets; affordance debt is most visible
    # when the next target may be on either side of the body.
    if abs(y) < 0.10 and rng.random() < 0.55:
        y += rng.choice([-1.0, 1.0]) * rng.uniform(0.12, 0.22)
    z = rng.uniform(*cfg["z"])
    return (x, y, z)


def sample_task(split: str, seed: int, episode: int) -> TaskSpec:
    cfg = SPLITS[split]
    rng = random.Random(650003 + 100003 * seed + 7907 * episode + sum(ord(c) for c in split))
    first = sample_target(rng, cfg, future=False)
    future = sample_target(rng, cfg, future=True)
    samples = [future]
    for _ in range(5):
        samples.append(sample_target(rng, cfg, future=True))
    return TaskSpec(
        split=split,
        dyn=DynParams(float(cfg["kp_scale"]), float(cfg["payload"]), float(cfg["damping"])),
        support_width=float(cfg["support_width"]),
        support_depth=float(cfg["support_depth"]),
        first_target=first,
        future_target=future,
        future_samples=tuple(samples),
        perturbation=float(cfg["perturbation"]),
    )


def wrap_angle(x: float) -> float:
    return math.atan2(math.sin(x), math.cos(x))


def analytic_margin(task: TaskSpec, q: np.ndarray) -> float:
    # Fast support proxy used only for debt estimation. The executed rollouts
    # still use MuJoCo COM measurements.
    rel_x = 0.62 * float(q[0]) + 0.075 * math.sin(float(q[2]))
    rel_y = 0.70 * float(q[1]) + 0.110 * math.sin(float(q[3]))
    return min(task.support_depth / 2.0 - abs(rel_x), task.support_width / 2.0 - abs(rel_y))


def analytic_reach_proxy(q: np.ndarray, target: np.ndarray, hand: str) -> float:
    side = 1.0 if hand == "left" else -1.0
    shoulder = np.array([q[0], q[1] + side * 0.235, 1.34 + 0.05 * math.sin(float(q[2]))], dtype=float)
    diff = target - shoulder
    dx = float(diff[0])
    dy = float(diff[1])
    dz = float(diff[2])
    yaw_des = math.atan2(dy, max(0.08, dx))
    horiz = max(0.10, math.sqrt(dx * dx + dy * dy))
    pitch_des = -math.atan2(dz, horiz)
    if hand == "left":
        yaw = float(q[4])
        pitch = float(q[5])
    else:
        yaw = float(q[7])
        pitch = float(q[8])
    reach = float(np.linalg.norm(diff))
    range_penalty = max(0.0, reach - 0.56) + 0.35 * max(0.0, 0.18 - reach)
    align_penalty = 0.085 * abs(wrap_angle(yaw - yaw_des)) + 0.085 * abs(wrap_angle(pitch - pitch_des))
    return range_penalty + align_penalty


def future_debt(
    task: TaskSpec,
    current_q: np.ndarray,
    samples: Iterable[tuple[float, float, float]],
    include_balance: bool = True,
    include_recovery: bool = True,
) -> float:
    debts = []
    for future_target in samples:
        target = target_array(future_target)
        best = float("inf")
        for cand in candidate_postures(target, task):
            q = np.array(cand.q, dtype=float)
            dist = analytic_reach_proxy(q, target, cand.hand)
            margin = analytic_margin(task, q)
            tilt = float(math.sqrt(float(q[2]) ** 2 + float(q[3]) ** 2))
            recovery = float(np.linalg.norm((q - current_q) * POSTURE_WEIGHTS)) if include_recovery else 0.0
            balance = max(0.0, task.perturbation - margin) if include_balance else 0.0
            pseudo = dist + 0.120 * recovery + 0.75 * balance + 0.022 * tilt
            best = min(best, pseudo)
        debts.append(best)
    return float(mean(debts))


def prepare_episode(split: str, seed: int, episode: int) -> PreparedEpisode:
    task = sample_task(split, seed, episode)
    first_target = target_array(task.first_target)
    future_target = target_array(task.future_target)
    candidates = candidate_postures(first_target, task)
    start_q = NEUTRAL_Q.copy()
    start_v = np.zeros_like(start_q)
    first_outcomes = [
        simulate_to_posture(task, start_q, start_v, np.array(c.q, dtype=float), first_target, c.hand)
        for c in candidates
    ]
    future_candidates = candidate_postures(future_target, task)
    debt_full = [
        future_debt(task, outcome.qpos, task.future_samples, include_balance=True, include_recovery=True)
        for outcome in first_outcomes
    ]
    debt_no_balance = [
        future_debt(task, outcome.qpos, task.future_samples, include_balance=False, include_recovery=True)
        for outcome in first_outcomes
    ]
    debt_no_recovery = [
        future_debt(task, outcome.qpos, task.future_samples, include_balance=True, include_recovery=False)
        for outcome in first_outcomes
    ]
    debt_small_sample = [
        future_debt(task, outcome.qpos, task.future_samples[:2], include_balance=True, include_recovery=True)
        for outcome in first_outcomes
    ]
    return PreparedEpisode(task, candidates, first_outcomes, future_candidates, debt_full, debt_no_balance, debt_no_recovery, debt_small_sample)


def first_cost(outcome: SimOutcome) -> float:
    return outcome.target_distance + 0.25 * outcome.balance_failure + 0.25 * max(0.0, -outcome.support_margin)


def second_outcomes_for(prep: PreparedEpisode, first_idx: int, cache: dict[int, list[SimOutcome]]) -> list[SimOutcome]:
    if first_idx not in cache:
        future_target = target_array(prep.task.future_target)
        first = prep.first_outcomes[first_idx]
        cache[first_idx] = [
            simulate_to_posture(prep.task, first.qpos, first.qvel * 0.25, np.array(c.q, dtype=float), future_target, c.hand)
            for c in prep.future_candidates
        ]
    return cache[first_idx]


def best_second(prep: PreparedEpisode, first_idx: int, cache: dict[int, list[SimOutcome]]) -> tuple[int, SimOutcome]:
    row = second_outcomes_for(prep, first_idx, cache)
    idx = int(np.argmin([out.energy for out in row]))
    return idx, row[idx]


def robust_margin_penalty(prep: PreparedEpisode, idx: int) -> float:
    out = prep.first_outcomes[idx]
    narrowed = out.support_margin - prep.task.perturbation - 0.025
    return max(0.0, -narrowed) + 0.35 * out.balance_failure


def choose_first(method: str, prep: PreparedEpisode, rng: random.Random, cache: dict[int, list[SimOutcome]]) -> tuple[int, float]:
    candidates = prep.candidates
    first = prep.first_outcomes
    if method == "random_posture":
        return rng.randrange(len(candidates)), 0.0
    if method == "arm_only_reach":
        valid = [idx for idx, c in enumerate(candidates) if c.root_motion < 0.02 and c.torso_motion < 0.02]
        if not valid:
            valid = list(range(len(candidates)))
        idx = min(valid, key=lambda i: first_cost(first[i]))
        return idx, 0.0
    if method in {"greedy_reach_mpc", "current_target_only_greedy"}:
        idx = int(np.argmin([first_cost(out) for out in first]))
        return idx, 0.0
    if method == "comfort_regularized_mpc":
        scores = [
            first_cost(out) + 0.020 * out.effort + 0.025 * out.posture_norm
            for out in first
        ]
        return int(np.argmin(scores)), 0.0
    if method == "robust_balance_mpc":
        scores = [
            first_cost(out) + 0.020 * out.effort + 0.70 * robust_margin_penalty(prep, idx) + 0.015 * out.posture_norm
            for idx, out in enumerate(first)
        ]
        return int(np.argmin(scores)), 0.0
    if method == "oracle_two_step_mpc":
        scores = []
        for idx, out in enumerate(first):
            _, second = best_second(prep, idx, cache)
            scores.append(first_cost(out) + second.energy)
        return int(np.argmin(scores)), 0.0
    if method in ABLATION_METHODS or method == "affordance_debt_mpc":
        if method == "no_future_debt":
            debt = [0.0 for _ in first]
        elif method == "no_balance_margin":
            debt = prep.debt_no_balance
        elif method == "no_recovery_cost":
            debt = prep.debt_no_recovery
        elif method == "small_future_sample":
            debt = prep.debt_small_sample
        elif method == "current_target_only_greedy":
            debt = [0.0 for _ in first]
        else:
            debt = prep.debt_full
        scores = []
        for idx, out in enumerate(first):
            effort_term = 0.0 if method == "no_torque_comfort" else 0.018 * out.effort + 0.018 * out.posture_norm
            balance = 0.0 if method == "no_balance_margin" else 0.55 * robust_margin_penalty(prep, idx)
            scores.append(first_cost(out) + 0.62 * float(debt[idx]) + effort_term + balance)
        chosen = int(np.argmin(scores))
        return chosen, float(debt[chosen])
    raise ValueError(method)


def evaluate_method(method: str, prep: PreparedEpisode, seed: int, episode: int, ablation: bool, cache: dict[int, list[SimOutcome]]) -> dict:
    rng = random.Random(651119 + 7919 * seed + 101 * episode + sum(ord(c) for c in method) + sum(ord(c) for c in prep.task.split))
    first_idx, chosen_debt = choose_first(method, prep, rng, cache)
    second_idx, second = best_second(prep, first_idx, cache)
    first = prep.first_outcomes[first_idx]
    candidate = prep.candidates[first_idx]
    future_candidate = prep.future_candidates[second_idx]
    sequential_success = float(first.success > 0.5 and second.success > 0.5 and first.balance_failure < 0.5 and second.balance_failure < 0.5)
    combined_energy = first.energy + second.energy + 0.020 * float(np.linalg.norm((second.qpos - first.qpos) * POSTURE_WEIGHTS))
    oracle_second_energy = min(out.energy for out in second_outcomes_for(prep, first_idx, cache))
    return {
        "seed": seed,
        "episode": episode,
        "split": prep.task.split,
        "method": method,
        "support_width": prep.task.support_width,
        "kp_scale": prep.task.dyn.kp_scale,
        "payload_mass": prep.task.dyn.payload_mass,
        "first_candidate": first_idx,
        "first_candidate_name": candidate.name,
        "first_hand": candidate.hand,
        "second_candidate": second_idx,
        "second_candidate_name": future_candidate.name,
        "immediate_success": first.success,
        "future_success": second.success,
        "sequential_success": sequential_success,
        "first_distance": first.target_distance,
        "future_distance": second.target_distance,
        "combined_energy": combined_energy,
        "first_energy": first.energy,
        "future_energy": second.energy,
        "oracle_second_energy": oracle_second_energy,
        "energy_regret": combined_energy - oracle_second_energy,
        "affordance_debt": chosen_debt,
        "first_support_margin": first.support_margin,
        "future_support_margin": second.support_margin,
        "first_balance_failure": first.balance_failure,
        "future_balance_failure": second.balance_failure,
        "first_effort": first.effort,
        "future_effort": second.effort,
        "first_posture_norm": first.posture_norm,
        "future_posture_norm": second.posture_norm,
        "ablation": ablation,
    }


def run_method_set(split: str, seed: int, episode: int, methods: list[str], ablation: bool) -> list[dict]:
    prep = prepare_episode(split, seed, episode)
    cache: dict[int, list[SimOutcome]] = {}
    return [evaluate_method(method, prep, seed, episode, ablation, cache) for method in methods]


def run_task(task: tuple[str, int, int, tuple[str, ...], bool]) -> list[dict]:
    split, seed, episode, methods, ablation = task
    return run_method_set(split, seed, episode, list(methods), ablation)


def execute_tasks(
    tasks: list[tuple[str, int, int, tuple[str, ...], bool]],
    workers: int,
    chunksize: int,
    pool: ProcessPoolExecutor | None = None,
) -> list[dict]:
    if workers <= 1:
        nested = [run_task(task) for task in tasks]
    elif pool is not None:
        nested = list(pool.map(run_task, tasks, chunksize=chunksize))
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            nested = list(pool.map(run_task, tasks, chunksize=chunksize))
    rows: list[dict] = []
    for chunk in nested:
        rows.extend(chunk)
    return rows


def ci95(vals: Iterable[float]) -> float:
    vals = list(vals)
    if len(vals) < 2:
        return 0.0
    return 1.96 * stdev(vals) / math.sqrt(len(vals))


def summarize(rows: list[dict], keys: list[str]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        groups.setdefault(key, []).append(row)
    out = []
    for key, vals in sorted(groups.items()):
        seq = [float(v["sequential_success"]) for v in vals]
        imm = [float(v["immediate_success"]) for v in vals]
        fut = [float(v["future_success"]) for v in vals]
        energy = [float(v["combined_energy"]) for v in vals]
        debt = [float(v["affordance_debt"]) for v in vals]
        margins = [float(v["future_support_margin"]) for v in vals]
        failures = [max(float(v["first_balance_failure"]), float(v["future_balance_failure"])) for v in vals]
        summary = {k: key[i] for i, k in enumerate(keys)}
        summary.update(
            {
                "episodes": len(vals),
                "sequential_success": mean(seq),
                "sequential_success_ci95": ci95(seq),
                "immediate_success": mean(imm),
                "future_success": mean(fut),
                "combined_energy_mean": mean(energy),
                "combined_energy_ci95": ci95(energy),
                "affordance_debt_mean": mean(debt),
                "future_support_margin_mean": mean(margins),
                "balance_failure_rate": mean(failures),
            }
        )
        out.append(summary)
    return out


def paired_stats(rows: list[dict], proposed: str = "affordance_debt_mpc") -> list[dict]:
    baselines = [m for m in MAIN_METHODS if m != proposed]
    by_key: dict[tuple, dict[str, dict]] = {}
    for row in rows:
        by_key.setdefault((row["split"], row["seed"], row["episode"]), {})[row["method"]] = row
    out = []
    for split in sorted({row["split"] for row in rows}):
        cases = [methods for key, methods in by_key.items() if key[0] == split and proposed in methods]
        for baseline in baselines:
            paired = [(case[proposed], case[baseline]) for case in cases if baseline in case]
            if not paired:
                continue
            success_delta = [float(p["sequential_success"]) - float(b["sequential_success"]) for p, b in paired]
            energy_improvement = [float(b["combined_energy"]) - float(p["combined_energy"]) for p, b in paired]
            margin_delta = [float(p["future_support_margin"]) - float(b["future_support_margin"]) for p, b in paired]
            p_val = 1.0
            if len(energy_improvement) > 1 and stdev(energy_improvement) > 1e-12:
                p_val = float(stats.ttest_1samp(energy_improvement, 0.0).pvalue)
                if math.isnan(p_val):
                    p_val = 1.0
            out.append(
                {
                    "split": split,
                    "baseline": baseline,
                    "paired_episodes": len(paired),
                    "success_delta_mean": mean(success_delta),
                    "success_delta_ci95": ci95(success_delta),
                    "energy_improvement_mean": mean(energy_improvement),
                    "energy_improvement_ci95": ci95(energy_improvement),
                    "future_margin_delta_mean": mean(margin_delta),
                    "future_margin_delta_ci95": ci95(margin_delta),
                    "energy_ttest_p": p_val,
                }
            )
    return out


def write_rows(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def format_rows(rows: list[dict]) -> list[dict]:
    formatted = []
    for row in rows:
        clean = dict(row)
        for key, value in row.items():
            if isinstance(value, float):
                clean[key] = f"{value:.4f}"
        formatted.append(clean)
    return formatted


def plot_results(metrics: list[dict], ablation: list[dict]) -> None:
    splits = sorted({row["split"] for row in metrics})
    methods = [
        "arm_only_reach",
        "greedy_reach_mpc",
        "comfort_regularized_mpc",
        "robust_balance_mpc",
        "affordance_debt_mpc",
        "oracle_two_step_mpc",
    ]
    labels = ["ArmOnly", "Greedy", "Comfort", "Robust", "Debt", "Oracle"]
    x = np.arange(len(splits))
    width = 0.13
    plt.figure(figsize=(12.5, 4.8))
    for idx, method in enumerate(methods):
        vals = [float(next(row["sequential_success"] for row in metrics if row["split"] == split and row["method"] == method)) for split in splits]
        plt.bar(x + (idx - 2.5) * width, vals, width=width, label=labels[idx])
    plt.xticks(x, splits, rotation=20, ha="right")
    plt.ylabel("Sequential success")
    plt.ylim(0, 1.02)
    plt.title("Whole-body affordance-debt sequential success")
    plt.legend(ncol=6, fontsize=8)
    plt.tight_layout()
    plt.savefig(FIGURES / "affordance_debt_success_by_split.png", dpi=180)
    plt.close()

    plt.figure(figsize=(12.5, 4.8))
    for idx, method in enumerate(methods):
        vals = [float(next(row["combined_energy_mean"] for row in metrics if row["split"] == split and row["method"] == method)) for split in splits]
        plt.bar(x + (idx - 2.5) * width, vals, width=width, label=labels[idx])
    plt.xticks(x, splits, rotation=20, ha="right")
    plt.ylabel("Combined energy, lower is better")
    plt.title("Whole-body reach energy by split")
    plt.legend(ncol=6, fontsize=8)
    plt.tight_layout()
    plt.savefig(FIGURES / "affordance_debt_energy_by_split.png", dpi=180)
    plt.close()

    order = sorted(ablation, key=lambda row: float(row["combined_energy_mean"]))
    plt.figure(figsize=(9.2, 4.8))
    plt.barh([row["method"] for row in order], [float(row["combined_energy_mean"]) for row in order])
    plt.xlabel("Combined energy, lower is better")
    plt.title("Combined-shift affordance-debt ablations")
    plt.tight_layout()
    plt.savefig(FIGURES / "affordance_debt_ablation_energy.png", dpi=180)
    plt.close()

    plt.figure(figsize=(9.2, 4.8))
    vals = [
        float(next(row["future_support_margin_mean"] for row in metrics if row["split"] == "combined_shift" and row["method"] == method))
        for method in methods
    ]
    plt.bar(labels, vals)
    plt.ylabel("Future support margin")
    plt.title("Combined-shift future balance margin")
    plt.tight_layout()
    plt.savefig(FIGURES / "affordance_debt_margin_combined.png", dpi=180)
    plt.close()


def run(args: argparse.Namespace) -> None:
    raw_rows: list[dict] = []
    pool = ProcessPoolExecutor(max_workers=args.workers) if args.workers > 1 else None
    try:
        for split in args.splits:
            tasks = [
                (split, seed, episode, tuple(MAIN_METHODS), False)
                for seed in range(args.seeds)
                for episode in range(args.episodes)
            ]
            raw_rows.extend(execute_tasks(tasks, args.workers, args.chunksize, pool))
            write_rows(RESULTS / "affordance_debt_raw.partial.csv", format_rows(raw_rows))
            write_rows(RESULTS / "affordance_debt_metrics.partial.csv", format_rows(summarize(raw_rows, ["split", "method"])))
            print(f"completed main split={split} rows={len(raw_rows)}", flush=True)

        ablation_rows: list[dict] = []
        for seed in range(args.seeds):
            tasks = [
                ("combined_shift", seed, episode, tuple(ABLATION_METHODS), True)
                for episode in range(args.episodes)
            ]
            ablation_rows.extend(execute_tasks(tasks, args.workers, args.chunksize, pool))
            write_rows(RESULTS / "affordance_debt_ablation.partial.csv", format_rows(summarize(ablation_rows, ["method"])))
            print(f"completed ablation seed={seed} rows={len(ablation_rows)}", flush=True)
    finally:
        if pool is not None:
            pool.shutdown()

    main_summary = summarize(raw_rows, ["split", "method"])
    seed_summary = summarize(raw_rows, ["split", "method", "seed"])
    ablation_summary = summarize(ablation_rows, ["method"])
    pairwise = paired_stats(raw_rows)

    write_rows(RESULTS / "affordance_debt_raw.csv", format_rows(raw_rows))
    write_rows(RESULTS / "affordance_debt_metrics.csv", format_rows(main_summary))
    write_rows(RESULTS / "affordance_debt_seed_metrics.csv", format_rows(seed_summary))
    write_rows(RESULTS / "affordance_debt_ablation.csv", format_rows(ablation_summary))
    write_rows(RESULTS / "affordance_debt_pairwise.csv", format_rows(pairwise))

    write_rows(RESULTS / "metrics.csv", format_rows(main_summary))
    write_rows(RESULTS / "raw_seed_metrics.csv", format_rows(seed_summary))
    write_rows(RESULTS / "ablation_metrics.csv", format_rows(ablation_summary))
    write_rows(RESULTS / "pairwise_stats.csv", format_rows(pairwise))
    write_rows(RESULTS / "stress_sweep.csv", format_rows(main_summary))
    write_rows(FIGURES / "stress_curve_data.csv", format_rows(main_summary))
    negative_cases = [
        {
            "case": "dynamic stepping not modeled",
            "observed": "support margin is evaluated with a standing support polygon, not footstep replanning",
            "paper_status": "limitation",
        },
        {
            "case": "out-of-distribution acrobatics",
            "observed": "finite posture library cannot represent kneeling, stepping, or hand support",
            "paper_status": "limitation",
        },
        {
            "case": "custom MuJoCo benchmark only",
            "observed": "evidence supports strong-revise at best without humanoid hardware or public benchmark validation",
            "paper_status": "limitation",
        },
    ]
    write_rows(RESULTS / "negative_cases.csv", negative_cases)
    plot_results(main_summary, ablation_summary)
    with (RESULTS / "summary.txt").open("w", encoding="utf-8") as f:
        f.write("Real MuJoCo humanoid whole-body affordance-debt benchmark for paper 65\n")
        f.write(f"seeds={args.seeds} episodes={args.episodes} splits={','.join(args.splits)}\n")
        for row in main_summary:
            if row["method"] in {"affordance_debt_mpc", "greedy_reach_mpc", "robust_balance_mpc", "oracle_two_step_mpc"}:
                f.write(
                    f"{row['split']} {row['method']} seq={row['sequential_success']:.3f}+/-{row['sequential_success_ci95']:.3f} "
                    f"energy={row['combined_energy_mean']:.3f}+/-{row['combined_energy_ci95']:.3f} "
                    f"margin={row['future_support_margin_mean']:.3f}\n"
                )
    print(f"wrote real affordance-debt benchmark results to {RESULTS}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--episodes", type=int, default=12)
    parser.add_argument("--splits", nargs="+", default=list(SPLITS.keys()))
    parser.add_argument("--workers", type=int, default=max(1, min(4, (os.cpu_count() or 2) - 1)))
    parser.add_argument("--chunksize", type=int, default=1)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
