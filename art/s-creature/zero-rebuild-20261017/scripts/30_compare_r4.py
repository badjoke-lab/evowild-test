"""Comparison boards from actual PNG pixels; crops and proportional layout only."""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT=Path(__file__).resolve().parents[1]
LABEL=sys.argv[1]
VIEWS=['SIDE','FRONT','FRONT34','REAR34','BACK']
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
sources={};outputs=[]

def read(path):
    sources[str(path.relative_to(ROOT.parent))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return Image.open(path).convert('RGB')

def render(stage,v):
    return read(ROOT/'renders'/stage/(v+'.png'))

def panel(canvas,pic,x,y,w,h,label):
    ImageDraw.Draw(canvas).text((x+12,y+10),label,font=font,fill='#172333')
    im=ImageOps.contain(pic,(w-20,h-50))
    canvas.paste(im,(x+(w-im.width)//2,y+44+(h-50-im.height)//2))

def save(canvas,suffix):
    path=ROOT/'comparisons'/(LABEL.upper()+'_'+suffix+'.png')
    assert not path.exists(),path
    canvas.save(path);outputs.append(str(path.relative_to(ROOT)))

ref=read(ROOT.parent/'references/00_s_type_modeling_image_v1.png')
ref_crops={'SIDE':(35,70,755,513),'FRONT':(765,86,948,513),'FRONT34':(1130,83,1434,513)}
close={'SIDE':((50,70,400,255),(70,100,600,365)),
       'FRONT':((817,103,906,250),(525,30,675,380)),
       'FRONT34':((1140,85,1300,255),(280,35,700,380))}
title=LABEL.upper().replace('_',' ')
canvas=Image.new('RGB',(1800,1530),'#edf1f5')
for i,(v,crop) in enumerate(ref_crops.items()):
    for j,(pic,label) in enumerate([(ref.crop(crop),'REFERENCE'),(render('revised_r3',v),'R3'),(render(LABEL,v),title)]):
        panel(canvas,pic,j*600,i*500,600,500,label+' / '+v)
ImageDraw.Draw(canvas).text((12,1507),'Actual Blender renders; fixed R3 cameras and studio. Reference pose/projection differs.',font=small,fill='#172333')
save(canvas,'REFERENCE_R3_COMPARISON')
canvas=Image.new('RGB',(1800,1530),'#edf1f5')
for i,(v,(a,b)) in enumerate(close.items()):
    for j,(pic,label) in enumerate([(ref.crop(a),'REFERENCE'),(render('revised_r3',v).crop(b),'R3'),(render(LABEL,v).crop(b),title)]):
        panel(canvas,pic,j*600,i*500,600,500,label+' / '+v+' CROWN')
ImageDraw.Draw(canvas).text((12,1507),'Unretouched source pixels; proportional crop enlargement only. No generated imagery.',font=small,fill='#172333')
save(canvas,'CROWN_COMPARISON')
if all((ROOT/'renders'/LABEL/(v+'.png')).exists() for v in VIEWS):
    canvas=Image.new('RGB',(1800,1000),'#edf1f5')
    for i,v in enumerate(VIEWS):
        panel(canvas,render(LABEL,v),i%3*600,i//3*500,600,500,title+' / '+v)
    panel(canvas,ref,1200,500,600,500,'CANONICAL REFERENCE')
    save(canvas,'FIVE_VIEWS')
    canvas=Image.new('RGB',(1440,2850),'#edf1f5')
    for i,v in enumerate(VIEWS):
        panel(canvas,render('revised_r3',v),0,i*570,720,570,'R3 / '+v)
        panel(canvas,render(LABEL,v),720,i*570,720,570,title+' / '+v)
    save(canvas,'R3_FIVE_VIEW_COMPARISON')
    canvas=Image.new('RGB',(900,400),'#edf1f5')
    for row,stage in enumerate(['revised_r3',LABEL]):
        for i,v in enumerate(VIEWS):
            canvas.paste(render(stage,v).resize((171,128),Image.Resampling.LANCZOS),(i*180,row*190+48))
            ImageDraw.Draw(canvas).text((i*180+4,row*190+8),('R3' if row==0 else 'R4')+' / '+v,font=small,fill='#172333')
    save(canvas,'STATIC_128PX')
out=ROOT/'evidence'/('COMPARISON_'+LABEL+'.json');assert not out.exists()
out.write_text(json.dumps({'method':'Actual unretouched renders; crop, proportional resize, labels only.',
    'reference_crops':ref_crops,'close_crops':close,'source_sha256':sources,'outputs':outputs},indent=2)+'\n')
print('COMPARISONS',outputs)
