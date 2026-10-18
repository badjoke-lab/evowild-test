"""Check final render provenance, preserved artifacts and saved/reloaded pixels."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/R4_FINAL_LOCAL_CHECKS.json'
assert not OUT.exists()
model=ROOT/'S_ZERO_CANDIDATE_REVISED_R4.blend'
digest=hashlib.sha256(model.read_bytes()).hexdigest()
old=json.loads((ROOT/'evidence/RENDER_revised_r3.json').read_text())
new=json.loads((ROOT/'evidence/RENDER_revised_r4.json').read_text())
audit=json.loads((ROOT/'evidence/VERIFY_S_ZERO_CANDIDATE_REVISED_R4_RELOAD.json').read_text())
assert new['source_sha256']==digest==audit['file_sha256'][model.name]
assert len(audit['changed_meshes'])==6 and len(audit['unchanged_meshes'])==138
assert not any(r.get('nonadjacent_self_overlap_candidates') for r in audit['meshes'])
for k in ['engine','samples','seed','resolution','view_transform','look']:
    assert old[k]==new[k],k
views={}
for v in ['SIDE','FRONT','FRONT34','REAR34','BACK']:
    for k in ['camera_matrix','ortho_scale']:
        assert old['views'][v][k]==new['views'][v][k],(v,k)
    p=ROOT/new['views'][v]['file']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==new['views'][v]['sha256']
    row={'r3_camera_and_studio_match':True,'sha256':new['views'][v]['sha256']}
    if v in ['SIDE','FRONT','FRONT34']:
        a=Image.open(ROOT/'renders/r4_trial_e'/(v+'.png')).convert('RGB')
        b=Image.open(p).convert('RGB')
        assert ImageChops.difference(a,b).getbbox() is None,v
        row['rgb_equal_to_reviewed_E']=True
    views[v]=row
viewport=json.loads((ROOT/'evidence/MCP_R4_VIEWPORT_CAPTURE.json').read_text())
assert viewport['source_sha256']==digest
for v,r in viewport['views'].items():
    p=Path(r['filepath'])
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
    extrema=Image.open(p).convert('RGB').getextrema()
    assert max(hi-lo for lo,hi in extrema)>30,(v,extrema)
protected=json.loads((ROOT/'evidence/R4_RECOVERY_START.json').read_text())['protected_artifacts']
for name,entry in protected.items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==entry['sha256'],name
report={'model_sha256':digest,'model_bytes':model.stat().st_size,'views':views,
    'viewport_images':list(viewport['views']),'protected_artifacts_unchanged':len(protected),
    'changed_meshes':audit['changed_meshes'],'unchanged_meshes':len(audit['unchanged_meshes']),
    'side_outline_checks':audit['side_outline_checks'],'no_nonadjacent_self_overlap_candidates_in_crowns':True,
    'overall':'REVISE','production_keep':False,'rig_gait_pc_mobile_validation':False,
    'limits':'Image similarity review and mesh integrity are distinct from rigging and runtime acceptance.'}
OUT.write_text(json.dumps(report,indent=2)+'\n')
print('R4_LOCAL_CHECKS_PASS',digest,len(protected),'protected artifacts')
