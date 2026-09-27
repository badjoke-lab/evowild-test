import math
import os
import sys
import json
import numpy as np
import trimesh


def args():
    xs = sys.argv
    if "--" not in xs:
        raise SystemExit("Expected input.glb output.glb metadata.json")
    user = xs[xs.index("--") + 1:]
    if len(user) != 3:
        raise SystemExit("Expected 3 args")
    return [os.path.abspath(x) for x in user]


def tube_mesh(points, radii_x, radii_y=None, sections=12):
    pts = np.asarray(points, dtype=float)
    rx = np.asarray(radii_x, dtype=float)
    ry = rx if radii_y is None else np.asarray(radii_y, dtype=float)
    n = len(pts)
    verts = []
    faces = []
    for i, p in enumerate(pts):
        if i == 0:
            tangent = pts[1] - pts[0]
        elif i == n - 1:
            tangent = pts[-1] - pts[-2]
        else:
            tangent = pts[i + 1] - pts[i - 1]
        tangent = tangent / np.linalg.norm(tangent)
        e1 = np.array([1.0, 0.0, 0.0])
        e1 = e1 - tangent * np.dot(e1, tangent)
        if np.linalg.norm(e1) < 1e-8:
            e1 = np.array([0.0, 1.0, 0.0])
            e1 = e1 - tangent * np.dot(e1, tangent)
        e1 = e1 / np.linalg.norm(e1)
        e2 = np.cross(tangent, e1)
        e2 = e2 / np.linalg.norm(e2)
        for j in range(sections):
            a = 2.0 * math.pi * j / sections
            verts.append(p + e1 * rx[i] * math.cos(a) + e2 * ry[i] * math.sin(a))

    for i in range(n - 1):
        for j in range(sections):
            a = i * sections + j
            b = i * sections + (j + 1) % sections
            c = (i + 1) * sections + (j + 1) % sections
            d = (i + 1) * sections + j
            faces.append([a, b, c])
            faces.append([a, c, d])

    verts.append(pts[0]); c0 = len(verts) - 1
    verts.append(pts[-1]); c1 = len(verts) - 1
    for j in range(sections):
        faces.append([c0, (j + 1) % sections, j])
        a = (n - 1) * sections + j
        b = (n - 1) * sections + (j + 1) % sections
        faces.append([c1, a, b])

    return trimesh.Trimesh(
        vertices=np.asarray(verts),
        faces=np.asarray(faces),
        process=False,
    )


def blade_mesh(points, half_widths, half_thicknesses):
    """Build a tapered swept blade instead of an antler-like round tube."""
    pts = np.asarray(points, dtype=float)
    widths = np.asarray(half_widths, dtype=float)
    thickness = np.asarray(half_thicknesses, dtype=float)
    verts = []
    faces = []

    for i, p in enumerate(pts):
        if i == 0:
            tangent = pts[1] - pts[0]
        elif i == len(pts) - 1:
            tangent = pts[-1] - pts[-2]
        else:
            tangent = pts[i + 1] - pts[i - 1]
        tangent = tangent / np.linalg.norm(tangent)

        # Crests run mostly through the Y/Z plane. Use X for plate thickness
        # and a Y/Z normal for the visible blade width.
        yz_normal = np.array([0.0, -tangent[2], tangent[1]])
        if np.linalg.norm(yz_normal) < 1e-8:
            yz_normal = np.array([0.0, 1.0, 0.0])
        yz_normal = yz_normal / np.linalg.norm(yz_normal)
        x_axis = np.array([1.0, 0.0, 0.0])

        n = yz_normal * widths[i]
        t = x_axis * thickness[i]
        verts.extend([
            p - t - n,
            p + t - n,
            p + t + n,
            p - t + n,
        ])

    for i in range(len(pts) - 1):
        a = i * 4
        b = (i + 1) * 4
        # Two broad faces.
        faces += [
            [a + 0, b + 0, b + 3], [a + 0, b + 3, a + 3],
            [a + 1, a + 2, b + 2], [a + 1, b + 2, b + 1],
            # Thin top/bottom edges.
            [a + 3, b + 3, b + 2], [a + 3, b + 2, a + 2],
            [a + 0, a + 1, b + 1], [a + 0, b + 1, b + 0],
        ]

    # Root and tip caps.
    faces += [[0, 3, 2], [0, 2, 1]]
    e = (len(pts) - 1) * 4
    faces += [[e + 0, e + 1, e + 2], [e + 0, e + 2, e + 3]]

    return trimesh.Trimesh(
        vertices=np.asarray(verts),
        faces=np.asarray(faces),
        process=False,
    )


