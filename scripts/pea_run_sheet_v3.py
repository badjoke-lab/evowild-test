from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "public" / "concept"
OUT_DIR = ROOT / "artifacts" / "pea-run-sheet-v3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PHASES = ["CONTACT", "PUSH", "LIFT", "FLIGHT", "REACH", "LAND"]
TARGET_FOOT_Y = {
    "CONTACT": 220,
    "PUSH": 220,
    "LIFT": 211,
    "FLIGHT": 199,
    "REACH": 205,
    "LAND": 220,
}


def split_sheet(path: Path) -> list[np.ndarray]:
    image = Image.open(path).convert("RGBA")
    fw = image.width // 3
    fh = image.height // 2
    frames = []
    for row in range(2):
        for col in range(3):
            crop = image.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh))
            frames.append(np.asarray(crop).copy())
    return frames


def clean_connected(frame: np.ndarray) -> tuple[np.ndarray, dict]:
    alpha = frame[:, :, 3]
    mask = (alpha > 12).astype(np.uint8)
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)

    if count <= 1:
        return frame.copy(), {"component_area": 0}

    h, w = mask.shape
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return frame.copy(), {"component_area": 0}

    cx = w * 0.5
    cy = h * 0.48
    nearest_idx = np.argmin((xs - cx) ** 2 + (ys - cy) ** 2)
    seed_label = int(labels[int(ys[nearest_idx]), int(xs[nearest_idx])])

    if seed_label <= 0:
        areas = stats[1:, cv2.CC_STAT_AREA]
        seed_label = 1 + int(np.argmax(areas))

    keep = labels == seed_label
    cleaned = frame.copy()
    cleaned[~keep] = 0

    yy, xx = np.nonzero(keep)
    if len(xx) == 0:
        return cleaned, {"component_area": 0}

    metrics = {
        "component_area": int(len(xx)),
        "min_x": int(xx.min()),
        "max_x": int(xx.max()),
        "min_y": int(yy.min()),
        "max_y": int(yy.max()),
    }
    return cleaned, metrics


def foot_y(mask: np.ndarray) -> int:
    h, w = mask.shape
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return h - 1
    central = (xs >= int(w * 0.18)) & (xs <= int(w * 0.88))
    if np.any(central):
        return int(ys[central].max())
    return int(ys.max())


def align_key(frame: np.ndarray, phase: str) -> tuple[np.ndarray, dict]:
    cleaned, metrics = clean_connected(frame)
    mask = cleaned[:, :, 3] > 12
    h, w = mask.shape
    ys, xs = np.nonzero(mask)

    if len(xs) == 0:
        return cleaned, {**metrics, "dx": 0, "dy": 0, "foot_y_before": h - 1}

    bbox_center_x = (float(xs.min()) + float(xs.max())) * 0.5
    dx = int(round(w * 0.5 - bbox_center_x))
    fy = foot_y(mask)
    dy = int(round(TARGET_FOOT_Y[phase] - fy))

    matrix = np.float32([[1, 0, dx], [0, 1, dy]])
    aligned = cv2.warpAffine(
        cleaned,
        matrix,
        (w, h),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )

    aligned_mask = aligned[:, :, 3] > 12
    return aligned, {
        **metrics,
        "dx": dx,
        "dy": dy,
        "foot_y_before": fy,
        "foot_y_after": foot_y(aligned_mask),
    }


def optical_mid(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    h, w, _ = a.shape

    def gray(rgba: np.ndarray) -> np.ndarray:
        rgb = rgba[:, :, :3].astype(np.float32)
        alpha = rgba[:, :, 3:4].astype(np.float32) / 255.0
        composite = rgb * alpha
        return cv2.cvtColor(composite.astype(np.uint8), cv2.COLOR_RGB2GRAY)

    ga = gray(a)
    gb = gray(b)

    flow_ab = cv2.calcOpticalFlowFarneback(
        ga, gb, None, 0.5, 4, 21, 4, 7, 1.5, 0
    )
    flow_ba = cv2.calcOpticalFlowFarneback(
        gb, ga, None, 0.5, 4, 21, 4, 7, 1.5, 0
    )

    grid_x, grid_y = np.meshgrid(
        np.arange(w, dtype=np.float32),
        np.arange(h, dtype=np.float32),
    )

    map_ax = grid_x - flow_ab[:, :, 0] * 0.5
    map_ay = grid_y - flow_ab[:, :, 1] * 0.5
    map_bx = grid_x - flow_ba[:, :, 0] * 0.5
    map_by = grid_y - flow_ba[:, :, 1] * 0.5

    wa = cv2.remap(
        a, map_ax, map_ay, cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)
    )
    wb = cv2.remap(
        b, map_bx, map_by, cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)
    )

    af = wa[:, :, 3:4].astype(np.float32) / 255.0
    bf = wb[:, :, 3:4].astype(np.float32) / 255.0
    out_a = (af + bf) * 0.5
    premul = (
        wa[:, :, :3].astype(np.float32) * af
        + wb[:, :, :3].astype(np.float32) * bf
    ) * 0.5
    out_rgb = np.divide(
        premul,
        np.maximum(out_a, 1e-5),
        out=np.zeros_like(premul),
        where=out_a > 1e-5,
    )
    out = np.concatenate(
        [np.clip(out_rgb, 0, 255), np.clip(out_a * 255.0, 0, 255)],
        axis=2,
    ).astype(np.uint8)
    return out


