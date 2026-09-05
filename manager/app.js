/* Azúcar Post Manager — front-end.

   Two modes, detected at boot:
   - LIVE: /api/events responds → reads the real pipeline queue from GitHub and
     saves edits back through /api/save (Cloudflare Pages Functions, behind
     Cloudflare Access). Photos upload through /api/upload.
   - DEMO: no API (local prototype) → loads static events.json and keeps all
     edits in memory so you can click around safely. */

const LEAD_MS = 2 * 60 * 60 * 1000;         // 2-hour minimum lead time
const DAY = 24 * 60 * 60 * 1000;

let DATA = { events: [] };
let LIVE = false;
let FALLBACK = false;                         // live API exists but is failing → read-only snapshot
let currentView = 'upcoming';
let currentEvent = null;
let editingPost = null;                       // logical post being edited, or null for "new"
let photosState = [];                         // photo URLs in the open editor

/* ---------- helpers ---------- */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) => (s || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function todayStart() { const d = new Date(); d.setHours(0, 0, 0, 0); return d; }
function isArchived(ev) { return new Date(ev.event_date + 'T23:59:59') < todayStart(); }
function eventDateDisplay(ev) {
  const d = new Date(ev.event_date + 'T12:00:00');
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
}
function daysUntil(ev) {
  const d = new Date(ev.event_date + 'T12:00:00');
  return Math.round((d - todayStart()) / DAY);
}
function statusCounts(ev) {
  const c = { pending: 0, posted: 0, failed: 0 };
  ev.posts.forEach(p => { c[p.status] = (c[p.status] || 0) + 1; });
  return c;
}
function flyerStyle(ev) {
  const img = ev.posts.find(p => p.images && p.images.length)?.images[0];
  return img ? `background-image:url('${img}')` : `background-image:${ev.flyer_grad}`;
}
function postThumb(p, ev) {
  if (p.images && p.images.length) return `background-image:url('${p.images[0]}')`;
  return `background-image:${p.image_grad || ev.flyer_grad}`;
}
function pill(status, n) {
  const map = { pending: ['pill-pending', 'pending'], posted: ['pill-posted', 'posted'], failed: ['pill-failed', 'to fix'] };
  const [cls, label] = map[status];
  return `<span class="pill ${cls}"><span class="d"></span>${n} ${label}</span>`;
}

/* ---------- API ---------- */
async function api(path, opts) {
  const res = await fetch(path, opts);
  let data = {};
  try { data = await res.json(); } catch { /* non-JSON error page */ }
  if (!res.ok) {
    const err = new Error(data.error || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return data;
}

async function refreshData() {
  if (LIVE) {
    DATA = await api('/api/events');
  }
  if (currentEvent) {
    currentEvent = DATA.events.find(e => e.id === currentEvent.id) || null;
  }
}

/* ---------- list view ---------- */
function renderList() {
  const upcoming = DATA.events.filter(e => !isArchived(e)).sort((a, b) => a.event_date.localeCompare(b.event_date));
  const history = DATA.events.filter(isArchived).sort((a, b) => b.event_date.localeCompare(a.event_date));
  $('#seg-up').textContent = upcoming.length;
  $('#seg-hist').textContent = history.length;

  const list = currentView === 'upcoming' ? upcoming : history;
  const isHist = currentView === 'history';
  $('#list-title').textContent = isHist ? 'History' : 'Upcoming events';
  $('#list-count').textContent = list.length + (isHist ? ' archived' : ' active');
  $('#list-note').textContent = isHist
    ? 'Events that have already happened move here automatically. Read-only.'
    : 'Events with a future date. They archive themselves the day after they happen.';
  $('#btn-new').style.display = isHist ? 'none' : '';
  $('#samplebar').style.display = (!LIVE && !FALLBACK && !isHist && upcoming.some(e => e.source === 'sample')) ? '' : 'none';

  const wrap = $('#eventlist');
  if (!list.length) {
    wrap.innerHTML = `<div class="empty"><div class="big">${isHist ? '🗂️' : '🌤️'}</div>
      <h3>${isHist ? 'Nothing archived yet' : 'No upcoming events'}</h3>
      <p>${isHist ? 'Past events will collect here once they wrap.' : 'When you schedule posts for a future event, its card shows up here.'}</p></div>`;
    return;
  }
  wrap.innerHTML = list.map(ev => {
    const c = statusCounts(ev);
    const du = daysUntil(ev);
    const badge = isHist ? '' : (du === 0 ? 'Today' : du === 1 ? 'Tomorrow' : `in ${du} days`);
    return `<button class="ev" data-ev="${ev.id}">
      <div class="flyer" style="${flyerStyle(ev)}">
        <span class="tag">${esc(ev.tag)}</span>
        ${badge ? `<span class="days">${badge}</span>` : ''}
      </div>
      <div class="body">
        <p class="name">${esc(ev.name)}</p>
        <p class="date">${eventDateDisplay(ev)} · ${ev.posts.length} posts</p>
        <div class="meta">
          <span class="pill pill-count">${ev.posts.length} posts</span>
          ${c.pending ? pill('pending', c.pending) : ''}
          ${c.failed ? pill('failed', c.failed) : ''}
          ${isHist && c.posted ? pill('posted', c.posted) : ''}
        </div>
      </div>
    </button>`;
  }).join('');
  $$('.ev', wrap).forEach(el => el.addEventListener('click', () => openEvent(el.dataset.ev)));
}

/* ---------- detail view ---------- */
function openEvent(id) {
  currentEvent = DATA.events.find(e => e.id === id);
  if (!currentEvent) { renderList(); showView('v-list'); return; }
  const ev = currentEvent;
  const archived = isArchived(ev);
  $('#d-name').textContent = ev.name;
  $('#d-date').textContent = eventDateDisplay(ev) + (archived ? ' · archived' : '');

  $('#d-controls').innerHTML = archived
    ? `<div class="archived-note">🗂️ This event has passed — it's archived and read-only. Its posts already went out.</div>`
    : `<div class="toolbar">
         <button class="btn btn-primary" id="btn-add">＋ Add a post</button>
         <span class="spacer" style="flex:1"></span>
         <button class="btn btn-danger" id="btn-delall">Delete all pending</button>
       </div>`;
  if (!archived) {
    $('#btn-add').addEventListener('click', () => openEdit(null));
    $('#btn-delall').addEventListener('click', deleteAll);
  }
  renderPosts(archived);
  showView('v-detail');
}

function groupByDay(posts) {
  const groups = new Map();
  [...posts].sort((a, b) => a.scheduled_for_utc.localeCompare(b.scheduled_for_utc)).forEach(p => {
    const label = new Date(p.scheduled_for_utc).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' });
    if (!groups.has(label)) groups.set(label, []);
    groups.get(label).push(p);
  });
  return groups;
}

function renderPosts(archived) {
  const ev = currentEvent;
  const groups = groupByDay(ev.posts);
  const html = [...groups.entries()].map(([day, posts]) => `
    <div class="dayhdr">${day}</div>
    ${posts.map(p => {
      const time = new Date(p.scheduled_for_utc).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
      const editable = !archived && p.status !== 'posted';
      return `<div class="post ${editable ? 'editable' : ''}" data-id="${p.ids[0]}">
        <div class="thumb" style="${postThumb(p, ev)}"><span class="plat ${p.platforms[0]}">${p.platforms[0] === 'facebook' ? 'FB' : 'IG'}</span></div>
        <div class="mid">
          <div class="time">${time}</div>
          <p class="cap">${esc(p.caption)}</p>
          <div class="plats">${p.platforms.map(x => `<span class="chip ${x}">${x === 'facebook' ? 'FB' : 'IG'}</span>`).join('')}</div>
          ${p.status === 'failed' && p.result ? `<div class="result-note">⚠️ ${esc(p.result)}</div>` : ''}
        </div>
        <div class="right">
          ${pillOne(p.status)}
          ${editable ? `<div class="rowbtns">
            <button class="icobtn" data-act="edit" aria-label="Edit">✏️</button>
            <button class="icobtn del" data-act="del" aria-label="Delete">🗑️</button>
          </div>` : ''}
        </div>
      </div>`;
    }).join('')}`).join('');
  $('#postlist').innerHTML = html;

  $$('.post.editable').forEach(el => {
    const id = el.dataset.id;
    el.addEventListener('click', (e) => {
      const act = e.target.closest('[data-act]')?.dataset.act;
      if (act === 'del') { e.stopPropagation(); deleteOne(id, el); }
      else openEdit(findPost(id));
    });
  });
}

function pillOne(status) {
  const map = { pending: ['pill-pending', 'Pending'], posted: ['pill-posted', 'Posted'], failed: ['pill-failed', 'Needs fix'] };
  const [cls, label] = map[status];
  return `<span class="pill ${cls}"><span class="d"></span>${label}</span>`;
}
function findPost(id) { return currentEvent.posts.find(p => p.ids.includes(id)); }
/* What /api/save needs to address ONE event: the campaign key plus, for
   engine-made events, the Monday id (a recurring event's campaign key is shared
   with its earlier editions). Older API builds sent only `campaign: ev.id`. */
function eventRef(ev) {
  const ref = { campaign: ev.campaign || ev.id };
  if (ev.monday_event_id) ref.monday_event_id = ev.monday_event_id;
  if (ev.event_date) ref.event_date = ev.event_date;
  return ref;
}

/* When the live API is broken we're showing an old snapshot — pretending to
   save would silently lose Pedro & Jamie's edits, so block writes loudly. */
function blockIfFallback() {
  if (FALLBACK) toast('⚠️ Live connection is down — changes can’t be saved right now.');
  return FALLBACK;
}

async function deleteOne(id, el) {
  if (blockIfFallback()) return;
  const post = findPost(id);
  el.style.transition = '.25s'; el.style.opacity = '.4';
  try {
    if (LIVE) {
      await api('/api/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ op: 'delete', ids: post.ids }) });
      await refreshData();
    } else {
      currentEvent.posts = currentEvent.posts.filter(p => p !== post);
    }
    if (currentEvent) { renderPosts(false); } else { renderList(); showView('v-list'); }
    toast('Post deleted');
  } catch (err) {
    el.style.opacity = '1';
    toast('⚠️ ' + err.message);
  }
}

async function deleteAll() {
  if (blockIfFallback()) return;
  const n = currentEvent.posts.filter(p => p.status !== 'posted').length;
  if (!confirm(`Delete all ${n} pending posts for "${currentEvent.name}"?${LIVE ? '' : '\n\n(Prototype — nothing is really removed yet.)'}`)) return;
  try {
    if (LIVE) {
      await api('/api/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ op: 'delete_campaign', ...eventRef(currentEvent) }) });
      await refreshData();
    } else {
      currentEvent.posts = currentEvent.posts.filter(p => p.status === 'posted');
    }
    if (currentEvent) { openEvent(currentEvent.id); } else { renderList(); showView('v-list'); }
    toast('Pending posts deleted');
  } catch (err) {
    toast('⚠️ ' + err.message);
  }
}

/* ---------- edit modal ---------- */
function minWhen() { return new Date(Date.now() + LEAD_MS); }
function toLocalInput(d) {
  const p = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

function openEdit(post) {
  editingPost = post;
  const isNew = !post;
  $('#e-title').textContent = isNew ? 'Add a post' : 'Edit post';
  $('#e-cap').value = post ? post.caption : '';
  updateChars();

  photosState = post && post.images ? [...post.images] : [];
  renderPhotos();

  const min = minWhen();
  const whenEl = $('#e-when');
  whenEl.min = toLocalInput(min);
  let val = post ? new Date(post.scheduled_for_utc) : new Date(min.getTime() + DAY);
  if (val < min) val = new Date(min.getTime() + 30 * 60 * 1000);
  whenEl.value = toLocalInput(val);

  const plats = post ? post.platforms : ['instagram', 'facebook'];
  $$('.tog').forEach(t => t.classList.toggle('on', plats.includes(t.dataset.plat)));

  $('#e-err').classList.remove('show');
  $('#e-delete').style.display = isNew ? 'none' : '';
  setSaving(false);
  $('#overlay').classList.add('active');
  $('#e-cap').focus();
}

function renderPhotos() {
  const ph = $('#e-photos');
  ph.innerHTML = photosState.map((src, i) =>
    `<div class="photo" data-i="${i}" style="background-image:url('${src}')"><span class="rm">✕</span></div>`
  ).join('') + `<label class="photo add" title="Add a photo"><span>＋</span></label>`;
  $$('.photo .rm', ph).forEach((x, i) => x.addEventListener('click', e => {
    e.stopPropagation();
    photosState.splice(i, 1);
    renderPhotos();
  }));
  $('.photo.add', ph).addEventListener('click', () => $('#e-file').click());
}

async function onFilePicked(e) {
  const file = e.target.files[0];
  e.target.value = '';
  if (!file) return;
  if (LIVE) {
    toast('Uploading photo…');
    try {
      const form = new FormData();
      form.set('file', file);
      const { url } = await api('/api/upload', { method: 'POST', body: form });
      photosState.push(url);
      renderPhotos();
      toast('Photo added');
    } catch (err) {
      toast('⚠️ ' + err.message);
    }
  } else {
    photosState.push(URL.createObjectURL(file));
    renderPhotos();
    toast('Photo added (demo — local only)');
  }
}

function closeEdit() { $('#overlay').classList.remove('active'); editingPost = null; }
function updateChars() { $('#e-chars').textContent = $('#e-cap').value.length + ' characters'; }
function setSaving(b) {
  const btn = $('#e-save');
  btn.disabled = b;
  btn.textContent = b ? 'Saving…' : 'Save';
}

async function saveEdit() {
  if (FALLBACK) return showErr('Live connection is down — changes can’t be saved right now. Try again later.');
  const whenEl = $('#e-when');
  const chosen = new Date(whenEl.value);
  const plats = $$('.tog.on').map(t => t.dataset.plat);

  if (!whenEl.value || isNaN(chosen)) { return showErr('Pick a date and time for this post.'); }
  if (chosen < minWhen()) {
    return showErr('That time is too soon — posts must be at least 2 hours out. Pick a later time, or post it manually on Facebook if you need it now.');
  }
  if (!plats.length) { return showErr('Pick at least one place to post — Instagram, Facebook, or both.'); }
  if (!$('#e-cap').value.trim()) { return showErr('The caption is empty.'); }

  const isNew = !editingPost;
  if (LIVE) {
    setSaving(true);
    try {
      await api('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          op: 'upsert',
          ...eventRef(currentEvent),
          ids: editingPost ? editingPost.ids : [],
          platforms: plats,
          scheduled_for_utc: chosen.toISOString(),
          caption: $('#e-cap').value,
          image_url: photosState[0] || '',
        }),
      });
      await refreshData();
    } catch (err) {
      setSaving(false);
      return showErr(err.message);
    }
    closeEdit();
    if (currentEvent) { renderPosts(false); } else { renderList(); showView('v-list'); }
  } else {
    if (editingPost) {
      editingPost.caption = $('#e-cap').value;
      editingPost.platforms = plats;
      editingPost.scheduled_for_utc = chosen.toISOString();
      editingPost.images = [...photosState];
      editingPost.status = 'pending';
    } else {
      currentEvent.posts.push({
        ids: ['new_' + Math.random().toString(36).slice(2, 8)],
        platforms: plats,
        scheduled_for_utc: chosen.toISOString(),
        images: [...photosState],
        image_grad: currentEvent.flyer_grad,
        caption: $('#e-cap').value,
        status: 'pending',
        result: '',
      });
    }
    closeEdit();
    renderPosts(false);
  }
  toast(isNew ? 'Post added to the queue' : 'Saved & scheduled');
}
function showErr(msg) { const e = $('#e-err'); e.textContent = msg; e.classList.add('show'); }

/* ---------- view switching ---------- */
function showView(id) { $$('.view').forEach(v => v.classList.remove('active')); $('#' + id).classList.add('active'); window.scrollTo(0, 0); }

let toastT;
function toast(msg) {
  $('#toast-msg').textContent = msg;
  const t = $('#toast'); t.classList.add('show');
  clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove('show'), 2600);
}

/* ---------- who am I (Cloudflare Access identity) ---------- */
async function loadIdentity() {
  try {
    const res = await fetch('/cdn-cgi/access/get-identity', { cache: 'no-store' });
    if (!res.ok) return;
    const me = await res.json();
    const name = (me.name || me.email || '').split('@')[0];
    if (name) {
      $('.who').lastChild.textContent = name.charAt(0).toUpperCase() + name.slice(1);
      $('.avatar').textContent = name.charAt(0).toUpperCase();
    }
  } catch { /* not behind Access (demo) — keep default */ }
}

/* ---------- wire up ---------- */
$('#seg').addEventListener('click', e => {
  const b = e.target.closest('button[data-view]'); if (!b) return;
  currentView = b.dataset.view;
  $$('#seg button').forEach(x => x.classList.toggle('active', x === b));
  renderList(); showView('v-list');
});
$('#btn-back').addEventListener('click', () => { renderList(); showView('v-list'); });
$('#btn-new').addEventListener('click', () => toast('New events come from your Monday board — schedule posts for one and its card appears here'));
$('#e-close').addEventListener('click', closeEdit);
$('#e-cancel').addEventListener('click', closeEdit);
$('#e-save').addEventListener('click', saveEdit);
$('#e-delete').addEventListener('click', async () => {
  if (!editingPost) return;
  if (FALLBACK) return showErr('Live connection is down — changes can’t be saved right now. Try again later.');
  const post = editingPost;
  try {
    if (LIVE) {
      await api('/api/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ op: 'delete', ids: post.ids }) });
      await refreshData();
    } else {
      currentEvent.posts = currentEvent.posts.filter(p => p !== post);
    }
    closeEdit();
    if (currentEvent) { renderPosts(false); } else { renderList(); showView('v-list'); }
    toast('Post deleted');
  } catch (err) {
    showErr(err.message);
  }
});
$('#e-cap').addEventListener('input', updateChars);
$('#e-file').addEventListener('change', onFilePicked);
$$('.tog').forEach(t => t.addEventListener('click', () => t.classList.toggle('on')));
$('#overlay').addEventListener('click', e => { if (e.target.id === 'overlay') closeEdit(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape' && $('#overlay').classList.contains('active')) closeEdit(); });

/* ---------- boot ---------- */
(async function boot() {
  let liveError = null;
  try {
    const live = await api('/api/events?ts=' + Date.now());
    if (live.mode === 'live') { LIVE = true; DATA = live; }
  } catch (e) { liveError = e; /* no API here, or the API is failing */ }
  if (!LIVE) {
    // A 404 means there's no API at all (local prototype) → quiet demo mode.
    // Anything else means the deployed API is BROKEN — say so, loudly, instead
    // of letting an old snapshot pass for live data.
    FALLBACK = !!liveError && liveError.status !== 404;
    try {
      DATA = await (await fetch('events.json?ts=' + Date.now(), { cache: 'no-store' })).json();
    } catch {
      $('#eventlist').innerHTML = `<div class="empty"><div class="big">⚠️</div><h3>Couldn't load events</h3>
        <p>The events feed isn't reachable. Refresh the page, or check that the API is deployed.</p></div>`;
      return;
    }
    if (FALLBACK) {
      DATA.events = DATA.events.filter(e => e.source !== 'sample');
      const snapDate = DATA.generated_at
        ? new Date(DATA.generated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : '';
      $('#livebar').innerHTML = `⚠️ <span><b>Live connection is down</b> — showing an old saved copy${snapDate ? ` from ${snapDate}` : ''}.
        New posts and edits won't show, and <b>saving is off</b> until it's fixed.
        <span class="livebar-why">${esc(liveError.message)}</span></span>`;
      $('#livebar').style.display = '';
    }
  }
  loadIdentity();
  renderList();
})();
