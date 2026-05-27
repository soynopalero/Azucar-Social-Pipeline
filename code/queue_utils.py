"""
queue_utils.py
--------------
Shared helpers for the post-scheduler pipeline.

Queue file: posts_queue.json at the repo root.
"""

import json
import os
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
QUEUE_PATH = REPO_ROOT / "posts_queue.json"
LOCAL_TZ = ZoneInfo("America/Los_Angeles")


def load_queue() -> dict:
    if not QUEUE_PATH.exists():
        return {"posts": []}
    with open(QUEUE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_queue(queue: dict):
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
    # Mirror to docs/ so the GitHub Pages dashboard can fetch it from same dir
    docs_copy = REPO_ROOT / "docs" / "posts_queue.json"
    docs_copy.parent.mkdir(exist_ok=True)
    with open(docs_copy, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)


def new_post_id(scheduled_dt_utc: datetime) -> str:
    stamp = scheduled_dt_utc.strftime("%Y%m%d_%H%M%S")
    suffix = secrets.token_hex(3)
    return f"{stamp}_{suffix}"


def parse_local_time(when: str) -> datetime:
    """Parse 'YYYY-MM-DD HH:MM' as Pacific time, return timezone-aware datetime."""
    try:
        naive = datetime.strptime(when, "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            naive = datetime.strptime(when, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"❌ Could not parse time '{when}'. Use format: YYYY-MM-DD HH:MM (Pacific time)")
            print("   Example: 2026-06-13 16:00")
            sys.exit(1)
    return naive.replace(tzinfo=LOCAL_TZ)


def to_utc_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def from_utc_iso(s: str) -> datetime:
    return datetime.fromisoformat(s)


def fmt_local(dt_utc_iso: str) -> str:
    dt = from_utc_iso(dt_utc_iso).astimezone(LOCAL_TZ)
    return dt.strftime("%Y-%m-%d %H:%M %Z")


def upload_image_to_catbox(image_path: str) -> str:
    """Upload local image to catbox.moe, return public URL."""
    print(f"📤 Uploading image to catbox.moe...")
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        sys.exit(1)
    with open(image_path, "rb") as f:
        response = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": f},
            timeout=120,
        )
    if response.status_code == 200 and response.text.startswith("http"):
        url = response.text.strip()
        print(f"✅ Hosted at: {url}")
        return url
    print(f"❌ catbox.moe upload failed (status {response.status_code}):")
    print(response.text)
    sys.exit(1)


def git_commit_and_push(message: str):
    """Stage posts_queue.json, commit, and push. Skips push if no remote/network."""
    try:
        subprocess.run(
            ["git", "add", str(QUEUE_PATH)],
            cwd=REPO_ROOT, check=True, capture_output=True, text=True,
        )
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        if result.returncode != 0:
            if "nothing to commit" in result.stdout + result.stderr:
                print("ℹ️  No queue changes to commit.")
                return
            print(f"❌ git commit failed:\n{result.stdout}\n{result.stderr}")
            sys.exit(1)
        print("✅ Committed queue update locally.")
        push = subprocess.run(
            ["git", "push"],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        if push.returncode != 0:
            print(f"⚠️  git push failed (queue saved locally, push manually later):")
            print(push.stderr)
        else:
            print("🚀 Pushed to GitHub — cloud workflow will pick it up.")
    except FileNotFoundError:
        print("⚠️  git not found on PATH — queue saved locally only.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  git operation failed: {e.stderr}")
