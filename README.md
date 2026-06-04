# 短视频平台剪辑指南：素材整理、脚本生成、字幕烧录与发布文案

适用场景：用手机、相机或运动相机拍摄的竖屏/横屏混合素材，剪成适合小红书、抖音、视频号、Reels、TikTok 等平台发布的 9:16 竖屏短视频。

核心原则：先整理素材和脚本，再结构化镜头表，最后自动化生成片段、烧录字幕、合成音频、检查成片。不要直接在最终 MP4 上做不可逆修补；能从脚本或镜头表源头修改，就从源头重导。

---

## 如何使用这个 Skill

这个仓库包含一个通用视频剪辑 skill：`agent-video-editor/`。它适合交给 Claude、Codex 或其他能读取文件、运行命令、调用 FFmpeg 的 agent 使用。

### 方式一：作为项目内 Skill 使用

把 `agent-video-editor/` 放在视频项目根目录，然后对 agent 说：

```text
使用 agent-video-editor，把 raw/ 里的素材和 scripts/ 里的脚本剪成一条 9:16 短视频。
请先扫描素材、抽关键帧、生成镜头表，再用 FFmpeg 构建成片，并输出封面和发布文案。
```

推荐项目结构：

```text
project/
├── agent-video-editor/
├── raw/
├── scripts/
├── build/
├── output/
└── publish-copy.md
```

### 方式二：安装到 Agent 的 Skills 目录

如果你的 agent 工具支持本地 skills，可以把 `agent-video-editor/` 整个文件夹放进对应的 skills 目录。之后在新项目里直接点名使用：

```text
用 agent-video-editor 帮我剪这个短视频项目。
素材在 raw/，脚本在 scripts/script.md，目标平台是小红书和抖音。
```

如果工具支持 `.skill` 包，也可以导入打包文件：

```text
agent-video-editor-YYYYMMDD.skill
```

### 常用命令

扫描素材：

```bash
python3 agent-video-editor/scripts/inspect_media.py raw \
  --json build/edit/media_manifest.json \
  --md build/edit/media_manifest.md
```

抽关键帧：

```bash
python3 agent-video-editor/scripts/make_keyframes.py raw \
  --out-dir build/edit/keyframes \
  --times 3,10
```

转换手机图片：

```bash
python3 agent-video-editor/scripts/convert_images.py raw \
  --out-dir converted \
  --format png
```

按镜头表构建视频：

```bash
python3 agent-video-editor/scripts/build_vlog.py \
  --plan scripts/shot-plan.json \
  --project-name edit \
  --raw-dir raw \
  --output output/final.mp4
```

生成封面：

```bash
python3 agent-video-editor/scripts/make_cover.py output/final.mp4 \
  --at 00:00:03 \
  --title "封面标题" \
  --subtitle "简短副标题" \
  --output output/cover.jpg
```

### 给 Agent 的推荐提示词

```text
请使用 agent-video-editor workflow：
1. 先检查项目结构和素材清单。
2. 用 ffprobe 生成素材信息，并抽关键帧。
3. 根据脚本整理 shot-plan.json。
4. 处理 HEIC、横竖屏、字幕、安全区、隐私遮挡和 BGM。
5. 用 FFmpeg 导出 1080x1920 H.264 MP4。
6. 抽帧检查字幕、封面候选和关键时间点。
7. 输出适合目标平台的标题、正文、标签和封面文案。
```

### 依赖安装

至少需要：

```bash
ffmpeg -version
ffprobe -version
python3 -m pip install pillow
```

可选：

```bash
python3 -m pip install pillow-heif numpy fonttools
```

---

## 1. 项目文件夹结构

推荐每个视频项目单独建一个文件夹：

```text
project/
├── raw/                    # 原始素材，只读不改
├── converted/              # 转码后的图片/视频，例如 HEIC 转 PNG
├── annotated/              # 标注图、箭头图、遮挡隐私后的图片
├── scripts/                # 剪辑脚本、镜头表、自动化脚本
├── build/
│   └── edit/
│       ├── keyframes/      # 素材关键帧
│       ├── segments/       # 单个镜头片段
│       ├── overlays/       # 字幕、信息卡、标题卡 PNG
│       ├── captioned/      # 已叠字幕片段
│       ├── qc_frames/      # 抽帧检查图
│       └── concat.txt      # 片段合并清单
├── output/
│   ├── final.mp4           # 最终成片
│   └── cover.jpg           # 封面图
└── publish-copy.md         # 标题、正文、标签
```

