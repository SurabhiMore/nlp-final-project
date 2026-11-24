// The live page: talk to an exhibit and watch it answer.
//
// The flow is the plain page's (main.js): hold the talk button and speak, or tap it
// to start and tap again to send; /transcribe shows what it heard so the visitor can
// fix it; /ask answers with its sources; /speak reads each sentence in the exhibit's
// voice. Here /speak also returns when each sound and word is spoken, so the exhibit's
// mouth and the subtitles follow the voice, and the stage reacts to the answer:
// a cited painting paints itself, a cited letter writes itself, a question after the
// exhibit's time ages the scene, the T. rex's camera moves to the part it talks about.
//
// URL options: ?persona=t-rex picks the exhibit (use this in QR codes),
//              ?mode=neutral asks the plain museum guide instead,
//              ?session=P1 labels a user test in the server log.

import { Sound, decodeTiming, mouthUpdate, wordTime } from './sound.js';
import {
  clearWarp, drawWarp, initScenes, paintingLabelAt, renderFrame, resizeScenes, scenes, tr, trChomp, trFocus,
  trRegionAt, trRoar, trSnort, trWake, vg, vgBlink, vgHidePainting, vgIntro, vgNight, vgPaint, vgScan, vgSepia,
} from './scenes.js';
import { clamp, follow, lerp, runTweens, sceneOf, smooth, state, tween } from './state.js';

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(window.location.search);
state.mode = params.get('mode') === 'neutral' ? 'neutral' : 'persona';
const testLabel = (params.get('session') || '').trim();
const isTest = /^[A-Za-z0-9_-]{1,32}$/.test(testLabel);
const sessionId = isTest ? testLabel
  : (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2);
const isIOS = /iP(hone|ad|od)/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
const STATUS_LABELS = { not_in_sources: 'Not in my sources', outside_time: 'Outside my time', declined: 'Off topic' };
const SCENE_CREDIT = { vg: 'Self-Portrait, 1887, Art Institute of Chicago' };

const el = {};
for (const id of ['stage', 'plate-name', 'plate-meta', 'pill', 'pill-text', 'fs', 'subs', 'letter', 'art-label', 'callout', 'callout-big',
  'callout-cap', 'stamp', 'stamp-meta', 'pages', 'chip', 'hint', 'heard', 'heard-text', 'heard-warning', 'heard-send', 'heard-redo',
  'orb', 'orb-label', 'counter', 'yr', 'cap', 'cover', 'cover-title', 'cover-text', 'cover-btn', 'fallback', 'exhibits', 'text-form',
  'text-question', 'status', 'stop', 'conversation', 'turn-template', 'session-note']) {
  el[id.replace(/-([a-z])/g, (m, c) => c.toUpperCase())] = $(id);
}

let manifest = {};
const turnsBy = new Map();   // exhibit id -> its answer cards, kept when switching exhibits
const met = new Set();       // exhibits whose opening has played
let cues = [];
let running = true;

