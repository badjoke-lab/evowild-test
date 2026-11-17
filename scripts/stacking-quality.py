#!/usr/bin/env python3
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw,ImageFont
W=Path('work/sprite-stacking/quality');O=Path('public/exp-sprite-stacking/evidence');font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
def mask(im):
 a=np.asarray(im.convert('RGB')).astype(int);return (np.abs(a[:,:,0]-a[:,:,1])<=2)&(np.abs(a[:,:,1]-a[:,:,2])<=2)&(a[:,:,0]>50)&(a[:,:,0]<254)
def score(a,b):
 a=mask(a);b=mask(b);return {'approxSilhouetteIoU':float(np.logical_and(a,b).sum()/max(1,np.logical_or(a,b).sum())),'sourceCoverage':float(np.logical_and(a,b).sum()/max(1,a.sum())),'sourcePixels':int(a.sum()),'candidatePixels':int(b.sum())}
rows=[]
for view in ['front','front-quarter','side','rear-quarter','rear']:
 names=['2d','glb','16','32','64','128'];images=[Image.open(W/f'{view}-{n}.png').convert('RGB') for n in names];w,h=images[0].size;sheet=Image.new('RGB',(w*3,(h+46)*2),'#f3f3eb');draw=ImageDraw.Draw(sheet)
 for i,(name,img) in enumerate(zip(names,images)):
  x=i%3*w;y=i//3*(h+46);draw.text((x+16,y+12),f'{view.upper()}  /  '+({'2d':'2D BILLBOARD','glb':'SOURCE GLB'}.get(name,f'{name} HORIZONTAL SLICES')),font=font,fill='#34452b');sheet.paste(img,(x,y+46))
 sheet.save(O/f'comparison-{view}.png',optimize=True)
 for name,img in zip(names,images):
  if name!='glb':rows.append({'view':view,'method':name,**score(images[1],img)})
images=[]
for el in [5,15,35,60,80]:
 pair=[Image.open(W/f'elevation-{el}-{m}.png').convert('RGB') for m in ['glb','canvas']];w,h=pair[0].size;panel=Image.new('RGB',(w*2,h+46),'#f3f3eb');d=ImageDraw.Draw(panel)
 for i,im in enumerate(pair):panel.paste(im,(i*w,46));d.text((i*w+16,12),f'{el} DEG  /  '+['SOURCE GLB','128 HORIZONTAL SLICES'][i],font=font,fill='#34452b')
 panel.save(O/f'elevation-{el}.png',optimize=True);images.append({'elevation':el,**score(*pair)})
(O/'quality.json').write_text(json.dumps({'fiveDirections':rows,'elevationStress':images,'measurement':'Approximate grayscale silhouette mask from same-camera actual rendered images, excluding tinted floor/shadow. Grayscale threshold abs(R-G),abs(G-B)<=2 and 50<R<254. Antialias edges and near-white highlights can be excluded; this is not exact mesh silhouette ground truth. Use side-by-side PNGs for final inspection.','phase':.625,'frames':48,'lighting':'shared creature-local Lambert'},indent=2)+'\n');print('Saved five comparisons, five elevation pairs, approximate silhouette metrics')
