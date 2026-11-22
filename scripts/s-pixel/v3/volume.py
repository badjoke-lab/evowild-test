"""Register the corrected four-view S art as an indexed volume per pose.

Only `source` reads the drawings and rig. The derivative commands instead
read the published volumes, so a revision cannot require repainting a LOD.
"""
import argparse
import gzip
import hashlib
import json
import runpy
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / 'public/s-pixel-lab'
ASSETS = LAB / 'v3/assets'
VOXELS = ASSETS / 'voxels'
EVIDENCE = LAB / 'v3/evidence'
V2 = LAB / 'v2/assets'
GRID_OFFSET = 385  # Existing rig's pivot in side-drawing units.
WIDTH_SCALE = 1.32  # Registered end-view width in world space.


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value, compact=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=None if compact else 2,
                               separators=(',', ':') if compact else None) + '\n')


def load_volume(index, pose):
    raw = gzip.decompress((VOXELS / pose['file']).read_bytes())
    if sha(raw) != pose['sha256']:
        raise ValueError('Source checksum mismatch for ' + pose['name'])
    data = np.frombuffer(raw, np.uint8).reshape(index['shape'])
    if data.max() >= len(index['palette']):
        raise ValueError('Unknown palette index in ' + pose['name'])
    return data


def generate_source():
    # Use the locked four-view registration and exact v2 limb/crest corrections.
    v2 = runpy.run_path(str(ROOT / 'scripts/s-pixel/v2/bake.py'))
    rig = v2['source']
    art = ROOT / 'art/s-creature/references/00_s_type_modeling_image_v1.png'
    if sha(art.read_bytes()) != rig.SOURCE:
        raise ValueError('Canonical reference does not match the S design lock')
    rig.load_drawings()
    for part in rig.PARTS:
        rig.reconstruct(part)
    origin = [rig.X0 - GRID_OFFSET, 0, rig.Z0 * WIDTH_SCALE]
    index = {
        'format': 'indexed-voxel-v1', 'dtype': 'uint8', 'compression': 'gzip',
        'order': ['y', 'z', 'x'], 'shape': [rig.NY, rig.NZ, rig.NX],
        'originXYZ': origin, 'stepXYZ': [rig.SX, rig.SY, rig.SZ * WIDTH_SCALE],
        'sideDrawingPivotX': GRID_OFFSET, 'transparentIndex': 0,
        'palette': ['#' + c for c in rig.PALETTE.values()],
        'period': rig.PERIOD, 'frames': rig.NFRAMES, 'stride': rig.STRIDE,
        'referenceSHA256': rig.SOURCE, 'reference': str(art.relative_to(ROOT)),
        'poses': [],
    }
    VOXELS.mkdir(parents=True, exist_ok=True)
    for frame in range(-1, rig.NFRAMES):
        name = 'idle' if frame == -1 else f'run-{frame:02}'
        transforms, feet = rig.rig(frame)
        volume = np.zeros(index['shape'], np.uint8)
        for part in rig.PARTS:
            key = part['name']
            cells, _ = rig.posed(frame, [part])
            leg = v2['in_limb'](key)
            if leg:
                v2['shift_limb'](cells, leg, frame)
            if key.startswith('crest'):
                v2['restore_spine'](cells, part, transforms[key])
            np.copyto(volume, cells, where=cells != 0)
        raw = volume.tobytes()
        filename = name + '.u8.gz'
        (VOXELS / filename).write_bytes(gzip.compress(raw, compresslevel=6, mtime=0))
        index['poses'].append({'name': name, 'file': filename, 'sha256': sha(raw),
                               'occupied': int(np.count_nonzero(volume)), 'feet': feet})
    write_json(VOXELS / 'index.json', index)


