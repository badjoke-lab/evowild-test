"""Create an offline-served release archive with a local launcher."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
root=Path(__file__).resolve().parents[2]
demo=root/'public/s-pixel-lab'
with ZipFile(root/'public/s-pixel-lab-demo.zip','w',compression=ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(demo.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(demo))
