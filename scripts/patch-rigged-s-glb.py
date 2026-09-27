import json
import math
import struct
import sys
from pathlib import Path

# Directly patch POSITION values inside the existing GLB. This deliberately
# avoids Blender re-export: re-export changed the original shading/normals and
# made the NPR pass expose every triangle. All skins, animations, normals,
# materials, textures and buffer layout remain byte-for-byte unchanged except
# for the selected position floats.

args = sys.argv[1:]
if len(args) != 3:
    raise SystemExit("usage: patch-rigged-s-glb.py INPUT.glb OUTPUT.glb REPORT.json")

src = Path(args[0])
out = Path(args[1])
report_path = Path(args[2])

data = bytearray(src.read_bytes())
if len(data) < 20:
    raise RuntimeError("GLB too small")

magic, version, total_len = struct.unpack_from("<4sII", data, 0)
if magic != b"glTF" or version != 2 or total_len != len(data):
    raise RuntimeError("not a valid GLB v2")

JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942
json_doc = None
bin_start = None
bin_len = None
p = 12
while p < len(data):
    chunk_len, chunk_type = struct.unpack_from("<II", data, p)
    start = p + 8
    end = start + chunk_len
    if end > len(data):
        raise RuntimeError("truncated GLB chunk")
    if chunk_type == JSON_CHUNK:
        json_doc = json.loads(bytes(data[start:end]).decode("utf-8").rstrip(" \t\r\n\x00"))
    elif chunk_type == BIN_CHUNK and bin_start is None:
        bin_start = start
        bin_len = chunk_len
    p = end

if json_doc is None or bin_start is None:
    raise RuntimeError("GLB JSON/BIN chunk missing")

component = {
    5120: ("b", 1),
    5121: ("B", 1),
    5122: ("h", 2),
    5123: ("H", 2),
    5125: ("I", 4),
    5126: ("f", 4),
}
arity = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}

def accessor_layout(index):
    a = json_doc["accessors"][index]
    if "sparse" in a:
        raise RuntimeError(f"sparse accessor unsupported: {index}")
    bv = json_doc["bufferViews"][a["bufferView"]]
    if bv.get("buffer", 0) != 0:
        raise RuntimeError("only GLB buffer 0 is supported")
    fmt, comp_size = component[a["componentType"]]
    n = arity[a["type"]]
    elem_size = comp_size * n
    stride = bv.get("byteStride", elem_size)
    base = bin_start + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    return a, fmt, comp_size, n, stride, base

def normalized_value(raw, ctype):
    if ctype == 5120:
        return max(raw / 127.0, -1.0)
    if ctype == 5121:
        return raw / 255.0
    if ctype == 5122:
        return max(raw / 32767.0, -1.0)
    if ctype == 5123:
        return raw / 65535.0
    if ctype == 5125:
        return raw / 4294967295.0
    return float(raw)

def read_accessor(index, normalize=False):
    a, fmt, comp_size, n, stride, base = accessor_layout(index)
    sfmt = "<" + fmt * n
    values = []
    for i in range(a["count"]):
        vals = struct.unpack_from(sfmt, data, base + i * stride)
        if normalize and a.get("normalized", False):
            vals = tuple(normalized_value(v, a["componentType"]) for v in vals)
        elif normalize:
            vals = tuple(float(v) for v in vals)
        values.append(vals)
    return values

def write_position(index, vertex_index, xyz):
    a, fmt, comp_size, n, stride, base = accessor_layout(index)
    if a["componentType"] != 5126 or a["type"] != "VEC3":
        raise RuntimeError("POSITION accessor must be FLOAT VEC3")
    struct.pack_into("<fff", data, base + vertex_index * stride, *xyz)

def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)

nodes = json_doc.get("nodes", [])
skins = json_doc.get("skins", [])
meshes = json_doc.get("meshes", [])

patched_primitives = []
total_changed = 0
global_max_shift = 0.0

