#!/usr/bin/env python3
"""Verify all 11 user-provided PNG mock originals before Codex uses them.

Stdlib-only; failure means image transfer/reference gate not satisfied.
Do not fall back to generated imagery or silently skip a missing image.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/2p5d/mockups/manifest.json"

def main():
    doc=json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing=[]
    corrupt=[]
    for item in doc["items"]:
        path=ROOT/item["path"]
        if not path.is_file():
            missing.append(item["path"])
            print(f"MISSING {item['path']}")
            continue
        data=path.read_bytes()
        sha=hashlib.sha256(data).hexdigest()
        try:
            signature=data[:8]==bytes((137,80,78,71,13,10,26,10))
            dims=struct.unpack(">II",data[16:24])
        except (ValueError,struct.error):
            signature=False;dims=(0,0)
        if sha!=item["sha256"] or len(data)!=item["size_bytes"] or not signature or list(dims)!=item["dimensions"]:
            corrupt.append(item["path"])
            print(f"BAD {item['path']} SHA256={sha} bytes={len(data)} dimensions={dims}")
        else:
            print(f"PASS {item['path']} SHA256={sha}")
    if missing or corrupt:
        print(f"REFERENCE_IMAGE_MISSING / INVALID: {len(missing)} missing, {len(corrupt)} corrupt.")
        print("Attach evowild-2p5d-codex-mockups-originals.zip and extract at repository root.")
        return 2
    print(f"PASS: {len(doc['items'])} original mocks match expected PNG bytes.")
    return 0

if __name__=="__main__":
    sys.exit(main())
