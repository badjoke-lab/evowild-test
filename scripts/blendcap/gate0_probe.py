#!/usr/bin/env python3
"""Gate 0 environment probe for the isolated EvoWild BlendCap S motion bench.

This script does not install anything and does not download gated model assets.
It reports whether the current machine is a plausible environment for the next
manual/source-build step.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

MIN_FREE_GB = 32.0
MIN_BLENDER = (4, 2, 0)
PINNED_BLENDCAP_SHA = "e3238699507c00e34b6c948931c4742915b8dc42"


def run(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=15,
            check=False,
        )
        return p.returncode, p.stdout.strip()
    except Exception as exc:
        return 1, str(exc)


def parse_blender_version(text: str) -> tuple[int, int, int] | None:
    # Typical first line: "Blender 4.2.3"
    for token in text.replace("\n", " ").split():
        if token and token[0].isdigit() and "." in token:
            parts = token.split(".")
            if len(parts) >= 2 and all(p.isdigit() for p in parts[:2]):
                nums = [int(p) if p.isdigit() else 0 for p in parts[:3]]
                while len(nums) < 3:
                    nums.append(0)
                return tuple(nums[:3])
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="EvoWild repository root",
    )
    parser.add_argument(
        "--blendcap-root",
        default=os.environ.get("BLENDCAP_ROOT", ""),
        help="Optional local BlendCap checkout to verify",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    disk = shutil.disk_usage(repo_root)
    free_gb = disk.free / (1024 ** 3)

    blender_path = shutil.which("blender")
    blender_text = ""
    blender_version = None
    if blender_path:
        _, blender_text = run([blender_path, "--version"])
        blender_version = parse_blender_version(blender_text.splitlines()[0] if blender_text else "")

    git_path = shutil.which("git")

    nvidia_path = shutil.which("nvidia-smi")
    nvidia_text = ""
    if nvidia_path:
        _, nvidia_text = run(
            [
                nvidia_path,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader",
            ]
        )

    s_asset = repo_root / "public/models/evowild-s/focus-rigged-v5.glb"

    blendcap_root = Path(args.blendcap_root).expanduser().resolve() if args.blendcap_root else None
    blendcap_source_ok = None
    blendcap_sha = None
    if blendcap_root:
        expected_files = [
            blendcap_root / "README.md",
            blendcap_root / "requirements.txt",
            blendcap_root / "save_mhr_data.py",
            blendcap_root / "blendcap/retarget",
        ]
        blendcap_source_ok = all(p.exists() for p in expected_files)
        if git_path and (blendcap_root / ".git").exists():
            code, out = run([git_path, "-C", str(blendcap_root), "rev-parse", "HEAD"])
            if code == 0:
                blendcap_sha = out.strip()

    os_name = platform.system()
    macos = os_name == "Darwin"
    linux = os_name == "Linux"
    windows = os_name == "Windows"

    blockers: list[str] = []
    warnings: list[str] = []

    if free_gb < MIN_FREE_GB:
        blockers.append(f"free disk below {MIN_FREE_GB:g} GB")
    if not git_path:
        blockers.append("git not found")
    if not blender_path:
        blockers.append("blender not found")
    elif blender_version is None or blender_version < MIN_BLENDER:
        blockers.append("Blender 4.2+ not detected")
    if not s_asset.exists():
        blockers.append("locked S runtime asset missing")

    if macos:
        warnings.append(
            "macOS is not supported by the paid BlendCap build; source build is unsupported and experimental"
        )
    if not nvidia_path:
        warnings.append("validated NVIDIA path not detected; CPU-only or experimental GPU path required")
    if blendcap_root and blendcap_source_ok is False:
        blockers.append("BlendCap checkout is missing expected source files")
    if blendcap_sha and blendcap_sha != PINNED_BLENDCAP_SHA:
        warnings.append(
            f"BlendCap checkout is {blendcap_sha}, bench pin is {PINNED_BLENDCAP_SHA}"
        )
    if not blendcap_root:
        warnings.append("BlendCap source checkout not supplied; upstream pin not locally verified")

    plausible_cpu = (
        not blockers
        and blender_path is not None
        and git_path is not None
        and free_gb >= MIN_FREE_GB
    )
    plausible_gpu = plausible_cpu and bool(nvidia_path)

    if plausible_gpu:
        suggested = "PASS_GPU_TEST"
    elif plausible_cpu:
        suggested = "PASS_CPU_TEST"
    else:
        suggested = "BLOCKED_ENV"

    result = {
        "bench": "blendcap-s-motion-bench-v0.1",
        "blendcap_pin": PINNED_BLENDCAP_SHA,
        "os": os_name,
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python": sys.version.split()[0],
        "repo_root": str(repo_root),
        "free_disk_gb": round(free_gb, 2),
        "git": git_path,
        "blender": blender_path,
        "blender_version": blender_version,
        "nvidia_smi": nvidia_path,
        "nvidia": nvidia_text or None,
        "s_asset_exists": s_asset.exists(),
        "blendcap_root": str(blendcap_root) if blendcap_root else None,
        "blendcap_source_files_ok": blendcap_source_ok,
        "blendcap_checkout_sha": blendcap_sha,
        "platform_flags": {
            "macos": macos,
            "linux": linux,
            "windows": windows,
        },
        "blockers": blockers,
        "warnings": warnings,
        "suggested_gate0_decision": suggested,
        "note": (
            "A PASS here means the machine is plausible for the next source-build test. "
            "It does not prove BlendCap capture works and does not authorize Gate 1."
        ),
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
