"""Arrange real render pixels, check protected bytes, then inventory delivery."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[3]
try:font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',19)
except OSError:font=ImageFont.load_default()
BG=(234,240,246);INK=(20,35,50)
sources={}
def paste(canvas,path,box):
    source=Image.open(path).convert('RGB');sources[str(path.relative_to(REPO))]=hashlib.sha256(path.read_bytes()).hexdigest()
    thumb=ImageOps.contain(source,(box[2],box[3]),Image.Resampling.LANCZOS)
    canvas.paste(thumb,(box[0]+(box[2]-thumb.width)//2,box[1]+(box[3]-thumb.height)//2))
def save(canvas,name):
    out=ROOT/'comparisons'/name;assert not out.exists();canvas.save(out)
canvas=Image.new('RGB',(1620,690),BG);draw=ImageDraw.Draw(canvas)
for row,label in enumerate(['R6','R7']):
    for col,f in enumerate([1,6,12,18,24]):
        x=10+col*322;y=12+row*325
        draw.text((x,y),label+' / frame '+str(f),font=font,fill=INK)
        paste(canvas,ROOT/'renders'/(label+'_final_hip')/('F%02d_SIDE_HIP.png'%f),(x,y+28,310,270))
draw.text((10,660),'Same cameras / Cycles / saved meshes. R7 = guarded trial B. No image deformation.',font=font,fill=INK)
save(canvas,'R6_R7_SIDE_HIP_FIVE_POSES.png')
canvas=Image.new('RGB',(1300,670),BG);draw=ImageDraw.Draw(canvas)
for row,label in enumerate(['R6','R7']):
    for col,(f,v) in enumerate([(12,'REAR34_HIP'),(24,'REAR34_HIP'),(12,'BACK_HIP'),(24,'BACK_HIP')]):
        x=10+col*322;y=10+row*322
        draw.text((x,y),label+' F'+str(f)+' '+v,font=font,fill=INK)
        paste(canvas,ROOT/'renders'/(label+'_final_hip')/('F%02d_%s.png'%(f,v)),(x,y+28,310,270))
save(canvas,'R6_R7_REAR_BACK_DEFORMATION.png')
canvas=Image.new('RGB',(1620,600),BG);draw=ImageDraw.Draw(canvas)
for row,label in enumerate(['R6','R7']):
    for col,v in enumerate(['SIDE','FRONT','FRONT34','REAR34','BACK']):
        x=10+col*322;y=10+row*285
        draw.text((x,y),label+' '+v,font=font,fill=INK)
        paste(canvas,ROOT/'renders'/(label+'_final_static')/('F01_'+v+'.png'),(x,y+30,310,240))
save(canvas,'R6_R7_STATIC_FIVE_VIEWS.png')
ref=REPO/'art/s-creature/references/00_s_type_modeling_image_v1.png'
canvas=Image.new('RGB',(1500,600),BG);draw=ImageDraw.Draw(canvas)
draw.text((10,10),'Canonical pelvis / thigh (different pose and projection)',font=font,fill=INK)
cropped=Image.open(ref).convert('RGB').crop((400,188,655,414));cropped=ImageOps.contain(cropped,(480,435),Image.Resampling.LANCZOS)
canvas.paste(cropped,(10,60));sources[str(ref.relative_to(REPO))]=hashlib.sha256(ref.read_bytes()).hexdigest()
for col,label in enumerate(['R6','R7'],1):
    draw.text((col*500+10,10),label+' neutral / SIDE_HIP',font=font,fill=INK)
    paste(canvas,ROOT/'renders'/(label+'_final_hip')/'F01_SIDE_HIP.png',(col*500+10,50,480,435))
draw.text((10,530),'R7 preserves R6 silhouette. Canonical angular planes and white/dark boundary still need revision.',font=font,fill=INK)
draw.text((10,560),'Reference comparison is qualitative; images are not registered for a numeric silhouette score.',font=font,fill=INK)
save(canvas,'REFERENCE_R6_R7_PELVIS.png')
canvas=Image.new('RGB',(850,330),BG);draw=ImageDraw.Draw(canvas)
for row,label in enumerate(['R6','R7']):
    for col,v in enumerate(['SIDE','FRONT','FRONT34','REAR34','BACK']):
        x=col*170;y=row*160
        draw.text((x+6,y+2),label+' '+v,font=font,fill=INK)
        paste(canvas,ROOT/'renders'/(label+'_final_static')/('F01_'+v+'.png'),(x,y+28,170,128))
save(canvas,'R6_R7_STATIC_128PX.png')
(ROOT/'evidence/COMPARISON_SOURCES.json').write_text(json.dumps({'method':'Unmodified render pixels, proportional resize, placement and labels only. Reference crop coordinates [400,188,655,414].','sources':sources},indent=2)+'\n')
start=json.loads((ROOT/'evidence/START_PROTECTION.json').read_text());bad=[]
for rel,expected in start['files'].items():
    payload=(REPO/rel).read_bytes()
    if len(payload)!=expected['bytes'] or hashlib.sha256(payload).hexdigest()!=expected['sha256']:bad.append(rel)
assert not bad,bad
checks={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protected_existing_files':len(start['files']),'changed_or_missing':bad,
 'R6_static_protected_copy_equal':(ROOT/'protected/S_ZERO_R6_STATIC_PROTECTED.blend').read_bytes()==(ROOT.parent/'r6-recovery-20261020/S_ZERO_CANDIDATE_REVISED_R6.blend').read_bytes(),
 'R6_rig_protected_copy_equal':(ROOT/'protected/S_ZERO_R6_RIG_PROTECTED.blend').read_bytes()==(ROOT.parent/'r6-recovery-20261020/verification/S_ZERO_R6_HIP_DEFORMATION_RECOVERED_C.blend').read_bytes()}
(ROOT/'evidence/FINAL_PROTECTION.json').write_text(json.dumps(checks,indent=2)+'\n')
manifest=ROOT/'evidence/R7_DELIVERY_MANIFEST.json';assert not manifest.exists()
entries={}
for p in sorted(ROOT.rglob('*')):
    if p.is_file():entries[str(p.relative_to(REPO))]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
manifest.write_text(json.dumps({'branch':'exp/s-fullbody-zero-verify-20261017','transport':'ssh://git@ssh.github.com:443/badjoke-lab/evowild-test.git','files':entries},indent=2)+'\n')
print('DELIVERY_READY',len(entries),'files',sum(v['bytes'] for v in entries.values()),'bytes; protected',len(start['files']))
