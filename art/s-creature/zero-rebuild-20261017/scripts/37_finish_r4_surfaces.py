"""Remove incidental triangle shading while retaining D's sculpted sections.

No vertices, colors or outline change. Smooth interpolation on the four
locally retopologized shells; real edges above 35 degrees remain sharp.
"""
import bpy
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'verification/S_ZERO_R4_TRIAL_D.blend'
OUT=ROOT/'verification/S_ZERO_R4_TRIAL_E.blend'
REPORT=ROOT/'evidence/REVISION_R4_TRIAL_E.json'
assert not OUT.exists() and not REPORT.exists()
audit=json.loads((ROOT/'evidence/VERIFY_S_ZERO_R4_TRIAL_D_RELOAD.json').read_text())
assert not any(r.get('nonadjacent_self_overlap_candidates') for r in audit['meshes'])
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
changed=[]
for ob in bpy.data.collections['S_ZERO_CREATURE'].objects:
    if ob.name.startswith(('CROWN_MAIN_','CROWN_BLUE_')):
        for p in ob.data.polygons:
            p.use_smooth=True
        ob.data.set_sharp_from_angle(angle=math.radians(35))
        ob.data.update();changed.append(ob.name)
bpy.context.scene['stage']='R4_TRIAL_E'
bpy.context.scene['candidate_status']='REVISE; D geometry with incidental triangle shading removed; visual review pending'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
REPORT.write_text(json.dumps({'source':str(SOURCE.relative_to(ROOT)),'output':str(OUT.relative_to(ROOT)),
    'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'output_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'changed_shading_meshes':changed,
    'geometry_changed_from_D':False,'reason':'D exposes incidental triangulation in SIDE and FRONT34; preserve sculpt and interpolate normals, with sharp edges over 35 degrees.'},indent=2)+'\n')
print('R4_TRIAL_E_SAVED',changed)
