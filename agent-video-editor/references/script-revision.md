# Script Revision & Fact-Check

Use this before turning a script into a shot plan, especially for gear reviews, product news, "sequel" videos, or any script that makes factual claims. A wrong claim baked into subtitles is expensive to fix after export, so fix it at the script stage.

## 1. Match the creator before writing

- Read the creator's real history first (past posts, titles, captions, best-performing pieces). Do not write in a generic "viral script" voice.
- Match the **format** they actually publish, not just the tone. If they mostly post footage + on-screen text + light voiceover, do not hand them a full talking-head monologue.
- If the project ships writing skills (hook writer, script writer, cover skill), read their instructions before drafting titles, hooks, scripts, or covers. Listing a skill is not the same as using it.
- When a new video continues an earlier hit, frame it as a sequel: reuse its premise, persona facts, and closing line, and show the original cover early as credibility.

## 2. Separate facts from voice

Every claim in a script falls into one of three buckets. Tag each before finalizing:

| Bucket | Source | Rule |
| --- | --- | --- |
| Verified fact | Official site, press release, primary review/video | Keep, and keep the wording as strong as the source — no stronger |
| Creator's experience | The creator told you directly | Keep, in their words |
| Unsourced | Your inference, a reseller rumor, a "sounds right" detail | Delete or rewrite as "official info says…" |

Hard rules:

- Never invent first-hand sensations (fit, comfort, "doesn't pinch") for products the creator has not used. Mark those spots `[待补: 你试过吗？]` and ask.
- Do not round numbers up for drama ("上千赞" when it's 516). Use the real figure or a softer true phrase ("快一千").
- Check time words against dates ("去年" vs "今年", "已上市" vs "明年春季").
- Do not add prices unless the user asks; prices go stale and invite disputes.
- Do not disparage the old version or a competitor to make the new one look good. Describe what changed, neutrally.

## 3. Label changes precisely

"Updated" is usually wrong. Pick the exact word per item:

- **换代 / 新版 (replaces old)** — the old model is being retired or superseded.
- **出新款 / 新增型号 (sits alongside)** — a variant added; the original stays.
- **新系列 (new line)** — never existed before.

A headline or cover that says "全部换代" when only one item was replaced is a factual error, not a style choice.

## 4. Per-item structure for multi-product scripts

For each product, use the same four beats so viewers can compare:

1. **原来定位** — what the previous version / line was for
2. **改了啥** — only sourced changes
3. **适合谁** — the audience in the creator's words
4. **什么场景选它** — the concrete situation

Order items by audience relevance (e.g. beginner-relevant first), not by brand. If the script gets long (>2 min), split the advanced items into a follow-up episode instead of cramming.

Mirror the four beats in an on-screen text card per item, e.g. `新系列 → 运动鞋手感 → 怕挤脚的新手 → 入门/泡馆一整天`.

## 5. Keep a correction table

When revising a draft (yours or a reference script the user supplied), output a table so the user can audit every change:

| Draft wording | Changed to | Reason / source |
| --- | --- | --- |
| 上千个赞 | 快一千个赞 | Original post: 516 likes |
| 楦型偏宽 | (deleted) | No source found |

Cite sources at the end. Rows with "no source" are deletions by default.

## 6. Keep script, cover, and shot plan in sync

- After the cover headline is chosen, re-check the script: item count, labels (换代/新款), and promises must match the cover.
- When an item has no usable image, say so and plan text-only cards rather than borrowing a look-alike image.
- Credit image sources in filenames (e.g. `Brand_Model_01_side_src-UKC.png`) so attribution survives into the edit.
- Only after these checks, convert the script to `shot-plan.json` (see `shot-plan-format.md`).

## Revision checklist

- [ ] Read creator history and project writing skills
- [ ] Format matches what the creator actually posts
- [ ] Every claim tagged: verified / creator / deleted
- [ ] No invented first-hand feel; open questions marked `[待补]`
- [ ] Numbers and dates checked against sources
- [ ] 换代 / 新款 / 新系列 used correctly; no price unless asked
- [ ] Multi-item scripts use the 4-beat structure
- [ ] Correction table + sources delivered
- [ ] Cover, title, and script agree