for node_index, node in enumerate(nodes):
    if "mesh" not in node or "skin" not in node:
        continue
    skin = skins[node["skin"]]
    joint_nodes = skin.get("joints", [])
    head_slots = [
        slot for slot, joint_node_index in enumerate(joint_nodes)
        if "head" in nodes[joint_node_index].get("name", "").lower()
    ]
    if not head_slots:
        continue
    # Prefer the shortest exact name when several helper/head joints exist.
    head_slot = min(
        head_slots,
        key=lambda slot: (nodes[joint_nodes[slot]].get("name", "").lower() != "head",
                          len(nodes[joint_nodes[slot]].get("name", "")))
    )
    head_name = nodes[joint_nodes[head_slot]].get("name", "head")

    mesh = meshes[node["mesh"]]
    for prim_index, prim in enumerate(mesh.get("primitives", [])):
        attrs = prim.get("attributes", {})
        needed = ("POSITION", "JOINTS_0", "WEIGHTS_0")
        if not all(k in attrs for k in needed):
            continue

        pos_index = attrs["POSITION"]
        joints_index = attrs["JOINTS_0"]
        weights_index = attrs["WEIGHTS_0"]
        positions = [list(v) for v in read_accessor(pos_index)]
        joints = read_accessor(joints_index)
        weights = read_accessor(weights_index, normalize=True)
        if not (len(positions) == len(joints) == len(weights)):
            raise RuntimeError("skinned accessor counts differ")

        head_weight = []
        for js, ws in zip(joints, weights):
            w = 0.0
            for j, value in zip(js, ws):
                if int(j) == head_slot:
                    w += float(value)
            head_weight.append(w)

        selected = [
            i for i, w in enumerate(head_weight)
            if w >= 0.18
        ]
        if len(selected) < 12:
            continue

        xs = [positions[i][0] for i in selected]
        ys = [positions[i][1] for i in selected]
        zs = [positions[i][2] for i in selected]
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)
        height = max_y - min_y
        depth = max_z - min_z
        if height <= 1e-6 or depth <= 1e-6:
            continue

        # Estimate the skull centre from the lower half of the head-weighted
        # vertices instead of from the two crest tips themselves.
        base_indices = [
            i for i in selected
            if positions[i][1] <= min_y + height * 0.47 and head_weight[i] >= 0.28
        ]
        if not base_indices:
            base_indices = selected
        weight_sum = sum(max(head_weight[i], 1e-6) for i in base_indices)
        center_x = sum(positions[i][0] * max(head_weight[i], 1e-6) for i in base_indices) / weight_sum

        y_measure = min_y + height * 0.62
        y_blend = min_y + height * 0.50
        z_start = min_z + depth * 0.65
        side_guard = max(0.0015, (max(xs) - min(xs)) * 0.010)

        crest_indices = [
            i for i in selected
            if positions[i][1] >= y_measure and positions[i][2] >= z_start
            and abs(positions[i][0] - center_x) > side_guard
        ]
        left = [i for i in crest_indices if positions[i][0] < center_x]
        right = [i for i in crest_indices if positions[i][0] > center_x]
        if len(left) < 3 or len(right) < 3:
            raise RuntimeError(
                f"crest split not measurable for primitive {prim_index}: "
                f"left={len(left)} right={len(right)}"
            )

        left_inner = max(positions[i][0] for i in left)
        right_inner = min(positions[i][0] for i in right)
        gap = right_inner - left_inner
        crest_min = min(positions[i][0] for i in crest_indices)
        crest_max = max(positions[i][0] for i in crest_indices)
        crest_span = max(crest_max - crest_min, 1e-6)

        # Shift each lobe rigidly toward the centre. This preserves its width.
        # A small overlap is intentional so animation cannot reopen a visible
        # central slit during the run cycle.
        target_overlap = max(0.0035, crest_span * 0.045)
        shift_amount = max(0.0, (gap + target_overlap) * 0.5)

        changed = 0
        local_max_shift = 0.0
        for i in selected:
            x, y, z = positions[i]
            if y <= y_blend or z <= z_start:
                continue
            dx = x - center_x
            if abs(dx) <= side_guard * 0.5:
                continue

            hy = smooth01((y - y_blend) / max(1e-6, y_measure - y_blend))
            hz = smooth01((z - z_start) / max(1e-6, max_z - z_start))
            hw = smooth01((head_weight[i] - 0.18) / 0.45)
            strength = hy * (0.74 + 0.26 * hz) * (0.75 + 0.25 * hw)

            shift = shift_amount if dx < 0 else -shift_amount
            new_x = x + shift * strength
            positions[i][0] = new_x
            local_max_shift = max(local_max_shift, abs(new_x - x))
            changed += 1

        for i in selected:
            # Only writes changed and unchanged selected head vertices; all
            # other geometry bytes remain untouched.
            if positions[i][1] > y_blend and positions[i][2] > z_start:
                write_position(pos_index, i, positions[i])

        total_changed += changed
        global_max_shift = max(global_max_shift, local_max_shift)
        patched_primitives.append({
            "node_index": node_index,
            "mesh_index": node["mesh"],
            "primitive_index": prim_index,
            "head_joint_name": head_name,
            "head_joint_slot": head_slot,
            "vertex_count": len(positions),
            "head_weighted_count": len(selected),
            "crest_left_count": len(left),
            "crest_right_count": len(right),
            "head_center_x": center_x,
            "head_bounds": {
                "min_y": min_y, "max_y": max_y,
                "min_z": min_z, "max_z": max_z,
            },
            "y_measure": y_measure,
            "y_blend": y_blend,
            "z_start": z_start,
            "left_inner_before": left_inner,
            "right_inner_before": right_inner,
            "gap_before": gap,
            "target_overlap": target_overlap,
            "shift_amount": shift_amount,
            "changed_vertices": changed,
            "max_x_shift": local_max_shift,
        })

if not patched_primitives or total_changed == 0:
    raise RuntimeError("no rigged S head geometry was patched")

out.write_bytes(data)
report = {
    "source": str(src),
    "output": str(out),
    "method": "direct_glb_position_patch_preserve_all_other_accessors",
    "patched_primitives": patched_primitives,
    "changed_vertices": total_changed,
    "max_x_shift": global_max_shift,
    "status": "rigged_headfix_v3_direct_glb_candidate",
}
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("S_HEADFIX_V3_REPORT " + json.dumps(report, separators=(",", ":")))
