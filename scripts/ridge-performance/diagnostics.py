"""Summarize two single-variable controls with the same course, cameras and poses."""
import csv
import json
import sys
from pathlib import Path
from statistics import mean

work,report=map(Path,sys.argv[1:3])
rows=[]
for screen in ('pc','phone'):
    for camera in ('race','follow'):
        key=f'{screen}-100-pixel-{camera}'
        ref=json.loads((work/'measured-after'/(key+'.json')).read_text())
        for folder in ('ground-only','measured-after','flat-color'):
            samples=json.loads((work/folder/(key+'.json')).read_text())
            for a,b in zip(ref,samples,strict=True):
                assert all(a[k]==b[k] for k in ('frame','size','state_sha','actors_sha','nativeVisible','pixel_ids','lod'))
                if folder=='flat-color':
                    assert a['triangles']==b['triangles'] and a['calls']==b['calls']
            values=lambda key,part:round(mean(i[key].get(part,0) for i in samples),3)
            rows.append(dict(id=key,control=folder,frames=len(samples),mesh_gpu_ms=values('gpu','pixelMesh'),
                             ground_gpu_ms=values('gpu','ground'),wait_ms=values('cpu','wait'),
                             mesh_triangles=values('triangles','pixelMesh'),mesh_draws=values('calls','pixelMesh')))
with (report/'surface-controls.csv').open('w',newline='') as f:
    out=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');out.writeheader();out.writerows(rows)
