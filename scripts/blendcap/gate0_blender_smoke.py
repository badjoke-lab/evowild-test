#!/usr/bin/env python3
"""Headless Blender registration smoke test for pinned BlendCap source.

Run with Blender's Python, not system Python:
  blender --background --python scripts/blendcap/gate0_blender_smoke.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import traceback
from pathlib import Path

import bpy

PINNED_BLENDCAP_SHA = "e3238699507c00e34b6c948931c4742915b8dc42"


def main() -> int:
    root_text = os.environ.get("BLENDCAP_ROOT", "")
    result = {
        "bench": "blendcap-s-motion-bench-v0.1",
        "blender_version": list(bpy.app.version),
        "blendcap_pin": PINNED_BLENDCAP_SHA,
        "blendcap_root": root_text or None,
        "import_ok": False,
        "register_ok": False,
        "unregister_ok": False,
        "error": None,
    }

    try:
        if bpy.app.version < (4, 2, 0):
            raise RuntimeError(f"Blender 4.2+ required, got {bpy.app.version_string}")

        if not root_text:
            raise RuntimeError("BLENDCAP_ROOT is not set")

        root = Path(root_text).resolve()
        init_py = root / "__init__.py"
        if not init_py.exists():
            raise RuntimeError(f"BlendCap __init__.py not found: {init_py}")

        package_name = "blendcap_source_smoke"
        spec = importlib.util.spec_from_file_location(
            package_name,
            init_py,
            submodule_search_locations=[str(root)],
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("could not build import spec")

        module = importlib.util.module_from_spec(spec)
        sys.modules[package_name] = module
        spec.loader.exec_module(module)
        result["import_ok"] = True

        module.register()
        result["register_ok"] = True

        module.unregister()
        result["unregister_ok"] = True

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()

    print("BLENDCAP_GATE0_BLENDER_SMOKE=" + json.dumps(result, ensure_ascii=False))
    return 0 if (
        result["import_ok"]
        and result["register_ok"]
        and result["unregister_ok"]
    ) else 3


if __name__ == "__main__":
    raise SystemExit(main())
