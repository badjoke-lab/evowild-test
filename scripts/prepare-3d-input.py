from __future__ import annotations

from collections import deque
from pathlib import Path
from PIL import Image
import argparse
import json
import math


def is_background_pixel(r: int, g: int, b: int, a: int, threshold: int) -> bool:
    if a == 0:
        return True
    # Background is neutral near-white. Requiring low channel spread keeps
    # cyan/blue/silver body highlights even when they are bright.
    spread = max(r, g, b) - min(r, g, b)
    return min(r, g, b) >= threshold and spread <= 12


def remove_edge_connected_background(im: Image.Image, threshold: int = 242) -> Image.Image:
    rgba = im.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    visited = bytearray(w * h)
    q: deque[tuple[int, int]] = deque()

    def enqueue(x: int, y: int) -> None:
        idx = y * w + x
        if visited[idx]:
            return
        visited[idx] = 1
        r, g, b, a = px[x, y]
        if is_background_pixel(r, g, b, a, threshold):
            q.append((x, y))

    for x in range(w):
        enqueue(x, 0)
        enqueue(x, h - 1)
    for y in range(h):
        enqueue(0, y)
        enqueue(w - 1, y)

    while q:
        x, y = q.popleft()
        r, g, b, _ = px[x, y]
        px[x, y] = (r, g, b, 0)
        if x > 0:
            enqueue(x - 1, y)
        if x + 1 < w:
            enqueue(x + 1, y)
        if y > 0:
            enqueue(x, y - 1)
        if y + 1 < h:
            enqueue(x, y + 1)

    return rgba


def alpha_bbox(im: Image.Image) -> tuple[int, int, int, int]:
    alpha = im.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        raise RuntimeError("No foreground remains after edge-connected background removal")
    return bbox


def prepare(src: Path, dst: Path, *, left_crop_ratio: float, canvas_size: int, fill_ratio: float, threshold: int) -> dict:
    im = Image.open(src).convert("RGBA")
    original_size = im.size

    if left_crop_ratio > 0:
        crop_x = int(round(im.width * left_crop_ratio))
        im = im.crop((crop_x, 0, im.width, im.height))

    cleaned = remove_edge_connected_background(im, threshold=threshold)
    bbox = alpha_bbox(cleaned)
    subject = cleaned.crop(bbox)

    max_subject = int(round(canvas_size * fill_ratio))
    scale = min(max_subject / subject.width, max_subject / subject.height)
    new_size = (
        max(1, int(round(subject.width * scale))),
        max(1, int(round(subject.height * scale))),
    )
    subject = subject.resize(new_size, Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 0))
    x = (canvas_size - subject.width) // 2
    y = (canvas_size - subject.height) // 2
    canvas.alpha_composite(subject, (x, y))

    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst)

    alpha = canvas.getchannel("A")
    opaque = sum(1 for v in alpha.getdata() if v > 0)
    total = canvas_size * canvas_size
    result = {
        "source": str(src),
        "destination": str(dst),
        "original_size": list(original_size),
        "post_left_crop_size": list(im.size),
        "source_foreground_bbox": list(bbox),
        "subject_size_before_resize": list(cleaned.crop(bbox).size),
        "subject_size_after_resize": list(new_size),
        "canvas_size": [canvas_size, canvas_size],
        "fill_ratio_requested": fill_ratio,
        "left_crop_ratio": left_crop_ratio,
        "background_threshold": threshold,
        "nontransparent_fraction": round(opaque / total, 6),
        "method": "edge_connected_neutral_white_flood_fill",
    }
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("--left-crop-ratio", type=float, default=0.30)
    ap.add_argument("--canvas-size", type=int, default=1024)
    ap.add_argument("--fill-ratio", type=float, default=0.90)
    ap.add_argument("--threshold", type=int, default=242)
    ap.add_argument("--metadata", type=Path)
    args = ap.parse_args()

    result = prepare(
        args.src,
        args.dst,
        left_crop_ratio=args.left_crop_ratio,
        canvas_size=args.canvas_size,
        fill_ratio=args.fill_ratio,
        threshold=args.threshold,
    )
    if args.metadata:
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
