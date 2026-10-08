#!/usr/bin/env python3
"""One bounded rescue attempt: QEM decimation followed by PyMeshFix hole repair.
Nothing here certifies S morphology, skinning, or game readiness.
"""
import json
from pathlib import Path
import traceback
import numpy as np
import trimesh
import pymeshfix
import inspect
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000"
SOURCE=BASE/"t2-meshfix/S-trellis2-clean-seed0000-maincomponent-meshfix.glb"
OUT=BASE/"t2-qem-repair"
OUT.mkdir(parents=True,exist_ok=True)
DST=OUT/"S-trellis2-qem-repair-best.glb"

def load(path):
    return trimesh.load(path,force="scene").to_geometry()

def audit(m):
    return {"faces":int(len(m.faces)),"vertices":int(len(m.vertices)),
            "components":int(m.body_count),"watertight":bool(m.is_watertight),
            "winding_consistent":bool(m.is_winding_consistent),
            "is_volume":bool(m.is_volume),"euler":int(m.euler_number),
            "bounds":np.asarray(m.bounds).tolist()}

def drift(a,b):
    np.random.seed(171)
    av,_=trimesh.sample.sample_surface(a,30000)
    np.random.seed(172)
    bv,_=trimesh.sample.sample_surface(b,30000)
    da=cKDTree(bv).query(av,workers=2)[0]
    db=cKDTree(av).query(bv,workers=2)[0]
    diag=float(np.linalg.norm(a.extents))
    return {"p95_over_diag":float((np.quantile(da,.95)+np.quantile(db,.95))/2/diag),
            "p99_over_diag":float((np.quantile(da,.99)+np.quantile(db,.99))/2/diag),
            "max_sampled_over_diag":float(max(da.max(),db.max())/diag),
            "samples_each":30000}

report={"experiment":"single QEM + MeshFix repair rescue", "input":str(SOURCE.relative_to(ROOT)),
        "scope":"geometry viability only; no morphology/rig/game approval",
        "trials":[],"outcome":"RUN_ERROR","selected":None}
try:
    s=load(SOURCE)
    report["source"]=audit(s)
    assert s.is_watertight and s.body_count==1,"Input source not watertight/connected"
    for target in (120000,80000,60000):
        trial={"target":target}
        try:
            reduced=s.simplify_quadric_decimation(face_count=target,aggression=5)
            trial["qem_raw"]=audit(reduced)
            fixer=pymeshfix.MeshFix(np.asarray(reduced.vertices,dtype=np.float64),
                                    np.asarray(reduced.faces,dtype=np.int32))
            signature=inspect.signature(fixer.repair)
            kwargs={}
            if 'verbose' in signature.parameters: kwargs['verbose']=False
            if 'joincomp' in signature.parameters: kwargs['joincomp']=False
            if 'remove_smallest_components' in signature.parameters:
                kwargs['remove_smallest_components']=False
            fixer.repair(**kwargs)
            repaired=trimesh.Trimesh(vertices=np.asarray(fixer.points),
                                      faces=np.asarray(fixer.faces),process=False)
            repaired.remove_unreferenced_vertices()
            # MeshFix sometimes outputs globally reversed but consistently wound faces.
            if repaired.is_watertight and repaired.is_winding_consistent and repaired.volume<0:
                repaired.invert()
            trial["repaired"]=audit(repaired)
            trial["drift_vs_original"]=drift(s,repaired)
            good=(repaired.is_watertight and repaired.is_volume and
                  repaired.is_winding_consistent and repaired.body_count==1 and
                  len(repaired.faces)<=150000 and
                  trial["drift_vs_original"]["p95_over_diag"]<=0.012)
            trial["topology_drift_gate"]=bool(good)
            if good:
                repaired.export(DST,file_type="glb")
                report["selected"]={"target":target,
                                   "final_faces":int(len(repaired.faces)),
                                   "model":str(DST.relative_to(ROOT)),
                                   "drift":trial["drift_vs_original"]}
        except Exception as exc:
            trial["exception"]=str(exc)
            trial["traceback_tail"]=traceback.format_exc()[-1600:]
        report["trials"].append(trial)
    report["outcome"]=("CANDIDATE_RENDER_REQUIRED" if report["selected"]
                       else "REJECT_QEM_PLUS_MESHFIX")
except Exception as exc:
    report["fatal"]=str(exc)
    report["traceback_tail"]=traceback.format_exc()[-2000:]

(OUT/"QEM_MESHFIX_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n")
(OUT/"QEM_MESHFIX_RESULT.md").write_text(
    "# TRELLIS2 QEM + MeshFix rescue\n\n"
    f"Outcome: **{report['outcome']}**\n\n"
    "An accepted geometry gate is only permission to examine the actual five-view renders.\n"
    "Input is not based on latest primary authority image. No production integration.\n"
    "See QEM_MESHFIX_AUDIT.json.\n"
)
print(json.dumps({"outcome":report["outcome"],
                  "selected":report["selected"],
                  "trials":report["trials"]},indent=2))
