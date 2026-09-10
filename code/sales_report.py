"""
Post-show sales report — Eventbrite advance tickets + Toast door sales.

Answers the two questions Pedro asks the morning after every show:
  1. How many tickets sold on Eventbrite, and how much money actually lands?
  2. How many tickets/covers rang up on Toast at the door?

Sends Pedro + Jayme a Telegram summary plus the full dated report as a file
attachment, so there's a running record for bookkeeping and for comparing shows
month over month at the admin meeting.

The report is NEVER committed: this repo is public, and per-show revenue is not.
reports/sales/ and reports/toast/ are gitignored; Telegram is the archive.

Usage (from repo root):
  python code/sales_report.py                      # shows that ended in the last 36h
  python code/sales_report.py --date 2026-09-06    # one specific show day
  python code/sales_report.py --days 7             # the last week of shows
  python code/sales_report.py --date 2026-09-06 --dry-run   # print only, no send/write
  python code/sales_report.py --selftest           # offline math check, no API calls

Env:
  EVENTBRITE_TOKEN         required (same secret the create-event bot uses)
  TELEGRAM_BOT_TOKEN       optional — no token, no Telegram, everything else still runs
  TELEGRAM_NOTIFY_CHAT_IDS optional — comma-separated chat ids
  TOAST_CLIENT_ID          optional — Toast Standard/Analytics API credentials
  TOAST_CLIENT_SECRET      optional
  TOAST_RESTAURANT_GUID    optional — the location GUID from Toast Web
  TOAST_TICKET_ITEMS       optional — comma-separated name fragments that count
                           as a ticket/cover (default: cover,ticket,admission,entry,door)

Toast without API access: export the sales CSV from Toast Web and drop it in
reports/toast/ named for the show date (e.g. reports/toast/2026-09-06.csv), or
pass --toast-csv <path>. The parser matches columns by header name, so most of
Toast's item-sales exports work as-is. See docs/sales-report.md.

Money notes (why the numbers are shaped this way):
- Every figure is computed in integer cents from Eventbrite's own per-attendee
  `costs` block. Floats are never used for money.
- Payout is derived as gross - eventbrite_fee - payment_fee - tax. That holds
  whether fees are passed to the buyer or absorbed by us, but it is still an
  ESTIMATE: only Eventbrite's payout report is bank-authoritative, and it can
  differ on refunds mid-cycle, chargebacks and tax remittance.
- Free RSVP tickets (the "$X cover at door" ones this repo creates when tax
  settings block paid ticketing) are counted separately from paid tickets, so
  a $0 payout on a busy night reads as expected rather than as a bug.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo


def load_dotenv() -> None:
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv()

import requests  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = REPO_ROOT / "reports" / "sales"
TOAST_CSV_DIR = REPO_ROOT / "reports" / "toast"

PACIFIC = ZoneInfo("America/Los_Angeles")

EB_BASE = "https://www.eventbriteapi.com/v3"
EB_ORG = "2861869150261"  # same org the create-event bot posts to

DEFAULT_LOOKBACK_HOURS = 36  # "the show that just happened", incl. a late Sunday

RETRY_CODES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 4

TOAST_HOST = os.environ.get("TOAST_API_HOST", "https://ws-api.toasttab.com").rstrip("/")
DEFAULT_TICKET_WORDS = "cover,ticket,admission,entry,door"


# ─── money ───────────────────────────────────────────────────────────────────

def usd(cents: int) -> str:
    """Format integer cents as $1,234.56 (negatives as -$12.00)."""
    sign = "-" if cents < 0 else ""
    return f"{sign}${abs(cents) / 100:,.2f}"


def parse_money(text: str) -> int:
    """Parse '$1,234.56', '(12.00)' or '-12' into integer cents. 0 if unparseable."""
    s = (text or "").strip()
    if not s:
        return 0
    negative = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[^0-9.\-]", "", s)
    if not s or s in {"-", ".", "-."}:
        return 0
    try:
        cents = int(round(float(s) * 100))
    except ValueError:
        return 0
    return -cents if negative else cents


# ─── Eventbrite ──────────────────────────────────────────────────────────────

def eb_token() -> str:
    token = (os.environ.get("EVENTBRITE_TOKEN") or "").strip()
    if not token:
        sys.exit("EVENTBRITE_TOKEN env var is empty — set it in code/.env locally, "
                 "or as a GitHub Actions secret.")
    return token


def eb_get(path: str, params: dict | None = None) -> dict:
    """GET one page of the Eventbrite API, retrying transient failures."""
    url = f"{EB_BASE}{path}"
    headers = {"Authorization": f"Bearer {eb_token()}"}
    last = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            r = requests.get(url, headers=headers, params=params or {}, timeout=45)
        except requests.RequestException as e:
            last = e
        else:
            if r.ok:
                return r.json()
            if r.status_code not in RETRY_CODES:
                raise RuntimeError(f"Eventbrite GET {path} — HTTP {r.status_code}\n{r.text[:400]}")
            last = RuntimeError(f"HTTP {r.status_code}")
        if attempt < MAX_ATTEMPTS:
            wait = 2.0 * (2 ** (attempt - 1))
            print(f"  … Eventbrite {path} failed ({last}); retry {attempt} in {wait:.0f}s",
                  flush=True)
            time.sleep(wait)
    raise RuntimeError(f"Eventbrite GET {path} failed after {MAX_ATTEMPTS} attempts: {last}")


def eb_paginate(path: str, key: str, params: dict | None = None):
    """Yield every object across Eventbrite's continuation-token pagination."""
    params = dict(params or {})
    seen_pages = 0
    while True:
        body = eb_get(path, params)
        yield from body.get(key) or []
        page = body.get("pagination") or {}
        seen_pages += 1
        if not page.get("has_more_items") or not page.get("continuation"):
            return
        if seen_pages > 200:  # a runaway loop would burn the hourly rate limit
            print(f"  ⚠️ {path}: stopped after 200 pages — check the filter.")
            return
        params["continuation"] = page["continuation"]


