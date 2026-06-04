# Publish, Audio, Cover, and QC Reference

Use this reference near the end of an edit, or whenever the user asks for platform copy, cover text, BGM, final checks, or timestamp revisions.

## BGM Mixing

General targets:

- Narration or important original audio should stay clear.
- BGM beds usually sit around -18 to -12 dB.
- Sound effects may be slightly louder than BGM, but should not mask speech.
- During dense subtitle/info-card moments, lower BGM by 1-3 dB if the edit feels busy.

Mix an existing silent-or-dialogue edit with BGM:

```bash
ffmpeg -y -i output/video_no_bgm.mp4 -stream_loop -1 -i assets/bgm.wav \
  -filter_complex "[1:a]volume=0.20,atrim=0:9999[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]" \
  -map 0:v:0 -map "[a]" \
  -c:v copy -c:a aac -b:a 160k -shortest output/final_with_bgm.mp4
```

If the source has no audio, add a silent AAC track before later mixing:

```bash
ffmpeg -y -i output/video_only.mp4 \
  -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest output/video_silent_audio.mp4
```

## Cover

Good cover text is shorter than the title. It should explain the topic at a glance, not summarize every detail.

Cover checklist:

- Use a real frame or photo from the video when possible.
- Keep the main title to 6-14 visible characters for CJK, or 3-7 words for English.
- Place text in the upper or lower third, away from platform buttons and profile overlays.
- Keep contrast high enough to read on a phone grid.
- Make one cover for the final upload, and optionally 2-3 alternates if the user is choosing a direction.

Generate a cover from a final video:

```bash
python3 agent-video-editor/scripts/make_cover.py output/final.mp4 \
  --at 00:00:03 \
  --title "Cover title" \
  --subtitle "Short supporting line" \
  --output output/cover.jpg
```

## Platform Copy

Title formulas:

- `place/topic + useful question`
- `experience + result`
- `who it is for + what they will learn`
- `surprise/detail + conclusion`

Xiaohongshu-style structure:

```text
Title:
Useful searchable title with a clear angle

Caption:
Hook or one-sentence conclusion.

What I noticed:
1. Practical detail
2. Practical detail
3. Practical detail

Good for:
- Audience or situation

Not ideal for:
- Honest limitation

Tags:
#location #topic #audience #content-type
```

Douyin/TikTok/Reels-style structure:

```text
Short hook.
One result or opinion.
Optional question or action prompt.

#topic #location #shortvideo
```

Tag layering:

- Location or category tag.
- Topic tag.
- Audience tag.
- Format tag such as vlog, review, tutorial, checklist, or first impression.

## Timestamp Revisions

When a user asks to remove text or a visual element at a timestamp:

1. Convert the timestamp to seconds.
2. Compute cumulative segment ranges from the shot plan.
3. Edit the original `caption`, `card`, overlay asset, or source segment in the shot plan.
4. Rebuild from source.
5. Extract a QC frame at the requested timestamp and a few seconds around it.

Avoid patching text removal directly on the final MP4 unless the source plan is unavailable.

## Final Delivery Checklist

Before export:

- Shot plan duration matches the intended runtime.
- Segment in/out points are inside source media durations.
- Subtitles and cards have no typos.
- Privacy-sensitive areas are removed, blurred, mosaicked, or replaced.
- BGM does not compete with voice or important source audio.
- Cover text is readable and explains the topic quickly.

After export:

```bash
ffprobe -v error \
  -show_entries format=duration,size:stream=index,codec_type,codec_name,width,height,avg_frame_rate \
  -of json output/final.mp4
```

Create a contact sheet:

```bash
mkdir -p build/edit/qc_frames
ffmpeg -y -hide_banner -loglevel error \
  -i output/final.mp4 \
  -vf "select='eq(n,30)+eq(n,900)+eq(n,1800)+eq(n,2700)',scale=270:480,tile=2x2" \
  -frames:v 1 build/edit/qc_frames/contact_sheet.jpg
```

Before publishing:

- Title has a clear hook or useful searchable angle.
- Caption explains who the video suits and any important limitation.
- Tags cover location/category, topic, audience, and content type.
- Output file and cover file are final versions.
