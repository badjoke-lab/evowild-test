#!/usr/bin/env python3
"""Audited, non-voxel QEM recovery for the pre-existing TRELLIS.2 S source.

Experimental only. This script does NOT claim morphology or animation approval.
"""
import json
from pathlib import Path
import traceback

import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000"
SOURCE = BASE / "t2-meshfix/S-trellis2-clean-seed0000-maincomponent-meshfix.glb"
DEST = BASE / "t2-qem-recovery"
DEST.mkdir(parents=True, exist_ok=True)
OUTPUT = DEST / "S-trellis2-meshfix-qem-best.glb"

def scene_mesh(path):
    scene = trimesh.load(path, force="scene")
    mesh = scene.to_geometry()
    if not isinstance(mesh, trimesh.Trimesh):
        raise RuntimeError(f"Expected one Trimesh, got {type(mesh)}")
    return mesh

def summary(mesh):
    return {
        "faces": int(len(mesh.faces)),
        "vertices": int(len(mesh.vertices)),
        "connected_bodies": int(mesh.body_count),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "is_volume": bool(mesh.is_volume),
        "euler_number": int(mesh.euler_number),
        "area": float(mesh.area),
        "volume": float(mesh.volume),
        "bounds": np.asarray(mesh.bounds).tolist(),
        "extents": np.asarray(mesh.extents).tolist()
    }

def sampled_drift(source, candidate):
    # Symmetric surface-point nearest-neighbour proxy (NOT exact Hausdorff).
    # Shared sampling density and seeded runs make experiments comparable.
    np.random.seed(20261008)
    a, _ = trimesh.sample.sample_surface(source, 30000)
    np.random.seed(20261009)
    b, _ = trimesh.sample.sample_surface(candidate, 30000)
    da = cKDTree(b).query(a, workers=2)[0]
    db = cKDTree(a).query(b, workers=2)[0]
    diag = float(np.linalg.norm(source.extents))
    return {
        "sample_count_per_surface": 30000,
        "source_bbox_diagonal": diag,
        "mean_over_diag": float((np.mean(da) + np.mean(db)) / 2 / diag),
        "p95_over_diag": float((np.quantile(da, .95) + np.quantile(db, .95)) / 2 / diag),
        "p99_over_diag": float((np.quantile(da, .99) + np.quantile(db, .99)) / 2 / diag),
        "approx_max_over_diag": float(max(da.max(), db.max()) / diag)
    }

report = {
    "source_file": str(SOURCE.relative_to(ROOT)),
    "algorithm": "trimesh simplify_quadric_decimation / fast-simplification, NOT LODTailor",
    "source_is_authoritative_morphology": False,
    "input_reference_note": "TRELLIS seed0 used older 01_s_body_primary.png; 00_s_type_modeling_image_v1.png remains the higher authority",
    "approved_for_game": False,
    "trials": [],
    "selected": None,
    "outcome": "NOT_RUN"
}

try:
    source = scene_mesh(SOURCE)
    report["source"] = summary(source)
    if not source.is_watertight or source.body_count != 1:
        raise RuntimeError("Repaired input is not single-body watertight; abort")
    # Evaluate from the untouched repaired mesh every time: never chain decimations.
    for target in (120000, 80000, 60000):
        trial = {"target_faces": target}
        try:
            m = source.simplify_quadric_decimation(face_count=target, aggression=5)
            trial["mesh"] = summary(m)
            trial["drift"] = sampled_drift(source, m)
            geom_ok = (m.body_count == 1 and m.is_watertight
                       and m.is_winding_consistent and m.is_volume)
            drift_ok = trial["drift"]["p95_over_diag"] <= 0.012
            trial["topology_pass"] = bool(geom_ok)
            trial["drift_candidate_pass"] = bool(drift_ok)
            trial["keep_for_visual_review"] = bool(geom_ok and drift_ok)
            if trial["keep_for_visual_review"]:
                # Select the lowest polygon count that preserves these baseline invariants.
                m.export(OUTPUT, file_type="glb")
                report["selected"] = {"target_faces": target, "mesh": trial["mesh"],
                                      "drift": trial["drift"],
                                      "output_file": str(OUTPUT.relative_to(ROOT))}
        except Exception as e:
            trial["error"] = f"{type(e).__name__}: {e}"
            trial["traceback_tail"] = traceback.format_exc()[-1400:]
        report["trials"].append(trial)
    report["outcome"] = ("GEOMETRY_CANDIDATE_FOR_VISUAL_REVIEW" if report["selected"]
                         else "REJECT_QEM_TOPOLOGY_OR_DRIFT")
except Exception as e:
    report["outcome"] = "RUN_ERROR"
    report["fatal_error"] = f"{type(e).__name__}: {e}"
    report["fatal_traceback_tail"] = traceback.format_exc()[-1600:]

(DEST / "QEM_RECOVERY_AUDIT.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(DEST / "QEM_RECOVERY_RESULT.md").write_text(
    "# TRELLIS.2 S — audited QEM recovery\n\n"
    f"- Outcome: **{report['outcome']}**\n"
    f"- Source: \`{report['source_file']}\`\n"
    f"- Selected: \`{(report['selected'] or {}).get('output_file', 'NONE')}\`\n"
    "- Original highest-priority S modeling reference was NOT used to generate this candidate.\n"
    "- A topology PASS is NOT an appearance/skin deformation/rig/game PASS.\n"
    "- No legacy source, main branch, or existing creature runtime was modified.\n"
    "- See QEM_RECOVERY_AUDIT.json for every attempted face count and all rejected trials.\n",
    encoding="utf-8"
)
print(json.dumps({"outcome": report["outcome"], "trials": report["trials"],
                  "selected": report["selected"]}, indent=2))
