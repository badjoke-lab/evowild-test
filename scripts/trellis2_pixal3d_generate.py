#!/usr/bin/env python3
import argparse
import json
import inspect
import os
import pathlib
import shutil
import traceback
import uuid
import urllib.request

from gradio_client import Client, handle_file

ROOT = pathlib.Path(__file__).resolve().parents[1]
INPUT = ROOT / "art/s-creature/references/01_s_body_primary.png"
BASE_OUT = ROOT / "art/s-creature/experiments/trellis2-pixal3d/raw"

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


def jsonable(value):
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def find_paths(value):
    found = []
    if isinstance(value, pathlib.Path):
        found.append(str(value))
    elif isinstance(value, str):
        if pathlib.Path(value).exists():
            found.append(value)
    elif isinstance(value, dict):
        for key in ("path", "url"):
            v = value.get(key)
            if isinstance(v, str) and pathlib.Path(v).exists():
                found.append(v)
        for v in value.values():
            found.extend(find_paths(v))
    elif isinstance(value, (list, tuple)):
        for v in value:
            found.extend(find_paths(v))
    return list(dict.fromkeys(found))


def as_file(value):
    candidates = find_paths(value)
    if candidates:
        return handle_file(candidates[0])
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and value.get("path"):
        return value
    raise RuntimeError(f"Could not resolve preprocess output as file: {value!r}")


