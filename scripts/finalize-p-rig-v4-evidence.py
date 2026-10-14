"""Compose evidence from actual captured browser frames and record provenance."""
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root=Path('docs/evidence/p-rig-v4-20261014')
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
data=json.loads((root/'isolated-continuous-trace.json').read_text())
frames=data['frames']
cycle=int(frames[0]['cycle'])+1
strip=Image.new('RGB',(1920,1050),'#e8eef0')
d=ImageDraw.Draw(strip)
selected=[]
for phase in range(12):
    frame=min(frames,key=lambda f:abs(f['cycle']-cycle-phase/12))
    file=Path('work/p-rig-v4/capture/v4/isolated-continuous')/f"{frame['index']:04}.png"
    im=Image.open(file).convert('RGB').crop((360,180,840,490))
    x,y=phase%4*480,phase//4*350
    strip.paste(im,(x,y+30))
    d.text((x+12,y+5),f"{frame['index']/60:.3f}s / phase {frame['phase']:.3f} / {'FLIGHT' if frame['flight'] else 'SUPPORT'}",font=font,fill='#203844')
    selected.append(frame)
strip.save(root/'actual-motion-filmstrip.png')
(root/'actual-motion-filmstrip-frames.json').write_text(json.dumps(selected,indent=2)+'\n')

paired=json.loads((root/'all-20-contact-validation.json').read_text())
with (root/'all-20-foot-raster.csv').open('w',newline='') as f:
    w=csv.writer(f,lineterminator='\n')
    w.writerow(['run','version','runner/foot','comparedIntervals','soleMeanPx','soleMaxPx','centroidMeanPx','centroidMaxPx','anchorMaxMetres','laneMax','soleVerticalResidualMeanPx','soleVerticalResidualMaxPx'])
    for run in paired['results']:
        for version in run['versions']:
            for id,v in version['byFoot'].items():
                w.writerow([run['name'],version['version'],id,v['soles']['n'],v['soles']['mean'],v['soles']['max'],v['centroids']['mean'],v['centroids']['max'],v['anchors']['max'],v['lanes']['max'],v['verticalResiduals']['mean'],v['verticalResiduals']['max']])

videos={}
for p in sorted(root.glob('*.mp4')):
    videos[p.name]=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,size:stream=width,height,r_frame_rate,nb_frames','-of','json',str(p)],text=True))
tests=json.loads((root/'2p5d-test-results.json').read_text())['stats']
files=subprocess.check_output(['git','diff','--name-only','HEAD'],text=True).splitlines()
files+=subprocess.check_output(['git','ls-files','--others','--exclude-standard','public/concept/p-layered-v4','docs/evidence/p-rig-v4-20261014','docs/p-rig-v4-review-20261014.md','scripts/*p-rig-v4*'],text=True).splitlines()
files=sorted(set(files))
(root/'changed-files.txt').write_text('\n'.join(sorted(set(files+['docs/evidence/p-rig-v4-20261014/changed-files.txt','docs/evidence/p-rig-v4-20261014/validation.json'])))+'\n')
hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files if Path(p).is_file() and not p.endswith(('validation.json','changed-files.txt'))}
(root/'validation.json').write_text(json.dumps({
    'baseline':'6025245731c2484bfaab5e2817f06cc8e804716a',
    'verdict':'REVISE; support control KEEP; no default promotion',
    'chromium':subprocess.check_output(['/usr/bin/chromium','--version'],text=True).strip(),
    'local2p5dTests':tests,'build':'PASS: npm --ignore-scripts run build',
    'videos':videos,'sha256':hashes,
    'limitations':['Pixel 7 emulation, not a physical mobile device','Virtual clock rendering, not a real-time 60fps performance measurement','Foot raster metrics use isolated pre-occlusion masks; whole-scene optical foot tracking is not claimed','Finite sampled interval, not a global bound on body correction']
},indent=2)+'\n')
print(json.dumps({'testStats':tests,'videos':{k:v['format']['duration'] for k,v in videos.items()},'files':len(files)}))
