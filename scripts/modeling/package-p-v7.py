"""Package unaltered actual GLB renders; retain the canonical source verbatim."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'docs/evidence/p-canonical-3d-v7-20261012'
VIEWS=['SIDE','FRONT','FRONT34','REAR34','BACK']
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(fontpath,22);small=ImageFont.truetype(fontpath,16)
for version in ['', 'v6-']:
    for view in VIEWS:
        im=Image.open(E/f'{version}{view}.png').convert('RGB')
        im.save(E/f'{version}{view}.webp',quality=94,method=6)
canvas=Image.new('RGB',(1650,1000),'#e2e7e9');d=ImageDraw.Draw(canvas)
for i,view in enumerate(VIEWS):
    x=(i%3)*550;y=(i//3)*500
    im=Image.open(E/f'{view}.webp');im.thumbnail((550,450));canvas.paste(im,(x,y+42))
    d.text((x+15,y+10),'v7 / '+view,font=font,fill='#152735')
d.text((1120,550),'STATIC SHAPE: REVISE',font=font,fill='#9c302a')
d.text((1120,605),'Actual p-canonical-v7.glb renders',font=small,fill='#263743')
d.text((1120,640),'No gait / no production approval',font=small,fill='#263743')
canvas.save(E/'five-views.webp',quality=94,method=6)
canvas=Image.new('RGB',(1650,770),'#e2e7e9');d=ImageDraw.Draw(canvas)
titles=['Canonical P.webp (unchanged)','v6 / exact GLB','v7 / exact GLB']
for i,title in enumerate(titles):d.text((i*550+15,16),title,font=font,fill='#152735')
ref=Image.open(ROOT/'public/concept/P.webp').convert('RGB');ref=ref.resize((517,407),Image.Resampling.NEAREST);canvas.paste(ref,(16,110))
for i,version in [(1,'v6-'),(2,'')]:
    im=Image.open(E/f'{version}FRONT34.webp');im.thumbnail((550,550));canvas.paste(im,(550*i,65))
d.text((15,590),'Single 207 x 163 authority image;',font=small,fill='#263743')
d.text((15,615),'not an orthographic or relit reference.',font=small,fill='#263743')
d.text((565,590),'v6 and v7: identical orthographic camera, scale, lights, rest pose and render settings.',font=small,fill='#263743')
d.text((15,680),'REVISE: continuous topology improved; canonical muscle volumes and surface planes remain mismatched.',font=font,fill='#9c302a')
d.text((15,725),'Static gate not passed. Rig deformation and running deliberately not advanced.',font=small,fill='#263743')
canvas.save(E/'comparison-canonical-v6-v7.webp',quality=95,method=6)
# Full five-view v6/v7 comparison: no per-model scaling or cropping.
canvas=Image.new('RGB',(1500,1340),'#e2e7e9');d=ImageDraw.Draw(canvas)
for row,version in enumerate(['v6-','']):
    for col,view in enumerate(VIEWS):
        im=Image.open(E/f'{version}{view}.webp');im.thumbnail((300,300));x=col*300;y=row*380
        canvas.paste(im,(x,y+55));d.text((x+12,y+15),('v6' if version else 'v7')+' / '+view,font=small,fill='#152735')
ref=Image.open(ROOT/'public/concept/P.webp').convert('RGB').resize((517,407),Image.Resampling.NEAREST);canvas.paste(ref,(20,875))
d.text((20,810),'Canonical P.webp / unchanged pixels, nearest-neighbour enlargement',font=font,fill='#152735')
d.text((580,940),'Same-model comparison cameras fixed across both GLBs.',font=font,fill='#263743')
d.text((580,995),'Front and rear anatomy are inferred from the single reference.',font=font,fill='#263743')
d.text((580,1060),'Static review: REVISE / production HOLD.',font=font,fill='#9c302a')
canvas.save(E/'comparison-five-views.webp',quality=94,method=6)
files=['public/concept/P.webp','art/p-creature/workspaces/P-v6-canonical-sculpt-review.blend','public/models/evowild-p/p-canonical-v6.glb','art/p-creature/workspaces/P-v7-reference-retopology.blend','public/models/evowild-p/p-canonical-v7.glb']
hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
(E/'artifact-sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
print('packaged',len(VIEWS),'actual v7 views and common-camera v6 comparisons')
