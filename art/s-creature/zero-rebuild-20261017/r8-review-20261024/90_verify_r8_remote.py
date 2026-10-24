"""Fresh SSH-443 Git database; verify every saved R8 artifact at the named HEAD.

Usage: python3 90_verify_r8_remote.py COMMIT OUTPUT_JSON
No local objects, alternates, or worktree files are used to supply remote bytes.
"""
import datetime,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
REPO=Path(__file__).resolve().parents[4]
ROOT='art/s-creature/zero-rebuild-20261017/'
BRANCH='exp/s-fullbody-zero-verify-20261017'
URL='ssh://git@ssh.github.com:443/badjoke-lab/evowild-test.git'
commit=sys.argv[1];out=Path(sys.argv[2]);assert len(commit)==40 and not out.exists()
env=os.environ.copy()
for key in ['GIT_DIR','GIT_WORK_TREE','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES']:env.pop(key,None)
def git(where,*args):
    return subprocess.check_output(['git','-C',str(where),*args],env=env,stderr=subprocess.STDOUT)
assert git(REPO,'rev-parse','HEAD').decode().strip()==commit
assert git(REPO,'branch','--show-current').decode().strip()==BRANCH
paths=git(REPO,'ls-tree','-r','--name-only',commit,'--',ROOT+'r8-form-20261023').decode().splitlines()
artifact_count=len(paths)
paths+=['art/s-creature/references/00_s_type_modeling_image_v1.png',
 ROOT+'r7-hip-20261022/S_ZERO_CANDIDATE_REVISED_R7.blend',
 ROOT+'r7-hip-20261022/verification/S_ZERO_R7_HIP_DEFORMATION_VERIFIED_B.blend']
expected={}
for rel in paths:
    payload=(REPO/rel).read_bytes()
    oid=git(REPO,'rev-parse',commit+':'+rel).decode().strip()
    assert hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()==oid,rel
    expected[rel]={'git_blob':oid,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()}
clone=Path(tempfile.mkdtemp(prefix='evowild-r8-independent-ssh443-'))
git(clone,'init','--quiet');git(clone,'config','core.sshCommand','ssh -o BatchMode=yes -o ConnectTimeout=30')
git(clone,'remote','add','origin',URL);git(clone,'config','remote.origin.promisor','true')
git(clone,'config','remote.origin.partialclonefilter','blob:none');git(clone,'config','core.sparseCheckout','true')
git(clone,'config','core.sparseCheckoutCone','false')
(clone/'.git/info/sparse-checkout').write_text(''.join('/'+p+'\n' for p in paths))
print('INDEPENDENT_FETCH',clone,artifact_count,'R8 files',flush=True)
print(git(clone,'fetch','--depth=1','--filter=blob:none','origin',BRANCH).decode(),flush=True)
assert git(clone,'rev-parse','FETCH_HEAD').decode().strip()==commit
print(git(clone,'checkout','--detach','FETCH_HEAD').decode(),flush=True)
assert not (clone/'.git/objects/info/alternates').exists()
verified={}
for rel,item in expected.items():
    payload=(clone/rel).read_bytes()
    assert len(payload)==item['bytes'] and hashlib.sha256(payload).hexdigest()==item['sha256'],rel
    assert payload==(REPO/rel).read_bytes(),rel
    verified[rel]={**item,'byte_equal':True}
remote=git(clone,'ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0];assert remote==commit
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commit':commit,'local_head':commit,'remote_head':remote,
 'branch':BRANCH,'transport':URL,'fresh_object_database':str(clone),'reused_local_objects':False,'alternates_absent':True,
 'r8_saved_artifact_count':artifact_count,'additional_reference_and_R7_files':3,'verified_file_count':len(verified),
 'verified_bytes':sum(v['bytes'] for v in verified.values()),'all_byte_equal':True,'files':verified}
out.write_text(json.dumps(report,indent=2)+'\n')
print('R8_REMOTE_BYTES_VERIFIED',len(verified),report['verified_bytes'],commit,flush=True)