def iter_file_objs(value):
    if isinstance(value, dict):
        meta = value.get("meta") or {}
        if (
            isinstance(meta, dict)
            and meta.get("_type") == "gradio.FileData"
        ) or ("path" in value and ("url" in value or "orig_name" in value)):
            yield value
        for v in value.values():
            yield from iter_file_objs(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from iter_file_objs(v)
    elif hasattr(value, "path"):
        yield {
            "path": getattr(value, "path", None),
            "url": getattr(value, "url", None),
            "orig_name": getattr(value, "orig_name", None),
            "mime_type": getattr(value, "mime_type", None),
        }


def save_returned_files(result, out_dir, client=None, base_url=None):
    copied = []
    seen = set()

    # Local outputs, if the installed client still downloaded anything.
    for src in find_paths(result):
        p = pathlib.Path(src)
        if not p.is_file() or str(p) in seen:
            continue
        dst = out_dir / p.name
        if dst.resolve() != p.resolve():
            shutil.copy2(p, dst)
        copied.append(str(dst))
        seen.add(str(p))

    # With download_files=False, explicitly fetch only returned output files.
    for obj in iter_file_objs(result):
        url = obj.get("url")
        if not url:
            continue
        if url.startswith("/") and base_url:
            url = base_url.rstrip("/") + url
        if not url.startswith("http"):
            continue
        name = obj.get("orig_name") or pathlib.Path(str(obj.get("path") or "output.bin")).name
        if not name:
            name = "output.bin"
        dst = out_dir / name
        try:
            headers = dict(getattr(client, "headers", {}) or {})
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as r:
                dst.write_bytes(r.read())
            copied.append(str(dst))
        except Exception as exc:
            (out_dir / "download-errors.txt").open("a", encoding="utf-8").write(
                f"{url}\t{exc!r}\n"
            )
    return list(dict.fromkeys(copied))


def client_for(space, download_files=False):
    token = os.environ.get("HF_TOKEN", "").strip() or None
    params = inspect.signature(Client).parameters
    kwargs = {"verbose": True}
    if "download_files" in params:
        kwargs["download_files"] = download_files
    if token:
        if "hf_token" in params:
            kwargs["hf_token"] = token
        elif "token" in params:
            kwargs["token"] = token
        # If neither exists, huggingface_hub can still pick HF_TOKEN from env.
    print("gradio_client.Client auth parameter:", "hf_token" if "hf_token" in params else ("token" if "token" in params else "env-only"))
    return Client(space, **kwargs)


def run_pixal3d(seed, resolution, out_dir):
    session_id = str(uuid.uuid4())
    pre_client = client_for("TencentARC/Pixal3D", download_files=True)
    client = client_for("TencentARC/Pixal3D", download_files=False)

    pre = pre_client.predict(
        image=handle_file(str(INPUT)),
        api_name="/preprocess",
    )

    gen = client.predict(
        image=as_file(pre),
        seed=seed,
        resolution=resolution,
        manual_fov=-1.0,
        fov_unit="deg",
        session_id=session_id,
        api_name="/generate_3d",
        **DEFAULTS,
    )

    (out_dir / "generation.json").write_text(
        json.dumps(jsonable(gen), indent=2) + "\n",
        encoding="utf-8",
    )
    preview_dir = out_dir / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_files = save_returned_files(
        gen, preview_dir, client, "https://tencentarc-pixal3d.hf.space"
    )

    state_path = gen[0] if isinstance(gen, (tuple, list)) else gen
    if isinstance(state_path, dict):
        state_path = (
            state_path.get("state_path")
            or state_path.get("path")
            or state_path.get("value")
            or state_path
        )

    (out_dir / "state-path.txt").write_text(str(state_path) + "\n", encoding="utf-8")

    glb = client.predict(
        state_path=state_path,
        decimation_target=300000,
        texture_size=2048,
        session_id=session_id,
        api_name="/extract_glb_api",
    )

    return {
        "engine": "TencentARC/Pixal3D",
        "seed": seed,
        "resolution": resolution,
        "session_id": session_id,
        "preprocess_return": jsonable(pre),
        "generate_return": jsonable(gen),
        "preview_files": preview_files,
        "extract_return": jsonable(glb),
        "saved_files": save_returned_files(glb, out_dir, client, "https://tencentarc-pixal3d.hf.space"),
    }


def run_trellis2(seed, resolution, out_dir):
    pre_client = client_for("microsoft/TRELLIS.2", download_files=True)
    client = client_for("microsoft/TRELLIS.2", download_files=False)

    pre = pre_client.predict(
        input=handle_file(str(INPUT)),
        api_name="/preprocess_image",
    )

    gen = client.predict(
        image=as_file(pre),
        seed=seed,
        resolution=resolution,
        api_name="/image_to_3d",
        **DEFAULTS,
    )

    glb = client.predict(
        decimation_target=300000,
        texture_size=2048,
        api_name="/extract_glb",
    )

    return {
        "engine": "microsoft/TRELLIS.2",
        "seed": seed,
        "resolution": resolution,
        "preprocess_return": jsonable(pre),
        "generate_return": jsonable(gen),
        "extract_return": jsonable(glb),
        "saved_files": save_returned_files(glb, out_dir, client, "https://microsoft-trellis-2.hf.space"),
    }


def main():
    global INPUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["pixal3d", "trellis2"], required=True)
    ap.add_argument("--input", default="art/s-creature/references/01_s_body_primary.png")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resolution", default="1024")
    args = ap.parse_args()
    INPUT = ROOT / args.input
    if not INPUT.is_file():
        raise FileNotFoundError(INPUT)

    out_dir = BASE_OUT / args.engine / f"seed-{args.seed:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "report.json"

    report = {
        "status": "RUNNING",
        "input": str(INPUT.relative_to(ROOT)),
        "engine": args.engine,
        "seed": args.seed,
        "resolution": args.resolution,
        "auth_mode": "HF_TOKEN" if os.environ.get("HF_TOKEN", "").strip() else "anonymous",
    }

    try:
        if args.engine == "pixal3d":
            report.update(run_pixal3d(args.seed, args.resolution, out_dir))
        else:
            report.update(run_trellis2(args.seed, args.resolution, out_dir))

        glbs = [p for p in report.get("saved_files", []) if p.lower().endswith(".glb")]
        report["glb_files"] = glbs
        report["status"] = "SUCCESS" if glbs else "NO_GLB"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        if not glbs:
            raise RuntimeError("Space call completed but no local GLB was returned.")
    except Exception as exc:
        report["status"] = "FAILED"
        report["error"] = repr(exc)
        report["traceback"] = traceback.format_exc()
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        raise


if __name__ == "__main__":
    main()
