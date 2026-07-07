#!/usr/bin/env python3
"""
build_events.py  —  Adapter: turn the pipeline's flat posts_queue.json into the
event-grouped shape the Post Manager UI consumes (manager/events.json).

In production this same grouping logic runs inside a Cloudflare Pages Function
that reads the live queue (and, later, event names/dates from the Monday board).
For the local prototype it writes a static events.json plus a few clearly-marked
SAMPLE upcoming events so the active board is clickable even though the real
queue is entirely in the past.

Logical post = one card row. Instagram + Facebook entries that share the same
scheduled time + caption are MERGED into a single logical post that carries both
platforms (and remembers both underlying queue ids), matching the UI where one
row has IG/FB chips and the editor has IG/FB toggles.
"""
import json, io, os, datetime, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
QUEUE = os.path.join(ROOT, "posts_queue.json")
OUT = os.path.join(HERE, "events.json")

PACIFIC = datetime.timezone(datetime.timedelta(hours=-7))  # PDT (display only, prototype)

# Real campaigns we know how to name/date. Everything else with a campaign gets
# a best-effort name; standalone posts get bucketed into one archived event.
CAMPAIGN_META = {
    "vida_amore_june_20": {
        "name": "Orgullo LGBTQ+: El Tributo — Vida Amore",
        "event_date": "2026-06-20",
        "tag": "👑 Drag",
        "flyer_grad": "linear-gradient(135deg,#7B2FF0,#2b6cf0)",
    },
}


def load_queue():
    with io.open(QUEUE, encoding="utf-8") as f:
        return json.load(f)["posts"]


def merge_logical(posts):
    """Merge IG+FB twins (same time + caption) into one logical post."""
    buckets = {}
    order = []
    for p in posts:
        key = (p["scheduled_for_utc"], p["caption"])
        if key not in buckets:
            buckets[key] = {
                "ids": [],
                "platforms": [],
                "scheduled_for_utc": p["scheduled_for_utc"],
                "caption": p["caption"],
                "image_url": p.get("image_url"),
                "images": [],
                "status": p["status"],
                "result": p.get("result", ""),
            }
            order.append(key)
        b = buckets[key]
        b["ids"].append(p["id"])
        if p["platform"] not in b["platforms"]:
            b["platforms"].append(p["platform"])
        if p.get("image_url") and p["image_url"] not in b["images"]:
            b["images"].append(p["image_url"])
        # status precedence: failed > pending > posted (surface problems)
        rank = {"failed": 2, "pending": 1, "posted": 0}
        if rank.get(p["status"], 0) > rank.get(b["status"], 0):
            b["status"] = p["status"]
            b["result"] = p.get("result", "")
    return [buckets[k] for k in order]


def display_time(iso):
    dt = datetime.datetime.fromisoformat(iso).astimezone(PACIFIC)
    return dt.strftime("%a %b %-d · %-I:%M %p") if os.name != "nt" else dt.strftime("%a %b %d · %I:%M %p").replace(" 0", " ")


def build_real_events(posts):
    by_campaign = {}
    standalone = []
    for p in posts:
        c = p.get("campaign")
        if c:
            by_campaign.setdefault(c, []).append(p)
        else:
            standalone.append(p)

    events = []
    for camp, plist in by_campaign.items():
        meta = CAMPAIGN_META.get(camp, {})
        logical = merge_logical(plist)
        logical.sort(key=lambda x: x["scheduled_for_utc"])
        event_date = meta.get("event_date") or max(p["scheduled_for_utc"] for p in plist)[:10]
        events.append({
            "id": camp,
            "name": meta.get("name", camp.replace("_", " ").title()),
            "event_date": event_date,
            "tag": meta.get("tag", "✨ Event"),
            "flyer_grad": meta.get("flyer_grad", "linear-gradient(135deg,#E5195E,#FF7A2F)"),
            "source": "real",
            "posts": [to_ui_post(l) for l in logical],
        })

    if standalone:
        logical = merge_logical(standalone)
        logical.sort(key=lambda x: x["scheduled_for_utc"])
        events.append({
            "id": "spring_2026_oneoffs",
            "name": "Earlier one-off posts (Spring 2026)",
            "event_date": max(p["scheduled_for_utc"] for p in standalone)[:10],
            "tag": "🗂️ One-offs",
            "flyer_grad": "linear-gradient(135deg,#2F9E6B,#7B2FF0)",
            "source": "real",
            "posts": [to_ui_post(l) for l in logical],
        })
    return events


