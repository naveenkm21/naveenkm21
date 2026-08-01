# How this profile is built

Three self-contained animated SVGs, arranged in a terminal-styled README.
No JavaScript, no GitHub token, no third-party stats service. GitHub strips
`<script>` and most inline CSS from READMEs but **does** render SVGs embedded
via `<img>` and plays their SMIL / CSS-keyframe animations — so all motion
lives inside the SVG files.

## Files

| File | What it is | Regenerate when |
|------|------------|-----------------|
| `contrib-heatmap.svg` | 53×7 contribution calendar, diagonal reveal | automatically, daily |
| `avi-ascii.svg` | monochrome self-typing ASCII portrait | you change your photo |
| `info-card.svg` | neofetch-style role/stack/highlights card | your details change |

## One-time setup

```bash
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# macOS/Linux:         source .venv/bin/activate
pip install -r scripts/requirements.txt
```

The daily workflow only needs `requests` + `beautifulsoup4` (already in
requirements.txt). The portrait pipeline also needs `pillow numpy
opencv-python rembg` — uncomment them in `scripts/requirements.txt` and
`pip install` locally only when you want to convert a photo.

## The heatmap (auto, daily)

```bash
GH_USERNAME=naveenkm21 python scripts/fetch_contributions.py  # -> data/contributions.json
python scripts/render_heatmap_svg.py                          # -> contrib-heatmap.svg
```

`fetch_contributions.py` scrapes the public HTML at
`https://github.com/users/<username>/contributions` (no auth) and derives
streaks, best day, and monthly totals. `render_heatmap_svg.py` draws the grid
with a GitHub-ish green ramp and a play-once diagonal reveal.

`.github/workflows/update-profile-art.yml` runs both on a daily cron and
commits the result. `[skip ci]` in the bot's commit message stops it from
re-triggering itself; `contents: write` lets it push. Trigger it once by hand
from the **Actions** tab (`workflow_dispatch`) to confirm it commits.

## The portrait (manual, when your photo changes)

```bash
python scripts/prep_photo.py source-photo.jpg   # -> source-prepped.png
python scripts/make_ascii_svg.py                # -> avi-ascii.svg
```

`prep_photo.py`: rembg cutout → CLAHE local-contrast boost → composite on pure
white (so the background maps to spaces). `make_ascii_svg.py`: downsample to a
character grid, map brightness to a density ramp, and wipe each row in
left-to-right with a block cursor. **If `source-prepped.png` is absent it
emits a placeholder portrait**, so the README renders before you add a photo.

Design choices that matter: monochrome (rainbow per-char looks like static)
and high contrast (a busy background washes out to spaces).

## The info card (manual, when your details change)

```bash
python scripts/make_info_card.py    # -> info-card.svg
STATIC=1 python scripts/make_info_card.py   # frozen frame for previews
```

Edit the `ROWS` list at the top of `scripts/make_info_card.py`. Keep the
*story* here — the heatmap already covers raw GitHub stats.

## README gotchas (GitHub markdown)

- Inline `style="..."` is stripped. The only vertical spacing GitHub honors is
  `<br>`.
- `<h1>`/`<h2>` draw a full-width underline rule — use `<h3>` for titles.
- Two images on one row need a `<table>`; keep each column `valign="top"`.
- The heatmap's display width (`860`) equals `370 + 490` so the edges line up.
