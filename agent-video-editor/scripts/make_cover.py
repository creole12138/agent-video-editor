#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}


def default_font() -> str:
    candidates = [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise SystemExit("No usable font found. Pass --font-file.")


def require_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except ImportError as exc:
        raise SystemExit("Pillow is required. Install with: python3 -m pip install pillow") from exc
    return Image, ImageDraw, ImageFont, ImageOps


def extract_frame(src: Path, at: str, tmp: Path) -> Path:
    out = tmp / "cover_frame.jpg"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            at,
            "-i",
            str(src),
            "-frames:v",
            "1",
            str(out),
        ],
        check=True,
    )
    return out


def cover_crop(image: Image.Image, width: int, height: int) -> Image.Image:
    _, _, _, ImageOps = require_pillow()
    image = ImageOps.exif_transpose(image).convert("RGB")
    scale = max(width / image.width, height / image.height)
    resized = image.resize((int(image.width * scale), int(image.height * scale)))
    x = (resized.width - width) // 2
    y = (resized.height - height) // 2
    return resized.crop((x, y, x + width, y + height))


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines = []
    for raw in text.splitlines():
        current = ""
        for ch in raw:
            trial = current + ch
            if current and draw.textlength(trial, font=font) > max_width:
                lines.append(current)
                current = ch
            else:
                current = trial
        if current:
            lines.append(current)
    return lines


def draw_cover(base: Image.Image, title: str, subtitle: str, font_file: str, out: Path) -> None:
    Image, ImageDraw, ImageFont, _ = require_pillow()
    draw = ImageDraw.Draw(base)
    width, height = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, int(height * 0.52), width, height), fill=(0, 0, 0, 125))
    base = Image.alpha_composite(base.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(base)

    title_font = ImageFont.truetype(font_file, 92)
    subtitle_font = ImageFont.truetype(font_file, 42)
    title_lines = wrap_text(draw, title, title_font, width - 140)[:3]
    y = int(height * 0.58)
    for line in title_lines:
        draw.text((70, y), line, font=title_font, fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0, 230))
        y += 108
    if subtitle:
        for line in wrap_text(draw, subtitle, subtitle_font, width - 140)[:2]:
            draw.text((74, y + 16), line, font=subtitle_font, fill=(238, 241, 245, 255), stroke_width=2, stroke_fill=(0, 0, 0, 220))
            y += 56
    out.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(out, quality=94)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a vertical short-video cover image.")
    parser.add_argument("source", help="Source image or video")
    parser.add_argument("--title", required=True, help="Large cover title")
    parser.add_argument("--subtitle", default="", help="Small supporting line")
    parser.add_argument("--at", default="00:00:03", help="Timestamp for video frame extraction")
    parser.add_argument("--output", default="output/cover.jpg", help="Cover output path")
    parser.add_argument("--font-file", default=None, help="Font path")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    args = parser.parse_args()

    src = Path(args.source)
    font_file = args.font_file or default_font()
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        frame = extract_frame(src, args.at, tmp) if src.suffix.lower() in VIDEO_EXTS else src
        Image, _, _, _ = require_pillow()
        with Image.open(frame) as image:
            base = cover_crop(image, args.width, args.height)
        draw_cover(base, args.title, args.subtitle, font_file, Path(args.output))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