def keep_largest_component(mesh):
    """Drop detached legacy crest/tail shards created by source-face surgery."""
    verts = np.asarray(mesh.vertices)
    faces = np.asarray(mesh.faces)
    n = len(verts)
    parent = np.arange(n, dtype=np.int64)
    rank = np.zeros(n, dtype=np.int8)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

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

    for tri in faces:
        union(tri[0], tri[1])
        union(tri[1], tri[2])
        union(tri[2], tri[0])

    roots = np.array([find(i) for i in range(n)], dtype=np.int64)
    face_roots = roots[faces[:, 0]]
    unique, counts = np.unique(face_roots, return_counts=True)
    keep_root = unique[np.argmax(counts)]
    keep_faces = faces[face_roots == keep_root]
    removed_faces = int(len(faces) - len(keep_faces))
    component_count = int(len(unique))

    out = trimesh.Trimesh(
        vertices=verts.copy(),
        faces=keep_faces.copy(),
        process=False,
        visual=mesh.visual,
    )
    out.remove_unreferenced_vertices()
    return out, component_count, removed_faces


def main():
    input_path, output_path, meta_path = args()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(meta_path), exist_ok=True)

    scene = trimesh.load(input_path, force="scene")
    if len(scene.geometry) != 1:
        raise RuntimeError(f"Expected one source geometry, got {len(scene.geometry)}")
    source = next(iter(scene.geometry.values())).copy()

    v = np.asarray(source.vertices).copy()
    f = np.asarray(source.faces).copy()
    original = v.copy()

    x_min, y_min, z_min = v.min(axis=0)
    x_max, y_max, z_max = v.max(axis=0)
    cx = (x_min + x_max) * 0.5

    # Verified raw GLB basis:
    # X lateral, Y vertical, +Z head, -Z tail.

    # 1) Sprint torso: longer, narrower and with a clearer tucked waist.
    body = (
        (v[:, 2] > -0.50) & (v[:, 2] < 0.45) &
        (v[:, 1] > -0.18) & (v[:, 1] < 0.30)
    )
    v[body, 2] *= 1.13
    v[body, 0] = cx + (v[body, 0] - cx) * 0.82

    waist = (
        (v[:, 2] > -0.14) & (v[:, 2] < 0.13) &
        (v[:, 1] > -0.14) & (v[:, 1] < 0.22)
    )
    v[waist, 0] = cx + (v[waist, 0] - cx) * 0.72

    belly = (
        (v[:, 2] > -0.46) & (v[:, 2] < 0.38) &
        (v[:, 1] > -0.24) & (v[:, 1] < 0.08)
    )
    factor = np.clip((0.08 - v[belly, 1]) / 0.32, 0.0, 1.0)
    v[belly, 1] += 0.095 * factor

    # 2) Head/neck: make the head smaller and more wedge-like and remove
    # some of the deer/horse read from the lower crest/ear region.
    head = (
        (v[:, 2] > 0.52) & (v[:, 2] < 1.02) &
        (v[:, 1] > 0.14) & (v[:, 1] < 0.54)
    )
    hx = float(np.median(v[head, 0]))
    hz = 0.73
    hy = 0.33
    v[head, 0] = hx + (v[head, 0] - hx) * 0.69
    v[head, 1] = hy + (v[head, 1] - hy) * 0.80
    v[head, 2] = hz + (v[head, 2] - hz) * 0.96 + 0.012

    neck = (
        (v[:, 2] > 0.30) & (v[:, 2] < 0.67) &
        (v[:, 1] > 0.02) & (v[:, 1] < 0.47)
    )
    v[neck, 0] = cx + (v[neck, 0] - cx) * 0.74
    neck_center_y = 0.25
    v[neck, 1] = neck_center_y + (v[neck, 1] - neck_center_y) * 0.86

    # Collapse lateral ear-like remnants toward the skull before deleting the
    # old high crest. This avoids the four-prong silhouette seen in v14.
    ear_like = (
        (v[:, 2] > 0.40) & (v[:, 2] < 0.84) &
        (v[:, 1] > 0.31) & (v[:, 1] < 0.47) &
        (np.abs(v[:, 0] - cx) > 0.050)
    )
    v[ear_like, 0] = cx + (v[ear_like, 0] - cx) * 0.58
    v[ear_like, 1] = 0.35 + (v[ear_like, 1] - 0.35) * 0.45

    # 3) Limbs: retain v14 length, but reduce shaft/foot bulk.
    fore_leg = ((v[:, 2] > 0.18) & (v[:, 2] < 0.50) & (v[:, 1] < -0.05))
    hind_leg = ((v[:, 2] > -0.54) & (v[:, 2] < -0.15) & (v[:, 1] < -0.02))
    leg_mask = fore_leg | hind_leg
    v[leg_mask, 0] = cx + (v[leg_mask, 0] - cx) * 0.74

    foot = (v[:, 1] < -0.62)
    v[foot, 0] = cx + (v[foot, 0] - cx) * 0.74
    v[foot, 2] *= 1.015
    v[foot, 1] += 0.030

    # Side-view limb slimming: v16 mainly narrowed X, so shafts still read
    # too thick in profile. Compress longitudinal thickness around each limb.
    fore_center_z = 0.33
    hind_center_z = -0.34
    v[fore_leg, 2] = fore_center_z + (v[fore_leg, 2] - fore_center_z) * 0.82
    v[hind_leg, 2] = hind_center_z + (v[hind_leg, 2] - hind_center_z) * 0.84

    fore_upper = (
        (v[:, 2] > 0.17) & (v[:, 2] < 0.50) &
        (v[:, 1] > -0.34) & (v[:, 1] < 0.16)
    )
    hind_upper = (
        (v[:, 2] > -0.56) & (v[:, 2] < -0.14) &
        (v[:, 1] > -0.36) & (v[:, 1] < 0.14)
    )
    v[fore_upper, 2] = fore_center_z + (v[fore_upper, 2] - fore_center_z) * 0.88
    v[hind_upper, 2] = hind_center_z + (v[hind_upper, 2] - hind_center_z) * 0.88

    # Reduce shoulder/rump peaks so the top line reads as a fast alien runner,
    # not a familiar ungulate.
    shoulder = ((v[:, 2] > 0.10) & (v[:, 2] < 0.42) & (v[:, 1] > 0.18))
    rump = ((v[:, 2] > -0.44) & (v[:, 2] < -0.08) & (v[:, 1] > 0.15))
    v[shoulder, 1] -= 0.050
    v[rump, 1] -= 0.060

    # 4) Local silhouette surgery. v17 improved global width but the neck/chest
    # junction and upper limb masses still read as one horse-like block.
    torso_core = (
        (v[:, 2] > -0.36) & (v[:, 2] < 0.30) &
        (v[:, 1] > -0.12) & (v[:, 1] < 0.24)
    )
    torso_center_y = 0.065
    v[torso_core, 1] = torso_center_y + (v[torso_core, 1] - torso_center_y) * 0.86

    lower_neck = (
        (v[:, 2] > 0.27) & (v[:, 2] < 0.54) &
        (v[:, 1] > 0.03) & (v[:, 1] < 0.34)
    )
    v[lower_neck, 0] = cx + (v[lower_neck, 0] - cx) * 0.68
    lower_neck_center_y = 0.19
    v[lower_neck, 1] = lower_neck_center_y + (v[lower_neck, 1] - lower_neck_center_y) * 0.80

    chest_front = (
        (v[:, 2] > 0.08) & (v[:, 2] < 0.40) &
        (v[:, 1] > -0.14) & (v[:, 1] < 0.22)
    )
    chest_center_z = 0.24
    v[chest_front, 0] = cx + (v[chest_front, 0] - cx) * 0.72
    v[chest_front, 2] = chest_center_z + (v[chest_front, 2] - chest_center_z) * 0.82

    shoulder_mass = (
        (v[:, 2] > 0.14) & (v[:, 2] < 0.48) &
        (v[:, 1] > -0.30) & (v[:, 1] < 0.12)
    )
    v[shoulder_mass, 0] = cx + (v[shoulder_mass, 0] - cx) * 0.70
    v[shoulder_mass, 2] = fore_center_z + (v[shoulder_mass, 2] - fore_center_z) * 0.80

    thigh_mass = (
        (v[:, 2] > -0.56) & (v[:, 2] < -0.13) &
        (v[:, 1] > -0.32) & (v[:, 1] < 0.12)
    )
    v[thigh_mass, 0] = cx + (v[thigh_mass, 0] - cx) * 0.68
    v[thigh_mass, 2] = hind_center_z + (v[thigh_mass, 2] - hind_center_z) * 0.78

    muzzle = (
        (v[:, 2] > 0.72) & (v[:, 2] < 1.10) &
        (v[:, 1] > 0.16) & (v[:, 1] < 0.46)
    )
    muzzle_center_y = 0.31
    v[muzzle, 0] = hx + (v[muzzle, 0] - hx) * 0.64
    v[muzzle, 1] = muzzle_center_y + (v[muzzle, 1] - muzzle_center_y) * 0.76

    # v18 left a large C-shaped rear limb in side view. Pull the lower hind
    # shaft toward a gentle rearward center line instead of scaling the whole
    # thigh again.
    hind_shaft = (
        (v[:, 2] > -0.58) & (v[:, 2] < -0.12) &
        (v[:, 1] > -0.72) & (v[:, 1] < -0.16)
    )
    hind_t = np.clip((-v[hind_shaft, 1] - 0.16) / 0.56, 0.0, 1.0)
    hind_line_z = -0.34 - 0.055 * hind_t
    v[hind_shaft, 2] = hind_line_z + (v[hind_shaft, 2] - hind_line_z) * 0.72

    rear_dorsal = (
        (v[:, 2] > -0.56) & (v[:, 2] < -0.12) &
        (v[:, 1] > 0.12)
    )
    v[rear_dorsal, 1] = 0.12 + (v[rear_dorsal, 1] - 0.12) * 0.48

    face_original = original[f]

    # Remove the legacy fan/high crest and feather tail from source geometry.
    crest_vertex = (
        (face_original[:, :, 1] > 0.40) &
        (face_original[:, :, 2] > 0.08) &
        (face_original[:, :, 2] < 0.92)
    )
    remove_crest = (crest_vertex.sum(axis=1) >= 2)

    tail_vertex = (
        (face_original[:, :, 2] < -0.55) &
        (face_original[:, :, 1] > -0.36)
    )
    remove_tail = (tail_vertex.sum(axis=1) >= 2)

    keep = ~(remove_crest | remove_tail)
    body_mesh = trimesh.Trimesh(
        vertices=v,
        faces=f[keep],
        process=False,
        visual=source.visual,
    )
    body_mesh.remove_unreferenced_vertices()
    body_mesh, source_component_count_after_cut, detached_faces_removed = keep_largest_component(body_mesh)

    # Preserve the new silhouette but remove the worst triangulated spikes.
    # Taubin smoothing is intentionally mild to avoid shrinking long limbs.
    trimesh.smoothing.filter_taubin(
        body_mesh,
        lamb=0.28,
        nu=0.30,
        iterations=4,
    )

    # 4) Two swept blade crests. These deliberately replace the round
    # antler-like v14 tubes with flat aerodynamic plates.
    crest = []
    for side in (-1.0, 1.0):
        x0 = cx + side * 0.036
        points = np.array([
            [x0, 0.402, 0.605],
            [x0 + side * 0.002, 0.438, 0.525],
            [x0 + side * 0.003, 0.475, 0.425],
            [x0 + side * 0.002, 0.515, 0.310],
            [x0, 0.548, 0.185],
        ])
        crest.append(blade_mesh(
            points,
            [0.020, 0.022, 0.019, 0.013, 0.0025],
            [0.006, 0.0055, 0.0048, 0.0035, 0.0012],
        ))

    # 5) One thin, nearly horizontal tail with a gentle downward release.
    tail = tube_mesh(
        np.array([
            [cx, 0.035, -0.52],
            [cx, 0.026, -0.69],
            [cx, 0.010, -0.87],
            [cx, -0.014, -1.04],
            [cx, -0.040, -1.18],
        ]),
        [0.026, 0.022, 0.016, 0.009, 0.0022],
        [0.029, 0.025, 0.018, 0.010, 0.0022],
        sections=10,
    )

    out = trimesh.Scene()
    out.add_geometry(body_mesh, geom_name="S_body", node_name="S_body")
    out.add_geometry(crest[0], geom_name="S_crest_L", node_name="S_crest_L")
    out.add_geometry(crest[1], geom_name="S_crest_R", node_name="S_crest_R")
    out.add_geometry(tail, geom_name="S_tail", node_name="S_tail")
    out.export(output_path)

    meta = {
        "status": "shape_refine_v20_head_hindline_balance_candidate_not_canonical",
        "source_vertices": int(len(original)),
        "source_faces": int(len(f)),
        "body_vertices_after_surgery": int(len(body_mesh.vertices)),
        "body_faces_after_surgery": int(len(body_mesh.faces)),
        "removed_crest_faces": int(remove_crest.sum()),
        "removed_tail_faces": int(remove_tail.sum()),
        "collapsed_ear_like_vertices": int(ear_like.sum()),
        "source_component_count_after_cut": source_component_count_after_cut,
        "detached_faces_removed": detached_faces_removed,
        "new_crest_count": 2,
        "crest_geometry": "swept_blade_prism",
        "new_tail_count": 1,
        "coordinate_basis": "raw_glb_x_lateral_y_vertical_z_longitudinal_head_positive_z",
        "preview_rotation_y": "-pi/2",
        "reference": "public/concept/S.webp",
        "source": os.path.basename(input_path),
        "output": os.path.basename(output_path),
    }
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    if not os.path.exists(output_path) or os.path.getsize(output_path) < 1024:
        raise RuntimeError("v20 GLB missing or too small")
    print("SHAPE_V20", json.dumps(meta, separators=(",", ":")))


if __name__ == "__main__":
    main()
