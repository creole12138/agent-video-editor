#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff"}


def ffprobe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip() or "ffprobe failed"}
    return json.loads(result.stdout or "{}")


def display_size(stream: dict) -> tuple[int | None, int | None, int]:
    width = stream.get("width")
    height = stream.get("height")
    rotate = 0
    tags = stream.get("tags") or {}
    side_data = stream.get("side_data_list") or []
    if tags.get("rotate"):
        try:
            rotate = int(float(tags["rotate"]))
        except ValueError:
            rotate = 0
    for item in side_data:
        if "rotation" in item:
            try:
                rotate = int(float(item["rotation"]))
            except ValueError:
                pass
    if width and height and abs(rotate) in (90, 270):
        return int(height), int(width), rotate
    return int(width) if width else None, int(height) if height else None, rotate


def inspect_file(path: Path, root: Path) -> dict:
    suffix = path.suffix.lower()
    item = {
        "file": path.relative_to(root).as_posix(),
        "kind": "video" if suffix in VIDEO_EXTS else "image" if suffix in IMAGE_EXTS else "other",
        "ext": suffix,
        "size_bytes": path.stat().st_size,
    }
    if item["kind"] == "other":
        return item

    probe = ffprobe(path)
    if "error" in probe:
        item["error"] = probe["error"]
        return item

    fmt = probe.get("format") or {}
    streams = probe.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    if fmt.get("duration"):
        try:
            item["duration"] = round(float(fmt["duration"]), 3)
        except ValueError:
            pass
    if video:
        width, height, rotate = display_size(video)
        item.update(
            {
                "codec": video.get("codec_name"),
                "width": width,
                "height": height,
                "rotation": rotate,
                "fps": video.get("avg_frame_rate"),
            }
        )
    item["audio_streams"] = len(audio)
    if suffix in {".heic", ".heif"}:
        item["note"] = "Convert to PNG first if color, brightness, or orientation looks wrong."
    return item


def write_markdown(items: list[dict], out: Path) -> None:
    lines = [
        "# Media Inspection",
        "",
        "| File | Kind | Duration | Size | Rotation | Audio | Notes |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in items:
        size = ""
        if item.get("width") and item.get("height"):
            size = f"{item['width']}x{item['height']}"
        duration = item.get("duration", "")
        rotation = item.get("rotation", "")
        audio = item.get("audio_streams", "")
        note = item.get("note") or item.get("error") or ""
        lines.append(
            f"| `{item['file']}` | {item['kind']} | {duration} | {size} | {rotation} | {audio} | {note} |"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect raw media and write a reusable media manifest.")
    parser.add_argument("input_dir", nargs="?", default="raw", help="Directory containing raw media")
    parser.add_argument("--json", default="build/edit/media_manifest.json", help="Output JSON manifest")
    parser.add_argument("--md", default="build/edit/media_manifest.md", help="Output Markdown table")
    parser.add_argument("--recursive", action="store_true", help="Scan subdirectories")
    args = parser.parse_args()

    root = Path.cwd()
    src = root / args.input_dir
    if not src.exists():
        raise SystemExit(f"Input directory not found: {src}")

    pattern = "**/*" if args.recursive else "*"
    files = [p for p in sorted(src.glob(pattern)) if p.is_file()]
    items = [inspect_file(path, root) for path in files]

    json_out = root / args.json
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(items, root / args.md)
    print(f"Inspected {len(items)} files")
    print(f"Wrote {json_out}")
    print(f"Wrote {root / args.md}")


if __name__ == "__main__":
    main()
