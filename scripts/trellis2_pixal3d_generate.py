#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import shutil
import traceback
import uuid

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


def save_returned_files(result, out_dir):
    copied = []
    for src in find_paths(result):
        p = pathlib.Path(src)
        if not p.is_file():
            continue
        dst = out_dir / p.name
        if dst.resolve() != p.resolve():
            shutil.copy2(p, dst)
        copied.append(str(dst))
    return copied


def client_for(space):
    token = os.environ.get("HF_TOKEN", "").strip() or None
    return Client(space, hf_token=token, verbose=True)


def run_pixal3d(seed, resolution, out_dir):
    session_id = str(uuid.uuid4())
    client = client_for("TencentARC/Pixal3D")

    pre = client.predict(
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

    state_path = gen[0] if isinstance(gen, (tuple, list)) else gen
    if isinstance(state_path, dict):
        state_path = state_path.get("path") or state_path.get("value") or state_path

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
        "extract_return": jsonable(glb),
        "saved_files": save_returned_files(glb, out_dir),
    }


def run_trellis2(seed, resolution, out_dir):
    client = client_for("microsoft/TRELLIS.2")

    pre = client.predict(
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
        "saved_files": save_returned_files(glb, out_dir),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["pixal3d", "trellis2"], required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resolution", default="1024")
    args = ap.parse_args()

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
