"""
insights_api.py
---------------
A small, defensive Meta Graph API client for READING insights.

Why this exists as its own module: the posting scripts (facebook_post.py,
instagram_post.py) only ever write. Reading insights has a completely
different failure mode — Meta renames and retires metrics on almost every
API version bump (`impressions` became `views` for Instagram media, the
`period` argument moved for several account metrics, `plays` was folded into
`views` for Reels). A metric that worked last quarter returns
`(#100) metric[0] must be one of the following values: ...` today, and a
naive request for ten metrics fails as a unit even when nine are fine.

So the rule here is: never let one dead metric cost us the other nine.
`insights()` asks for everything at once, and only if that fails does it fall
back to probing metrics one at a time, keeping whatever answers. The working
set is cached to disk so the slow path runs roughly once per API change
rather than once per post.

Read-only. Nothing in this file publishes, edits or deletes.
"""

import json
import os
import time
import urllib.parse
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "insights"
SUPPORT_CACHE = DATA_DIR / "_metric_support.json"

# Pinned deliberately. Meta retires a version roughly every two years; bumping
# this is a conscious act with a probe run behind it, not something to drift.
API_VERSION = os.getenv("GRAPH_API_VERSION", "v21.0")
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

TIMEOUT = 30
MAX_RETRIES = 4


class GraphError(RuntimeError):
    """A Graph API call that failed for a reason worth stopping on."""


def _sleep_backoff(attempt: int):
    time.sleep(min(2 ** attempt, 30))


def graph_get(path: str, token: str, **params) -> dict:
    """GET one Graph endpoint, retrying transient failures.

    Meta signals rate limiting with code 4 / 17 / 32 / 613 and momentary
    server trouble with code 1 or 2. Those are worth waiting out. Anything
    else (a bad metric name, a permission we do not hold) will fail exactly
    the same way on a retry, so it is raised immediately.
    """
    params["access_token"] = token
    url = f"{BASE_URL}/{path.lstrip('/')}"

    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, params=params, timeout=TIMEOUT)
        except requests.RequestException as exc:
            if attempt == MAX_RETRIES - 1:
                raise GraphError(f"network error on {path}: {exc}") from exc
            _sleep_backoff(attempt)
            continue

        if r.status_code == 200:
            return r.json()

        try:
            err = r.json().get("error", {})
        except ValueError:
            err = {"message": r.text[:300]}

        code = err.get("code")
        transient = code in (1, 2, 4, 17, 32, 613) or r.status_code >= 500
        if transient and attempt < MAX_RETRIES - 1:
            _sleep_backoff(attempt)
            continue

        raise GraphError(
            f"{path} failed [{r.status_code}] code={code}: {err.get('message', '?')}"
        )

    raise GraphError(f"{path}: exhausted retries")


def paginate(path: str, token: str, limit_pages: int = 100, **params):
    """Yield every node across a paged edge (media lists, post lists).

    Meta returns `paging.next` as a fully-formed URL with the cursor and the
    token already in it, so after the first call we follow that verbatim
    rather than rebuilding params and risking a drifted cursor.
    """
    params.setdefault("limit", 100)
    page = graph_get(path, token, **params)
    pages = 0

    while True:
        for node in page.get("data", []):
            yield node

        pages += 1
        next_url = page.get("paging", {}).get("next")
        if not next_url or pages >= limit_pages:
            return

        for attempt in range(MAX_RETRIES):
            try:
                r = requests.get(next_url, timeout=TIMEOUT)
                if r.status_code == 200:
                    page = r.json()
                    break
                if r.status_code < 500 and attempt == 0:
                    return  # a dead cursor is not worth retrying
            except requests.RequestException:
                pass
            if attempt == MAX_RETRIES - 1:
                return
            _sleep_backoff(attempt)


def _load_support() -> dict:
    if SUPPORT_CACHE.exists():
        try:
            return json.loads(SUPPORT_CACHE.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return {}
    return {}


def _save_support(support: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SUPPORT_CACHE.write_text(
        json.dumps(support, indent=2, sort_keys=True), encoding="utf-8"
    )


def _flatten(payload: dict) -> dict:
    """Reduce an insights response to {metric_name: number}.

    Meta returns three shapes depending on the metric: a `values` list of
    {value, end_time} for time-series metrics, a `total_value.value` scalar,
    and a `total_value.breakdowns` structure for demographics. The first two
    collapse to a number; breakdowns are kept whole under `<metric>__breakdown`
    because there is no single number to reduce them to.
    """
    out = {}
    for row in payload.get("data", []):
        name = row.get("name")
        if not name:
            continue

        total = row.get("total_value")
        if isinstance(total, dict):
            if "value" in total:
                out[name] = total["value"]
            if "breakdowns" in total:
                out[f"{name}__breakdown"] = total["breakdowns"]
            continue

        values = row.get("values") or []
        if not values:
            continue
        if len(values) == 1:
            out[name] = values[0].get("value")
        else:
            out[name] = {v.get("end_time"): v.get("value") for v in values}
    return out


def insights(obj_id: str, token: str, metrics, support_key: str, **params) -> dict:
    """Fetch insights for one object, degrading past unsupported metrics.

    Fast path: ask for every metric in one call. That is what succeeds on a
    healthy day and it costs a single request.

    Slow path: the batch failed, so we cannot tell which metric Meta objected
    to — the error names only the first one. Probe each metric alone, keep the
    survivors, and cache that set under `support_key` (one key per object
    kind, e.g. "ig_media:REELS") so every later object of the same kind takes
    the fast path again with a list we know is good.

    Returns {metric: value}, plus `_unsupported` listing what this object kind
    no longer answers to — silence about a missing metric would otherwise read
    as a zero, which is the one lie this whole exercise cannot afford.
    """
    support = _load_support()
    known = support.get(support_key)
    ask = [m for m in metrics if m in known] if known else list(metrics)

    if not ask:
        return {"_unsupported": list(metrics)}

    try:
        payload = graph_get(f"{obj_id}/insights", token, metric=",".join(ask), **params)
        result = _flatten(payload)
        if known is None:
            support[support_key] = ask
            _save_support(support)
        result["_unsupported"] = [m for m in metrics if m not in ask]
        return result
    except GraphError as exc:
        if known is not None:
            # A cached-good set just broke: Meta changed under us. Drop the
            # cache for this kind and re-probe rather than reporting zeros.
            support.pop(support_key, None)
            _save_support(support)
        first_failure = str(exc)

    working, result = [], {}
    for metric in metrics:
        try:
            payload = graph_get(f"{obj_id}/insights", token, metric=metric, **params)
        except GraphError:
            continue
        got = _flatten(payload)
        if got:
            working.append(metric)
            result.update(got)

    support[support_key] = working
    _save_support(support)

    result["_unsupported"] = [m for m in metrics if m not in working]
    if not working:
        result["_error"] = first_failure
    return result


def require_env(*names) -> dict:
    """Read required credentials, naming every one that is missing at once."""
    values, missing = {}, []
    for name in names:
        val = os.getenv(name)
        if not val:
            missing.append(name)
        values[name] = val
    if missing:
        raise SystemExit(
            "Missing credentials: "
            + ", ".join(missing)
            + "\nThese live as GitHub Actions secrets; this script is meant to run "
            "in the insights-pull workflow, or locally with code/.env loaded."
        )
    return values
