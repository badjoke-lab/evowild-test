"""Edit saved R2 foot meshes through Blender MCP; never rebuild the creature.

Existing 10-sided toe rings are reshaped into a faceted split wedge with an
explicit sole. Existing ivory/blue meshes are fitted to those surfaces.
No new objects, mesh elements, materials, limb poses or studio changes.
All output model paths must be new. Execute once in a fresh checkout.
"""
import bpy
import bmesh
import hashlib
import json
import math
import shutil
import struct
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'S_ZERO_CANDIDATE_REVISED_R2.blend'
COPY = ROOT / 'verification/S_ZERO_R3_WORKING_COPY.blend'
OUT = ROOT / 'verification/S_ZERO_R3_TRIAL_A.blend'
REPORT = ROOT / 'evidence/REVISION_R3_TRIAL_A.json'
EXPECTED = '3406e12f54670ca397eb31825721aa08e36fbc46a0bc68e2dcfbcbaae0c09662'
assert bpy.app.version == (4, 3, 2)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
assert all(not p.exists() for p in [COPY, OUT, REPORT])
shutil.copyfile(SOURCE, COPY)
assert COPY.read_bytes() == SOURCE.read_bytes()
bpy.ops.wm.open_mainfile(filepath=str(COPY), load_ui=False)


def signature(ob):
    h = hashlib.sha256()
    for v in ob.data.vertices:
        h.update(struct.pack('<3f', *v.co))
    for p in ob.data.polygons:
        h.update(struct.pack('<' + 'I' * len(p.vertices), *p.vertices))
        h.update(struct.pack('<I?', p.material_index, p.use_smooth))
    for row in ob.matrix_world:
        h.update(struct.pack('<4f', *row))
    return h.hexdigest()


collection = bpy.data.collections['S_ZERO_CREATURE']
before = {o.name: signature(o) for o in collection.objects if o.type == 'MESH'}
changes = []
# Local x, top, bottom, half-width, distance from foot midline.
# Forward is -X. Ground is Z=-0.018, outsole is Z=-0.016.
sections = [
    (.050, .188, .028, .025, .042),
    (.033, .203, -.008, .033, .043),
    (.007, .193, -.016, .043, .049),
    (-.025, .171, -.016, .045, .054),
    (-.062, .142, -.016, .044, .057),
    (-.101, .111, -.016, .040, .059),
    (-.140, .079, -.016, .034, .059),
    (-.175, .052, -.016, .028, .058),
    (-.210, .028, -.016, .019, .056),
    (-.234, .012, -.016, .010, .054),
]
# Same winding and vertex count as the original R2 cross sections.
profile = [(1, .28), (.86, 0), (.28, 0), (-.28, 0), (-.86, 0),
           (-1, .28), (-.74, .82), (-.28, 1), (.28, 1), (.74, .82)]
feet = [('FORE_NEAR', -.45, -.29), ('FORE_FAR', -1.46, .28),
        ('HIND_NEAR', 1.97, -.28), ('HIND_FAR', .64, .28)]


def section_at(x):
    x = max(sections[-1][0], min(sections[0][0], x))
    for a, b in zip(sections, sections[1:]):
        if b[0] <= x <= a[0]:
            t = (a[0] - x) / (a[0] - b[0])
            return tuple(v * (1 - t) + w * t for v, w in zip(a, b))
    return sections[-1]


def roof(x, lateral):
    _, top, bottom, width, _ = section_at(x)
    a = abs(lateral) / width
    if a <= .28:
        fraction = 1.0
    elif a <= .74:
        fraction = 1 - (a - .28) / .46 * .18
    else:
        fraction = .82 - (a - .74) / .26 * .54
    return bottom + fraction * (top - bottom)


def finish(ob, old):
    ob.data.update()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges), ob.name
    assert all(f.calc_area() > 1e-12 for f in bm.faces), ob.name
    bm.to_mesh(ob.data)
    bm.free()
    changes.append({'name': ob.name, 'vertices': len(old),
                    'moved': sum((v.co - a).length > 1e-7 for v, a in zip(ob.data.vertices, old)),
                    'max_displacement': max((v.co - a).length for v, a in zip(ob.data.vertices, old)),
                    'before': before[ob.name], 'after': signature(ob)})


