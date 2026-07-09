"""
Flyer sync: move Telegram photos onto a Monday item's flyer column, then flag
captions for regeneration. Dispatched by the bot's /update flow — Cloudflare
Workers kill background work after ~30s, which is not enough to shuttle 9
photos, so the heavy lifting happens here.

Env: MONDAY_API_KEY, TELEGRAM_BOT_TOKEN
     ITEM_ID, TG_FILE_IDS (comma-separated, hero first), NOTIFY_CHAT_ID (optional)
"""
from __future__ import annotations

import json
import os
import sys

import requests

MONDAY_API = "https://api.monday.com/v2"
MONDAY_FILE_API = "https://api.monday.com/v2/file"

BOARD_ID = "18414182966"
COL_FLYER = "file_mm4nnwtq"
COL_CAPTION_STATUS = "text_mm4wk4kr"

MONDAY_KEY = os.environ.get("MONDAY_API_KEY", "").strip()
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
ITEM_ID = os.environ.get("ITEM_ID", "").strip()
FILE_IDS = [f.strip() for f in os.environ.get("TG_FILE_IDS", "").split(",") if f.strip()]
NOTIFY_CHAT_ID = os.environ.get("NOTIFY_CHAT_ID", "").strip()


def monday_gql(query: str, variables: dict) -> dict:
    r = requests.post(MONDAY_API, timeout=60,
                      headers={"Authorization": MONDAY_KEY, "API-Version": "2024-10",
                               "Content-Type": "application/json"},
                      json={"query": query, "variables": variables})
    body = r.json()
    if body.get("errors"):
        raise RuntimeError(json.dumps(body["errors"]))
    return body["data"]


def tg_download(file_id: str) -> tuple[str, bytes]:
    info = requests.get(f"https://api.telegram.org/bot{TG_TOKEN}/getFile",
                        params={"file_id": file_id}, timeout=30).json()
    path = info.get("result", {}).get("file_path")
    if not path:
        raise RuntimeError(f"getFile failed for {file_id}: {json.dumps(info)[:200]}")
    data = requests.get(f"https://api.telegram.org/file/bot{TG_TOKEN}/{path}", timeout=120)
    data.raise_for_status()
    name = path.split("/")[-1] or "flyer.jpg"
    return name, data.content


def monday_upload(item_id: str, filename: str, content: bytes) -> None:
    query = (f'mutation ($file: File!) {{ add_file_to_column('
             f'item_id: {item_id}, column_id: "{COL_FLYER}", file: $file) {{ id }} }}')
    r = requests.post(MONDAY_FILE_API, timeout=120,
                      headers={"Authorization": MONDAY_KEY},
                      data={"query": query, "map": json.dumps({"image": "variables.file"})},
                      files={"image": (filename, content, "image/jpeg")})
    body = r.json()
    if body.get("errors") or not body.get("data", {}).get("add_file_to_column"):
        raise RuntimeError(f"upload failed: {json.dumps(body)[:300]}")


def pick_hero(photos: list) -> int:
    """Vision: which image is the main/full-cast flyer? People can't control
    album order on their phones, so the machine decides what goes first
    (= the website hero image). Returns an index; 0 on any failure."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key or len(photos) < 2:
        return 0
    import base64
    import re
    content = [{"type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg",
                           "data": base64.b64encode(c).decode()}}
               for _, c in photos[:10]]
    content.append({"type": "text", "text":
        f"These are {len(photos[:10])} flyers for one nightlife event. Exactly one is the MAIN/hero "
        "flyer — the full-cast or title artwork representing the whole event; the others are "
        "individual performer spotlights or variants. "
        'Reply with ONLY JSON: {"hero": <1-based image number>}'})
    try:
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=120,
                          headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                                   "content-type": "application/json"},
                          json={"model": "claude-sonnet-5", "max_tokens": 500,
                                "messages": [{"role": "user", "content": content}]})
        data = r.json()
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        m = re.search(r'"hero"\s*:\s*(\d+)', text)
        if m:
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(photos):
                return idx
        print(f"hero pick: no usable answer ({text[:120]!r}); keeping sent order")
    except Exception as ex:
        print(f"hero pick failed ({ex}); keeping sent order")
    return 0


def notify(text: str) -> None:
    if not (TG_TOKEN and NOTIFY_CHAT_ID):
        return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", timeout=15,
                      json={"chat_id": NOTIFY_CHAT_ID, "text": text})
    except requests.RequestException as e:
        print(f"notify failed: {e}")


def main() -> int:
    if not (MONDAY_KEY and TG_TOKEN and ITEM_ID and FILE_IDS):
        sys.exit("Missing MONDAY_API_KEY / TELEGRAM_BOT_TOKEN / ITEM_ID / TG_FILE_IDS")

    print(f"Downloading {len(FILE_IDS)} photos from Telegram...")
    photos = [tg_download(fid) for fid in FILE_IDS]

    hero = pick_hero(photos)
    if hero:
        photos.insert(0, photos.pop(hero))
        print(f"Hero flyer detected at position {hero + 1} of the batch — moved to front.")
    else:
        print("Hero flyer: keeping first-sent as the hero.")

    print("Clearing the flyer column...")
    monday_gql(
        """mutation($b: ID!, $i: ID!, $c: String!, $v: JSON!) {
             change_column_value(board_id: $b, item_id: $i, column_id: $c, value: $v) { id } }""",
        {"b": BOARD_ID, "i": ITEM_ID, "c": COL_FLYER, "v": json.dumps({"clear_all": True})})

    for idx, (name, content) in enumerate(photos, 1):
        print(f"Uploading {idx}/{len(photos)}: {name} ({len(content)} bytes)")
        monday_upload(ITEM_ID, name, content)

    print("Flagging captions for regeneration...")
    monday_gql(
        """mutation($b: ID!, $i: ID!, $c: String!, $v: String!) {
             change_simple_column_value(board_id: $b, item_id: $i, column_id: $c, value: $v) { id } }""",
        {"b": BOARD_ID, "i": ITEM_ID, "c": COL_CAPTION_STATUS, "v": "regenerate"})

    notify(f"🖼 {len(photos)} new flyers are on the event — I picked the full-cast/main art "
           "as the website hero image. Fresh captions are being drafted from them now and "
           "will arrive here for approval shortly.")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
