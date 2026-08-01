#!/usr/bin/env python3
"""
Convert scripts/../source-prepped.png into a self-typing monochrome ASCII SVG.

- Downsample the prepped image to a character grid (~100 wide).
- Each pixel's brightness picks a glyph from a density ramp
  (sparse chars = bright, dense chars = dark). A leading SPACE clears the
  background to nothing, so only the high-contrast subject prints.
- Monochrome (one light-gray fill) -- per-character rainbow is what makes most
  ASCII portraits look like static.
- Each row wipes left-to-right (SMIL), staggered top->bottom, with a small
  block cursor riding the wipe edge. Prints once and freezes -- no loop.

If source-prepped.png is missing, a built-in placeholder portrait is used so
the README renders out of the box. Drop in your photo (Steps 3a/3b) to replace.

    python scripts/prep_photo.py source-photo.jpg   # once per photo
    python scripts/make_ascii_svg.py                # writes avi-ascii.svg
"""
import os

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "..", "source-prepped.png")
OUT = os.path.join(HERE, "..", "avi-ascii.svg")

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
COLS = 100               # character columns
FONT_SIZE = 8
CHAR_W = 4.8             # monospace advance at FONT_SIZE
LINE_H = 8.0
FILL = "#b9c2cc"         # single light-gray
CURSOR = "#39d353"
FONT = ("ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, "
        "'Liberation Mono', monospace")

# Built-in placeholder (used only when source-prepped.png is absent).
PLACEHOLDER = [
    "                                                            ",
    "                 .:-=+++++++++++=-:.                        ",
    "             .-=+*################*+=-.                     ",
    "          .-+*#####################%##*=.                  ",
    "        .=*###########################%#*=.                ",
    "       =*###############################%#*.               ",
    "      +##########%%%%%%%%%%%%%%##########%#*.              ",
    "     =#######%%%*=:.        .:=*%%%#######%#=              ",
    "    :*#####%%*.                  .*%%######%*.             ",
    "    =#####%%:      .-==-.  .-==-.   :%%#####%-             ",
    "    *####%%:     .+#%##%#+.+#%##%+.  :%%####%+             ",
    "    *####%=      *%#*  *%#=%#*  #%*   =%####%+             ",
    "    *####%=      *%#*  *%#=%#*  #%*   =%####%+             ",
    "    +####%-       +#%##%+. +#%##%+.   -%####%=             ",
    "    :*####%.        .::.     .::.    .%%####*.             ",
    "     =#####%.         .-====-.      .%%#####-              ",
    "      +#####%:      .+%%%%%%%%+.   :%%#####+.              ",
    "       =######%=.    .=*####*=.  .=%%#####=                ",
    "        .+######%*-.          .-*%%#####*.                 ",
    "          .+########%*+=--=+*%%%######*-                   ",
    "            .-+*###################*+-.                    ",
    "                .:-=+*******+=-:.                          ",
    "              [ naveenkm21 // add your photo ]             ",
    "                                                           ",
]


def load_grid():
    """Return list[str] rows. Uses the real image if present."""
    if not os.path.exists(SRC):
        print("[ascii] source-prepped.png not found -> using placeholder")
        return PLACEHOLDER
    try:
        from PIL import Image
    except ImportError:
        print("[ascii] Pillow not installed -> using placeholder "
              "(pip install pillow numpy to convert a photo)")
        return PLACEHOLDER

    img = Image.open(SRC).convert("L")
    w, h = img.size
    # characters are ~2x taller than wide; correct aspect when sampling rows
    rows = max(1, int(COLS * (h / w) * 0.5))
    img = img.resize((COLS, rows))
    px = img.load()
    n = len(RAMP)
    grid = []
    for y in range(rows):
        line = []
        for x in range(COLS):
            val = px[x, y]                 # 0=black .. 255=white
            idx = int((255 - val) / 255 * (n - 1))  # dark -> dense glyph
            line.append(RAMP[idx])
        grid.append("".join(line).rstrip())
    return grid


def render():
    grid = load_grid()
    cols = max((len(r) for r in grid), default=COLS)
    width = int(cols * CHAR_W) + 20
    height = int(len(grid) * LINE_H) + 20
    x0 = 10
    y0 = 14

    per_char = 0.010      # seconds per character within a row
    row_stagger = 0.10    # extra delay per row
    defs, texts, cursors = [], [], []

    for r, row in enumerate(grid):
        if not row:
            continue
        row_w = len(row) * CHAR_W
        y = y0 + r * LINE_H
        begin = r * row_stagger
        dur = max(0.25, len(row) * per_char)
        cid = f"clip{r}"
        defs.append(
            f'<clipPath id="{cid}">'
            f'<rect x="{x0}" y="{y - FONT_SIZE}" width="0" height="{LINE_H+2}">'
            f'<animate attributeName="width" from="0" to="{row_w:.1f}" '
            f'begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/>'
            f'</rect></clipPath>'
        )
        texts.append(
            f'<text x="{x0}" y="{y}" clip-path="url(#{cid})" '
            f'xml:space="preserve">{esc(row)}</text>'
        )
        # cursor block rides the wipe edge, then vanishes
        cursors.append(
            f'<rect class="cur" x="{x0}" y="{y - FONT_SIZE + 1}" '
            f'width="{CHAR_W:.1f}" height="{FONT_SIZE}" opacity="0">'
            f'<animate attributeName="x" from="{x0}" to="{x0+row_w:.1f}" '
            f'begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{begin+dur:.2f}s"/>'
            f'</rect>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="ASCII portrait">
  <defs>
{chr(10).join(defs)}
  </defs>
  <style>
    text {{ font-family:{FONT}; font-size:{FONT_SIZE}px; fill:{FILL};
            white-space:pre; letter-spacing:0; }}
    .cur {{ fill:{CURSOR}; }}
  </style>
  <rect x="0" y="0" width="{width}" height="{height}" rx="8" fill="#0d1117"/>
  {chr(10).join(texts)}
  {chr(10).join(cursors)}
</svg>
'''
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[ascii] wrote {OUT}  ({len(grid)} rows x {cols} cols)")


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


if __name__ == "__main__":
    render()
