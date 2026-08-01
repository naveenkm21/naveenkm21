#!/usr/bin/env python3
"""
Render data/contributions.json as an animated 53x7 contribution heatmap SVG.

Rounded boxes reveal once with a diagonal slide-down (CSS keyframes that play
on load, then freeze -- no looping glow). GitHub renders SVG animation when the
file is embedded via <img>, so all motion lives inside this file.
"""
import json
import os
from datetime import datetime

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data", "contributions.json")
OUT = os.path.join(HERE, "..", "contrib-heatmap.svg")

# none -> brightest (level 5 is a neon top end used for your very best days).
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 13          # box size
GAP = 3            # gap between boxes
PAD = 20           # outer padding
TOP = 54           # room for title / weekday labels
BOTTOM = 46        # room for legend + footer
RADIUS = 3
WEEKS = 53
DAYS = 7
FONT = ("ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, "
        "'Liberation Mono', monospace")

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def level_for(count, level):
    # Promote the single best tier to the neon top color for a little pop.
    if count >= 20:
        return 5
    return max(0, min(4, level))


def build_columns(days):
    """Group days into calendar weeks (columns), aligned so row 0 = Sunday."""
    cols = []
    col = [None] * 7
    for d in days:
        wd = datetime.strptime(d["date"], "%Y-%m-%d").weekday()  # Mon=0..Sun=6
        row = (wd + 1) % 7  # shift so Sunday=0, matching GitHub's grid
        col[row] = d
        if row == 6:
            cols.append(col)
            col = [None] * 7
    if any(c is not None for c in col):
        cols.append(col)
    return cols[-WEEKS:]


def month_labels(cols, x0, y):
    """One month tick per column where the month first appears."""
    out = []
    last = None
    for i, col in enumerate(cols):
        first = next((c for c in col if c), None)
        if not first:
            continue
        m = int(first["date"][5:7])
        if m != last:
            last = m
            x = x0 + i * (CELL + GAP)
            out.append(f'<text x="{x}" y="{y}" class="mo">{MONTHS[m-1]}</text>')
    return "\n".join(out)


def render():
    data = load()
    days = data["days"]
    stats = data["stats"]
    cols = build_columns(days)

    grid_w = len(cols) * (CELL + GAP) - GAP
    width = PAD * 2 + grid_w + 30            # +30 for weekday labels gutter
    height = TOP + DAYS * (CELL + GAP) - GAP + BOTTOM
    x0 = PAD + 30
    y0 = TOP

    boxes = []
    max_delay = 0.0
    for ci, col in enumerate(cols):
        for ri in range(DAYS):
            d = col[ri]
            x = x0 + ci * (CELL + GAP)
            y = y0 + ri * (CELL + GAP)
            if d is None:
                fill = PALETTE[0]
                count = 0
            else:
                fill = PALETTE[level_for(d["count"], d["level"])]
                count = d["count"]
            # Diagonal reveal: delay grows with column + row.
            delay = (ci + ri) * 0.018
            max_delay = max(max_delay, delay)
            title = ""
            if d is not None:
                label = "No contributions" if count == 0 else \
                    f"{count} contribution{'s' if count != 1 else ''}"
                title = f"<title>{label} on {d['date']}</title>"
            boxes.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="{RADIUS}" fill="{fill}" class="cell" '
                f'style="animation-delay:{delay:.3f}s">{title}</rect>'
            )

    # Weekday labels (Mon / Wed / Fri, like GitHub).
    wdays = {1: "Mon", 3: "Wed", 5: "Fri"}
    wlabels = []
    for ri, name in wdays.items():
        y = y0 + ri * (CELL + GAP) + CELL - 2
        wlabels.append(f'<text x="{PAD}" y="{y}" class="wd">{name}</text>')

    # Legend (Less [] [] [] [] More) bottom-right.
    legend_y = height - 20
    legend_x = width - PAD - (5 * (CELL + GAP)) - 74
    legend = [f'<text x="{legend_x - 6}" y="{legend_y + CELL - 3}" '
              f'class="lg" text-anchor="end">Less</text>']
    for i, c in enumerate(PALETTE[:5]):
        lx = legend_x + i * (CELL + GAP)
        legend.append(f'<rect x="{lx}" y="{legend_y}" width="{CELL}" '
                      f'height="{CELL}" rx="{RADIUS}" fill="{c}" '
                      f'class="cell" style="animation-delay:'
                      f'{max_delay + 0.05 + i*0.05:.3f}s"/>')
    lx = legend_x + 5 * (CELL + GAP)
    legend.append(f'<text x="{lx + 6}" y="{legend_y + CELL - 3}" '
                  f'class="lg">More</text>')

    total = stats["total"]
    footer = (f'{total:,} contributions in the last year  '
              f'·  current streak {stats["current_streak"]}d  '
              f'·  longest {stats["longest_streak"]}d')

    mlabels = month_labels(cols, x0, TOP - 12)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub contribution heatmap">
  <style>
    .bg   {{ fill:#0d1117; }}
    text  {{ font-family:{FONT}; }}
    .title{{ fill:#c9d1d9; font-size:13px; font-weight:600; }}
    .mo   {{ fill:#8b949e; font-size:10px; }}
    .wd   {{ fill:#8b949e; font-size:9px; }}
    .lg   {{ fill:#8b949e; font-size:10px; }}
    .ft   {{ fill:#7d8590; font-size:11px; }}
    .cell {{ opacity:0; transform:translateY(-6px);
             animation:pop .45s ease-out forwards; }}
    @keyframes pop {{ to {{ opacity:1; transform:translateY(0); }} }}
    @media (prefers-reduced-motion: reduce) {{
      .cell {{ animation:none; opacity:1; transform:none; }}
    }}
  </style>
  <rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="10"/>
  <text x="{PAD}" y="26" class="title">naveen@github ~ $ ./contributions.sh</text>
  {mlabels}
  {chr(10).join(wlabels)}
  {chr(10).join(boxes)}
  {chr(10).join(legend)}
  <text x="{PAD}" y="{height - 20 + CELL - 3}" class="ft">{footer}</text>
</svg>
'''
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[heatmap] wrote {OUT}  ({len(cols)} weeks, {total:,} contributions)")


if __name__ == "__main__":
    render()
