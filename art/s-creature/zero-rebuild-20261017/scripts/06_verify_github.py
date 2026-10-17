"""Verify GitHub tree entries and download artifact bytes through authenticated gh.
Usage: python3 THIS COMMIT REPORT_NAME [--final]
Does not modify remote branches or any artifact. Never prints credentials.
"""
import concurrent.futures
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
PREFIX = ROOT.relative_to(REPO_ROOT).as_posix()
REPO = 'badjoke-lab/evowild-test'
BRANCH = 'exp/s-fullbody-zero-verify-20261017'
commit, report_name = sys.argv[1:3]
final = '--final' in sys.argv


def gh(path, raw=False):
    args = ['gh', 'api', path]
    if raw:
        args += ['-H', 'Accept: application/vnd.github.raw']
    return subprocess.check_output(args, timeout=120)


head = json.loads(gh(f'repos/{REPO}/git/ref/heads/{BRANCH}'))['object']['sha']
assert head == commit, (head, commit)
tree = json.loads(gh(f'repos/{REPO}/git/trees/{commit}?recursive=1'))
assert not tree.get('truncated')
entries = [x for x in tree['tree'] if x['type'] == 'blob' and
           (x['path'].startswith(PREFIX + '/') or x['path'] == 'art/s-creature/references/00_s_type_modeling_image_v1.png')]
tree_checks = []
for entry in entries:
    local = REPO_ROOT / entry['path']
    data = local.read_bytes()
    oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert oid == entry['sha'], entry['path']
    tree_checks.append({'path': entry['path'], 'bytes': len(data), 'git_blob_sha': oid,
                        'github_tree_match': True})
paths = [f'{PREFIX}/S_ZERO_{stage}.blend' for stage in ['BLOCKOUT', 'REFINED', 'CANDIDATE']]
if final:
    paths += [e['path'] for e in entries if '/renders/candidate_review/' in e['path'] or
              '/renders/revised_r1/' in e['path'] or '/comparisons/' in e['path'] or
              e['path'].endswith('S_ZERO_CANDIDATE_REVISED_R1.blend')]


def verify(path):
    body = gh(f'repos/{REPO}/contents/{quote(path, safe="/")}?ref={commit}', raw=True)
    local = (REPO_ROOT / path).read_bytes()
    assert body == local, path
    record = {'path': path, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(),
              'downloaded_from_github': True, 'matches_local_bytes': True,
              'url': f'https://github.com/{REPO}/blob/{commit}/{path}'}
    print('REMOTE_BYTES_VERIFIED', path, len(body), flush=True)
    return record


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    downloads = list(pool.map(verify, paths))
report = {'utc': datetime.now(timezone.utc).isoformat(), 'repository': REPO, 'branch': BRANCH,
          'commit': commit, 'github_branch_head_matches': True, 'tree_checks': tree_checks,
          'downloads': downloads}
out = ROOT / 'evidence' / report_name
assert not out.exists()
out.write_text(json.dumps(report, indent=2) + '\n')
print('REMOTE_VERIFICATION_COMPLETE', commit, len(tree_checks), 'tree entries;', len(downloads), 'downloads')
