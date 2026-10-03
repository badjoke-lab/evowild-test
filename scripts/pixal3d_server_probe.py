#!/usr/bin/env python3
import json
import pathlib
import re
import urllib.request

OUT = pathlib.Path("art/s-creature/experiments/trellis2-pixal3d/server-probe")
OUT.mkdir(parents=True, exist_ok=True)

BASE = "https://tencentarc-pixal3d-server.hf.space"
URLS = {
    "root": BASE + "/",
    "config": BASE + "/config",
    "api_info": BASE + "/gradio_api/info",
}

headers = {
    "User-Agent": "evowild-pixal3d-server-probe/1.0",
    "Accept": "*/*",
}

report = {"base": BASE, "endpoints": {}, "remote_urls": []}
all_text = []

for name, url in URLS.items():
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", errors="replace")
            status = r.status
            ctype = r.headers.get("content-type")
        report["endpoints"][name] = {
            "ok": True,
            "status": status,
            "content_type": ctype,
            "bytes": len(body.encode("utf-8")),
        }
    except Exception as exc:
        body = ""
        report["endpoints"][name] = {
            "ok": False,
            "error": repr(exc),
        }

    suffix = "json" if name in {"config", "api_info"} else "html"
    (OUT / f"{name}.{suffix}").write_text(body, encoding="utf-8")
    all_text.append(body)

joined = "\n".join(all_text)
patterns = [
    r'https://[a-zA-Z0-9-]+\.gradio\.live',
    r'https://[a-zA-Z0-9.-]+\.hf\.space',
]
remote = []
for pat in patterns:
    remote.extend(re.findall(pat, joined))
report["remote_urls"] = sorted(set(remote))
report["instances"] = []

for base in [u for u in report["remote_urls"] if u.endswith(".gradio.live")]:
    item = {"base": base}
    for name, suffix in {
        "queue": "/queue?session_id=",
        "api_info": "/gradio_api/info",
        "config": "/config",
    }.items():
        req = urllib.request.Request(base + suffix, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read().decode("utf-8", errors="replace")
                item[name] = {
                    "ok": True,
                    "status": r.status,
                    "content_type": r.headers.get("content-type"),
                    "bytes": len(body.encode("utf-8")),
                }
            if name == "queue":
                try:
                    item["queue_data"] = json.loads(body)
                except Exception:
                    item["queue_text"] = body[:1000]
            elif name == "api_info":
                try:
                    info = json.loads(body)
                    item["api_names"] = sorted((info.get("named_endpoints") or {}).keys())
                except Exception as exc:
                    item["api_info_parse_error"] = repr(exc)
        except Exception as exc:
            item[name] = {"ok": False, "error": repr(exc)}
    report["instances"].append(item)

# Pull useful HTML component values out of config if possible.
try:
    cfg = json.loads((OUT / "config.json").read_text(encoding="utf-8"))
    components = cfg.get("components", [])
    html_values = []
    for comp in components:
        props = comp.get("props") or {}
        value = props.get("value")
        if isinstance(value, str) and ("gradio.live" in value or "Instance" in value):
            html_values.append(value)
    report["config_html_values"] = html_values
except Exception as exc:
    report["config_parse_error"] = repr(exc)

(OUT / "report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

print(json.dumps(report, indent=2, ensure_ascii=False))
