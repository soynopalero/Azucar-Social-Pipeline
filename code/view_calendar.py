"""
view_calendar.py
----------------
Generates a self-contained HTML calendar of upcoming posts and opens it in your
default browser.

Usage:
    python view_calendar.py              # opens browser to the calendar
    python view_calendar.py --no-open    # generates file but doesn't open

Reads posts_queue.json. Renders a 2-month calendar (current + next month) with
each post as a clickable cell showing the flyer thumbnail, time, and caption.
"""

import argparse
import calendar
import html
import json
import webbrowser
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parent.parent
QUEUE_PATH = REPO_ROOT / "posts_queue.json"
OUTPUT_PATH = REPO_ROOT / "posts_calendar.html"
LOCAL_TZ = ZoneInfo("America/Los_Angeles")

STATUS_COLORS = {
    "pending": "#f5b800",
    "posted": "#34c759",
    "failed": "#ff3b30",
}


def load_posts():
    if not QUEUE_PATH.exists():
        return []
    with open(QUEUE_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("posts", [])


def group_by_day(posts):
    """Return {date_obj: [post, ...]} keyed by local-date."""
    grouped = defaultdict(list)
    for p in posts:
        dt_local = datetime.fromisoformat(p["scheduled_for_utc"]).astimezone(LOCAL_TZ)
        grouped[dt_local.date()].append((dt_local, p))
    for day in grouped:
        grouped[day].sort(key=lambda x: x[0])
    return grouped


def render_month(year, month, grouped, today):
    cal = calendar.Calendar(firstweekday=6)  # Sunday-first
    weeks = cal.monthdatescalendar(year, month)
    month_name = calendar.month_name[month]

    rows_html = []
    for week in weeks:
        cells = []
        for day in week:
            in_month = (day.month == month)
            is_today = (day == today)
            classes = ["day"]
            if not in_month:
                classes.append("other-month")
            if is_today:
                classes.append("today")

            posts_today = grouped.get(day, [])
            posts_html_parts = []
            for dt_local, p in posts_today:
                color = STATUS_COLORS.get(p["status"], "#999")
                time_str = dt_local.strftime("%I:%M%p").lstrip("0").lower()
                caption_first_line = p["caption"].split("\n", 1)[0][:80]
                caption_full_attr = html.escape(p["caption"][:500])
                image = html.escape(p["image_url"])
                post_id = html.escape(p["id"])
                status = p["status"]
                posts_html_parts.append(
                    f'<div class="post {status}" style="border-left-color:{color};" '
                    f'title="{caption_full_attr}" data-id="{post_id}">'
                    f'<img src="{image}" loading="lazy" />'
                    f'<div class="post-meta">'
                    f'<span class="time">{html.escape(time_str)}</span>'
                    f'<span class="caption">{html.escape(caption_first_line)}</span>'
                    f'</div>'
                    f'</div>'
                )
            posts_block = "\n".join(posts_html_parts)
            cells.append(
                f'<td class="{" ".join(classes)}">'
                f'<div class="day-num">{day.day}</div>'
                f'{posts_block}'
                f'</td>'
            )
        rows_html.append("<tr>" + "".join(cells) + "</tr>")

    rows_str = "\n".join(rows_html)
    return f"""
    <section class="month">
      <h2>{month_name} {year}</h2>
      <table>
        <thead>
          <tr><th>Sun</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th></tr>
        </thead>
        <tbody>
        {rows_str}
        </tbody>
      </table>
    </section>
    """


def build_html(posts):
    today = datetime.now(LOCAL_TZ).date()
    grouped = group_by_day(posts)

    # Current month + next month
    months_to_show = [(today.year, today.month)]
    nxt = today.replace(day=28) + timedelta(days=4)
    months_to_show.append((nxt.year, nxt.month))

    months_html = "\n".join(render_month(y, m, grouped, today) for y, m in months_to_show)

    counts = {"pending": 0, "posted": 0, "failed": 0}
    for p in posts:
        counts[p["status"]] = counts.get(p["status"], 0) + 1

    generated_at = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %I:%M %p %Z")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Azucar Social Pipeline — Calendar</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #fafaf7;
    color: #1a1a1a;
    margin: 0;
    padding: 2rem;
    max-width: 1400px;
    margin-inline: auto;
  }}
  header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 1rem;
    margin-bottom: 2rem;
  }}
  h1 {{ font-size: 1.5rem; margin: 0; font-weight: 600; }}
  .meta {{ color: #666; font-size: 0.85rem; }}
  .stats {{ display: flex; gap: 1rem; margin-top: 0.5rem; font-size: 0.9rem; }}
  .stat {{ display: inline-flex; align-items: center; gap: 0.4rem; }}
  .stat-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
  .month {{ margin-bottom: 3rem; }}
  h2 {{ font-size: 1.1rem; font-weight: 500; color: #444; margin-bottom: 0.75rem; }}
  table {{ width: 100%; border-collapse: collapse; }}
  thead th {{
    padding: 0.5rem;
    text-align: left;
    font-weight: 500;
    color: #888;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid #e0e0e0;
  }}
  td {{
    vertical-align: top;
    border: 1px solid #ececec;
    height: 130px;
    width: 14.28%;
    padding: 0.4rem;
    background: white;
    position: relative;
  }}
  td.other-month {{ background: #f4f4f0; color: #bbb; }}
  td.today {{ background: #fffbea; }}
  td.today .day-num {{ color: #b07700; font-weight: 700; }}
  .day-num {{ font-size: 0.85rem; color: #888; margin-bottom: 0.3rem; }}
  .post {{
    background: #f7f7f4;
    border-left: 3px solid #999;
    border-radius: 3px;
    padding: 0.25rem;
    margin-bottom: 0.25rem;
    font-size: 0.7rem;
    display: flex;
    gap: 0.3rem;
    overflow: hidden;
    cursor: pointer;
    transition: background 0.15s;
  }}
  .post:hover {{ background: #efece6; }}
  .post img {{
    width: 32px;
    height: 32px;
    object-fit: cover;
    border-radius: 2px;
    flex-shrink: 0;
  }}
  .post-meta {{ overflow: hidden; flex: 1; }}
  .post .time {{ display: block; font-weight: 600; color: #333; }}
  .post .caption {{
    display: block;
    color: #666;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .post.posted {{ opacity: 0.65; }}
  .post.failed {{ background: #ffe9e9; }}
  footer {{
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #e0e0e0;
    color: #999;
    font-size: 0.8rem;
  }}
  code {{ background: #ececec; padding: 1px 5px; border-radius: 3px; font-size: 0.85em; }}
</style>
</head>
<body>
<header>
  <div>
    <h1>Azúcar Social Pipeline</h1>
    <div class="stats">
      <span class="stat"><span class="stat-dot" style="background:{STATUS_COLORS['pending']}"></span>Pending: {counts['pending']}</span>
      <span class="stat"><span class="stat-dot" style="background:{STATUS_COLORS['posted']}"></span>Posted: {counts['posted']}</span>
      <span class="stat"><span class="stat-dot" style="background:{STATUS_COLORS['failed']}"></span>Failed: {counts['failed']}</span>
    </div>
  </div>
  <div class="meta">Generated {generated_at}</div>
</header>
{months_html}
<footer>
  Refresh by running <code>python code/view_calendar.py</code>. Hover any post to see the full caption.
</footer>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Generate an HTML calendar of upcoming posts")
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open in browser")
    args = parser.parse_args()

    posts = load_posts()
    print(f"📅 Loaded {len(posts)} post(s) from queue")

    html_content = build_html(posts)
    OUTPUT_PATH.write_text(html_content, encoding="utf-8")
    print(f"✅ Wrote {OUTPUT_PATH}")

    if not args.no_open:
        webbrowser.open(f"file://{OUTPUT_PATH.as_posix()}")
        print(f"🌐 Opening in browser...")


if __name__ == "__main__":
    main()
