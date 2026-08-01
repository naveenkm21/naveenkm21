#!/usr/bin/env python3
"""
Hand-author a neofetch-style info card SVG.

Keep the *story* here (role, stack, highlights) -- the contribution graph
already covers raw GitHub stats. Each line fades + slides in on a short
stagger so the panel looks like it is printing next to the portrait.

Set STATIC=1 to emit a frozen frame (handy for local previews).
"""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

FONT = ("ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, "
        "'Liberation Mono', monospace")

# neofetch-ish palette
C = {
    "bg": "#0d1117",
    "border": "#30363d",
    "key": "#39d353",   # green keys
    "val": "#c9d1d9",   # light values
    "dim": "#7d8590",   # separators / dim text
    "accent": "#58a6ff",  # blue accents (title, links)
    "yellow": "#e3b341",
}

TITLE = "naveen@github"

# (key, value) rows. Keep values short so they fit ~490px width.
ROWS = [
    ("OS",        "Full-Stack + Android Dev"),
    ("Host",      "Chennai, India"),
    ("Uptime",    "B.Tech CSE @ SRM (in progress)"),
    ("Now",       "Android + Jetpack Compose, ML"),
    ("Prev",      "Spring Boot APIs, React web apps"),
    ("Stack",     "TypeScript · Kotlin · React · Spring"),
    ("DB",        "PostgreSQL · Supabase"),
    ("Learning",  "System design · Cloud · DSA"),
    ("Highlights", "EstateHub · Fitness Tracker · Stock ML"),
    ("Motto",     "Code. Build. Break. Improve. Repeat."),
]

# neofetch color swatch strip (two rows of 8 blocks)
SWATCH = ["#161b22", "#f85149", "#39d353", "#e3b341",
          "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]

PAD = 22
LINE = 22
TITLE_Y = 40
FIRST_ROW_Y = 74
KEY_X = PAD
VAL_X = 132
WIDTH = 490


def anim(delay):
    if STATIC:
        return 'style="opacity:1;transform:none"'
    return f'class="ln" style="animation-delay:{delay:.2f}s"'


def render():
    rows_svg = []
    y = FIRST_ROW_Y
    delay = 0.15
    for key, val in ROWS:
        rows_svg.append(
            f'<g {anim(delay)}>'
            f'<text x="{KEY_X}" y="{y}" class="k">{key}</text>'
            f'<text x="{VAL_X - 12}" y="{y}" class="d">:</text>'
            f'<text x="{VAL_X}" y="{y}" class="v">{esc(val)}</text>'
            f'</g>'
        )
        y += LINE
        delay += 0.14

    # color swatch row
    sw_y = y + 8
    swatches = []
    for i, c in enumerate(SWATCH):
        sx = PAD + i * 22
        swatches.append(f'<rect x="{sx}" y="{sw_y}" width="16" height="16" '
                        f'rx="2" fill="{c}"/>')
    swatch_g = f'<g {anim(delay)}>' + "".join(swatches) + '</g>'
    y = sw_y + 30

    height = y + PAD

    title_bar = (
        f'<g {anim(0.05)}>'
        f'<text x="{PAD}" y="{TITLE_Y}" class="t">{TITLE}</text>'
        f'<text x="{PAD + len(TITLE)*8.4:.0f}" y="{TITLE_Y}" class="d"> </text>'
        f'<text x="{PAD}" y="{TITLE_Y + 8}" class="rule">'
        f'{"-" * 58}</text>'
        f'</g>'
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-label="neofetch-style info card">
  <style>
    text {{ font-family:{FONT}; }}
    .t   {{ fill:{C['accent']}; font-size:15px; font-weight:700; }}
    .rule{{ fill:{C['dim']}; font-size:13px; letter-spacing:0px; }}
    .k   {{ fill:{C['key']}; font-size:13px; font-weight:600; }}
    .v   {{ fill:{C['val']}; font-size:13px; }}
    .d   {{ fill:{C['dim']}; font-size:13px; }}
    .ln  {{ opacity:0; transform:translateX(-8px);
            animation:in .5s ease-out forwards; }}
    @keyframes in {{ to {{ opacity:1; transform:translateX(0); }} }}
    @media (prefers-reduced-motion: reduce) {{
      .ln {{ animation:none; opacity:1; transform:none; }}
    }}
  </style>
  <rect x="1" y="1" width="{WIDTH-2}" height="{height-2}" rx="10"
        fill="{C['bg']}" stroke="{C['border']}" stroke-width="1"/>
  {title_bar}
  {chr(10).join(rows_svg)}
  {swatch_g}
</svg>
'''
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[info-card] wrote {OUT} ({'static' if STATIC else 'animated'})")


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


if __name__ == "__main__":
    render()