def to_ui_post(l):
    return {
        "ids": l["ids"],
        "platforms": l["platforms"],
        "scheduled_for_utc": l["scheduled_for_utc"],
        "scheduled_display": display_time(l["scheduled_for_utc"]),
        "images": l["images"] or ([l["image_url"]] if l["image_url"] else []),
        "caption": l["caption"],
        "status": l["status"],
        "result": l["result"],
    }


def sample_events():
    """Clearly-marked SAMPLE upcoming events so the active board is clickable.
    Dates are relative to 'now' so the demo always has live content. These are
    NOT in your real queue — they're removed the moment we wire live data."""
    now = datetime.datetime.now(datetime.timezone.utc)

    def slot(days, hour_pt, plats, status, cap, grad):
        dt = (now + datetime.timedelta(days=days)).astimezone(PACIFIC).replace(
            hour=hour_pt, minute=0, second=0, microsecond=0)
        utc = dt.astimezone(datetime.timezone.utc)
        return {
            "ids": ["sample_" + hashlib.md5((cap[:20]+str(days)+str(hour_pt)).encode()).hexdigest()[:6]],
            "platforms": plats,
            "scheduled_for_utc": utc.isoformat(),
            "scheduled_display": dt.strftime("%a %b %d · %I:%M %p").replace(" 0", " "),
            "images": [],
            "image_grad": grad,
            "caption": cap,
            "status": status,
            "result": "",
        }

    return [
        {
            "id": "noche_vaquera_sample", "name": "Noche Vaquera", "tag": "🤠 Monthly",
            "event_date": (now + datetime.timedelta(days=6)).date().isoformat(),
            "flyer_grad": "linear-gradient(135deg,#B70F49,#FF7A2F)", "source": "sample",
            "posts": [
                slot(1, 19, ["instagram", "facebook"], "pending", "Ponte las botas 🤠 Noche Vaquera regresa. Cumbia, banda y mucho perreo. Sábado — puertas 9PM.", "linear-gradient(135deg,#B70F49,#FF7A2F)"),
                slot(3, 15, ["instagram"], "pending", "Se viene lo bueno 🐎 ¿Ya tienes tu sombrero listo?", "linear-gradient(135deg,#7B2FF0,#2b6cf0)"),
                slot(6, 11, ["instagram", "facebook"], "pending", "HOY nos ponemos vaqueros. 9PM. Trae al crew. 🤠🔥", "linear-gradient(135deg,#FF7A2F,#E9930B)"),
            ],
        },
        {
            "id": "vida_amore_sample", "name": "Vida Amore · Summer Drag", "tag": "👑 Drag",
            "event_date": (now + datetime.timedelta(days=13)).date().isoformat(),
            "flyer_grad": "linear-gradient(135deg,#7B2FF0,#E5195E)", "source": "sample",
            "posts": [
                slot(4, 19, ["instagram", "facebook"], "pending", "Las reinas regresan 👑 Vida Amore — una noche de puro glamour. Reserva tu mesa por DM.", "linear-gradient(135deg,#7B2FF0,#E5195E)"),
                slot(9, 11, ["instagram", "facebook"], "pending", "El escenario está listo 💅 ¿Y tú?", "linear-gradient(135deg,#E5195E,#FF7A2F)"),
            ],
        },
        {
            "id": "social_sundays_sample", "name": "Social Sundays", "tag": "☀️ Weekly",
            "event_date": (now + datetime.timedelta(days=3)).date().isoformat(),
            "flyer_grad": "linear-gradient(135deg,#2F9E6B,#2b6cf0)", "source": "sample",
            "posts": [
                slot(2, 15, ["instagram"], "pending", "Domingo relajado con los tuyos ☀️ 2x1 en margaritas hasta las 8.", "linear-gradient(135deg,#2F9E6B,#E9930B)"),
            ],
        },
    ]


def main():
    posts = load_queue()
    events = build_real_events(posts) + sample_events()
    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "note": "Prototype data. 'real' events come from your live posts_queue.json; 'sample' events are demo-only and vanish when live data is wired.",
        "events": events,
    }
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUT} — {len(events)} events "
          f"({sum(1 for e in events if e['source']=='real')} real, "
          f"{sum(1 for e in events if e['source']=='sample')} sample)")


if __name__ == "__main__":
    main()
