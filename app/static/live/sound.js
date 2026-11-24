// Sound for the live page: the exhibit's voice, sound effects, quiet surroundings,
// and the mouth shape for every speech sound.
//
// Voice clips play through an analyser, so the page knows how loud the voice is.
// Each clip from /speak?timing=true comes with the time of every sound and word
// (X-Echoes-Timing), which drives the mouth and the subtitles.

import { clamp, follow, lerp, smooth, state } from './state.js';

export const Sound = {
  ctx: null,
  level: 0,
  voice: null,       // the voice clip playing now
  owner: null,       // which exhibit it belongs to
  timing: null,      // its sounds and words
  voiceStart: 0,
  voiceDur: 0,
  cache: new Map(),

  // Phones only allow sound after a tap, so this runs inside every tap handler.
  unlock() {
    if (!this.ctx) {
      const Context = window.AudioContext || window.webkitAudioContext;
      if (!Context) return;
      const ctx = new Context();
      this.ctx = ctx;
      this.master = ctx.createGain(); this.master.gain.value = 0.95; this.master.connect(ctx.destination);
      this.analyser = ctx.createAnalyser(); this.analyser.fftSize = 1024; this.analyser.connect(this.master);
      this.fx = ctx.createGain(); this.fx.gain.value = 0.8; this.fx.connect(this.master);
      this.amb = ctx.createGain(); this.amb.gain.value = 0; this.amb.connect(this.master);
      this.buf = new Float32Array(this.analyser.fftSize);
    }
    if (this.ctx.state === 'suspended') this.ctx.resume().catch(() => {});
    try {
      // a tiny silent sound, so iOS Safari treats the audio session as started
      const silent = this.ctx.createBufferSource();
      silent.buffer = this.ctx.createBuffer(1, 1, 22050);
      silent.connect(this.ctx.destination); silent.start(0);
    } catch (e) { /* not needed elsewhere */ }
  },

  decode(arrayBuffer) {
    this.unlock();
    return new Promise((resolve, reject) => this.ctx.decodeAudioData(arrayBuffer, resolve, reject));
  },

  loadUrl(url) {
    if (!this.cache.has(url)) {
      const p = fetch(url)
        .then((r) => { if (!r.ok) throw new Error('Could not load ' + url); return r.arrayBuffer(); })
        .then((b) => this.decode(b));
      p.catch(() => this.cache.delete(url));
      this.cache.set(url, p);
    }
    return this.cache.get(url);
  },

  playBuffer(buffer, { voice = true, owner = null, timing = null, gain = 1, offset = 0, duration, rate = 1 } = {}) {
    this.unlock();
    if (!this.ctx || !buffer) return Promise.resolve();
    return new Promise((resolve) => {
      const src = this.ctx.createBufferSource();
      src.buffer = buffer;
      src.playbackRate.value = rate;
      const g = this.ctx.createGain(); g.gain.value = gain;
      src.connect(g); g.connect(voice ? this.analyser : this.fx);
      let done = false;
      src._finish = () => { if (!done) { done = true; resolve(); } };
      src.onended = () => {
        if (this.voice === src) { this.voice = null; this.timing = null; this.owner = null; }
        src._finish();
      };
      if (voice) {
        this.stopVoice();
        this.voice = src; this.owner = owner; this.timing = timing;
        this.voiceStart = this.ctx.currentTime;
        this.voiceDur = (duration || buffer.duration - offset) / rate;
        mouth.idx = 0;
      }
      src.start(0, offset, duration);
    });
  },

  async playUrl(url, options = {}) {
    let buffer;
    try { buffer = await this.loadUrl(url); } catch (e) { return; }
    return this.playBuffer(buffer, options);
  },

  stopVoice() {
    if (!this.voice) return;
    const v = this.voice;
    this.voice = null; this.timing = null; this.owner = null;
    try { v.stop(); } catch (e) { /* already stopped */ }
    if (v._finish) v._finish();
  },

  // Seconds into the clip that the listener hears now.
  voiceTime() {
    if (!this.voice) return -1;
    return this.ctx.currentTime - this.voiceStart - (this.ctx.outputLatency || 0) - (this.ctx.baseLatency || 0);
  },

  tick() {
    if (!this.analyser) return 0;
    this.analyser.getFloatTimeDomainData(this.buf);
    let sum = 0;
    for (let i = 0; i < this.buf.length; i++) sum += this.buf[i] * this.buf[i];
    const target = clamp((Math.sqrt(sum / this.buf.length) - 0.006) * 6.5, 0, 1);
    this.level += (target - this.level) * (target > this.level ? 0.6 : 0.2);
    return this.level;
  },

  noise() {
    if (!this._noise) {
      const n = this.ctx.sampleRate * 2;
      const b = this.ctx.createBuffer(1, n, this.ctx.sampleRate);
      const d = b.getChannelData(0);
      for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
      this._noise = b;
    }
    return this._noise;
  },

  burst({ type = 'lowpass', freq = 240, q = 0.8, gain = 0.5, len = 0.3, to = null } = {}) {
    if (!this.ctx) return;
    const c = this.ctx, t = c.currentTime;
    const n = c.createBufferSource(); n.buffer = this.noise();
    const f = c.createBiquadFilter(); f.type = type; f.frequency.value = freq; f.Q.value = q;
    const g = c.createGain(); g.gain.setValueAtTime(gain, t); g.gain.exponentialRampToValueAtTime(0.0001, t + len);
    n.connect(f); f.connect(g); g.connect(to || this.fx); n.start(t, Math.random()); n.stop(t + len + 0.02);
  },

  thud(strength = 1) {
    if (!this.ctx) return;
    const c = this.ctx, t = c.currentTime;
    const o = c.createOscillator(); o.type = 'sine';
    o.frequency.setValueAtTime(62, t); o.frequency.exponentialRampToValueAtTime(26, t + 0.42);
    const g = c.createGain();
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.9 * strength, t + 0.012); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.6);
    o.connect(g); g.connect(this.fx); o.start(t); o.stop(t + 0.65);
    this.burst({ freq: 240, gain: 0.55 * strength, len: 0.3 });
  },

  sweep(sec = 2.4, low = 220, high = 2600, peak = 0.45, type = 'bandpass') {
    if (!this.ctx) return;
    const c = this.ctx, t = c.currentTime;
    const n = c.createBufferSource(); n.buffer = this.noise(); n.loop = true;
    const f = c.createBiquadFilter(); f.type = type; f.Q.value = 0.9;
    f.frequency.setValueAtTime(low, t); f.frequency.exponentialRampToValueAtTime(high, t + sec * 0.5); f.frequency.exponentialRampToValueAtTime(low * 0.8, t + sec);
    const g = c.createGain();
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(peak, t + sec * 0.45); g.gain.exponentialRampToValueAtTime(0.0001, t + sec);
    n.connect(f); f.connect(g); g.connect(this.fx); n.start(t); n.stop(t + sec + 0.05);
  },

  // Quiet surroundings: wind and crickets in Arles, a low rumble and insects in the Cretaceous.
  ambience(kind) {
    if (!this.ctx) return;
    const c = this.ctx;
    if (this._amb) { const old = this._amb; old.g.gain.setTargetAtTime(0, c.currentTime, 0.4); setTimeout(() => old.stop(), 2500); this._amb = null; }
    this.ambKind = kind;
    if (!kind) return;
    const g = c.createGain(); g.gain.value = 0; g.connect(this.amb);
    const n = c.createBufferSource(); n.buffer = this.noise(); n.loop = true;
    const f = c.createBiquadFilter();
    const lfo = c.createOscillator(), lg = c.createGain();
    if (kind === 'vg') { f.type = 'bandpass'; f.frequency.value = 520; f.Q.value = 0.6; lfo.frequency.value = 0.09; lg.gain.value = 0.05; g.gain.setTargetAtTime(0.09, c.currentTime, 1); }
    else { f.type = 'lowpass'; f.frequency.value = 85; f.Q.value = 0.7; lfo.frequency.value = 0.05; lg.gain.value = 0.15; g.gain.setTargetAtTime(0.45, c.currentTime, 1); }
    lfo.connect(lg); lg.connect(g.gain);
    n.connect(f); f.connect(g); n.start(); lfo.start();
    this._amb = { g, stop: () => { try { n.stop(); lfo.stop(); } catch (e) { /* stopped */ } } };
    this.nextCritter = c.currentTime + 1;
    this.amb.gain.setTargetAtTime(1, c.currentTime, 0.5);
  },

  critters(dt) {
    if (!this.ctx || !this.ambKind) return;
    this.amb.gain.value = follow(this.amb.gain.value, state.speaker ? 0.35 : 1, 3, dt);
    if (this.ctx.currentTime < this.nextCritter) return;
    const c = this.ctx, t = c.currentTime;
    if (this.ambKind === 'vg') {
      for (let k = 0; k < 3; k++) {
        const o = c.createOscillator(); o.type = 'triangle'; o.frequency.value = 4300 + Math.random() * 300;
        const g = c.createGain(); const s = t + k * 0.055;
        g.gain.setValueAtTime(0.0001, s); g.gain.exponentialRampToValueAtTime(0.012, s + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, s + 0.04);
        o.connect(g); g.connect(this.amb); o.start(s); o.stop(s + 0.05);
      }
      this.nextCritter = t + 0.7 + Math.random() * 1.6;
    } else {
      this.burst({ type: 'bandpass', freq: 5200, q: 9, gain: 0.025, len: 0.9, to: this.amb });
      this.nextCritter = t + 2 + Math.random() * 5;
    }
  },
};