// ------------------------------------------------------------------ helpers
const exhibit = (id) => state.exhibits.find((e) => e.id === id);
const shortPeriod = (e) => { const s = (e.time_period || '').split(',')[0].trim(); return s.charAt(0).toUpperCase() + s.slice(1); };
const safeUrl = (url) => (/^https?:\/\//i.test(url || '') ? url : null);
const normalizeUrl = (url) => (url || '').split(/[?#]/)[0].replace(/\/+$/, '');

function setStatus(message, isError) {
  el.status.textContent = message || '';
  el.status.classList.toggle('error', Boolean(isError));
}
function setPill(text, mode) { el.pillText.textContent = text; el.pill.dataset.state = mode; }
function setControls() {
  el.textForm.querySelector('button').disabled = state.busy;
  el.heardSend.disabled = state.busy;
  for (const b of el.exhibits.querySelectorAll('button')) b.disabled = state.busy;
}

// ------------------------------------------------------------------ exhibits and the stage
async function loadExhibits() {
  try {
    state.exhibits = await (await fetch('/personas')).json();
    // newest first, so the buttons read like the time travel between them
    const end = (e) => (e.years && e.years[1] != null ? e.years[1] : 0);
    state.exhibits.sort((a, b) => end(b) - end(a));
  } catch (e) {
    setStatus('Could not load the exhibits. Is the server running?', true);
    return;
  }
  try { manifest = await (await fetch('/static/live/art/manifest.json')).json(); } catch (e) { manifest = {}; }
  const wanted = params.get('persona');
  const first = state.exhibits.some((e) => e.id === wanted) ? wanted : (state.exhibits[0] || {}).id;
  el.exhibits.innerHTML = '';
  for (const e of state.exhibits) {
    const b = document.createElement('button');
    b.type = 'button'; b.dataset.id = e.id;
    b.innerHTML = '<b></b><span></span>';
    b.querySelector('b').textContent = e.name;
    b.querySelector('span').textContent = shortPeriod(e);
    b.addEventListener('click', () => travel(e.id));
    el.exhibits.appendChild(b);
  }
  if (first) { applyExhibit(first); showCover(first); }
}

function applyExhibit(id) {
  const e = exhibit(id);
  if (!e) return;
  const leaving = state.current;
  if (leaving) turnsBy.set(leaving, Array.from(el.conversation.children));
  state.current = id;
  document.body.dataset.exhibit = sceneOf(id) || 'other';
  el.plateName.textContent = state.mode === 'neutral' ? 'Museum guide: ' + e.name : e.name;
  el.plateMeta.textContent = [shortPeriod(e), SCENE_CREDIT[sceneOf(id)]].filter(Boolean).join(' · ');
  for (const b of el.exhibits.querySelectorAll('button')) b.setAttribute('aria-pressed', String(b.dataset.id === id));
  el.textQuestion.placeholder = 'Or type a question for ' + e.name.split(' ')[0] + '…';
  el.conversation.replaceChildren(...(turnsBy.get(id) || []));
  const url = new URL(window.location.href);
  url.searchParams.set('persona', id);
  window.history.replaceState(null, '', url);
}

function showCover(id) {
  if (met.has(id)) return;
  const e = exhibit(id), s = sceneOf(id);
  if (s === 'vg') { el.coverTitle.textContent = 'Step into the painting'; el.coverText.textContent = "Vincent's self-portrait, in front of the wheat field he wrote about to Theo."; el.coverBtn.textContent = 'Enter with sound'; }
  else if (s === 'tr') { el.coverTitle.textContent = 'A fossil in the dark'; el.coverText.textContent = 'The skeleton on its plinth, as you would find it in the museum.'; el.coverBtn.textContent = 'Wake it up'; }
  else { el.coverTitle.textContent = 'Meet ' + e.name; el.coverText.textContent = 'Ask out loud, and the exhibit answers in its own voice.'; el.coverBtn.textContent = 'Start with sound'; }
  document.body.dataset.cover = s || 'other';
  el.cover.hidden = false;
}

function greetingFor(e) {
  return state.mode === 'neutral' ? 'Ask the museum guide anything about ' + e.name + '.' : e.greeting;
}

// The opening: Vincent's portrait comes closer, the T. rex wakes and roars; then a greeting.
async function meet(id, { greet = true } = {}) {
  if (met.has(id)) return;
  met.add(id);
  el.cover.hidden = true;
  Sound.unlock();
  Sound.ambience(sceneOf(id));
  const e = exhibit(id);
  state.busy = true; setControls();
  try {
    if (scenes.ok && sceneOf(id) === 'vg') await vgIntro();
    if (scenes.ok && sceneOf(id) === 'tr' && tr.ready) {
      setPill('Waking up', 'thinking');
      await trWake();
      if (greet) await roar(id);
    }
  } finally {
    state.busy = false; setControls(); setPill('Ready', 'idle');
  }
  const asked = askCount;
  if (greet && state.current === id) await speak(id, splitSentences(greetingFor(e)), 'en');
  if (sceneOf(id) === 'tr' && state.current === id && askCount === asked) el.hint.hidden = false;
}

async function roar(id) {
  const e = exhibit(id);
  if (!e || !(e.sounds || []).includes('roar')) return;
  state.speaker = id;
  setPill('Roaring', 'speaking');
  const body = scenes.ok ? trRoar() : null;
  await Sound.playUrl(`/sound/${id}/roar`, { voice: true, owner: id });
  if (body) await body;
  if (state.speaker === id) state.speaker = null;
  setPill('Ready', 'idle');
}

// ------------------------------------------------------------------ time travel between exhibits
function yearText(ago, now) {
  const year = now - ago;
  if (year >= 1) return String(Math.round(year));
  if (ago < 12000) return Math.round(ago - now + 1).toLocaleString('en-US') + ' BC';
  if (ago < 1e6) return Math.round(ago / 1000).toLocaleString('en-US') + ',000 years ago';
  return (Math.round(ago / 1e5) / 10).toLocaleString('en-US', { maximumFractionDigits: 1 }) + ' million years ago';
}

async function travel(to) {
  if (state.busy || to === state.current || !exhibit(to)) return;
  Sound.unlock();
  stopSpeaking(); clearEffects(); hideHeard();
  el.cover.hidden = true;
  state.busy = true; setControls();
  const now = new Date().getFullYear();
  const yearOf = (e) => (e && e.years && e.years[1] != null ? e.years[1] : now);
  const a = Math.max(1, now - yearOf(exhibit(state.current))), b = Math.max(1, now - yearOf(exhibit(to)));
  const back = b > a;
  el.cap.textContent = back ? 'Travelling back in time' : 'Travelling forward in time';
  el.counter.hidden = false;
  Sound.sweep(2.4);
  let swapped = false;
  await tween(2600, (k) => {
    if (scenes.ok) drawWarp(k, back);
    const p = smooth(clamp((k - 0.1) / 0.8, 0, 1));
    el.yr.textContent = yearText(Math.pow(10, lerp(Math.log10(a), Math.log10(b), p)), now);
    if (!swapped && k >= 0.5) { swapped = true; applyExhibit(to); }
  });
  clearWarp();
  el.counter.hidden = true;
  state.busy = false; setControls();
  if (met.has(to)) { Sound.ambience(sceneOf(to)); if (sceneOf(to) === 'tr') el.hint.hidden = false; }
  else showCover(to);
}

// ------------------------------------------------------------------ speaking
let playbackId = 0;
let subWords = [];

function splitSentences(text) {
  return (text.match(/[^.!?]+[.!?]+["')\]]*|[^.!?]+$/g) || [text]).map((s) => s.trim()).filter(Boolean);
}

function stopSpeaking() {
  playbackId += 1;
  Sound.stopVoice();
  state.speaker = null;
  el.stop.hidden = true;
  el.subs.hidden = true;
  cues = [];
}

async function fetchClip(id, text, lang) {
  const body = new FormData();
  body.append('persona', id);
  body.append('text', text);
  if (lang) body.append('lang', lang);
  body.append('timing', 'true');
  const response = await fetch('/speak', { method: 'POST', body });
  if (response.status === 204) return null;
  if (!response.ok) throw new Error('speech failed');
  const timing = decodeTiming(response.headers.get('X-Echoes-Timing'));
  const buf = await Sound.decode(await response.arrayBuffer());
  return { buf, timing, text };
}

// Speak the sentences one after another, making the next while the current one plays,
// then play the exhibit's sound (the T. rex's roar) if the answer has one.
async function speak(id, sentences, lang, opts = {}) {
  stopSpeaking();
  const run = playbackId;
  Sound.unlock();
  if (!sentences.length && !opts.sound) return;
  el.stop.hidden = false;
  try {
    let next = sentences.length ? fetchClip(id, sentences[0], lang) : null;
    const sound = opts.sound && opts.sound.url ? Sound.loadUrl(opts.sound.url).catch(() => null) : null;
    for (let i = 0; i < sentences.length; i++) {
      const clip = await next;
      if (run !== playbackId) return;
      next = i + 1 < sentences.length ? fetchClip(id, sentences[i + 1], lang) : null;
      if (!clip) continue;
      if (opts.onFirstAudio && i === 0) opts.onFirstAudio();
      state.speaker = id;
      setPill('Speaking', 'speaking'); el.orb.dataset.state = 'speaking';
      showSubs(clip);
      planCues(clip, opts.fx);
      await Sound.playBuffer(clip.buf, { voice: true, owner: id, timing: clip.timing });
      if (run !== playbackId) return;
    }
    if (sound) {
      const buf = await sound;
      if (run !== playbackId || !buf) return;
      el.subs.hidden = true;
      state.speaker = id;
      const body = scenes.ok && sceneOf(id) === 'tr' && opts.sound.name === 'roar' ? trRoar() : null;
      await Sound.playBuffer(buf, { voice: true, owner: id });
      if (body) await body;
    }
  } catch (error) {
    setStatus('The answer is shown below, but the voice could not be played.', true);
  } finally {
    if (run === playbackId) {
      state.speaker = null;
      el.stop.hidden = true; el.subs.hidden = true;
      setPill('Ready', 'idle'); el.orb.dataset.state = 'idle';
    }
  }
}

function showSubs(clip) {
  el.subs.replaceChildren();
  let words = clip.timing && clip.timing.words && clip.timing.words.length ? clip.timing.words : null;
  if (!words) {
    // no word timings (not English): spread the words over the clip
    const parts = clip.text.split(/\s+/).filter(Boolean), d = clip.buf.duration;
    words = parts.map((w, i) => [w, (i / parts.length) * d, ((i + 1) / parts.length) * d, 1]);
  }
  subWords = words.map((w, i) => {
    const s = document.createElement('span');
    const next = words[i + 1];
    s.className = 'w';
    s.textContent = w[0] + (w[3] && next && !/^[.,!?;:]/.test(next[0]) ? ' ' : '');
    el.subs.appendChild(s);
    return { el: s, start: w[1], end: w[2] };
  });
  el.subs.hidden = false;
}
function updateSubs() {
  if (el.subs.hidden || !Sound.voice) return;
  const t = Sound.voiceTime();
  for (const w of subWords) { w.el.classList.toggle('on', t >= w.start); w.el.classList.toggle('now', t >= w.start && t < w.end + 0.05); }
}

// ------------------------------------------------------------------ what the stage does with an answer
const NUM = '\\d[\\d,]*(?:\\.\\d+)?';
const UNIT = '(?:newtons|newton|N|metres|meters|metre|meter|m|feet|ft|kilometres|kilometers|km|tonnes|tons|tonne|ton|kg|kilograms|pounds|lbs|million years|years|teeth|versions|paintings|letters|bones)';
const UNIT_RE = new RegExp(`(${NUM}(?:\\s*(?:to|-)\\s*${NUM})?\\s*${UNIT})(?![\\w])`, 'i');
const WORDNUM = { two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10, eleven: 11, twelve: 12 };
const WORDNUM_RE = /\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(versions|paintings|letters|teeth|fingers|claws|brothers|sisters|times)\b/i;
const YEAR_RE = /\b(1[5-9]\d\d)\b/;

// The number worth showing big in this sentence, and the word where it starts.
function calloutFor(text) {
  let m = text.match(UNIT_RE);
  if (m) return { big: m[1].replace(/\s+/g, ' '), first: m[1].split(/\s/)[0] };
  m = text.match(WORDNUM_RE);
  if (m) return { big: WORDNUM[m[1].toLowerCase()] + ' ' + m[2].toLowerCase(), first: m[1] };
  m = text.match(YEAR_RE);
  if (m) return { big: m[1], first: m[1] };
  return null;
}

function planEffects(id, data) {
  const s = sceneOf(id), fx = { scene: s };
  if (state.mode !== 'persona') return fx;
  const answer = data.answer || '', both = ((data.question || '') + ' ' + answer).toLowerCase();
  if (data.status === 'outside_time') fx.timewall = true;
  if (s === 'vg') {
    if (data.status === 'not_in_sources') fx.pages = true;
    if (data.status === 'declined') fx.away = true;
    if (/\bAI\b|artificial intelligence/.test(answer)) fx.scan = true;
    if (/\b(starry|stars?|night)\b/i.test(answer)) fx.night = true;
    for (const c of data.citations || []) {
      const art = manifest[normalizeUrl(c.url)];
      if (art && !art.self && !art.backdrop && !fx.painting) fx.painting = art;
      if (!fx.letter && /letter/i.test(c.source || '')) fx.letter = c;
    }
  }
  if (s === 'tr') {
    if (data.status === 'declined') fx.snort = true;
    if (/\b(arms?|forelimbs?|fingers?|claws?)\b/.test(both)) fx.focus = 'arms';
    else if (/\b(bite|bit|jaws?|teeth|tooth|skull|mouth)\b/.test(both)) { fx.focus = 'head'; fx.chomp = true; }
    else if (/\b(scales?|feathers?|skin)\b/.test(both)) fx.focus = 'body';
    else if (/\btails?\b/.test(both)) fx.focus = 'tail';
    else if (/\b(legs?|run|ran|running|fast|speed|walk|feet|foot)\b/.test(both)) fx.focus = 'legs';
  }
  fx.calloutShown = false;
  return fx;
}

function startEffects(id, fx) {
  if (!fx.scene) return;
  const e = exhibit(id);
  if (fx.timewall) {
    if (fx.scene === 'vg') { vg.mode = 'away'; vgSepia(true); }
    el.stampMeta.textContent = e.name + ' · ' + shortPeriod(e);
    setTimeout(() => { el.stamp.hidden = false; }, 500);
  }
  if (fx.pages) {
    vg.mode = 'searching';
    el.pages.classList.remove('run', 'done'); el.pages.hidden = false;
    void el.pages.offsetWidth;
    el.pages.classList.add('run');
    setTimeout(() => { el.pages.classList.add('done'); vg.mode = 'idle'; }, state.reduce ? 200 : 1700);
  }
  if (fx.away) { vg.mode = 'away'; setTimeout(() => { if (vg.mode === 'away') vg.mode = 'idle'; }, 1400); }
  if (fx.scan) vgScan();
  if (fx.painting) {
    vgPaint(fx.painting).then(() => {
      el.artLabel.replaceChildren();
      const b = document.createElement('b'); b.textContent = fx.painting.title;
      el.artLabel.append(b, ', ' + fx.painting.date, document.createElement('br'), fx.painting.museum + ' · ' + fx.painting.licence);
      el.artLabel.hidden = false;
    });
  }
  if (fx.letter && state.W / state.H > 1.1) setTimeout(() => { if (fx.live) showLetter(fx.letter); }, 1600);
  if (fx.snort) trSnort(exhibit(id).sounds && exhibit(id).sounds.includes('roar') ? `/sound/${id}/roar` : null);
  if (fx.focus) trFocus(fx.focus);
  fx.live = true;
}

function endEffects(id, fx) {
  fx.live = false;
  if (fx.letter && el.letter.hidden && state.current === id) showLetter(fx.letter);
  if (fx.focus) setTimeout(() => trFocus(null), 1400);
  if (fx.timewall && fx.scene === 'vg') vg.mode = 'idle';
}

// Things timed to a word: night falls on "starry", the jaws snap on "bite", a number appears as it is said.
function planCues(clip, fx) {
  cues = [];
  if (!fx) return;
  const at = (pattern, fallback) => {
    const t = wordTime(clip.timing, pattern);
    if (t != null) return t;
    const m = clip.text.search(pattern);
    return m < 0 ? fallback : (m / Math.max(clip.text.length, 1)) * clip.buf.duration;
  };
  if (fx.night && !fx.nightDone) {
    const t = at(/starr|\bstars?\b|night/i, null);
    if (t != null) { fx.nightDone = true; cues.push({ t, fn: () => vgNight(true) }); }
  }
  if (fx.chomp && !fx.chompDone) {
    const t = at(/^(bite|bit|jaws?|teeth|tooth)\b/i, null);
    if (t != null) { fx.chompDone = true; cues.push({ t, fn: () => trChomp() }); }
  }
  if (!fx.calloutShown) {
    const c = calloutFor(clip.text);
    if (c) {
      fx.calloutShown = true;
      const escaped = c.first.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      cues.push({ t: at(new RegExp('^' + escaped, 'i'), 0.3), fn: () => showCallout(c.big) });
    }
  }
}
function runCues() {
  if (!cues.length || !Sound.voice) return;
  const t = Sound.voiceTime();
  cues = cues.filter((c) => { if (t >= c.t) { c.fn(); return false; } return true; });
}

function showLetter(cite) {
  el.letter.replaceChildren();
  const body = document.createElement('div');
  const words = (cite.quote || cite.snippet || '').split(/\s+/).filter(Boolean).map((w) => {
    const s = document.createElement('span'); s.className = 'w'; s.textContent = w + ' '; body.appendChild(s); return s;
  });
  const src = document.createElement('div');
  src.className = 'src';
  src.textContent = 'From his letters, as cited: ' + cite.source + '. ' + (cite.licence || '') + '.';
  el.letter.append(body, src);
  el.letter.hidden = false;
  words.forEach((s, i) => setTimeout(() => s.classList.add('on'), (state.reduce ? 0 : 140) * i + 250));
}
function showCallout(big) {
  el.calloutBig.textContent = big;
  el.calloutCap.textContent = '';
  el.callout.hidden = false;
  el.callout.style.animation = 'none'; void el.callout.offsetWidth; el.callout.style.animation = '';
  clearTimeout(el.callout._t);
  el.callout._t = setTimeout(() => { el.callout.hidden = true; }, 3600);
}

function clearEffects() {
  for (const k of ['letter', 'artLabel', 'chip', 'hint', 'callout', 'stamp', 'pages']) el[k].hidden = true;
  el.pages.classList.remove('run', 'done');
  if (scenes.ok) {
    vgHidePainting();
    if (vg.ready && (vg.u.uNight.value > 0.001)) vgNight(false);
    if (vg.ready && (vg.u.uSepia.value > 0.001)) vgSepia(false);
    vg.mode = 'idle';
    trFocus(null);
  }
}

// ------------------------------------------------------------------ the conversation
function addTurn(id, question) {
  const node = el.turnTemplate.content.firstElementChild.cloneNode(true);
  node.dataset.state = 'loading';
  node.querySelector('.q').textContent = question ? 'You asked: ' + question : 'Listening…';
  node.querySelector('.a').innerHTML = '<span class="loading"><span></span><span></span><span></span></span> Thinking…';
  el.conversation.prepend(node);
  return node;
}
function fillTurn(node, data, askedAt) {
  node.dataset.state = STATUS_LABELS[data.status] ? 'low' : 'ok';
  node.querySelector('.q').textContent = 'You asked: ' + data.question;
  node.querySelector('.a').textContent = data.answer;
  const badge = node.querySelector('.badge');
  if (STATUS_LABELS[data.status]) { badge.textContent = STATUS_LABELS[data.status]; badge.hidden = false; }
  const list = node.querySelector('.sources');
  for (const c of data.citations || []) {
    const li = document.createElement('li');
    const url = safeUrl(c.url);
    const name = document.createElement(url ? 'a' : 'span');
    name.className = 'src'; name.textContent = c.source || c.id;
    if (url) { name.href = url; name.target = '_blank'; name.rel = 'noopener'; }
    const licence = document.createElement('span'); licence.className = 'lic'; licence.textContent = (c.licence || '').split(' (')[0];
    const quote = document.createElement('span'); quote.className = 'snip'; quote.textContent = '“' + (c.quote || c.snippet || '').trim() + '”';
    li.append(name, licence, quote);
    list.appendChild(li);
  }
  list.hidden = !list.children.length;
  const note = node.querySelector('.note');
  const parts = [];
  if (data.sound && data.sound.note) parts.push('Sound: ' + data.sound.note + '.');
  parts.push('Answer shown after ' + ((performance.now() - askedAt) / 1000).toFixed(1) + ' s');
  note.textContent = parts.join(' ');
}
function failTurn(node, message) {
  node.dataset.state = 'error';
  node.querySelector('.a').textContent = message || 'Something went wrong.';
  const badge = node.querySelector('.badge'); badge.textContent = 'Request failed'; badge.hidden = false;
}

// ------------------------------------------------------------------ asking
let askCount = 0;
async function ask(fields) {
  const id = state.current;
  if (state.busy || !id || !fields.text) return;
  askCount += 1;
  Sound.unlock();
  stopSpeaking(); clearEffects(); hideHeard();
  if (!met.has(id)) await meet(id, { greet: false });
  state.busy = true; setControls(); setStatus('');
  const askedAt = performance.now();
  const node = addTurn(id, fields.text);
  setPill('Thinking', 'thinking'); el.orb.dataset.state = 'thinking';
  if (sceneOf(id) === 'vg') vg.mode = 'thinking';
  if (sceneOf(id) === 'tr') tr.thinking = 1;
  const body = new FormData();
  body.append('persona', id);
  body.append('mode', state.mode);
  body.append('session_id', sessionId);
  body.append('text', fields.text);
  if (fields.heard) {
    body.append('heard', fields.heard);
    if (fields.sttMs != null) body.append('stt_ms', fields.sttMs);
  }
  try {
    const response = await fetch('/ask', { method: 'POST', body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Something went wrong.');
    vg.mode = 'idle'; tr.thinking = 0;
    fillTurn(node, data, askedAt);
    const fx = planEffects(id, data);
    startEffects(id, fx);
    state.busy = false; setControls();
    speak(id, data.sentences || [], data.detected_language, {
      fx,
      sound: data.sound,
      onFirstAudio: () => { node.querySelector('.note').textContent += ', voice started after ' + ((performance.now() - askedAt) / 1000).toFixed(1) + ' s'; },
    }).then(() => endEffects(id, fx));
  } catch (error) {
    vg.mode = 'idle'; tr.thinking = 0;
    failTurn(node, error.message);
    state.busy = false; setControls();
    setPill('Ready', 'idle'); el.orb.dataset.state = 'idle';
  }
}

// ------------------------------------------------------------------ what it heard
let pending = null;   // what /transcribe heard, until it is sent or dropped

function showHeard(data) {
  pending = { heard: data.text, sttMs: data.timings && data.timings.stt_ms };
  el.heardText.value = data.text;
  el.heardWarning.hidden = !data.low_confidence;
  el.heard.classList.toggle('unsure', Boolean(data.low_confidence));
  el.heard.hidden = false;
  el.heardSend.focus();
  setPill('Check what I heard', 'idle');
}
function hideHeard() { pending = null; el.heard.hidden = true; el.heardText.value = ''; }
function sendHeard() {
  const question = el.heardText.value.trim();
  if (!pending || state.busy) return;
  if (!question) { setStatus('Type your question, or record it again.', true); return; }
  const sent = { text: question, heard: pending.heard, sttMs: pending.sttMs };
  hideHeard();
  ask(sent);
}

async function transcribe(audio, filename) {
  const id = state.current;
  hideHeard();
  state.busy = true; setControls();
  setPill('Checking what I heard', 'thinking'); el.orb.dataset.state = 'thinking';
  const body = new FormData();
  body.append('persona', id);
  body.append('audio', audio, filename);
  try {
    const response = await fetch('/transcribe', { method: 'POST', body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Something went wrong.');
    state.busy = false; setControls();
    el.orb.dataset.state = 'idle';
    if (!data.text) { setPill('Ready', 'idle'); setStatus('We could not hear a question. Please try again, or type it.', true); return; }
    showHeard(data);
  } catch (error) {
    state.busy = false; setControls();
    setPill('Ready', 'idle'); el.orb.dataset.state = 'idle';
    setStatus(error.message || 'Something went wrong.', true);
  }
}

// ------------------------------------------------------------------ recording
let recorder = null, chunks = [], recordStart = 0, pressStart = 0, wanted = false, tapMode = false, micMeter = null;

function pickMimeType() {
  if (!window.MediaRecorder) return null;
  return ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus'].find((t) => MediaRecorder.isTypeSupported(t)) || '';
}
function setListening(on) {
  el.orb.dataset.state = on ? 'listening' : 'idle';
  el.orbLabel.textContent = on ? (tapMode ? 'Listening… tap to send' : 'Listening… let go to send') : 'Hold to talk, or tap';
  if (sceneOf(state.current) === 'vg') vg.mode = on ? 'listening' : 'idle';
  if (sceneOf(state.current) === 'tr') tr.listening = on ? 1 : 0;
  if (on) setPill('Listening', 'listening');
}
// How loud the visitor is, so the painting ripples with their voice. Skipped on iPhones,
// where reading the microphone this way can change where the sound plays afterwards.
function startMicMeter(stream) {
  if (isIOS) return null;
  try {
    const Context = window.AudioContext || window.webkitAudioContext;
    const ctx = new Context();
    const an = ctx.createAnalyser(); an.fftSize = 512;
    ctx.createMediaStreamSource(stream).connect(an);
    return { ctx, an, buf: new Float32Array(an.fftSize) };
  } catch (e) {
    return null;
  }
}

async function startRecording() {
  if (state.busy || recorder) return;
  Sound.unlock(); stopSpeaking(); hideHeard(); setStatus('');
  if (window.isSecureContext === false) { setStatus('The microphone only works on a secure (https) link. Please type your question.', true); return; }
  const mimeType = pickMimeType();
  if (mimeType === null || !navigator.mediaDevices) { setStatus('This browser cannot record audio. Please type your question.', true); return; }
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (error) {
    setStatus('Microphone access was blocked. Allow it, or type your question.', true);
    return;
  }
  if (!wanted && !tapMode) {
    // the button was let go while the browser asked for the microphone
    stream.getTracks().forEach((track) => track.stop());
    setStatus('The microphone is ready. Now hold the button while you speak, or tap it.');
    return;
  }
  chunks = [];
  recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
  recorder.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data); };
  recorder.onstop = () => {
    stream.getTracks().forEach((track) => track.stop());
    if (micMeter) { micMeter.ctx.close().catch(() => {}); micMeter = null; }
    const type = recorder.mimeType || mimeType || 'audio/webm';
    const heldFor = performance.now() - recordStart;
    recorder = null; tapMode = false;
    setListening(false);
    vg.listenLevel = 0;
    if (heldFor < 500 || !chunks.length) { setPill('Ready', 'idle'); setStatus('Hold the button while you speak, or tap it to start and again to send.'); return; }
    const ext = type.includes('mp4') ? 'mp4' : type.includes('ogg') ? 'ogg' : 'webm';
    transcribe(new Blob(chunks, { type }), 'question.' + ext);
  };
  recordStart = performance.now();
  recorder.start();
  micMeter = startMicMeter(stream);
  setListening(true);
}
function stopRecording() {
  wanted = false;
  if (recorder && recorder.state === 'recording') recorder.stop();
}

el.orb.addEventListener('pointerdown', (event) => {
  event.preventDefault();
  if (recorder) { if (tapMode) stopRecording(); return; }
  if (state.busy) return;
  if (!met.has(state.current)) { meet(state.current); return; }
  wanted = true; tapMode = false; pressStart = performance.now();
  if (el.orb.setPointerCapture) el.orb.setPointerCapture(event.pointerId);
  startRecording();
});
el.orb.addEventListener('pointerup', () => {
  if (!wanted) return;
  if (performance.now() - pressStart < 350) {
    // a quick tap: keep listening until the next tap
    tapMode = true; wanted = false;
    if (recorder) setListening(true);
  } else stopRecording();
});
el.orb.addEventListener('pointercancel', () => { if (!tapMode) stopRecording(); });
el.orb.addEventListener('keydown', (event) => {
  if ((event.key === ' ' || event.key === 'Enter') && !event.repeat) { event.preventDefault(); if (recorder) return; wanted = true; startRecording(); }
});
el.orb.addEventListener('keyup', (event) => { if (event.key === ' ' || event.key === 'Enter') stopRecording(); });
el.orb.addEventListener('contextmenu', (event) => event.preventDefault());

el.textForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const question = el.textQuestion.value.trim();
  if (!question) return;
  el.textQuestion.value = '';
  ask({ text: question });
});
el.heardSend.addEventListener('click', () => { Sound.unlock(); sendHeard(); });
el.heardText.addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); Sound.unlock(); sendHeard(); } });
el.heardRedo.addEventListener('click', () => { hideHeard(); setPill('Ready', 'idle'); setStatus('Hold the button and ask again, or tap it.'); el.orb.focus(); });
el.stop.addEventListener('click', () => { stopSpeaking(); setPill('Ready', 'idle'); el.orb.dataset.state = 'idle'; });
el.coverBtn.addEventListener('click', () => meet(state.current));
el.fs.addEventListener('click', async () => {
  try { if (document.fullscreenElement) await document.exitFullscreen(); else await el.stage.requestFullscreen(); }
  catch (e) { setStatus('Full screen is not available in this browser.'); }
});

// Taps on the exhibit itself: Vincent blinks at you; the T. rex offers a question about the part you touched.
let down = null;
el.stage.addEventListener('pointerdown', (e) => { down = { x: e.clientX, y: e.clientY, t: performance.now() }; });
el.stage.addEventListener('pointerup', (e) => {
  if (!down || e.target.closest('button, textarea, input, a, .letter, .heard, .chip')) { down = null; return; }
  const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y), quick = performance.now() - down.t < 450;
  down = null;
  if (moved > 12 || !quick || !scenes.ok) return;
  const r = el.stage.getBoundingClientRect(), px = e.clientX - r.left, py = e.clientY - r.top;
  if (sceneOf(state.current) === 'vg') { vgBlink(); return; }
  if (sceneOf(state.current) !== 'tr' || state.busy) return;
  const question = trRegionAt(px, py);
  if (!question) return;
  const ex = exhibit(state.current);
  if (ex && (ex.sounds || []).includes('roar')) Sound.playUrl(`/sound/${state.current}/roar`, { voice: false, gain: 0.45, offset: 0.15, duration: 0.9, rate: 0.82 });
  el.chip.replaceChildren();
  const k = document.createElement('span'); k.className = 'k'; k.textContent = 'Ask the T. rex';
  const q = document.createElement('button'); q.type = 'button'; q.className = 'q'; q.textContent = '“' + question + '”';
  q.addEventListener('click', () => { el.chip.hidden = true; ask({ text: question }); });
  el.chip.append(k, q);
  el.chip.style.left = clamp(px, 130, state.W - 130) + 'px';
  el.chip.style.top = Math.max(py, 120) + 'px';
  el.chip.hidden = false; el.hint.hidden = true;
  clearTimeout(el.chip._t); el.chip._t = setTimeout(() => { el.chip.hidden = true; }, 5000);
});

// ------------------------------------------------------------------ the loop
const p = state.pointer;
el.stage.addEventListener('pointermove', (e) => {
  const r = el.stage.getBoundingClientRect();
  p.tx = clamp(((e.clientX - r.left) / r.width) * 2 - 1, -1, 1);
  p.ty = clamp(-(((e.clientY - r.top) / r.height) * 2 - 1), -1, 1);
  p.moved = performance.now();
});
el.stage.addEventListener('pointerleave', () => { p.tx = 0; p.ty = 0; });

function resize() {
  const r = el.stage.getBoundingClientRect();
  state.W = Math.max(1, r.width); state.H = Math.max(1, r.height);
  resizeScenes();
}

let last = performance.now();
function frame(now) {
  if (!running) return;
  requestAnimationFrame(frame);
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  p.x = follow(p.x, p.tx, 5, dt); p.y = follow(p.y, p.ty, 5, dt);
  runTweens(now);
  const level = Sound.tick();
  mouthUpdate(dt);
  runCues();
  Sound.critters(dt);
  if (micMeter) {
    micMeter.an.getFloatTimeDomainData(micMeter.buf);
    let sum = 0;
    for (let i = 0; i < micMeter.buf.length; i++) sum += micMeter.buf[i] * micMeter.buf[i];
    vg.listenLevel = clamp(Math.sqrt(sum / micMeter.buf.length) * 9, 0, 1);
  } else if (recorder) {
    vg.listenLevel = 0.5 + 0.3 * Math.sin(now / 90);
  }
  el.orb.style.setProperty('--lvl', state.speaker ? level.toFixed(3) : '0');
  updateSubs();
  const at = paintingLabelAt();
  if (at && !el.artLabel.hidden) { el.artLabel.style.left = at.x + 'px'; el.artLabel.style.top = at.y + 'px'; }
  renderFrame(dt, now / 1000);
}
document.addEventListener('visibilitychange', () => {
  if (document.hidden) running = false;
  else if (!running) { running = true; last = performance.now(); requestAnimationFrame(frame); }
});

// ------------------------------------------------------------------ start
if (isTest && el.sessionNote) { el.sessionNote.textContent = 'Test session ' + testLabel; el.sessionNote.hidden = false; }
new ResizeObserver(resize).observe(el.stage);
resize();
if (!initScenes(el.stage)) el.fallback.hidden = false;
setControls();
loadExhibits().then(() => requestAnimationFrame(frame));

// For checking the page in a browser without sound: the same steps a visitor takes.
window.echoesLive = { ask: (text) => ask({ text }), meet: () => meet(state.current), travel, state };