def eb_events_in_window(start: dt.datetime, end: dt.datetime) -> list[dict]:
    """Org events whose LOCAL start falls in [start, end]. Newest-first scan,
    stopping as soon as we run past the window — the org has hundreds of events
    and there's no server-side 'started between' filter."""
    found = []
    for ev in eb_paginate(f"/organizations/{EB_ORG}/events/", "events",
                          {"order_by": "start_desc",
                           "status": "live,started,ended,completed"}):
        local = (ev.get("start") or {}).get("local")
        if not local:
            continue
        when = dt.datetime.fromisoformat(local).replace(tzinfo=PACIFIC)
        if when > end:
            continue
        if when < start:
            break  # start_desc ordering — everything after this is older still
        found.append(ev)
    return list(reversed(found))  # chronological


@dataclass
class TicketSales:
    """Eventbrite side of one event, all money in integer cents."""
    paid_tickets: int = 0
    free_tickets: int = 0
    checked_in: int = 0
    gross: int = 0
    eventbrite_fee: int = 0
    payment_fee: int = 0
    tax: int = 0
    refunded_tickets: int = 0
    refunded_gross: int = 0
    by_ticket_class: dict[str, int] = field(default_factory=dict)
    discount_codes: dict[str, int] = field(default_factory=dict)

    @property
    def tickets_sold(self) -> int:
        return self.paid_tickets + self.free_tickets

    @property
    def payout(self) -> int:
        """Estimated money that reaches the bank."""
        return self.gross - self.eventbrite_fee - self.payment_fee - self.tax


def _cost(attendee: dict, key: str) -> int:
    """Integer cents out of an Eventbrite costs block, tolerating a missing key."""
    block = (attendee.get("costs") or {}).get(key) or {}
    value = block.get("value")
    return int(value) if isinstance(value, (int, float)) else 0


def eb_event_sales(event_id: str) -> TicketSales:
    """One row per ticket: attendees, not orders — an order can hold several."""
    s = TicketSales()
    for a in eb_paginate(f"/events/{event_id}/attendees/", "attendees"):
        if a.get("cancelled") or a.get("status") == "Deleted":
            continue
        if a.get("refunded"):
            s.refunded_tickets += 1
            s.refunded_gross += _cost(a, "gross")
            continue

        base = _cost(a, "base_price")
        if base > 0:
            s.paid_tickets += 1
        else:
            s.free_tickets += 1
        s.gross += _cost(a, "gross")
        s.eventbrite_fee += _cost(a, "eventbrite_fee")
        s.payment_fee += _cost(a, "payment_fee")
        s.tax += _cost(a, "tax")
        if a.get("checked_in"):
            s.checked_in += 1
        name = (a.get("ticket_class_name") or "General Admission").strip()
        s.by_ticket_class[name] = s.by_ticket_class.get(name, 0) + 1

    s.discount_codes = eb_discount_usage(event_id)
    return s