// X-Echoes-Timing is base64 JSON: {segs: [[start, length, shape, stress]], words: [[word, start, end, space]]}
export function decodeTiming(header) {
  if (!header) return null;
  try {
    const raw = atob(header);
    const bytes = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
    return JSON.parse(new TextDecoder().decode(bytes));
  } catch (e) {
    return null;
  }
}

// [open, wide, round, lower lip up] for each group of speech sounds
export const VIS = {
  sil: [0, 0, 0, 0], PP: [0, 0, 0, 0.4], FF: [0.06, 0.1, 0, 1], TH: [0.2, 0.15, 0, 0.3], DD: [0.24, 0.12, 0, 0],
  KK: [0.34, 0, 0, 0], CH: [0.24, -0.2, 0.6, 0], SS: [0.12, 0.5, 0, 0], RR: [0.26, -0.1, 0.5, 0],
  AA: [0.95, 0.12, 0, 0], EH: [0.55, 0.3, 0, 0], IH: [0.3, 0.75, 0, 0], OH: [0.62, -0.3, 0.75, 0], UU: [0.24, -0.5, 1, 0],
};

export const mouth = { open: 0, wide: 0, round: 0, lip: 0, emph: 0, idx: 0 };

// Called once a frame: move the mouth towards the shape of the sound being heard now,
// blending into the next sound near the end of each one.
export function mouthUpdate(dt) {
  let target = [0, 0, 0, 0], stress = 0;
  const segs = Sound.timing && Sound.timing.segs;
  if (Sound.voice && segs && segs.length) {
    const t = Sound.voiceTime();
    let i = mouth.idx;
    if (i >= segs.length || segs[i][0] > t) i = 0;
    while (i + 1 < segs.length && segs[i + 1][0] <= t) i++;
    mouth.idx = i;
    const s = segs[i];
    if (s && t >= s[0] && t < s[0] + s[1] + 0.1) {
      const p = VIS[s[2]] || VIS.DD;
      target = p.slice();
      const k = (t - s[0]) / Math.max(s[1], 0.001);
      const next = segs[i + 1];
      if (k > 0.45 && next) {
        const q = VIS[next[2]] || VIS.DD, m = smooth(clamp((k - 0.45) / 0.55, 0, 1)) * 0.55;
        for (let j = 0; j < 4; j++) target[j] = lerp(p[j], q[j], m);
      }
      stress = s[3];
    }
    target[0] *= 0.75 + 0.5 * Sound.level;
  } else if (Sound.voice) {
    // no timing (a sound effect, or a voice Kokoro gave no timing for): follow the loudness
    target = [clamp(Sound.level * 1.25, 0, 1), 0, 0, 0];
  }
  const closing = target[0] < mouth.open;
  mouth.open = follow(mouth.open, target[0], closing ? (target[0] < 0.05 ? 48 : 30) : 36, dt);
  mouth.wide = follow(mouth.wide, target[1], 22, dt);
  mouth.round = follow(mouth.round, target[2], 22, dt);
  mouth.lip = follow(mouth.lip, target[3], 32, dt);
  mouth.emph = Math.max(mouth.emph * Math.exp(-dt * 3.5), stress === 2 ? 1 : stress === 1 ? 0.45 : 0);
}

// When a word is heard in the current clip (seconds), or null.
export function wordTime(timing, pattern) {
  const w = timing && timing.words && timing.words.find((x) => pattern.test(x[0]));
  return w ? w[1] : null;
}
