"""
runway_video.py
---------------
Generates a video with the Runway API (Gen-4) so it can be posted to the
Out And About Facebook Page / @cluboutandabout Instagram account.

Usage:
    # Animate an existing flyer (the usual case)
    python runway_video.py --image "docs/media/fb-kit/frivola.jpg" \
        --prompt "slow push in, confetti drifting, neon sign flickering"

    # No flyer? Runway makes the first frame from text, then animates it
    python runway_video.py --prompt "neon cantina at night, warm pink light"

    # Wider or square instead of the 9:16 default
    python runway_video.py --image flyer.jpg --prompt "..." --shape square

How it works:
    1. If you passed a local image, it is uploaded to catbox.moe for a public
       URL (Runway fetches the image itself, same as Instagram does).
    2. If you passed no image, text_to_image makes a first frame first.
    3. image_to_video starts the job, which returns a task id.
    4. We poll the task until it finishes and download the .mp4.

Credentials:
    RUNWAY_API_KEY in your .env file (see docs/runway.md).
"""

import os
import sys
import time
import argparse
from datetime import datetime

import requests
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

API_KEY = os.getenv("RUNWAY_API_KEY")

BASE_URL = "https://api.dev.runwayml.com/v1"
# Runway pins behaviour to a dated version header. If a call starts failing
# with a version error, check docs.dev.runwayml.com and bump this one line.
API_VERSION = "2024-11-06"

VIDEO_MODEL = "gen4_turbo"
IMAGE_MODEL = "gen4_image"

# Runway takes pixel ratios, not "9:16". These are the three we actually use:
# vertical for Reels/Stories/TikTok, square for the feed, wide for the website.
SHAPES = {
    "vertical": {"video": "720:1280", "image": "1080:1920"},
    "square":   {"video": "960:960",  "image": "1080:1080"},
    "wide":     {"video": "1280:720", "image": "1920:1080"},
}

# A finished job usually lands well inside this; a queued one can sit a while.
POLL_SECONDS = 5
TIMEOUT_SECONDS = 15 * 60


def headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "X-Runway-Version": API_VERSION,
        "Content-Type": "application/json",
    }


def upload_image_to_host(image_path: str) -> str:
    """Upload a local image to catbox.moe and return the public URL."""

    print(f"📤 Uploading image to public host (catbox.moe)...")

    with open(image_path, "rb") as f:
        response = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": f},
        )

    if response.status_code == 200 and response.text.startswith("http"):
        url = response.text.strip()
        print(f"✅ Image hosted at: {url}")
        return url

    print(f"❌ Failed to upload image to catbox.moe (status {response.status_code}):")
    print(response.text)
    sys.exit(1)


def start_task(endpoint: str, payload: dict) -> str:
    """POST a generation request and return the task id."""

    response = requests.post(
        f"{BASE_URL}/{endpoint}",
        headers=headers(),
        json=payload,
        timeout=60,
    )

    if response.status_code not in (200, 201):
        print(f"❌ Runway rejected the {endpoint} request (status {response.status_code}):")
        print(response.text)
        # 401 is almost always a missing/typo'd key; 429 is out of credits.
        if response.status_code == 401:
            print("   → Check RUNWAY_API_KEY in your .env file.")
        if response.status_code == 429:
            print("   → Runway is rate-limiting or the account is out of credits.")
        sys.exit(1)

    task_id = response.json().get("id")
    if not task_id:
        print(f"❌ Runway accepted the request but returned no task id: {response.text}")
        sys.exit(1)

    return task_id


