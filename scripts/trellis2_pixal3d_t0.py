#!/usr/bin/env python3
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

OUT = pathlib.Path("art/s-creature/experiments/trellis2-pixal3d/t0")
OUT.mkdir(parents=True, exist_ok=True)

SPACES = {
    "trellis2": {
        "repo": "microsoft/TRELLIS.2",
        "agents": "https://huggingface.co/spaces/microsoft/TRELLIS.2/agents.md",
        "api_info": "https://microsoft-trellis-2.hf.space/gradio_api/info",
        "config": "https://microsoft-trellis-2.hf.space/config",
        "targets": ["/preprocess_image", "/image_to_3d", "/extract_glb"],
    },
    "pixal3d": {
        "repo": "TencentARC/Pixal3D",
        "agents": "https://huggingface.co/spaces/TencentARC/Pixal3D/agents.md",
        "api_info": "https://tencentarc-pixal3d.hf.space/gradio_api/info",
        "config": "https://tencentarc-pixal3d.hf.space/config",
        "targets": ["/preprocess", "/generate_3d", "/extract_glb_api"],
    },
}

token = os.environ.get("HF_TOKEN", "").strip()
headers = {
    "User-Agent": "evowild-t0-endpoint-smoke/1.1",
    "Accept": "*/*",
}
if token:
    headers["Authorization"] = f"Bearer {token}"


def get(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return {
                "ok": True,
                "status": r.status,
                "content_type": r.headers.get("content-type"),
                "body": raw.decode("utf-8", errors="replace"),
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"ok": False, "status": e.code, "error": str(e), "body": body}
    except Exception as e:
        return {"ok": False, "status": None, "error": repr(e), "body": ""}


summary = {
    "auth_mode": "HF_TOKEN" if token else "anonymous",
    "spaces": {},
}

for key, spec in SPACES.items():
    item = {"repo": spec["repo"]}
    for endpoint in ("agents", "api_info", "config"):
        result = get(spec[endpoint])
        body = result.pop("body", "")
        item[endpoint] = result

        suffix = "txt" if endpoint == "agents" else "json"
        path = OUT / f"{key}-{endpoint}.{suffix}"
        path.write_text(body, encoding="utf-8")

        if endpoint == "api_info" and result.get("ok"):
            try:
                parsed = json.loads(body)
                named = parsed.get("named_endpoints", {})
                item["api_names"] = sorted(named.keys())
                item["endpoint_schemas"] = {
                    name: named.get(name)
                    for name in spec["targets"]
                    if name in named
                }
            except Exception as exc:
                item["api_parse_error"] = repr(exc)

        if endpoint == "config" and result.get("ok"):
            try:
                parsed = json.loads(body)
                deps = parsed.get("dependencies", [])
                item["config_api_names"] = sorted(
                    {
                        d.get("api_name")
                        for d in deps
                        if isinstance(d, dict) and d.get("api_name")
                    }
                )
                item["target_dependencies"] = [
                    {
                        "id": d.get("id"),
                        "api_name": d.get("api_name"),
                        "queue": d.get("queue"),
                        "inputs": d.get("inputs"),
                        "outputs": d.get("outputs"),
                    }
                    for d in deps
                    if isinstance(d, dict)
                    and d.get("api_name") in {x.lstrip("/") for x in spec["targets"]}
                ]
            except Exception as exc:
                item["config_parse_error"] = repr(exc)

    summary["spaces"][key] = item

(OUT / "summary.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

print(json.dumps(summary, indent=2, ensure_ascii=False))

reachable = [
    v.get("api_info", {}).get("ok", False)
    for v in summary["spaces"].values()
]
sys.exit(0 if any(reachable) else 2)
