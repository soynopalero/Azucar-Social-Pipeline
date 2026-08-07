// Azúcar → Google Calendar webhook (v3: create + sync cleanup).
// v3 fixes the sync fallback: pulse-tagged entries are never title-matched,
// so a cancelled duplicate item can't delete the real event's entry.
// Paste this into script.google.com (the existing project), then redeploy:
// Deploy → Manage deployments → ✏️ Edit → Version: "New version" → Deploy.
// The web app URL stays the same, so no repo secret changes are needed.
//
// POST (no action, or action:"create") — original behavior: the pipeline calls
// this right after creating an Eventbrite event, and it drops the event onto
// the shared "Azucar Events" calendar.
//
// POST action:"sync" — called by code/gcal_sync.py for each Monday item:
//   deletes the matching calendar entry when the item is Cancelled/Postponed,
//   or moves it when the Monday date/time no longer matches. Matching is by
//   the Monday pulse URL that "create" bakes into the description; a
//   title+date fallback catches hand-made entries. dry_run:true reports what
//   would change without touching the calendar.
//
// GET — version probe ("azucar-gcal v3"). gcal_sync.py checks this first and
// refuses to run against an old deployment (v1 would mistake sync payloads
// for create requests; v2's fallback had the duplicate-deletion bug).

const CALENDAR_ID = 'c_9d7b35fff634fd116745c13d46a7b125a1c9f7aa6676652f4cc90ac4375a5e84@group.calendar.google.com';
const SHARED_TOKEN = 'azucar-gcal-2026'; // must match the pipeline's token
const TZ = 'America/Los_Angeles';

function doGet() {
  return ContentService.createTextOutput('azucar-gcal v3');
}

function doPost(e) {
  try {
    const p = JSON.parse(e.postData.contents);
    if (p.token !== SHARED_TOKEN) {
      return ContentService.createTextOutput('forbidden');
    }
    if (p.action === 'sync') {
      return ContentService
        .createTextOutput(JSON.stringify(syncEvent(p)))
        .setMimeType(ContentService.MimeType.JSON);
    }
    const cal = CalendarApp.getCalendarById(CALENDAR_ID);
    cal.createEvent(
      p.name,
      new Date(p.start_utc),
      new Date(p.end_utc),
      { description: p.description || '', location: p.location || '' }
    );
    return ContentService.createTextOutput('ok');
  } catch (err) {
    return ContentService.createTextOutput('error: ' + err);
  }
}

function syncEvent(p) {
  const cal = CalendarApp.getCalendarById(CALENDAR_ID);
  const now = new Date();
  // A week back so a just-passed stale entry still gets cleaned; ~18 months
  // forward covers anything the pipeline could have scheduled.
  const from = new Date(now.getTime() - 7 * 24 * 3600 * 1000);
  const to = new Date(now.getTime() + 550 * 24 * 3600 * 1000);
  const events = cal.getEvents(from, to);

  const marker = '/pulses/' + String(p.item_id);
  let matchedBy = 'pulse-id';
  let matches = events.filter(function (ev) {
    return (ev.getDescription() || '').indexOf(marker) !== -1;
  });

  const removing = p.status === 'cancelled' || p.status === 'postponed';
  if (!matches.length && removing && p.name && p.event_date) {
    // Fallback for hand-made entries the pipeline never tagged: exact same
    // title on the exact event day only — never a looser match, so a sibling
    // recurring show on another date can't be swept up. Entries carrying ANY
    // pulse tag are off-limits here: they belong to a specific Monday item
    // and are only ever matched by their own id above. (First dry-run caught
    // this: a cancelled duplicate item, same name + same day as the real one,
    // would otherwise have deleted the REAL event's entry.)
    matches = events.filter(function (ev) {
      return ev.getTitle() === p.name &&
        (ev.getDescription() || '').indexOf('/pulses/') === -1 &&
        Utilities.formatDate(ev.getStartTime(), TZ, 'yyyy-MM-dd') === p.event_date;
    });
    matchedBy = 'title+date';
  }

  const changes = [];
  matches.forEach(function (ev) {
    const entry = { id: ev.getId(), title: ev.getTitle(), start: ev.getStartTime().toISOString() };
    if (removing) {
      if (!p.dry_run) ev.deleteEvent();
      entry.change = 'delete';
      changes.push(entry);
    } else if (p.start_utc && p.end_utc) {
      const ns = new Date(p.start_utc);
      const ne = new Date(p.end_utc);
      if (Math.abs(ev.getStartTime().getTime() - ns.getTime()) > 60 * 1000) {
        if (!p.dry_run) ev.setTime(ns, ne);
        entry.change = 'reschedule';
        entry.new_start = ns.toISOString();
        changes.push(entry);
      }
    }
  });

  return {
    ok: true,
    action: 'sync',
    item_id: String(p.item_id),
    matched: matches.length,
    matched_by: matches.length ? matchedBy : null,
    dry_run: !!p.dry_run,
    changes: changes,
  };
}