def eb_discount_usage(event_id: str) -> dict[str, int]:
    """Per-code redemption counts — this is how we tell which queen actually
    brought people (SLAYON / BLUNT / FANTASY). Best-effort: discounts live at
    the ORGANIZATION level and the endpoint needs a token with organizer scope,
    so a failure here degrades to 'no code data' instead of sinking the run."""
    codes: dict[str, int] = {}
    try:
        for d in eb_paginate(f"/organizations/{EB_ORG}/discounts/", "discounts",
                             {"scope": "event", "event_id": event_id}):
            sold = d.get("quantity_sold") or 0
            if sold:
                codes[d.get("code") or "?"] = sold
    except Exception as e:  # noqa: BLE001 — never let reporting break the report
        print(f"  (discount codes unavailable for {event_id}: {e})")
    return codes


# ─── Toast ───────────────────────────────────────────────────────────────────

@dataclass
class ToastSales:
    """Door sales rung up on the POS. Money in integer cents."""
    items: int = 0
    amount: int = 0
    by_item: dict[str, int] = field(default_factory=dict)
    source: str = "none"
    note: str = ""


def ticket_words() -> list[str]:
    raw = os.environ.get("TOAST_TICKET_ITEMS") or DEFAULT_TICKET_WORDS
    return [w.strip().lower() for w in raw.split(",") if w.strip()]


def looks_like_ticket(name: str) -> bool:
    low = (name or "").lower()
    return any(w in low for w in ticket_words())


def toast_configured() -> bool:
    return all(os.environ.get(k, "").strip() for k in
               ("TOAST_CLIENT_ID", "TOAST_CLIENT_SECRET", "TOAST_RESTAURANT_GUID"))


def toast_token() -> str:
    r = requests.post(
        f"{TOAST_HOST}/authentication/v1/authentication/login",
        json={"clientId": os.environ["TOAST_CLIENT_ID"].strip(),
              "clientSecret": os.environ["TOAST_CLIENT_SECRET"].strip(),
              "userAccessType": "TOAST_MACHINE_CLIENT"},
        timeout=45)
    if not r.ok:
        raise RuntimeError(f"Toast login — HTTP {r.status_code}\n{r.text[:300]}")
    token = ((r.json().get("token") or {}).get("accessToken") or "").strip()
    if not token:
        raise RuntimeError(f"Toast login returned no accessToken: {r.text[:300]}")
    return token


def toast_sales_api(day_start: dt.datetime, day_end: dt.datetime) -> ToastSales:
    """Ticket/cover items rung up between two instants, via the Orders API."""
    out = ToastSales(source="api")
    token = toast_token()
    headers = {"Authorization": f"Bearer {token}",
               "Toast-Restaurant-External-ID": os.environ["TOAST_RESTAURANT_GUID"].strip()}
    fmt = "%Y-%m-%dT%H:%M:%S.000%z"
    page = 1
    while True:
        r = requests.get(f"{TOAST_HOST}/orders/v2/ordersBulk", headers=headers, timeout=60,
                         params={"startDate": day_start.strftime(fmt),
                                 "endDate": day_end.strftime(fmt),
                                 "page": page, "pageSize": 100})
        if not r.ok:
            raise RuntimeError(f"Toast ordersBulk — HTTP {r.status_code}\n{r.text[:300]}")
        orders = r.json() or []
        if not orders:
            break
        for order in orders:
            if order.get("voided") or order.get("deleted"):
                continue
            for check in order.get("checks") or []:
                if check.get("voided") or check.get("deleted"):
                    continue
                for sel in check.get("selections") or []:
                    if sel.get("voided") or sel.get("deleted"):
                        continue
                    name = (sel.get("displayName") or "").strip()
                    if not looks_like_ticket(name):
                        continue
                    qty = sel.get("quantity") or 1
                    qty = int(qty) if float(qty).is_integer() else 1
                    price = sel.get("price")
                    cents = int(round(float(price) * 100)) if price is not None else 0
                    out.items += qty
                    out.amount += cents
                    out.by_item[name] = out.by_item.get(name, 0) + qty
        if len(orders) < 100:
            break
        page += 1
        if page > 200:
            out.note = "stopped after 200 pages"
            break
    return out


