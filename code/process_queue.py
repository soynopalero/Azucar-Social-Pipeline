"""
process_queue.py
----------------
Cloud worker — invoked by the GitHub Actions cron every 15 minutes.
Reads posts_queue.json, posts anything that's due (status=pending and
scheduled_for_utc <= now), updates the queue, and exits.

The GitHub Actions workflow handles committing the updated queue back.

Credentials are read from environment variables (set as GitHub repo secrets):
    FB_PAGE_ACCESS_TOKEN, IG_USER_ID, FB_PAGE_ID
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from queue_utils import load_queue, save_queue, from_utc_iso

# Load .env when running locally (no-op in GitHub Actions where env is set natively)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"


# Meta returns transient failures that look permanent. On 2026-09-08 four
# posts died on code 190 ("This Page access token belongs to a Page that is
# not accessible") while four others in the same run used the same token
# successfully ~30s later. Recorded as failed, they would never have been
# retried, and the promo for two upcoming events was simply lost.
#
# Meta flags many of these itself with is_transient; the explicit codes cover
# the ones it does not. 190 is included deliberately: it is also the code for a
# genuinely expired token, and retrying that costs a minute before failing —
# far cheaper than silently dropping a post that would have gone out.
TRANSIENT_META_CODES = {1, 2, 4, 17, 32, 190, 324, 341, 368, 613}

POST_ATTEMPTS = 4
POST_BACKOFF = 10.0  # seconds; waits 10s, 20s, 30s — covers a ~1 min wobble

# How many scheduler runs a post may stay pending on transient errors before
# it is called failed. At one run per 5 minutes this is ~30 minutes of trying,
# which spans a Meta blip without leaving a post retrying forever against a
# token that is actually dead.
MAX_TRANSIENT_CYCLES = 6


def is_transient_meta_error(body: dict) -> bool:
    """True if a Graph API error body describes a failure worth retrying."""
    err = (body or {}).get("error")
    if not isinstance(err, dict):
        return False
    if err.get("is_transient") is True:
        return True
    return err.get("code") in TRANSIENT_META_CODES


def graph_post(url: str, data: dict, *, what: str, timeout: int = 120) -> dict:
    """POST to the Graph API, retrying transient errors.

    ONLY for calls that create nothing when they fail — the Facebook /photos
    call and the Instagram container creation. Retrying a call that may have
    partially succeeded would double-post, which is worse than the bug this
    fixes, so media_publish keeps its own narrower retry and is not routed here.
    """
    body: dict = {}
    for attempt in range(1, POST_ATTEMPTS + 1):
        try:
            body = requests.post(url, data=data, timeout=timeout).json()
        except (requests.RequestException, ValueError) as e:
            body = {"error": {"message": f"request failed: {e}", "is_transient": True}}
        if "error" not in body:
            return body
        if not is_transient_meta_error(body):
            return body  # a real rejection — retrying will not change it
        if attempt < POST_ATTEMPTS:
            wait = POST_BACKOFF * attempt
            msg = (body.get("error") or {}).get("message", "")
            print(f"    … {what} transient error ({msg[:90]}); "
                  f"retry {attempt}/{POST_ATTEMPTS - 1} in {wait:.0f}s")
            time.sleep(wait)
    return body


def wait_for_container_ready(container_id: str, timeout_s: int = 180, poll_s: int = 5) -> dict:
    """Poll a media container until Meta finishes processing the image.

    IG ingests the image asynchronously; publishing before status_code is
    FINISHED fails with error 9007 / subcode 2207027 ("media is not ready").
    """
    deadline = time.monotonic() + timeout_s
    while True:
        status = requests.get(
            f"{BASE_URL}/{container_id}",
            params={"fields": "status_code", "access_token": PAGE_ACCESS_TOKEN},
            timeout=60,
        ).json()
        code = status.get("status_code")
        if code == "FINISHED":
            return {"ok": True}
        if code == "ERROR" or "error" in status:
            return {"ok": False, "error": f"container processing failed: {status}"}
        if time.monotonic() >= deadline:
            return {"ok": False, "error": f"container not ready after {timeout_s}s (last status: {status})"}
        time.sleep(poll_s)


def facebook_permalink(response: dict) -> str | None:
    """Build the Page-post URL from a /photos response.

    The endpoint returns two ids: `id` is the photo, and `post_id` is the Page
    post ("<page>_<post>") — the only one that forms a URL a person can open.
    We used to keep the photo id and drop post_id, so every posted entry
    recorded an id nobody could turn back into a link.
    """
    post_id = response.get("post_id") or ""
    if "_" in post_id:
        page, _, pid = post_id.partition("_")
        if page and pid:
            return f"https://www.facebook.com/{page}/posts/{pid}"
    return None


def instagram_permalink(media_id: str) -> str | None:
    """Ask Graph for the media's public URL.

    Best-effort by design: the post is already live by the time this runs, so a
    failure here costs a link, never the post.
    """
    try:
        data = requests.get(
            f"{BASE_URL}/{media_id}",
            params={"fields": "permalink", "access_token": PAGE_ACCESS_TOKEN},
            timeout=30,
        ).json()
        return data.get("permalink") or None
    except Exception as e:  # network, JSON, anything — never re-raise
        print(f"    ⚠️  permalink lookup failed for media {media_id}: {e}")
        return None


def _publish_instagram(fields: dict, what: str, ready_timeout_s: int = 180) -> dict:
    """Create a media container, wait for Meta to ingest it, then publish.

    Photos and Reels differ only in the container fields and in how long Meta
    takes to process them, so they share everything below. A Reel is a video
    being transcoded, which is minutes of work rather than seconds — hence the
    caller-supplied timeout.
    """
    container = graph_post(
        f"{BASE_URL}/{IG_USER_ID}/media",
        {**fields, "access_token": PAGE_ACCESS_TOKEN},
        what=what, timeout=60,
    )
    if "id" not in container:
        return {"ok": False, "error": f"container creation failed: {container}",
                "transient": is_transient_meta_error(container)}

    ready = wait_for_container_ready(container["id"], timeout_s=ready_timeout_s)
    if not ready["ok"]:
        return ready

    # Belt-and-suspenders: retry publish a few times in case Meta still
    # reports the media as not ready right after FINISHED.
    publish = {}
    for attempt in range(3):
        if attempt:
            time.sleep(10)
        publish = requests.post(
            f"{BASE_URL}/{IG_USER_ID}/media_publish",
            data={"creation_id": container["id"], "access_token": PAGE_ACCESS_TOKEN},
            timeout=60,
        ).json()
        if "id" in publish:
            return {"ok": True, "id": publish["id"], "container_id": container["id"],
                    "permalink": instagram_permalink(publish["id"])}
        if publish.get("error", {}).get("code") != 9007:
            break
    return {"ok": False, "error": f"publish failed: {publish}"}


def post_to_instagram(image_url: str, caption: str) -> dict:
    """Post a photo. Returns {'ok': True, 'id': ...} or {'ok': False, 'error': ...}."""
    return _publish_instagram(
        {"image_url": image_url, "caption": caption},
        what="IG container creation",
    )


def post_reel_to_instagram(video_url: str, caption: str) -> dict:
    """Post a Reel from a public video URL.

    Worth the extra code: in our own 2026 numbers a Reel reaches a median 505
    people against 175 for a flyer — the same reach as three photos, as one
    post. Reel production had fallen to zero by August, and this pipeline
    being photo-only was part of why.

    Note for whoever wires captions to audio: Meta's publishing API has no
    parameter for Instagram's licensed music library — that exists only in the
    app. Any soundtrack has to be baked into the file before it gets here, and
    baked-in commercial music on a business account is what Rights Manager
    mutes. Original or licensed audio only.
    """
    return _publish_instagram(
        {"media_type": "REELS", "video_url": video_url, "caption": caption},
        what="IG Reel container creation",
        ready_timeout_s=600,  # transcoding, not a thumbnail fetch
    )


IG_CAROUSEL_MAX = 10  # Meta's publishing API limit; the app allows more


def post_carousel_to_instagram(image_urls: list, caption: str) -> dict:
    """Post a multi-image carousel.

    Three calls rather than one: every image becomes its own child container
    (`is_carousel_item`, and deliberately no caption — the caption belongs to
    the parent), then a CAROUSEL parent referencing them, then the publish.

    This is what makes the Monday "this week" post possible, and it is why the
    every-week nights can drop to zero posts of their own: one carousel covers
    the whole week. Carousels also earn their place on the numbers — they take
    roughly nine times the saves of a single image, and a saved post keeps
    working all week, which is exactly what a what's-on post is for.
    """
    if not image_urls:
        return {"ok": False, "error": "carousel needs at least one image"}
    if len(image_urls) > IG_CAROUSEL_MAX:
        return {"ok": False,
                "error": f"carousel has {len(image_urls)} images, Meta allows "
                         f"{IG_CAROUSEL_MAX} — trim it before queueing"}
    if len(image_urls) == 1:
        # One slide is not a carousel; Meta rejects the parent. Post it as the
        # plain photo it actually is rather than failing the whole entry.
        return post_to_instagram(image_urls[0], caption)

    children = []
    for i, url in enumerate(image_urls, 1):
        child = graph_post(
            f"{BASE_URL}/{IG_USER_ID}/media",
            {"image_url": url, "is_carousel_item": "true",
             "access_token": PAGE_ACCESS_TOKEN},
            what=f"IG carousel child {i}/{len(image_urls)}", timeout=60,
        )
        if "id" not in child:
            return {"ok": False,
                    "error": f"carousel child {i} failed: {child}",
                    "transient": is_transient_meta_error(child)}
        children.append(child["id"])

    return _publish_instagram(
        {"media_type": "CAROUSEL", "children": ",".join(children), "caption": caption},
        what="IG carousel container creation",
        ready_timeout_s=300,  # a parent waits on every child being ingested
    )


def post_carousel_to_facebook(image_urls: list, caption: str) -> dict:
    """Post a multi-photo Page post.

    Facebook builds these the other way round from Instagram: each photo is
    uploaded to /photos UNPUBLISHED to get an id, then one /feed post attaches
    them. Uploading published photos instead would spray the Page with
    individual photo posts, which is the opposite of the point.
    """
    if not image_urls:
        return {"ok": False, "error": "carousel needs at least one image"}
    if len(image_urls) == 1:
        return post_to_facebook(image_urls[0], caption)

    media_ids = []
    for i, url in enumerate(image_urls, 1):
        photo = graph_post(
            f"{BASE_URL}/{FB_PAGE_ID}/photos",
            {"url": url, "published": "false", "access_token": PAGE_ACCESS_TOKEN},
            what=f"FB unpublished photo {i}/{len(image_urls)}",
        )
        if "id" not in photo:
            return {"ok": False,
                    "error": f"FB photo {i} upload failed: {photo}",
                    "transient": is_transient_meta_error(photo)}
        media_ids.append(photo["id"])

    response = graph_post(
        f"{BASE_URL}/{FB_PAGE_ID}/feed",
        {
            "message": caption,
            "attached_media": json.dumps([{"media_fbid": m} for m in media_ids]),
            "access_token": PAGE_ACCESS_TOKEN,
        },
        what="FB multi-photo post", timeout=60,
    )
    if "id" in response:
        return {"ok": True, "id": response["id"],
                "permalink": facebook_permalink(response)}
    return {"ok": False, "error": f"FB multi-photo post failed: {response}",
            "transient": is_transient_meta_error(response)}


def post_video_to_facebook(video_url: str, caption: str) -> dict:
    """Post a video to the Page from a public URL.

    Different edge from photos (/videos, and `file_url` rather than `url`), and
    it answers with the video id alone — there is no post_id to build a
    permalink from, so posted video entries keep their id but no link.
    """
    response = graph_post(
        f"{BASE_URL}/{FB_PAGE_ID}/videos",
        {
            "file_url": video_url,
            "description": caption,
            "access_token": PAGE_ACCESS_TOKEN,
        },
        what="FB video post", timeout=120,
    )
    if "id" in response:
        return {"ok": True, "id": response["id"],
                "permalink": facebook_permalink(response)}
    return {"ok": False, "error": f"FB video post failed: {response}",
            "transient": is_transient_meta_error(response)}


def post_to_facebook(image_url: str, caption: str) -> dict:
    """Post a photo to the FB Page via Graph API using a remote image URL.

    Returns {'ok': True, 'id': ...} or {'ok': False, 'error': ...}.
    """
    response = graph_post(
        f"{BASE_URL}/{FB_PAGE_ID}/photos",
        {
            "url": image_url,
            "message": caption,
            "access_token": PAGE_ACCESS_TOKEN,
        },
        what="FB photo post",
    )
    if "id" in response:
        return {"ok": True, "id": response["id"], "post_id": response.get("post_id"),
                "permalink": facebook_permalink(response)}
    return {"ok": False, "error": f"FB post failed: {response}",
            "transient": is_transient_meta_error(response)}


def main():
    missing = [k for k, v in {
        "FB_PAGE_ACCESS_TOKEN": PAGE_ACCESS_TOKEN,
        "IG_USER_ID": IG_USER_ID,
        "FB_PAGE_ID": FB_PAGE_ID,
    }.items() if not v]
    if missing:
        # IG_USER_ID and FB_PAGE_ID are only required for their respective platforms,
        # but we error early if FB_PAGE_ACCESS_TOKEN is missing (used by both).
        if "FB_PAGE_ACCESS_TOKEN" in missing:
            print(f"❌ Missing required env var(s): {', '.join(missing)}")
            sys.exit(1)
        print(f"⚠️  Missing env var(s): {', '.join(missing)} — will skip posts that need them.")

    queue = load_queue()
    posts = queue.get("posts", [])
    now_utc = datetime.now(timezone.utc)
    print(f"⏰ Now (UTC): {now_utc.isoformat()}")

    due = [
        p for p in posts
        if p["status"] == "pending" and from_utc_iso(p["scheduled_for_utc"]) <= now_utc
    ]

    if not due:
        print(f"ℹ️  No posts due. Queue has {len(posts)} entry(ies).")
        return

    print(f"📋 {len(due)} post(s) due — processing...\n")
    any_changes = False

    for entry in due:
        print(f"--- Processing {entry['id']} ---")
        print(f"    Scheduled: {entry['scheduled_for_utc']}")
        print(f"    Platform:  {entry['platform']}")

        platform = entry["platform"]
        # A `video_url` on the entry is what makes it a Reel / Page video.
        # Absent, it is a photo exactly as before — every existing queue entry
        # keeps working untouched.
        video_url = entry.get("video_url")
        # `image_urls` (plural) makes it a carousel; `image_url` stays the
        # single-photo field every existing entry uses.
        image_urls = entry.get("image_urls") or []
        # `format: "story"` routes to the Stories endpoints; no caption is sent.
        is_story = entry.get("format") == "story"
        if is_story:
            print(f"    Media:     story")
        elif video_url:
            print(f"    Media:     video ({video_url})")
        elif image_urls:
            print(f"    Media:     carousel, {len(image_urls)} slides")

        if platform == "instagram":
            if not IG_USER_ID:
                print(f"    ⚠️  IG_USER_ID not set — skipping")
                continue
            if is_story:
                result = post_story_to_instagram(entry.get("image_url"), video_url)
                result_label = "Instagram story id"
            elif video_url:
                result = post_reel_to_instagram(video_url, entry["caption"])
                result_label = "Instagram Reel id"
            elif image_urls:
                result = post_carousel_to_instagram(image_urls, entry["caption"])
                result_label = "Instagram media id"
            else:
                result = post_to_instagram(entry["image_url"], entry["caption"])
                result_label = "Instagram media id"
        elif platform == "facebook":
            if not FB_PAGE_ID:
                print(f"    ⚠️  FB_PAGE_ID not set — skipping")
                continue
            if is_story:
                result = post_story_to_facebook(entry["image_url"])
                result_label = "Facebook story id"
            elif video_url:
                result = post_video_to_facebook(video_url, entry["caption"])
                result_label = "Facebook video id"
            elif image_urls:
                result = post_carousel_to_facebook(image_urls, entry["caption"])
                result_label = "Facebook post id"
            else:
                result = post_to_facebook(entry["image_url"], entry["caption"])
                result_label = "Facebook post id"
        else:
            print(f"    ⚠️  Unsupported platform '{platform}' — skipping")
            continue

        if result["ok"]:
            entry["posted_at"] = datetime.now(timezone.utc).isoformat()
            entry["status"] = "posted"
            entry["result"] = f"{result_label}: {result['id']}"
            entry.pop("transient_attempts", None)
            if result.get("permalink"):
                entry["permalink"] = result["permalink"]
            print(f"    ✅ Posted! {result_label}: {result['id']}")
            if result.get("permalink"):
                print(f"       {result['permalink']}")
        elif result.get("transient"):
            # In-process retries are already spent. Leave it pending so the next
            # scheduler run tries again — that is what turns a Meta outage into a
            # late post rather than a lost one. Bounded, so a genuinely dead
            # token stops being retried instead of spinning forever.
            tries = entry.get("transient_attempts", 0) + 1
            entry["result"] = result["error"]
            if tries < MAX_TRANSIENT_CYCLES:
                entry["transient_attempts"] = tries
                entry["status"] = "pending"
                print(f"    ↻ Transient ({tries}/{MAX_TRANSIENT_CYCLES}) — staying pending, "
                      f"will retry next run: {result['error'][:120]}")
            else:
                entry.pop("transient_attempts", None)
                entry["posted_at"] = datetime.now(timezone.utc).isoformat()
                entry["status"] = "failed"
                print(f"    ❌ Failed after {tries} transient attempts: {result['error']}")
        else:
            entry["posted_at"] = datetime.now(timezone.utc).isoformat()
            entry["status"] = "failed"
            entry["result"] = result["error"]
            print(f"    ❌ Failed: {result['error']}")
        any_changes = True

    if any_changes:
        save_queue(queue)
        print(f"\n💾 Queue updated.")


def post_story_to_instagram(image_url: str = None, video_url: str = None) -> dict:
    """Post a Story. Stories carry no caption — the artwork is the message.

    Every-week nights get no feed posts of their own (the Monday round-up
    covers them), so a same-day story is how they show up on the night they
    happen. Stories also don't count against the feed's daily cap: they live
    in a different tray and don't bury the feed posts we paid attention for.
    """
    fields = {"media_type": "STORIES"}
    if video_url:
        fields["video_url"] = video_url
    else:
        fields["image_url"] = image_url
    return _publish_instagram(fields, what="IG story container creation",
                              ready_timeout_s=600 if video_url else 180)


def post_story_to_facebook(image_url: str) -> dict:
    """Post a photo Story to the Page.

    Same two-step shape as the multi-photo post: upload the photo UNPUBLISHED
    to get an id (a published upload would also land in the feed), then hand
    that id to /photo_stories.
    """
    photo = graph_post(
        f"{BASE_URL}/{FB_PAGE_ID}/photos",
        {"url": image_url, "published": "false", "access_token": PAGE_ACCESS_TOKEN},
        what="FB story photo upload",
    )
    if "id" not in photo:
        return {"ok": False, "error": f"FB story photo upload failed: {photo}",
                "transient": is_transient_meta_error(photo)}
    response = graph_post(
        f"{BASE_URL}/{FB_PAGE_ID}/photo_stories",
        {"photo_id": photo["id"], "access_token": PAGE_ACCESS_TOKEN},
        what="FB photo story", timeout=60,
    )
    if response.get("success") or response.get("post_id") or response.get("id"):
        return {"ok": True, "id": response.get("post_id") or response.get("id") or photo["id"]}
    return {"ok": False, "error": f"FB photo story failed: {response}",
            "transient": is_transient_meta_error(response)}


def selftest() -> int:
    """Offline check of the Facebook URL builder. No network, no credentials."""
    transient_cases = [
        # The exact payload that lost four posts on 2026-09-08.
        ({"error": {"message": "This Page access token belongs to a Page that is "
                               "not accessible.", "type": "OAuthException", "code": 190}},
         True, "code 190 page-not-accessible (the 2026-09-08 failure)"),
        ({"error": {"code": 1, "message": "Please reduce the amount of data"}},
         True, "code 1 reduce-data"),
        ({"error": {"code": 324, "is_transient": True, "message": "Missing image"}},
         True, "code 324 flagged is_transient"),
        ({"error": {"code": 99999, "is_transient": True}}, True,
         "unknown code but Meta says transient"),
        ({"error": {"message": "request failed: timeout", "is_transient": True}},
         True, "network failure we synthesise"),
        # Permanent — retrying these just delays a failure we cannot fix.
        ({"error": {"code": 100, "message": "Invalid parameter"}}, False,
         "code 100 invalid parameter"),
        ({"error": {"code": 200, "message": "Permissions error"}}, False,
         "code 200 permissions"),
        ({"error": {"code": 190, "is_transient": False}}, True,
         "code 190 stays retryable even when Meta says not transient"),
        ({"id": "123"}, False, "success body has no error"),
        ({}, False, "empty body"),
        (None, False, "None body"),
    ]
    tfail = 0
    for body, expected, label in transient_cases:
        got = is_transient_meta_error(body)
        if got != expected:
            tfail += 1
        print(f"  {'ok  ' if got == expected else 'FAIL'} {label}: transient={got}")
    print()

    cases = [
        ({"id": "123", "post_id": "555_999"},
         "https://www.facebook.com/555/posts/999", "normal photo post"),
        ({"id": "123"}, None, "no post_id (older API shape) -> no link, not a broken one"),
        ({"id": "123", "post_id": ""}, None, "empty post_id"),
        ({"id": "123", "post_id": "no-underscore"}, None, "malformed post_id"),
        ({"id": "123", "post_id": "_999"}, None, "missing page half"),
        ({"id": "123", "post_id": "555_"}, None, "missing post half"),
    ]
    failures = 0
    for response, expected, label in cases:
        got = facebook_permalink(response)
        if got != expected:
            failures += 1
        print(f"  {'ok  ' if got == expected else 'FAIL'} {label}: {got!r}")
    failures += tfail
    if failures:
        print(f"{failures} case(s) failed.")
        return 1
    print(f"All {len(cases) + len(transient_cases)} cases passed.")
    return 0


if __name__ == "__main__":
    # --selftest runs before main() so it never needs posting credentials.
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
