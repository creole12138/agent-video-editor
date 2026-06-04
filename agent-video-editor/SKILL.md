---
name: agent-video-editor
description: End-to-end, tool-agnostic short-video editing workflow for agentic assistants such as Claude, Codex, or other coding agents. Use when an agent needs to inspect raw media, organize footage, create a shot plan, generate a 9:16 social-platform vlog or explainer with FFmpeg, convert HEIC/mobile photos, burn Chinese/English subtitles, generate title/info cards, apply privacy mosaic/blur, mix BGM or silent audio, validate output frames/duration, package deliverables, or write Xiaohongshu/Douyin/TikTok/Reels publishing copy.
---

# Agent Video Editor

## Purpose

Use this skill to turn raw media plus a script, brief, or shot list into a platform-ready short video. The workflow is designed for agent tools that can read files, run shell commands, write code, and inspect images, regardless of whether the host is Claude, Codex, or another assistant.

## Agent Operating Rules

- Treat original media as read-only. Write generated files under `build/`, `converted/`, and `output/`.
- Start by inspecting the project: list files, read the brief/script, probe media duration, and extract keyframes before editing.
- Use a structured shot plan as the source of truth. Prefer rebuilding from the plan over patching the final MP4.
- Keep all paths project-relative in generated docs and plans. Do not bake personal home directories into reusable files.
- Ask for clarification only when the missing decision changes the story, privacy treatment, or deliverable format.
- Validate visually: after export, inspect frames around hook, subtitles, cards, edits requested by timestamp, and ending.
- Report what changed, where the output is, and any limitations such as missing BGM or unavailable filters.

## Workflow

1. **Set up the workspace**
   - Read `references/setup.md` for tools, folders, and fonts.
   - Use `raw/`, `converted/`, `build/edit/`, `output/`, and `publish-copy.md`.
2. **Inspect media**
   - List files with `find` or `rg --files`.
   - Run `scripts/inspect_media.py` to capture duration, dimensions, rotation, audio streams, and HEIC notes.
   - Run `scripts/make_keyframes.py` to review keyframes quickly before planning.
3. **Plan the edit**
   - Convert the user's script into a shot list.
   - Use the JSON schema in `references/shot-plan-format.md`.
   - Put hook, context, info, action, conclusion, and CTA in a sensible sequence.
4. **Preprocess assets**
   - Convert HEIC/mobile special photos to PNG with `scripts/convert_images.py` when needed.
   - Generate or edit annotated images, privacy mosaics, and cards.
5. **Build video**
   - For standard vertical edits, run `scripts/build_vlog.py`.
   - For custom pipelines, use helpers in `references/core-functions.md`.
   - Use overlay PNG subtitles for portability instead of relying on FFmpeg `drawtext`, `subtitles`, or `ass`.
6. **Audio**
   - Mix user-provided BGM when available.
   - If no BGM is available, add a silent AAC track.
   - If the user wants a placeholder beat and accepts synthetic audio, use `scripts/gen_bgm.py`.
   - Read `references/publish-and-qc.md` for BGM levels and mix commands.
7. **Validate and iterate**
   - Run `ffprobe` on the final MP4.
   - Extract QC frames or contact sheets.
   - If the user asks for text removal at a timestamp, map the timestamp back to the shot plan and remove the source caption/card text before rebuilding.
8. **Publish copy**
   - Write title, caption, hashtags, and cover text for the target platform.
   - Keep long-form copy for Xiaohongshu and short hook-driven copy for Douyin/TikTok/Reels.
   - Generate a cover with `scripts/make_cover.py` when a cover image is requested.
   - Read `references/publish-and-qc.md` for platform templates and the final delivery checklist.

## Quick Commands

Build from a shot plan:

```bash
python3 agent-video-editor/scripts/build_vlog.py \
  --plan scripts/shot-plan.json \
  --project-name edit \
  --raw-dir raw \
  --output output/final.mp4
```

Inspect raw media:

```bash
python3 agent-video-editor/scripts/inspect_media.py raw \
  --json build/edit/media_manifest.json \
  --md build/edit/media_manifest.md
```

Extract keyframes:

```bash
python3 agent-video-editor/scripts/make_keyframes.py raw \
  --out-dir build/edit/keyframes \
  --times 3,10
```

Convert mobile images:

```bash
python3 agent-video-editor/scripts/convert_images.py raw \
  --out-dir converted \
  --format png
```

Generate placeholder BGM:

```bash
python3 agent-video-editor/scripts/gen_bgm.py 90 build/edit/bgm.wav
```

Inspect output:

```bash
ffprobe -v error \
  -show_entries format=duration,size:stream=index,codec_type,codec_name,width,height,avg_frame_rate \
  -of json output/final.mp4
```

Extract a QC frame:

```bash
mkdir -p build/edit/qc_frames
ffmpeg -y -hide_banner -loglevel error \
  -ss 00:00:30 -i output/final.mp4 \
  -frames:v 1 build/edit/qc_frames/check_0030.jpg
```

Generate a cover:

```bash
python3 agent-video-editor/scripts/make_cover.py output/final.mp4 \
  --at 00:00:03 \
  --title "Cover title" \
  --subtitle "Short supporting line" \
  --output output/cover.jpg
```

## Platform Copy Guidance

- Title formula: `subject/location + tension/question + result`.
- Xiaohongshu: use a useful, searchable caption with context, practical info, who it suits, who it does not suit, and tags.
- Douyin/TikTok/Reels: use a compact hook plus one conclusion or action prompt.
- Cover text should be shorter than video title and readable on mobile.

## References

- `references/setup.md`: environment, folder structure, install checks.
- `references/shot-plan-format.md`: JSON shot plan schema and planning heuristics.
- `references/core-functions.md`: FFmpeg/Pillow helper patterns, subtitles, rotation, mosaic, concat pitfalls.
- `references/publish-and-qc.md`: BGM mixing, cover guidance, platform copy templates, timestamp revisions, final checklist.