# Header fragments Toast's various item-sales exports use, in priority order.
CSV_ITEM_KEYS = ("menuitem", "itemname", "item", "name", "product")
CSV_QTY_KEYS = ("itemqty", "itemquantity", "qtysold", "quantity", "qty", "itemcount", "count")
CSV_AMOUNT_KEYS = ("netsales", "netamount", "netamt", "grosssales", "grossamount",
                   "itemtotal", "amount", "total", "sales")


def _norm(s: str) -> str:
    """Normalize a CSV header for matching. '%' becomes 'pct' rather than being
    stripped: dropping it collapsed 'Net Sales %' onto 'Net Sales', and the
    percentage column then got read as money (caught by --selftest)."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower().replace("%", "pct"))


def _pick_column(headers: list[str], keys: tuple[str, ...]) -> str | None:
    """Exact normalized match first, then containment — so 'Net Sales' wins over
    'Net Sales %' and 'Item' never shadows 'Menu Item'. Percentage columns are
    never a candidate; none of item/qty/amount is ever a percentage."""
    norm = {h: _norm(h) for h in headers}
    usable = [h for h in headers if "pct" not in norm[h]]
    for key in keys:
        for h in usable:
            if norm[h] == key:
                return h
    for key in keys:
        for h in usable:
            if key in norm[h]:
                return h
    return None


def toast_sales_csv(path: Path) -> ToastSales:
    """Parse a Toast Web item-sales export, matching columns by header name."""
    out = ToastSales(source=f"csv:{path.name}")
    rows = list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))
    if not rows:
        out.note = "CSV had no rows"
        return out
    headers = [h for h in (rows[0].keys()) if h]
    item_col = _pick_column(headers, CSV_ITEM_KEYS)
    qty_col = _pick_column(headers, CSV_QTY_KEYS)
    amt_col = _pick_column(headers, CSV_AMOUNT_KEYS)
    if not item_col:
        out.note = f"couldn't find an item-name column in: {', '.join(headers[:8])}"
        return out
    out.note = f"columns: item={item_col!r} qty={qty_col!r} amount={amt_col!r}"

    for row in rows:
        name = (row.get(item_col) or "").strip()
        if not name or not looks_like_ticket(name):
            continue
        qty = 1
        if qty_col:
            raw = re.sub(r"[^0-9.\-]", "", (row.get(qty_col) or "").strip())
            try:
                qty = int(round(float(raw))) if raw else 0
            except ValueError:
                qty = 0
        cents = parse_money(row.get(amt_col, "")) if amt_col else 0
        out.items += qty
        out.amount += cents
        out.by_item[name] = out.by_item.get(name, 0) + qty
    return out


def toast_for_day(day: dt.date, csv_override: Path | None) -> ToastSales:
    """API if credentials are set, else a CSV export, else say so plainly."""
    if csv_override:
        if not csv_override.exists():
            return ToastSales(note=f"{csv_override} not found")
        return toast_sales_csv(csv_override)

    if toast_configured():
        start = dt.datetime.combine(day, dt.time(0, 0), PACIFIC)
        end = start + dt.timedelta(days=1)
        try:
            return toast_sales_api(start, end)
        except Exception as e:  # noqa: BLE001 — Eventbrite half must still report
            print(f"  ⚠️ Toast API failed for {day}: {e}")
            return ToastSales(note=f"Toast API error: {e}")

    for candidate in sorted(TOAST_CSV_DIR.glob(f"{day.isoformat()}*.csv")):
        return toast_sales_csv(candidate)

    return ToastSales(note="no Toast credentials and no CSV export for this date")


# ─── report shaping ──────────────────────────────────────────────────────────

@dataclass
class EventReport:
    name: str
    url: str
    day: dt.date
    start_local: str
    sales: TicketSales


@dataclass
class DayReport:
    """Toast is a per-DAY total: the POS knows the door rang up 31 covers, not
    which of two same-night events each cover belonged to. Kept at day level
    rather than split by a guess."""
    day: dt.date
    events: list[EventReport]
    toast: ToastSales

    @property
    def eb_payout(self) -> int:
        return sum(e.sales.payout for e in self.events)

    @property
    def total_take(self) -> int:
        return self.eb_payout + self.toast.amount


def pretty_day(day: dt.date) -> str:
    # Built by hand rather than with strftime("%-d"): the no-pad flag is
    # glibc-only and raises on Windows.
    return f"{day:%a %b} {day.day}, {day.year}"


def pretty_time(start_local: str) -> str:
    """'2026-09-06T21:00:00' -> '9:00 PM'. Empty string if it won't parse."""
    try:
        t = dt.datetime.fromisoformat(start_local)
    except (TypeError, ValueError):
        return ""
    hour = 12 if t.hour % 12 == 0 else t.hour % 12
    return f"{hour}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'}"


