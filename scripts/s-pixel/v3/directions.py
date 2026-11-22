"""Build distant colour/depth sprites from the exported 128-plane volume.

The v2 bake has fixed relative paths. Give it a temporary build tree: immutable
v2 code and v1 browser harness, v3 stack inputs, private writable output. This
lets both versions use the identical shader, texel selection and depth padding.
"""
import argparse
import functools
import hashlib
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading

from volume import ASSETS, LAB, ROOT, V2, sha, write_json

RECIPE = ROOT / 'scripts/s-pixel'
ARCHIVED = V2 / 'angles'


def digest_files(pairs):
    result = hashlib.sha256()
    for name, data in sorted(pairs):
        result.update(name.encode() + b'\0' + len(data).to_bytes(8, 'little') + data)
    return result.hexdigest()


def recipe_hash():
    paths = [RECIPE / 'v2/atlas.mjs', RECIPE / 'v2/pad-depth.py', RECIPE / 'browser.mjs',
             LAB / 'sections.js', LAB / 'v2/sections.js', LAB / 'renderer.js']
    return digest_files((str(p.relative_to(ROOT)), p.read_bytes()) for p in paths)


def input_hash(assets):
    manifest = json.loads((assets / 'manifest.json').read_text())
    # The v2 recipe consumes 128-plane indexed images plus the registered camera
    # space, crops, palette, pose ordering and surface construction algorithm.
    fields = {k: float(manifest[k]) for k in ('x0', 'z0', 'sx', 'sz', 'height', 'nx', 'nz')}
    fields['palette'] = manifest['palette']
    fields['poses'] = [(pose['name'], pose['stacks']['128']) for pose in manifest['poses']]
    files = [('metadata', json.dumps(fields, separators=(',', ':'), sort_keys=True).encode())]
    for pose in manifest['poses']:
        name = pose['name'] + '.png'
        files.append((name, (assets / 'stack-128' / name).read_bytes()))
    return digest_files(files)


def describe(atlas):
    index_data = (atlas / 'index.json').read_bytes()
    index = json.loads(index_data)
    pages = {}
    for angle in index['angles']:
        for paint, _, _, depth in angle['files']:
            for name in (paint, depth):
                pages[name] = sha((atlas / name).read_bytes())
    return {
        'indexSHA256': sha(index_data), 'pageSHA256': pages,
        'directions': index['directions'], 'elevations': [a['elev'] for a in index['angles']],
        'samples': sum(len(angle['rects']) for angle in index['angles']),
    }


class QuietFiles(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def render(staging, assets):
    scripts = staging / 'scripts/s-pixel'
    (scripts / 'v2').mkdir(parents=True)
    for name in ('v2/atlas.mjs', 'v2/pad-depth.py', 'browser.mjs'):
        shutil.copyfile(RECIPE / name, scripts / name)
    (staging / 'node_modules').symlink_to(ROOT / 'node_modules', target_is_directory=True)
    web = staging / 'public/s-pixel-lab'
    source = web / 'v2/assets'
    source.mkdir(parents=True)
    for item in ('index.html', 'lab.css', 'lab.js', 'renderer.js', 'sections.js', 'assets'):
        (web / item).symlink_to(LAB / item)
    (web / 'v2/sections.js').symlink_to(LAB / 'v2/sections.js')
    for item in ('stack-128', 'manifest.json'):
        (source / item).symlink_to(assets / item)
    handler = functools.partial(QuietFiles, directory=str(staging / 'public'))
    with http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            env = {**os.environ, 'LAB_URL': f'http://127.0.0.1:{server.server_port}/s-pixel-lab/'}
            subprocess.run(['node', str(scripts / 'v2/atlas.mjs')], env=env, check=True)
        finally:
            server.shutdown()
            thread.join()
    subprocess.run([sys.executable, str(scripts / 'v2/pad-depth.py')], check=True)
    return source / 'angles'


def publish(assets, force):
    recipe, inputs = recipe_hash(), input_hash(assets)
    # Cache keys are pinned to the verified v2 build. Editing either the shader
    # or a voxel-derived input causes a real rebuild, even if v2 is edited too.
    cache = json.loads((RECIPE / 'v3/direction-cache.json').read_text())
    old = describe(ARCHIVED)
    output_hash = sha(json.dumps(old, sort_keys=True, separators=(',', ':')).encode())
    can_reuse = inputs == cache['inputs'] and recipe == cache['recipe'] and output_hash == cache['output']
    if can_reuse and not force:
        descriptor = old
        index_url = '../../v2/assets/angles/index.json'
    else:
        with tempfile.TemporaryDirectory(prefix='s01-angles-') as temp:
            built = render(Path(temp), assets)
            descriptor = describe(built)
            if descriptor == old:
                index_url = '../../v2/assets/angles/index.json'
            else:
                # Content addressing keeps the old atlas valid while a new one
                # is being written and avoids serving stale pages after edits.
                build_hash = sha(json.dumps(descriptor, sort_keys=True).encode())[:16]
                dirname = 'angles-' + build_hash
                shutil.copytree(built, assets / dirname, dirs_exist_ok=True)
                index_url = dirname + '/index.json'
    write_json(assets / 'directions.json', {
        'index': index_url, 'stack128SHA256': inputs, 'recipeSHA256': recipe, **descriptor,
    })
    print('Far sprite index:', index_url, '/', descriptor['samples'], 'registered views')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='Render all 12,000 views even if hashes match')
    parser.add_argument('--assets', type=Path, default=ASSETS, help='v3 stack input and descriptor output directory')
    args = parser.parse_args()
    publish(args.assets.resolve(), args.force)
