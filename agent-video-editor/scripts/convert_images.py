#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

IMAGE_EXTS = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def register_heif() -> bool:
    try:
        import pillow_heif
    except ImportError:
        return False
    pillow_heif.register_heif_opener()
    return True


def require_pillow():
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise SystemExit("Pillow is required. Install with: python3 -m pip install pillow") from exc
    return Image, ImageOps


def safe_name(path: Path) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in path.name)


def convert_one(src: Path, input_root: Path, output_root: Path, fmt: str, max_side: int | None) -> Path:
    Image, ImageOps = require_pillow()
    rel_parent = src.parent.relative_to(input_root)
    out_dir = output_root / rel_parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{safe_name(src)}.{fmt.lower()}"

    with Image.open(src) as image:
        image = ImageOps.exif_transpose(image)
        if max_side:
            image.thumbnail((max_side, max_side))
        if fmt.upper() in {"JPEG", "JPG"}:
            image = image.convert("RGB")
            image.save(out, "JPEG", quality=94)
        else:
            image.convert("RGB").save(out, fmt.upper())
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert mobile/special images to stable PNG or JPEG assets.")
    parser.add_argument("input_dir", nargs="?", default="raw", help="Directory containing source images")
    parser.add_argument("--out-dir", default="converted", help="Output directory")
    parser.add_argument("--format", choices=["png", "jpeg"], default="png", help="Output image format")
    parser.add_argument("--max-side", type=int, default=None, help="Optional max width/height")
    parser.add_argument("--recursive", action="store_true", help="Scan subdirectories")
    args = parser.parse_args()

    root = Path.cwd()
    src_dir = root / args.input_dir
    out_dir = root / args.out_dir
    heif_ready = register_heif()
    pattern = "**/*" if args.recursive else "*"
    converted = 0

    for src in sorted(src_dir.glob(pattern)):
        if not src.is_file() or src.suffix.lower() not in IMAGE_EXTS:
            continue
        if src.suffix.lower() in {".heic", ".heif"} and not heif_ready:
            print(f"Skipped HEIC/HEIF without pillow-heif: {src}")
            continue
        out = convert_one(src, src_dir, out_dir, args.format, args.max_side)
        print(f"{src} -> {out}")
        converted += 1
    print(f"Converted {converted} images")


if __name__ == "__main__":
    main()
