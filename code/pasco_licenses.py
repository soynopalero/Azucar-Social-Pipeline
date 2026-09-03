"""
Pasco business-license snapshot — docs/pasco_licenses.csv + docs/pasco_licenses_changes.json.

STATUS: NO WORKING SOURCE YET. The scheduled run is disabled and this script
will not produce a snapshot until DATASET_ID below points at real license
records. The fetching, diffing and schema-resolution machinery is finished and
tested; only the source is missing. Do not re-enable the schedule until a run
succeeds by hand.

Pasco is a Business Licensing Service partner city, so the WA Department of
Revenue — not the city — issues the general Pasco business license as a "city
endorsement". Every licensed business in town is therefore on a DOR roll. The
open question is whether that roll is published as data anywhere.

Ruled out so far, each confirmed against the live portal:

  4wur-kfnr  "Business Lookup"  — NOT a dataset. Reports assetType, displayType
      and viewType all 'href' with zero columns; the SODA query refuses it with
      "no row or column access to non-tabular tables" and the bulk export with
      "Non-tabular datasets do not support rows requests." It is a catalog link
      pointing at DOR's own lookup web application. Its name and description are
      the closest match on the portal for what we want, which is exactly why it
      is worth naming here — it is a trap, not a candidate.

  hw7n-fcif  "BLS License list (merged)"  — a real tabular dataset, but of the
      wrong thing entirely. Its columns are agency, program, what_is_the_license_
      name_category, what_are_the_fees_associated_with_this_license, what_rcws_
      and_wacs_govern_this_license and so on: it is a reference catalogue of
      license TYPES the state issues, not a list of businesses holding them.
      There is no business name, no UBI and no address anywhere in it.

Taken together these point one way: DOR appears to publish Business Lookup
deliberately as a searchable application rather than as bulk data, so the full
roll may not be on data.wa.gov at all. If that holds, the realistic routes are a
public records request to DOR or to the City of Pasco, and the narrower
datasets that do exist as data (LCB liquor and cannabis licensees, L&I
contractors, DOL transportation licenses) for the slices they cover.

NOT covered by DOR in any case — these stay with the city and need a public
records request to businesslicense@pasco-wa.gov: solicitor licenses, residential
rental licenses, and taxi / for-hire driver licenses.

Env: SOCRATA_APP_TOKEN  (optional; raises the rate limit, and the dataset is
                         public so a rejected token only prints a warning)
     PASCO_CITY_FIELD   (optional override if the city column is named oddly)
Run:  python code/pasco_licenses.py      then commit docs/ and push.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
SNAPSHOT_CSV = DOCS / "pasco_licenses.csv"
CHANGES_JSON = DOCS / "pasco_licenses_changes.json"

# PLACEHOLDER — this ID does not hold license records. See the module docstring
# for what it and 4wur-kfnr actually are and why both were ruled out. It is left
# here so the script still resolves and reports honestly rather than pointing at
# nothing; the run fails at schema resolution, printing the columns it did find.
# Replace it once a real source is settled, and re-enable the workflow schedule
# only after a manual run succeeds.
DATASET_ID = "hw7n-fcif"
METADATA_URL = f"https://data.wa.gov/api/views/{DATASET_ID}.json"
RESOURCE_URL = f"https://data.wa.gov/resource/{DATASET_ID}.json"

CITY = "PASCO"
PAGE_SIZE = 5000
SAMPLE_ROWS = 25  # rows read to recover column names if metadata is unreadable
MAX_ROWS = 200_000  # runaway guard; Pasco is nowhere near this

APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN", "").strip()
CITY_FIELD_OVERRIDE = os.environ.get("PASCO_CITY_FIELD", "").strip()

# Network resilience, same shape as the Monday sync: data.wa.gov rate-limits
# token-less callers with a 429 and occasionally 503s mid-page, and a single
# transient failure should not throw away a run that is 40k rows deep.
MAX_ATTEMPTS = 5
BASE_BACKOFF = 2.0  # waits ~2s, 4s, 8s, 16s between attempts
RETRY_HTTP_CODES = {429, 500, 502, 503, 504}

# A license is "open" unless DOR says otherwise. Matching on the open side
# rather than enumerating every closure reason means a status string we have
# never seen before reads as open, not as a phantom closure in the diff.
OPEN_STATUSES = {"active", "open", "current", "valid"}

# How we recognise each column we care about, most specific pattern first. DOR
# has renamed these before, so nothing is hardcoded — see resolve_field().
FIELD_CANDIDATES: dict[str, list[str]] = {
    # Physical location, never the mailing address: a Kennewick business with a
    # Pasco PO box is not a Pasco business, and vice versa.
    "city": ["location_city", "physical_city", "business_city", "city"],
    "ubi": ["ubi"],
    "name": ["business_name", "legal_name", "firm_name", "entity_name", "name"],
    "trade_name": ["trade_name", "dba", "doing_business_as"],
    "status": ["business_status", "account_status", "license_status", "status"],
    "address": ["location_address", "physical_address", "street_address", "address"],
    "zip": ["location_zip", "physical_zip", "zip_code", "zip"],
    "opened": ["open_date", "first_issue_date", "effective_date", "license_issue_date"],
    "closed": ["close_date", "closed_date", "expiration_date"],
}
REQUIRED_FIELDS = ("city", "ubi", "name")


class SocrataError(RuntimeError):
    """An HTTP error from data.wa.gov, carrying the status code and response body.

    Socrata explains itself in the body ("Invalid app token", "Unknown sort key"),
    and urllib throws that body away unless you read it — which is how a 403 here
    first showed up as a bare "Forbidden" with nothing to act on.
    """

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


# Cleared for the rest of the run if data.wa.gov rejects the token — see fetch_json.
_use_token = bool(APP_TOKEN)


def _error_body(exc: urllib.error.HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", "replace").strip()[:400]
    except OSError:
        return ""


def _request(url: str, params: dict | None, use_token: bool) -> object:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    headers = {"Accept": "application/json", "User-Agent": "azucar-social-pipeline/1.0"}
    if use_token and APP_TOKEN:
        headers["X-App-Token"] = APP_TOKEN
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_json(url: str, params: dict | None = None) -> object:
    """GET JSON with backoff on the throttling/5xx codes Socrata actually returns."""
    global _use_token

    last: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        if attempt:
            time.sleep(BASE_BACKOFF * (2 ** (attempt - 1)))
        try:
            return _request(url, params, _use_token)
        except urllib.error.HTTPError as exc:
            body = _error_body(exc)
            # A 403 while we are sending a token nearly always means the token is
            # the problem (wrong value in the secret, revoked upstream), not the
            # data. Prove it by retrying once without: if that works, the licenses
            # are reachable and only the credential is bad, so finish the run
            # token-less and say so loudly rather than failing on a credential
            # this public dataset does not actually require.
            if exc.code == 403 and _use_token:
                try:
                    result = _request(url, params, use_token=False)
                except urllib.error.HTTPError:
                    pass  # Forbidden with or without it — the token is not the cause.
                else:
                    print("WARNING: SOCRATA_APP_TOKEN was rejected (403). Continuing "
                          "without it — slower, and liable to throttling on big pulls. "
                          "Re-check the secret against the app token on data.wa.gov. "
                          f"Server said: {body or '(no detail)'}", file=sys.stderr)
                    _use_token = False
                    return result
            if exc.code not in RETRY_HTTP_CODES:
                raise SocrataError(
                    exc.code, f"HTTP {exc.code} from {url}: {body or exc.reason}") from exc
            last = exc
            print(f"  HTTP {exc.code} from data.wa.gov, retrying…", file=sys.stderr)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last = exc
            print(f"  {type(exc).__name__} from data.wa.gov, retrying…", file=sys.stderr)
    raise RuntimeError(f"data.wa.gov unreachable after {MAX_ATTEMPTS} attempts: {last}")


def dataset_columns() -> list[str]:
    """The dataset's column names, preferring its metadata endpoint.

    /api/views/ is the authoritative list, but it is a separate endpoint with its
    own permissions and it has 403'd while the rows themselves stayed readable —
    so fall back to sampling rows and unioning their keys. That is the fallback
    rather than the default because a sample cannot see a column that happens to
    be null in every row it draws.
    """
    try:
        meta = fetch_json(METADATA_URL)
        cols = [c["fieldName"] for c in meta.get("columns", []) if c.get("fieldName")]
        if cols:
            return cols
        print("Dataset metadata listed no columns — sampling rows instead.", file=sys.stderr)
    except RuntimeError as exc:  # SocrataError included
        print(f"Could not read dataset metadata ({exc}) — sampling rows instead.",
              file=sys.stderr)

    sample = fetch_json(RESOURCE_URL, {"$limit": SAMPLE_ROWS})
    cols = sorted({key for row in sample for key in row})
    if not cols:
        raise RuntimeError(f"Dataset {DATASET_ID} returned no metadata and no rows — "
                           "check that it still exists at that ID.")
    return cols


def resolve_field(role: str, columns: list[str]) -> str | None:
    """Map a role ('city', 'status', …) onto whatever DOR calls that column today.

    Exact matches win, then suffix matches ('dor_location_city' for 'location_city'),
    then any column containing the candidate. Mailing-address columns are excluded
    outright so a fuzzy match can never silently swap physical for mailing.
    """
    usable = [c for c in columns if "mail" not in c.lower()]
    for candidate in FIELD_CANDIDATES[role]:
        for match in (
            lambda c: c == candidate,
            lambda c: c.endswith("_" + candidate),
            lambda c: candidate in c,
        ):
            hits = [c for c in usable if match(c.lower())]
            if hits:
                return sorted(hits, key=len)[0]
    return None


def resolve_schema() -> dict[str, str]:
    columns = dataset_columns()
    fields = {role: resolve_field(role, columns) for role in FIELD_CANDIDATES}
    if CITY_FIELD_OVERRIDE:
        fields["city"] = CITY_FIELD_OVERRIDE

    missing = [r for r in REQUIRED_FIELDS if not fields.get(r)]
    if missing:
        raise RuntimeError(
            f"Could not find {missing} in dataset {DATASET_ID}. DOR renamed something.\n"
            f"Columns now available: {', '.join(sorted(columns))}\n"
            "Add the real name to FIELD_CANDIDATES (or set PASCO_CITY_FIELD)."
        )
    resolved = {role: col for role, col in fields.items() if col}
    print(f"Dataset columns ({len(columns)}): " + ", ".join(sorted(columns)))
    print("Resolved columns: " + ", ".join(f"{r}={c}" for r, c in sorted(resolved.items())))
    unresolved = [r for r in FIELD_CANDIDATES if r not in resolved]
    if unresolved:
        print(f"Unresolved (optional) roles: {', '.join(unresolved)}", file=sys.stderr)
    return resolved


def fetch_pasco_rows(city_field: str) -> list[dict]:
    """Page through every Pasco row. Ordered by :id so paging can't drift."""
    where = f"upper({city_field})='{CITY}'"
    rows: list[dict] = []
    order: str | None = ":id"

    while len(rows) < MAX_ROWS:
        params = {"$where": where, "$limit": PAGE_SIZE, "$offset": len(rows)}
        if order:
            params["$order"] = order
        try:
            page = fetch_json(RESOURCE_URL, params)
        except SocrataError as exc:
            # Some Socrata dataset types reject `:id` as a sort key. Drop it once
            # and carry on — rows may repeat across pages, which dedupe handles.
            if exc.code == 400 and order and not rows:
                print("  :id ordering rejected, paging unordered", file=sys.stderr)
                order = None
                continue
            raise
        if not page:
            break
        # Socrata hands back dicts for location/point columns. Flatten to text up
        # front so every downstream .strip() and the CSV writer see plain strings.
        rows.extend({k: v if isinstance(v, str) else json.dumps(v, sort_keys=True)
                     for k, v in row.items()} for row in page)
        print(f"  fetched {len(rows)} rows…")
        if len(page) < PAGE_SIZE:
            break

    return rows