def render_telegram(days: list[DayReport]) -> str:
    lines: list[str] = []
    for d in days:
        lines.append(f"🎟️ Sales report — {pretty_day(d.day)}")
        for e in d.events:
            s = e.sales
            when = pretty_time(e.start_local)
            lines.append(f"\n▸ {e.name}" + (f" — {when}" if when else ""))
            bits = [f"{s.tickets_sold} ticket{'s' if s.tickets_sold != 1 else ''}"]
            if s.free_tickets and s.paid_tickets:
                bits.append(f"{s.paid_tickets} paid / {s.free_tickets} free RSVP")
            elif s.free_tickets:
                bits.append("all free RSVP — cover collected at the door")
            if s.tickets_sold:
                pct = round(100 * s.checked_in / s.tickets_sold)
                bits.append(f"{s.checked_in} checked in ({pct}%)")
            lines.append("   " + " · ".join(bits))
            if s.gross:
                lines.append(f"   Gross {usd(s.gross)} · fees −{usd(s.eventbrite_fee + s.payment_fee)}"
                             + (f" · tax −{usd(s.tax)}" if s.tax else ""))
                lines.append(f"   → Eventbrite payout ≈ {usd(s.payout)}")
            if s.refunded_tickets:
                lines.append(f"   Refunded: {s.refunded_tickets} ({usd(s.refunded_gross)})")
            if s.discount_codes:
                codes = " · ".join(f"{c} {n}" for c, n in
                                   sorted(s.discount_codes.items(), key=lambda kv: -kv[1]))
                lines.append(f"   Codes: {codes}")

        t = d.toast
        if t.source == "none":
            lines.append(f"\n🍞 Toast door: not connected ({t.note})")
        else:
            lines.append(f"\n🍞 Toast door: {t.items} item{'s' if t.items != 1 else ''}"
                         f" · {usd(t.amount)}")
        if t.source == "none":
            # Never print a total that silently treats un-wired door sales as $0
            # — on a free-RSVP night that reads as "we made nothing".
            lines.append(f"\n💰 Eventbrite payout ≈ {usd(d.eb_payout)}"
                         " — door sales not included, Toast isn't connected yet.")
        else:
            lines.append(f"\n💰 Total take ≈ {usd(d.total_take)}"
                         f"  (Eventbrite {usd(d.eb_payout)} + door {usd(t.amount)})")
        lines.append("")

    lines.append("Eventbrite figures are its own per-order numbers — the payout "
                 "report is the bank-authoritative one.")
    return "\n".join(lines).strip()


