"""Comparison boards from original pixels only: crop, equal-scale resize, labels.
Usage: python3 55_compare_r6.py revised_r6 (or r6_trial_b).
"""
import hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[1]
label=sys.argv[1];sources={};outputs=[]
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',24)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
def read(p):
    sources[str(p.relative_to(ROOT.parent))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return Image.open(p).convert('RGB')
def pic(stage,view):return read(ROOT/'renders'/stage/(view+'.png'))
def panel(canvas,im,x,y,w,h,title):
    ImageDraw.Draw(canvas).text((x+12,y+10),title,font=font,fill='#172333')
    im=ImageOps.contain(im,(w-24,h-66))
    canvas.paste(im,(x+(w-im.width)//2,y+52+(h-66-im.height)//2))
def save(c,suffix):
    p=ROOT/'comparisons'/(label.upper()+'_'+suffix+'.png');assert not p.exists();c.save(p);outputs.append(str(p.relative_to(ROOT)))
ref=read(ROOT.parent/'references/00_s_type_modeling_image_v1.png')
views=['SIDE','FRONT','FRONT34','REAR34','BACK']
ref_crops={'SIDE':(35,70,755,513),'FRONT':(765,86,948,513),'FRONT34':(1130,83,1434,513),'BACK':(951,85,1123,513)}
hip_crops={'SIDE':(650,320,935,640),'FRONT':(490,290,710,600),
           'FRONT34':(665,310,885,625),'REAR34':(625,325,900,650),'BACK':(445,310,755,640)}
ref_hip={'SIDE':(405,205,646,395),'FRONT':(806,248,913,424),
         'FRONT34':(1280,235,1405,420),'BACK':(979,226,1109,422)}
c=Image.new('RGB',(1800,1040),'#edf1f5')
for i,v in enumerate(views):panel(c,pic(label,v),i%3*600,i//3*520,600,520,'R6 / '+v)
panel(c,ref,1200,520,600,520,'CANONICAL S REFERENCE');save(c,'FIVE_VIEWS')
c=Image.new('RGB',(1800,2660),'#edf1f5')
for i,v in enumerate(views):
    rview=v if v in ref_crops else 'BACK'
    title='REFERENCE / '+rview+(' (no REAR34 concept)' if v=='REAR34' else '')
    panel(c,ref.crop(ref_crops[rview]),0,i*520,600,520,title)
    panel(c,pic('revised_r5',v),600,i*520,600,520,'R5 / '+v)
    panel(c,pic(label,v),1200,i*520,600,520,'R6 / '+v)
ImageDraw.Draw(c).text((12,2620),'Actual pixels. Concept pose/projection differs; no matching REAR34 reference. Overall verdict: REVISE.',font=small,fill='#172333')
save(c,'REFERENCE_R5_COMPARISON')
c=Image.new('RGB',(1800,2660),'#edf1f5')
for i,v in enumerate(views):
    rview=v if v in ref_hip else 'BACK'
    title='REFERENCE / '+rview+(' (context only)' if v=='REAR34' else '')
    if v=='FRONT':title='REFERENCE / FRONT (hip occluded)'
    panel(c,ref.crop(ref_hip[rview]),0,i*520,600,520,title)
    panel(c,pic('revised_r5',v).crop(hip_crops[v]),600,i*520,600,520,'R5 / '+v)
    panel(c,pic(label,v).crop(hip_crops[v]),1200,i*520,600,520,'R6 / '+v)
ImageDraw.Draw(c).text((12,2620),'Crops use identical R5/R6 coordinates. Connected shape improved; facets and deformation still require revision.',font=small,fill='#172333')
save(c,'PELVIS_COMPARISON')
c=Image.new('RGB',(1440,2850),'#edf1f5')
for i,v in enumerate(views):
    panel(c,pic('revised_r5',v),0,i*570,720,570,'R5 / '+v)
    panel(c,pic(label,v),720,i*570,720,570,'R6 / '+v)
save(c,'R5_FIVE_VIEW_COMPARISON')
c=Image.new('RGB',(920,410),'#edf1f5')
for j,stage in enumerate(['revised_r5',label]):
    for i,v in enumerate(views):
        c.paste(pic(stage,v).resize((171,128),Image.Resampling.LANCZOS),(i*184,j*190+48))
        ImageDraw.Draw(c).text((i*184+4,j*190+8),('R5' if j==0 else 'R6')+' / '+v,font=small,fill='#172333')
ImageDraw.Draw(c).text((8,386),'Static 128px canvas; not a PC/mobile runtime or gait test.',font=small,fill='#172333')
save(c,'STATIC_128PX')
test_dir=ROOT/'renders/r6_hip_test_b'
if all((test_dir/(state+'_'+view+'.png')).exists() for state in ['NEUTRAL','NEAR_FORWARD','NEAR_BACK'] for view in ['SIDE','SIDE_HIP','REAR34_HIP','BACK_HIP']):
    c=Image.new('RGB',(1800,2180),'#edf1f5')
    poses=[('NEUTRAL','NEUTRAL / 0, 0 deg'),('NEAR_FORWARD','NEAR +25 / FAR -20 deg'),('NEAR_BACK','NEAR -20 / FAR +25 deg')]
    for j,(state,title) in enumerate(poses):
        for i,view in enumerate(['SIDE','SIDE_HIP','REAR34_HIP','BACK_HIP']):
            panel(c,read(test_dir/(state+'_'+view+'.png')),j*600,i*520,600,520,title+' / '+view.replace('_HIP',''))
    d=ImageDraw.Draw(c)
    d.text((12,2100),'Saved verification armature. Actual deformed mesh; fixed lighting. Ground hidden: no IK/contact test.',font=small,fill='#172333')
    d.text((12,2132),'Motion executes, deformation quality FAILS: maximum edge stretch 2.12x / 2.01x; local compression and tiny faces remain.',font=small,fill='#172333')
    save(c,'HIP_THREE_POSES')
p=ROOT/'evidence'/('COMPARISON_'+label+'.json');assert not p.exists()
p.write_text(json.dumps({'method':'Unretouched actual render pixels; crop, proportional resize and labels only.',
    'reference_hip_crops':ref_hip,'render_hip_crops':hip_crops,'source_sha256':sources,'outputs':outputs},indent=2)+'\n')
print('R6 comparison boards:',outputs)
