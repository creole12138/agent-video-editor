#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff"}


def run(cmd: list[str]) -> bool:
    result = subprocess.run(cmd, check=False)
    return result.returncode == 0


def duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return float(result.stdout.strip() or 0)
    except ValueError:
        return 0.0


def safe_stem(path: Path) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in path.stem)


def frame_times(path: Path, requested: list[float]) -> list[float]:
    dur = duration(path)
    if dur <= 0:
        return requested
    usable = []
    for t in requested:
        if t < dur:
            usable.append(t)
    if not usable:
        usable = [max(0.0, dur * 0.5)]
    return usable


def make_video_frames(path: Path, root: Path, out_dir: Path, times: list[float], scale: int) -> int:
    count = 0
    for t in frame_times(path, times):
        out = out_dir / f"{safe_stem(path)}_{int(t * 1000):06d}ms.jpg"
        ok = run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{t:.3f}",
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-vf",
                f"scale={scale}:-1",
                str(out),
            ]
        )
        if ok:
            count += 1
    return count


def make_image_thumb(path: Path, out_dir: Path, scale: int) -> int:
    out = out_dir / f"{safe_stem(path)}_image.jpg"
    ok = run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-vf",
            f"scale={scale}:-1",
            str(out),
        ]
    )
    return 1 if ok else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract review keyframes from raw video and image media.")
    parser.add_argument("input_dir", nargs="?", default="raw", help="Directory containing source media")
    parser.add_argument("--out-dir", default="build/edit/keyframes", help="Output keyframe directory")
    parser.add_argument("--times", default="3,10", help="Comma-separated seconds for videos")
    parser.add_argument("--scale", type=int, default=540, help="Output frame width")
    parser.add_argument("--recursive", action="store_true", help="Scan subdirectories")
    args = parser.parse_args()

    root = Path.cwd()
    src = root / args.input_dir
    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    times = [float(x.strip()) for x in args.times.split(",") if x.strip()]
    pattern = "**/*" if args.recursive else "*"

    written = 0
    for path in sorted(src.glob(pattern)):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in VIDEO_EXTS:
            written += make_video_frames(path, root, out_dir, times, args.scale)
        elif suffix in IMAGE_EXTS:
            written += make_image_thumb(path, out_dir, args.scale)
    print(f"Wrote {written} keyframe images to {out_dir}")


if __name__ == "__main__":
    main()
