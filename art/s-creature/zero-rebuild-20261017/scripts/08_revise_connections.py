"""Focused sculpt on existing CANDIDATE vertices after five-view REVISE decision.
No source builder is executed. No original file is saved. All untouched meshes
must retain their geometry hashes. Keeps source vertex topology for editability.
"""
import bpy
import hashlib
import json
import math
import struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'S_ZERO_CANDIDATE_REVISED_R1.blend'
assert bpy.app.version == (4, 3, 2)
assert Path(bpy.data.filepath).name == 'S_ZERO_CANDIDATE_REVIEW.blend'
assert not OUTPUT.exists(), 'Never overwrite a saved model'
source_hash = hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
assert source_hash == 'fac25ffe586cacd294c4d0b9f7ab4ae71f93595a3f70fcfa9354c5b44cbef29d'
model = bpy.data.collections['S_ZERO_CREATURE']
body = bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
targets = ['DELTOID_N', 'DELTOID_F', 'BRACHIAL_FORE_NEAR', 'BRACHIAL_FORE_FAR', 'PELVIS_N', 'PELVIS_F']


def geom_hash(obj):
    h = hashlib.sha256()
    for v in obj.data.vertices:
        h.update(struct.pack('<3f', *v.co))
    for p in obj.data.polygons:
        h.update(struct.pack('<' + 'I' * len(p.vertices), *p.vertices))
    return h.hexdigest()


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


before = {o.name: geom_hash(o) for o in model.objects if o.type == 'MESH'}
changes = []
for name in targets:
    obj = bpy.data.objects[name]
    old = [v.co.copy() for v in obj.data.vertices]
    side = -1 if name.endswith('_N') or name.endswith('_NEAR') else 1
    for v in obj.data.vertices:
        x, y, z = v.co
        if name.startswith('DELTOID'):
            # Flatten egg-like lateral fullness and draw the lower end into the arm.
            lower = ease((1.78 - z) / .38)
            upper = ease((z - 1.58) / .25)
            v.co.y = side * (abs(y) - .025 * upper + .065 * lower)
            v.co.x = -.84 + (x + .84) * (1.0 + .06 * upper)
        elif name.startswith('BRACHIAL'):
            # Existing upper-arm shell is buried in the core, leaving a white island.
            w = ease((z - 1.04) / .37)
            v.co.y += side * (.035 + .065 * w)
            v.co.z += .025 * w
        elif name.startswith('PELVIS'):
            # Reduce upper lateral bulb; uncover the lower anatomical taper.
            low = ease((1.76 - z) / .40)
            high = ease((z - 1.60) / .27)
            v.co.y += side * (.058 * low - .018 * high)
    # Constrained skin clearance on the outer half of each existing loft ring.
    # Same-side hit only, bounded displacement: avoids REFINED's cross-limb ray jumps.
    sides = 16
    ring_count = (len(obj.data.vertices) - 2) // sides
    for i in range(ring_count):
        ring = list(obj.data.vertices[i * sides:(i + 1) * sides])
        cy = sum(side * v.co.y for v in ring) / sides
        ry = max(side * v.co.y - cy for v in ring)
        for v in ring:
            outward = (side * v.co.y - cy) / max(.001, ry)
            weight = ease(outward / .65)
            if not weight:
                continue
            hit, normal, face, distance = bvh.ray_cast(Vector((v.co.x, side * 2, v.co.z)), Vector((0, -side, 0)), 4)
            if hit is None or side * hit.y <= .10:
                continue
            correction = max(0.0, min(.075, side * hit.y + .012 - side * v.co.y))
            v.co.y += side * correction * weight
    obj.data.update()
    obj['r1_sculpt'] = 'Existing loft vertices reshaped after five-view inspection; bounded same-side skin clearance'
    distances = [(v.co - previous).length for v, previous in zip(obj.data.vertices, old)]
    changes.append({'object': name, 'vertices': len(old),
                    'max_vertex_displacement': max(distances),
                    'mean_vertex_displacement': sum(distances) / len(distances),
                    'before_geometry_sha256': before[name], 'after_geometry_sha256': geom_hash(obj)})
after = {o.name: geom_hash(o) for o in model.objects if o.type == 'MESH'}
untouched = sorted(set(before) - set(targets))
assert all(before[n] == after[n] for n in untouched)
assert all(before[n] != after[n] for n in targets)
scene = bpy.context.scene
scene['stage'] = 'CANDIDATE_REVISED_R1'
scene['candidate_status'] = 'REVISE; focused shoulder/hip sculpt pending five-view review; not production KEEP'
scene['source_sha256'] = source_hash
scene.camera = bpy.data.objects['CAM_FRONT34']
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
report = {'source': 'verification/S_ZERO_CANDIDATE_REVIEW.blend', 'source_sha256': source_hash,
          'output': OUTPUT.name, 'output_sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
          'decision_trigger': 'evidence/CANDIDATE_REVIEW.json', 'changed_meshes': changes,
          'unchanged_mesh_count': len(untouched), 'unchanged_meshes': untouched,
          'topology_changed': False, 'limitations': 'Separate shell/core intersections and lack of deformation topology are not resolved by this local sculpt.'}
(ROOT / 'evidence' / 'REVISION_R1.json').write_text(json.dumps(report, indent=2) + '\n')
print('REVISION_SAVED', OUTPUT, 'changed', len(changes), 'unchanged', len(untouched), flush=True)
