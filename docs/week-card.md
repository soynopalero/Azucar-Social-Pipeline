# The "This Week at Azúcar" card

The first slide of the Monday round-up carousel. A punk-zine card with the
week written out, because a stack of flyers does not tell anyone what is on
Thursday.

- **Template (do not post this one):** https://www.canva.com/design/DAHWLCTrgMQ/edit
- **Builder:** `code/build_week_card.py` — board to six rows
- **Review + gate:** `code/week_card_review.py` — Telegram approval
- **Runs:** `.github/workflows/week-card.yml`, **Fridays 09:00 PT**

---

## The approval gate

**Nothing posts unless Pedro taps ✅.** A week that is never approved is
simply never queued — silence beats a wrong post.

```
Friday 09:00 PT   workflow reads the board for NEXT week
                  -> Telegram: the rows + [✅ Post it] [✏️ Change something]

tap ✅            bot fires week-card.yml with action=approve
                  -> re-reads the board, queues the round-up for Monday 11:00

tap ✏️            bot asks what to change (typing or a voice note)
                  -> fires action=regen with the note
                  -> rebuilt card comes back for another look
```

Friday on purpose: it leaves the weekend to fix the board before anything is
queued. Most feedback is really "the board is wrong" — fix it there and tap
🔄 Just rebuild, so the board stays the single source of truth.

The buttons are handled by the Telegram bot in the **azucar-events-pipeline**
repo (`src/telegram.js`, the `week:` callback). It writes nothing here — it
fires this workflow back with the action, the same baton the caption approval
already passes. Pedro's note rides in as a workflow input, so unlike captions
there is no Monday column to write and later clear.

`week-carousel.yml` has **no schedule any more**. Queueing is what approval
does; a cron there would post the week whether or not anyone tapped. It stays
dispatch-only as the manual escape hatch.

## What still needs hands

Filling the Canva template. The credentials now exist — see **Canva API**
below — but the fill is not wired into the Friday job yet, so the last step is
manual: paste six rows, delete the empty strips, export.

It takes about two minutes. The section below is the whole procedure.

---

## Filling the card

1. Open the template and **duplicate it** (File → Make a copy). Never type
   into the template itself — it is the thing every future week starts from.
2. Paste the rows from the Telegram message into the copy.
3. **Delete the strip and the black day tag of every row you did not fill.**
   An empty row does not disappear on its own; it leaves blank paper. This is
   the step people forget.
4. Export as PNG and hand it to the carousel as the first slide.

A Claude session with the Canva MCP can do all four in one go — the template's
fields are already named, so it is `autofill-design` followed by deleting the
unused strips. Ask for "fill this week's card".

---

## The six slots

The template has six event rows, tagged as Canva autofill fields. The builder
emits exactly these names:

| Field | Example |
|---|---|
| `week_label` | `Week Sept 21-27` |
| `day_1` … `day_6` | `THU 24` |
| `title_1` … `title_6` | `Heels Class` |
| `detail_1` … `detail_6` | `with Frankie 6 PM • with Kimora 7 PM • 21+ • $10` |

Six is the ceiling. A seventh event is **not** dropped — it comes back under
`overflow` and belongs in the caption, the same contract the carousel already
uses for flyers past Meta's 10-slide limit.

---

## Where the words come from

Nothing is typed into the card by hand. Every row is built from the board:

| On the card | From the board |
|---|---|
| Big bold line | **Card Title**, else the event name shortened |
| Start of the small line | **Card Tagline**, else **Primary Entertainer** |
| Rest of the small line | **Age Restriction** • **Event Time** • **Price From** |
| Day tag | **Event Date** |

`Card Title` and `Card Tagline` are overrides. Leave them empty and the
pipeline guesses; fill them when the guess reads badly. Two cases worth
knowing:

- **Long names.** "American Horror Story viewing party and Drag show" does not
  fit the bold line. Its Card Title is `AHS Drag Show`. The builder reports any
  title still too long rather than clipping it silently, so check the Telegram
  message for a `WARNING`.
- **An act named after its own event.** Furanium Fever's Primary Entertainer is
  "Furanium Fever", which would read as a stutter. When the act matches the
  title the builder leaves it out, so that row gets a Card Tagline instead.

---

## Merging two events into one row

Two events on the same day that are really one thing — the 6pm and 7pm heels
classes — take **one** row. Six rows is a hard ceiling, and spending two of
them on the same class is how a genuinely busy week loses an event.

The merged row keeps each part's own time:

```
THU 24  Heels Class
        with Frankie 6 PM • with Kimora 7 PM • 21+ • $10
```

Merging is decided in this order:

1. **Same day + same Card Title.** Explicit, and the way to force it. Setting
   both heels classes to `Heels Class` is what combines them.
2. **Same day + near-identical names.** "Heels dance class with Frankie" and
   "...with Kimora" merge on their shared prefix. This is the fallback for
   events nobody has given a Card Title yet.

Different days never merge, whatever the names. "Drag Bingo" and "Drag Show"
do not merge on a shared first word.

**To stop two events merging:** give them different Card Titles.

---

## Things that will bite

