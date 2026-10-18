"""Read-only final GitHub tree and download verification at the exact branch head."""
import concurrent.futures
import base64
import hashlib
import json
import subprocess
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
REPO_ROOT=ROOT.parents[2]
REPO='badjoke-lab/evowild-test'
BRANCH='exp/s-fullbody-zero-verify-20261017'
PREFIX=ROOT.relative_to(REPO_ROOT).as_posix()
OUT=ROOT/'evidence/REMOTE_R2_FINAL_VERIFY.json'
assert not OUT.exists()


def api(path,raw=False):
    cmd=['gh','api',f'repos/{REPO}/'+path]
    if raw:cmd+=['-H','Accept: application/vnd.github.raw']
    data=subprocess.check_output(cmd,timeout=90)
    return data if raw else json.loads(data)


commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO_ROOT,text=True).strip()
head=api('git/ref/heads/'+BRANCH)['object']['sha']
assert head==commit,(head,commit)
tree=api('git/trees/'+commit+'?recursive=1')
assert not tree.get('truncated')
checks=[]
blob_ids={}
for e in tree['tree']:
    if e['type']!='blob' or not e['path'].startswith(PREFIX+'/'):continue
    path=REPO_ROOT/e['path']
    data=path.read_bytes()
    oid=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert oid==e['sha'],e['path']
    blob_ids[e['path']]=oid
    checks.append({'path':e['path'],'bytes':len(data),'git_blob_sha':oid,'matches_local':True})
previous_downloads=0
for report_name in ['REMOTE_missing_images.json','REMOTE_r2_assets.json']:
    report=json.loads((ROOT/'evidence'/report_name).read_text())
    assert not report['pending'],report_name
    previous_downloads+=len(report['verified'])
    for e in report['verified']:
        assert any(t['path']==e['path'] and t['git_blob_sha']==e['git_blob_sha'] for t in checks),e['path']
paths=[f'{PREFIX}/S_ZERO_{stage}.blend' for stage in ['BLOCKOUT','REFINED','CANDIDATE','CANDIDATE_REVISED_R1','CANDIDATE_REVISED_R2']]
paths += [f'{PREFIX}/R2_QUALITY_REVIEW.md',f'{PREFIX}/scripts/11_sculpt_r2.py',f'{PREFIX}/scripts/13_refine_r2_interface.py']


def download(path):
    blob=api('git/blobs/'+blob_ids[path])
    assert blob['encoding']=='base64' and blob['sha']==blob_ids[path]
    data=base64.b64decode(blob['content'])
    assert data==(REPO_ROOT/path).read_bytes(),path
    print('FINAL_REMOTE_BYTES_VERIFIED',path,flush=True)
    return {'path':path,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'download_matches_local':True,'download_method':'Git blob API',
            'url':f'https://github.com/{REPO}/blob/{commit}/{path}'}


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    downloaded=list(pool.map(download,paths))
report={'utc':datetime.now(timezone.utc).isoformat(),'repository':REPO,'branch':BRANCH,'commit':commit,
        'branch_head_matches':True,'tree_checks':checks,'download_checks':downloaded,
        'previous_individual_downloads_at_same_final_blob_ids':previous_downloads,
        'pending_artifacts':[],'force_push_used':False}
OUT.write_text(json.dumps(report,indent=2)+'\n')
print('FINAL_REMOTE_VERIFIED',commit,len(checks),'files;',len(downloaded),'fresh downloads',flush=True)
