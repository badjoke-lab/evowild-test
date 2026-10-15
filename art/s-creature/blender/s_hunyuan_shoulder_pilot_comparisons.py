"""Compose existing real renders; never generate or retouch model imagery."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[3]
STATION=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012'
OUT=STATION/'review-v5-shoulder-structure-pilot'
reference=Image.open(ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png')
def paste(canvas,image,x,y,w,h):
    scale=min(w/image.width,h/image.height)
    image=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.LANCZOS)
    canvas.paste(image,(x+(w-image.width)//2,y+(h-image.height)//2))
rows=[('SIDE',(240,180,400,355),(330,185,730,620)),('FRONT',(803,233,918,361),(270,185,735,590)),('FRONT34',(1210,226,1312,370),(365,200,720,625))]
for version,filename in [('RIGHT_FINAL','CANONICAL_STAGE1_RIGHT_FINAL.jpg'),('LAYER_PILOT','CANONICAL_STAGE1_LAYER_PILOT.jpg')]:
    canvas=Image.new('RGB',(1800,1500),'#171d24');d=ImageDraw.Draw(canvas)
    for row,(tag,box,modelbox) in enumerate(rows):
        for col,label in enumerate(['CANONICAL','STAGE1_MATCHED',version]):
            im=reference.crop(box) if col==0 else Image.open(OUT/(label+'_DETAIL_'+tag+'.png')).crop(modelbox)
            paste(canvas,im,col*600+10,row*500+40,580,450)
            d.text((col*600+15,row*500+12),tag+' / '+label,fill='white')
    canvas.save(OUT/filename,quality=95)
tags=['SIDE','FRONT','FRONT34','REAR34','BACK']
boxes={'SIDE':(18,78,758,516),'FRONT':(764,78,948,516),'FRONT34':(1128,78,1432,516),'BACK':(951,78,1124,516)}
canvas=Image.new('RGB',(2000,1080),'#171d24');d=ImageDraw.Draw(canvas)
for col,tag in enumerate(tags):
    d.text((col*400+10,10),tag,fill='white')
    if tag in boxes:paste(canvas,reference.crop(boxes[tag]),col*400+5,40,390,300)
    else:d.text((col*400+10,150),'3D coherence view; no source rear34',fill='white')
    for row,version in enumerate(['V5_STAGE1','LAYER_PILOT'],1):
        path=(STATION/'review-v5' if row==1 else OUT)/(version+'_'+tag+'.png')
        paste(canvas,Image.open(path),col*400+5,row*355+30,390,310)
        d.text((col*400+10,row*355+10),version,fill='white')
canvas.save(OUT/'CANONICAL_STAGE1_LAYER_FIVE_VIEWS.jpg',quality=94)
# Derived screenshot previews retain the complete Blender window. Originals
# remain alongside them locally. Hashes preserve provenance of the raw capture.
evidence=OUT/'viewport-evidence';evidence.mkdir(exist_ok=True)
manifest={}
for path in sorted(OUT.glob('*_SCREEN_*.png')):
    im=Image.open(path).convert('RGB');im.thumbnail((1800,1200),Image.Resampling.LANCZOS)
    dest=evidence/(path.stem+'.jpg');im.save(dest,quality=91)
    manifest[path.name]={'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'preview':str(dest.relative_to(OUT)),'preview_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
(OUT/'VIEWPORT_CAPTURE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
projections=json.loads((OUT/'LANDMARK_SCREEN_PROJECTIONS.json').read_text())
try:font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',22)
except OSError:font=ImageFont.load_default()
for tag,info in projections.items():
    im=Image.open(OUT/info['source_capture']).convert('RGB');draw=ImageDraw.Draw(im)
    for label,item in info['landmarks'].items():
        if label not in ['superior_shoulder','posterior_ridge','pectoral_boundary','upper_arm']:continue
        x,y=item['pixel'];draw.ellipse((x-10,y-10,x+10,y+10),outline='#ff624a',width=4)
        text=label+' / v'+str(item['source_vertex'])
        box=draw.textbbox((x+15,y-25),text,font=font);draw.rectangle(box,fill='#171d24');draw.text((x+15,y-25),text,font=font,fill='#ffcf70')
    im.thumbnail((1800,1200),Image.Resampling.LANCZOS);im.save(OUT/('STAGE1_LANDMARKS_'+tag+'.jpg'),quality=94)
print('Comparisons and',len(manifest),'real viewport previews written')
