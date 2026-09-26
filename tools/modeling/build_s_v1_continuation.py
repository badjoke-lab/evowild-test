#!/usr/bin/env python3
"""
EvoWild Run — S modeling continuity builder.

This is NOT an Astra-generated model. It is a deterministic fallback builder
created after the Work/Astra session hit its usage cap, so the S-only modeling
lane has a reproducible continuation point.

Design authority:
  docs/references/evowild-creature-reference-sheet-20260921.jpg
  public/concept/S.webp
  public/concept/s-run-sheet.svg

Do not use the old procedural Motion First runner as a shape reference.

Usage:
  python tools/modeling/build_s_v1_continuation.py
  python tools/modeling/build_s_v1_continuation.py --out /tmp/evowild-s

Dependencies:
  numpy trimesh scikit-image
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import trimesh
from skimage import measure


def smin(a, b, k=.15):
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def ellipsoid(X, Y, Z, c, r):
    cx, cy, cz = c
    rx, ry, rz = r
    return (
        np.sqrt(((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 + ((Z - cz) / rz) ** 2) - 1
    ) * min(r)


def tapered_capsule(X, Y, Z, a, b, r0, r1):
    a = np.array(a, np.float32)
    b = np.array(b, np.float32)
    v = b - a
    px, py, pz = X - a[0], Y - a[1], Z - a[2]
    den = float(v @ v)
    t = np.clip((px * v[0] + py * v[1] + pz * v[2]) / den, 0, 1)
    qx, qy, qz = a[0] + t * v[0], a[1] + t * v[1], a[2] + t * v[2]
    r = r0 + (r1 - r0) * t
    return np.sqrt((X - qx) ** 2 + (Y - qy) ** 2 + (Z - qz) ** 2) - r


def mesh_sdf(fn, bounds, res, smooth=3):
    (xmin, xmax), (ymin, ymax), (zmin, zmax) = bounds
    nx, ny, nz = res
    xs = np.linspace(xmin, xmax, nx, dtype=np.float32)
    ys = np.linspace(ymin, ymax, ny, dtype=np.float32)
    zs = np.linspace(zmin, zmax, nz, dtype=np.float32)
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    V = fn(X, Y, Z).astype(np.float32)
    sp = (
        (xmax - xmin) / (nx - 1),
        (ymax - ymin) / (ny - 1),
        (zmax - zmin) / (nz - 1),
    )
    verts, faces, _, _ = measure.marching_cubes(V, 0, spacing=sp)
    verts += np.array([xmin, ymin, zmin])
    m = trimesh.Trimesh(verts, faces, process=True)
    if smooth:
        trimesh.smoothing.filter_taubin(m, iterations=smooth, lamb=.42, nu=-.46)
    m.remove_unreferenced_vertices()
    return m


def color(mesh, rgba):
    mesh.visual.face_colors = np.array(rgba, np.uint8)
    return mesh


def build(out: Path):
    out.mkdir(parents=True, exist_ok=True)

    def body_fn(X, Y, Z):
        # Athletic thorax + tucked waist + lighter pelvis.
        d = ellipsoid(X, Y, Z, (0, 1.90, 0.30), (0.37, 0.33, 0.69))
        d = smin(d, ellipsoid(X, Y, Z, (0, 1.91, -0.56), (0.33, 0.30, 0.54)), .18)
        d = smin(
            d,
            tapered_capsule(X, Y, Z, (0, 1.90, -0.34), (0, 1.91, 0.32), .20, .23),
            .14,
        )
        # Shoulder/withers integrated into chest.
        d = smin(d, ellipsoid(X, Y, Z, (0, 2.06, 0.56), (0.28, 0.24, 0.39)), .14)
        # Low forward neck; avoid the rejected tall generic-animal neck.
        d = smin(
            d,
            tapered_capsule(X, Y, Z, (0, 2.00, 0.86), (0, 2.15, 1.52), .18, .115),
            .13,
        )
        d = smin(d, ellipsoid(X, Y, Z, (0, 2.14, 1.44), (0.16, 0.17, 0.26)), .12)
        # Small directional head + tapered muzzle.
        d = smin(d, ellipsoid(X, Y, Z, (0, 2.17, 1.80), (0.15, 0.135, 0.285)), .10)
        d = smin(
            d,
            tapered_capsule(X, Y, Z, (0, 2.15, 1.90), (0, 2.08, 2.16), .105, .036),
            .08,
        )
        # Short structural tail integrated into pelvis.
        d = smin(
            d,
            tapered_capsule(X, Y, Z, (0, 1.92, -1.02), (0, 1.82, -1.38), .13, .068),
            .10,
        )
        d = smin(
            d,
            tapered_capsule(X, Y, Z, (0, 1.82, -1.35), (0, 1.69, -1.60), .068, .025),
            .06,
        )
        return d

    body = mesh_sdf(
        body_fn,
        ((-0.68, .68), (1.20, 2.60), (-1.95, 2.40)),
        (86, 106, 190),
        4,
    )

    # Pale body flowing to dark head/neck and a muted darker tail.
    cent = body.triangles_center
    light = np.array([204, 219, 228], dtype=float)
    dark = np.array([42, 55, 74], dtype=float)
    tailc = np.array([78, 98, 118], dtype=float)
    t = np.clip((cent[:, 2] - 0.68) / (1.18 - 0.68), 0, 1)[:, None]
    rgb = light[None, :] * (1 - t) + dark[None, :] * t
    tt = np.clip((-cent[:, 2] - 0.82) / (1.55 - 0.82), 0, 1)[:, None]
    rgb = rgb * (1 - tt) + tailc[None, :] * tt
    fc = np.concatenate(
        [
            np.clip(rgb, 0, 255).astype(np.uint8),
            np.full((len(body.faces), 1), 255, dtype=np.uint8),
        ],
        axis=1,
    )
    body.visual.face_colors = fc

    def underside_fn(X, Y, Z):
        d = tapered_capsule(X, Y, Z, (0, 1.66, -0.40), (0, 1.67, 0.42), .12, .14)
        d = smin(
            d,
            tapered_capsule(X, Y, Z, (0, 1.69, .46), (0, 1.91, 1.20), .13, .060),
            .10,
        )
        return d

    under = color(
        mesh_sdf(
            underside_fn,
            ((-.30, .30), (1.25, 2.05), (-.75, 1.40)),
            (48, 64, 108),
            2,
        ),
        [38, 48, 61, 255],
    )

    limbs = {}
    armor = {}
    specs = {
        "fore_L": (-.30, True, -1),
        "fore_R": (.30, True, 1),
        "hind_L": (-.28, False, -1),
        "hind_R": (.28, False, 1),
    }

    for name, (x, fore, side) in specs.items():
        if fore:
            pts = [
                (x, 1.90, .67),
                (x + .020 * side, 1.33, .82),
                (x - .015 * side, .73, .63),
                (x + .010 * side, .18, .86),
            ]
            rs = [.125, .105, .071, .046]
        else:
            pts = [
                (x, 1.89, -.66),
                (x + .035 * side, 1.34, -.48),
                (x - .025 * side, .83, -.86),
                (x + .015 * side, .18, -.68),
            ]
            rs = [.145, .118, .076, .048]

        def limb_fn(X, Y, Z, pts=pts, rs=rs):
            d = tapered_capsule(X, Y, Z, pts[0], pts[1], rs[0], rs[1])
            d = smin(d, tapered_capsule(X, Y, Z, pts[1], pts[2], rs[1], rs[2]), .075)
            d = smin(d, tapered_capsule(X, Y, Z, pts[2], pts[3], rs[2], rs[3]), .055)
            x0, _, z0 = pts[3]
            d = smin(
                d,
                tapered_capsule(X, Y, Z, (x0, .16, z0), (x0 - .045, .12, z0 + .22), .055, .026),
                .04,
            )
            d = smin(
                d,
                tapered_capsule(X, Y, Z, (x0, .16, z0), (x0 + .045, .12, z0 + .23), .055, .026),
                .04,
            )
            return d

        zvals = [p[2] for p in pts]
        limb = mesh_sdf(
            limb_fn,
            ((x - .26, x + .26), (.05, 2.08), (min(zvals) - .30, max(zvals) + .36)),
            (52, 150, 82),
            2,
        )
        color(limb, [55, 72, 90, 255])
        limbs[name] = limb

        rootc = pts[0]
        cap = trimesh.creation.icosphere(subdivisions=2, radius=1)
        cap.apply_scale([.11, .16, .25 if fore else .23])
        cap.apply_translation(rootc)
        color(cap, [198, 213, 222, 255])
        armor[name + "_root"] = cap

        kneec = pts[1]
        kc = trimesh.creation.icosphere(subdivisions=1, radius=1)
        kc.apply_scale([.085, .085, .12])
        kc.apply_translation(kneec)
        color(kc, [108, 152, 188, 255])
        armor[name + "_knee"] = kc

    def horn(points, radii, rgba):
        meshes = []
        for i in range(len(points) - 1):
            a, b = points[i], points[i + 1]
            r0, r1 = radii[i], radii[i + 1]
            mins = np.minimum(a, b) - max(r0, r1) * 2
            maxs = np.maximum(a, b) + max(r0, r1) * 2

            def fn(X, Y, Z, a=a, b=b, r0=r0, r1=r1):
                return tapered_capsule(X, Y, Z, a, b, r0, r1)

            meshes.append(
                mesh_sdf(
                    fn,
                    ((mins[0], maxs[0]), (mins[1], maxs[1]), (mins[2], maxs[2])),
                    (34, 42, 72),
                    1,
                )
            )
        m = trimesh.util.concatenate(meshes)
        return color(m, rgba)

    crest_main = horn(
        [(0, 2.31, 1.68), (0, 2.50, 1.28), (0, 2.65, .76), (0, 2.69, .26)],
        [.105, .085, .060, .024],
        [50, 74, 106, 255],
    )
    crest_lower = horn(
        [(0, 2.27, 1.64), (0, 2.40, 1.24), (0, 2.49, .82)],
        [.075, .052, .020],
        [90, 151, 205, 255],
    )

    eyes = {}
    for side in (-1, 1):
        e = trimesh.creation.icosphere(subdivisions=2, radius=1)
        e.apply_scale([.025, .032, .038])
        e.apply_translation([.145 * side, 2.205, 1.92])
        color(e, [244, 191, 58, 255])
        eyes[f"eye_{side}"] = e

    plates = {}
    for side in (-1, 1):
        sh = trimesh.creation.icosphere(subdivisions=2, radius=1)
        sh.apply_scale([.065, .12, .40])
        sh.apply_translation([.37 * side, 2.06, .39])
        color(sh, [188, 207, 220, 255])
        plates[f"shoulder_{side}"] = sh

        hp = trimesh.creation.icosphere(subdivisions=2, radius=1)
        hp.apply_scale([.060, .105, .30])
        hp.apply_translation([.31 * side, 2.01, -.58])
        color(hp, [145, 181, 206, 255])
        plates[f"hip_{side}"] = hp

    spine = trimesh.creation.icosphere(subdivisions=2, radius=1)
    spine.apply_scale([.055, .075, .45])
    spine.apply_translation([0, 2.20, .02])
    color(spine, [116, 171, 210, 255])
    plates["spine"] = spine

    cue = {}

    def cap_piece(a, b, r, rgba):
        mins = np.minimum(a, b) - r * 2
        maxs = np.maximum(a, b) + r * 2

        def fn(X, Y, Z):
            return tapered_capsule(X, Y, Z, a, b, r, r)

        return color(
            mesh_sdf(
                fn,
                ((mins[0], maxs[0]), (mins[1], maxs[1]), (mins[2], maxs[2])),
                (32, 34, 54),
                1,
            ),
            rgba,
        )

    cue["top"] = cap_piece((-.12, 2.32, 1.76), (.12, 2.32, 1.76), .034, [28, 38, 49, 255])
    cue["left"] = cap_piece((-.14, 2.30, 1.72), (-.165, 2.20, 1.80), .036, [28, 38, 49, 255])
    cue["right"] = cap_piece((.14, 2.30, 1.72), (.165, 2.20, 1.80), .036, [28, 38, 49, 255])

    for side, rgba in [(-1, [248, 177, 58, 255]), (1, [51, 216, 255, 255])]:
        light = trimesh.creation.icosphere(subdivisions=1, radius=1)
        light.apply_scale([.038, .038, .048])
        light.apply_translation([.182 * side, 2.245, 1.82])
        color(light, rgba)
        cue["light" + str(side)] = light

    scene = trimesh.Scene()
    scene.add_geometry(body, node_name="Body", geom_name="Body")
    scene.add_geometry(under, node_name="Underside", geom_name="Underside")
    for n, m in eyes.items():
        scene.add_geometry(m, node_name=n, geom_name=n)
    for n, m in limbs.items():
        scene.add_geometry(m, node_name=n, geom_name=n)
    for n, m in armor.items():
        scene.add_geometry(m, node_name=n, geom_name=n)
    scene.add_geometry(crest_main, node_name="Crest_Main", geom_name="Crest_Main")
    scene.add_geometry(crest_lower, node_name="Crest_Lower", geom_name="Crest_Lower")
    for n, m in plates.items():
        scene.add_geometry(m, node_name=n, geom_name=n)
    for n, m in cue.items():
        scene.add_geometry(m, node_name="Cue_" + n, geom_name="Cue_" + n)

    # Ground to y=0; +Z is forward.
    shift = [0, -scene.bounds[0][1], 0]
    for g in scene.geometry.values():
        g.apply_translation(shift)

    glb_path = out / "s-v1.glb"
    glb_path.write_bytes(trimesh.exchange.gltf.export_glb(scene))

    print(
        "wrote",
        glb_path,
        "faces",
        sum(len(g.faces) for g in scene.geometry.values()),
        "geometries",
        len(scene.geometry),
        "bounds",
        scene.bounds,
    )


def main():
    parser = argparse.ArgumentParser()
    repo_root = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--out",
        type=Path,
        default=repo_root / "public" / "models" / "astra",
        help="Output directory; default is public/models/astra",
    )
    args = parser.parse_args()
    build(args.out)


if __name__ == "__main__":
    main()
