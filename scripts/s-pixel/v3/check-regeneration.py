"""A scratch-only regression check: edit one pose in the volume, rebuild distant sprites.

The published art is read-only throughout. The probe exchanges two palette indices
in the idle pose. Its silhouette and atlas packing must therefore remain fixed;
all 24 unedited poses and all depth pages must retain their previous pixels.
"""
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

from directions import ARCHIVED, ASSETS, publish
from volume import EVIDENCE, sha, write_json

here = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='s01-source-edit-') as tmpdir:
    root = Path(tmpdir) / 'assets'
    shutil.copytree(ASSETS / 'voxels', root / 'voxels')
    source_path = root / 'voxels/index.json'
    source = json.loads(source_path.read_text())
    idle = source['poses'][0]
    file = root / 'voxels' / idle['file']
    raw = np.frombuffer(gzip.decompress(file.read_bytes()), np.uint8).copy()
    # A bijective exchange preserves the greedy mesher's equality boundaries.
    ivory, silver = raw == 10, raw == 9
    changed = ivory | silver
    assert ivory.any() and silver.any()
    raw[ivory], raw[silver] = 9, 10
    file.write_bytes(gzip.compress(raw.tobytes(), mtime=0))
    idle['sha256'] = sha(raw.tobytes())
    write_json(source_path, source)
    subprocess.run([sys.executable, str(here / 'volume.py'), 'stacks', '--assets', str(root)], check=True)
    publish(root, False)
    descriptor = json.loads((root / 'directions.json').read_text())
    assert descriptor['index'].startswith('angles-')
    result_dir = (root / descriptor['index']).parent
    geometry = (result_dir / 'index.json').read_bytes()
    assert geometry == (ARCHIVED / 'index.json').read_bytes()
    atlas = json.loads(geometry)
    totals = {'idleChangedViews': 0, 'runChangedViews': 0, 'changedDepthPages': 0}
    for bank in atlas['angles']:
        for pg, (paint, _, _, depth) in enumerate(bank['files']):
            with Image.open(result_dir / depth) as a, Image.open(ARCHIVED / depth) as b:
                totals['changedDepthPages'] += int(a.tobytes() != b.tobytes())
            with Image.open(result_dir / paint) as a, Image.open(ARCHIVED / paint) as b:
                im_a, im_b = np.asarray(a), np.asarray(b)
                for tile, (page, x, y, w, h, _, _) in enumerate(bank['rects']):
                    if page != pg:
                        continue
                    diff = np.any(im_a[y:y+h, x:x+w] != im_b[y:y+h, x:x+w])
                    counts = 'idleChangedViews' if tile < atlas['directions'] else 'runChangedViews'
                    totals[counts] += int(diff)
    assert totals['idleChangedViews'] > 0 and not totals['runChangedViews'] and not totals['changedDepthPages'], totals
    write_json(EVIDENCE / 'regeneration-probe.json', {
        'scratchPose': idle['name'], 'scratchIndexExchange': [10, 9], 'changedVoxels': int(changed.sum()),
        'scratchStack128SHA256': descriptor['stack128SHA256'], 'scratchFarIndex': descriptor['index'],
        'unchangedPoses': 24, 'totalViews': descriptor['samples'], **totals,
    })
    print(totals)
