"""Pack actual GLB render evidence and label the limitation unambiguously."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'docs/evidence/p-canonical-3d-v7b-rescue-20261014'
fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(fontfile,24);small=ImageFont.truetype(fontfile,17)
views=['SIDE','FRONT','FRONT34','REAR34','BACK']
sheet=Image.new('RGB',(1650,1050),'#e2e6e9')
d=ImageDraw.Draw(sheet)
for i,view in enumerate(views):
 x=(i%3)*550;y=(i//3)*510
 im=Image.open(E/f'{view}.png');im.thumbnail((550,445))
 sheet.paste(im,(x,y+40));d.text((x+12,y+10),'v7b rescue / '+view,font=font,fill='#192d3d')
d.text((1120,555),'STATIC REVIEW',font=font,fill='#96352d')
d.text((1120,595),'NOT ORIGINAL v8',font=small,fill='#263a48')
d.text((1120,625),'No gait / no adoption',font=small,fill='#263a48')
sheet.save(E/'five-views.webp',quality=94)
cmp=Image.new('RGB',(1650,830),'#e2e6e9')
q=ImageDraw.Draw(cmp)
titles=['Canonical P.webp','v7 (saved source GLB)','v7b RESCUE (new GLB)']
for i,t in enumerate(titles):q.text((12+550*i,18),t,font=font,fill='#182b39')
ref=Image.open(ROOT/'public/concept/P.webp').convert('RGB')
ref.thumbnail((525,425));ref=ref.resize((ref.width*2,ref.height*2),Image.Resampling.NEAREST);ref.thumbnail((525,425))
cmp.paste(ref,(15,115))
old=Image.open(ROOT/'docs/evidence/p-canonical-3d-v7-20261012/FRONT34.webp')
new=Image.open(E/'FRONT34.png')
for i,im in [(1,old),(2,new)]:
 im.thumbnail((535,555));cmp.paste(im,(550*i,70))
q.text((25,640),'Image source: canonical P.webp, unchanged.',font=small,fill='#263a48')
q.text((25,678),'Camera preset reused from v7 Blender source; v7 reference is saved earlier render.',font=small,fill='#263a48')
q.text((25,735),'Candidate review only; NOT the missing Codex v8; static anatomy may remain REVISE.',font=small,fill='#993d2c')
cmp.save(E/'canonical-v7-v7b-comparison.webp',quality=94)
manifest=json.loads((E/'AUTHORING.json').read_text())
manifest['renders']=[v+'.png' for v in views]
manifest['canonicalSHA256']=hashlib.sha256((ROOT/'public/concept/P.webp').read_bytes()).hexdigest()
(E/'VALIDATION.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('PACKAGED_REAL_3D_RESCUE',manifest['bytes'])
