#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run(cmd, check=True)


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        text=True,
    ).strip()
    return float(out or 0)


def require_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise SystemExit("Pillow is required. Install with: python3 -m pip install pillow") from exc
    return Image, ImageDraw, ImageFont


class Builder:
    def __init__(self, root: Path, plan: dict, project_name: str, raw_dir: str | None, output: Path):
        self.root = root
        self.plan = plan
        self.w = int(plan.get("width", 1080))
        self.h = int(plan.get("height", 1920))
        self.fps = int(plan.get("fps", 30))
        self.raw = root / (raw_dir or plan.get("raw_dir", "raw"))
        self.converted_heic = root / plan.get("converted_heic_dir", "converted-heic")
        self.build = root / plan.get("build_dir", f"build/{project_name}")
        self.segments_dir = self.build / "segments"
        self.captioned_dir = self.build / "captioned"
        self.overlays_dir = self.build / "overlays"
        self.concat_file = self.build / "concat.txt"
        self.output = output
        self.font_file = plan.get("font_file") or self.default_font()

    def default_font(self) -> str:
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
        raise SystemExit("No usable font found. Set font_file in the shot plan.")

    def media_path(self, name: str) -> Path:
        direct = self.root / name
        raw = self.raw / name
        if name.lower().endswith(".heic"):
            converted = self.converted_heic / f"{Path(name).name}.png"
            if converted.exists():
                return converted
        if raw.exists():
            return raw
        return direct

    def prepare(self) -> None:
        if self.build.exists():
            shutil.rmtree(self.build)
        self.segments_dir.mkdir(parents=True, exist_ok=True)
        self.captioned_dir.mkdir(parents=True, exist_ok=True)
        self.overlays_dir.mkdir(parents=True, exist_ok=True)
        self.output.parent.mkdir(parents=True, exist_ok=True)

    def vf_video(self) -> str:
        return (
            f"scale={self.w}:{self.h}:force_original_aspect_ratio=increase,"
            f"crop={self.w}:{self.h},setsar=1,fps={self.fps},format=yuv420p"
        )

    def vf_image(self) -> str:
        bg = (
            f"[0:v]scale={self.w}:{self.h}:force_original_aspect_ratio=increase,"
            f"crop={self.w}:{self.h},gblur=sigma=35,eq=brightness=-0.08:saturation=0.9[bg]"
        )
        fg = f"[0:v]scale={self.w - 80}:{self.h - 120}:force_original_aspect_ratio=decrease[fg]"
        over = f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps={self.fps},format=yuv420p"
        return ";".join([bg, fg, over])

    def font(self, size: int) -> ImageFont.FreeTypeFont:
        _, _, ImageFont = require_pillow()
        return ImageFont.truetype(self.font_file, size=size)

    def text_width(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
        if not text:
            return 0
        box = draw.textbbox((0, 0), text, font=font)
        return box[2] - box[0]

    def wrap_to_width(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        lines: list[str] = []
        for raw in text.splitlines():
            if not raw:
                lines.append("")
                continue
            current = ""
            for ch in raw:
                trial = current + ch
                if current and self.text_width(draw, trial, font) > max_width:
                    lines.append(current)
                    current = ch
                else:
                    current = trial
            if current:
                lines.append(current)
        return lines

    def draw_centered(self, draw: ImageDraw.ImageDraw, lines: list[str], font: ImageFont.FreeTypeFont, y: int, size_gap: int) -> None:
        heights = []
        for line in lines:
            box = draw.textbbox((0, 0), line or " ", font=font, stroke_width=2)
            heights.append(box[3] - box[1])
        total = sum(heights) + size_gap * max(0, len(lines) - 1)
        cursor = y - total // 2
        for line, height in zip(lines, heights):
            x = (self.w - self.text_width(draw, line, font)) // 2
            draw.text((x, cursor), line, font=font, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 220))
            cursor += height + size_gap

    def make_overlay(self, index: int, item: dict) -> Path | None:
        text = item.get("caption") or item.get("card")
        if not text:
            return None
        Image, ImageDraw, _ = require_pillow()
        image = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        out = self.overlays_dir / f"{index:02d}.png"

        if item.get("card"):
            title, _, body = text.partition("\n\n")
            title_font = self.font(76)
            body_font = self.font(48)
            lines = self.wrap_to_width(draw, body, body_font, self.w - 220)
            line_h = 66
            block_h = 120 + len(lines) * line_h
            top = max(120, (self.h - block_h) // 2)
            draw.rounded_rectangle((72, top - 54, self.w - 72, top + block_h + 54), radius=34, fill=(22, 28, 34, 235))
            self.draw_centered(draw, [title], title_font, top + 30, 0)
            y = top + 120
            for line in lines:
                if not line:
                    y += 20
                    continue
                draw.text((128, y), line, font=body_font, fill=(242, 245, 248, 255))
                y += line_h
        elif str(item.get("style", "")).lower() == "title":
            title_font = self.font(72)
            lines = self.wrap_to_width(draw, text, title_font, self.w - 160)
            block_h = len(lines) * 92 + 56
            y0 = self.h // 2 - block_h // 2
            draw.rounded_rectangle((76, y0, self.w - 76, y0 + block_h), radius=30, fill=(0, 0, 0, 150))
            self.draw_centered(draw, lines, title_font, self.h // 2, 18)
        else:
            caption_font = self.font(56)
            lines = self.wrap_to_width(draw, text, caption_font, self.w - 180)
            block_h = len(lines) * 72 + 44
            y0 = self.h - block_h - 150
            draw.rounded_rectangle((70, y0, self.w - 70, y0 + block_h), radius=26, fill=(0, 0, 0, 158))
            self.draw_centered(draw, lines, caption_font, y0 + block_h // 2, 12)

        image.save(out)
        return out

    def render_segment(self, index: int, item: dict) -> Path:
        kind = item["kind"]
        dur = float(item["dur"])
        out = self.segments_dir / f"{index:02d}.mp4"
        common = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]

        if kind == "video":
            run([
                *common,
                "-ss", str(item.get("start", 0)),
                "-t", str(dur),
                "-i", str(self.media_path(item["file"])),
                "-map", "0:v:0",
                "-an",
                "-vf", self.vf_video(),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                str(out),
            ])
        elif kind == "image":
            run([
                *common,
                "-loop", "1",
                "-t", str(dur),
                "-i", str(self.media_path(item["file"])),
                "-map", "0:v:0",
                "-filter_complex", self.vf_image(),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                str(out),
            ])
        elif kind == "card":
            run([
                *common,
                "-f", "lavfi",
                "-i", f"color=c=0x12171c:s={self.w}x{self.h}:r={self.fps}:d={dur}",
                "-vf", "format=yuv420p",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "18",
                "-t", str(dur),
                str(out),
            ])
        else:
            raise ValueError(f"Unsupported segment kind: {kind}")

        return self.apply_overlay(index, out, item)

    def apply_overlay(self, index: int, base: Path, item: dict) -> Path:
        overlay = self.make_overlay(index, item)
        if overlay is None:
            return base
        out = self.captioned_dir / f"{index:02d}.mp4"
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(base),
            "-loop", "1",
            "-i", str(overlay),
            "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p",
            "-t", str(item["dur"]),
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            str(out),
        ])
        return out

    def build_video(self) -> None:
        self.prepare()
        paths = [self.render_segment(i + 1, item) for i, item in enumerate(self.plan["segments"])]
        self.concat_file.write_text(
            "".join(f"file '{path.relative_to(self.concat_file.parent).as_posix()}'\n" for path in paths),
            encoding="utf-8",
        )
        total = sum(ffprobe_duration(path) for path in paths)
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat",
            "-safe", "0",
            "-i", str(self.concat_file),
            "-f", "lavfi",
            "-t", f"{total:.3f}",
            "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-vf", f"fps={self.fps},format=yuv420p",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            str(self.output),
        ])
        print(f"Wrote {self.output}")
        print(f"Duration target: {total:.3f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a vertical vlog from a JSON shot plan.")
    parser.add_argument("--plan", required=True, help="Path to shot-plan JSON")
    parser.add_argument("--project-name", default="vlog", help="Name used for build directory when plan omits build_dir")
    parser.add_argument("--raw-dir", default=None, help="Raw media directory relative to project root")
    parser.add_argument("--output", required=True, help="Output MP4 path")
    args = parser.parse_args()

    root = Path.cwd()
    plan_path = root / args.plan
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    builder = Builder(root, plan, args.project_name, args.raw_dir, root / args.output)
    builder.build_video()


if __name__ == "__main__":
    main()