def row_key(row: dict, fields: dict[str, str]) -> str:
    """Stable identity for a license across runs: UBI plus trade name.

    UBI alone is not unique — one UBI covers every location of a chain, and each
    has its own license row, so keying on UBI alone would collapse them.
    """
    ubi = (row.get(fields["ubi"]) or "").strip()
    trade = (row.get(fields.get("trade_name", "")) or "").strip().upper()
    addr = (row.get(fields.get("address", "")) or "").strip().upper()
    return "|".join((ubi, trade, addr))


def is_open(row: dict, fields: dict[str, str]) -> bool:
    status_field = fields.get("status")
    if not status_field:
        return True
    return (row.get(status_field) or "").strip().lower() in OPEN_STATUSES


def summarise(row: dict, fields: dict[str, str]) -> dict:
    """The handful of columns a human actually reads in the changes file."""
    out = {}
    for role in ("name", "trade_name", "address", "status", "opened", "closed", "ubi"):
        col = fields.get(role)
        if col and (row.get(col) or "").strip():
            out[role] = row[col].strip()
    return out


def load_previous() -> tuple[list[dict], list[str]]:
    if not SNAPSHOT_CSV.exists():
        return [], []
    with SNAPSHOT_CSV.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames or [])


def write_snapshot(rows: list[dict], columns: list[str]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    with SNAPSHOT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    if not APP_TOKEN:
        print("No SOCRATA_APP_TOKEN set — running unauthenticated (throttled).",
              file=sys.stderr)

    fields = resolve_schema()
    print(f"Fetching {CITY} rows from data.wa.gov/{DATASET_ID}…")
    rows = fetch_pasco_rows(fields["city"])
    if not rows:
        # An empty result is never legitimate for a city this size — it means a
        # renamed column or a silently broken filter, and writing it out would
        # report every business in Pasco as closed. Bail instead.
        raise RuntimeError(f"Zero rows for {CITY}. Filter or schema is wrong — not overwriting.")

    # Dedupe (unordered paging can repeat) and sort so the committed CSV diffs
    # cleanly month to month instead of reshuffling.
    by_key = {row_key(r, fields): r for r in rows}
    current = sorted(by_key.values(), key=lambda r: row_key(r, fields))
    print(f"{len(current)} unique {CITY} license rows.")

    previous, prev_columns = load_previous()
    prev_by_key = {row_key(r, fields): r for r in previous} if prev_columns else {}

    # Union of both schemas: if DOR adds a column mid-year we keep the old ones
    # so historical rows do not lose data on the next write.
    columns = list(dict.fromkeys(
        [c for c in prev_columns if c] + sorted({k for r in current for k in r})
    ))
    write_snapshot(current, columns)

    opened, closed, vanished = [], [], []
    if prev_by_key:
        for key, row in by_key.items():
            was = prev_by_key.get(key)
            if was is None:
                opened.append(summarise(row, fields))
            elif is_open(was, fields) and not is_open(row, fields):
                closed.append(summarise(row, fields))
        for key, row in prev_by_key.items():
            if key not in by_key:
                # Dropped out of DOR's five-year window rather than closing today.
                vanished.append(summarise(row, fields))

    entry = {
        "run_date": dt.date.today().isoformat(),
        "total_rows": len(current),
        "open_rows": sum(1 for r in current if is_open(r, fields)),
        "first_run": not prev_by_key,
        "counts": {"new": len(opened), "closed": len(closed), "aged_out": len(vanished)},
        "new": opened,
        "closed": closed,
        "aged_out": vanished,
    }

    history = []
    if CHANGES_JSON.exists():
        try:
            history = json.loads(CHANGES_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("Changes file was corrupt — starting a fresh history.", file=sys.stderr)
    # Re-running on the same day replaces that day's entry instead of stacking.
    history = [h for h in history if h.get("run_date") != entry["run_date"]]
    history.insert(0, entry)
    CHANGES_JSON.write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")

    if entry["first_run"]:
        print("First run — baseline written, no diff to report.")
    else:
        print(f"New: {len(opened)} • Closed: {len(closed)} • Aged out: {len(vanished)}")
    print(f"Wrote {SNAPSHOT_CSV.relative_to(REPO_ROOT)} and "
          f"{CHANGES_JSON.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
