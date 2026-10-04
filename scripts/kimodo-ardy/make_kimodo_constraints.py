#!/usr/bin/env python3
"""Generate Kimodo root2d constraints for EvoWild feasibility cases."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np


def smoothstep(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def trajectory(mode: str, t: np.ndarray, speed: float) -> tuple[np.ndarray, np.ndarray]:
    duration = max(float(t[-1]), 1e-6)

    if mode == "straight":
        x = np.zeros_like(t)
        z = speed * t
    elif mode == "accel":
        v0 = max(1.2, speed * 0.35)
        v = v0 + (speed - v0) * smoothstep(t / duration)
        dt = t[1] - t[0]
        z = np.cumsum(v) * dt
        z -= z[0]
        x = np.zeros_like(t)
    elif mode == "decel":
        v1 = max(1.2, speed * 0.35)
        v = speed + (v1 - speed) * smoothstep(t / duration)
        dt = t[1] - t[0]
        z = np.cumsum(v) * dt
        z -= z[0]
        x = np.zeros_like(t)
    elif mode == "curve":
        radius = max(4.5, speed * 1.4)
        total_angle = math.radians(55.0)
        theta = total_angle * smoothstep(t / duration)
        x = radius * (1.0 - np.cos(theta))
        z = radius * np.sin(theta)
    elif mode == "lane-change":
        z = speed * t
        phase = smoothstep((t / duration - 0.20) / 0.60)
        x = 1.20 * phase
    else:
        raise ValueError(f"unsupported mode: {mode}")

    pos = np.stack((x, z), axis=1)
    tangent = np.gradient(pos, t, axis=0)
    yaw = np.arctan2(tangent[:, 0], tangent[:, 1])
    heading = np.stack((np.cos(yaw), np.sin(yaw)), axis=1)
    return pos, heading


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["straight", "accel", "decel", "curve", "lane-change"], required=True)
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--speed", type=float, default=4.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.duration <= 0 or args.fps <= 0 or args.speed <= 0:
        raise SystemExit("duration, fps and speed must be positive")

    frames = int(round(args.duration * args.fps))
    if frames < 2:
        raise SystemExit("duration/fps combination must produce at least 2 frames")
    t = np.arange(frames, dtype=float) / args.fps
    pos, heading = trajectory(args.mode, t, args.speed)

    payload = [{
        "type": "root2d",
        "frame_indices": list(range(frames)),
        "smooth_root_2d": pos.tolist(),
        "global_root_heading": heading.tolist(),
    }]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} ({frames} frames, {args.mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
