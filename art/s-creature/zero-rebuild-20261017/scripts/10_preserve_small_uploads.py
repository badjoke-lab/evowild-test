"""Upload missing artifacts individually; verify downloaded bytes after every file.

Uses gh's credential store, never exposes credentials, never rewrites refs or files.
Only the named preservation branch is writable. Resume skips byte-identical files.
Usage: python3 THIS missing-images|r2-assets
"""
import base64
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
REPO = 'badjoke-lab/evowild-test'
BRANCH = 'exp/s-fullbody-zero-verify-20261017'
MODE = sys.argv[1]
assert MODE in ['missing-images', 'r2-assets']
REPORT = ROOT / 'evidence' / ('REMOTE_' + MODE.replace('-', '_') + '.json')
report = json.loads(REPORT.read_text()) if REPORT.exists() else {
    'repository': REPO, 'branch': BRANCH, 'mode': MODE, 'verified': [], 'pending': []}
if MODE == 'missing-images':
    paths = json.loads((ROOT / 'evidence/R2_START_STATE.json').read_text())['missing_remote_images']
else:
    paths = json.loads((ROOT / 'evidence/R2_UPLOAD_MANIFEST.json').read_text())['paths']
assert all(p.startswith('art/s-creature/zero-rebuild-20261017/') for p in paths)
started = time.monotonic()


def api(endpoint, payload=None, raw=False):
    cmd = ['gh', 'api', f'repos/{REPO}/' + endpoint]
    if payload is not None:
        cmd += ['--method', 'PUT', '--input', '-']
    if raw:
        cmd += ['-H', 'Accept: application/vnd.github.raw']
    p = subprocess.run(cmd, input=json.dumps(payload).encode() if payload else None,
                       capture_output=True, timeout=75)
    if p.returncode:
        raise RuntimeError(p.stderr.decode()[:500])
    return p.stdout if raw else json.loads(p.stdout)


head = api('git/ref/heads/' + BRANCH)['object']['sha']
initial_tree = api('git/trees/' + head + '?recursive=1')
assert not initial_tree.get('truncated')
initial_entries = {e['path']:e['sha'] for e in initial_tree['tree'] if e['type']=='blob'}
verified = {e['path']:e for e in report['verified']}
report['pending'] = [p for p in paths if not (
    p in verified and initial_entries.get(p)==verified[p]['git_blob_sha'] and
    hashlib.sha256((REPO_ROOT/p).read_bytes()).hexdigest()==verified[p]['sha256'])]
report.pop('stop_reason',None)
for path in list(report['pending']):
    if time.monotonic() - started > 720:
        report['stop_reason'] = '12 minute network budget exhausted'
        break
    try:
        data = (REPO_ROOT / path).read_bytes()
        oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        head = api('git/ref/heads/' + BRANCH)['object']['sha']
        tree = api('git/trees/' + head + '?recursive=1')
        assert not tree.get('truncated')
        existing = next((e for e in tree['tree'] if e['path'] == path), None)
        if existing:
            assert existing['sha'] == oid, 'Refusing to replace different remote content: ' + path
            commit = head
        else:
            result = api('contents/' + quote(path, safe='/'), {
                'branch': BRANCH,
                'message': 'Preserve S artifact: ' + '/'.join(path.split('/')[-2:]),
                'content': base64.b64encode(data).decode()})
            commit = result['commit']['sha']
            assert result['content']['sha'] == oid
        # The contents raw-download route can stall after successful PUTs.
        # Fetch the exact Git blob instead; this never resends uploaded content.
        blob = api('git/blobs/' + oid)
        assert blob['encoding'] == 'base64' and blob['sha'] == oid
        downloaded = base64.b64decode(blob['content'])
        assert downloaded == data, 'Remote download differs: ' + path
        record = {'path': path, 'bytes': len(data), 'commit': commit, 'git_blob_sha': oid,
                  'sha256': hashlib.sha256(data).hexdigest(), 'downloaded_matches_local': True,
                  'download_method': 'Git blob API, base64 decoded to exact bytes'}
        report['verified'] = [e for e in report['verified'] if e['path'] != path] + [record]
        report['pending'].remove(path)
        report['last_verified_head'] = commit
        print('REMOTE_BYTES_VERIFIED', path, commit, flush=True)
    except Exception as exc:
        report['stop_reason'] = str(exc)
        print('UPLOAD_STOPPED', str(exc), flush=True)
        REPORT.write_text(json.dumps(report, indent=2) + '\n')
        sys.exit(1)
    REPORT.write_text(json.dumps(report, indent=2) + '\n')
REPORT.write_text(json.dumps(report, indent=2) + '\n')
print('FINISHED', len(report['verified']), 'verified;', len(report['pending']), 'pending', flush=True)
