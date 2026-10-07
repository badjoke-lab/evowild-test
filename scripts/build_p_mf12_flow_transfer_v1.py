#!/usr/bin/env python3
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "public" / "concept" / "p-run-sheet.webp"
DONOR = ROOT / "art" / "2p5d" / "motion-donors" / "p-mf12-v1.webp"
OUT = ROOT / "artifacts" / "p-mf12-flow-transfer-v1"
CELL = 256

def split_sheet(path, cols, rows, count):
    img = Image.open(path).convert("RGBA")
    fw = img.width // cols
    fh = img.height // rows
    return [
        img.crop(((i % cols) * fw, (i // cols) * fh, (i % cols + 1) * fw, (i // cols + 1) * fh)).resize((CELL, CELL), Image.Resampling.LANCZOS)
        for i in range(count)
    ]

def alpha_bbox(arr):
    alpha = arr[..., 3]
    ys, xs = np.where(alpha > 12)
    if len(xs) == 0:
        return (0, 0, CELL, CELL)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)

def premul_gray(arr):
    rgb = arr[..., :3].astype(np.float32)
    a = arr[..., 3:4].astype(np.float32) / 255.0
    premul = rgb * a
    gray = cv2.cvtColor(premul.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    # Give silhouette edges weight even when RGB is dark.
    gray = np.maximum(gray, (arr[..., 3].astype(np.float32) * 0.55).astype(np.uint8))
    return gray

def sample_bilinear(field, x, y):
    h, w = field.shape[:2]
    x = np.clip(x, 0, w - 1.001)
    y = np.clip(y, 0, h - 1.001)
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    x1 = np.minimum(x0 + 1, w - 1)
    y1 = np.minimum(y0 + 1, h - 1)
    wx = (x - x0)[..., None]
    wy = (y - y0)[..., None]
    a = field[y0, x0]
    b = field[y0, x1]
    c = field[y1, x0]
    d = field[y1, x1]
    return (a * (1 - wx) * (1 - wy) + b * wx * (1 - wy) + c * (1 - wx) * wy + d * wx * wy)

def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / max(1e-6, edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def warp_source_with_donor(source_img, donor_a, donor_b):
    src = np.array(source_img, dtype=np.uint8)
    da = np.array(donor_a, dtype=np.uint8)
    db = np.array(donor_b, dtype=np.uint8)

    # Existing Motion First donor faces opposite the production P sprites.
    da = np.ascontiguousarray(da[:, ::-1])
    db = np.ascontiguousarray(db[:, ::-1])

    flow = cv2.calcOpticalFlowFarneback(
        premul_gray(da),
        premul_gray(db),
        None,
        0.5,
        4,
        19,
        4,
        7,
        1.4,
        0,
    )
    flow = cv2.GaussianBlur(flow, (0, 0), 2.2)

    sx0, sy0, sx1, sy1 = alpha_bbox(src)
    dx0, dy0, dx1, dy1 = alpha_bbox(da)
    sw = max(1, sx1 - sx0)
    sh = max(1, sy1 - sy0)
    dw = max(1, dx1 - dx0)
    dh = max(1, dy1 - dy0)

    yy, xx = np.mgrid[0:CELL, 0:CELL].astype(np.float32)
    donor_x = dx0 + (xx - sx0) / sw * dw
    donor_y = dy0 + (yy - sy0) / sh * dh
    sampled = sample_bilinear(flow, donor_x, donor_y)

    fx = sampled[..., 0] * (sw / dw)
    fy = sampled[..., 1] * (sh / dh)

    # Keep canonical head / torso identity stable while allowing the lower
    # running silhouette to follow the already-approved mf12 motion field.
    rel_y = (yy - sy0) / sh
    lower = smoothstep(0.43, 0.78, rel_y)
    weight = 0.28 + 0.72 * lower

    # Tail and muzzle may move, but less than limbs.
    rel_x = (xx - sx0) / sw
    edge_damp = 0.74 + 0.26 * smoothstep(0.10, 0.26, rel_x) * (1.0 - smoothstep(0.83, 0.97, rel_x))
    weight *= edge_damp

    alpha_weight = smoothstep(0.01, 0.25, src[..., 3].astype(np.float32) / 255.0)
    weight *= 0.35 + 0.65 * alpha_weight

    fx = np.clip(fx * weight, -18.0, 18.0)
    fy = np.clip(fy * weight, -16.0, 16.0)

    map_x = (xx - fx).astype(np.float32)
    map_y = (yy - fy).astype(np.float32)
    warped = cv2.remap(
        src,
        map_x,
        map_y,
        interpolation=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )

    warped[warped[..., 3] < 3, :3] = 0
    return Image.fromarray(warped, "RGBA"), {
        "max_dx": float(np.max(np.abs(fx))),
        "max_dy": float(np.max(np.abs(fy))),
        "source_bbox": [sx0, sy0, sx1, sy1],
        "donor_bbox": [dx0, dy0, dx1, dy1],
    }

def component_count(frame):
    arr = np.array(frame)
    mask = (arr[..., 3] > 24).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    significant = 0
    for i in range(1, count):
        if stats[i, cv2.CC_STAT_AREA] >= 18:
            significant += 1
    return significant

def make_review(frames):
    canvas = Image.new("RGBA", (CELL * 4, CELL * 3), (18, 22, 27, 255))
    draw = ImageDraw.Draw(canvas)
    names = ["CONTACT","MID_CP","PUSH","MID_PL","LIFT","MID_LF","FLIGHT","MID_FR","REACH","MID_RL","LAND","MID_LC"]
    for i, frame in enumerate(frames):
        x = (i % 4) * CELL
        y = (i // 4) * CELL
        canvas.alpha_composite(frame, (x, y))
        draw.rectangle((x + 5, y + 5, x + 78, y + 21), fill=(0, 0, 0, 165))
        draw.text((x + 8, y + 8), names[i], fill=(245, 248, 250, 255))
    canvas.save(OUT / "p-mf12-flow-transfer-v1-review.png")

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = split_sheet(SOURCE, 3, 2, 6)
    donor = split_sheet(DONOR, 4, 3, 12)

    frames = []
    metrics = []
    for i in range(12):
        if i % 2 == 0:
            frame = source[i // 2].copy()
            metric = {"kind": "exact-production-keyframe"}
        else:
            frame, metric = warp_source_with_donor(source[i // 2], donor[i - 1], donor[i])
            metric["kind"] = "mf12-motion-field-transfer"
        metric["frame"] = i
        metric["components"] = component_count(frame)
        frames.append(frame)
        metrics.append(metric)

    sheet = Image.new("RGBA", (CELL * 4, CELL * 3), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        sheet.alpha_composite(frame, ((i % 4) * CELL, (i // 4) * CELL))
    candidate_path = OUT / "p-run-sheet-mf12-flow-transfer-v1.webp"
    sheet.save(candidate_path, "WEBP", lossless=True, method=6)

    public_candidate = ROOT / "public" / "concept" / "p-run-sheet-mf12-flow-transfer-v1.webp"
    public_candidate.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(public_candidate, "WEBP", lossless=True, method=6)

    make_review(frames)

    gif_frames = []
    for frame in frames:
        bg = Image.new("RGB", (CELL, CELL), (18, 22, 27))
        bg.paste(frame, mask=frame.getchannel("A"))
        gif_frames.append(bg)
    gif_frames[0].save(
        OUT / "p-mf12-flow-transfer-v1-loop.gif",
        save_all=True,
        append_images=gif_frames[1:],
        duration=72,
        loop=0,
        disposal=2,
    )

    report = {
        "appearance_source": "public/concept/p-run-sheet.webp",
        "motion_source": "art/2p5d/motion-donors/p-mf12-v1.webp",
        "new_motion_created": False,
        "method": "existing mf12 donor optical-flow field transferred onto exact production P pixels; no frame blending",
        "production_modified": False,
        "frames": metrics,
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
