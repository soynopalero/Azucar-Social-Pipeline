"""
facebook_post.py
----------------
Posts a photo + caption to the Out And About Facebook Page
using the Meta Graph API.

Usage:
    python facebook_post.py --image /path/to/image.jpg --caption "Your caption here"

Or edit the IMAGE_PATH and CAPTION variables directly below and run:
    python facebook_post.py
"""

import os
import sys
import argparse
import requests
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

PAGE_ID = os.getenv("FB_PAGE_ID")
PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")

# ── Optional: hardcode for a quick one-off test ──────────────────────────────
# IMAGE_PATH = "/path/to/your/flyer.jpg"
# CAPTION = "Your caption here"
# ─────────────────────────────────────────────────────────────────────────────


def post_photo_to_facebook(image_path: str, caption: str, scheduled_time: int = None):
    """Upload a photo and post it with a caption to the Facebook Page."""

    if not PAGE_ID or not PAGE_ACCESS_TOKEN:
        print("❌ Missing credentials. Make sure FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN are set in your .env file.")
        sys.exit(1)

    if not os.path.exists(image_path):
        print(f"❌ Image not found at: {image_path}")
        sys.exit(1)

    print(f"📸 Uploading image: {image_path}")

    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos"

    data = {
        "caption": caption,
        "access_token": PAGE_ACCESS_TOKEN,
    }

    if scheduled_time:
        data["published"] = "false"
        data["scheduled_publish_time"] = str(scheduled_time)
        print(f"⏰ Scheduling post for Unix timestamp: {scheduled_time}")

    with open(image_path, "rb") as image_file:
        response = requests.post(
            url,
            data=data,
            files={
                "source": image_file,
            }
        )

    result = response.json()

    if "id" in result:
        post_id = result["id"]
        if scheduled_time:
            print(f"✅ Post scheduled successfully!")
        else:
            print(f"✅ Post published successfully!")
        print(f"   Post ID: {post_id}")
        print(f"   View it at: https://www.facebook.com/{PAGE_ID}/posts/{post_id}")
    else:
        print("❌ Something went wrong:")
        print(result)


def post_video_to_facebook(video_path: str, caption: str):
    """Upload a video and post it with a caption to the Facebook Page."""

    if not PAGE_ID or not PAGE_ACCESS_TOKEN:
        print("❌ Missing credentials. Make sure FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN are set in your .env file.")
        sys.exit(1)

    if not os.path.exists(video_path):
        print(f"❌ Video not found at: {video_path}")
        sys.exit(1)

    print(f"🎬 Uploading video: {video_path}")

    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/videos"

    with open(video_path, "rb") as video_file:
        response = requests.post(
            url,
            data={
                "description": caption,
                "access_token": PAGE_ACCESS_TOKEN,
            },
            files={
                "source": video_file,
            },
            timeout=300,
        )

    result = response.json()

    if "id" in result:
        post_id = result["id"]
        print(f"✅ Video published successfully!")
        print(f"   Video ID: {post_id}")
        print(f"   View it at: https://www.facebook.com/{PAGE_ID}/videos/{post_id}")
    else:
        print("❌ Something went wrong:")
        print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post a photo or video to the Out And About Facebook Page")
    parser.add_argument("--image", type=str, help="Path to the image file")
    parser.add_argument("--video", type=str, help="Path to the video file")
    parser.add_argument("--caption", type=str, help="Caption for the post")
    parser.add_argument("--schedule", type=int, help="Unix timestamp to schedule the post for")
    args = parser.parse_args()

    if args.video:
        caption = args.caption if args.caption else CAPTION
        post_video_to_facebook(args.video, caption)
    else:
        image_path = args.image if args.image else IMAGE_PATH
        caption = args.caption if args.caption else CAPTION
        post_photo_to_facebook(image_path, caption, scheduled_time=args.schedule)
