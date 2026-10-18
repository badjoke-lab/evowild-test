"""Save the visually reviewed, reopened trial B as a new R3 checkpoint."""
import bpy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'verification/S_ZERO_R3_TRIAL_B.blend'
OUT = ROOT / 'S_ZERO_CANDIDATE_REVISED_R3.blend'
REPORT = ROOT / 'evidence/R3_SAVE.json'
assert not OUT.exists() and not REPORT.exists()
review = json.loads((ROOT / 'evidence/SCULPT_R3_REVIEW.json').read_text())
audit = json.loads((ROOT / 'evidence/VERIFY_S_ZERO_R3_TRIAL_B_RELOAD.json').read_text())
assert review['working_checkpoint_decision'] == 'RETAIN_TRIAL_B_AS_R3'
assert review['overall'] == 'REVISE' and not review['production_keep']
assert len(audit['changed_meshes']) == 44 and len(audit['unchanged_meshes']) == 100
assert not any(r.get('nonadjacent_self_overlap_candidates') for r in audit['meshes'])
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert source_hash == audit['file_sha256'][SOURCE.name]
bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False)
scene = bpy.context.scene
scene['stage'] = 'REVISED_R3'
scene['candidate_status'] = 'REVISE overall; retain reviewed local foot/ankle improvement; not production KEEP'
scene['revision_source_sha256'] = source_hash
scene['revision_scope'] = 'Eight split wedge toes, 32 existing foot surface details, four existing ankle fins. R2 body and crowns preserved.'
scene.camera = bpy.data.objects['CAM_FRONT34']
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.overlay.show_overlays = False
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True)
output_hash = hashlib.sha256(OUT.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(OUT), load_ui=False)
assert Path(bpy.data.filepath) == OUT and bpy.context.scene['stage'] == 'REVISED_R3'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
REPORT.write_text(json.dumps({'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': source_hash,
    'model': OUT.name, 'sha256': output_hash, 'bytes': OUT.stat().st_size,
    'reopened_in_live_blender': True, 'blender': bpy.app.version_string,
    'overall': 'REVISE', 'working_checkpoint': 'R3', 'production_keep': False}, indent=2) + '\n')
print('R3_SAVED_AND_REOPENED', OUT.name, output_hash)