- **Prices are hand-typed and inconsistent.** The board really holds `$10`,
  `10$`, `20`, `Free` and `$20-$40`. They are all normalised to a leading sign,
  so a merged row does not claim the two heels classes cost different amounts.
  `Free` becomes `FREE`.
- **Deleting rows exposes the background.** The page background carries faint
  ghost lettering behind the lower rows. Covered on a six-event week, slightly
  visible on a quiet one. It reads as zine texture, but that is why it is there.
- **Adding a seventh row is not a small change.** Row geometry is fixed: tops
  at `462 + 142 × (n-1)`, strips 790.6 × 128. Seven rows means re-flowing all
  of them and dropping the title size below 46px, which is where it stops being
  readable on a phone.
- **New text boxes come out in the wrong font.** Canva's editing API sets size,
  colour and weight but not typeface. This does not affect filling the card —
  the six rows already exist and only their text changes. It only bites if
  someone adds a row.

---

## Canva API

Connect API credentials are in place. `code/canva_api.py --probe` asked Canva
directly on **2026-09-26**; these are its answers, not the documentation's:

| Question | Answer |
|---|---|
| Is `autofill` available? | **Yes**, and `brand_template` too |
| Is autofill trial-limited on this account? | **No.** A real autofill returned no `trial_information` at all |
| Do refresh tokens survive being used? | **No.** Single-use, and re-using one revokes every token from that flow |

The spec says autofill is Enterprise-only. It is not, on this account — which
is why the probe exists: the only trustworthy answer came from spending one
real call.

### The token rotation problem

Every refresh spends the stored token and returns a replacement, so a fixed
`CANVA_REFRESH_TOKEN` secret authenticates exactly once. `code/gh_secret.py`
writes the replacement straight back into the secret, in the same breath as the
refresh, before anything else can fail and strand it.

That needs **`GH_SECRETS_PAT`**: a fine-grained PAT scoped to this repository
alone, with **Secrets: Read and write** and nothing else. `GITHUB_TOKEN` cannot
do it — there is no `secrets: write` permission to grant a workflow.

Without the PAT nothing breaks immediately: the rotated token is sent to
Telegram to be pasted in by hand. That works, and it is not a plan — a weekly
job that needs a human to paste a credential fails on the first busy Friday.

Two rules the code enforces, both for the same reason (**this repo is public,
and so is every Actions log**):

- A token is never printed. Only a fingerprint — first six characters, last
  four, length — which is enough to tell two tokens apart in a log and not
  enough to use one.
- A failure reason never contains the value that failed to write.

### Re-authorizing

Needed only if the token is ever lost — a crash between refresh and write-back,
or a revoked flow. `python code/canva_authorize.py` on a normal computer, with
`CANVA_CLIENT_ID` (the auth client's `OC-…`, from Outside Canva →
Configuration, **not** the App ID) and `CANVA_CLIENT_SECRET` set. It prints one
refresh token, once.

Authorizing again silently invalidates the previous refresh token, so do it
only when you mean to replace it.

### One template per row count

**Connect cannot delete elements.** An unfilled row leaves a blank strip, and
the MCP `delete-element` call that removes one has no REST equivalent. So the
rows are removed up front — once, by hand — and the job picks the template
matching the week:

| Events | Template | |
|---|---|---|
| 3 | `DAHWQ9JH6J0` | https://www.canva.com/design/DAHWQ9JH6J0/edit |
| 4 | `DAHWQpp0I-E` | https://www.canva.com/design/DAHWQpp0I-E/edit |
| 5 | `DAHWQnDRd5c` | https://www.canva.com/design/DAHWQnDRd5c/edit |
| 6 | `DAHWLCTrgMQ` | the original |

`canva_api.WEEK_CARD_TEMPLATES` is the registry; `template_for(rows)` picks one.

**Below three events there is no card.** One or two events is a flyer, not a
week, and the carousel already falls back to a single photo post. Those weeks
go to Telegram to be handled by hand rather than posting a near-empty card.

Three things learned building these, all of which will bite again:

- **Rows are bottom-anchored, not centred.** The last row always ends at
  y=1300, where row 6 ended. Centring a short block looked more balanced until
  it was rendered — see the ghost lettering below.
- **The background has old text baked into it.** `MAHWLHd8FoY` carries a faint
  "Heels Class" and "AHS Drag Show" across the strip band, apparently from an
  earlier export. Six rows cover it; fewer do not, and it reads as a printing
  error rather than as texture. Each variant therefore carries a black panel
  over the exposed band (x 312→1060, from y=486 down to its first row). The
  real fix is re-exporting the background without the ghost text.
- **`get-design-dataset` lies about trimmed templates.** It reports all 19
  fields for every variant, including rows that were deleted. It cannot tell
  you a template's row count, which is why the count is hard-coded, and why
  `fields_for()` trims the payload — an untrimmed one fails quietly.

Also fixed in all three: row 4's day text sat 7px lower than every other row
in the original (tag at 898, text at 910, where the rest are tag+5). **The
master `DAHWLCTrgMQ` still has that 7px drop** — worth correcting there too.

### What is still missing

The Friday job does not call Canva yet. `build_week_card.py` already emits
exactly the payload `/v1/autofills` wants and the templates now exist, so what
remains is wiring: pick the template, trim the fields, autofill, export the
PNG, hand it to the carousel as slide one.
