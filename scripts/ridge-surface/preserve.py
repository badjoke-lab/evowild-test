"""Record source and asset trees that must match the specified starting commit."""
import hashlib
import json
import platform
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2]
ref='2606922a521ae9d9d8a4563824c22b13f2d12815'
paths=['src','public/s-pixel-lab','public/race-integration','public/ridge-performance']
subprocess.run(['git','diff','--exit-code',ref,'--',*paths],cwd=root,check=True)
trees={p:subprocess.check_output(['git','rev-parse',ref+':'+p],cwd=root,text=True).strip() for p in paths}
manifest=json.loads((root/'public/s-pixel-lab/v3/assets/manifest.json').read_text())
data=dict(starting_head=ref,preserved_trees=trees,poses=manifest['frames'],palette_entries=len(manifest['palette']),
    renderer='Chromium / ANGLE SwiftShader',physical_gpu_measured=False,
    chromium=subprocess.check_output(['/usr/bin/chromium','--version'],text=True).strip(),platform=platform.platform(),
    cpu_quota=Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
    assets={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in [
        'public/s-pixel-lab/v4.1/assets/geometry.gz','public/s-pixel-lab/v3/assets/runtime/paint.gz',
        'public/ridge-performance/ridge-optimized.zip']})
(root/'public/ridge-surface/evidence/preserved.json').write_text(json.dumps(data,indent=2)+'\n')
print('Preserved source and artifact trees verified.')
