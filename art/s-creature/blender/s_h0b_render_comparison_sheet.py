"""Evidence only: original user S PNG + baseline + REJECT H0 + real H0b.
No source image modification, virtual concepts or rerendered fake references.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'art/s-creature/references/00_s_type_modeling_image_v1.png').is_file())
EXP=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011'
OUT=EXP/'h0b-integrated-shoulder-20261012'
R=OUT/'review'
REF=ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
assert hashlib.sha256(REF.read_bytes()).hexdigest()=='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
ref=Image.open(REF).convert('RGB')
assert ref.size==(1448,1086)
fpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def ft(size):return ImageFont.truetype(fpath,size)
def place(img,canvas,x,y,w,h):
    im=img.copy()
    im.thumbnail((w-12,h-12),Image.Resampling.LANCZOS)
    canvas.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2))
views=['SIDE','FRONT','FRONT34','REAR34','BACK']
crops={'SIDE':(18,75,756,512),
       'FRONT':(766,81,949,513),
       'FRONT34':(1127,81,1433,513),
       'BACK':(951,81,1124,513)}
W,H=390,320
canvas=Image.new('RGB',(W*5+195,4*H+60),(237,240,243))
draw=ImageDraw.Draw(canvas)
for col,v in enumerate(views):
    draw.text((205+col*W,6),v,font=ft(20),fill=(19,22,29))
for row,variant in enumerate(('REFERENCE','BASE','H0_REJECT','H0b')):
    draw.text((9,58+row*H),variant,font=ft(18),
              fill=(156,44,42) if variant=='H0_REJECT' else (12,23,39))
    for col,v in enumerate(views):
        if variant=='REFERENCE':
            if v not in crops:continue
            im=ref.crop(crops[v])
        elif variant=='H0_REJECT':
            f=R/f'REJECTED_H0_{v}.png'
            if not f.exists():
                raise RuntimeError(f'Need exact recorded H0 render for 3-way same-camera review: {f}')
            im=Image.open(f).convert('RGB')
        else:
            im=Image.open(R/f'{variant}_{v}.png').convert('RGB')
        place(im,canvas,195+col*W,40+row*H,W,H-12)
canvas.save(R/'H0b_CANONICAL_VS_H0_VS_BASE_5VIEW.jpg',quality=93,subsampling=0)
gray=Image.new('RGB',(W*5+150,3*H+60),(235,238,240))
g=ImageDraw.Draw(gray)
for col,v in enumerate(views):g.text((160+col*W,7),v,font=ft(20),fill=(20,23,28))
for row,variant in enumerate(('BASE','H0b','H0b')):
    if row==2:break
    g.text((8,50+row*H),variant+'_CLAY',font=ft(18),fill=(20,23,29))
    for col,v in enumerate(views):
        im=Image.open(R/f'{variant}_{v}_CLAY.png').convert('RGB')
        place(im,gray,150+col*W,40+row*H,W,H-12)
gray=gray.crop((0,0,gray.width,2*H+45))
gray.save(R/'H0b_BASE_VS_SINGLE_COLOR_5VIEW.jpg',quality=93)
qa=json.loads((OUT/'H0b_REAL_NATIVE_SURFACE_QA.json').read_text())
qa["actual_render_evidence"]="H0b_CANONICAL_VS_H0_VS_BASE_5VIEW.jpg"
qa["original_art_match_requires_visual_review"]=True
(OUT/'H0b_REAL_NATIVE_SURFACE_QA.json').write_text(json.dumps(qa,indent=2)+'\n')
print('H0b_COMPARISON_READY',qa["technical_mesh_gate"],qa["edited_physical_mesh_objects"],qa["additional_mesh_armor_objects"])
