#!/usr/bin/env python3
"""Extract reusable whole-body motion signals from a BlendCap BVH.

This intentionally does not retarget human limbs onto the EvoWild S rig.
It produces normalized body-level channels for later hybrid experiments:
root travel, vertical COM/hips motion, pelvis rotation, torso pitch/roll,
and a left/right leg phase proxy.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean


def parse_bvh(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    channels = []
    stack = []
    current = None
    motion_index = None
    fps = None
    frames_declared = None

    for i, raw in enumerate(lines):
        line = raw.strip()
        if line.startswith("ROOT ") or line.startswith("JOINT "):
            current = line.split(None, 1)[1]
            stack.append(current)
        elif line == "}":
            if stack:
                stack.pop()
                current = stack[-1] if stack else None
        elif line.startswith("CHANNELS "):
            parts = line.split()
            count = int(parts[1])
            names = parts[2:2+count]
            for name in names:
                channels.append((current, name))
        elif line == "MOTION":
            motion_index = i
            break

    if motion_index is None:
        raise ValueError("BVH has no MOTION section")

    j = motion_index + 1
    if lines[j].strip().startswith("Frames:"):
        frames_declared = int(lines[j].split(":", 1)[1].strip())
        j += 1
    if lines[j].strip().startswith("Frame Time:"):
        frame_time = float(lines[j].split(":", 1)[1].strip())
        fps = 1.0 / frame_time if frame_time > 0 else 0.0
        j += 1

    frames = []
    for raw in lines[j:]:
        raw = raw.strip()
        if not raw:
            continue
        vals = [float(x) for x in raw.split()]
        if len(vals) != len(channels):
            raise ValueError(f"frame has {len(vals)} values, expected {len(channels)}")
        frames.append(vals)

    return channels, frames, fps, frames_declared


def series(channels, frames, joint, channel):
    try:
        idx = channels.index((joint, channel))
    except ValueError:
        return None
    return [f[idx] for f in frames]


def centered(values):
    if not values:
        return []
    m = mean(values)
    return [v - m for v in values]


def normalize(values):
    if not values:
        return []
    c = centered(values)
    peak = max(abs(v) for v in c) or 1.0
    return [v / peak for v in c]


def stats(values):
    if not values:
        return None
    lo, hi = min(values), max(values)
    return {
        "min": lo,
        "max": hi,
        "range": hi - lo,
        "mean": mean(values),
    }


def dominant_period(values, fps):
    """Crude autocorrelation period suitable for short gait clips."""
    if not values or len(values) < 12 or not fps:
        return None
    x = centered(values)
    denom = sum(v*v for v in x)
    if denom <= 1e-12:
        return None

    min_lag = max(2, int(fps * 0.20))
    max_lag = min(len(x)//2, int(fps * 1.20))
    best = None
    for lag in range(min_lag, max_lag + 1):
        num = sum(x[i] * x[i+lag] for i in range(len(x)-lag))
        den_a = sum(x[i]**2 for i in range(len(x)-lag))
        den_b = sum(x[i+lag]**2 for i in range(len(x)-lag))
        den = math.sqrt(max(den_a * den_b, 1e-12))
        corr = num / den
        if best is None or corr > best[1]:
            best = (lag, corr)
    if best is None:
        return None
    lag, corr = best
    return {
        "lag_frames": lag,
        "period_seconds": lag / fps,
        "cycles_per_second": fps / lag,
        "autocorrelation": corr,
    }


def avg_series(parts):
    usable = [p for p in parts if p]
    if not usable:
        return []
    n = min(len(p) for p in usable)
    return [sum(p[i] for p in usable) / len(usable) for i in range(n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bvh")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.bvh)
    channels, frames, fps, declared = parse_bvh(path)

    def s(j, c):
        return series(channels, frames, j, c)

    root_x = s("Root", "Xposition") or []
    root_y = s("Root", "Yposition") or []
    root_z = s("Root", "Zposition") or []
    hips_y = s("Hips", "Yposition") or []

    pelvis_pitch = s("Hips", "Xrotation") or []
    pelvis_yaw = s("Hips", "Yrotation") or []
    pelvis_roll = s("Hips", "Zrotation") or []

    spine_pitch = avg_series([
        s("Spine", "Xrotation"), s("Spine1", "Xrotation"),
        s("Spine2", "Xrotation"), s("Spine3", "Xrotation"),
    ])
    spine_roll = avg_series([
        s("Spine", "Zrotation"), s("Spine1", "Zrotation"),
        s("Spine2", "Zrotation"), s("Spine3", "Zrotation"),
    ])
    neck_pitch = s("Neck", "Xrotation") or []
    head_pitch = s("Head", "Xrotation") or []

    left_leg = s("LeftUpLeg", "Xrotation") or s("LeftLeg", "Xrotation") or []
    right_leg = s("RightUpLeg", "Xrotation") or s("RightLeg", "Xrotation") or []

    horizontal_ranges = {
        "x": (max(root_x)-min(root_x)) if root_x else 0.0,
        "z": (max(root_z)-min(root_z)) if root_z else 0.0,
    }
    forward_axis = max(horizontal_ranges, key=horizontal_ranges.get)
    root_forward = root_x if forward_axis == "x" else root_z
    lateral = root_z if forward_axis == "x" else root_x

    frame_count = len(frames)
    time = [(i / fps if fps else i) for i in range(frame_count)]

    signals = {
        "time": time,
        "root_forward_norm": normalize(root_forward),
        "root_lateral_norm": normalize(lateral),
        "hips_vertical_norm": normalize(hips_y),
        "pelvis_pitch_norm": normalize(pelvis_pitch),
        "pelvis_roll_norm": normalize(pelvis_roll),
        "torso_pitch_norm": normalize(spine_pitch),
        "torso_roll_norm": normalize(spine_roll),
        "neck_pitch_norm": normalize(neck_pitch),
        "head_pitch_norm": normalize(head_pitch),
        "left_leg_phase_proxy": normalize(left_leg),
        "right_leg_phase_proxy": normalize(right_leg),
    }

    report = {
        "source": str(path),
        "frame_count": frame_count,
        "frames_declared": declared,
        "fps": fps,
        "duration_seconds": (frame_count - 1) / fps if fps and frame_count else 0,
        "channel_count": len(channels),
        "joint_names": sorted({j for j, _ in channels if j}),
        "forward_axis": forward_axis,
        "raw_stats": {
            "root_x": stats(root_x),
            "root_y": stats(root_y),
            "root_z": stats(root_z),
            "hips_y": stats(hips_y),
            "pelvis_pitch_deg": stats(pelvis_pitch),
            "pelvis_roll_deg": stats(pelvis_roll),
            "torso_pitch_deg_avg": stats(spine_pitch),
            "torso_roll_deg_avg": stats(spine_roll),
            "neck_pitch_deg": stats(neck_pitch),
            "head_pitch_deg": stats(head_pitch),
            "left_leg_pitch_deg": stats(left_leg),
            "right_leg_pitch_deg": stats(right_leg),
        },
        "cadence_proxies": {
            "left_leg": dominant_period(left_leg, fps),
            "right_leg": dominant_period(right_leg, fps),
            "torso_pitch": dominant_period(spine_pitch, fps),
            "hips_vertical": dominant_period(hips_y, fps),
        },
        "signals": signals,
        "transfer_policy": {
            "allowed": [
                "root speed envelope",
                "hips vertical oscillation",
                "pelvis pitch/roll",
                "torso pitch/roll",
                "neck/head delayed pitch",
                "cadence timing proxy",
            ],
            "forbidden": [
                "direct human arm to S foreleg mapping",
                "direct human leg to S hindleg mapping",
                "one-to-one human spine proportion mapping",
            ],
        },
    }

    Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "frame_count", "fps", "duration_seconds", "forward_axis",
        "raw_stats", "cadence_proxies"
    )}, indent=2))


if __name__ == "__main__":
    main()
