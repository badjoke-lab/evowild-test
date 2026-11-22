"""Pack nonempty 12-cell bricks without modifying any indexed source voxel.

The two triangles of a brick are its conservative screen bounds. The renderer
intersects the ray with the brick, then visits the original cells to find colour
and the actual first surface depth. Empty margins do not occupy GPU storage.
"""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

ASSETS = Path(__file__).resolve().parents[3] / 'public/s-pixel-lab/v3/assets'
BRICK = 12


def generate():
    source = ASSETS / 'voxels'
    dest = ASSETS / 'exact'
    dest.mkdir(exist_ok=True)
    manifest = json.loads((source / 'index.json').read_text())
    paint = bytearray()
    descriptors = []
    poses = []
    for pose in manifest['poses']:
        raw = gzip.decompress((source / (pose['name'] + '.u8.gz')).read_bytes())
        volume = np.frombuffer(raw, dtype='u1').reshape(manifest['shape'])
        restored = np.zeros_like(volume)
        first = len(descriptors)
        for y in range(0, volume.shape[0], BRICK):
            for z in range(0, volume.shape[1], BRICK):
                for x in range(0, volume.shape[2], BRICK):
                    chunk = volume[y:y+BRICK, z:z+BRICK, x:x+BRICK]
                    cy, cz, cx = np.nonzero(chunk)
                    if not cy.size:
                        continue
                    x0, y0, z0 = x + cx.min(), y + cy.min(), z + cz.min()
                    sx, sy, sz = np.ptp(cx)+1, np.ptp(cy)+1, np.ptp(cz)+1
                    box = np.s_[y0:y0+sy, z0:z0+sz, x0:x0+sx]
                    offset = len(paint)
                    paint.extend(volume[box].tobytes())
                    descriptors.append([x0, y0, z0, offset, sx, sy, sz, 0])
                    restored[box] = np.frombuffer(paint[offset:], 'u1').reshape(sy, sz, sx)
        if not np.array_equal(restored, volume):
            raise ValueError(f'Brick round-trip failed for {pose["name"]}')
        poses.append(dict(name=pose['name'], first=first, count=len(descriptors)-first,
                          sha256=hashlib.sha256(raw).hexdigest()))
    (dest / 'bricks.u32.gz').write_bytes(gzip.compress(np.asarray(descriptors, dtype='<u4').tobytes(), mtime=0))
    (dest / 'paint.u8.gz').write_bytes(gzip.compress(bytes(paint), mtime=0))
    index = dict(brickEdge=BRICK, origin=manifest['originXYZ'], step=manifest['stepXYZ'],
                 paintBytes=len(paint), descriptors=len(descriptors), poses=poses)
    (dest / 'index.json').write_text(json.dumps(index, separators=(',', ':')))
    print(f'{len(poses)} poses, {len(descriptors)} tight boxes, {len(paint):,} indexed bytes')


if __name__ == '__main__':
    generate()
