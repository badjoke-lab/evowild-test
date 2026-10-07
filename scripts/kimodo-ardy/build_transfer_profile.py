#!/usr/bin/env python3
"""Build a normalized, quadruped-safe transfer profile from external motion signals.

Absolute human/humanoid gait values are intentionally not transferred to
EvoWild. Only dimensionless trajectory/transition shapes are exported.
"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np

SAMPLES = 32

def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("empty timeseries")
    cols = {k: np.array([float(r[k]) for r in rows], dtype=float) for k in rows[0].keys()}
    return cols

def robust_scale(x: np.ndarray, q: float = 95.0) -> float:
    v = float(np.percentile(np.abs(x), q))
    return v if v > 1e-9 else 1.0

def sample_curve(x: np.ndarray, n: int = SAMPLES):
    src = np.linspace(0.0, 1.0, len(x))
    dst = np.linspace(0.0, 1.0, n)
    return np.interp(dst, src, x).tolist()

def build(summary: dict, meta: dict, ts: dict):
    speed = ts["speed_mps"]
    accel = ts["accel_mps2"]
    turn = ts["turn_rate_rad_s"]

    speed_scale = max(float(np.percentile(speed, 95)), 1e-9)
    accel_scale = robust_scale(accel)
    turn_scale = robust_scale(turn)

    return {
        "schema_version": 1,
        "source_text": meta.get("text") or meta.get("texts") or meta.get("prompt"),
        "source_duration_s": summary.get("duration_s"),
        "source_heading_method": summary.get("heading_source"),
        "transfer_policy": {
            "absolute_transfer_allowed": False,
            "eligible_channels": [
                "normalized_root_speed_shape",
                "normalized_signed_acceleration_shape",
                "normalized_signed_turn_rate_shape"
            ],
            "blocked_channels": [
                "absolute_speed_mps",
                "absolute_human_step_rate_hz",
                "human_stance_ratio",
                "human_joint_rotations",
                "human_foot_to_quadruped_leg_mapping"
            ],
            "reason": "Kimodo source skeleton is human/humanoid while EvoWild S is quadruped."
        },
        "normalization": {
            "speed_p95_mps": speed_scale,
            "abs_accel_p95_mps2": accel_scale,
            "abs_turn_rate_p95_rad_s": turn_scale,
            "samples": SAMPLES
        },
        "curves": {
            "t01": np.linspace(0.0, 1.0, SAMPLES).tolist(),
            "speed01": sample_curve(np.clip(speed / speed_scale, 0.0, 1.5)),
            "accel_signed": sample_curve(np.clip(accel / accel_scale, -2.0, 2.0)),
            "turn_rate_signed": sample_curve(np.clip(turn / turn_scale, -2.0, 2.0))
        },
        "source_contact_metrics_for_reference_only": summary.get("foot_contacts")
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", type=Path, required=True)
    ap.add_argument("--meta", type=Path, required=True)
    ap.add_argument("--timeseries", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()

    summary = json.loads(a.summary.read_text(encoding="utf-8"))
    meta = json.loads(a.meta.read_text(encoding="utf-8"))
    profile = build(summary, meta, read_csv(a.timeseries))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    print(a.output)

if __name__ == "__main__":
    main()
