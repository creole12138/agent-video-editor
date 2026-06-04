# Core Functions and FFmpeg Patterns

These snippets are reusable patterns for custom pipelines when `scripts/build_vlog.py` is not enough.

## Rotation-Aware Probe

```python
import json
import subprocess

def probe_display_size(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams", "-of", "json", path],
        capture_output=True,
        text=True,
        check=True,
    )
    stream = json.loads(r.stdout)["streams"][0]
    w = int(stream["width"])
    h = int(stream["height"])
    rotate = int(stream.get("tags", {}).get("rotate", "0") or 0)
    if abs(rotate) in (90, 270):
        w, h = h, w
    return w, h
```

## Fit Modes

Crop to fill 9:16:

```bash
scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920
```

Letterbox without cropping:

```python
def letterbox_vf(src_w, src_h, target_w=1080, target_h=1920):
    scale = min(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale) & ~1
    new_h = int(src_h * scale) & ~1
    pad_x = (target_w - new_w) // 2
    pad_y = (target_h - new_h) // 2
    return f"scale={new_w}:{new_h},pad={target_w}:{target_h}:{pad_x}:{pad_y}:black"
```

Blurred background:

```bash
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=35[bg];
[0:v]scale=1000:1800:force_original_aspect_ratio=decrease[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2
```

## Subtitle Overlay With Pillow

Generate transparent subtitle PNGs and overlay them with FFmpeg. This avoids depending on FFmpeg text filters.

```python
from PIL import Image, ImageDraw, ImageFont

def make_subtitle_png(text, out, font_file, width=1080, font_size=56):
    font = ImageFont.truetype(font_file, font_size)
    lines = text.splitlines() or [text]
    line_h = font_size + 16
    pad = 24
    height = len(lines) * line_h + pad * 2
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((60, 0, width - 60, height), radius=24, fill=(0, 0, 0, 155))
    y = pad
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font, stroke_width=2)
        x = (width - (box[2] - box[0])) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 220))
        y += line_h
    img.save(out)
```

Overlay:

```bash
ffmpeg -y -i segment.mp4 -loop 1 -i subtitle.png \
  -filter_complex "[0:v][1:v]overlay=0:H-h-150:format=auto,format=yuv420p" \
  -t 3 -an captioned.mp4
```

## Image Segments

Always loop stills:

```bash
ffmpeg -y -loop 1 -t 3 -i converted/photo.png \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p" \
  -c:v libx264 -preset veryfast -crf 18 segment.mp4
```

## Concatenation

Prefer re-encoded uniform segments, then concat:

```bash
ffmpeg -y -f concat -safe 0 -i build/edit/concat.txt \
  -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 \
  -map 0:v:0 -map 1:a:0 \
  -vf "fps=30,format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 128k -shortest output/final.mp4
```

If duration or DTS is wrong, re-encode with `setpts=N/30/TB`.

## Privacy Mosaic

```python
from PIL import Image, ImageDraw

def pixelate(img, x, y, w, h, block=15):
    region = img.crop((x, y, x + w, y + h))
    small = region.resize((max(1, w // block), max(1, h // block)), Image.BOX)
    mosaic = small.resize((w, h), Image.NEAREST)
    img.paste(mosaic, (x, y))
    return img

def draw_coord_grid(img, step=200):
    dbg = img.copy()
    draw = ImageDraw.Draw(dbg)
    for x in range(0, img.width, step):
        draw.line([(x, 0), (x, img.height)], fill=(255, 0, 0), width=2)
        draw.text((x + 4, 8), str(x), fill=(255, 0, 0))
    for y in range(0, img.height, step):
        draw.line([(0, y), (img.width, y)], fill=(0, 255, 0), width=2)
        draw.text((4, y + 4), str(y), fill=(0, 255, 0))
    return dbg
```

## Common Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| Portrait clip squashed | rotate metadata ignored | use rotation-aware display size |
| Still image flashes for one frame | missing `-loop 1 -t` | loop images with explicit duration |
| HEIC dark/gray | auxiliary stream read | convert to PNG first |
| Chinese boxes | font lacks CJK | use CJK-capable font |
| concat duration wrong | B-frame/DTS issue | re-encode uniform segments and force fps/PTS |
| subtitles cover platform UI | too low | reserve bottom safe area |

