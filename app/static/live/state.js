// Shared state and small helpers for the live page (live.html).

export const state = {
  exhibits: [],        // from /personas
  current: null,       // the exhibit on stage (persona id)
  speaker: null,       // the exhibit whose voice is playing (persona id), or null
  mode: 'persona',     // or 'neutral' for the plain museum guide
  busy: false,
  W: 1,
  H: 1,
  pointer: { x: 0, y: 0, tx: 0, ty: 0, moved: 0 },
  reduce: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
};

export const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (t) => t * t * (3 - 2 * t);
export const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const easeOutBack = (t) => { const c1 = 1.3, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };
export const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
// Move `cur` towards `target` at `rate` per second, the same at any frame rate.
export const follow = (cur, target, rate, dt) => cur + (target - cur) * (1 - Math.exp(-rate * dt));

// Tweens run in the render loop, so they pause with it when the tab is hidden.
const tweens = new Set();
export function tween(ms, fn, ease = (t) => t) {
  if (state.reduce) ms = Math.min(ms, 250);
  return new Promise((resolve) => tweens.add({ start: performance.now(), ms, fn, ease, resolve }));
}
export function runTweens(now) {
  for (const tw of tweens) {
    const k = clamp((now - tw.start) / tw.ms, 0, 1);
    tw.fn(tw.ease(k), k);
    if (k >= 1) { tweens.delete(tw); tw.resolve(); }
  }
}

// The two exhibits that have their own animated scene; any other exhibit gets a plain stage.
export const sceneOf = (id) => (id === 'van-gogh' ? 'vg' : id === 't-rex' ? 'tr' : null);
