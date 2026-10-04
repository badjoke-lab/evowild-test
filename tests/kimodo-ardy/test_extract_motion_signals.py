#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import math
import tempfile
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "kimodo-ardy" / "extract_motion_signals.py"

spec = importlib.util.spec_from_file_location("extract_motion_signals", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def synthetic_motion(fps: float = 30.0, seconds: float = 4.0):
    n = int(fps * seconds)
    t = np.arange(n) / fps

    root = np.zeros((n, 3), dtype=np.float64)
    root[:, 1] = 1.0 + 0.03 * np.sin(2.0 * math.pi * 2.0 * t)
    root[:, 2] = 3.0 * t

    heading = np.zeros((n, 2), dtype=np.float64)
    heading[:, 0] = 1.0

    contacts = np.zeros((n, 4), dtype=np.float64)
    cycle = int(fps)
    stance = int(round(0.25 * fps))
    for start in range(0, n, cycle):
        contacts[start : start + stance, 0:2] = 1.0
        rstart = start + cycle // 2
        contacts[rstart : rstart + stance, 2:4] = 1.0

    return {
        "root_positions": root,
        "global_root_heading": heading,
        "foot_contacts": contacts,
        "fps": np.array(fps),
    }


def main():
    summary, series = module.analyze_motion(synthetic_motion())

    assert summary["frames"] == 120
    assert abs(summary["fps"] - 30.0) < 1e-9
    assert abs(summary["mean_speed_mps"] - 3.0) < 0.05
    assert abs(summary["vertical_root_dominant_hz"] - 2.0) < 0.3

    contacts = summary["foot_contacts"]
    assert contacts["available"] is True
    assert contacts["left_contact_onsets"] == 4
    assert contacts["right_contact_onsets"] == 4
    assert 1.9 < contacts["combined_step_rate_hz"] < 2.1

    assert len(series["frame"]) == 120
    assert np.max(np.abs(series["turn_rate_rad_s"])) < 1e-6

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "series.csv"
        module.write_csv(out, series)
        assert out.exists()
        assert out.read_text(encoding="utf-8").splitlines()[0].startswith("frame,time_s")

    print("extract_motion_signals synthetic test: PASS")


if __name__ == "__main__":
    main()
