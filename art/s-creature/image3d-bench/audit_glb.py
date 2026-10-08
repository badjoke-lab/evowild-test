#!/usr/bin/env python3
"""Conservative static-geometry audit of image-to-3D GLB outputs.

No qualitative acceptance decision is made. Five-view morphology and deformation
quality require a separate visual/Blender inspection against locked S references.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import trimesh


def inspect(input_path: Path) -> dict:
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    scene = trimesh.load(str(input_path), file_type='glb', force='scene', process=False)
    meshes = [m for m in scene.dump() if isinstance(m, trimesh.Trimesh) and len(m.faces)]
    if not meshes:
        raise ValueError('GLB contains no triangle mesh')
    all_bounds = np.stack([mesh.bounds for mesh in meshes])
    mins = all_bounds[:, 0].min(axis=0)
    maxs = all_bounds[:, 1].max(axis=0)
    extents = maxs - mins
    if not np.all(np.isfinite(extents)) or np.any(extents <= 0):
        raise ValueError('Missing or invalid world-coordinate 3D extents')
    records = []
    for i, mesh in enumerate(meshes):
        edges = mesh.edges_sorted
        _, counts = np.unique(edges, axis=0, return_counts=True)
        area_faces = mesh.area_faces
        records.append({
            'index': i,
            'vertices': int(len(mesh.vertices)),
            'triangles': int(len(mesh.faces)),
            'watertight': bool(mesh.is_watertight),
            'winding_consistent': bool(mesh.is_winding_consistent),
            'boundary_edges': int(np.count_nonzero(counts == 1)),
            'nonmanifold_edges_over_two_faces': int(np.count_nonzero(counts > 2)),
            'degenerate_or_zero_area_triangles': int(np.count_nonzero(area_faces <= 1e-14)),
            'surface_area': round(float(mesh.area), 7),
            'bounds_min': [round(float(x), 7) for x in mesh.bounds[0]],
            'bounds_max': [round(float(x), 7) for x in mesh.bounds[1]],
        })
    return {
        'schema': 'evowild-s-image3d-glb-audit-v1',
        'input_name': input_path.name,
        'input_bytes': input_path.stat().st_size,
        'mesh_count': len(meshes),
        'vertex_count': sum(r['vertices'] for r in records),
        'triangle_count': sum(r['triangles'] for r in records),
        'world_extents_xyz': [round(float(x), 7) for x in extents],
        'bbox_ratio_xyz_over_max': [round(float(x / extents.max()), 7) for x in extents],
        'all_meshes_watertight': all(r['watertight'] for r in records),
        'total_boundary_edges': sum(r['boundary_edges'] for r in records),
        'total_nonmanifold_edges_over_two_faces': sum(r['nonmanifold_edges_over_two_faces'] for r in records),
        'total_degenerate_or_zero_area_triangles': sum(r['degenerate_or_zero_area_triangles'] for r in records),
        'meshes': records,
        'warnings': [
            'World coordinates and object axes may differ between generators; dimensions alone do not indicate S-type conformity.',
            'Watertightness is advisory for separate crest, tail, and foot meshes and is not an automatic rejection.',
            'Skinning, rig deformation, reference-image fidelity, material quality, and licensing are NOT validated.',
        ],
        'morphology_decision': 'REVIEW_REQUIRED',
        'game_ready_decision': 'NOT_EVALUATED',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb', type=Path)
    parser.add_argument('--output', '-o', type=Path, help='Write JSON report to this path')
    args = parser.parse_args()
    try:
        result = inspect(args.glb)
    except Exception as exc:
        print(f'AUDIT_FAILED: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + '\n', encoding='utf-8')
    print(rendered)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