def pack_slices(volume, count, palette, path):
    ny, nz, nx = volume.shape
    if ny % count:
        raise ValueError('Stack count must divide volume height')
    planes = volume.reshape(count, ny // count, nz, nx)
    middle = planes.shape[1] // 2
    slices = planes[:, middle].copy()
    # A narrow feature may lie on only one plane of a coarser band.
    for j in sorted(range(planes.shape[1]), key=lambda k: abs(k + .5 - planes.shape[1] / 2)):
        np.copyto(slices, planes[:, j], where=(slices == 0) & (planes[:, j] != 0))
    rects = []
    u = v = shelf = 0
    for layer in slices:
        z, x = np.nonzero(layer)
        left, top, w, h = (int(x.min()), int(z.min()), int(np.ptp(x)+1), int(np.ptp(z)+1)) if len(x) else (0, 0, 0, 0)
        if u + w > 1024:
            u, v, shelf = 0, v + shelf, 0
        rects.append([left, top, w, h, u, v])
        u += w
        shelf = max(shelf, h)
    atlas = np.zeros((v + shelf, 1024), np.uint8)
    for layer, (x, z, w, h, u, v) in zip(slices, rects):
        atlas[v:v+h, u:u+w] = layer[z:z+h, x:x+w]
    img = Image.frombytes('P', (atlas.shape[1], atlas.shape[0]), atlas.tobytes())
    rgb = b''.join(bytes.fromhex(c[1:]) for c in palette)
    img.putpalette(rgb.ljust(768, b'\0'))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, transparency=0, optimize=True)
    return rects


def generate_stacks():
    index = json.loads((VOXELS / 'index.json').read_text())
    ny, nz, nx = index['shape']
    sx, sy, sz = index['stepXYZ']
    x0, _, z0 = index['originXYZ']
    manifest = {k: index[k] for k in ('palette', 'period', 'frames', 'stride')}
    manifest.update(x0=x0 + index['sideDrawingPivotX'], z0=z0, sx=sx, sz=sz,
                    height=ny*sy, nx=nx, nz=nz, poses=[])
    for pose in index['poses']:
        cells = load_volume(index, pose)
        stacks = {}
        for count in (64, 128):
            path = ASSETS / f'stack-{count}' / (pose['name'] + '.png')
            stacks[str(count)] = pack_slices(cells, count, index['palette'], path)
        manifest['poses'].append({'name': pose['name'], 'feet': pose['feet'], 'stacks': stacks})
    write_json(ASSETS / 'manifest.json', manifest, compact=True)


def unpack_atlas(root, entry, count, shape):
    ny, nz, nx = shape
    volume = np.zeros((count, nz, nx), np.uint8)
    with Image.open(root / f'stack-{count}' / (entry['name'] + '.png')) as img:
        if img.mode != 'P' or img.info.get('transparency') != 0:
            raise ValueError('Expected an indexed, transparent source atlas')
        sheet = np.asarray(img)
        for y, (x, z, w, h, u, v) in enumerate(entry['stacks'][str(count)]):
            volume[y, z:z+h, x:x+w] = sheet[v:v+h, u:u+w]
    return volume


def compare_v2():
    source = json.loads((VOXELS / 'index.json').read_text())
    v2 = json.loads((V2 / 'manifest.json').read_text())
    v3 = json.loads((ASSETS / 'manifest.json').read_text())
    report = {'shapeYZX': source['shape'], 'paletteMatchesV2': v2['palette'] == v3['palette'],
              'metadataEqual': v2 == v3, 'poses': []}
    for p, old, new in zip(source['poses'], v2['poses'], v3['poses'], strict=True):
        cells = load_volume(source, p)
        row = {'name': p['name'], 'voxelSHA256': p['sha256']}
        for count in (64, 128):
            a = unpack_atlas(V2, old, count, source['shape'])
            b = unpack_atlas(ASSETS, new, count, source['shape'])
            diff = np.count_nonzero(a != b)
            row[f'v2IndexDiff{count}'] = int(diff)
            if count == 128:
                row['roundTripDiff'] = int(np.count_nonzero(cells != b))
        report['poses'].append(row)
    write_json(EVIDENCE / 'voxel-roundtrip.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['source', 'stacks', 'verify', 'all'])
    parser.add_argument('--assets', type=Path, default=ASSETS, help='Use a separate set of source and stack files')
    args = parser.parse_args()
    ASSETS = args.assets.resolve()
    VOXELS = ASSETS / 'voxels'
    EVIDENCE = ASSETS.parent / 'evidence'
    if args.stage in ('source', 'all'):
        generate_source()
    if args.stage in ('stacks', 'all'):
        generate_stacks()
    if args.stage in ('verify', 'all'):
        result = compare_v2()
        differences = sum(row['v2IndexDiff64'] + row['v2IndexDiff128'] for row in result['poses'])
        print(f"{len(result['poses'])} poses. Index differences against v2: {differences}.")
        if any(p['roundTripDiff'] for p in result['poses']):
            raise ValueError('Lossy round-trip in the full resolution stack')