命名建议：

- 原始素材保持相机原文件名，不覆盖、不改写。
- 自动生成内容放进 `build/`，可以随时删除重建。
- 发布文件放进 `output/`，按版本命名，例如 `final_v1.mp4`、`final_no_subtitle_v2.mp4`。
- 脚本和镜头表放进 `scripts/`，方便追踪修改。

---

## 2. 必要工具与环境

### 基础工具

macOS：

```bash
brew install ffmpeg
python3 -m pip install pillow
```

Ubuntu/Debian：

```bash
sudo apt update
sudo apt install ffmpeg python3-pip
python3 -m pip install pillow
```

可选依赖：

```bash
python3 -m pip install pillow-heif numpy fonttools
```

用途：

- `ffmpeg`：剪切、缩放、合并、混音、导出。
- `ffprobe`：检查素材时长、尺寸、编码、旋转信息。
- `Pillow`：生成字幕图层、信息卡、马赛克、封面。
- `pillow-heif`：在部分环境中读取 HEIC 图片。
- `numpy`：需要自动生成简单 BGM 或音效时使用。

### 字体准备

字幕必须使用支持中文、英文、数字和常见符号的字体。建议准备：

- 一套中文字体：如思源黑体、苹方、黑体、Noto Sans CJK。
- 一套英文字体：如 Inter、Arial、DejaVu Sans。

中英混排容易出现方块字或乱码。稳妥做法是：

- 优先选一套覆盖 CJK 的字体。
- 如果字体覆盖不完整，就按字符选择字体。
- 在脚本里把字体路径做成配置项，不要写死个人电脑路径。

---

## 3. 素材整理流程

### 3.1 列出素材清单

```bash
find raw -maxdepth 1 -type f | sort
```

### 3.2 批量查看素材信息

```bash
for f in raw/*; do
  ffprobe -v error -select_streams v:0 \
    -show_entries stream=codec_name,width,height:stream_tags=rotate:format=duration \
    -of csv=p=0 "$f" 2>/dev/null | awk -v file="$f" -F, '{print file","$0}'
done
```

重点看：

- 时长是否覆盖脚本时间码。
- 竖拍/横拍是否混合。
- 是否有旋转元数据。
- 是否有音频轨。
- 是否有 HEIC、Live Photo、空间照片等特殊格式。

### 3.3 批量提取关键帧

```bash
mkdir -p build/edit/keyframes
for f in raw/*; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  ffmpeg -y -hide_banner -loglevel error -ss 3 -i "$f" \
    -frames:v 1 "build/edit/keyframes/${base}_3s.jpg"
  ffmpeg -y -hide_banner -loglevel error -ss 10 -i "$f" \
    -frames:v 1 "build/edit/keyframes/${base}_10s.jpg"
done
```

把关键帧铺开看，比逐个播放视频更快。先给素材打标签：

- hook：开场冲击镜头。
- location：地点、路标、门头。
- detail：价格、菜单、设施、产品细节。
- broll：环境过渡镜头。
- action：动作/体验/实测。
- ending：结尾、总结、封面候选。

### 3.4 处理 HEIC 和手机特殊图片

HEIC 可能有多流、深度图、空间照片等情况。FFmpeg 有时会读到辅助流，导致画面变暗、灰度或方向错误。

通用方案：

```bash
mkdir -p converted
```

macOS 可用系统预览/QuickLook 或图片工具批量转 PNG。Linux 或跨平台环境可用 `pillow-heif`：

```python
from pathlib import Path
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()

src_dir = Path("raw")
out_dir = Path("converted")
out_dir.mkdir(exist_ok=True)

for src in src_dir.glob("*.HEIC"):
    img = Image.open(src).convert("RGB")
    img.save(out_dir / f"{src.name}.png")
```

剪辑脚本遇到 `.HEIC` 时，优先读取 `converted/<原文件名>.png`。

---

## 4. 从脚本到镜头表

人类可读脚本和机器可读镜头表要分开。

### 4.1 人类脚本字段

| 字段 | 用途 |
|---|---|
| 段落 | 钩子、背景、信息、过程、体验、总结 |
| 镜头号 | 方便沟通修改 |
| 素材文件 | 对应原始素材 |
| 入点/出点 | 视频素材截取范围 |
| 时长 | 图片、信息卡、转场时长 |
| 画面描述 | 确认画面内容 |
| 字幕/口播 | 后续烧录或配音 |
| 备注 | BGM、音效、隐私处理、封面候选 |

