"""Evidence layout only: exact reference crops + unretouched Blender renders."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'art/s-creature/references/00_s_type_modeling_image_v1.png').is_file())
OUT=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/h0-body-armor-pass1'
R=OUT/'review';REF=ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
ref=Image.open(REF).convert('RGB');assert ref.size==(1448,1086)
assert REF.stat().st_size==1982782
assert hashlib.sha256(REF.read_bytes()).hexdigest()=='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def font(n,b=False):return ImageFont.truetype(FB if b else F,n)
views=['SIDE','FRONT','FRONT34','REAR34','BACK']
crops={'SIDE':[18,75,756,512],'FRONT':[766,81,949,513],'FRONT34':[1127,81,1433,513],'BACK':[951,81,1124,513]}
def fit(canvas,img,box):
 x,y,w,h=box;im=img.copy();im.thumbnail((w,h),Image.Resampling.LANCZOS)
 canvas.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2))
def drawtext(d,xy,t,n=22,fill='#263449',bold=False):d.text(xy,t,font=font(n,bold),fill=fill,spacing=8)
W=2660;M=24;LH=210;CW=480;GAP=6;ROW=385
sheet=Image.new('RGB',(W,1430),'#edf1f5');d=ImageDraw.Draw(sheet)
drawtext(d,(M,18),'EvoWild Run / S H0 body + armor pass 1',38,bold=True)
drawtext(d,(W-330,18),'REJECT',44,fill='#ac3034',bold=True)
drawtext(d,(M,71),'Sole authority: 00_s_type_modeling_image_v1.png  |  Same-camera BASE vs H0  |  No H1 / no game approval',22)
for j,v in enumerate(views):drawtext(d,(LH+j*(CW+GAP)+12,115),v,25,bold=True)
for row,label in enumerate(['REFERENCE\nExact source\nimage crops','BASE\nOriginal\nHunyuan2MV','H0 / REJECT\nSame base\nLocal edits']):
 y=160+row*(ROW+14)
 drawtext(d,(M,y+20),label,23,bold=True,fill='#ac3034' if row==2 else '#263449')
 for j,v in enumerate(views):
  box=(LH+j*(CW+GAP),y,CW,ROW)
  if row==0:
   if v in crops:fit(sheet,ref.crop(crops[v]),box)
   else:
    drawtext(d,(box[0]+45,y+100),'No REAR34 panel\nin the original sheet.\n\nContinuity check only;\nno invented reference.',21)
  else:fit(sheet,Image.open(R/f"S_{'BASE' if row==1 else 'H0'}_{v}.png").convert('RGB'),box)
drawtext(d,(M,1374),'Reference poses / cameras are not pixel-calibrated. BASE and H0 share orthographic scale, camera, shading and framing.',22)
sheet.save(R/'S_H0_vs_reference.jpg',quality=94,subsampling=0)
# Clay comparison eliminates the white material advantage, no retouch or mesh compositing.
clay=Image.new('RGB',(W,1080),'#edf1f5');d=ImageDraw.Draw(clay)
drawtext(d,(M,18),'H0 geometry check / identical gray material',36,bold=True)
drawtext(d,(W-330,18),'REJECT',44,fill='#ac3034',bold=True)
drawtext(d,(M,72),'Actual Blender renders. Width and plate relief are visible, but shoulder integration / plate flow do not pass.',22)
for j,v in enumerate(views):drawtext(d,(LH+j*(CW+GAP)+12,119),v,25,bold=True)
for row,var in enumerate(['BASE','H0']):
 y=165+row*425
 drawtext(d,(M,y+25),var+('\nREJECT' if row else '\nOriginal'),25,bold=True)
 for j,v in enumerate(views):fit(clay,Image.open(R/f'S_{var}_{v}_CLAY.png').convert('RGB'),(LH+j*(CW+GAP),y,CW,390))
drawtext(d,(M,1015),'No body replacement. Sculpt remains an editable shape key; separate armor surfaces retain true thickness.',22)
clay.save(R/'S_H0_before_after_clay.jpg',quality=94,subsampling=0)
# Larger paired crops retain exactly the same crop on BASE/H0 and keep visible defects.
close=Image.new('RGB',(2080,1600),'#edf1f5');d=ImageDraw.Draw(close)
drawtext(d,(25,15),'H0 visual failure detail / actual render crops / REJECT',34,bold=True,fill='#ac3034')
closecrops={'FRONT':(485,360,947,660),'FRONT34':(480,335,1100,720),'BACK':(495,360,940,670)}
for i,(v,box) in enumerate(closecrops.items()):
 y=90+i*485
 drawtext(d,(20,y+6),v,26,bold=True)
 for j,var in enumerate(['BASE','H0']):
  x=170+j*940
  drawtext(d,(x,y),var+(' / REJECT' if var=='H0' else ' / Original'),25,bold=True)
  fit(close,Image.open(R/f'S_{var}_{v}.png').convert('RGB').crop(box),(x,y+43,910,402))
drawtext(d,(25,1553),'Identical crop for each BASE/H0 pair. Small overlaps, broad cap edges and round shoulder lobes remain visible.',21)
close.save(R/'S_H0_failure_detail.jpg',quality=94,subsampling=0)
(OUT/'H0_COMPARISON_LAYOUT.json').write_text(json.dumps({'reference':str(REF.relative_to(ROOT)),'reference_sha256':hashlib.sha256(REF.read_bytes()).hexdigest(),'reference_crop_boxes_pixels':crops,'paired_detail_crop_boxes_pixels':closecrops,'comparison_method':'Exact image crops + proportional resize for sheet layout only. No painting, generative image edits, or geometry overlays. BASE/H0 camera and full-frame dimensions identical.'},indent=2)+'\n')
print('Saved comparison sheets')
