#!/usr/bin/env python3
"""Make actual five-view evidence with the exact S primary design artwork.
Never approves a model or changes any art/geometry.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

REF = Path("art/s-creature/references/00_s_type_modeling_image_v1.png")
SHA256 = "93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
SIZE = (1448, 1086)
BYTES = 1982782
VIEWS = ("side", "front", "front34", "rear34", "back")
ROWS = (
    ("R0 A6 - approved recovery silhouette (not production-ready)",
     "authority-r0-a6", "S_authority_r0_a6_{view}.png",
     "Recovery baseline; rig and anatomy not approved"),
    ("R1 A2 v2 - limited KEEP / overall R1 REVISE",
     "authority-r1-a2-scapula-v2", "S_scapula_v2_{view}.png",
     "Best retained limited shoulder-apex donor; anatomical seam remains"),
    ("R1 A3 v1 - REJECT / DO NOT PROMOTE",
     "authority-r1-a3-sidepatch-v1", "S_R1_A3_sidepatch_v1_{view}.png",
     "Mechanical pass did not fix the visible shoulder-to-foreleg seam"),
)

def run(root: Path, out: Path) -> None:
    ref = root / REF
    raw = ref.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SHA256 or len(raw) != BYTES:
        raise ValueError(f"Authority identity mismatch sha256={digest}, bytes={len(raw)}")
    with Image.open(ref) as im:
        im.load()
        if im.size != SIZE or im.format != "PNG":
            raise ValueError(f"Authority metadata mismatch size={im.size}, format={im.format}")
        authority = im.convert("RGB")
    images = {}
    for name, folder, pattern, _ in ROWS:
        for view in VIEWS:
            p = root / "art/s-creature/output/review" / folder / pattern.format(view=view)
            with Image.open(p) as im:
                im.load()
                if min(im.size) < 100:
                    raise ValueError(f"Suspiciously small render {p}: {im.size}")
                images[(name,view)] = im.convert("RGB")
    width, ref_h, row_h = 1950, 960, 360
    height = 75 + ref_h + row_h * len(ROWS) + 68
    sheet = Image.new("RGB", (width, height), (246,246,246))
    draw = ImageDraw.Draw(sheet)
    dark, muted = (20,25,32), (85,92,100)
    draw.text((30,20), "EVOWILD S - LOCKED HIGHEST AUTHORITY / ACTUAL 3D FIVE-VIEW REVIEW", fill=dark)
    draw.text((30,46), "SHA-256: " + SHA256, fill=muted)
    ref_img = ImageOps.contain(authority, (1850,895), method=Image.Resampling.LANCZOS)
    sheet.paste(ref_img, ((width-ref_img.width)//2,80))
    draw.text((35,75+ref_h-23), "HIGHEST AUTHORITY ARTWORK - exact source verified; only proportionally scaled for layout", fill=muted)
    col_w = (width-60)//5
    for row,(name,folder,pattern,note) in enumerate(ROWS):
        top = 75+ref_h+row*row_h
        draw.text((35,top+8),name,fill=dark)
        draw.text((35,top+31),note,fill=muted)
        for col,view in enumerate(VIEWS):
            im = ImageOps.contain(images[(name,view)],(col_w-15,274),method=Image.Resampling.LANCZOS)
            sheet.paste(im,(30+col*col_w+(col_w-im.width)//2,top+60+(274-im.height)//2))
            draw.text((38+col*col_w,top+340),view.upper(),fill=muted)
    draw.text((35,height-35),"REVIEW EVIDENCE ONLY - S PRODUCTION MODEL: NOT APPROVED - RIGGING/H3 MOTION: BLOCKED",fill=dark)
    out.mkdir(parents=True,exist_ok=True)
    image_path = out / "S_AUTHORITY_vs_R0_R1A2_R1A3_fiveview.jpg"
    sheet.save(image_path,quality=92,optimize=True)
    report = {
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "highest_authority":{"path":REF.as_posix(),"sha256":SHA256,"bytes":BYTES,"dimensions":list(SIZE),"identity_verified":True},
      "source_render_views":list(VIEWS),
      "candidates":{
        "R0_A6":{"review":"RECOVERY_SILHOUETTE_ONLY","source":"S-authority-r0-a5-v2.blend"},
        "R1_A2_V2":{"review":"LOCAL_KEEP_OVERALL_REVISE","source":"S-authority-r1-a2-scapula-v2.blend"},
        "R1_A3_V1":{"review":"REJECT","source":"S-authority-r1-a3-sidepatch-v1.blend"}
      },
      "s_production_approved":False,
      "rigging_allowed":False,
      "h3_motion_allowed":False,
      "next_geometry_gate":"R0_R1_LEGACY_EXPERIMENT_ONLY_REJECTED_R1A3",
      "primary_next_stage":"QEM_CANDIDATE_DEFORMATION_FEASIBILITY_ON_SEPARATE_DONOR_BRANCH",
      "note":"Historical R0/R1 reference comparison only. Later QEM donor selection is evaluated separately; this report does not approve or rank the QEM model. Do not promote old source-lod2.glb."
    }
    (out/"S_AUTHORITY_GATE_STATUS.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"AUTHORITY_OK {digest} / FIVE_VIEW_ROWS={len(ROWS)} / DO_NOT_PROMOTE")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,default=Path("."))
    parser.add_argument("--out",type=Path,default=Path("art/s-creature/output/review/authority-motion-preflight"))
    a=parser.parse_args()
    run(a.repo,a.out)
