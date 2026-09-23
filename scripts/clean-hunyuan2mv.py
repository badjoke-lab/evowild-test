from pathlib import Path
import json
import struct
import sys

import numpy as np

src = Path(sys.argv[1])
out = Path(sys.argv[2])
report_path = Path(sys.argv[3])

data = src.read_bytes()
magic, version, total_len = struct.unpack_from("<4sII", data, 0)
if magic != b"glTF" or version != 2:
    raise RuntimeError("Expected GLB 2.0")

json_len, json_type = struct.unpack_from("<I4s", data, 12)
if json_type != b"JSON":
    raise RuntimeError("Expected JSON chunk")
gltf = json.loads(data[20:20 + json_len])

bin_start = 20 + json_len
bin_len, bin_type = struct.unpack_from("<I4s", data, bin_start)
if bin_type != b"BIN\x00":
    raise RuntimeError("Expected BIN chunk")
buf = memoryview(data)[bin_start + 8:bin_start + 8 + bin_len]

primitive = gltf["meshes"][0]["primitives"][0]

def accessor_array(index):
    accessor = gltf["accessors"][index]
    view = gltf["bufferViews"][accessor["bufferView"]]
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    count = accessor["count"]
    ncomp = {"SCALAR": 1, "VEC3": 3}[accessor["type"]]
    dtype = {5125: np.uint32, 5126: np.float32}[accessor["componentType"]]
    nbytes = count * ncomp * np.dtype(dtype).itemsize
    arr = np.frombuffer(buf[offset:offset + nbytes], dtype=dtype)
    return arr.reshape((count, ncomp)) if ncomp > 1 else arr

positions = accessor_array(primitive["attributes"]["POSITION"]).astype(np.float32, copy=False)
faces = accessor_array(primitive["indices"]).reshape((-1, 3)).astype(np.uint32, copy=False)

pa = positions[faces[:, 0]]
pb = positions[faces[:, 1]]
pc = positions[faces[:, 2]]
area2 = np.linalg.norm(np.cross(pb - pa, pc - pa), axis=1)
valid_mask = area2 > 1e-10
valid_faces = faces[valid_mask]

parent = np.arange(len(positions), dtype=np.int32)
rank = np.zeros(len(positions), dtype=np.int8)

def find(x):
    x = int(x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = int(parent[x])
    return x

def union(a, b):
    ra, rb = find(a), find(b)
    if ra == rb:
        return
    if rank[ra] < rank[rb]:
        parent[ra] = rb
    elif rank[ra] > rank[rb]:
        parent[rb] = ra
    else:
        parent[rb] = ra
        rank[ra] += 1

for tri in valid_faces:
    union(tri[0], tri[1])
    union(tri[1], tri[2])
    union(tri[2], tri[0])

roots = np.array([find(tri[0]) for tri in valid_faces], dtype=np.int32)
unique_roots, counts = np.unique(roots, return_counts=True)
largest_root = int(unique_roots[np.argmax(counts)])
component_faces = valid_faces[roots == largest_root]

used_vertices = np.unique(component_faces.reshape(-1))
remap = -np.ones(len(positions), dtype=np.int64)
remap[used_vertices] = np.arange(len(used_vertices), dtype=np.int64)
clean_faces = remap[component_faces].astype(np.uint32)
clean_positions = positions[used_vertices].astype(np.float32)

index_bytes = clean_faces.reshape(-1).tobytes()
position_bytes = clean_positions.tobytes()

def pad4(blob):
    return blob + b"\x00" * ((4 - (len(blob) % 4)) % 4)

index_blob = pad4(index_bytes)
position_offset = len(index_blob)
bin_blob = index_blob + position_bytes
bin_blob = pad4(bin_blob)

mins = clean_positions.min(axis=0).astype(float).tolist()
maxs = clean_positions.max(axis=0).astype(float).tolist()

out_gltf = {
    "asset": {"version": "2.0", "generator": "EvoWild Hunyuan cleanup"},
    "scene": 0,
    "scenes": [{"nodes": [0]}],
    "nodes": [{"mesh": 0}],
    "meshes": [{
        "primitives": [{
            "attributes": {"POSITION": 1},
            "indices": 0,
            "mode": 4
        }]
    }],
    "buffers": [{"byteLength": len(bin_blob)}],
    "bufferViews": [
        {"buffer": 0, "byteOffset": 0, "byteLength": len(index_bytes), "target": 34963},
        {"buffer": 0, "byteOffset": position_offset, "byteLength": len(position_bytes), "target": 34962}
    ],
    "accessors": [
        {
            "bufferView": 0,
            "byteOffset": 0,
            "componentType": 5125,
            "count": int(clean_faces.size),
            "type": "SCALAR",
            "min": [int(clean_faces.min())],
            "max": [int(clean_faces.max())]
        },
        {
            "bufferView": 1,
            "byteOffset": 0,
            "componentType": 5126,
            "count": int(len(clean_positions)),
            "type": "VEC3",
            "min": mins,
            "max": maxs
        }
    ]
}

json_blob = json.dumps(out_gltf, separators=(",", ":")).encode("utf-8")
json_blob += b" " * ((4 - (len(json_blob) % 4)) % 4)

total = 12 + 8 + len(json_blob) + 8 + len(bin_blob)
glb = (
    struct.pack("<4sII", b"glTF", 2, total)
    + struct.pack("<I4s", len(json_blob), b"JSON")
    + json_blob
    + struct.pack("<I4s", len(bin_blob), b"BIN\x00")
    + bin_blob
)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(glb)

report = {
    "source_vertices": int(len(positions)),
    "source_triangles": int(len(faces)),
    "degenerate_triangles_removed": int((~valid_mask).sum()),
    "nondegenerate_triangles": int(valid_mask.sum()),
    "connected_components_after_degenerate_removal": int(len(unique_roots)),
    "largest_component_triangles": int(len(component_faces)),
    "clean_vertices": int(len(clean_positions)),
    "clean_triangles": int(len(clean_faces)),
    "clean_bytes": int(len(glb)),
    "rule": "remove area2<=1e-10; retain largest connected component"
}
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
