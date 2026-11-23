"""Select slow interval predecessors, then summarize their independent GPU replays."""
import csv
import json
import sys
from pathlib import Path

work,out=map(Path,sys.argv[1:3])
versions=('before','after')
extremes={}
rows=[]
for screen in ('pc','phone'):
    for n in (50,100):
        for cam in ('race','follow'):
            key=f'{screen}-{n}-pixel-{cam}'
            for version in versions:
                samples=json.loads((work/f'accept-{version}'/(key+'.json')).read_text())['samples']
                slow=sorted(range(len(samples)),key=lambda i:-samples[i]['interval_ms'])[:3]
                # A reported RAF gap ends at sample i (simulation frame 25+i).
                # Replay the preceding rendered frame, which occupied that gap.
                extremes.setdefault(key,set()).update(i+24 for i in slow)
                for i in slow:
                    rows.append(dict(id=key,build=version,frame=i+24,gap_ms=round(samples[i]['interval_ms'],2)))
(work/'tail-frames.json').write_text(json.dumps({k:sorted(v) for k,v in extremes.items()}))
if len(sys.argv)>3:
    for row in rows:
        folder=work/('tail-'+row['build'])
        data=next(r for r in json.loads((folder/(row['id']+'.json')).read_text()) if r['frame']==row['frame'])
        assert not data['streaming']
        for k in ('ground','course','classicS','otherMorph','sceneOther','pixelMesh','sprite'):
            row['replay_gpu_'+k+'_ms']=round(data['gpu'].get(k,0),3)
        for k in ('simulation','ui','pixel','wait'):
            row['replay_cpu_'+k+'_ms']=round(data['cpu'].get(k,0),3)
        row['surface_triangles']=data['triangles'].get('pixelMesh',0)
        row.update(data['lod'])
    with (out/'slow-replay.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
