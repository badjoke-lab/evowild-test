"""Re-fetch actual delivery files from GitHub using a fresh SSH-443 object store.

Usage: python3 64_verify_remote_ssh.py COMMIT_SHA OUTPUT_JSON
No objects or alternates from the worktree are reused.
"""
import hashlib,json,subprocess,sys,tempfile,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[3]
commit=sys.argv[1];out=Path(sys.argv[2])
assert len(commit)==40 and not out.exists()
manifest=ROOT/'evidence/R6_DELIVERY_MANIFEST.json'
delivery=json.loads(manifest.read_text())
entries=delivery['files'].copy()
entries[str(manifest.relative_to(REPO))]={'bytes':manifest.stat().st_size,'sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()}
clone=Path(tempfile.mkdtemp(prefix='evowild-r6-github-ssh443-'))
def git(*args,input=None):
    return subprocess.check_output(['git','-C',str(clone),*args],input=input,stderr=subprocess.STDOUT)
git('init','--quiet')
git('config','core.sshCommand','ssh -o BatchMode=yes -o ConnectTimeout=30')
git('remote','add','origin',delivery['transport'])
git('config','remote.origin.promisor','true')
git('config','remote.origin.partialclonefilter','blob:none')
git('config','core.sparseCheckout','true')
git('config','core.sparseCheckoutCone','false')
patterns=''.join('/'+rel+'\n' for rel in entries)
(clone/'.git/info/sparse-checkout').write_text(patterns)
print('Fresh independent fetch:',clone,flush=True)
print(git('fetch','--depth=1','--filter=blob:none','origin',delivery['branch']).decode(),flush=True)
fetched=git('rev-parse','FETCH_HEAD').decode().strip()
assert fetched==commit,(fetched,commit)
print(git('checkout','--detach','FETCH_HEAD').decode(),flush=True)
verified={}
for rel,expected in entries.items():
    downloaded=clone/rel;local=REPO/rel
    payload=downloaded.read_bytes();digest=hashlib.sha256(payload).hexdigest()
    assert digest==expected['sha256'] and len(payload)==expected['bytes'],rel
    assert payload==local.read_bytes(),rel
    verified[rel]={'bytes':len(payload),'sha256':digest,'byte_equal':True}
remote=git('ls-remote','origin','refs/heads/'+delivery['branch']).decode().split()[0]
assert remote==commit
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commit':commit,'remote_head':remote,
    'transport':delivery['transport'],'fresh_object_database':str(clone),
    'reused_local_objects':False,'verified_file_count':len(verified),
    'verified_bytes':sum(v['bytes'] for v in verified.values()),'all_byte_equal':True,'files':verified}
out.write_text(json.dumps(report,indent=2)+'\n')
print('REMOTE_R6_ALL_BYTES_VERIFIED',len(verified),report['verified_bytes'],commit,flush=True)
