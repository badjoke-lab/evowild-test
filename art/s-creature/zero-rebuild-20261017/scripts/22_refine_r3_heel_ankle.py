"""Refine the reviewed trial A: relieve the heel and seat existing ankle fins.

No added geometry. R2 and trial A are immutable. This script writes trial B.
"""
import bpy
import bmesh
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'verification/S_ZERO_R3_TRIAL_A.blend'
OUT = ROOT / 'verification/S_ZERO_R3_TRIAL_B.blend'
REPORT = ROOT / 'evidence/REVISION_R3_TRIAL_B.json'
assert not OUT.exists() and not REPORT.exists()
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False)
trial = json.loads((ROOT / 'evidence/REVISION_R3_TRIAL_A.json').read_text())
sections = trial['sections']
feet = [('FORE_NEAR', -.45, -.29, -.39, .20),
        ('FORE_FAR', -1.46, .28, -1.37, .37),
        ('HIND_NEAR', 1.97, -.28, 1.98, .23),
        ('HIND_FAR', .64, .28, .73, .22)]
changes = []


def section_at(x):
    x = max(sections[-1][0], min(sections[0][0], x))
    for a, b in zip(sections, sections[1:]):
        if b[0] <= x <= a[0]:
            t = (a[0] - x) / (a[0] - b[0])
            return tuple(v * (1 - t) + w * t for v, w in zip(a, b))
    return sections[-1]


def finish(ob, old):
    ob.data.update()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges), ob.name
    assert all(f.calc_area() > 1e-12 for f in bm.faces), ob.name
    bm.to_mesh(ob.data)
    bm.free()
    changes.append({'name': ob.name,
                    'moved_vertices': sum((v.co - a).length > 1e-7 for v, a in zip(ob.data.vertices, old)),
                    'max_displacement': max((v.co - a).length for v, a in zip(ob.data.vertices, old))})


for name, fx, fy, ankle_x, ankle_z in feet:
    for k in [-1, 1]:
        for prefix in ['TOE_', 'TOE_IVORY_', 'TOE_CYAN_', 'HOOF_FACE_', 'HOOF_SIGNAL_']:
            ob = bpy.data.objects[prefix + name + '_' + str(k)]
            old = [v.co.copy() for v in ob.data.vertices]
            for v in ob.data.vertices:
                x = v.co.x - fx
                if x <= -.04:
                    continue
                t = min(1, max(0, (x + .04) / .09))
                weight = t * t * (3 - 2 * t)
                _, top, bottom, width, distance = section_at(x)
                center_y = fy + k * distance
                v.co.y = center_y + (v.co.y - center_y) * (1 - .20 * weight)
                lower = min(1, max(0, (top - v.co.z) / (top - bottom)))
                v.co.z += .035 * weight * lower
            finish(ob, old)
    # Existing fin was authored at the penultimate leg station. On the far
    # foreleg this was mid-cannon (.37), not the actual ankle (.14-.20).
    # Move it to the ankle; shorten the existing outline without adding spurs.
    ob = bpy.data.objects['ANKLE_FIN_' + name]
    old = [v.co.copy() for v in ob.data.vertices]
    target_x = fx + .045
    target_z = .205
    side = -1 if fy < 0 else 1
    for v in ob.data.vertices:
        v.co.x = target_x + (v.co.x - ankle_x) * .78
        v.co.z = target_z + (v.co.z - ankle_z) * .72
        v.co.y -= side * .012
    finish(ob, old)

bpy.context.scene['stage'] = 'R3_TRIAL_B'
bpy.context.scene['candidate_status'] = 'Heel/ankle refinement pending real render review; overall REVISE'
bpy.context.scene.camera = bpy.data.objects['CAM_FRONT34']
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
REPORT.write_text(json.dumps({'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': source_hash,
    'output': str(OUT.relative_to(ROOT)), 'output_sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(),
    'trigger': 'Trial A improves wedge/contact but posterior foot block is too full; far-fore ankle fin was on the cannon.',
    'method': 'Existing vertices only: rear-foot lateral taper, heel sole relief, reposition/shorten four existing ankle fins.',
    'changes': changes, 'decision': 'PENDING visual review'}, indent=2) + '\n')
print('R3_TRIAL_B_SAVED', len(changes), 'existing meshes locally refined')
