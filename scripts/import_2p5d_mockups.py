#!/usr/bin/env python3
"""Safely import original user-provided 2.5D mock PNGs from handoff ZIP.

Usage:
  python3 scripts/import_2p5d_mockups.py /path/to/evowild-2p5d-codex-mockups-originals.zip

Only 11 exact SHA-256 verified PNG files are allowed. Never overwrite a
different file or expand arbitrary paths from untrusted ZIP archives.
"""
import hashlib
import json
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/2p5d/mockups/manifest.json"


def main(argv):
    if len(argv) != 2:
        print("Usage: python3 scripts/import_2p5d_mockups.py <original-mocks.zip>")
        return 2
    source = Path(argv[1]).expanduser()
    if not source.is_file():
        print("REFERENCE_IMAGE_MISSING: specified ZIP not found:", source)
        return 2
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    staged = []
    try:
        with zipfile.ZipFile(source) as archive:
            for item in manifest["items"]:
                rel = item["path"]
                if not rel.startswith("docs/2p5d/mockups/") or not rel.endswith(".png"):
                    raise ValueError("Unsafe manifest path " + rel)
                raw = archive.read(rel)
                dims = struct.unpack(">II", raw[16:24]) if len(raw) >= 24 else (0, 0)
                good = (
                    raw[:8] == bytes((137,80,78,71,13,10,26,10))
                    and list(dims) == item["dimensions"]
                    and len(raw) == item["size_bytes"]
                    and hashlib.sha256(raw).hexdigest() == item["sha256"]
                )
                if not good:
                    raise ValueError("Corrupt or substituted PNG: " + rel)
                target = ROOT / rel
                if target.exists() and target.read_bytes() != raw:
                    raise ValueError("Existing file differs (refusing overwrite): " + rel)
                staged.append((target, raw))
    except (zipfile.BadZipFile, KeyError, ValueError, struct.error) as exc:
        print("REFERENCE_IMAGE_INVALID:", exc)
        return 2
    for target, raw in staged:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(raw)
        print("VERIFIED", target.relative_to(ROOT))
    print("PASS: exactly",len(staged),"original PNG references imported without re-encoding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
