"""Package unaltered actual GLB renders; retain the canonical source verbatim."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'docs/evidence/p-canonical-3d-v8-20261013'
W=ROOT/'work/p-canonical-v8/rendered'
VIEWS=['SIDE','FRONT','FRONT34','REAR34','BACK']
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(fontpath,22);small=ImageFont.truetype(fontpath,16)
for version in ['v8-', 'v7-']:
    for view in VIEWS:
        im=Image.open(W/f'{version}{view}.png').convert('RGB')
        im.save(E/f'{version if version=='v7-' else ''}{view}.webp',quality=94,method=6)
canvas=Image.new('RGB',(1650,1000),'#e2e7e9');d=ImageDraw.Draw(canvas)
for i,view in enumerate(VIEWS):
    x=(i%3)*550;y=(i//3)*500
    im=Image.open(E/f'{view}.webp');im.thumbnail((550,450));canvas.paste(im,(x,y+42))
    d.text((x+15,y+10),'v8 / '+view,font=font,fill='#152735')
d.text((1120,550),'STATIC SHAPE: REVISE',font=font,fill='#9c302a')
d.text((1120,605),'Actual p-canonical-v8.glb renders',font=small,fill='#263743')
d.text((1120,640),'No gait / no production approval',font=small,fill='#263743')
canvas.save(E/'five-views.webp',quality=94,method=6)
canvas=Image.new('RGB',(1650,770),'#e2e7e9');d=ImageDraw.Draw(canvas)
titles=['Canonical P.webp (unchanged)','v7 / exact GLB','v8 / exact GLB']
for i,title in enumerate(titles):d.text((i*550+15,16),title,font=font,fill='#152735')
ref=Image.open(ROOT/'public/concept/P.webp').convert('RGB');ref=ref.resize((517,407),Image.Resampling.NEAREST);canvas.paste(ref,(16,110))
for i,version in [(1,'v7-'),(2,'')]:
    im=Image.open(E/f'{version}FRONT34.webp');im.thumbnail((550,550));canvas.paste(im,(550*i,65))
d.text((15,590),'Single 207 x 163 authority image;',font=small,fill='#263743')
d.text((15,615),'not an orthographic or relit reference.',font=small,fill='#263743')
d.text((565,590),'v7 and v8: identical orthographic camera, scale, lights, rest pose and render settings.',font=small,fill='#263743')
d.text((15,680),'REVISE: chest folds, shoulder height and tail thickness improved; canonical anatomy still mismatched.',font=font,fill='#9c302a')
d.text((15,725),'Static gate not passed. Rig deformation and running deliberately not advanced.',font=small,fill='#263743')
canvas.save(E/'comparison-canonical-v7-v8.webp',quality=95,method=6)
# Full five-view v7/v8 comparison: no per-model scaling or cropping.
canvas=Image.new('RGB',(1500,1340),'#e2e7e9');d=ImageDraw.Draw(canvas)
for row,version in enumerate(['v7-','']):
    for col,view in enumerate(VIEWS):
        im=Image.open(E/f'{version}{view}.webp');im.thumbnail((300,300));x=col*300;y=row*380
        canvas.paste(im,(x,y+55));d.text((x+12,y+15),('v7' if version else 'v8')+' / '+view,font=small,fill='#152735')
ref=Image.open(ROOT/'public/concept/P.webp').convert('RGB').resize((517,407),Image.Resampling.NEAREST);canvas.paste(ref,(20,875))
d.text((20,810),'Canonical P.webp / unchanged pixels, nearest-neighbour enlargement',font=font,fill='#152735')
d.text((580,940),'Same-model comparison cameras fixed across both GLBs.',font=font,fill='#263743')
d.text((580,995),'Front and rear anatomy are inferred from the single reference.',font=font,fill='#263743')
d.text((580,1060),'Static review: REVISE / production HOLD.',font=font,fill='#9c302a')
canvas.save(E/'comparison-five-views.webp',quality=94,method=6)
files=['public/concept/P.webp','art/p-creature/workspaces/P-v7-reference-retopology.blend','public/models/evowild-p/p-canonical-v7.glb','art/p-creature/workspaces/P-v8-layered-anatomy.blend','public/models/evowild-p/p-canonical-v8.glb']
hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
(E/'artifact-sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
provenance=E/'render-provenance.json'
data=json.loads(provenance.read_text())
for d in data:
    d['renderSourcePNG']=d.get('renderSourcePNG',d['image'])
    d['image']=d['image'].replace('.png','.webp')
    d['displayEncoding']='WebP quality 94, no geometry/image retouch'
provenance.write_text(json.dumps(data,indent=2)+'\n')
print('packaged',len(VIEWS),'actual v8 views and common-camera v7 comparisons')

# Neutral material comparison, same camera and lights; geometry is untouched.
canvas=Image.new('RGB',(1650,775),'#e2e7e9');d=ImageDraw.Draw(canvas)
for i,version in enumerate(['v7','v8']):
    im=Image.open(W/f'{version}-clay-FRONT34.png');im.thumbnail((825,675));canvas.paste(im,(i*825,45))
    d.text((i*825+16,12),version+' / neutral material / FRONT34',font=font,fill='#152735')
d.text((16,736),'Actual GLBs, identical lighting and scale. Material override for shape inspection only.',font=font,fill='#263743')
canvas.save(E/'comparison-clay.webp',quality=94,method=6)
