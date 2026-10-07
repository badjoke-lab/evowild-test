#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "kimodo-ardy" / "compare_launch_profiles.py"
spec = importlib.util.spec_from_file_location("compare_launch_profiles", SCRIPT)
m = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m)


def main():
    t = np.linspace(0.0, 6.0, 181)
    # A deliberately front-loaded launch: 80% by roughly 2.0 s.
    speed = 1.0 - np.exp(-1.2 * t)
    result = m.compare(t, speed)
    metrics = result["metrics"]
    assert result["samples"] == 32
    assert metrics["thresholds"]["t80"]["kimodo_t01"] < metrics["thresholds"]["t80"]["evowild_t01"]
    assert result["decision_rule"]["absolute_human_motion_transfer"] is False
    assert len(result["curves"]["kimodo_launch_envelope01"]) == 32
    print("compare_launch_profiles test: PASS")


if __name__ == "__main__":
    main()
