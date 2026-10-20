"""Check protected bytes, saved-file render provenance, and construct commit manifest."""
import hashlib,json,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[3]
OUT=ROOT/'evidence/FINAL_LOCAL_CHECKS.json'
MANIFEST=ROOT/'evidence/R6_DELIVERY_MANIFEST.json'
assert not OUT.exists() and not MANIFEST.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected=json.loads((ROOT/'evidence/RECOVERY_PROTECTED_FILES.json').read_text())
for name,entry in protected['protected_files'].items():
    p=REPO/name
    assert p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256'],name
formal=ROOT/'S_ZERO_CANDIDATE_REVISED_R6.blend'
saved=json.loads((ROOT/'evidence/R6_RECOVERED_SAVE.json').read_text())
assert sha(formal)==saved['output_sha256']
images=[];render_reports=[]
for label,count in [('revised_r6',5),('hip_recovered_c',12)]:
    report=json.loads((ROOT/'evidence'/('RENDER_'+label+'.json')).read_text())
    assert len(report['renders'])==count
    assert sha(ROOT/report['source'])==report['source_sha256']
    for item in report['renders']:
        p=ROOT/item['file'];assert sha(p)==item['sha256']
        with Image.open(p) as im:im.verify()
        images.append(item['file'])
    render_reports.append(report)
old_static=json.loads((ROOT.parent/'evidence/RENDER_revised_r5.json').read_text())
for item in render_reports[0]['renders']:
    prior=old_static['views'][item['view']]
    assert item['camera_matrix']==prior['camera_matrix']
    assert item['ortho_scale']==prior['ortho_scale']
old_hip=json.loads((ROOT.parent/'evidence/RENDER_R6_HIP_TEST_B.json').read_text())
for item in render_reports[1]['renders']:
    prior=old_hip['poses'][item['state']]['views'][item['view']]
    assert item['camera_matrix']==prior['camera_matrix']
    assert item['ortho_scale']==prior['ortho_scale']
for p in (ROOT/'comparisons').glob('*.png'):
    with Image.open(p) as im:im.verify()
audit=json.loads((ROOT/'evidence/INDEPENDENT_SAVED_DEFORMATION.json').read_text())
assert audit['rest_coordinates_exact']
for state in audit['records']['after']['states'].values():
    assert state['whole_body']['edge_max']<1.44
    assert state['whole_body']['triangles_below_0_35']==0
    assert state['whole_body']['rest_normal_dot_negative']==0
report={'protected_existing_files':len(protected['protected_files']),'all_protected_bytes_unchanged':True,
    'source_and_formal_hashes_verified':True,'new_saved_file_renders_verified':len(images),
    'R5_static_and_B_hip_cameras_exact':True,'all_png_decode_checks_passed':True,
    'formal_no_rig_evidence':'R6_RECOVERED_SAVE.json; ../evidence/VERIFY_R6_RECOVERED_C_RELOAD.json',
    'deformation':'Independent saved-file audit and whole-body scan agree; residual 1.435x stretch and .537 area ratio, REVISE',
    'production_keep':False}
OUT.write_text(json.dumps(report,indent=2)+'\n')
# Stage only this recovery plus prior uncommitted R6 outputs. Unrelated R3/R5
# leftovers remain untouched and excluded.
untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=REPO).decode().split('\0')
paths=[]
for rel in untracked:
    if not rel:continue
    p=REPO/rel
    if ROOT in p.parents:
        paths.append(rel)
    elif ROOT.parent in p.parents and ('r6' in p.name.lower() or any(part.lower().startswith('r6_') for part in p.parts)):
        paths.append(rel)
    elif rel.endswith('/R6_RECOVERY_INDEX.md'):
        paths.append(rel)
assert str(formal.relative_to(REPO)) in paths
assert str((ROOT.parent/'verification/S_ZERO_R6_TRIAL_B.blend').relative_to(REPO)) in paths
entries={rel:{'bytes':(REPO/rel).stat().st_size,'sha256':sha(REPO/rel)} for rel in sorted(paths)}
manifest={'base_head':protected['head'],'branch':'exp/s-fullbody-zero-verify-20261017',
    'transport':'ssh://git@ssh.github.com:443/badjoke-lab/evowild-test.git',
    'files':entries,'manifest_self_excluded':True,'production_keep':False}
MANIFEST.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(report));print('Manifest files',len(entries),'bytes',sum(e['bytes'] for e in entries.values()))
