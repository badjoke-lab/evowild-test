"""Save the recovered static R6 under a new directory, never replace prior R6."""
import bpy, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'verification/S_ZERO_R6_RECOVERED_C.blend'
target=ROOT/'S_ZERO_CANDIDATE_REVISED_R6.blend'
report_path=ROOT/'evidence/R6_RECOVERED_SAVE.json'
assert not target.exists() and not report_path.exists()
review=json.loads((ROOT/'evidence/R6_REPAIR_AND_DEFORMATION_C.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==review['static_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)
assert not bpy.data.actions
assert not any(o.vertex_groups for o in bpy.data.objects if o.type=='MESH')
assert not any(m.type=='ARMATURE' for o in bpy.data.objects for m in o.modifiers)
sc=bpy.context.scene
sc['stage']='REVISED_R6_RECOVERED_20261020'
sc['candidate_status']='REVISE. Static welded pelvis retained; local tessellation repaired. Separate hip test improved; residual 1.435x stretch, full gait/runtime not verified.'
sc['r6_original_trial_b_sha256']=review['source_sha256']
sc['r6_validation']='verification/S_ZERO_R6_HIP_DEFORMATION_RECOVERED_C.blend; validation armature only.'
sc['r6_review']='R5-to-B static continuity improvement retained. C preserves every B source coordinate and protected surface. Further faceting/palette refinement remains.'
sc.camera=bpy.data.objects['CAM_FRONT34'];sc.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
sha=hashlib.sha256(target.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(target),load_ui=False)
assert not any(o.type=='ARMATURE' for o in bpy.data.objects) and not bpy.data.actions
report={'source':str(source.relative_to(ROOT)),'source_sha256':review['static_sha256'],
 'output':target.name,'output_sha256':sha,'bytes':target.stat().st_size,'blender':bpy.app.version_string,
 'armatures':0,'actions':0,'vertex_groups':0,'live_reloaded':True,
 'static_decision':'REVISE; improved R5 pelvis continuity retained, B rest silhouette unchanged, tessellation repaired',
 'deformation_decision':'REVISE; major observed defects reduced; residual stretch/compression and untested gait/runtime',
 'production_keep':False,'original_root_R6_preserved':True}
report_path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
