"""Verify committed R5 artifacts through GitHub and freshly download deliverables.

Run after a normal push. Uses gh's existing authentication; never reads/prints keys.
Exact branch head and Git blob IDs are checked. Downloads go to a fresh temp dir.
"""
import base64
import concurrent.futures
import hashlib
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
PREFIX = ROOT.relative_to(REPO_ROOT).as_posix()
REPO = 'badjoke-lab/evowild-test'
BRANCH = subprocess.check_output(['git', 'branch', '--show-current'], cwd=REPO_ROOT, text=True).strip()
COMMIT = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO_ROOT, text=True).strip()
OUT = ROOT / 'evidence/REMOTE_R5_FINAL_VERIFY.json'
assert not OUT.exists()


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', 'repos/' + REPO + '/' + path], timeout=120))


head = api('git/ref/heads/' + BRANCH)['object']['sha']
assert head == COMMIT, (head, COMMIT)
tree = api('git/trees/' + COMMIT + '?recursive=1')
assert not tree.get('truncated')
checks = []
blobs = {}
for entry in tree['tree']:
    if entry['type'] != 'blob' or not entry['path'].startswith(PREFIX + '/'):
        continue
    path = REPO_ROOT / entry['path']
    data = path.read_bytes()
    oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert oid == entry['sha'], entry['path']
    blobs[entry['path']] = oid
    checks.append({'path': entry['path'], 'bytes': len(data), 'git_blob_sha': oid, 'matches_local': True})

relative_paths = ['S_ZERO_CANDIDATE_REVISED_R5.blend', 'R5_QUALITY_REVIEW.md',
                  'evidence/VERIFY_S_ZERO_CANDIDATE_REVISED_R5_RELOAD.json',
                  'evidence/SCULPT_R5_REVIEW.json', 'evidence/R5_SAVE.json',
                  'evidence/R5_FINAL_LOCAL_CHECKS.json', 'evidence/R5_ARTIFACT_MANIFEST.json']
relative_paths += ['renders/revised_r5/' + v + '.png' for v in ['SIDE','FRONT','FRONT34','REAR34','BACK']]
relative_paths += ['renders/revised_r5_viewport/' + v + '.png' for v in ['SIDE','FRONT34','REAR34','BACK']]
relative_paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'comparisons').glob('REVISED_R5_*.png'))]
relative_paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'scripts').glob('*.py')) if p.name[:2].isdigit() and int(p.name[:2])>=41]
download_dir = Path(tempfile.mkdtemp(prefix='evowild-r5-github-'))


def download(relative):
    path = PREFIX + '/' + relative
    blob = api('git/blobs/' + blobs[path])
    assert blob['encoding'] == 'base64' and blob['sha'] == blobs[path]
    data = base64.b64decode(blob['content'])
    local = (REPO_ROOT / path).read_bytes()
    assert data == local, path
    destination = download_dir / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    print('REMOTE_BYTES_VERIFIED', relative, flush=True)
    return {'path': path, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'download_matches_local': True, 'method': 'GitHub Git blob API; downloaded and saved',
            'url': f'https://github.com/{REPO}/blob/{COMMIT}/{path}'}


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    downloads = list(pool.map(download, relative_paths))
report = {'utc': datetime.now(timezone.utc).isoformat(), 'repository': REPO, 'branch': BRANCH,
          'commit': COMMIT, 'branch_head_matches': True, 'tree_checks': checks,
          'download_checks': downloads, 'download_directory': str(download_dir),
          'pending_artifacts': [], 'force_push_used': False}
OUT.write_text(json.dumps(report, indent=2) + '\n')
print('REMOTE_R5_VERIFIED', COMMIT, len(checks), 'tree files;', len(downloads), 'fresh downloads', flush=True)
