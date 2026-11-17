#!/usr/bin/env python3
"""Exact triangle/plane intersections -> RGBA horizontal cross sections.
No generated art, mesh edits, raster pose deformation, or renderer in runtime.
Requires Python 3, numpy and Pillow. Input: stacking-poses.mjs integrated skin.
Colors: source has no material/UV/texture/color; preserve neutral glTF white,
with explicitly baked Lambert lighting. Alpha is coverage, zero outside solid.
"""
from pathlib import Path
import argparse,json,math,concurrent.futures,hashlib
import numpy as np
from PIL import Image
P=Path('work/sprite-stacking/poses');O=Path('public/exp-sprite-stacking/assets')
META=json.loads((P/'manifest.json').read_text());N=META['vertices']
IND=np.fromfile(P/'indices.bin',dtype='<u4').reshape(-1,3)
PPU=64;SIZE=256;CENTER=SIZE/2;HEIGHT=math.ceil(META['max'][1]*100)/100
LIGHT=np.array([.4,.85,.35]);LIGHT/=np.linalg.norm(LIGHT)
def srgb(a):return np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055)
def cross(vertices,normals,h):
 tri=vertices[IND];ns=normals[IND];valid=(tri[:,:,1].min(axis=1)<=h)&(tri[:,:,1].max(axis=1)>h)
 tri=tri[valid];ns=ns[valid];seg=[];nn=[]
 # Each non-coplanar triangle has exactly two edge crossings.
 rows=[];vals=[]
 for a,b in [(0,1),(1,2),(2,0)]:
  hit=(tri[:,a,1]<=h)!=(tri[:,b,1]<=h);ids=np.flatnonzero(hit)
  u=(h-tri[ids,a,1])/(tri[ids,b,1]-tri[ids,a,1]);
  rows.extend(ids.tolist());vals.extend(np.concatenate([tri[ids,a]+(tri[ids,b]-tri[ids,a])*u[:,None],ns[ids,a]+(ns[ids,b]-ns[ids,a])*u[:,None]],axis=1))
 if not rows:return np.zeros((1,1,4),dtype=np.uint8),[0,0],0
 order=np.argsort(rows,kind='stable');v=np.array(vals)[order].reshape(-1,2,6)
 q=v[:,:,[0,2]]*PPU+CENTER;ns=v[:,:,3:];img=np.zeros((SIZE,SIZE,4),np.uint8);odd=0
 lo=max(0,int(math.floor(q[:,:,1].min())));hi=min(SIZE,int(math.ceil(q[:,:,1].max())))
 for row in range(lo,hi):
  y=row+.5;hit=(q[:,0,1]<=y)!=(q[:,1,1]<=y)
  a=q[hit,0];b=q[hit,1];na=ns[hit,0];nb=ns[hit,1]
  if not len(a):continue
  u=(y-a[:,1])/(b[:,1]-a[:,1]);xs=a[:,0]+(b[:,0]-a[:,0])*u;norm=na+(nb-na)*u[:,None]
  order=np.argsort(xs);xs=xs[order];norm=norm[order]
  # Shared boundaries may coincide: parity remains correct (zero-width pairs).
  if len(xs)%2:odd+=1
  for j in range(0,len(xs)-1,2):
   left,right=xs[j:j+2];x0=max(0,int(math.floor(left)));x1=min(SIZE,int(math.ceil(right)))
   if x0>=x1:continue
   xx=np.arange(x0,x1)+.5;near=(xx-left>right-xx).astype(int);normal=norm[j+near];normal/=np.maximum(1e-9,np.linalg.norm(normal,axis=1))[:,None]
   brightness=.28+.72*np.maximum(0,normal@LIGHT);rgb=np.round(srgb(brightness)*255).astype(np.uint8)
   coverage=np.clip(np.minimum(xx+.5,right)-np.maximum(xx-.5,left),0,1)
   img[row,x0:x1,:3]=rgb[:,None];img[row,x0:x1,3]=np.maximum(img[row,x0:x1,3],np.round(coverage*255).astype(np.uint8))
 ys,xs=np.nonzero(img[:,:,3]);
 if not len(xs):return np.zeros((1,1,4),np.uint8),[0,0],odd
 x0=max(0,int(xs.min())-1);y0=max(0,int(ys.min())-1);x1=min(SIZE,int(xs.max())+2);y1=min(SIZE,int(ys.max())+2)
 return img[y0:y1,x0:x1],[x0,y0],odd
def generate(frame):
 data=np.fromfile(P/f'{frame:02}.bin',dtype='<f4');v=data[:N*3].reshape(-1,3);norm=data[N*3:].reshape(-1,3);result=[]
 for count in [16,32,64,128]:
  tiles=[];odd=0
  for i in range(count):
   img,origin,bad=cross(v,norm,(i+.5)*HEIGHT/count);tiles.append((img,origin));odd+=bad
  rects=[];x=y=rowh=0;W=1024
  for img,origin in tiles:
   h,w=img.shape[:2]
   if x+w+2>W:x=0;y+=rowh+2;rowh=0
   rects.append([x,y,w,h,*origin]);x+=w+2;rowh=max(rowh,h)
  H=y+rowh;atlas=Image.new('RGBA',(W,H))
  for (img,_),r in zip(tiles,rects):atlas.paste(Image.fromarray(img),(r[0],r[1]))
  dest=O/f'stack-{count}';dest.mkdir(parents=True,exist_ok=True);file=dest/f'{frame:02}.png';atlas.save(file,optimize=True)
  result.append({'layers':count,'frame':frame,'file':str(file.relative_to(O)),'width':W,'height':H,'bytes':file.stat().st_size,'rects':rects,'oddScanlines':odd})
 return result
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=4);parser.add_argument('--frames',type=int,default=48);args=parser.parse_args();O.mkdir(parents=True,exist_ok=True)
 atlases=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
  for result in pool.map(generate,range(args.frames)):
   atlases.extend(result);print('Slices frame',result[0]['frame'],flush=True)
 manifest={k:v for k,v in META.items() if k!='samples'}
 manifest.update({'version':1,'pixelsPerUnit':PPU,'tileSize':SIZE,'height':HEIGHT,'light':LIGHT.tolist(),'ambient':.28,'diffuse':.72,'frames':args.frames,'atlases':atlases,'frameConditions':[12,24,48],'layerConditions':[16,32,64,128],'sampling':'48 integrated phase samples; 12 uses every fourth, 24 every second. No temporal interpolation.','materialNote':'Existing D3-C v2 GLB has no materials, UVs, images or COLOR_0. Neutral default white and coverage alpha preserved. No painted texture invented.','bakedLight':'Creature-local Lambert. World-fixed relighting is not supported by RGBA-only stacks.'})
 (O/'manifest.json').write_text(json.dumps(manifest,separators=(',',':'))+'\n')
 (O/'motion-samples.json').write_text(json.dumps(META['samples'],separators=(',',':'))+'\n')
 print('Done',sum(a['bytes'] for a in atlases),'bytes')
