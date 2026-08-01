#!/usr/bin/env python3
"""
Fetch a user's public GitHub contribution calendar -- no token, no GraphQL.

GitHub serves the same calendar fragment the profile page uses at:
    https://github.com/users/<username>/contributions
We scrape the day cells, then write data/contributions.json with the raw
days plus derived stats (streaks, best day, monthly totals).
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "naveenkm21")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
URL = f"https://github.com/users/{USERNAME}/contributions"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (profile-art fetcher)",
    "X-Requested-With": "XMLHttpRequest",
}


def parse_count(text: str) -> int:
    """'4 contributions on January 1st.' -> 4 ; 'No contributions' -> 0."""
    if not text:
        return 0
    m = re.search(r"([\d,]+)\s+contribution", text)
    return int(m.group(1).replace(",", "")) if m else 0


def fetch_days():
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Map each day cell's id -> tooltip text (tooltips hold the exact counts).
    tips = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if target:
            tips[target] = tip.get_text(strip=True)

    days = []
    for cell in soup.select("td.ContributionCalendar-day"):
        d = cell.get("data-date")
        if not d:
            continue
        level = int(cell.get("data-level", 0))
        cid = cell.get("id", "")
        count = parse_count(tips.get(cid, ""))
        # Fallback: some layouts expose the count on the cell itself.
        if count == 0 and level > 0:
            count = parse_count(cell.get("aria-label", ""))
        days.append({"date": d, "count": count, "level": level})

    days.sort(key=lambda x: x["date"])
    return days


def total_from_summary(text_total, days):
    return text_total if text_total is not None else sum(d["count"] for d in days)


def compute_stats(days):
    total = sum(d["count"] for d in days)

    # Streaks (consecutive days with count > 0).
    longest = current = run = 0
    for d in days:
        if d["count"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    # Current streak = trailing run ending on the most recent day.
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        else:
            break

    best = max(days, key=lambda x: x["count"], default={"date": "", "count": 0})

    monthly = {}
    for d in days:
        key = d["date"][:7]  # YYYY-MM
        monthly[key] = monthly.get(key, 0) + d["count"]

    active_days = sum(1 for d in days if d["count"] > 0)
    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": active_days,
        "monthly": monthly,
    }


def main():
    try:
        days = fetch_days()
    except Exception as e:  # noqa: BLE001
        print(f"[fetch] error: {e}", file=sys.stderr)
        sys.exit(1)

    if not days:
        print("[fetch] no day cells parsed -- GitHub markup may have changed",
              file=sys.stderr)
        sys.exit(1)

    payload = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "days": days,
        "stats": compute_stats(days),
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    s = payload["stats"]
    print(f"[fetch] {len(days)} days, {s['total']} contributions, "
          f"current streak {s['current_streak']}, longest {s['longest_streak']}")


if __name__ == "__main__":
    main()
