"""Save the visually reviewed trial B as a separate REVISE working R2."""
import bpy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'S_ZERO_CANDIDATE_REVISED_R2.blend'
assert Path(bpy.data.filepath).name=='S_ZERO_R2_TRIAL_B.blend'
assert not OUT.exists()
review=json.loads((ROOT/'evidence/SCULPT_R2_REVIEW.json').read_text())
assert review['retain_local_improvement'] is True
assert review['overall_decision']=='REVISE'
assert set(review['inspected_trial_b_views'])=={'SIDE','FRONT','FRONT34'}
scene=bpy.context.scene
scene['stage']='CANDIDATE_REVISED_R2'
scene['candidate_status']='REVISE overall; shoulder integration and frontal crown improvement retained. NOT production KEEP.'
scene['r2_source']='S_ZERO_CANDIDATE_REVISED_R1.blend'
scene['r2_source_sha256']='f8e8a80360ee5886d485a17610cf62a9387d10cdb09e4801a055be99bf8d8a4f'
scene['r2_scope']='Existing shoulder/scapula/upper arm union with chest, local seam fairing and palette interpolation; lateral crown sections only'
scene['r2_remaining']='Shoulder plane refinement, hip intersections, wedge toes, organic tail layers, joint retopology and rigging; gait/runtime untested'
scene.camera=bpy.data.objects['CAM_FRONT34']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
(ROOT/'evidence/R2_SAVE.json').write_text(json.dumps({
    'source_trial':'verification/S_ZERO_R2_TRIAL_B.blend','output':OUT.name,
    'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'bytes':OUT.stat().st_size,
    'decision':'REVISE','local_improvement_retained':True,'production_promoted':False},indent=2)+'\n')
print('R2_SAVED',OUT.name,OUT.stat().st_size)