def fit_top_detail(ob, fx, fy, k, signal=False):
    """Flatten the existing rounded ivory/blue cap into a surface-following ridge."""
    old = [v.co.copy() for v in ob.data.vertices]
    sides = 8 if signal else 10
    assert len(old) == 7 * sides + 2
    for ring in range(7):
        t = ring / 6
        x = -.204 + .154 * t
        _, _, _, _, center = section_at(x)
        width = (.0025 + .0025 * math.sin(math.pi * t)) if signal else (.006 + .009 * math.sin(math.pi * t))
        offset = -.005 if signal else 0
        for j in range(sides):
            angle = 2 * math.pi * j / sides
            dy = offset + width * math.cos(angle)
            z = roof(x, dy) + (.0048 if signal else .0014) + .0012 * math.sin(angle)
            ob.data.vertices[ring * sides + j].co = (fx + x, fy + k * center + dy, z)
    for end, ring in [(7 * sides, 0), (7 * sides + 1, 6)]:
        ob.data.vertices[end].co = sum((ob.data.vertices[ring * sides + j].co for j in range(sides)), Vector()) / sides
    for p in ob.data.polygons:
        p.use_smooth = False
    finish(ob, old)


def fit_side_detail(ob, fx, fy, k, side, signal=False):
    old = [v.co.copy() for v in ob.data.vertices]
    assert len(old) == 10
    # x and normalized height on the original side of each existing toe.
    outline = ([(-.17, .38), (-.085, .73), (-.064, .69), (-.14, .31)] if signal else
               [(-.19, .40), (-.055, .88), (-.005, .65), (-.12, .18)])
    center = tuple(sum(p[i] for p in outline) / 4 for i in range(2))
    parameters = [(x, h, -.0003) for x, h in outline]
    parameters += [(center[0] + (x - center[0]) * .56, center[1] + (h - center[1]) * .56, .0012)
                   for x, h in outline]
    parameters += [(*center, .0020), (*center, -.0018)]
    for vertex, (x, fraction, relief) in zip(ob.data.vertices, parameters):
        _, top, bottom, width, distance = section_at(x)
        if fraction >= .82:
            lateral = .28 + (1 - fraction) / .18 * .46
        elif fraction >= .28:
            lateral = .74 + (.82 - fraction) / .54 * .26
        else:
            lateral = .86 + fraction / .28 * .14
        vertex.co = (fx + x, fy + k * distance + side * (width * lateral + relief),
                     bottom + fraction * (top - bottom))
    finish(ob, old)


for name, fx, fy in feet:
    side = -1 if fy < 0 else 1
    for k in [-1, 1]:
        suffix = name + '_' + str(k)
        ob = bpy.data.objects['TOE_' + suffix]
        old = [v.co.copy() for v in ob.data.vertices]
        assert len(old) == 102 and len(ob.data.polygons) == 110
        for ring, (x, top, bottom, width, distance) in enumerate(sections):
            for j, (lateral, fraction) in enumerate(profile):
                ob.data.vertices[ring * 10 + j].co = (fx + x, fy + k * distance + width * lateral,
                                                       bottom + fraction * (top - bottom))
        for end, ring in [(100, 0), (101, 9)]:
            ob.data.vertices[end].co = sum((ob.data.vertices[ring * 10 + j].co for j in range(10)), Vector()) / 10
        for p in ob.data.polygons:
            p.use_smooth = False
        finish(ob, old)
        fit_top_detail(bpy.data.objects['HOOF_FACE_' + suffix], fx, fy, k)
        fit_top_detail(bpy.data.objects['HOOF_SIGNAL_' + suffix], fx, fy, k, signal=True)
        fit_side_detail(bpy.data.objects['TOE_IVORY_' + suffix], fx, fy, k, side)
        fit_side_detail(bpy.data.objects['TOE_CYAN_' + suffix], fx, fy, k, side, signal=True)

after = {o.name: signature(o) for o in collection.objects if o.type == 'MESH'}
changed = sorted(n for n in before if before[n] != after[n])
assert changed == sorted(r['name'] for r in changes)
assert len(changed) == 40 and set(before) == set(after)
assert before['S_ZERO_BODY_CONTINUOUS'] == after['S_ZERO_BODY_CONTINUOUS']
bpy.context.scene['stage'] = 'R3_TRIAL_A'
bpy.context.scene['candidate_status'] = 'Foot wedge trial; needs real render review; overall REVISE'
bpy.context.scene.camera = bpy.data.objects['CAM_FRONT34']
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
REPORT.write_text(json.dumps({'source': SOURCE.name, 'source_sha256': EXPECTED,
    'working_copy_sha256': hashlib.sha256(COPY.read_bytes()).hexdigest(),
    'output': str(OUT.relative_to(ROOT)), 'output_sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(),
    'method': 'Existing foot vertices reshaped; topology and object set retained. No source generator executed.',
    'scope': '8 split toes and 32 existing surface details only. Body, ankles, crown, tail and studio untouched.',
    'sections': sections, 'cross_section': profile, 'changes': changes,
    'unchanged_meshes': sorted(n for n in before if before[n] == after[n]),
    'floor_z': -.018, 'sole_z': -.016, 'decision': 'PENDING visual review'}, indent=2) + '\n')
print('R3_TRIAL_A_SAVED', len(changed), 'foot meshes edited;', len(before) - len(changed), 'meshes unchanged')