def render_markdown(d: DayReport) -> str:
    out = [f"# Sales report — {pretty_day(d.day)}", ""]
    out.append(f"*Generated {dt.datetime.now(PACIFIC):%Y-%m-%d %H:%M %Z} by "
               "`code/sales_report.py`.*")
    out.append("")
    if d.toast.source == "none":
        out.append(f"**Eventbrite payout ≈ {usd(d.eb_payout)}** — door sales are "
                   "*not* included below: Toast isn't connected yet.")
    else:
        out.append(f"**Total take ≈ {usd(d.total_take)}** — Eventbrite "
                   f"{usd(d.eb_payout)} + Toast door {usd(d.toast.amount)}")
    out.append("")

    out.append("## Eventbrite")
    out.append("")
    if not d.events:
        out.append("No Eventbrite events on this date.")
    else:
        out.append("| Event | Tickets | Checked in | Gross | Fees | Tax | Payout (est.) |")
        out.append("|---|---:|---:|---:|---:|---:|---:|")
        for e in d.events:
            s = e.sales
            checked = f"{s.checked_in}" + (
                f" ({round(100 * s.checked_in / s.tickets_sold)}%)" if s.tickets_sold else "")
            when = pretty_time(e.start_local)
            label = f"{e.name}" + (f" ({when})" if when else "")
            out.append(f"| [{label}]({e.url}) | {s.tickets_sold} | {checked} | "
                       f"{usd(s.gross)} | {usd(s.eventbrite_fee + s.payment_fee)} | "
                       f"{usd(s.tax)} | **{usd(s.payout)}** |")
        out.append("")
        for e in d.events:
            s = e.sales
            details = []
            if s.by_ticket_class:
                details.append("By ticket type: " + ", ".join(
                    f"{k} — {v}" for k, v in sorted(s.by_ticket_class.items())))
            if s.free_tickets:
                details.append(f"Free RSVP tickets: {s.free_tickets} "
                               "(cover collected at the door, so the money shows up "
                               "under Toast rather than here)")
            if s.refunded_tickets:
                plural = "s" if s.refunded_tickets != 1 else ""
                details.append(f"Refunded: {s.refunded_tickets} ticket{plural}, "
                               f"{usd(s.refunded_gross)} — excluded from the totals above")
            if s.discount_codes:
                details.append("Discount codes redeemed: " + ", ".join(
                    f"**{c}** — {n}" for c, n in
                    sorted(s.discount_codes.items(), key=lambda kv: -kv[1])))
            if details:
                out.append(f"### {e.name}")
                out.extend(f"- {x}" for x in details)
                out.append("")

    out.append("## Toast (door)")
    out.append("")
    t = d.toast
    if t.source == "none":
        out.append(f"Not connected — {t.note}. See `docs/sales-report.md` for the "
                   "two ways to wire this up.")
    else:
        out.append(f"Source: `{t.source}`" + (f" — {t.note}" if t.note else ""))
        out.append("")
        out.append(f"**{t.items} ticket/cover items · {usd(t.amount)}**")
        if t.by_item:
            out.append("")
            out.append("| Item | Qty |")
            out.append("|---|---:|")
            for name, qty in sorted(t.by_item.items(), key=lambda kv: -kv[1]):
                out.append(f"| {name} | {qty} |")
    out.append("")
    out.append("---")
    out.append("")
    out.append("Payout is an estimate derived as gross − Eventbrite fee − payment fee "
               "− tax. Check **Reports → Payouts** in Eventbrite for the "
               "bank-authoritative figure before closing the books.")
    return "\n".join(out) + "\n"


def send_telegram_document(path: Path, caption: str) -> None:
    """Send the full markdown report as a file attachment. This is the archive:
    the repo is PUBLIC, so per-show revenue is never committed — Telegram keeps
    the file indefinitely, it's searchable, and it forwards to a bookkeeper."""
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_ids = [c.strip() for c in
                (os.environ.get("TELEGRAM_NOTIFY_CHAT_IDS") or "").split(",") if c.strip()]
    if not token or not chat_ids:
        return
    for cid in chat_ids:
        try:
            with open(path, "rb") as fh:
                r = requests.post(f"https://api.telegram.org/bot{token}/sendDocument",
                                  timeout=45, data={"chat_id": cid, "caption": caption[:1000]},
                                  files={"document": (path.name, fh, "text/markdown")})
            print(f"  Telegram file → {cid}: {r.status_code}")
        except (requests.RequestException, OSError) as e:
            print(f"  Telegram file → {cid} failed: {e}")


