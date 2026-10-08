#!/usr/bin/env python3
"""One authority-driven S creature generation attempt. No paid GPU or fallback loops."""
import hashlib, io, json, os, shutil, sys, traceback, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"art/s-creature/experiments/authority-rebuild-20261009"
OUT.mkdir(parents=True,exist_ok=True)
EXPECTED_SHA="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
URL="https://raw.githubusercontent.com/badjoke-lab/evowild-test/exp/s-creature-vibe-modeling/art/s-creature/references/00_s_type_modeling_image_v1.png"
INPUT=OUT/"authority-front34-clean-v1.png"
MODEL=OUT/"S-authority-trellis-v1.glb"
REPORT=OUT/"T1_AUTHORITY_GENERATION.json"

report={"status":"STARTED","engine":"microsoft/TRELLIS.2","seed":0,"resolution":1024,
        "input_name":str(INPUT.relative_to(ROOT)),"reference_url":URL,
        "reference_sha256_expected":EXPECTED_SHA,
        "input_crop_xyxy":[1128,78,1442,525],
        "source_constraints":"exact authority illustration crop, no creature repainting",
        "game_ready":False}
try:
    req=urllib.request.Request(URL,headers={"User-Agent":"evowild-github-actions-authority-check"})
    with urllib.request.urlopen(req, timeout=30) as response:
        raw=response.read()
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=EXPECTED_SHA:
        raise RuntimeError("AUTHORITATIVE_REFERENCE_SHA_MISMATCH")
    orig=Image.open(io.BytesIO(raw)).convert("RGB")
    if orig.size!=(1448,1086):raise RuntimeError("AUTHORITY_DIMENSIONS_MISMATCH")
    crop=orig.crop(tuple(report["input_crop_xyxy"]))
    # Remove only the panel's top-left caption; creature is below/right of this area.
    # This is a fixed rectangle, not generated/inpainted content.
    ImageDraw.Draw(crop).rectangle([0,0,116,47],fill=(243,245,245))
    sq=max(crop.width,crop.height)
    image=Image.new("RGB",(sq,sq),(242,244,245))
    image.paste(crop,((sq-crop.width)//2,(sq-crop.height)//2))
    image=image.resize((1024,1024),Image.Resampling.LANCZOS)
    image.save(INPUT,optimize=True)
    report["verified_reference_sha256"]=digest
    report["image_sha256"]=hashlib.sha256(INPUT.read_bytes()).hexdigest()
    report["input_pixel_dims"]=[1024,1024]
    report["input_bytes"]=INPUT.stat().st_size
    report["generator_auth_mode"]="env HF_TOKEN" if os.getenv("HF_TOKEN") else "anonymous"
    # Use the pinned existing repository code; no new generator architecture.
    sys.path.insert(0,str(ROOT/"scripts"))
    import trellis2_pixal3d_generate as g
    g.INPUT=INPUT
    rawdir=OUT/"raw-return"
    rawdir.mkdir(parents=True,exist_ok=True)
    ret=g.run_trellis2(seed=0,resolution='1024',out_dir=rawdir)
    glbs=[Path(x) for x in ret.get("saved_files",[]) if str(x).lower().endswith(".glb") and Path(x).is_file()]
    report["return_paths"]=[str(x) for x in glbs]
    if not glbs:raise RuntimeError("TRELLIS_API_NO_GLB_OUTPUT")
    src=max(glbs,key=lambda p:p.stat().st_size)
    if src.stat().st_size>80_000_000:
        raise RuntimeError("RETURN_GLB_TOO_LARGE_FOR_EXPERIMENT_BRANCH")
    shutil.copy2(src,MODEL)
    report.update(status="MODEL_GENERATED_UNREVIEWED",model=str(MODEL.relative_to(ROOT)),
                  model_bytes=MODEL.stat().st_size,
                  model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest())
except Exception as ex:
    report.update(status="FAILED",error=f"{type(ex).__name__}: {ex}",traceback=traceback.format_exc()[-3000:])
finally:
    REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="traceback"},indent=2))
if report["status"]!="MODEL_GENERATED_UNREVIEWED":
    sys.exit(2)
