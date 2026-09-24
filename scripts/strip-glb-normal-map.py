#!/usr/bin/env python3
import json
import struct
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: strip-glb-normal-map.py INPUT.glb OUTPUT.glb")

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
data = src.read_bytes()

if len(data) < 20:
    raise SystemExit("invalid GLB: too short")

magic, version, total_length = struct.unpack_from("<4sII", data, 0)
if magic != b"glTF" or version != 2:
    raise SystemExit("invalid GLB header")

json_len, json_type = struct.unpack_from("<I4s", data, 12)
if json_type != b"JSON":
    raise SystemExit("first chunk is not JSON")

json_start = 20
json_end = json_start + json_len
gltf = json.loads(data[json_start:json_end].decode("utf-8").rstrip(" \t\r\n\x00"))

removed = 0
for material in gltf.get("materials", []):
    if "normalTexture" in material:
        material.pop("normalTexture", None)
        removed += 1

encoded = json.dumps(gltf, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
padding = (-len(encoded)) % 4
encoded += b" " * padding

tail = data[json_end:]
new_total = 12 + 8 + len(encoded) + len(tail)
out = bytearray()
out += struct.pack("<4sII", b"glTF", 2, new_total)
out += struct.pack("<I4s", len(encoded), b"JSON")
out += encoded
out += tail

dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_bytes(out)

print(json.dumps({
    "input": str(src),
    "output": str(dst),
    "normal_textures_removed": removed,
    "input_bytes": len(data),
    "output_bytes_pre_prune": len(out)
}, indent=2))