def send_telegram(text: str) -> None:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_ids = [c.strip() for c in
                (os.environ.get("TELEGRAM_NOTIFY_CHAT_IDS") or "").split(",") if c.strip()]
    if not token or not chat_ids:
        print("\n(Telegram not configured — skipping send.)")
        return
    for cid in chat_ids:
        try:
            r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=20,
                              json={"chat_id": cid, "text": text[:4000],
                                    "disable_web_page_preview": True})
            print(f"  Telegram → {cid}: {r.status_code}")
        except requests.RequestException as e:
            print(f"  Telegram → {cid} failed: {e}")


# ─── main ────────────────────────────────────────────────────────────────────

def build_reports(start: dt.datetime, end: dt.datetime,
                  csv_override: Path | None) -> list[DayReport]:
    events = eb_events_in_window(start, end)
    print(f"Eventbrite: {len(events)} event(s) between "
          f"{start:%Y-%m-%d %H:%M} and {end:%Y-%m-%d %H:%M} PT")

    by_day: dict[dt.date, list[EventReport]] = {}
    for ev in events:
        local = ev["start"]["local"]
        day = dt.date.fromisoformat(local[:10])
        name = (ev.get("name") or {}).get("text") or "(untitled)"
        print(f"  · {name} — {local}")
        by_day.setdefault(day, []).append(EventReport(
            name=name, url=ev.get("url") or "", day=day, start_local=local,
            sales=eb_event_sales(ev["id"])))

    days = []
    for day in sorted(by_day):
        print(f"Toast: reading door sales for {day}…")
        days.append(DayReport(day=day, events=by_day[day],
                              toast=toast_for_day(day, csv_override)))

    # A show day with no Eventbrite event still has door sales worth reporting.
    if not days and csv_override:
        day = start.date()
        days.append(DayReport(day=day, events=[], toast=toast_for_day(day, csv_override)))
    return days


def main() -> int:
    ap = argparse.ArgumentParser(description="Post-show Eventbrite + Toast sales report")
    ap.add_argument("--date", help="report one show day, YYYY-MM-DD (Pacific)")
    ap.add_argument("--days", type=int,
                    help="report the last N days of shows instead of the default window")
    ap.add_argument("--toast-csv", type=Path,
                    help="path to a Toast item-sales CSV export for this date")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the report; don't send Telegram or write a file")
    ap.add_argument("--selftest", action="store_true",
                    help="offline check of the money math; makes no API calls")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    now = dt.datetime.now(PACIFIC)
    if args.date:
        day = dt.date.fromisoformat(args.date)
        start = dt.datetime.combine(day, dt.time(0, 0), PACIFIC)
        end = start + dt.timedelta(days=1)
    elif args.days:
        end = now
        start = now - dt.timedelta(days=args.days)
    else:
        end = now
        start = now - dt.timedelta(hours=DEFAULT_LOOKBACK_HOURS)

    days = build_reports(start, end, args.toast_csv)
    if not days:
        print("\nNo events in that window — nothing to report.")
        return 0

    text = render_telegram(days)
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")

    if args.dry_run:
        print("DRY RUN — no Telegram sent, no report file written.")
        return 0

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for d in days:
        path = REPORT_DIR / f"{d.day.isoformat()}.md"
        path.write_text(render_markdown(d), encoding="utf-8")
        print(f"Wrote {path.relative_to(REPO_ROOT)}")
        written.append((d, path))

    send_telegram(text)
    for d, path in written:
        send_telegram_document(path, f"Full sales report — {pretty_day(d.day)}")
    return 0


# ─── self-test ───────────────────────────────────────────────────────────────

