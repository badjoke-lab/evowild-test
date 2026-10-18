"""Publish the existing R4 Git commit in small GitHub Git-data API requests.

Use the small-object fallback after the documented R3 HTTP 408 on this branch. Immutable blobs and trees are
uploaded separately. Only an exact matching local commit may advance the named
preservation branch, with force=false and a checked previous head. If GitHub
normalizes commit metadata, stop before changing any ref so both histories can
be preserved on a new integration branch. Uses gh authentication without keys.
"""
import base64
import hashlib
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
REPO = 'badjoke-lab/evowild-test'
BRANCH = 'exp/s-fullbody-zero-verify-20261017'
REPORT = ROOT / 'evidence/R4_GIT_OBJECT_UPLOAD.json'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO_ROOT)


def api(endpoint, payload=None, method=None):
    cmd = ['gh', 'api', 'repos/' + REPO + '/' + endpoint]
    if payload is not None:
        cmd += ['--method', method or 'POST', '--input', '-']
    result = subprocess.run(cmd, input=json.dumps(payload).encode() if payload is not None else None,
                            capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr.decode()[:500])
    return json.loads(result.stdout)


assert git('branch', '--show-current').decode().strip() == BRANCH
commit = git('rev-parse', 'HEAD').decode().strip()
raw_commit = git('cat-file', '-p', commit).decode()
headers, message = raw_commit.split('\n\n', 1)
fields = {}
for line in headers.splitlines():
    key, value = line.split(' ', 1)
    fields.setdefault(key, []).append(value)
assert set(fields) == {'tree', 'parent', 'author', 'committer'}, fields.keys()
assert len(fields['parent']) == 1
parent = fields['parent'][0]
head = api('git/ref/heads/' + BRANCH)['object']['sha']
assert head == parent, (head, parent)
assert not git('diff', '--name-only').decode().strip(), 'Tracked worktree changes are not part of this commit'
initial = api('git/trees/' + parent + '?recursive=1')
assert not initial.get('truncated')
known = {e['sha'] for e in initial['tree'] if e['type'] == 'blob'}
changes = git('diff', '--name-only', parent, commit).decode().splitlines()
assert changes and all(p.startswith('art/s-creature/zero-rebuild-20261017/') for p in changes)
assert not git('diff', '--name-only', '--diff-filter=D', parent, commit).decode().strip()
report = json.loads(REPORT.read_text()) if REPORT.exists() else {
    'repository': REPO, 'branch': BRANCH, 'local_commit': commit, 'parent': parent,
    'reason': 'Previous R3 normal push returned HTTP 408 on this branch. Reusing the user-authorized small Git-data API uploads for R4; no failed R4 push is claimed.',
    'uploaded_blobs': {}, 'reused_blobs': {}, 'branch_updated': False, 'force': False}
assert report['local_commit'] == commit and report['parent'] == parent


def persist():
    REPORT.write_text(json.dumps(report, indent=2) + '\n')


try:
    entries = []
    for path in changes:
        data = git('show', commit + ':' + path)
        oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        assert data == (REPO_ROOT / path).read_bytes(), path
        if oid in known or oid in report['uploaded_blobs']:
            report['reused_blobs'][path] = oid
        else:
            result = api('git/blobs', {'encoding': 'base64', 'content': base64.b64encode(data).decode()})
            assert result['sha'] == oid, path
            report['uploaded_blobs'][oid] = {'path': path, 'bytes': len(data),
                                             'sha256': hashlib.sha256(data).hexdigest()}
            print('BLOB_PRESERVED', path, len(data), flush=True)
        entries.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': oid})
        persist()
    base_tree = api('git/commits/' + parent)['tree']['sha']
    tree = api('git/trees', {'base_tree': base_tree, 'tree': entries})
    assert tree['sha'] == fields['tree'][0], (tree['sha'], fields['tree'][0])
    report['tree_sha'] = tree['sha']
    persist()

    def identity(line):
        match = re.fullmatch(r'(.*) <([^<>]+)> (\d+) ([+-]\d{4})', line)
        assert match, line
        name, email, epoch, offset = match.groups()
        minutes = (int(offset[1:3]) * 60 + int(offset[3:5])) * (-1 if offset[0] == '-' else 1)
        date = datetime.fromtimestamp(int(epoch), timezone(timedelta(minutes=minutes))).isoformat()
        return {'name': name, 'email': email, 'date': date}

    created = api('git/commits', {'tree': tree['sha'], 'parents': [parent], 'message': message,
                               'author': identity(fields['author'][0]),
                               'committer': identity(fields['committer'][0])})
    report['api_commit'] = created['sha']
    report['commit_matches_local'] = created['sha'] == commit
    persist()
    assert created['sha'] == commit, 'API normalized commit metadata; no ref changed. Preserve both commits on a new integration branch.'
    assert api('git/ref/heads/' + BRANCH)['object']['sha'] == parent
    updated = api('git/refs/heads/' + BRANCH, {'sha': commit, 'force': False}, method='PATCH')
    assert updated['object']['sha'] == commit
    report['branch_updated'] = True
    report.pop('error', None)
    persist()
    print('EXACT_LOCAL_COMMIT_PUBLISHED', commit, flush=True)
except Exception as exc:
    report['error'] = str(exc)
    persist()
    raise
