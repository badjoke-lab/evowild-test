from pathlib import Path
import struct, json, io, os
import numpy as np
from collections import defaultdict, deque
from PIL import Image
import trimesh
from trimesh.visual.texture import TextureVisuals
from trimesh.visual.material import SimpleMaterial

artifact_root = Path(os.environ.get("SF3D_ARTIFACT_DIR", "/tmp/sf3d"))
matches = list(artifact_root.rglob("evowild_s_stable_fast_3d_textured.glb"))
if not matches:
    raise RuntimeError("Stable Fast 3D GLB missing from downloaded artifact")
src = matches[0]
data = src.read_bytes()

json_len, _ = struct.unpack_from("<I4s", data, 12)
gltf = json.loads(data[20:20+json_len])
bin_start = 20 + json_len
bin_len, bin_type = struct.unpack_from("<I4s", data, bin_start)
if bin_type != b"BIN\x00":
    raise RuntimeError("Expected binary GLB chunk")
buf = memoryview(data)[bin_start+8:bin_start+8+bin_len]

def accessor_array(idx):
    a = gltf["accessors"][idx]
    bv = gltf["bufferViews"][a["bufferView"]]
    offset = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    count = a["count"]
    ncomp = {"SCALAR":1, "VEC2":2, "VEC3":3, "VEC4":4}[a["type"]]
    dtype = {5125:np.uint32, 5126:np.float32}[a["componentType"]]
    nbytes = count * ncomp * np.dtype(dtype).itemsize
    arr = np.frombuffer(buf[offset:offset+nbytes], dtype=dtype)
    return arr.reshape((count, ncomp)) if ncomp > 1 else arr

primitive = gltf["meshes"][0]["primitives"][0]
indices = accessor_array(primitive["indices"]).reshape(-1)
positions = accessor_array(primitive["attributes"]["POSITION"])
uv = accessor_array(primitive["attributes"]["TEXCOORD_0"])
normals = accessor_array(primitive["attributes"]["NORMAL"])
faces = indices.reshape((-1, 3))

image_index = gltf["textures"][
    gltf["materials"][0]["pbrMetallicRoughness"]["baseColorTexture"]["index"]
]["source"]
image_def = gltf["images"][image_index]
image_bv = gltf["bufferViews"][image_def["bufferView"]]
image_bytes = bytes(
    buf[
        image_bv.get("byteOffset", 0):
        image_bv.get("byteOffset", 0) + image_bv["byteLength"]
    ]
)
base_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

vert_to_faces = defaultdict(list)
for fi, tri in enumerate(faces):
    for v in tri:
        vert_to_faces[int(v)].append(fi)

visited = np.zeros(len(faces), dtype=bool)
components = []
for start in range(len(faces)):
    if visited[start]:
        continue
    q = deque([start])
    visited[start] = True
    fis = []
    vset = set()
    while q:
        fi = q.popleft()
        fis.append(fi)
        for v in faces[fi]:
            v = int(v)
            if v not in vset:
                vset.add(v)
                for nfi in vert_to_faces[v]:
                    if not visited[nfi]:
                        visited[nfi] = True
                        q.append(nfi)
    vidx = np.array(sorted(vset), dtype=np.int64)
    pos = positions[vidx]
    center = pos.mean(axis=0)
    ext = pos.max(axis=0) - pos.min(axis=0)
    components.append({
        "face_indices": np.array(fis, dtype=np.int64),
        "faces": len(fis),
        "center": center,
        "diag": float(np.linalg.norm(ext)),
    })

components.sort(key=lambda c: c["faces"], reverse=True)
selected = []
for comp in components:
    cx = float(comp["center"][0])
    if cx > 0.2:
        continue
    if comp["faces"] < 25:
        continue
    if comp["diag"] < 0.07:
        continue
    selected.append(comp)

if not selected:
    raise RuntimeError("Cleanup removed every component")

selected_face_indices = np.concatenate([c["face_indices"] for c in selected])
selected_faces = faces[selected_face_indices]
used_vertices = np.unique(selected_faces.reshape(-1))

remap = -np.ones(len(positions), dtype=np.int64)
remap[used_vertices] = np.arange(len(used_vertices))
clean_faces = remap[selected_faces]
clean_positions = positions[used_vertices]
clean_uv = uv[used_vertices]
clean_normals = normals[used_vertices]

visual = TextureVisuals(
    uv=clean_uv,
    image=base_image,
    material=SimpleMaterial(image=base_image),
)
clean = trimesh.Trimesh(
    vertices=clean_positions,
    faces=clean_faces,
    vertex_normals=clean_normals,
    visual=visual,
    process=False,
)

out = Path("public/models/evowild-s-sf3d-clean.glb")
out.parent.mkdir(parents=True, exist_ok=True)
clean.export(out)

report = {
    "source_artifact_id": 10644576625,
    "source_faces": int(len(faces)),
    "source_vertices": int(len(positions)),
    "source_components": int(len(components)),
    "clean_faces": int(len(clean_faces)),
    "clean_vertices": int(len(clean_positions)),
    "clean_components_kept": int(len(selected)),
    "rule": "drop center_x>0.2, face_count<25, diag<0.07",
    "status": "prototype_only_not_final_asset",
}
Path("public/models/evowild-s-sf3d-clean.json").write_text(
    json.dumps(report, indent=2),
    encoding="utf-8",
)
print(json.dumps(report, indent=2))
