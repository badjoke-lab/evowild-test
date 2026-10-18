"""Evidence layout of real render pixels; crop/contain/label only, no retouching."""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
LABEL = sys.argv[1]
VIEWS = ['SIDE','FRONT','FRONT34','REAR34','BACK']
sources = {}
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',24)
small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)


def read(path):
    sources[str(path.relative_to(ROOT.parent))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return Image.open(path).convert('RGB')


def render(stage,view):
    return read(ROOT/'renders'/stage/(view+'.png'))


def panel(canvas,picture,x,y,w,h,label):
    ImageDraw.Draw(canvas).text((x+12,y+8),label,font=font,fill='#162435')
    im=ImageOps.contain(picture,(w-12,h-42))
    canvas.paste(im,(x+(w-im.width)//2,y+38+(h-42-im.height)//2))


def save(canvas,name):
    path=ROOT/'comparisons'/name
    assert not path.exists()
    canvas.save(path)
    print(path)


ref=read(ROOT.parent/'references/00_s_type_modeling_image_v1.png')
crops={'SIDE':(30,72,755,514),'FRONT':(765,86,948,513),'FRONT34':(1130,83,1434,513)}
title=LABEL.upper().replace('_',' ')
canvas=Image.new('RGB',(1800,1530),'#edf1f5')
for row,(view,crop) in enumerate(crops.items()):
    panel(canvas,ref.crop(crop),0,row*500,600,500,'REFERENCE / '+view)
    panel(canvas,render('revised_r1',view),600,row*500,600,500,'R1 / '+view)
    panel(canvas,render(LABEL,view),1200,row*500,600,500,title+' / '+view)
ImageDraw.Draw(canvas).text((12,1507),'Real Blender renders. Reference crops are illustrative; reference pose/projection is not exactly registered.',font=small,fill='#162435')
save(canvas,LABEL.upper()+'_REFERENCE_R1_COMPARISON.png')

canvas=Image.new('RGB',(1800,1120),'#edf1f5')
regions=[('SIDE',(335,315,605,570),'SHOULDER / CHEST / ARM'),
         ('FRONT34',(390,290,675,560),'SHOULDER / CHEST / ARM'),
         ('FRONT',(500,60,700,360),'FRONTAL CROWN')]
for col,(view,crop,label) in enumerate(regions):
    panel(canvas,render('revised_r1',view).crop(crop),col*600,0,600,560,'R1 / '+label)
    panel(canvas,render(LABEL,view).crop(crop),col*600,560,600,560,title+' / '+label)
save(canvas,LABEL.upper()+'_DETAILS.png')

if all((ROOT/'renders'/LABEL/(v+'.png')).exists() for v in VIEWS):
    canvas=Image.new('RGB',(1800,1000),'#edf1f5')
    for i,v in enumerate(VIEWS):
        panel(canvas,render(LABEL,v),i%3*600,i//3*500,600,500,title+' / '+v)
    panel(canvas,ref,1200,500,600,500,'CANONICAL MODELING REFERENCE')
    save(canvas,LABEL.upper()+'_FIVE_VIEWS.png')
    canvas=Image.new('RGB',(1440,2850),'#edf1f5')
    for i,v in enumerate(VIEWS):
        panel(canvas,render('revised_r1',v),0,i*570,720,570,'R1 / '+v)
        panel(canvas,render(LABEL,v),720,i*570,720,570,title+' / '+v)
    save(canvas,LABEL.upper()+'_R1_FIVE_VIEW_COMPARISON.png')
(ROOT/'evidence'/('COMPARISON_'+LABEL+'.json')).write_text(json.dumps({
    'method':'Unretouched render pixels, reference crops, uniform resizing and labels only.',
    'reference_crops':crops,'detail_crops':regions,'source_sha256':sources},indent=2)+'\n')