def wait_for_task(task_id: str) -> str:
    """Poll a task until it succeeds and return the URL of its output."""

    print(f"⏳ Runway is working (task {task_id})...")
    started = time.time()
    last_status = None

    while True:
        response = requests.get(
            f"{BASE_URL}/tasks/{task_id}",
            headers=headers(),
            timeout=60,
        )

        if response.status_code != 200:
            print(f"❌ Could not read task {task_id} (status {response.status_code}):")
            print(response.text)
            sys.exit(1)

        task = response.json()
        status = task.get("status")

        if status != last_status:
            print(f"   status: {status}")
            last_status = status

        if status == "SUCCEEDED":
            outputs = task.get("output") or []
            if not outputs:
                print(f"❌ Task succeeded but returned no output: {task}")
                sys.exit(1)
            return outputs[0]

        if status in ("FAILED", "CANCELLED"):
            print(f"❌ Runway task {status.lower()}: {task.get('failure') or task}")
            sys.exit(1)

        if time.time() - started > TIMEOUT_SECONDS:
            # The job keeps running on Runway's side — you can pick it up later.
            print(f"❌ Gave up waiting after {TIMEOUT_SECONDS // 60} min. Task id: {task_id}")
            sys.exit(1)

        time.sleep(POLL_SECONDS)


def download(url: str, out_path: str) -> str:
    """Download a finished Runway asset. Its URL expires, so grab it now."""

    print(f"⬇️  Downloading video...")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    with requests.get(url, stream=True, timeout=300) as response:
        response.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                f.write(chunk)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"✅ Saved {out_path} ({size_mb:.1f} MB)")
    return out_path


def generate_first_frame(prompt: str, ratio: str) -> str:
    """Gen-4 video animates a still, so with no flyer we make one first."""

    print("🎨 No image given — generating a first frame from the prompt...")
    task_id = start_task("text_to_image", {
        "model": IMAGE_MODEL,
        "promptText": prompt,
        "ratio": ratio,
    })
    url = wait_for_task(task_id)
    print(f"✅ First frame ready: {url}")
    return url


def generate_video(image_url: str, prompt: str, ratio: str, duration: int, out_path: str) -> str:
    print(f"🎬 Generating a {duration}s video ({ratio})...")
    payload = {
        "model": VIDEO_MODEL,
        "promptImage": image_url,
        "ratio": ratio,
        "duration": duration,
    }
    if prompt:
        payload["promptText"] = prompt

    task_id = start_task("image_to_video", payload)
    video_url = wait_for_task(task_id)
    return download(video_url, out_path)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a video with the Runway API (Gen-4)"
    )
    parser.add_argument("--prompt", type=str, default="",
                        help="What should happen in the shot (camera move, motion, mood)")
    parser.add_argument("--image", type=str,
                        help="Flyer or photo to animate — a local path or a public URL")
    parser.add_argument("--shape", choices=sorted(SHAPES), default="vertical",
                        help="vertical = Reels/Stories (default), square = feed, wide = website")
    parser.add_argument("--duration", type=int, choices=[5, 10], default=5,
                        help="Video length in seconds (Gen-4 supports 5 or 10)")
    parser.add_argument("--out", type=str,
                        help="Where to save the .mp4 (default: code/runway-<timestamp>.mp4)")
    args = parser.parse_args()

    if not API_KEY:
        print("❌ Missing credentials. Make sure RUNWAY_API_KEY is set in your .env file.")
        print("   Setup instructions: docs/runway.md")
        sys.exit(1)

    if not args.image and not args.prompt:
        print("❌ Give me something to work with: --image, --prompt, or both.")
        sys.exit(1)

    ratios = SHAPES[args.shape]

    out_path = args.out or os.path.join(
        "code", f"runway-{datetime.now().strftime('%Y%m%d-%H%M%S')}.mp4"
    )

    # An https:// image is handed to Runway as-is; a local file needs hosting.
    if args.image and args.image.startswith("http"):
        image_url = args.image
    elif args.image:
        if not os.path.exists(args.image):
            print(f"❌ Image not found at: {args.image}")
            sys.exit(1)
        image_url = upload_image_to_host(args.image)
    else:
        image_url = generate_first_frame(args.prompt, ratios["image"])

    path = generate_video(image_url, args.prompt, ratios["video"], args.duration, out_path)

    print()
    print("Next step — post it:")
    print(f'   python code/facebook_post.py --video "{path}" --caption "your caption"')


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as err:
        # Usually no internet, or a firewall between here and Runway.
        print(f"\n❌ Could not reach Runway: {err}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Cancelled. Any job already started keeps running on Runway.")
        sys.exit(1)
