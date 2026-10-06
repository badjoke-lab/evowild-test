#!/usr/bin/env python3
from pathlib import Path
import math
import json
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "pea-hd12-phase-transfer-v1"
CELL = 256
MORPHS = {
    "P": {"layout": (3, 2)},
    "E": {"layout": (3, 2)},
    "A": {"layout": (2, 3)},
}
PHASES = [
    "CONTACT","MID_CP","PUSH","MID_PL",
    "LIFT","MID_LF","FLIGHT","MID_FR",
    "REACH","MID_RL","LAND","MID_LC",
]

def split_sheet(path, cols, rows):
    img = Image.open(path).convert("RGBA")
    fw = img.width // cols
    fh = img.height // rows
    frames = []
    for i in range(6):
        col = i % cols
        row = i // cols
        frames.append(img.crop((col*fw, row*fh, (col+1)*fw, (row+1)*fh)))
    return frames

def split_mf12(path):
    img = Image.open(path).convert("RGBA")
    fw = img.width // 4
    fh = img.height // 3
    return [
        img.crop(((i%4)*fw, (i//4)*fh, (i%4+1)*fw, (i//4+1)*fh))
        for i in range(12)
    ]

def alpha_bbox(img, threshold=10):
    a = img.getchannel("A").point(lambda x: 255 if x > threshold else 0)
    return a.getbbox()

def normalize(img):
    bbox = alpha_bbox(img)
    if not bbox:
        return Image.new("RGBA", (CELL, CELL), (0,0,0,0))
    crop = img.crop(bbox)
    max_w, max_h = 240, 232
    scale = min(max_w/crop.width, max_h/crop.height)
    size = (max(1, round(crop.width*scale)), max(1, round(crop.height*scale)))
    crop = crop.resize(size, Image.Resampling.LANCZOS)
    out = Image.new("RGBA", (CELL, CELL), (0,0,0,0))
    x = (CELL-size[0])//2
    y = 244-size[1]
    out.alpha_composite(crop, (x,y))
    return out

def region_stats(img, front):
    a = img.getchannel("A")
    bbox = a.point(lambda x: 255 if x > 10 else 0).getbbox()
    if not bbox:
        return None
    minx,miny,maxx,maxy=bbox
    w=max(1,maxx-minx); h=max(1,maxy-miny)
    split_y=miny + h*0.54
    split_x=minx + w*0.53
    pts=[]
    pix=a.load()
    for y in range(max(0,int(split_y-8)), min(CELL,maxy)):
        for x in range(max(0,minx), min(CELL,maxx)):
            if pix[x,y] <= 18:
                continue
            if (x >= split_x) == front:
                pts.append((x,y))
    if len(pts)<12:
        return {"cx":split_x,"cy":split_y,"angle":0.0,"bbox":bbox}
    cx=sum(p[0] for p in pts)/len(pts)
    cy=sum(p[1] for p in pts)/len(pts)
    xx=sum((p[0]-cx)**2 for p in pts)/len(pts)
    yy=sum((p[1]-cy)**2 for p in pts)/len(pts)
    xy=sum((p[0]-cx)*(p[1]-cy) for p in pts)/len(pts)
    angle=0.5*math.atan2(2*xy, xx-yy)
    return {"cx":cx,"cy":cy,"angle":angle,"bbox":bbox}

def body_stats(img):
    bbox=alpha_bbox(img)
    if not bbox:
        return {"cx":CELL/2,"cy":CELL/2,"w":1,"h":1}
    minx,miny,maxx,maxy=bbox
    return {"cx":(minx+maxx)/2,"cy":(miny+maxy)/2,"w":maxx-minx,"h":maxy-miny}

def make_masks(src):
    bbox=alpha_bbox(src)
    if not bbox:
        z=Image.new("L",(CELL,CELL),0)
        return z,z,z
    minx,miny,maxx,maxy=bbox
    w=maxx-minx; h=maxy-miny
    split_y=int(miny+h*0.54)
    split_x=int(minx+w*0.53)
    alpha=src.getchannel("A")
    body=Image.new("L",(CELL,CELL),0)
    rear=Image.new("L",(CELL,CELL),0)
    front=Image.new("L",(CELL,CELL),0)
    ap=alpha.load(); bp=body.load(); rp=rear.load(); fp=front.load()
    overlap=14
    for y in range(CELL):
        for x in range(CELL):
            av=ap[x,y]
            if av==0:
                continue
            if y <= split_y+6:
                bp[x,y]=av
            if y >= split_y-overlap:
                if x < split_x:
                    rp[x,y]=av
                else:
                    fp[x,y]=av
    body=body.filter(ImageFilter.GaussianBlur(1.1))
    rear=rear.filter(ImageFilter.GaussianBlur(1.0))
    front=front.filter(ImageFilter.GaussianBlur(1.0))
    return body,rear,front

def masked_layer(src, mask):
    out=Image.new("RGBA",(CELL,CELL),(0,0,0,0))
    out.paste(src,(0,0),mask)
    return out

def transform_layer(layer, dx, dy, angle_deg):
    bbox=alpha_bbox(layer)
    if not bbox:
        return layer
    crop=layer.crop(bbox)
    rotated=crop.rotate(angle_deg, resample=Image.Resampling.BICUBIC, expand=True)
    out=Image.new("RGBA",(CELL,CELL),(0,0,0,0))
    x=round((bbox[0]+bbox[2])/2 - rotated.width/2 + dx)
    y=round((bbox[1]+bbox[3])/2 - rotated.height/2 + dy)
    out.alpha_composite(rotated,(x,y))
    return out

def odd_frame(src_even, donor_even, donor_odd):
    src=normalize(src_even)
    de=normalize(donor_even)
    do=normalize(donor_odd)

    body_mask,rear_mask,front_mask=make_masks(src)
    body=masked_layer(src,body_mask)
    rear=masked_layer(src,rear_mask)
    front=masked_layer(src,front_mask)

    sb=body_stats(src)
    deb=body_stats(de); dob=body_stats(do)
    # Keep artwork stable: donor body translation only, heavily damped.
    body_dx=(dob["cx"]-deb["cx"])*0.18
    body_dy=(dob["cy"]-deb["cy"])*0.18
    body=transform_layer(body,body_dx,body_dy,0.0)

    transformed=[]
    for is_front, layer in [(False,rear),(True,front)]:
        es=region_stats(de,is_front)
        os=region_stats(do,is_front)
        if not es or not os:
            transformed.append(layer)
            continue
        donor_w=max(1,deb["w"]); donor_h=max(1,deb["h"])
        dx=(os["cx"]-es["cx"])/donor_w*sb["w"]
        dy=(os["cy"]-es["cy"])/donor_h*sb["h"]
        dx=max(-22,min(22,dx))
        dy=max(-20,min(20,dy))
        da=math.degrees(os["angle"]-es["angle"])
        while da>90: da-=180
        while da<-90: da+=180
        da=max(-14,min(14,da))*0.72
        transformed.append(transform_layer(layer,dx,dy,da))

    out=Image.new("RGBA",(CELL,CELL),(0,0,0,0))
    # limb layers first; body overlap hides cut seams at roots.
    out.alpha_composite(transformed[0])
    out.alpha_composite(transformed[1])
    out.alpha_composite(body)
    return out

def compose_sheet(frames, path):
    sheet=Image.new("RGBA",(CELL*4,CELL*3),(0,0,0,0))
    for i,frame in enumerate(frames):
        sheet.alpha_composite(frame,((i%4)*CELL,(i//4)*CELL))
    sheet.save(path,"WEBP",lossless=True,method=6)

def review_png(frames,morph):
    canvas=Image.new("RGBA",(CELL*4,CELL*3),(18,22,27,255))
    d=ImageDraw.Draw(canvas)
    for i,frame in enumerate(frames):
        x=(i%4)*CELL; y=(i//4)*CELL
        canvas.alpha_composite(frame,(x,y))
        d.rectangle((x+5,y+5,x+88,y+22),fill=(0,0,0,170))
        d.text((x+8,y+8),PHASES[i],fill=(245,248,250,255))
    canvas.save(OUT/f"{morph.lower()}-hd12-poses.png")

def loop_gif(frames,morph):
    rgb=[]
    for frame in frames:
        bg=Image.new("RGB",(CELL,CELL),(18,22,27))
        bg.paste(frame,mask=frame.getchannel("A"))
        rgb.append(bg)
    rgb[0].save(
        OUT/f"{morph.lower()}-hd12-loop.gif",
        save_all=True, append_images=rgb[1:], duration=68, loop=0, disposal=2
    )

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={
        "method":"piecewise raster phase transfer; no optical-flow, no crossfade",
        "even_frames":"existing high-detail key poses",
        "odd_frames":"preceding high-detail pose with donor-driven front/rear lower-limb affine deltas",
        "morphs":{}
    }
    for morph,cfg in MORPHS.items():
        src=split_sheet(ROOT/f"public/concept/{morph.lower()}-run-sheet.webp",*cfg["layout"])
        donor=split_mf12(ROOT/f"public/concept/{morph.lower()}-run-sheet-mf12-v1.webp")
        frames=[]
        for i in range(12):
            if i%2==0:
                frames.append(normalize(src[i//2]))
            else:
                frames.append(odd_frame(src[i//2],donor[i-1],donor[i]))
        compose_sheet(frames,OUT/f"{morph.lower()}-run-sheet-hd12-phase-v1.webp")
        review_png(frames,morph)
        loop_gif(frames,morph)
        report["morphs"][morph]={"frames":12,"layout":"4x3"}
    (OUT/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("generated P/E/A high-detail 12-frame phase-transfer candidates")

if __name__=="__main__":
    main()
