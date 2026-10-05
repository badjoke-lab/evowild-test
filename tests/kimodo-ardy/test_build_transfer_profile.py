#!/usr/bin/env python3
from __future__ import annotations
import csv, importlib.util, json, tempfile
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/"scripts"/"kimodo-ardy"/"build_transfer_profile.py"
spec=importlib.util.spec_from_file_location("mtp", P)
m=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(m)

def main():
    summary={"duration_s":4.0,"heading_source":"test","foot_contacts":{"available":True}}
    meta={"text":"A person runs."}
    t=np.linspace(0,4,121)
    speed=np.linspace(0,5,121)
    accel=np.gradient(speed,t)
    turn=np.sin(t)
    ts={"speed_mps":speed,"accel_mps2":accel,"turn_rate_rad_s":turn}
    p=m.build(summary,meta,ts)
    assert p["transfer_policy"]["absolute_transfer_allowed"] is False
    assert len(p["curves"]["speed01"])==32
    assert max(p["curves"]["speed01"])<=1.5+1e-9
    assert "human_joint_rotations" in p["transfer_policy"]["blocked_channels"]
    print("build_transfer_profile test: PASS")

if __name__=="__main__": main()
