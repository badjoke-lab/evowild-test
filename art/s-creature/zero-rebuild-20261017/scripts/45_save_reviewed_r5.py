"""Save the visually reviewed C checkpoint as new R5, then reopen in live MCP."""
import bpy, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'verification/S_ZERO_R5_TRIAL_C.blend'
OUT=ROOT/'S_ZERO_CANDIDATE_REVISED_R5.blend'
REPORT=ROOT/'evidence/R5_SAVE.json'
assert not OUT.exists() and not REPORT.exists()
review=json.loads((ROOT/'evidence/SCULPT_R5_REVIEW.json').read_text())
audit=json.loads((ROOT/'evidence/VERIFY_S_ZERO_R5_TRIAL_C_RELOAD.json').read_text())
assert review['working_checkpoint_decision']=='RETAIN_TRIAL_C_AS_R5'
assert review['overall']=='REVISE' and not review['production_keep']
assert len(audit['changed_meshes'])==40 and len(audit['unchanged_meshes'])==104
assert not any(r.get('nonadjacent_self_overlap_candidates') for r in audit['meshes'])
assert all(r['root_center_inside_by_nearest_normal'] for r in audit['tail_root_embedding'].values())
digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert digest==audit['file_sha256'][SOURCE.name]
assert not bpy.data.is_dirty
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
s=bpy.context.scene
s['stage']='REVISED_R5'
s['candidate_status']='REVISE overall; tail sculpt checkpoint only. Not production KEEP.'
s['revision_source_sha256']=digest
s['revision_scope']='39 existing tail meshes and 1920 tail-only vertices of continuous body. Other 104 meshes preserved.'
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
assert bpy.context.scene['stage']=='REVISED_R5'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==digest
REPORT.write_text(json.dumps({'source':str(SOURCE.relative_to(ROOT)),'source_sha256':digest,
    'model':OUT.name,'sha256':output_hash,'bytes':OUT.stat().st_size,
    'reopened_in_live_blender':True,'blender':bpy.app.version_string,
    'overall':'REVISE','working_checkpoint':'R5','production_keep':False},indent=2)+'\n')
print('R5_SAVED_AND_REOPENED',output_hash)
