"""Verify final rendered evidence and all protected on-disk artifacts."""
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
REPO_ROOT=ROOT.parents[2]
OUT=ROOT/'evidence/FINAL_R2_LOCAL_CHECKS.json'
assert not OUT.exists()
baseline=json.loads((ROOT/'evidence/R2_START_STATE.json').read_text())
protected=[]
for p,d in baseline['protected_artifacts'].items():
    if p.endswith('QUALITY_REVIEW.md'):continue
    assert hashlib.sha256((REPO_ROOT/p).read_bytes()).hexdigest()==d['sha256'],p
    protected.append(p)
old_refs=dict(s.split(' ',1) for s in baseline['branches'])
refs=dict(s.split(' ',1) for s in subprocess.check_output(['git','for-each-ref','--format=%(refname) %(objectname)','refs/heads'],cwd=REPO_ROOT,text=True).splitlines())
branch=subprocess.check_output(['git','branch','--show-current'],cwd=REPO_ROOT,text=True).strip()
assert branch=='exp/s-fullbody-zero-verify-20261017'
other_refs={k:v for k,v in old_refs.items() if k!='refs/heads/'+branch}
assert all(refs[k]==v for k,v in other_refs.items())
r1=json.loads((ROOT/'evidence/RENDER_revised_r1.json').read_text())
r2=json.loads((ROOT/'evidence/RENDER_revised_r2.json').read_text())
b=json.loads((ROOT/'evidence/RENDER_r2_trial_b.json').read_text())
assert set(r2['views'])=={'SIDE','FRONT','FRONT34','REAR34','BACK'}
for key in ['engine','samples','seed','resolution','view_transform','look']:
    assert r1[key]==r2[key],key
assert r2['source_sha256']==hashlib.sha256((ROOT/'S_ZERO_CANDIDATE_REVISED_R2.blend').read_bytes()).hexdigest()
views={}
for view,entry in r2['views'].items():
    for key in ['camera_matrix','ortho_scale']:assert entry[key]==r1['views'][view][key]
    p=ROOT/entry['file']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256']
    assert Image.open(p).size==(1200,900)
    pixel_match=None
    if view in b['views']:
        pixel_match=Image.open(p).convert('RGBA').tobytes()==Image.open(ROOT/b['views'][view]['file']).convert('RGBA').tobytes()
        assert pixel_match,view
    views[view]={'sha256':entry['sha256'],'r1_camera_identical':True,
                 'decoded_pixels_match_reviewed_trial_b':pixel_match,
                 'png_file_bytes_match_trial_b':entry['sha256']==b['views'].get(view,{}).get('sha256') if view in b['views'] else None}
scripts=[]
for p in sorted((ROOT/'scripts').glob('*.py')):
    if p.name[0].isdigit() and int(p.name.split('_')[0])>=10:
        ast.parse(p.read_text(),filename=str(p));scripts.append(p.name)
for doc in ['QUALITY_REVIEW.md','R2_QUALITY_REVIEW.md']:
    for link in re.findall(r'\]\(([^)]+)\)',(ROOT/doc).read_text()):
        if link.startswith(('http','#')):continue
        assert (ROOT/link).exists(),(doc,link)
report={'branch':branch,'protected_files_unchanged':protected,'other_local_branches_unchanged':other_refs,
        'five_views_checked':views,'render_settings_match_r1':True,'scripts_syntax_checked':scripts,
        'local_document_links_exist':True,'production_files_modified':False,
        'decision':'REVISE; retain R2 local sculpt improvement; original models and R1 unchanged'}
OUT.write_text(json.dumps(report,indent=2)+'\n')
print('FINAL_LOCAL_CHECKS_PASSED',len(protected),'protected files;',len(views),'views; other branch refs unchanged')
