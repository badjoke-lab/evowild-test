"""Save reviewed static trial B as R6; never copy the test armature to R6."""
import bpy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'verification/S_ZERO_R6_TRIAL_B.blend'
OUT=ROOT/'S_ZERO_CANDIDATE_REVISED_R6.blend'
assert not OUT.exists()
review=json.loads((ROOT/'evidence/SCULPT_R6_REVIEW.json').read_text())
assert review['selected_trial']=='B' and review['overall']=='REVISE'
assert review['static_local_shape_improvement'] is True
verification=json.loads((ROOT/'evidence/VERIFY_R6_TRIAL_B.json').read_text())
expected=verification['hashes'][SOURCE.name]
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==expected
test=json.loads((ROOT/'evidence/R6_HIP_DEFORMATION_TEST_B.json').read_text())
assert test['source_sha256']==expected
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
assert not any(o.type=='ARMATURE' for o in bpy.data.objects) and not bpy.data.actions
assert not any(m.type=='ARMATURE' for o in bpy.data.objects for m in o.modifiers)
sc=bpy.context.scene;sc['stage']='REVISED_R6'
sc['candidate_status']='REVISE: local pelvis continuity improved; deformation quality fails; not production KEEP'
sc['r6_source_sha256']=expected
sc['r6_validation']='Separate verification/S_ZERO_R6_HIP_DEFORMATION_TEST_B.blend only; +25/-20 degree tests performed. No production rig.'
sc.camera=bpy.data.objects['CAM_FRONT34'];sc.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
sha=hashlib.sha256(OUT.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(OUT),load_ui=False)
assert not any(o.type=='ARMATURE' for o in bpy.data.objects) and not bpy.data.actions
report={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':expected,'output':OUT.name,
    'output_sha256':sha,'bytes':OUT.stat().st_size,'live_reloaded':True,'blender':bpy.app.version_string,
    'armatures':0,'actions':0,'overall':'REVISE','production_keep':False}
p=ROOT/'evidence/R6_SAVE.json';assert not p.exists();p.write_text(json.dumps(report,indent=2)+'\n')
print('Reviewed R6 saved and reloaded',report)
