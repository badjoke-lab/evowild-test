#!/usr/bin/env python3
"""Compare normalized launch-establishment shapes from two external motion clips."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np

SAMPLES = 32

def load(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    if len(rows)<2: raise ValueError("timeseries too short")
    t=np.array([float(r["time_s"]) for r in rows],dtype=float)
    s=np.array([float(r["speed_mps"]) for r in rows],dtype=float)
    return t,s

def profile(path: Path):
    t,s=load(path)
    dur=float(t[-1])
    q=max(float(np.percentile(s,95)),1e-9)
    dst=np.linspace(0.0,dur,SAMPLES)
    raw=np.interp(dst,t,s/q)
    env=np.minimum(np.maximum.accumulate(raw),1.0)
    x=np.linspace(0.0,1.0,SAMPLES)
    def threshold(v):
        ids=np.flatnonzero(env>=v)
        if not len(ids): return None
        i=int(ids[0])
        if i==0: z=0.0
        else:
            x0,x1=float(x[i-1]),float(x[i]); y0,y1=float(env[i-1]),float(env[i])
            z=x1 if abs(y1-y0)<1e-12 else x0+(v-y0)*(x1-x0)/(y1-y0)
        return {"t01":z,"seconds":z*dur}
    return {
        "duration_s":dur,
        "speed_p95_mps":q,
        "t50":threshold(.5),"t80":threshold(.8),"t90":threshold(.9),"t95":threshold(.95),
        "envelope":env.tolist(),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--a",type=Path,required=True)
    ap.add_argument("--b",type=Path,required=True)
    ap.add_argument("--a-label",default="a")
    ap.add_argument("--b-label",default="b")
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    pa,pb=profile(a.a),profile(a.b)
    ea=np.array(pa["envelope"]); eb=np.array(pb["envelope"]); d=eb-ea
    def delta(key):
        av=pa[key]; bv=pb[key]
        return None if av is None or bv is None else bv["seconds"]-av["seconds"]
    out={
        "schema_version":1,
        "comparison":"normalized monotonic launch-establishment envelopes",
        "a_label":a.a_label,"b_label":a.b_label,
        "a":pa,"b":pb,
        "b_minus_a":{
            "envelope_rmse":float(np.sqrt(np.mean(d*d))),
            "envelope_mae":float(np.mean(np.abs(d))),
            "mean_signed_delta":float(np.mean(d)),
            "delta_t50_s":delta("t50"),
            "delta_t80_s":delta("t80"),
            "delta_t90_s":delta("t90"),
            "delta_t95_s":delta("t95"),
        },
        "transfer_policy":"shape comparison only; absolute humanoid speed/cadence/stance/joints remain blocked",
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out["b_minus_a"],indent=2))

if __name__=="__main__":
    main()
