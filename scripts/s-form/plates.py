"""Compose unretouched browser captures. A shared scale is used within a column."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
WORK=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/workspace/scratch/s-form')
OUT=ROOT/'public/s-form/evidence'
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def text(d,xy,s,n=17,c='#213344'):d.text(xy,s,font=ImageFont.truetype(font,n),fill=c)
views=[('side','側面',390,(66,70,750,508),1),('front','正面',200,(787,107,930,506),428/395),
 ('rear','背面',200,(978,107,1110,506),428/395),('top','上面',320,(1177,781,1430,851),None),
 ('quarter','斜め45°',310,(1138,87,1430,504),428/413)]
art=Image.open(ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png')
plate=Image.new('RGB',(1570,1300),'#edf1f2');d=ImageDraw.Draw(plate)
text(d,(20,12),'EvoWild Run / S型の立体構造 — 原画を基準に比較',27)
text(d,(20,53),'新旧3Dは列ごとに同じカメラ・倍率。原画は接地線と頭冠高で登録。上面の原画は尾のみ。',16)
for j,label in enumerate(['最上位原画','旧128層原本','旧v4.1表面','新しい立体']):text(d,(12,212+j*290),label,16)
frames=json.loads((OUT/'comparison-camera.json').read_text());x=140
registration=[]
for (key,label,w,crop,refscale),camera in zip(views,frames):
 text(d,(x+8,92),label,19)
 shots=[Image.open(WORK/(prefix+key+'.png')).convert('RGB') for prefix in ['old-stack-','old-surface-','new-']]
 masks=[np.array(im).max(axis=2)>12 for im in shots]
 yy,xx=np.nonzero(np.logical_or.reduce(masks));box=(int(xx.min())-10,int(yy.min())-10,int(xx.max())+11,int(yy.max())+11)
 k=min((w-12)/(box[2]-box[0]),265/(box[3]-box[1]))
 size=(round((box[2]-box[0])*k),round((box[3]-box[1])*k))
 for j,(im,mask) in enumerate(zip(shots,masks)):
  im.putalpha(Image.fromarray((mask*255).astype('uint8')));im=im.crop(box).resize(size,Image.Resampling.LANCZOS)
  y=410+j*290;d.rectangle((x,y,x+w-4,y+280),fill='#dfe6e9')
  plate.paste(im,(x+(w-size[0])//2,y+8+(265-size[1])//2),im)
 ref=art.crop(crop);scale=k*camera['pixels_per_authoring_unit']*(refscale or 1)
 if refscale is None:scale=min((w-12)/ref.width,235/ref.height)
 ref=ref.resize((round(ref.width*scale),round(ref.height*scale)),Image.Resampling.LANCZOS)
 d.rectangle((x,120,x+w-4,400),fill='#dfe6e9')
 if refscale is not None:
  ground=325+camera['aim'][1]*camera['up'][1]*camera['pixels_per_authoring_unit']
  anchor=8+(265-size[1])/2+(ground-box[1])*k
  reference_ground=504 if key=='quarter' else 502
  refy=round(120+anchor-(reference_ground-crop[1])*scale)
 else:refy=128+(265-ref.height)//2
 plate.paste(ref,(x+(w-ref.width)//2,refy))
 if key=='top':text(d,(x+9,365),'尾の部分図・全身上面図なし',13)
 registration.append({'view':key,'shared_capture_crop':box,'shared_scale':k,'reference_scale':scale,'reference_crop':crop,'tail_only':refscale is None})
 x+=w
plate.save(OUT/'five-views.png',optimize=True)
(OUT/'image-registration.json').write_text(json.dumps(registration,indent=2)+'\n')
im=Image.new('RGB',(1200,840),'#edf1f2');d=ImageDraw.Draw(im)
text(d,(20,12),'新形状の四足走行 / 同じカメラで24位相から4点',23)
for j,phase in enumerate([0,6,12,18]):
 p=Image.open(WORK/f'run-{phase}.png').resize((600,390),Image.Resampling.LANCZOS)
 im.paste(p,((j%2)*600,60+(j//2)*390));text(d,((j%2)*600+12,65+(j//2)*390),f'{phase:02d} / 24',16)
im.save(OUT/'gait-four.png',optimize=True)
