#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
import re
import shutil
from io import BytesIO
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]

VIEW_MAP = {
    "back": 0,
    "rear34": 1,
    "side": 2,
    "front34": 3,
    "front": 4,
}

BASELINE = {
    "side": ROOT / "art/s-creature/output/review/vibe-b1a-v2/S_vibe_b1a_v2_side.png",
    "front": ROOT / "art/s-creature/output/review/vibe-b1a-v2/S_vibe_b1a_v2_front.png",
    "front34": ROOT / "art/s-creature/output/review/vibe-b1a-v2/S_vibe_b1a_v2_front34.png",
    "rear34": ROOT / "art/s-creature/output/review/vibe-b1a-v2/S_vibe_b1a_v2_rear34.png",
    "back": ROOT / "art/s-creature/output/review/vibe-b1a-v2/S_vibe_b1a_v2_back.png",
}


def extract_preview_images(html: str):
    encoded = re.findall(r"data:image/(?:jpeg|png);base64,([A-Za-z0-9+/=]+)", html)
    out = []
    seen = set()
    for b64 in encoded:
        raw = base64.b64decode(b64)
        h = hashlib.sha256(raw).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        try:
            im = Image.open(BytesIO(raw)).convert("RGB")
        except Exception:
            continue
        if im.size == (1024, 1024):
            out.append(im)
    if len(out) < 8:
        raise RuntimeError(f"Expected at least 8 full preview frames; got {len(out)}")
    return out


def make_contact(images, labels, path, cell=(420, 350), cols=5):
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell[0], rows * cell[1]), "white")
    draw = ImageDraw.Draw(sheet)
    for i, (im, label) in enumerate(zip(images, labels)):
        x = (i % cols) * cell[0]
        y = (i // cols) * cell[1]
        box = (cell[0] - 16, cell[1] - 42)
        thumb = ImageOps.contain(im.convert("RGB"), box)
        sheet.paste(thumb, (x + (cell[0] - thumb.width) // 2, y + 30))
        draw.text((x + 8, y + 8), label, fill="black")
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=92)


def mesh_audit(glb_path: Path):
    scene = trimesh.load(glb_path, force="scene")
    mesh = scene.dump(concatenate=True)

    edges = np.sort(mesh.edges, axis=1)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    boundary_edges = int(np.sum(counts == 1))
    nonmanifold_edges = int(np.sum(counts > 2))

    rounded = np.round(np.asarray(mesh.vertices), 8)
    duplicate_vertices = int(len(rounded) - len(np.unique(rounded, axis=0)))

    # Fast face-component count without materializing hundreds of thousands
    # of submeshes. The standard trimesh split path is too expensive for CI.
    nfaces = len(mesh.faces)
    parent = np.arange(nfaces, dtype=np.int32)
    rank = np.zeros(nfaces, dtype=np.uint8)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(int(a)), find(int(b))
        if ra == rb:
            return
        if rank[ra] < rank[rb]:
            parent[ra] = rb
        elif rank[ra] > rank[rb]:
            parent[rb] = ra
        else:
            parent[rb] = ra
            rank[ra] += 1

    for a, b in np.asarray(mesh.face_adjacency):
        union(a, b)

    roots = np.fromiter((find(i) for i in range(nfaces)), dtype=np.int32, count=nfaces)
    _, comp_counts = np.unique(roots, return_counts=True)
    comp_counts = np.sort(comp_counts)[::-1]

    return {
        "source_glb": glb_path.name,
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "connected_components": int(len(comp_counts)),
        "component_face_counts_desc": [int(x) for x in comp_counts[:32]],
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "is_volume": bool(mesh.is_volume),
        "euler_number": int(mesh.euler_number),
        "boundary_edges": boundary_edges,
        "nonmanifold_edges_gt2_faces": nonmanifold_edges,
        "duplicate_vertex_positions_rounded_1e-8": duplicate_vertices,
        "bounds": np.asarray(mesh.bounds).tolist(),
        "extents": np.asarray(mesh.extents).tolist(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-dir", required=True)
    args = ap.parse_args()

    src = Path(args.artifact_dir)
    reports = list(src.rglob("report.json"))
    glbs = list(src.rglob("*.glb"))
    if len(reports) != 1 or len(glbs) != 1:
        raise RuntimeError(f"Expected one report and one GLB; reports={reports}, glbs={glbs}")

    report = json.loads(reports[0].read_text(encoding="utf-8"))
    if report.get("status") != "SUCCESS":
        raise RuntimeError(f"Artifact report is not SUCCESS: {report.get('status')}")

    out = ROOT / "art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000"
    review = out / "review"
    out.mkdir(parents=True, exist_ok=True)
    review.mkdir(parents=True, exist_ok=True)

    dst_glb = out / "S-trellis2-clean-seed0000.glb"
    shutil.copy2(glbs[0], dst_glb)
    shutil.copy2(reports[0], out / "generation-report.json")

    frames = extract_preview_images(report["generate_return"])
    selected = {}
    for view, idx in VIEW_MAP.items():
        p = review / f"S_trellis2_clean_seed0000_{view}.jpg"
        frames[idx].save(p, quality=95)
        selected[view] = p

    order = ["side", "front", "front34", "rear34", "back"]
    make_contact(
        [Image.open(selected[v]) for v in order],
        [f"TRELLIS2 {v.upper()}" for v in order],
        review / "trellis2-five-view-contact.jpg",
    )

    compare_images = []
    compare_labels = []
    for v in order:
        compare_images.append(Image.open(BASELINE[v]))
        compare_labels.append(f"B1a-v2 {v.upper()}")
    for v in order:
        compare_images.append(Image.open(selected[v]))
        compare_labels.append(f"TRELLIS2 {v.upper()}")
    make_contact(
        compare_images,
        compare_labels,
        review / "b1a-v2-vs-trellis2-five-view.jpg",
        cols=5,
    )

    audit = mesh_audit(dst_glb)
    (out / "mesh-audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )

    (out / "README.md").write_text(
        """# TRELLIS.2 clean-input seed 0 candidate

Source run: GitHub Actions 37458478227
Input: `primary_clean_v1.png`
Resolution: 1024
Seed: 0

Review view mapping comes from the first 8-angle preview cycle returned by the official TRELLIS.2 Space:

- BACK = frame 0
- REAR34 = frame 1
- SIDE = frame 2
- FRONT34 = frame 3
- FRONT = frame 4

The GLB and review images are experimental evidence only. They do not modify the approved S mainline.
""",
        encoding="utf-8",
    )

    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
