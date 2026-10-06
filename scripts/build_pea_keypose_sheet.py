#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "artifacts" / "pea-keypose-capture" / "raw"
OUT = ROOT / "artifacts" / "pea-keypose-capture"
PHASES = ["CONTACT", "PUSH", "LIFT", "FLIGHT", "REACH", "LAND"]
CELL = 256
SHEET_W = CELL * 3
SHEET_H = CELL * 2

def alpha_bbox(img):
    rgba = img.convert("RGBA")
    alpha = rgba.getchannel("A")
    # Ignore very faint antialiasing noise.
    mask = alpha.point(lambda a: 255 if a > 10 else 0)
    return mask.getbbox()

def normalized_frame(path):
    img = Image.open(path).convert("RGBA")
    bbox = alpha_bbox(img)
    if not bbox:
        raise RuntimeError(f"no visible pixels in {path}")
    crop = img.crop(bbox)
    max_w, max_h = 238, 232
    scale = min(max_w / crop.width, max_h / crop.height)
    size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
    crop = crop.resize(size, Image.Resampling.LANCZOS)

    cell = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    # Side-on gait: horizontal center; foot line aligned near cell bottom.
    x = (CELL - crop.width) // 2
    y = 244 - crop.height
    cell.alpha_composite(crop, (x, y))
    return cell, {
        "source_bbox": list(bbox),
        "normalized_size": list(size),
        "paste": [x, y],
    }

def make_sheet(morph):
    frames = []
    metrics = []
    for i, phase in enumerate(PHASES):
        frame, metric = normalized_frame(RAW / f"{morph.lower()}-{i}.png")
        frames.append(frame)
        metrics.append({"phase": phase, **metric})

    sheet = Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        x = (i % 3) * CELL
        y = (i // 3) * CELL
        sheet.alpha_composite(frame, (x, y))

    webp = OUT / f"{morph.lower()}-run-sheet-mf-keypose-v1.webp"
    sheet.save(webp, "WEBP", lossless=True, method=6)

    contact = Image.new("RGBA", (SHEET_W, SHEET_H), (18, 22, 27, 255))
    for i, frame in enumerate(frames):
        x = (i % 3) * CELL
        y = (i // 3) * CELL
        contact.alpha_composite(frame, (x, y))
    draw = ImageDraw.Draw(contact)
    for i, phase in enumerate(PHASES):
        x = (i % 3) * CELL + 8
        y = (i // 3) * CELL + 8
        draw.rectangle((x - 3, y - 3, x + 72, y + 14), fill=(0, 0, 0, 150))
        draw.text((x, y), phase, fill=(245, 248, 250, 255))
    contact.save(OUT / f"{morph.lower()}-keyposes.png")

    current = Image.open(ROOT / "public" / "concept" / f"{morph.lower()}-run-sheet.webp").convert("RGBA")
    current = current.resize((768, 512), Image.Resampling.LANCZOS)
    compare = Image.new("RGBA", (1536, 512), (15, 18, 22, 255))
    compare.alpha_composite(current, (0, 0))
    compare.alpha_composite(contact, (768, 0))
    compare.save(OUT / f"{morph.lower()}-current-vs-mf-keypose.png")

    # Short loop only for visual review. No interpolation.
    gif_frames = []
    for frame in frames:
        bg = Image.new("RGB", (CELL, CELL), (18, 22, 27))
        bg.paste(frame, mask=frame.getchannel("A"))
        gif_frames.append(bg)
    gif_frames[0].save(
        OUT / f"{morph.lower()}-mf-keypose-loop.gif",
        save_all=True,
        append_images=gif_frames[1:],
        duration=[105, 115, 95, 90, 105, 110],
        loop=0,
        disposal=2,
    )

    return metrics

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    import json
    report = {
        "method": "Motion First canonical procedural gait; six direct keypose renders; no interpolation",
        "phases": PHASES,
        "morphs": {}
    }
    for morph in ["P", "E", "A"]:
        report["morphs"][morph] = make_sheet(morph)
    (OUT / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("generated Motion First P/E/A keypose candidates")

if __name__ == "__main__":
    main()
