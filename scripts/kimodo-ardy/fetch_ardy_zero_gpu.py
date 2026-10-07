#!/usr/bin/env python3
"""Generate one real ARDY baseline through a public third-party ZeroGPU host.

The inference host is NOT an NVIDIA-operated Space. It is used only to exercise
official NVIDIA ARDY checkpoint output without paying for GPU compute.
"""

from __future__ import annotations

import argparse
import json
import shutil
import urllib.request
from pathlib import Path
from typing import Any

from gradio_client import Client


def _source_path(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("path", "url", "name"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate:
                return candidate
    path = getattr(value, "path", None)
    if isinstance(path, str):
        return path
    raise TypeError(f"Unsupported Gradio file result: {type(value)!r} {value!r}")


def _copy_result(value: Any, dest: Path) -> None:
    src = _source_path(value)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.startswith(("http://", "https://")):
        urllib.request.urlretrieve(src, dest)
        return
    source = Path(src)
    if not source.exists():
        raise FileNotFoundError(f"Gradio result path does not exist: {source}")
    shutil.copy2(source, dest)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--space", default="cs686/ardy-motion-api")
    ap.add_argument("--prompt", default="A person accelerates smoothly from a run into a full sprint.")
    ap.add_argument("--duration", type=float, default=4.0)
    ap.add_argument("--diffusion-steps", type=int, default=4)
    ap.add_argument("--cfg-weight", type=float, default=2.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    client = Client(args.space, verbose=False)

    try:
        api = client.view_api(print_info=False, return_format="dict")
    except TypeError:
        api = {"note": "installed gradio_client did not support structured view_api"}
    (args.output_dir / "space-api.json").write_text(
        json.dumps(api, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    result = client.predict(
        args.prompt,
        args.duration,
        args.diffusion_steps,
        args.cfg_weight,
        args.seed,
        False,
        api_name="/generate_blender",
    )
    if not isinstance(result, (list, tuple)) or len(result) < 4:
        raise RuntimeError(f"Unexpected /generate_blender result: {result!r}")

    bvh, npz, metadata, returned_seed = result[:4]
    _copy_result(bvh, args.output_dir / "motion.bvh")
    _copy_result(npz, args.output_dir / "motion.npz")
    _copy_result(metadata, args.output_dir / "metadata.json")

    request = {
        "space": args.space,
        "host_classification": "third_party_zero_gpu",
        "authoritative_model_source": "nvidia/ARDY-Core-RP-20FPS-Horizon40",
        "prompt": args.prompt,
        "duration_requested_s": args.duration,
        "diffusion_steps": args.diffusion_steps,
        "cfg_weight": args.cfg_weight,
        "seed_requested": args.seed,
        "seed_returned": int(returned_seed),
        "api_name": "/generate_blender",
    }
    (args.output_dir / "request.json").write_text(
        json.dumps(request, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(request, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
