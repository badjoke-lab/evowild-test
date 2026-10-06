#!/usr/bin/env python3
from pathlib import Path
import math
import json
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"artifacts"/"pea-hd12-phase-transfer-v2"
CELL=256
PHASES=[
 "CONTACT","MID_CP","PUSH","MID_PL",
 "LIFT","MID_LF","FLIGHT","MID_FR",
 "REACH","MID_RL","LAND","MID_LC"
]
CFG={
 "P":{"layout":(3,2),"limb_y":0.64,"split_x":0.53,"max_shift":16,"max_angle":8},
 "E":{"layout":(3,2),"limb_y":0.57,"split_x":0.53,"max_shift":18,"max_angle":9},
 "A":{"layout":(2,3),"limb_y":0.64,"split_x":0.52,"max_shift":16,"max_angle":9},
}

def split6(path,cols,rows):
 img=Image.open(path).convert("RGBA")
 fw=img.width//cols; fh=img.height//rows
 return [img.crop(((i%cols)*fw,(i//cols)*fh,(i%cols+1)*fw,(i//cols+1)*fh)) for i in range(6)]

def split12(path):
 img=Image.open(path).convert("RGBA")
 fw=img.width//4; fh=img.height//3
 return [img.crop(((i%4)*fw,(i//4)*fh,(i%4+1)*fw,(i//4+1)*fh)) for i in range(12)]

def bbox(img):
 return img.getchannel("A").point(lambda a:255 if a>10 else 0).getbbox()

def normalize(img):
 b=bbox(img)
 if not b: return Image.new("RGBA",(CELL,CELL),(0,0,0,0))
 crop=img.crop(b)
 scale=min(240/crop.width,232/crop.height)
 size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
 crop=crop.resize(size,Image.Resampling.LANCZOS)
 out=Image.new("RGBA",(CELL,CELL),(0,0,0,0))
 out.alpha_composite(crop,((CELL-size[0])//2,244-size[1]))
 return out

def stats(img,front,cfg):
 a=img.getchannel("A"); b=bbox(img)
 if not b:return None
 minx,miny,maxx,maxy=b; w=maxx-minx; h=maxy-miny
 sy=miny+h*cfg["limb_y"]; sx=minx+w*cfg["split_x"]
 pts=[]; p=a.load()
 for y in range(max(0,int(sy-6)),min(CELL,maxy)):
  for x in range(max(0,minx),min(CELL,maxx)):
   if p[x,y]<=18:continue
   if (x>=sx)==front:pts.append((x,y))
 if len(pts)<8:return {"cx":sx,"cy":sy,"angle":0.0,"w":w,"h":h}
 cx=sum(x for x,y in pts)/len(pts); cy=sum(y for x,y in pts)/len(pts)
 xx=sum((x-cx)**2 for x,y in pts)/len(pts)
 yy=sum((y-cy)**2 for x,y in pts)/len(pts)
 xy=sum((x-cx)*(y-cy) for x,y in pts)/len(pts)
 return {"cx":cx,"cy":cy,"angle":.5*math.atan2(2*xy,xx-yy),"w":w,"h":h}

def limb_masks(src,cfg):
 a=src.getchannel("A"); b=bbox(src)
 zero=Image.new("L",(CELL,CELL),0)
 if not b:return zero,zero,zero,zero
 minx,miny,maxx,maxy=b; w=maxx-minx; h=maxy-miny
 sy=miny+h*cfg["limb_y"]; sx=minx+w*cfg["split_x"]
 # layer masks include a small root overlap; erase masks start lower so torso/root stays intact.
 rear_layer=Image.new("L",(CELL,CELL),0); front_layer=Image.new("L",(CELL,CELL),0)
 rear_erase=Image.new("L",(CELL,CELL),0); front_erase=Image.new("L",(CELL,CELL),0)
 ap=a.load(); rl=rear_layer.load(); fl=front_layer.load(); re=rear_erase.load(); fe=front_erase.load()
 for y in range(CELL):
  for x in range(CELL):
   av=ap[x,y]
   if not av:continue
   front=x>=sx
   if y>=sy-10:
    (fl if front else rl)[x,y]=av
   if y>=sy+7:
    (fe if front else re)[x,y]=av
 rear_layer=rear_layer.filter(ImageFilter.GaussianBlur(.7))
 front_layer=front_layer.filter(ImageFilter.GaussianBlur(.7))
 rear_erase=rear_erase.filter(ImageFilter.GaussianBlur(.9))
 front_erase=front_erase.filter(ImageFilter.GaussianBlur(.9))
 return rear_layer,front_layer,rear_erase,front_erase

def layer(src,mask):
 out=Image.new("RGBA",(CELL,CELL),(0,0,0,0)); out.paste(src,(0,0),mask); return out

def erase(src,mask):
 out=src.copy()
 a=out.getchannel("A")
 inv=ImageChops.invert(mask)
 out.putalpha(ImageChops.multiply(a,inv))
 return out

def transform(lay,dx,dy,angle):
 b=bbox(lay)
 if not b:return lay
 crop=lay.crop(b)
 rot=crop.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
 out=Image.new("RGBA",(CELL,CELL),(0,0,0,0))
 cx=(b[0]+b[2])/2; cy=(b[1]+b[3])/2
 out.alpha_composite(rot,(round(cx-rot.width/2+dx),round(cy-rot.height/2+dy)))
 return out

def delta(de,do,front,cfg,src):
 es=stats(de,front,cfg); os=stats(do,front,cfg); ss=stats(src,front,cfg)
 if not es or not os or not ss:return 0,0,0
 dx=(os["cx"]-es["cx"])/max(1,es["w"])*ss["w"]
 dy=(os["cy"]-es["cy"])/max(1,es["h"])*ss["h"]
 lim=cfg["max_shift"]; dx=max(-lim,min(lim,dx)); dy=max(-lim,min(lim,dy))
 da=math.degrees(os["angle"]-es["angle"])
 while da>90:da-=180
 while da<-90:da+=180
 da=max(-cfg["max_angle"],min(cfg["max_angle"],da*.55))
 return dx,dy,da

def odd(src0,de0,do0,cfg):
 src=normalize(src0); de=normalize(de0); do=normalize(do0)
 rl,fl,re,fe=limb_masks(src,cfg)
 base=erase(erase(src,re),fe)
 rear=layer(src,rl); front=layer(src,fl)
 rdx,rdy,ra=delta(de,do,False,cfg,src)
 fdx,fdy,fa=delta(de,do,True,cfg,src)
 rear=transform(rear,rdx,rdy,ra)
 front=transform(front,fdx,fdy,fa)
 out=Image.new("RGBA",(CELL,CELL),(0,0,0,0))
 out.alpha_composite(base)
 out.alpha_composite(rear)
 out.alpha_composite(front)
 return out

def save_sheet(frames,path):
 sheet=Image.new("RGBA",(CELL*4,CELL*3),(0,0,0,0))
 for i,f in enumerate(frames):sheet.alpha_composite(f,((i%4)*CELL,(i//4)*CELL))
 sheet.save(path,"WEBP",lossless=True,method=6)

def save_review(frames,morph):
 img=Image.new("RGBA",(CELL*4,CELL*3),(18,22,27,255)); d=ImageDraw.Draw(img)
 for i,f in enumerate(frames):
  x=(i%4)*CELL;y=(i//4)*CELL;img.alpha_composite(f,(x,y))
  d.rectangle((x+5,y+5,x+88,y+22),fill=(0,0,0,170));d.text((x+8,y+8),PHASES[i],fill="white")
 img.save(OUT/f"{morph.lower()}-hd12-v2-poses.png")
 rgb=[]
 for f in frames:
  bg=Image.new("RGB",(CELL,CELL),(18,22,27));bg.paste(f,mask=f.getchannel("A"));rgb.append(bg)
 rgb[0].save(OUT/f"{morph.lower()}-hd12-v2-loop.gif",save_all=True,append_images=rgb[1:],duration=68,loop=0,disposal=2)

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 rep={"method":"distal-limb-only phase transfer","optical_flow":False,"crossfade":False,"morphs":{}}
 for morph,cfg in CFG.items():
  src=split6(ROOT/f"public/concept/{morph.lower()}-run-sheet.webp",*cfg["layout"])
  donor=split12(ROOT/f"public/concept/{morph.lower()}-run-sheet-mf12-v1.webp")
  frames=[]
  for i in range(12):
   frames.append(normalize(src[i//2]) if i%2==0 else odd(src[i//2],donor[i-1],donor[i],cfg))
  save_sheet(frames,OUT/f"{morph.lower()}-run-sheet-hd12-phase-v2.webp")
  save_review(frames,morph)
  rep["morphs"][morph]={"frames":12,"layout":"4x3","limb_y":cfg["limb_y"]}
 (OUT/"report.json").write_text(json.dumps(rep,indent=2),encoding="utf-8")
 print("generated P/E/A distal-limb high-detail phase-transfer v2")

if __name__=="__main__":main()
