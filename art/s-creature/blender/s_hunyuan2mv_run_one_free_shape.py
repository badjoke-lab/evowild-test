"""Attempt exactly one no-token, public ZeroGPU Tencent Hunyuan3D-2mv shape
inference from SOURCE 3 real orthographic S views. Experiment only.
No paid compute and no manual-generated substitution. STOP after this ONE
attempt; failure logs must be preserved rather than hiding the result.
"""
from pathlib import Path
from datetime import datetime,timezone
import os,hashlib,json,traceback,shutil,re,requests
from urllib.parse import urljoin
from gradio_client import Client,handle_file

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/"experiments/canonical-cleanroom-fullbody-20261011/hunyuan2mv-original-source-20261012"
ref=ROOT/"references/00_s_type_modeling_image_v1.png"
SHA="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert hashlib.sha256(ref.read_bytes()).hexdigest()==SHA
assert not os.getenv("HF_TOKEN")
assert not os.getenv("HUGGING_FACE_HUB_TOKEN")
assert (out/"SOURCE_MULTIVIEW_INPUTS_AUDIT.json").exists()
P={
"front":out/"SOURCE_REAL_FRONT_ORTHO_RGBA.png",
"back":out/"SOURCE_REAL_BACK_ORTHO_RGBA.png",
"left":out/"SOURCE_REAL_LEFT_ORTHO_RGBA.png"}
report={
 "source_authority_SHA256":SHA,
 "provider":"tencent/Hunyuan3D-2mv",
 "purpose":"ONE exploratory noncommercial source multiview shape test ONLY",
 "using_public_ZeroGPU_without_HF_TOKEN":True,
 "user_paid_GPU_jobs_created":0,
 "gradio_auth_token_supplied":False,
 "GPU_generation_attempts":0,
 "inputs":{k:f.name for k,f in P.items()},
 "synthetic_unavailable_RIGHT":None,
 "license_commercial_reuse_cleared":False,
 "canonical_shape_approved":False,
 "main_updated":False,
 "time_start":datetime.now(timezone.utc).isoformat(),
 "generated":False,
}
try:
    for f in P.values():assert f.exists(),f
    client=Client("tencent/Hunyuan3D-2mv",verbose=False)
    deps=client.config.get("dependencies",[])
    endpoints=[v for v in deps if v.get("api_name")=="shape_generation"
               and len(v.get("inputs",[]))==13 and len(v.get("outputs",[]))==4]
    assert len(endpoints)==1, "No callable shape-only function."
    args=[
      None, # caption, unused in multiview mode
      None, # single image, unused in multiview mode
      handle_file(str(P["front"])),
      handle_file(str(P["back"])),
      handle_file(str(P["left"])),
      None, # missing source right view MUST NOT be faked
      30,   # diffusion steps
      7.5,  # guidance
      1240, # deterministic seed
      196,  # conservative octree resolution
      False, # input already RGBA masked from actual source
      200000,False
    ]
    report["GPU_generation_attempts"]=1
    print("S_HUNYUAN_MV_ONE_FREE_RUN",{
      "endpoint":"/shape_generation",
      "input_S_authority_sha":SHA,
      "views":["front","back","left"],
      "missing_right":True,
      "model":"tencent/Hunyuan3D-2mv",
      "no_token":True},flush=True)
    result=client.predict(*args,api_name="/shape_generation")
    report["api_return_types"]=[type(x).__name__ for x in result] if isinstance(result,(tuple,list)) else [type(result).__name__]
    if not isinstance(result,(tuple,list)) or len(result)!=4:
        raise RuntimeError("Shape endpoint did not return expected 4 values")
    report["api_result_file_update_shape"]=repr(result[0])[:1600]
    report["api_result_iframe_prefix"]=str(result[1])[:700]
    def scan_file(item):
        if isinstance(item,dict):
            for key in ("path","value","name","url"):
                x=item.get(key)
                if x:
                    ans=scan_file(x)
                    if ans:return ans
            return None
        if isinstance(item,str) and (item.endswith(".glb") or item.endswith(".obj")):
            return item
        return None
    filepath=scan_file(result[0])
    target=out/"HUNYUAN2MV_ORIGINAL_S_THREE_VIEW_SHAPE_ONE_TRIAL_UNAPPROVED.glb"
    if filepath and Path(filepath).is_file():
        shutil.copyfile(filepath,target)
        report["source_mesh_transfer"]="gradio_client_fully_downloaded_local_file"
    else:
        # Public Space returns gr.update(value=server_path) and an iframe
        # pointing at its public STATIC /UUID/white_mesh.html. This alternate
        # retrieval is explicit: never fabricate GLB from a screenshot.
        html=str(result[1])
        m=re.search(r'(/static/[a-zA-Z0-9-]+/white_mesh.html)',html)
        if not m:
            raise RuntimeError("No local GLB and no actual public Space mesh iframe found.")
        url=urljoin("https://tencent-hunyuan3d-2mv.hf.space",m.group(1).replace("white_mesh.html","white_mesh.glb"))
        response=requests.get(url,timeout=60)
        report["public_mesh_url"]=url
        report["public_mesh_http_status"]=response.status_code
        response.raise_for_status()
        if not response.content.startswith(b"glTF"):
            raise RuntimeError("Source is not a GLB binary. HTTP content prefix="+repr(response.content[:60]))
        target.write_bytes(response.content)
        report["source_mesh_transfer"]="public Space /static UUID actual glb, no user token"
    assert 12000<target.stat().st_size<100000000,target.stat().st_size
    report["generated"]=True
    report["candidate_file"]=target.name
    report["candidate_byte_size"]=target.stat().st_size
    report["candidate_sha256"]=hashlib.sha256(target.read_bytes()).hexdigest()
    report["space_generation_metadata"]=result[2] if isinstance(result[2],dict) else repr(result[2])[:1800]
    report["space_seed"]=result[3]
except Exception as e:
    report["error_type"]=type(e).__name__
    report["error_message"]=str(e)[:1500]
    report["traceback_last_8_lines"]=traceback.format_exc().splitlines()[-8:]
    print("S_FREE_MULTIVIEW_EXTERNAL_FAILURE",report["error_type"],report["error_message"],flush=True)
finally:
    report["time_finished"]=datetime.now(timezone.utc).isoformat()
    (out/"ONE_PUBLIC_ZERO_GPU_REAL_SHAPE_ATTEMPT.json").write_text(
          json.dumps(report,indent=2,default=str)+"\n")
    print("S_ONE_FREE_MV_ATTEMPT_RESULT",json.dumps(report,default=str),flush=True)