### 4.2 短视频结构模板

常见 60-150 秒结构：

1. 0-5 秒：强钩子。直接给结果、反差、动作、问题或惊喜。
2. 5-20 秒：交代地点/背景/主题。
3. 20-45 秒：核心信息，例如价格、规则、步骤、产品亮点。
4. 45-90 秒：过程和体验，用 B-roll 串联。
5. 90-120 秒：实测、优缺点、结论。
6. 结尾 3-8 秒：收藏/关注/下集预告/封面回收。

### 4.3 机器可读镜头表

建议用 JSON：

```json
{
  "width": 1080,
  "height": 1920,
  "fps": 30,
  "raw_dir": "raw",
  "converted_dir": "converted",
  "build_dir": "build/edit",
  "font_file": "path/to/font.ttf",
  "segments": [
    {
      "kind": "video",
      "file": "clip_001.mov",
      "start": 12.5,
      "dur": 2.5,
      "caption": "开场钩子字幕"
    },
    {
      "kind": "image",
      "file": "photo_001.heic",
      "dur": 3,
      "caption": "地点或细节说明"
    },
    {
      "kind": "card",
      "dur": 6,
      "card": "信息卡标题\n\n要点一\n要点二\n要点三"
    }
  ]
}
```

字段说明：

- `kind=video`：需要 `file`、`start`、`dur`。
- `kind=image`：需要 `file`、`dur`。
- `kind=card`：需要 `dur`、`card`。
- `caption`：底部字幕。
- `style: "title"`：居中标题字幕。

---

## 5. 画面适配：裁切还是留黑边

目标平台大多数适合 9:16：

```text
1080 x 1920
30 fps
H.264
AAC
```

### 5.1 裁切填满

适合：

- 主体在画面中间。
- 横拍素材但可以损失两侧。
- 想要平台观感更统一。

FFmpeg 思路：

```bash
scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920
```

### 5.2 留黑边/背景模糊

适合：

- 横拍素材主体靠边。
- 不想裁掉人物、产品、屏幕或动作轨迹。
- 教程类、说明类、需要保留完整画面的素材。

黑边 letterbox 思路：

```python
def letterbox_vf(src_w, src_h, target_w=1080, target_h=1920):
    scale = min(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale) & ~1
    new_h = int(src_h * scale) & ~1
    pad_x = (target_w - new_w) // 2
    pad_y = (target_h - new_h) // 2
    return f"scale={new_w}:{new_h},pad={target_w}:{target_h}:{pad_x}:{pad_y}:black"
```

背景模糊思路：

```bash
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=35[bg];
[0:v]scale=1000:1800:force_original_aspect_ratio=decrease[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2
```

### 5.3 旋转元数据

手机竖拍视频可能存成横向尺寸加 `rotate=90` 元数据。做自动 letterbox 时，要把旋转后的显示宽高算对。

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

---

## 6. 字幕烧录与信息卡

### 6.1 推荐方式：Pillow 生成字幕 PNG，FFmpeg overlay 叠加

很多 FFmpeg 安装没有 `drawtext`、`subtitles` 或 `ass` 滤镜。最稳定的方式是：

1. 用 Python + Pillow 生成透明 PNG 字幕层。
2. 用 FFmpeg `overlay` 叠到片段上。
3. 最终拼接所有已处理片段。

示例：

```bash
ffmpeg -y -i segment.mp4 -loop 1 -i subtitle.png \
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p" \
  -t 3 -an output_segment.mp4
```

### 6.2 字幕设计建议

- 底部字幕离底边留 120-180 px，避开平台按钮和标题区。
- 中文 44-64 px 较常用，根据信息密度调整。
- 白字 + 黑描边/半透明黑底最稳。
- 一条字幕尽量不超过两行。
- 动作镜头少放字幕，信息镜头再放重点文字。
- 价格、步骤、优缺点适合做全屏信息卡。

### 6.3 信息卡结构

信息卡适合：

- 价格表。
- 行程/路线。
- 步骤清单。
- 优缺点总结。
- 注意事项。

信息卡写法：

```text
标题

要点一
要点二
要点三
```

视觉上保持：

- 深色或浅色纯背景。
- 文字左对齐或居中，但不要混乱。
- 每张卡 5-10 秒。
- 一张卡不超过 8 条信息。

---

## 7. 片段生成与合并

### 7.1 视频片段

