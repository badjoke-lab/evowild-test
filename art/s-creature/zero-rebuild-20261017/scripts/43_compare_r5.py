"""Reference / R4 / R5 boards from unretouched actual render pixels only."""
import hashlib, json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
ROOT=Path(__file__).resolve().parents[1]
label=sys.argv[1]
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',24)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
sources={};outputs=[]
def read(p):
    sources[str(p.relative_to(ROOT.parent))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return Image.open(p).convert('RGB')
def pic(stage,view):return read(ROOT/'renders'/stage/(view+'.png'))
def panel(c,im,x,y,w,h,title):
    ImageDraw.Draw(c).text((x+12,y+10),title,font=font,fill='#172333')
    im=ImageOps.contain(im,(w-24,h-66));c.paste(im,(x+(w-im.width)//2,y+52+(h-66-im.height)//2))
def save(c,suffix):
    p=ROOT/'comparisons'/(label.upper()+'_'+suffix+'.png');assert not p.exists()
    c.save(p);outputs.append(str(p.relative_to(ROOT)))
ref=read(ROOT.parent/'references/00_s_type_modeling_image_v1.png')
tail={'SIDE':(775,325,1145,660),'FRONT34':(710,305,945,665),
      'REAR34':(720,330,1040,730),'BACK':(490,310,710,700)}
ref_tail={'SIDE':(505,205,754,408),'FRONT34':(1325,231,1435,403),
          'REAR34':(1084,676,1433,848),'BACK':(1015,231,1072,375)}
c=Image.new('RGB',(1800,2180),'#edf1f5')
for row,v in enumerate(tail):
    rtitle='REFERENCE / '+v if v!='REAR34' else 'REFERENCE / TAIL DETAIL (different view)'
    for j,(im,title) in enumerate([(ref.crop(ref_tail[v]),rtitle),
         (pic('revised_r4',v).crop(tail[v]),'R4 / '+v),
         (pic(label,v).crop(tail[v]),label.upper()+' / '+v)]):
        panel(c,im,j*600,row*530,600,530,title)
ImageDraw.Draw(c).text((12,2140),'Actual pixels; fixed R4 cameras and studio. Concept views are not calibrated 3D projections.',font=small,fill='#172333')
save(c,'TAIL_COMPARISON')
views=['SIDE','FRONT','FRONT34','REAR34','BACK']
if all((ROOT/'renders'/label/(v+'.png')).exists() for v in views):
    c=Image.new('RGB',(1800,1000),'#edf1f5')
    for i,v in enumerate(views):panel(c,pic(label,v),i%3*600,i//3*500,600,500,label.upper()+' / '+v)
    panel(c,ref,1200,500,600,500,'CANONICAL REFERENCE');save(c,'FIVE_VIEWS')
    c=Image.new('RGB',(1440,2850),'#edf1f5')
    for i,v in enumerate(views):
        panel(c,pic('revised_r4',v),0,i*570,720,570,'R4 / '+v)
        panel(c,pic(label,v),720,i*570,720,570,'R5 / '+v)
    save(c,'R4_FIVE_VIEW_COMPARISON')
    c=Image.new('RGB',(1800,2040),'#edf1f5')
    crops={'SIDE':(35,70,755,513),'FRONT':(765,86,948,513),
           'FRONT34':(1130,83,1434,513),'BACK':(951,85,1123,513)}
    for i,(v,crop) in enumerate(crops.items()):
        for j,(im,title) in enumerate([(ref.crop(crop),'REFERENCE'),(pic('revised_r4',v),'R4'),(pic(label,v),'R5')]):
            panel(c,im,j*600,i*500,600,500,title+' / '+v)
    ImageDraw.Draw(c).text((12,2008),'Reference pose / projection differs. Full-body R5 remains REVISE.',font=small,fill='#172333')
    save(c,'REFERENCE_R4_COMPARISON')
    c=Image.new('RGB',(920,400),'#edf1f5')
    for j,stage in enumerate(['revised_r4',label]):
        for i,v in enumerate(views):
            c.paste(pic(stage,v).resize((171,128),Image.Resampling.LANCZOS),(i*184,j*190+48))
            ImageDraw.Draw(c).text((i*184+4,j*190+8),('R4' if j==0 else 'R5')+' / '+v,font=small,fill='#172333')
    save(c,'STATIC_128PX')
p=ROOT/'evidence'/('COMPARISON_'+label+'.json');assert not p.exists()
p.write_text(json.dumps({'method':'Unretouched pixels; crop, proportional resize, labels only.',
    'reference_crops':ref_tail,'tail_crops':tail,'source_sha256':sources,'outputs':outputs},indent=2)+'\n')
print('COMPARISONS',outputs)
