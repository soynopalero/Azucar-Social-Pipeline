# Post-show sales report

Answers the two morning-after questions without logging into anything:

1. **Eventbrite** — how many tickets sold, and how much money actually lands in the bank.
2. **Toast** — how many covers/tickets rang up at the door.

You get a Telegram summary plus the full report as a file attachment, for every
show day. Nothing is committed: **this repo is public**, so per-show revenue
stays out of it. `reports/sales/` and `reports/toast/` are gitignored and
Telegram is the archive — the files stay in the chat, searchable, and forward
straight to a bookkeeper.

---

## Using it

It runs itself daily at 11:00 Pacific and reports any show from the last 36
hours. A day with no event exits quietly, so karaoke Wednesdays, Friday 18+
nights and Sunday shows are all covered by the one schedule.

To pull a specific date (a backfill, or a show you want to re-check):

**From GitHub** — Actions → *Post-show sales report* → *Run workflow* → put the
date in, e.g. `2026-09-06`.

**From your machine:**

```bash
python code/sales_report.py --date 2026-09-06   # one show day
python code/sales_report.py --days 7            # the last week
python code/sales_report.py --dry-run           # print only, send nothing
python code/sales_report.py --selftest          # check the math, no API calls
```

---

## What the numbers mean

| Line | What it is |
|---|---|
| **Tickets** | One row per ticket, not per order — a buyer taking 4 counts as 4. Refunded and cancelled tickets are excluded. |
| **Checked in** | How many of those advance tickets actually walked in. The gap is your no-show rate. |
| **Gross** | What buyers paid in total. |
| **Fees** | Eventbrite's service fee + payment processing. |
| **Payout (est.)** | `gross − Eventbrite fee − payment fee − tax`. |
| **Free RSVP** | Tickets with a $0 face value — the `"$X cover at door"` ones this repo's bot creates. Counted separately so a $0 payout on a busy night reads as expected, not as a bug. That money shows up under Toast instead. |
| **Codes** | Per-discount-code redemptions — this is how you tell which queen actually brought people (SLAYON / BLUNT / FANTASY). |

**Payout is an estimate.** It's derived from Eventbrite's own per-order figures
and matches the payout report in the ordinary case, but refunds mid-cycle,
chargebacks and tax remittance can move it. Before closing the books, check
**Reports → Payouts** in Eventbrite — that one is bank-authoritative.

---

## Toast: two ways to wire it up

Toast works either way. Until one is set up, the report still runs and just
says the door numbers aren't connected.

### Option A — the API (fully automatic)

Needs **Standard API access** on your Toast plan. To check whether you already
have it:

1. Log into **Toast Web**.
2. Go to **Integrations → Manage credentials** (**Toast Partner Integrations →
   API access** on some plans).
3. If you see **Create Analytics API Credentials** (or *Create Standard API
   Credentials*), you have it — create a credential and copy the **Client ID**
   and **Client secret**. The secret is shown **once**.
4. If the page isn't there, ask your Toast rep for *Standard API access*. It's
   sold as a read-only add-on, no partner agreement or integrator needed — but
   confirm the cost with them, it isn't published and it isn't on every plan.

You also need your **restaurant GUID**: Toast Web → **Restaurant Info**, or the
long `restaurantGuid` in the URL when you're in that location.

Then add three repo secrets (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `TOAST_CLIENT_ID` | Client ID from step 3 |
| `TOAST_CLIENT_SECRET` | Client secret from step 3 |
| `TOAST_RESTAURANT_GUID` | The location GUID |

### Option B — the CSV export (no API cost, one manual step)

1. Toast Web → **Reports → Sales → Menu item sales** (any item-level export
   works — the parser matches columns by header name).
2. Set the date range to the show day, export CSV.
3. Save it as `reports/toast/2026-09-06.csv` — named for the show date.
4. Run `python code/sales_report.py --date 2026-09-06` locally.

Because the folder is gitignored, the CSV path only works on your own machine —
the scheduled run can't see a file that was never pushed. If you want the door
numbers in the automatic Telegram report, that's Option A.

You can also point at a file directly:

```bash
python code/sales_report.py --date 2026-09-06 --toast-csv ~/Downloads/export.csv
```

### Which items count as a ticket

By default any item whose name contains **cover, ticket, admission, entry** or
**door**. If your POS buttons are named something else, set the
`TOAST_TICKET_ITEMS` repo *variable* (not secret) to a comma-separated list:

```
TOAST_TICKET_ITEMS = cover,ticket,admission,entry,door,puerta
```

Get this right or the number is quietly wrong — check the item table in the
first report against what you know the door took.

---

## When something breaks

- **A failed run Telegrams you** with a link to the log, so a silent failure
  doesn't look like a quiet night.
- **`EVENTBRITE_TOKEN env var is empty`** — the secret is missing or expired;
  it's the same one the Eventbrite create-event bot uses.
- **`discount codes unavailable`** — harmless. Code stats need organizer scope
  on the token; everything else still reports.
- **Toast API errors** are caught and printed — the Eventbrite half always
  still reports.
- **`python code/sales_report.py --selftest`** checks the money math offline,
  without touching either API. The workflow runs it before every report.