```bash
ffmpeg -y -ss 12.5 -t 2.5 -i raw/clip.mov \
  -map 0:v:0 -an \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p" \
  -c:v libx264 -preset veryfast -crf 18 \
  build/edit/segments/001.mp4
```

### 7.2 图片片段

图片必须用 `-loop 1 -t <duration>`，否则可能只有一帧：

```bash
ffmpeg -y -loop 1 -t 3 -i converted/photo.png \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p" \
  -c:v libx264 -preset veryfast -crf 18 \
  build/edit/segments/002.mp4
```

### 7.3 合并片段

`concat.txt`：

```text
file 'segments/001.mp4'
file 'segments/002.mp4'
file 'captioned/003.mp4'
```

合并并加静音音轨：

```bash
ffmpeg -y -f concat -safe 0 -i build/edit/concat.txt \
  -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 \
  -map 0:v:0 -map 1:a:0 \
  -vf "fps=30,format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 128k -shortest output/final.mp4
```

### 7.4 B-frame / DTS 问题

手机 H.265 素材可能有 B-frame。直接 `-c copy` 拼接时可能出现：

- 时长变长。
- `Non-monotonous DTS` 警告。
- 平台上传后音画不同步。

稳妥方案：

- 每个片段先重编码成统一参数。
- 最终 concat 后再强制 `fps=30,format=yuv420p`。
- 如果仍然异常，可用 `setpts=N/30/TB` 重写视频时间戳。

---

## 8. BGM、音效与混音

### 8.1 BGM 音量

常用参考：

- BGM 底层：约 -18 到 -12 dB。
- 人声/口播：保持最清楚。
- 字幕信息卡出现时，BGM 可短暂降低 1-3 dB。
- 音效比 BGM 略高，但不要盖住人声。

### 8.2 混入 BGM

```bash
ffmpeg -y -i output/no_music.mp4 -i assets/bgm.mp3 \
  -filter_complex "[1:a]volume=0.22,afade=t=out:st=115:d=4[bgm]" \
  -map 0:v:0 -map "[bgm]" \
  -c:v copy -c:a aac -b:a 128k -shortest output/final.mp4
```

### 8.3 没有 BGM 时

如果暂时没有音乐，仍建议加静音 AAC 轨，避免平台识别异常：

```bash
ffmpeg -y -i output/video_only.mp4 \
  -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 128k -shortest output/final.mp4
```

---

## 9. 隐私处理与马赛克

适用：

- 路人脸部。
- 手机号、二维码、票据、车牌。
- 未授权的儿童、工作人员、顾客。
- 屏幕上的个人账号信息。

静态图片马赛克：

```python
from PIL import Image

def pixelate(img, x, y, w, h, block=15):
    region = img.crop((x, y, x + w, y + h))
    small = region.resize((max(1, w // block), max(1, h // block)), Image.BOX)
    mosaic = small.resize((w, h), Image.NEAREST)
    img.paste(mosaic, (x, y))
    return img

img = Image.open("input.jpg").convert("RGB")
pixelate(img, 100, 200, 240, 160)
img.save("output.jpg")
```

定位坐标可先画网格：

```python
from PIL import Image, ImageDraw

img = Image.open("input.jpg").convert("RGB")
draw = ImageDraw.Draw(img)
for x in range(0, img.width, 200):
    draw.line([(x, 0), (x, img.height)], fill=(255, 0, 0), width=2)
    draw.text((x + 4, 8), str(x), fill=(255, 0, 0))
for y in range(0, img.height, 200):
    draw.line([(0, y), (img.width, y)], fill=(0, 255, 0), width=2)
    draw.text((4, y + 4), str(y), fill=(0, 255, 0))
img.save("grid_debug.jpg")
```

动态视频马赛克更复杂，建议：

- 固定位置：用 FFmpeg crop + scale + overlay 做局部像素化。
- 移动物体：优先在剪辑软件或视觉模型工具中处理。
- 高风险隐私：直接换镜头更稳。

---

## 10. 修改与返工流程

### 10.1 删除或修改字幕

不要用黑条遮最终视频。正确流程：

1. 在镜头表中找到对应 `caption` 或 `card`。
2. 修改或删除文字。
3. 重新生成相关片段或整片。
4. 抽帧检查目标时间点。

查找文字：

```bash
rg "要修改的字幕关键词" scripts build
```

抽帧检查：

```bash
mkdir -p build/edit/qc_frames
ffmpeg -y -hide_banner -loglevel error \
  -ss 00:01:20 -i output/final.mp4 \
  -frames:v 1 build/edit/qc_frames/check_0120.jpg
```

