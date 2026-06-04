# Shot Plan Format

Use a JSON shot plan as the source of truth for automated edits.

```json
{
  "width": 1080,
  "height": 1920,
  "fps": 30,
  "raw_dir": "raw",
  "converted_heic_dir": "converted",
  "build_dir": "build/edit",
  "font_file": "path/to/font.ttf",
  "segments": [
    {
      "kind": "video",
      "file": "clip_001.mov",
      "start": 12.5,
      "dur": 2.5,
      "caption": "Opening hook"
    },
    {
      "kind": "image",
      "file": "photo_001.heic",
      "dur": 3,
      "caption": "Location or detail"
    },
    {
      "kind": "card",
      "dur": 6,
      "card": "Info Card\n\nPoint one\nPoint two\nPoint three"
    }
  ]
}
```

## Segment Fields

- `kind`: `video`, `image`, or `card`.
- `file`: source media path relative to `raw_dir`, unless it is a project-relative generated asset.
- `start`: source video in-point in seconds. Required for `video`.
- `dur`: segment duration in seconds.
- `caption`: optional bottom subtitle.
- `style`: optional. Use `title` for centered title captions.
- `card`: full-screen card text with newlines.

## Planning Heuristics

- Use the first 3-5 seconds for movement, surprise, conflict, result, or a strong question.
- Keep ordinary B-roll at 2-4 seconds.
- Keep info cards at 5-10 seconds.
- Avoid over-captioning action shots.
- Put dense information in cards, not bottom subtitles.
- Keep the ending short and conclusive.

## Timestamp Edits

When the user asks to remove or change text at a timestamp:

1. Compute cumulative segment ranges from the shot plan.
2. Identify the segment covering that timestamp.
3. Remove or edit the segment `caption` or the relevant line inside `card`.
4. Rebuild and extract a QC frame at that timestamp.

