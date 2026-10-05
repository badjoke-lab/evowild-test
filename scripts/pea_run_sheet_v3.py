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


def split_with_layout(image: Image.Image, cols: int, rows: int) -> list[np.ndarray]:
    fw = image.width // cols
    fh = image.height // rows
    frames = []
    for row in range(rows):
        for col in range(cols):
            crop = image.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh))
            frames.append(np.asarray(crop).copy())
    return frames


def layout_score(frames: list[np.ndarray]) -> float:
    scores = []
    for frame in frames:
        mask = (frame[:, :, 3] > 12).astype(np.uint8)
        total = int(mask.sum())
        if total <= 0:
            scores.append(-5.0)
            continue

        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        largest = 0 if count <= 1 else int(stats[1:, cv2.CC_STAT_AREA].max())
        integrity = largest / max(1, total)

        border = np.zeros_like(mask)
        border[:4, :] = 1
        border[-4:, :] = 1
        border[:, :4] = 1
        border[:, -4:] = 1
        border_touch = int((mask * border).sum()) / max(1, total)

        scores.append(integrity - border_touch * 3.0)
    return float(np.mean(scores))


def split_sheet(path: Path) -> tuple[list[np.ndarray], str, dict]:
    image = Image.open(path).convert("RGBA")
    candidates = {}
    for cols, rows in ((3, 2), (2, 3)):
        frames = split_with_layout(image, cols, rows)
        candidates[f"{cols}x{rows}"] = {
            "frames": frames,
            "score": layout_score(frames),
        }

    selected = max(candidates.items(), key=lambda item: item[1]["score"])
    layout_name, payload = selected
    metrics = {
        "source_width": image.width,
        "source_height": image.height,
        "layout_scores": {
            name: round(float(candidate["score"]), 6)
            for name, candidate in candidates.items()
        },
        "selected_layout": layout_name,
    }
    return payload["frames"], layout_name, metrics


def clean_connected(frame: np.ndarray) -> tuple[np.ndarray, dict]:
    alpha = frame[:, :, 3]
    mask = (alpha > 12).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)

    if count <= 1:
        return frame.copy(), {"component_area": 0, "kept_components": 0}

    areas = stats[1:, cv2.CC_STAT_AREA]
    main_label = 1 + int(np.argmax(areas))
    main_area = int(stats[main_label, cv2.CC_STAT_AREA])
    keep = labels == main_label
    kept_components = 1

    # Armor plates, horns and thin limbs can be real creature pixels even when
    # alpha gaps split them from the largest body component. Keep meaningful
    # components; discard only small image-generation debris.
    min_area = max(18, int(main_area * 0.012))
    for label in range(1, count):
        if label == main_label:
            continue
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area >= min_area:
            keep |= labels == label
            kept_components += 1

    cleaned = frame.copy()
    cleaned[~keep] = 0

    yy, xx = np.nonzero(keep)
    if len(xx) == 0:
        return cleaned, {"component_area": 0, "kept_components": 0}

    metrics = {
        "component_area": int(len(xx)),
        "main_component_area": main_area,
        "kept_components": kept_components,
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
    """Create one single-silhouette inbetween.

    Do not cross-dissolve the two creatures. Large P/E/A pose differences make
    bidirectional blending show double heads and limbs. Instead, warp only the
    outgoing key pose halfway toward the next key pose.
    """
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

    grid_x, grid_y = np.meshgrid(
        np.arange(w, dtype=np.float32),
        np.arange(h, dtype=np.float32),
    )
    map_x = grid_x - flow_ab[:, :, 0] * 0.5
    map_y = grid_y - flow_ab[:, :, 1] * 0.5

    warped = cv2.remap(
        a,
        map_x,
        map_y,
        cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )

    # Keep alpha as one body and remove very faint flow residue.
    alpha = warped[:, :, 3]
    alpha[alpha < 10] = 0
    warped[:, :, 3] = alpha
    warped[alpha == 0, :3] = 0
    return warped


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


def write_outputs(
    morph: str,
    keys: list[np.ndarray],
    sequence: list[np.ndarray],
    metrics: list[dict],
    source_layout: str,
    source_metrics: dict,
) -> None:
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
        "source_layout": source_layout,
        "source_metrics": source_metrics,
        "key_phases": PHASES,
        "output_frames": 12,
        "interpolation": "single-silhouette-forward-flow-v3b",
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
        source_path = SOURCE_DIR / f"{morph}-run-sheet.webp"
        source_frames, source_layout, source_metrics = split_sheet(source_path)
        aligned = []
        metrics = []
        for phase, frame in zip(PHASES, source_frames):
            aligned_frame, frame_metrics = align_key(frame, phase)
            aligned.append(aligned_frame)
            metrics.append({"phase": phase, **frame_metrics})
        sequence = make_sequence(aligned)
        write_outputs(
            morph,
            aligned,
            sequence,
            metrics,
            source_layout=source_layout,
            source_metrics=source_metrics,
        )

    print(f"generated P/E/A v3 candidates under {OUT_DIR}")


if __name__ == "__main__":
    main()
