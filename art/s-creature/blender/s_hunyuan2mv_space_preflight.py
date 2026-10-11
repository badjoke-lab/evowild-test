"""Network/API preflight ONLY for the publicly hosted FREE ZeroGPU Space.
Does NOT request GPU inference, purchase compute, or send source art.
Outputs auditable endpoint compatibility report.
"""
import json,os,traceback
from pathlib import Path
from datetime import datetime,timezone
from gradio_client import Client
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/"experiments/canonical-cleanroom-fullbody-20261011/hunyuan2mv-original-source-20261012"
out.mkdir(parents=True,exist_ok=True)
r={"public_space":"tencent/Hunyuan3D-2mv","space_zero_gpu_public":True,
   "auth_token_used":False,"GPU_generation_requested":False,
   "paid_job_requested":False,"time_utc":datetime.now(timezone.utc).isoformat(),
   "usable_shape_endpoint_found":False}
try:
    assert not os.environ.get("HF_TOKEN")
    client=Client("tencent/Hunyuan3D-2mv",verbose=False)
    info=client.config
    dep=info.get("dependencies",[])
    endpoints=[]
    for i,d in enumerate(dep):
        if not d.get("backend_fn"):continue
        inputs=d.get("inputs",[])
        outputs=d.get("outputs",[])
        endpoints.append({"index":i,"api_name":d.get("api_name"),
                          "n_inputs":len(inputs),"n_outputs":len(outputs),
                          "api_visibility":d.get("api_visibility")})
    r["api_endpoints"]=endpoints
    r["usable_shape_endpoint_found"]=any(
         v["n_inputs"]==13 and v["n_outputs"]==4 and v["api_name"] not in (None,False)
         for v in endpoints)
    r["public_space_accessed_without_auth"]=True
except Exception as ex:
    r["error_type"]=type(ex).__name__
    r["error_message"]=str(ex)[:1200]
    r["public_space_accessed_without_auth"]=False
file=out/"PUBLIC_FREE_HUNYUAN2MV_API_PREFLIGHT.json"
file.write_text(json.dumps(r,indent=2)+"\n")
print("HUNYUAN2MV_FREE_SPACE_API_PREFLIGHT",json.dumps(r))
