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
    },
    "pixal3d": {
        "repo": "TencentARC/Pixal3D",
        "agents": "https://huggingface.co/spaces/TencentARC/Pixal3D/agents.md",
        "api_info": "https://tencentarc-pixal3d.hf.space/gradio_api/info",
        "config": "https://tencentarc-pixal3d.hf.space/config",
    },
}

token = os.environ.get("HF_TOKEN", "").strip()
headers = {
    "User-Agent": "evowild-t0-endpoint-smoke/1.0",
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
                item["api_names"] = sorted(
                    k for k in parsed.get("named_endpoints", {}).keys()
                )
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
            except Exception as exc:
                item["config_parse_error"] = repr(exc)

    summary["spaces"][key] = item

(OUT / "summary.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

print(json.dumps(summary, indent=2, ensure_ascii=False))

# Endpoint discovery is a smoke test, not generation.
# Fail only if both Spaces are wholly unreachable at API-info level.
reachable = [
    v.get("api_info", {}).get("ok", False)
    for v in summary["spaces"].values()
]
sys.exit(0 if any(reachable) else 2)
