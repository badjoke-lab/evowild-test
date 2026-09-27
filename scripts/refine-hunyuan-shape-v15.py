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
    v[body, 0] = cx + (v[body, 0] - cx) * 0.86

    waist = (
        (v[:, 2] > -0.14) & (v[:, 2] < 0.13) &
        (v[:, 1] > -0.14) & (v[:, 1] < 0.22)
    )
    v[waist, 0] = cx + (v[waist, 0] - cx) * 0.82

    belly = (
        (v[:, 2] > -0.46) & (v[:, 2] < 0.38) &
        (v[:, 1] > -0.24) & (v[:, 1] < 0.08)
    )
    factor = np.clip((0.08 - v[belly, 1]) / 0.32, 0.0, 1.0)
    v[belly, 1] += 0.078 * factor

    # 2) Head/neck: make the head smaller and more wedge-like and remove
    # some of the deer/horse read from the lower crest/ear region.
    head = (
        (v[:, 2] > 0.52) & (v[:, 2] < 1.02) &
        (v[:, 1] > 0.14) & (v[:, 1] < 0.54)
    )
    hx = float(np.median(v[head, 0]))
    hz = 0.73
    hy = 0.33
    v[head, 0] = hx + (v[head, 0] - hx) * 0.74
    v[head, 1] = hy + (v[head, 1] - hy) * 0.84
    v[head, 2] = hz + (v[head, 2] - hz) * 1.08 + 0.018

    neck = (
        (v[:, 2] > 0.30) & (v[:, 2] < 0.67) &
        (v[:, 1] > 0.02) & (v[:, 1] < 0.47)
    )
    v[neck, 0] = cx + (v[neck, 0] - cx) * 0.80
    neck_center_y = 0.25
    v[neck, 1] = neck_center_y + (v[neck, 1] - neck_center_y) * 0.90

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
    v[leg_mask, 0] = cx + (v[leg_mask, 0] - cx) * 0.82

    foot = (v[:, 1] < -0.62)
    v[foot, 0] = cx + (v[foot, 0] - cx) * 0.82
    v[foot, 2] *= 1.045
    v[foot, 1] += 0.022

    # Reduce shoulder/rump peaks so the top line reads as a fast alien runner,
    # not a familiar ungulate.
    shoulder = ((v[:, 2] > 0.10) & (v[:, 2] < 0.42) & (v[:, 1] > 0.18))
    rump = ((v[:, 2] > -0.44) & (v[:, 2] < -0.08) & (v[:, 1] > 0.15))
    v[shoulder, 1] -= 0.038
    v[rump, 1] -= 0.048

    face_original = original[f]

    # Remove the legacy fan/high crest and feather tail from source geometry.
    crest_vertex = (
        (face_original[:, :, 1] > 0.42) &
        (face_original[:, :, 2] > 0.36) &
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

    # 4) Two swept blade crests. These deliberately replace the round
    # antler-like v14 tubes with flat aerodynamic plates.
    crest = []
    for side in (-1.0, 1.0):
        x0 = cx + side * 0.036
        points = np.array([
            [x0, 0.405, 0.615],
            [x0 + side * 0.002, 0.455, 0.525],
            [x0 + side * 0.003, 0.505, 0.405],
            [x0 + side * 0.002, 0.552, 0.270],
            [x0, 0.585, 0.125],
        ])
        crest.append(blade_mesh(
            points,
            [0.028, 0.030, 0.026, 0.018, 0.003],
            [0.008, 0.007, 0.006, 0.004, 0.0015],
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
        "status": "shape_refine_v15_reference_silhouette_candidate_not_canonical",
        "source_vertices": int(len(original)),
        "source_faces": int(len(f)),
        "body_vertices_after_surgery": int(len(body_mesh.vertices)),
        "body_faces_after_surgery": int(len(body_mesh.faces)),
        "removed_crest_faces": int(remove_crest.sum()),
        "removed_tail_faces": int(remove_tail.sum()),
        "collapsed_ear_like_vertices": int(ear_like.sum()),
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
        raise RuntimeError("v15 GLB missing or too small")
    print("SHAPE_V15", json.dumps(meta, separators=(",", ":")))


if __name__ == "__main__":
    main()
