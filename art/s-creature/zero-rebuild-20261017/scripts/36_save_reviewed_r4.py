"""Save only the reviewed, independently reloaded E checkpoint as new R4."""
import bpy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'verification/S_ZERO_R4_TRIAL_E.blend'
OUT=ROOT/'S_ZERO_CANDIDATE_REVISED_R4.blend'
REPORT=ROOT/'evidence/R4_SAVE.json'
assert not OUT.exists() and not REPORT.exists()
review=json.loads((ROOT/'evidence/SCULPT_R4_REVIEW.json').read_text())
audit=json.loads((ROOT/'evidence/VERIFY_S_ZERO_R4_TRIAL_E_RELOAD.json').read_text())
assert review['working_checkpoint_decision']=='RETAIN_TRIAL_E_AS_R4'
assert review['overall']=='REVISE' and not review['production_keep']
assert len(audit['changed_meshes'])==6 and len(audit['unchanged_meshes'])==138
assert not any(r.get('nonadjacent_self_overlap_candidates') for r in audit['meshes'])
digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert digest==audit['file_sha256'][SOURCE.name]
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
s=bpy.context.scene
s['stage']='REVISED_R4'
s['candidate_status']='REVISE overall; retain local crown cross-section and root improvement. Not production KEEP.'
s['revision_source_sha256']=digest
s['revision_scope']='Existing six crown meshes only. Root seating, tapering oblique lens sections and local interior retopology. Other 138 meshes preserved.'
s.camera=bpy.data.objects['CAM_FRONT34']
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.overlay.show_overlays=False
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
output_hash=hashlib.sha256(OUT.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(OUT),load_ui=False)
assert Path(bpy.data.filepath)==OUT and not bpy.data.is_dirty
assert bpy.context.scene['stage']=='REVISED_R4'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==digest
REPORT.write_text(json.dumps({'source':str(SOURCE.relative_to(ROOT)),'source_sha256':digest,
    'model':OUT.name,'sha256':output_hash,'bytes':OUT.stat().st_size,
    'reopened_in_live_blender':True,'blender':bpy.app.version_string,
    'overall':'REVISE','working_checkpoint':'R4','production_keep':False},indent=2)+'\n')
print('R4_SAVED_AND_REOPENED',output_hash)
