"""Track the lowest drawn band of each supporting foot in world coordinates."""
import json
import math
from pathlib import Path
import runpy
import numpy as np

here=Path(__file__).resolve().parent
build=runpy.run_path(str(here/'bake.py'))
source=build['source']
source.load_drawings()
for part in source.PARTS:
    source.reconstruct(part)

soles={'v1':{},'v2':{}}
for frame in range(24):
    _,feet=source.rig(frame)
    for leg,foot in feet.items():
        if not foot['contact']:
            continue
        parts=[p for p in source.PARTS if p['name'] in [leg+s for s in ('inner','outer','ankle')]]
        vol,_=source.posed(frame,parts)
        for version in soles:
            if version=='v2':
                build['shift_limb'](vol,leg,frame)
            y=int(np.flatnonzero(vol.any(axis=(1,2)))[0])
            z,x=np.nonzero(vol[y]);soles[version][frame,leg]=(source.X[x].mean()-385,source.Z[z].mean()*1.32,y*source.SY)

def world(x,z,d,bend):
    if not bend:
        return (x-d,z)
    angle=d/1750
    c,s=math.cos(angle),math.sin(angle)
    return (-1750*s+c*x-s*z,1750*c+s*x+c*z)

result={}
for version,positions in soles.items():
    rows={}
    for samples in (12,24):
        step=24//samples
        for bend in (False,True):
            movements=[]
            for (frame,leg),(x,z,_) in positions.items():
                neighbor=positions.get(((frame+step)%24,leg))
                if frame%step or neighbor is None:
                    continue
                start=world(x,z,0,bend)
                for sub in range(1,9):
                    d=source.STRIDE/samples*sub/8
                    a,b=(x+d,z) if sub<8 else neighbor[:2]
                    movements.append(math.dist(start,world(a,b,d,bend)))
            rows[f'{samples}-'+('bend' if bend else 'straight')]={'samples':len(movements),'p95':round(float(np.percentile(movements,95)),3),'max':round(max(movements),3)}
    result[version]=rows
(build['EVIDENCE']/'stance.json').write_text(json.dumps(result,indent=2))