def make_sequence(keys: list[np.ndarray]) -> list[np.ndarray]:
    sequence = []
    for i, frame in enumerate(keys):
        nxt = keys[(i + 1) % len(keys)]
        sequence.append(frame)
        sequence.append(optical_mid(frame, nxt))
    return sequence


def checker(size: tuple[int, int], step: int = 16) -> Image.Image:
    w, h = size
    bg = Image.new("RGB", size, (34, 38, 44))
    draw = ImageDraw.Draw(bg)
    for y in range(0, h, step):
        for x in range(0, w, step):
            if ((x // step) + (y // step)) % 2:
                draw.rectangle((x, y, x + step - 1, y + step - 1), fill=(48, 53, 60))
    return bg


def write_outputs(morph: str, keys: list[np.ndarray], sequence: list[np.ndarray], metrics: list[dict]) -> None:
    h, w, _ = sequence[0].shape

    sheet = Image.new("RGBA", (w * 4, h * 3), (0, 0, 0, 0))
    for i, arr in enumerate(sequence):
        sheet.alpha_composite(Image.fromarray(arr, "RGBA"), ((i % 4) * w, (i // 4) * h))
    sheet.save(
        OUT_DIR / f"{morph}-run-sheet-v3.webp",
        format="WEBP",
        lossless=True,
        method=6,
    )

    preview = checker((w * 4, h * 3))
    draw = ImageDraw.Draw(preview)
    labels = []
    for i, arr in enumerate(sequence):
        cell = checker((w, h))
        cell.paste(Image.fromarray(arr, "RGBA"), (0, 0), Image.fromarray(arr[:, :, 3], "L"))
        x = (i % 4) * w
        y = (i // 4) * h
        preview.paste(cell, (x, y))
        label = PHASES[i // 2] if i % 2 == 0 else f"{PHASES[i // 2]}→{PHASES[(i // 2 + 1) % 6]}"
        labels.append(label)
        draw.rectangle((x + 5, y + 5, x + 150, y + 23), fill=(0, 0, 0))
        draw.text((x + 9, y + 8), label, fill=(255, 255, 255))
    preview.save(OUT_DIR / f"{morph}-v3-preview.png")

    gif_frames = []
    for arr in sequence:
        frame = checker((w, h))
        rgba = Image.fromarray(arr, "RGBA")
        frame.paste(rgba, (0, 0), rgba)
        gif_frames.append(frame)
    gif_frames[0].save(
        OUT_DIR / f"{morph}-v3-motion.gif",
        save_all=True,
        append_images=gif_frames[1:],
        duration=62,
        loop=0,
        disposal=2,
    )

    payload = {
        "morph": morph.upper(),
        "source": f"public/concept/{morph}-run-sheet.webp",
        "key_phases": PHASES,
        "output_frames": 12,
        "layout": "4x3",
        "key_metrics": metrics,
        "preview_labels": labels,
    }
    (OUT_DIR / f"{morph}-v3-metrics.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    for morph in ("p", "e", "a"):
        source_frames = split_sheet(SOURCE_DIR / f"{morph}-run-sheet.webp")
        aligned = []
        metrics = []
        for phase, frame in zip(PHASES, source_frames):
            aligned_frame, frame_metrics = align_key(frame, phase)
            aligned.append(aligned_frame)
            metrics.append({"phase": phase, **frame_metrics})
        sequence = make_sequence(aligned)
        write_outputs(morph, aligned, sequence, metrics)

    print(f"generated P/E/A v3 candidates under {OUT_DIR}")


if __name__ == "__main__":
    main()
