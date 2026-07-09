// Azúcar → Google Calendar webhook.
// Paste this into script.google.com (New project), then Deploy → New deployment
// → Web app → Execute as: Me → Who has access: Anyone → Deploy.
// Copy the web app URL into the pipeline repo's GCAL_WEBHOOK_URL secret.
//
// The pipeline POSTs here right after it creates an Eventbrite event, and this
// script drops the event onto the shared "Azucar Events" calendar.

const CALENDAR_ID = 'c_9d7b35fff634fd116745c13d46a7b125a1c9f7aa6676652f4cc90ac4375a5e84@group.calendar.google.com';
const SHARED_TOKEN = 'azucar-gcal-2026'; // must match the pipeline's token

function doPost(e) {
  try {
    const p = JSON.parse(e.postData.contents);
    if (p.token !== SHARED_TOKEN) {
      return ContentService.createTextOutput('forbidden');
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
