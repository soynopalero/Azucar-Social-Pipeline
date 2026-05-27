"""
instagram_post.py
-----------------
Posts a photo + caption to the @cluboutandabout Instagram account
using the Meta Graph API.

Usage:
    python instagram_post.py --image "path/to/image.jpg" --caption "Your caption here"

How it works:
    1. Uploads your image to Imgur (free, no account needed)
    2. Gives Instagram that public URL
    3. Instagram fetches it and publishes the post
"""

import os
import sys
import argparse
import requests
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()

PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")

API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

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
    else:
        print(f"❌ Failed to upload image to catbox.moe (status {response.status_code}):")
        print(response.text)
        sys.exit(1)


def post_photo_to_instagram(image_path: str, caption: str):
    """Post a photo with caption to Instagram using the Meta Graph API."""

    if not PAGE_ACCESS_TOKEN or not IG_USER_ID:
        print("❌ Missing credentials. Make sure FB_PAGE_ACCESS_TOKEN and IG_USER_ID are set in your .env file.")
        sys.exit(1)

    if not os.path.exists(image_path):
        print(f"❌ Image not found at: {image_path}")
        sys.exit(1)

    # Step 1: Upload image to a public host to get a public URL
    image_url = upload_image_to_host(image_path)

    # Step 2: Create a media container on Instagram
    print("📸 Creating Instagram media container...")
    container_response = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": PAGE_ACCESS_TOKEN,
        }
    )

    container_result = container_response.json()

    if "id" not in container_result:
        print("❌ Failed to create media container:")
        print(container_result)
        sys.exit(1)

    container_id = container_result["id"]
    print(f"✅ Media container created: {container_id}")

    # Step 3: Publish the container (this makes it go live on Instagram)
    print("🚀 Publishing to Instagram...")
    publish_response = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": PAGE_ACCESS_TOKEN,
        }
    )

    publish_result = publish_response.json()

    if "id" in publish_result:
        print(f"✅ Posted to Instagram successfully!")
        print(f"   View it at: https://www.instagram.com/cluboutandabout/")
    else:
        print("❌ Something went wrong publishing to Instagram:")
        print(publish_result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post a photo to @cluboutandabout on Instagram")
    parser.add_argument("--image", type=str, required=True, help="Path to the image file")
    parser.add_argument("--caption", type=str, required=True, help="Caption for the post")
    args = parser.parse_args()

    post_photo_to_instagram(args.image, args.caption)
