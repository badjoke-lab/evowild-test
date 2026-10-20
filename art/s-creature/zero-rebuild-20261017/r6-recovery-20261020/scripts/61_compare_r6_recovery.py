"""Evidence sheets: unretouched source pixels, crops, proportional resizing, text."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[1];PRIOR=ROOT.parent
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',23)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)
sources={};outputs=[]
def read(p):
    sources[str(p.relative_to(PRIOR.parent))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return Image.open(p).convert('RGB')
def panel(c,im,x,y,w,h,title):
    ImageDraw.Draw(c).text((x+12,y+10),title,font=font,fill='#172333')
    im=ImageOps.contain(im,(w-24,h-58))
    c.paste(im,(x+(w-im.width)//2,y+48+(h-58-im.height)//2))
def save(c,name):
    p=ROOT/'comparisons'/(name+'.png');assert not p.exists()
    c.save(p);outputs.append(str(p.relative_to(ROOT)))
def new(view):return read(ROOT/'renders/revised_r6'/(view+'.png'))
def old(view):return read(PRIOR/'renders/revised_r5'/(view+'.png'))
views=['SIDE','FRONT','FRONT34','REAR34','BACK']
ref=read(PRIOR.parent/'references/00_s_type_modeling_image_v1.png')
crops={'SIDE':(35,70,755,513),'FRONT':(765,86,948,513),'FRONT34':(1130,83,1434,513),'BACK':(951,85,1123,513)}
c=Image.new('RGB',(1800,1060),'#edf1f5')
for i,v in enumerate(views):panel(c,new(v),i%3*600,i//3*520,600,520,'RECOVERED R6 / '+v)
panel(c,ref,1200,520,600,520,'CANONICAL S REFERENCE')
save(c,'R6_RECOVERED_FIVE_VIEWS')
c=Image.new('RGB',(1800,2660),'#edf1f5')
for i,v in enumerate(views):
    rv=v if v in crops else 'BACK'
    panel(c,ref.crop(crops[rv]),0,i*520,600,520,'REFERENCE / '+rv+(' (context)' if v=='REAR34' else ''))
    panel(c,old(v),600,i*520,600,520,'R5 / '+v)
    panel(c,new(v),1200,i*520,600,520,'RECOVERED R6 / '+v)
ImageDraw.Draw(c).text((12,2620),'Actual pixels. Concept pose/projection differs; no matching REAR34 concept. Overall: REVISE.',font=small,fill='#172333')
save(c,'REFERENCE_R5_R6_FIVE_VIEW_COMPARISON')
poses=[('NEUTRAL','0 / 0 deg'),('NEAR_FORWARD','NEAR +25 / FAR -20 deg'),('NEAR_BACK','NEAR -20 / FAR +25 deg')]
for view in ['SIDE','SIDE_HIP','REAR34_HIP','BACK_HIP']:
    c=Image.new('RGB',(1800,1150),'#edf1f5')
    for i,(state,title) in enumerate(poses):
        before=read(PRIOR/'renders/r6_hip_test_b'/(state+'_'+view+'.png'))
        after=read(ROOT/'renders/hip_recovered_c'/(state+'_'+view+'.png'))
        panel(c,before,i*600,0,600,520,'BEFORE B / '+title)
        panel(c,after,i*600,520,600,520,'AFTER C / '+title)
    d=ImageDraw.Draw(c)
    d.text((12,1052),view+' | Same cameras, lighting, angles and samples. Actual saved armature renders; no image deformation.',font=small,fill='#172333')
    d.text((12,1082),'Max edge stretch: 2.1217 -> 1.4349 forward; 2.0076 -> 1.3832 back. Area <35%: 1 -> 0 (native tessellation).',font=small,fill='#172333')
    d.text((12,1112),'Residual stretch/compression remains. REVISE; no knee/hock articulation, IK, foot contact, gait or runtime proof.',font=small,fill='#172333')
    save(c,'HIP_BEFORE_AFTER_'+view)
c=Image.new('RGB',(920,410),'#edf1f5')
for j,fn in enumerate([old,new]):
    for i,v in enumerate(views):
        c.paste(fn(v).resize((171,128),Image.Resampling.LANCZOS),(i*184,j*190+48))
        ImageDraw.Draw(c).text((i*184+4,j*190+8),('R5' if j==0 else 'R6')+' / '+v,font=small,fill='#172333')
ImageDraw.Draw(c).text((8,386),'Static 128px canvas. Not a race runtime or gait test.',font=small,fill='#172333')
save(c,'R6_STATIC_128PX')
p=ROOT/'evidence/COMPARISON_SOURCES.json';assert not p.exists()
p.write_text(json.dumps({'method':__doc__,'source_sha256':sources,'outputs':outputs},indent=2)+'\n')
print('Comparison sheets saved:',outputs)
