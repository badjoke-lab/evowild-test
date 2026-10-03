#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import re
import shutil
import time
import urllib.parse
import urllib.request
import uuid

from gradio_client import Client, handle_file

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROXY = "https://tencentarc-pixal3d-server.hf.space"
DEFAULT_INPUT = ROOT / "art/s-creature/experiments/trellis2-pixal3d/prepared/primary_clean_v1.png"
OUT_ROOT = ROOT / "art/s-creature/experiments/trellis2-pixal3d/raw/pixal3d-dedicated"

DEFAULTS = dict(
    ss_guidance_strength=7.5,
    ss_guidance_rescale=0.7,
    ss_sampling_steps=12,
    ss_rescale_t=5.0,
    shape_slat_guidance_strength=7.5,
    shape_slat_guidance_rescale=0.5,
    shape_slat_sampling_steps=12,
    shape_slat_rescale_t=3.0,
    tex_slat_guidance_strength=1.0,
    tex_slat_guidance_rescale=0.0,
    tex_slat_sampling_steps=12,
    tex_slat_rescale_t=3.0,
)

HEADERS = {
    "User-Agent": "evowild-pixal3d-dedicated/1.0",
    "Accept": "*/*",
}


def fetch_text(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def fetch_json(url: str, timeout: int = 30):
    return json.loads(fetch_text(url, timeout=timeout))


def discover_instances():
    cfg = fetch_text(PROXY + "/config")
    urls = sorted(set(re.findall(r"https://[A-Za-z0-9-]+\.gradio\.live", cfg)))
    instances = []
    for base in urls:
        item = {"base": base, "reachable": False, "ahead": 10**9}
        try:
            q = fetch_json(base + "/queue?session_id=", timeout=15)
            item["queue"] = q
            item["ahead"] = int(q.get("total_ahead_for_unregistered", 10**9))
            info = fetch_json(base + "/gradio_api/info", timeout=15)
            names = sorted((info.get("named_endpoints") or {}).keys())
            item["api_names"] = names
            needed = {"/preprocess", "/generate_3d", "/extract_glb_api"}
            item["reachable"] = needed.issubset(set(names))
        except Exception as exc:
            item["error"] = repr(exc)
        instances.append(item)
    return instances


def local_path(value):
    if isinstance(value, pathlib.Path):
        return value
    if isinstance(value, str):
        p = pathlib.Path(value)
        if p.exists():
            return p
    if isinstance(value, dict):
        p = value.get("path")
        if isinstance(p, str) and pathlib.Path(p).exists():
            return pathlib.Path(p)
    if hasattr(value, "path"):
        p = getattr(value, "path", None)
        if p and pathlib.Path(p).exists():
            return pathlib.Path(p)
    raise RuntimeError(f"Could not resolve local file from {value!r}")


def file_objects(value):
    if isinstance(value, dict):
        meta = value.get("meta") or {}
        if (
            (isinstance(meta, dict) and meta.get("_type") == "gradio.FileData")
            or ("path" in value and ("url" in value or "orig_name" in value))
        ):
            yield value
        for v in value.values():
            yield from file_objects(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from file_objects(v)
    elif hasattr(value, "path"):
        yield {
            "path": getattr(value, "path", None),
            "url": getattr(value, "url", None),
            "orig_name": getattr(value, "orig_name", None),
            "mime_type": getattr(value, "mime_type", None),
        }


def download_preview_files(result, base: str, out_dir: pathlib.Path, limit: int = 32):
    saved = []
    errors = []
    for obj in file_objects(result):
        if len(saved) >= limit:
            break
        url = obj.get("url")
        path = obj.get("path")
        orig = obj.get("orig_name")
        if not url and isinstance(path, str) and path.startswith("/"):
            # The local deployment mounts TMP_DIR at /tmp.
            url = base.rstrip("/") + path
        elif isinstance(url, str) and url.startswith("/"):
            url = base.rstrip("/") + url
        if not url or not isinstance(url, str) or not url.startswith("http"):
            continue

        name = orig or pathlib.Path(str(path or urllib.parse.urlparse(url).path)).name or f"preview-{len(saved):02d}.bin"
        # Avoid collisions across render modes.
        dst = out_dir / f"{len(saved):02d}-{name}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                dst.write_bytes(r.read())
            saved.append(str(dst.relative_to(ROOT)))
        except Exception as exc:
            errors.append({"url": url, "error": repr(exc)})
    return saved, errors


def jsonable(value):
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "__dict__"):
        try:
            return jsonable(vars(value))
        except Exception:
            pass
    return repr(value)


def join_queue(base: str, session_id: str):
    url = base.rstrip("/") + "/queue/join?session_id=" + urllib.parse.quote(session_id)
    try:
        return fetch_json(url, timeout=15)
    except Exception as exc:
        return {"ok": False, "error": repr(exc)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(DEFAULT_INPUT.relative_to(ROOT)))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resolution", type=int, default=1024)
    ap.add_argument("--decimation-target", type=int, default=300000)
    ap.add_argument("--texture-size", type=int, default=2048)
    args = ap.parse_args()

    input_path = ROOT / args.input
    if not input_path.is_file():
        raise FileNotFoundError(input_path)

    out_dir = OUT_ROOT / f"seed-{args.seed:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "report.json"

    report = {
        "status": "DISCOVERING",
        "proxy": PROXY,
        "input": str(input_path.relative_to(ROOT)),
        "seed": args.seed,
        "resolution": args.resolution,
        "decimation_target": args.decimation_target,
        "texture_size": args.texture_size,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    try:
        instances = discover_instances()
        report["instances"] = instances
        candidates = [x for x in instances if x.get("reachable")]
        if not candidates:
            raise RuntimeError("No reachable official Pixal3D dedicated instance.")
        candidates.sort(key=lambda x: (x.get("ahead", 10**9), x["base"]))
        chosen = candidates[0]
        base = chosen["base"]
        report["chosen_instance"] = chosen
        report["status"] = "PREPROCESSING"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("Chosen instance:", base, "ahead:", chosen.get("ahead"))

        # Preprocess with the official server-side Pixal3D pipeline and download
        # exactly the returned clean image locally.
        pre_client = Client(base, verbose=True, download_files=True)
        pre = pre_client.predict(
            image=handle_file(str(input_path)),
            api_name="/preprocess",
        )
        pre_path = local_path(pre)
        saved_pre = out_dir / "preprocessed.png"
        shutil.copy2(pre_path, saved_pre)
        report["preprocess_return"] = jsonable(pre)
        report["preprocessed_file"] = str(saved_pre.relative_to(ROOT))

        session_id = uuid.uuid4().hex
        report["session_id"] = session_id
        report["queue_join_generate"] = join_queue(base, session_id)
        report["status"] = "GENERATING"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

        # Do not auto-download the many preview frames during generation.
        gen_client = Client(base, verbose=True, download_files=False)
        gen = gen_client.predict(
            image=handle_file(str(saved_pre)),
            seed=args.seed,
            resolution=args.resolution,
            session_id=session_id,
            api_name="/generate_3d",
            **DEFAULTS,
        )
        report["generate_return"] = jsonable(gen)
        if not isinstance(gen, dict):
            raise RuntimeError(f"Unexpected generate result: {type(gen)!r} {gen!r}")
        state_path = gen.get("state_path")
        if not isinstance(state_path, str) or not state_path:
            raise RuntimeError(f"No state_path in generate result: {gen!r}")
        report["state_path"] = state_path

        previews, preview_errors = download_preview_files(gen.get("render_paths"), base, out_dir)
        report["preview_files"] = previews
        report["preview_download_errors"] = preview_errors

        report["queue_join_extract"] = join_queue(base, session_id)
        report["status"] = "EXTRACTING_GLB"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

        # Extraction has one file output, so allow gradio_client to download it.
        extract_client = Client(base, verbose=True, download_files=True)
        glb = extract_client.predict(
            state_path=state_path,
            decimation_target=args.decimation_target,
            texture_size=args.texture_size,
            session_id=session_id,
            api_name="/extract_glb_api",
        )
        glb_path = local_path(glb)
        final_glb = out_dir / "candidate.glb"
        shutil.copy2(glb_path, final_glb)

        report["extract_return"] = jsonable(glb)
        report["glb_file"] = str(final_glb.relative_to(ROOT))
        report["glb_bytes"] = final_glb.stat().st_size
        report["status"] = "SUCCESS"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
    except Exception as exc:
        report["status"] = "FAILED"
        report["error"] = repr(exc)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        raise


if __name__ == "__main__":
    main()
