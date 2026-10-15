"""Live Blender 4.3.2 shoulder pilot. Executed via Blender MCP, never on source.

Functions are retained in bpy.app.driver_namespace['shoulder_pilot'].
The baseline mesh copy is an internal rollback buffer, not a second body.
"""
import bpy, bmesh, numpy as np, json, hashlib
from pathlib import Path
from mathutils import Vector

ROOT = Path('/Users/lyla/evowild-test-sculpt')
STATION = ROOT / 'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012'
OUT = STATION / 'review-v5-shoulder-structure-pilot'
SOURCE = STATION / 'review-v5/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5_STAGE1.blend'
OUT.mkdir(exist_ok=True)
assert bpy.app.version[:3] == (4, 3, 2)
assert Path(bpy.data.filepath) == SOURCE
assert not bpy.data.is_dirty
body = bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4']
baseline = body.data.copy()
baseline.name = 'STAGE1_ROLLBACK_BUFFER'
baseline.use_fake_user = True
coords = np.array([v.co[:] for v in baseline.vertices], dtype=np.float32)
protected = [p for p in STATION.rglob('*.blend') if OUT not in p.parents]
protected += [ROOT / 'art/s-creature/references/00_s_type_modeling_image_v1.png']
hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
assert hashes[str(SOURCE.relative_to(ROOT))] == '96b1bbc709f1db0dcd559540e28bd79d3863cfcc73ea2a5d916a020108a91f53'
(OUT / 'PROTECTED_BEFORE.json').write_text(json.dumps(hashes, indent=2) + '\n')
np.save(OUT / 'STAGE1_COORDINATES.npy', coords)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'S_HUNYUAN_SHOULDER_LAYER_WORKING.blend'), compress=True)
body.name = 'S_SHOULDER_STRUCTURE_PILOT'
body['source'] = str(SOURCE.relative_to(ROOT))
body['review_status'] = 'ONE_SIDE_WORK_IN_PROGRESS'

def view(tag, stage, landmarks=False):
    direction = Vector({'SIDE': (1, 0, 0), 'FRONT': (0, -1, 0), 'FRONT34': (1, -1, 0), 'REAR34': (1, 1, 0), 'BACK': (0, 1, 0), 'LEFT_SIDE':(-1,0,0), 'LEFT_FRONT34':(-1,-1,0), 'LEFT_REAR34':(-1,1,0)}[tag]).normalized()
    for ob in bpy.context.scene.objects:
        if ob != body and ob.type != 'LIGHT': ob.hide_set(True)
    bpy.context.view_layer.objects.active = body
    body.hide_set(False)
    body.select_set(True)
    for a in bpy.context.screen.areas:
        if a.type != 'VIEW_3D': continue
        sp = a.spaces.active
        sp.region_3d.view_rotation = (-direction).to_track_quat('-Z', 'Y')
        sp.region_3d.view_location = Vector((-.035, -.345, -.055))
        sp.region_3d.view_distance = .63
        sp.region_3d.view_perspective = 'ORTHO'
        sp.overlay.show_overlays = landmarks
        sp.shading.type = 'SOLID'
        sp.shading.light = 'STUDIO'
        sp.shading.show_shadows = True
        sp.shading.show_cavity = True
        sp.shading.cavity_type = 'BOTH'
        a.tag_redraw()
    bpy.context.scene['pilot_view'] = stage + '_' + tag
    print('VIEW', stage, tag)

def capture(tag, stage):
    """Save the real live viewport after look; includes Blender UI for provenance."""
    bpy.ops.screen.screenshot(filepath=str(OUT / (stage + '_SCREEN_' + tag + '.png')))

def rollback():
    if body.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
    old = body.data
    body.data = baseline.copy()
    if old.users == 0: bpy.data.meshes.remove(old)
    print('Restored exact Stage1 mesh', len(body.data.vertices), len(body.data.polygons))

bpy.app.driver_namespace['shoulder_pilot'] = globals().copy()
view('SIDE', '00_BASELINE')
print('PILOT_READY', str(OUT))
