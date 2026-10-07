#!/usr/bin/env python3
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "public" / "concept" / "p-run-sheet.webp"
DONOR = ROOT / "art" / "2p5d" / "motion-donors" / "p-mf12-v1.webp"
OUT = ROOT / "artifacts" / "p-mf12-flow-transfer-v2"
CELL = 256

def split_sheet(path, cols, rows, count):
    img = Image.open(path).convert("RGBA")
    fw = img.width // cols
    fh = img.height // rows
    return [
        img.crop(((i % cols) * fw, (i // cols) * fh, (i % cols + 1) * fw, (i // cols + 1) * fh)).resize((CELL, CELL), Image.Resampling.LANCZOS)
        for i in range(count)
    ]

def alpha_bbox(arr):
    alpha = arr[..., 3]
    ys, xs = np.where(alpha > 12)
    if len(xs) == 0:
        return (0, 0, CELL, CELL)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)

def premul_gray(arr):
    rgb = arr[..., :3].astype(np.float32)
    a = arr[..., 3:4].astype(np.float32) / 255.0
    premul = rgb * a
    gray = cv2.cvtColor(premul.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    return np.maximum(gray, (arr[..., 3].astype(np.float32) * 0.60).astype(np.uint8))

def dense_flow(a, b):
    flow = cv2.calcOpticalFlowFarneback(
        premul_gray(a), premul_gray(b), None,
        0.5, 5, 25, 5, 7, 1.5, 0
    )
    return cv2.GaussianBlur(flow, (0,0), 2.0)

def sample_bilinear(field, x, y):
    h, w = field.shape[:2]
    x = np.clip(x, 0, w - 1.001)
    y = np.clip(y, 0, h - 1.001)
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    x1 = np.minimum(x0 + 1, w - 1)
    y1 = np.minimum(y0 + 1, h - 1)
    wx = (x - x0)[..., None]
    wy = (y - y0)[..., None]
    a = field[y0, x0]; b = field[y0, x1]
    c = field[y1, x0]; d = field[y1, x1]
    return a*(1-wx)*(1-wy)+b*wx*(1-wy)+c*(1-wx)*wy+d*wx*wy

def smoothstep(edge0, edge1, x):
    t = np.clip((x-edge0)/max(1e-6,edge1-edge0),0.0,1.0)
    return t*t*(3.0-2.0*t)

def donor_flow_in_source_space(source_arr, donor_a, donor_mid):
    da = np.ascontiguousarray(np.array(donor_a,dtype=np.uint8)[:, ::-1])
    dm = np.ascontiguousarray(np.array(donor_mid,dtype=np.uint8)[:, ::-1])
    flow = dense_flow(da, dm)

    sx0,sy0,sx1,sy1 = alpha_bbox(source_arr)
    dx0,dy0,dx1,dy1 = alpha_bbox(da)
    sw=max(1,sx1-sx0); sh=max(1,sy1-sy0)
    dw=max(1,dx1-dx0); dh=max(1,dy1-dy0)

    yy,xx=np.mgrid[0:CELL,0:CELL].astype(np.float32)
    donor_x=dx0+(xx-sx0)/sw*dw
    donor_y=dy0+(yy-sy0)/sh*dh
    sampled=sample_bilinear(flow,donor_x,donor_y)
    return (
        sampled[...,0]*(sw/dw),
        sampled[...,1]*(sh/dh),
        (sx0,sy0,sx1,sy1),
    )

def warp_hybrid(source_img, next_img, donor_even, donor_mid):
    src=np.array(source_img,dtype=np.uint8)
    nxt=np.array(next_img,dtype=np.uint8)

    bridge=dense_flow(src,nxt)
    donor_x,donor_y,bbox=donor_flow_in_source_space(src,donor_even,donor_mid)
    sx0,sy0,sx1,sy1=bbox
    sh=max(1,sy1-sy0); sw=max(1,sx1-sx0)

    yy,xx=np.mgrid[0:CELL,0:CELL].astype(np.float32)
    rel_y=(yy-sy0)/sh
    rel_x=(xx-sx0)/sw
    lower=smoothstep(0.42,0.80,rel_y)

    # Bridge exactly between the two already-approved production keyframes.
    # Motion donor contributes only the local phase bias; it does not replace
    # or redraw the P artwork.
    bridge_scale=0.43+0.10*lower
    donor_scale=0.10+0.16*lower

    # Keep head/crest identity and tail silhouette stable.
    head_damp=1.0-0.42*smoothstep(0.79,0.96,rel_x)*(1.0-smoothstep(0.52,0.88,rel_y))
    tail_damp=0.82+0.18*smoothstep(0.10,0.28,rel_x)
    damp=np.clip(head_damp*tail_damp,0.52,1.0)

    fx=(bridge[...,0]*bridge_scale + donor_x*donor_scale)*damp
    fy=(bridge[...,1]*bridge_scale + donor_y*donor_scale)*damp

    alpha=src[...,3].astype(np.float32)/255.0
    local=0.35+0.65*smoothstep(0.01,0.28,alpha)
    fx*=local; fy*=local

    fx=np.clip(cv2.GaussianBlur(fx,(0,0),1.0),-28.0,28.0)
    fy=np.clip(cv2.GaussianBlur(fy,(0,0),1.0),-24.0,24.0)

    map_x=(xx-fx).astype(np.float32)
    map_y=(yy-fy).astype(np.float32)
    warped=cv2.remap(
        src,map_x,map_y,
        interpolation=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0,0,0,0)
    )
    warped[warped[...,3]<3,:3]=0
    return Image.fromarray(warped,"RGBA"),{
        "max_dx":float(np.max(np.abs(fx))),
        "max_dy":float(np.max(np.abs(fy))),
        "bridge_mean":float(np.mean(np.hypot(bridge[...,0],bridge[...,1]))),
        "donor_mean":float(np.mean(np.hypot(donor_x,donor_y))),
    }

def silhouette_metrics(a,b):
    aa=np.array(a)[...,3]>24; bb=np.array(b)[...,3]>24
    inter=np.logical_and(aa,bb).sum(); union=np.logical_or(aa,bb).sum()
    iou=float(inter/union) if union else 1.0
    def centroid(m):
        ys,xs=np.where(m)
        if not len(xs): return (0.0,0.0)
        return (float(xs.mean()),float(ys.mean()))
    ca=centroid(aa); cb=centroid(bb)
    shift=float(((ca[0]-cb[0])**2+(ca[1]-cb[1])**2)**0.5)
    return {"iou":iou,"centroid_shift":shift}

def make_review(frames):
    canvas=Image.new("RGBA",(CELL*4,CELL*3),(18,22,27,255))
    draw=ImageDraw.Draw(canvas)
    names=["CONTACT","MID_CP","PUSH","MID_PL","LIFT","MID_LF","FLIGHT","MID_FR","REACH","MID_RL","LAND","MID_LC"]
    for i,frame in enumerate(frames):
        x=(i%4)*CELL; y=(i//4)*CELL
        canvas.alpha_composite(frame,(x,y))
        draw.rectangle((x+5,y+5,x+78,y+21),fill=(0,0,0,165))
        draw.text((x+8,y+8),names[i],fill=(245,248,250,255))
    canvas.save(OUT/"p-mf12-flow-transfer-v2-review.png")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=split_sheet(SOURCE,3,2,6)
    donor=split_sheet(DONOR,4,3,12)
    frames=[]; metrics=[]
    for i in range(12):
        if i%2==0:
            frame=source[i//2].copy()
            metric={"kind":"exact-production-keyframe"}
        else:
            src_index=i//2
            next_index=(src_index+1)%6
            frame,metric=warp_hybrid(
                source[src_index],
                source[next_index],
                donor[i-1],
                donor[i],
            )
            metric["kind"]="production-bridge-plus-existing-mf12-bias"
        metric["frame"]=i
        frames.append(frame)
        metrics.append(metric)

    sheet=Image.new("RGBA",(CELL*4,CELL*3),(0,0,0,0))
    for i,frame in enumerate(frames):
        sheet.alpha_composite(frame,((i%4)*CELL,(i//4)*CELL))
    candidate=OUT/"p-run-sheet-mf12-flow-transfer-v2.webp"
    sheet.save(candidate,"WEBP",lossless=True,method=6)
    public=ROOT/"public"/"concept"/"p-run-sheet-mf12-flow-transfer-v2.webp"
    sheet.save(public,"WEBP",lossless=True,method=6)

    make_review(frames)

    gif=[]
    for frame in frames:
        bg=Image.new("RGB",(CELL,CELL),(18,22,27))
        bg.paste(frame,mask=frame.getchannel("A"))
        gif.append(bg)
    gif[0].save(
        OUT/"p-mf12-flow-transfer-v2-loop.gif",
        save_all=True,append_images=gif[1:],
        duration=72,loop=0,disposal=2
    )

    candidate_steps=[silhouette_metrics(frames[i],frames[(i+1)%12]) for i in range(12)]
    original_indices=[0,2,4,6,8,10]
    original_steps=[
        silhouette_metrics(frames[original_indices[i]],frames[original_indices[(i+1)%6]])
        for i in range(6)
    ]
    report={
        "appearance_source":"public/concept/p-run-sheet.webp",
        "motion_source":"art/2p5d/motion-donors/p-mf12-v1.webp",
        "new_motion_created":False,
        "frame_blending":False,
        "production_modified":False,
        "method":"one-sided production-pixel warp; bridge between exact production keyframes with existing mf12 local phase bias",
        "candidate_mean_iou":float(np.mean([m["iou"] for m in candidate_steps])),
        "candidate_mean_centroid_shift":float(np.mean([m["centroid_shift"] for m in candidate_steps])),
        "candidate_max_centroid_shift":float(np.max([m["centroid_shift"] for m in candidate_steps])),
        "original_mean_iou":float(np.mean([m["iou"] for m in original_steps])),
        "original_mean_centroid_shift":float(np.mean([m["centroid_shift"] for m in original_steps])),
        "original_max_centroid_shift":float(np.max([m["centroid_shift"] for m in original_steps])),
        "frames":metrics,
        "candidate_steps":candidate_steps,
        "original_steps":original_steps,
    }
    (OUT/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
