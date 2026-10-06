#!/usr/bin/env python3
from pathlib import Path
import os
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
RAW = Path(os.environ.get("PEA_KEYPOSE_RAW_DIR", "/tmp/pea-keypose-capture/raw"))
OUT = ROOT / "artifacts" / "pea-keypose-capture"
PHASES = ["CONTACT", "MID_CP", "PUSH", "MID_PL", "LIFT", "MID_LF", "FLIGHT", "MID_FR", "REACH", "MID_RL", "LAND", "MID_LC"]
CELL = 256
SHEET_W = CELL * 4
SHEET_H = CELL * 3

def remove_chroma(img):
    rgba = img.convert("RGBA")
    out = []
    for r, g, b, _ in rgba.getdata():
        dominance = g - max(r, b)
        if g >= 245 and r <= 18 and b <= 18:
            a = 0
        elif dominance >= 150:
            a = 0
        elif dominance >= 70:
            a = round(255 * (150 - dominance) / 80)
        else:
            a = 255
        out.append((r, g, b, a))
    rgba.putdata(out)
    return rgba

def alpha_bbox(img):
    rgba = remove_chroma(img)
    alpha = rgba.getchannel("A")
    # Ignore very faint antialiasing noise.
    mask = alpha.point(lambda a: 255 if a > 10 else 0)
    return mask.getbbox()

def normalized_frame(path):
    img = remove_chroma(Image.open(path))
    bbox = img.getchannel("A").point(lambda a: 255 if a > 10 else 0).getbbox()
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
        x = (i % 4) * CELL
        y = (i // 4) * CELL
        sheet.alpha_composite(frame, (x, y))

    webp = OUT / f"{morph.lower()}-run-sheet-mf12-v1.webp"
    sheet.save(webp, "WEBP", lossless=True, method=6)

    contact = Image.new("RGBA", (SHEET_W, SHEET_H), (18, 22, 27, 255))
    for i, frame in enumerate(frames):
        x = (i % 4) * CELL
        y = (i // 4) * CELL
        contact.alpha_composite(frame, (x, y))
    draw = ImageDraw.Draw(contact)
    for i, phase in enumerate(PHASES):
        x = (i % 4) * CELL + 8
        y = (i // 4) * CELL + 8
        draw.rectangle((x - 3, y - 3, x + 92, y + 14), fill=(0, 0, 0, 150))
        draw.text((x, y), phase, fill=(245, 248, 250, 255))
    contact.save(OUT / f"{morph.lower()}-mf12-poses.png")

    # Six semantic key poses are the even samples.
    semantic = [frames[i] for i in [0,2,4,6,8,10]]
    semantic_sheet = Image.new("RGBA", (768, 512), (18, 22, 27, 255))
    semantic_names = ["CONTACT","PUSH","LIFT","FLIGHT","REACH","LAND"]
    sem_draw = ImageDraw.Draw(semantic_sheet)
    for i, frame in enumerate(semantic):
        x = (i % 3) * 256
        y = (i // 3) * 256
        semantic_sheet.alpha_composite(frame, (x, y))
        sem_draw.rectangle((x+5,y+5,x+82,y+22), fill=(0,0,0,150))
        sem_draw.text((x+8,y+8),semantic_names[i],fill=(245,248,250,255))
    semantic_sheet.save(OUT / f"{morph.lower()}-keyposes.png")

    current = Image.open(ROOT / "public" / "concept" / f"{morph.lower()}-run-sheet.webp").convert("RGBA")
    current = current.resize((768, 512), Image.Resampling.LANCZOS)
    compare = Image.new("RGBA", (1536, 512), (15, 18, 22, 255))
    compare.alpha_composite(current, (0, 0))
    compare.alpha_composite(semantic_sheet, (768, 0))
    compare.save(OUT / f"{morph.lower()}-current-vs-mf-keypose.png")

    # 12 direct gait states; no image interpolation.
    gif_frames = []
    for frame in frames:
        bg = Image.new("RGB", (CELL, CELL), (18, 22, 27))
        bg.paste(frame, mask=frame.getchannel("A"))
        gif_frames.append(bg)
    gif_frames[0].save(
        OUT / f"{morph.lower()}-mf12-loop.gif",
        save_all=True,
        append_images=gif_frames[1:],
        duration=65,
        loop=0,
        disposal=2,
    )

    return metrics

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    import json
    report = {
        "method": "Motion First canonical procedural gait; twelve direct renders; no image interpolation",
        "phases": PHASES,
        "morphs": {}
    }
    for morph in ["P", "E", "A"]:
        report["morphs"][morph] = make_sheet(morph)
    (OUT / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("generated Motion First P/E/A keypose candidates")

if __name__ == "__main__":
    main()
