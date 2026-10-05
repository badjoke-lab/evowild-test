#!/usr/bin/env python3
"""Compare the current EvoWild launch-speed shape with a generated Kimodo clip.

This is a shape comparison only. It does not propose copying absolute human
speed, cadence, stance time, or joint rotations to the EvoWild quadruped.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

SAMPLES = 32


def smoothstep01(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def load_timeseries(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) < 2:
        raise ValueError("timeseries must contain at least two rows")
    time_s = np.asarray([float(r["time_s"]) for r in rows], dtype=float)
    speed = np.asarray([float(r["speed_mps"]) for r in rows], dtype=float)
    if not np.all(np.diff(time_s) > 0):
        raise ValueError("time_s must be strictly increasing")
    return time_s, speed


def simulate_evowild_launch(
    duration_s: float,
    *,
    launch_duration_s: float = 4.8,
    damping_lambda: float = 3.0,
    simulation_hz: float = 60.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Mirror current main.js launch target + THREE.MathUtils.damp behavior."""
    dt = 1.0 / simulation_hz
    n = int(math.ceil(duration_s * simulation_hz)) + 1
    t = np.arange(n, dtype=float) * dt
    target = smoothstep01(t / launch_duration_s)

    speed = np.zeros_like(t)
    alpha = 1.0 - math.exp(-damping_lambda * dt)
    for i in range(1, n):
        speed[i] = speed[i - 1] + (target[i] - speed[i - 1]) * alpha

    return t, speed


def p95_normalize(values: np.ndarray) -> tuple[np.ndarray, float]:
    scale = float(np.percentile(values, 95))
    if scale <= 1e-9:
        scale = 1.0
    return values / scale, scale


def monotonic_envelope(values: np.ndarray) -> np.ndarray:
    # For launch timing, compare "how quickly the clip establishes pace"
    # rather than frame-level oscillation caused by individual foot contacts.
    return np.minimum(np.maximum.accumulate(values), 1.0)


def threshold_time(t01: np.ndarray, curve: np.ndarray, threshold: float) -> float | None:
    idx = np.flatnonzero(curve >= threshold)
    if not len(idx):
        return None
    i = int(idx[0])
    if i == 0:
        return 0.0
    x0, x1 = float(t01[i - 1]), float(t01[i])
    y0, y1 = float(curve[i - 1]), float(curve[i])
    if abs(y1 - y0) < 1e-12:
        return x1
    return x0 + (threshold - y0) * (x1 - x0) / (y1 - y0)


def compare(time_s: np.ndarray, kimodo_speed: np.ndarray) -> dict:
    duration = float(time_s[-1])
    sample_t01 = np.linspace(0.0, 1.0, SAMPLES)
    sample_time = sample_t01 * duration

    kimodo_norm_full, kimodo_p95 = p95_normalize(kimodo_speed)
    kimodo_sample = np.interp(sample_time, time_s, kimodo_norm_full)

    evo_t, evo_speed = simulate_evowild_launch(duration)
    evo_sample_raw = np.interp(sample_time, evo_t, evo_speed)
    evo_sample, evo_p95 = p95_normalize(evo_sample_raw)

    kimodo_env = monotonic_envelope(kimodo_sample)
    evo_env = monotonic_envelope(evo_sample)

    thresholds = {}
    for threshold in (0.5, 0.8, 0.9, 0.95):
        key = f"t{int(threshold * 100)}"
        k = threshold_time(sample_t01, kimodo_env, threshold)
        e = threshold_time(sample_t01, evo_env, threshold)
        thresholds[key] = {
            "kimodo_t01": k,
            "evowild_t01": e,
            "kimodo_seconds": None if k is None else k * duration,
            "evowild_seconds": None if e is None else e * duration,
            "delta_t01_kimodo_minus_evowild": None if k is None or e is None else k - e,
        }

    delta = kimodo_env - evo_env
    return {
        "schema_version": 1,
        "comparison": "normalized launch establishment envelope",
        "transfer_scope": "visual-presentation candidate only; race physics unchanged",
        "source_duration_s": duration,
        "samples": SAMPLES,
        "normalization": {
            "kimodo_speed_p95_mps": kimodo_p95,
            "evowild_simulated_speed_p95_unitless": evo_p95,
        },
        "metrics": {
            "envelope_rmse": float(np.sqrt(np.mean(delta * delta))),
            "envelope_mae": float(np.mean(np.abs(delta))),
            "mean_signed_delta_kimodo_minus_evowild": float(np.mean(delta)),
            "thresholds": thresholds,
        },
        "curves": {
            "t01": sample_t01.tolist(),
            "kimodo_speed01_raw_sample": kimodo_sample.tolist(),
            "kimodo_launch_envelope01": kimodo_env.tolist(),
            "evowild_launch_envelope01": evo_env.tolist(),
            "delta_kimodo_minus_evowild": delta.tolist(),
        },
        "decision_rule": {
            "meaningful_if": "envelope_rmse >= 0.10 and Kimodo reaches 80% at least 0.10 normalized-time earlier",
            "absolute_human_motion_transfer": False,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("timeseries", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    t, speed = load_timeseries(args.timeseries)
    result = compare(t, speed)
    rendered = json.dumps(result, indent=2) + "\n"
    print(rendered, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
