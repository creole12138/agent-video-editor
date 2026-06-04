# Setup Reference

## Tools

Install FFmpeg and Python packages:

```bash
# macOS
brew install ffmpeg
python3 -m pip install pillow

# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg python3-pip
python3 -m pip install pillow
```

Optional packages:

```bash
python3 -m pip install pillow-heif numpy fonttools
```

Use:

- `ffmpeg`: trim, scale, encode, overlay, concat, mix audio.
- `ffprobe`: inspect duration, stream info, rotation, dimensions.
- `Pillow`: render subtitles/cards, process images, pixelate privacy regions.
- `pillow-heif`: read HEIC when system conversion is unavailable.
- `numpy`: synthesize placeholder BGM or effects.

## Fonts

Choose fonts that support the output language. For CJK subtitles, prefer Noto Sans CJK, Source Han Sans, PingFang, Hiragino, Microsoft YaHei, SimHei, or another CJK-capable font.

Make the font path configurable in scripts:

```json
{
  "font_file": "path/to/font.ttf"
}
```

If one font does not cover all characters, use a dual-font strategy in `core-functions.md`.

## Folder Structure

```text
project/
├── raw/                 # original source media
├── converted/           # HEIC/mobile photo conversions
├── annotated/           # marked-up or privacy-processed assets
├── scripts/             # shot plan and project scripts
├── build/edit/          # generated segments, overlays, QC frames
├── output/              # final video and cover
└── publish-copy.md      # platform title/caption/tags
```

## Install Checks

```bash
ffmpeg -version
ffprobe -version
python3 -c "from PIL import Image; print('Pillow OK')"
```

## HEIC Notes

Some phone HEIC files contain multiple streams such as depth or spatial-photo auxiliary data. If FFmpeg reads a dark grayscale stream, convert the image first:

```python
from pathlib import Path
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()

src_dir = Path("raw")
out_dir = Path("converted")
out_dir.mkdir(exist_ok=True)

for src in src_dir.glob("*.HEIC"):
    Image.open(src).convert("RGB").save(out_dir / f"{src.name}.png")
```