def selftest() -> int:
    """Offline check of the parts that are easy to get quietly wrong: the money
    math, refund exclusion, and the tolerant CSV column matching."""
    import tempfile

    failures = 0

    def check(label: str, got, expected):
        nonlocal failures
        ok = got == expected
        if not ok:
            failures += 1
        print(f"  {'ok  ' if ok else 'FAIL'} {label}: {got!r}"
              + ("" if ok else f" (expected {expected!r})"))

    check("usd(0)", usd(0), "$0.00")
    check("usd(150000)", usd(150000), "$1,500.00")
    check("usd(-1500)", usd(-1500), "-$15.00")
    check("parse_money('$1,234.56')", parse_money("$1,234.56"), 123456)
    check("parse_money('(12.00)')", parse_money("(12.00)"), -1200)
    check("parse_money('')", parse_money(""), 0)
    check("parse_money('n/a')", parse_money("n/a"), 0)

    # Fee-passed-to-buyer: $15 face, $2.29 EB fee, $0.55 payment fee.
    a_paid = {"costs": {"base_price": {"value": 1500}, "gross": {"value": 1784},
                        "eventbrite_fee": {"value": 229}, "payment_fee": {"value": 55},
                        "tax": {"value": 0}},
              "checked_in": True, "ticket_class_name": "General Admission"}
    # Fees absorbed by us: buyer pays $15, we net $12.16.
    a_absorbed = {"costs": {"base_price": {"value": 1500}, "gross": {"value": 1500},
                            "eventbrite_fee": {"value": 229}, "payment_fee": {"value": 55},
                            "tax": {"value": 0}},
                  "checked_in": False, "ticket_class_name": "General Admission"}
    a_free = {"costs": {"base_price": {"value": 0}, "gross": {"value": 0},
                        "eventbrite_fee": {"value": 0}, "payment_fee": {"value": 0},
                        "tax": {"value": 0}},
              "checked_in": True, "ticket_class_name": "GA — $10 cover at door"}

    s = TicketSales()
    for a in (a_paid, a_absorbed, a_free):
        base = _cost(a, "base_price")
        if base > 0:
            s.paid_tickets += 1
        else:
            s.free_tickets += 1
        s.gross += _cost(a, "gross")
        s.eventbrite_fee += _cost(a, "eventbrite_fee")
        s.payment_fee += _cost(a, "payment_fee")
        s.tax += _cost(a, "tax")
        if a.get("checked_in"):
            s.checked_in += 1

    check("paid tickets", s.paid_tickets, 2)
    check("free tickets", s.free_tickets, 1)
    check("tickets sold", s.tickets_sold, 3)
    check("checked in", s.checked_in, 2)
    check("gross", s.gross, 3284)
    # 3284 - 458 - 110 - 0 = 2716  ($15.00 face + $12.16 absorbed net)
    check("payout", s.payout, 2716)
    check("payout formatted", usd(s.payout), "$27.16")
    check("missing costs block is 0", _cost({}, "gross"), 0)

    # Ticket-name matching drives the whole Toast side.
    os.environ.pop("TOAST_TICKET_ITEMS", None)
    check("'Door Cover' is a ticket", looks_like_ticket("Door Cover"), True)
    check("'ADMISSION $10' is a ticket", looks_like_ticket("ADMISSION $10"), True)
    check("'Margarita' is not", looks_like_ticket("Margarita"), False)
    check("'Red Bull' is not", looks_like_ticket("Red Bull"), False)

    # 'Menu Item' must win over 'Item Qty'; 'Net Sales' over 'Net Sales %'.
    headers = ["Menu Item", "Item Qty", "Net Sales %", "Net Sales", "Gross Sales"]
    check("item column", _pick_column(headers, CSV_ITEM_KEYS), "Menu Item")
    check("qty column", _pick_column(headers, CSV_QTY_KEYS), "Item Qty")
    check("amount column", _pick_column(headers, CSV_AMOUNT_KEYS), "Net Sales")
    check("missing column is None", _pick_column(["Foo"], CSV_ITEM_KEYS), None)
    # A percentage column must never be picked as money, even when it is the
    # only near-match: reporting "Net Sales %" as dollars would look plausible
    # and be badly wrong.
    check("percent-only never matches money",
          _pick_column(["Menu Item", "Net Sales %"], CSV_AMOUNT_KEYS), None)
    check("falls back to Gross Sales",
          _pick_column(["Menu Item", "Net Sales %", "Gross Sales"], CSV_AMOUNT_KEYS),
          "Gross Sales")

    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp) / "2026-09-06.csv"
        csv_path.write_text(
            "Menu Item,Item Qty,Net Sales\n"
            "Door Cover,31,$465.00\n"
            "Margarita,58,$696.00\n"
            "Advance Ticket,4,$60.00\n",
            encoding="utf-8")
        t = toast_sales_csv(csv_path)
    check("CSV ticket items", t.items, 35)
    check("CSV ticket amount", t.amount, 52500)
    check("CSV excluded the bar", "Margarita" in t.by_item, False)

    if failures:
        print(f"\n{failures} check(s) failed.")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
