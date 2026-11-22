"""Count exact external quads without uploading them to WebGL.

The first scan uses the same u/v/sign/material contract as sections.js. The
second can merge through paint boundaries because v3 samples a spatial palette
texture. For each plane try both scan orders; keep the cheaper exact tiling.
"""
import gzip
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

ASSETS = Path(__file__).resolve().parents[3] / 'public/s-pixel-lab/v3/assets'


def rectangles(mask):
    # Mutate a compact local plane. Every accepted rectangle must be exactly
    # constant, including the face sign (opposing normals cannot be merged).
    mask = mask.copy()
    count = 0
    for y in np.flatnonzero(mask.any(axis=1)):
        cols = np.flatnonzero(mask[y])
        for x in cols:
            value = mask[y, x]
            if not value:
                continue
            right = x + 1
            while right < mask.shape[1] and mask[y, right] == value:
                right += 1
            bottom = y + 1
            while bottom < mask.shape[0] and np.all(mask[bottom, x:right] == value):
                bottom += 1
            mask[y:bottom, x:right] = 0
            count += 1
    return count


def face_counts(volume):
    xyz = volume.transpose(2, 0, 1).astype(np.int16)
    occupied = xyz != 0
    filled = ndimage.binary_fill_holes(occupied)
    # A virtual solid sentinel only occupies sealed air. It is never visible.
    filled_xyz = np.where(filled & ~occupied, 18, xyz)
    counts = dict(faces=0, exteriorFaces=0, stackQuads=0, outsideColorQuads=0,
                  outsideMaterialFreeQuads=0, dualScanQuads=0)
    for axis in range(3):
        order = (axis, (axis + 2) % 3, (axis + 1) % 3)
        original = xyz.transpose(order)
        closed = filled_xyz.transpose(order)
        empty = np.zeros(original.shape[1:], dtype=np.int16)
        for i in range(original.shape[0] + 1):
            def boundary(planes):
                a = planes[i - 1] if i else empty
                b = planes[i] if i < planes.shape[0] else empty
                return np.where(b == 0, a, np.where(a == 0, -b, 0))
            mask = boundary(original)
            if not mask.any():
                continue
            counts['faces'] += np.count_nonzero(mask)
            color = rectangles(mask)
            counts['stackQuads'] += color
            outer = boundary(closed)
            counts['exteriorFaces'] += np.count_nonzero(outer)
            counts['outsideColorQuads'] += rectangles(outer) if np.any(mask != outer) else color
            signs = np.sign(outer)
            normal = rectangles(signs)
            counts['outsideMaterialFreeQuads'] += normal
            counts['dualScanQuads'] += min(normal, rectangles(signs.T))
    return {key: int(value) for key, value in counts.items()}


def main():
    root = ASSETS / 'voxels'
    meta = json.loads((root / 'index.json').read_text())
    rows = []
    for p in meta['poses']:
        volume = np.frombuffer(gzip.decompress((root / p['file']).read_bytes()), np.uint8).reshape(meta['shape'])
        row = {'pose': p['name'], 'voxelCells': int((volume > 0).sum()), **face_counts(volume)}
        rows.append(row)
        print(row['pose'], row['stackQuads'], row['dualScanQuads'], flush=True)
    (ASSETS.parent / 'evidence/greedy.json').write_text(json.dumps(rows, indent=1) + '\n')


if __name__ == '__main__':
    main()
