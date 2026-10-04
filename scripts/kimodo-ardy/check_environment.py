#!/usr/bin/env python3
"""EvoWild Kimodo/ARDY GPU environment probe.

This script is intentionally dependency-light. It reports whether the current
machine is a plausible *inference test host*. It does not install packages,
download checkpoints, or expose authentication tokens.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class Probe:
    platform: str
    machine: str
    python: str
    nvidia_smi: bool
    torch_installed: bool
    torch_version: Optional[str]
    cuda_available: bool
    cuda_version: Optional[str]
    gpu_name: Optional[str]
    gpu_vram_gb: Optional[float]
    hf_token_present: bool
    kimodo_candidate: bool
    ardy_candidate: bool
    notes: list[str]


def nvidia_smi_info() -> tuple[bool, Optional[str], Optional[float]]:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return False, None, None
    try:
        out = subprocess.check_output(
            [
                exe,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=10,
        ).strip().splitlines()
        if not out:
            return True, None, None
        name, mem = [x.strip() for x in out[0].split(",", 1)]
        return True, name, round(float(mem) / 1024.0, 2)
    except Exception:
        return True, None, None


def main() -> int:
    notes: list[str] = []
    smi, smi_name, smi_vram = nvidia_smi_info()

    torch_installed = False
    torch_version = None
    cuda_available = False
    cuda_version = None
    gpu_name = smi_name
    gpu_vram_gb = smi_vram

    try:
        import torch  # type: ignore

        torch_installed = True
        torch_version = str(torch.__version__)
        cuda_available = bool(torch.cuda.is_available())
        cuda_version = getattr(torch.version, "cuda", None)

        if cuda_available:
            try:
                gpu_name = torch.cuda.get_device_name(0)
                props = torch.cuda.get_device_properties(0)
                gpu_vram_gb = round(props.total_memory / (1024 ** 3), 2)
            except Exception as exc:
                notes.append(f"torch CUDA device query failed: {exc}")
    except Exception as exc:
        notes.append(f"PyTorch unavailable: {exc}")

    hf_present = bool(
        os.getenv("HF_TOKEN")
        or os.getenv("HUGGING_FACE_HUB_TOKEN")
        or os.path.exists(os.path.expanduser("~/.cache/huggingface/token"))
    )

    if not smi:
        notes.append("nvidia-smi not found")
    if not cuda_available:
        notes.append("CUDA is not available through PyTorch")
    if not hf_present:
        notes.append(
            "No Hugging Face token detected; gated text encoders/checkpoints may require one"
        )

    # Candidate means only that the host clears the basic CUDA gate.
    # VRAM is reported separately because CPU text-encoder modes can change needs.
    kimodo_candidate = bool(cuda_available)
    ardy_candidate = bool(cuda_available)

    if gpu_vram_gb is not None and gpu_vram_gb < 3.0:
        notes.append(
            "GPU VRAM is below 3 GB; even reduced-VRAM Kimodo usage is unlikely to be practical"
        )
    if gpu_vram_gb is not None and gpu_vram_gb < 8.0:
        notes.append(
            "GPU VRAM is limited; expect CPU text encoding and/or reduced acceleration options"
        )

    probe = Probe(
        platform=platform.platform(),
        machine=platform.machine(),
        python=sys.version.split()[0],
        nvidia_smi=smi,
        torch_installed=torch_installed,
        torch_version=torch_version,
        cuda_available=cuda_available,
        cuda_version=cuda_version,
        gpu_name=gpu_name,
        gpu_vram_gb=gpu_vram_gb,
        hf_token_present=hf_present,
        kimodo_candidate=kimodo_candidate,
        ardy_candidate=ardy_candidate,
        notes=notes,
    )

    print(json.dumps(asdict(probe), indent=2, ensure_ascii=False))
    return 0 if (kimodo_candidate or ardy_candidate) else 2


if __name__ == "__main__":
    raise SystemExit(main())
