"""
refresh_token.py
----------------
Exchanges a short-lived User access token for a NON-EXPIRING Page access token
and writes it back to .env as FB_PAGE_ACCESS_TOKEN.

How Meta's token system works:
    short-lived User token (~1 hour)
        --> exchange via fb_exchange_token --> long-lived User token (~60 days)
        --> call /me/accounts --> Page token (NO expiration)

The Page token returned by /me/accounts has no expiration as long as:
    - you remain admin of the Page
    - you don't change your Facebook password
    - the app stays authorized

Usage:
    python refresh_token.py --user-token "EAA...."

You get the user-token from https://developers.facebook.com/tools/explorer/
(set "User or Page" to "User Token", click "Generate Access Token").
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

APP_ID = os.getenv("FB_APP_ID")
APP_SECRET = os.getenv("FB_APP_SECRET")
PAGE_ID = os.getenv("FB_PAGE_ID")

API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"


def exchange_for_long_lived_user_token(short_lived_token: str) -> str:
    print("🔄 Exchanging short-lived User token for long-lived User token (60 days)...")
    response = requests.get(
        f"{BASE_URL}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": APP_ID,
            "client_secret": APP_SECRET,
            "fb_exchange_token": short_lived_token,
        },
    )
    data = response.json()
    if "access_token" not in data:
        print("❌ Failed to get long-lived User token:")
        print(data)
        sys.exit(1)
    print(f"✅ Got long-lived User token (expires in ~{data.get('expires_in', 'unknown')} seconds)")
    return data["access_token"]


def get_page_token(long_lived_user_token: str, page_id: str) -> str:
    print(f"🔄 Fetching Page token for Page ID {page_id}...")
    response = requests.get(
        f"{BASE_URL}/me/accounts",
        params={"access_token": long_lived_user_token},
    )
    data = response.json()
    if "data" not in data:
        print("❌ Failed to fetch Page accounts:")
        print(data)
        sys.exit(1)

    for page in data["data"]:
        if str(page.get("id")) == str(page_id):
            print(f"✅ Found Page: {page.get('name')}")
            return page["access_token"]

    print(f"❌ Page ID {page_id} not found in your account list. Pages available:")
    for page in data["data"]:
        print(f"   - {page.get('name')} (id: {page.get('id')})")
    sys.exit(1)


def verify_token_never_expires(page_token: str):
    print("🔍 Verifying Page token has no expiration...")
    response = requests.get(
        f"{BASE_URL}/debug_token",
        params={
            "input_token": page_token,
            "access_token": f"{APP_ID}|{APP_SECRET}",
        },
    )
    data = response.json().get("data", {})
    expires_at = data.get("expires_at", 0)
    if expires_at == 0:
        print("✅ Confirmed: Page token does NOT expire 🎉")
    else:
        import datetime
        when = datetime.datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M:%S")
        print(f"⚠️  Page token expires at {when} (unexpected — admin role may be missing)")
    scopes = data.get("scopes", [])
    print(f"   Scopes: {', '.join(scopes)}")


def update_env_file(new_page_token: str):
    print(f"💾 Updating {ENV_PATH} with new FB_PAGE_ACCESS_TOKEN...")
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("FB_PAGE_ACCESS_TOKEN="):
            lines[i] = f"FB_PAGE_ACCESS_TOKEN={new_page_token}"
            updated = True
            break
    if not updated:
        lines.append(f"FB_PAGE_ACCESS_TOKEN={new_page_token}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("✅ .env updated")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Refresh Page token to a non-expiring one")
    parser.add_argument("--user-token", type=str, required=True, help="Short-lived User token from Graph API Explorer")
    args = parser.parse_args()

    if not (APP_ID and APP_SECRET and PAGE_ID):
        print("❌ Missing FB_APP_ID, FB_APP_SECRET, or FB_PAGE_ID in .env")
        sys.exit(1)

    long_lived = exchange_for_long_lived_user_token(args.user_token)
    page_token = get_page_token(long_lived, PAGE_ID)
    verify_token_never_expires(page_token)
    update_env_file(page_token)

    print("\n🎉 Done. Your FB_PAGE_ACCESS_TOKEN should now last indefinitely.")
    print("   You can post to Instagram with: python instagram_post.py --image ... --caption ...")