### 10.2 只改文案不改视频

把发布文案单独放在 `publish-copy.md`，不要写死进构建脚本。常见版本：

- 小红书长文案。
- 抖音短文案。
- 标题备选。
- 话题标签。
- 封面文案。

---

## 11. 发布标题与文案

### 11.1 标题公式

```text
地点/对象 + 反差/问题 + 实测/结果
```

示例模板：

```text
城市核心区竟然有这个？一次真实探店实测
```

```text
第一次体验这个项目，值不值得去？
```

```text
把这家店/这个地方测了一遍，优缺点都说清楚
```

### 11.2 小红书文案结构

1. 一句话钩子。
2. 你去了哪里/做了什么。
3. 最有用的信息：价格、位置、流程、体验重点。
4. 适合谁。
5. 不适合谁。
6. 真实感受和结论。
7. 收藏/关注引导。
8. 话题标签。

### 11.3 抖音文案结构

抖音文案更短：

```text
一句话总结体验 + 最关键的结果/建议 + 行动引导
```

示例模板：

```text
这次实测下来，优点是方便、信息清楚，缺点是高峰期体验会下降。想去的话建议提前看好时间。
```

### 11.4 标签分层

- 地点/场景：`#城市名 #旅行 #周末去哪儿`
- 内容主题：`#探店 #测评 #教程 #运动 #生活方式`
- 精准人群：`#新手友好 #亲子 #上班族 #学生党`
- 平台互动：`#收藏备用 #真实体验 #避坑指南`

---

## 12. 常见问题速查

| 问题 | 常见原因 | 解决方法 |
|---|---|---|
| 竖拍画面被压扁 | 没处理旋转元数据 | 读取 `rotate` 后交换显示宽高 |
| 图片片段只有一瞬间 | 没用 `-loop 1 -t` | 图片转视频时指定时长 |
| HEIC 画面发黑或灰度 | 读到了辅助/深度流 | 先转 PNG 再剪 |
| 中文字幕乱码/方块 | 字体不支持中文 | 使用 CJK 字体或逐字符选字体 |
| concat 后时长异常 | B-frame/DTS 问题 | 片段重编码，最终重写 fps/PTS |
| 音画不同步 | 混合素材时间戳不统一 | 统一 fps、重编码、避免 copy 拼接 |
| 字幕挡住平台按钮 | 字幕太靠底 | 底部留 120-180 px |
| 信息卡读不完 | 文字太多或时长太短 | 拆成多张卡或延长到 6-10 秒 |
| 文件被占用 | 预览/剪辑软件打开中 | 关闭占用进程或换输出文件名 |
| 最终上传变糊 | 码率/分辨率过低 | 保持 1080x1920，CRF 18-23，H.264 |

---

## 13. 自动化脚本建议

完整自动化项目可拆成：

```text
scripts/
├── inspect_media.py       # 扫描素材，生成清单
├── make_keyframes.py      # 批量抽帧
├── convert_images.py      # HEIC/图片预处理
├── build_video.py         # 按镜头表生成成片
├── make_cover.py          # 生成封面
└── publish_copy.md        # 发布文案模板
```

支持断点续做：

```python
import sys

start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
end = int(sys.argv[2]) if len(sys.argv) > 2 else len(segments)

for index, segment in enumerate(segments[start:end], start=start):
    render_segment(index, segment)
```

这样改第 20-25 个镜头时，不必重跑前 19 个。

---

## 14. 最终交付检查清单

导出前：

- 镜头表时长和脚本一致。
- 素材入点/出点没有越界。
- 字幕没有错别字。
- 隐私信息已遮挡。
- BGM 和人声不打架。
- 封面能在第一眼看懂主题。

导出后：

```bash
ffprobe -v error \
  -show_entries format=duration,size:stream=index,codec_type,codec_name,width,height,avg_frame_rate \
  -of json output/final.mp4
```

抽帧检查：

```bash
ffmpeg -y -hide_banner -loglevel error \
  -i output/final.mp4 \
  -vf "select='eq(n,30)+eq(n,900)+eq(n,1800)+eq(n,2700)',scale=270:480,tile=2x2" \
  -frames:v 1 build/edit/qc_frames/contact_sheet.jpg
```

发布前：

- 标题是否有钩子。
- 文案是否讲清楚“适合谁、不适合谁”。
- 标签是否覆盖地点、主题、人群和内容类型。
- 输出文件名是否是最终版本。
