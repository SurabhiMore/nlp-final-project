// The two animated exhibits of the live page, drawn with three.js:
//   Van Gogh: his 1887 self-portrait (Art Institute of Chicago, CC0) in a gilt frame,
//   in front of Wheat Field with Cypresses (The Met, CC0), whose brushstrokes move.
//   The face blinks, follows the visitor and shapes its mouth for every sound.
//   T. rex: Quaternius's low-poly T. rex (CC0) on a museum plinth, which turns from
//   fossil to flesh, walks out into a Cretaceous evening and roars.
// app.js decides what happens; this file only draws it.

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Sound, mouth } from './sound.js';
import { clamp, easeInOut, easeOutBack, follow, lerp, sceneOf, smooth, state, tween, wait } from './state.js';

const ART = '/static/live/art/';
const PW = 843 / 1074;   // the self-portrait's width for a height of 1
let renderer = null;
let warpCanvas = null, warpCtx = null, DPR = 1;
const texLoader = new THREE.TextureLoader();
const _v = new THREE.Vector3(), _d = new THREE.Vector3();

export const scenes = { ok: false };

export function initScenes(stage) {
  warpCanvas = stage.querySelector('#warp');
  warpCtx = warpCanvas.getContext('2d');
  try {
    renderer = new THREE.WebGLRenderer({ canvas: stage.querySelector('#gl'), antialias: true, powerPreference: 'high-performance' });
  } catch (e) {
    return false;
  }
  DPR = Math.min(window.devicePixelRatio || 1, 2);
  renderer.setPixelRatio(DPR);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  scenes.ok = true;
  buildVg().catch((e) => console.error('Van Gogh scene:', e));
  buildTrex().catch((e) => { console.error('T. rex scene:', e); tr.state = 'error'; });
  return true;
}

export function resizeScenes() {
  if (!renderer) return;
  renderer.setSize(state.W, state.H, false);
  warpCanvas.width = Math.round(state.W * DPR);
  warpCanvas.height = Math.round(state.H * DPR);
  if (vg.ready) vgLayout();
  if (tr.ready) trLayout();
}

export function renderFrame(dt, t) {
  if (!renderer) return;
  const s = sceneOf(state.current);
  if (s === 'vg' && vg.ready) { vgUpdate(dt, t); renderer.render(vg.scene, vg.camera); }
  else if (s === 'tr' && tr.ready) { trUpdate(dt, t); renderer.render(tr.scene, tr.camera); }
  else { renderer.setClearColor(0x05060a, 1); renderer.clear(); }
}

const talking = (scene) => state.mode === 'persona' && sceneOf(state.speaker) === scene;

// ------------------------------------------------------------------ shaders
const SIMPLE_VS = 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }';

const PAINT_FS = `
precision highp float;
uniform sampler2D uTex; uniform sampler2D uFlow;
uniform float uTime, uStrength, uVoice, uAspect, uNight, uSepia, uListen;
uniform vec2 uMouth, uLight, uTexel;
uniform vec4 uView;
varying vec2 vUv;
float h21(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vnoise(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(h21(i), h21(i + vec2(1.0, 0.0)), u.x), mix(h21(i + vec2(0.0, 1.0)), h21(i + vec2(1.0, 1.0)), u.x), u.y); }
float lum(vec3 c){ return dot(c, vec3(0.3, 0.59, 0.11)); }
vec3 sampleFlow(vec2 uv){
  vec3 f = texture2D(uFlow, uv).rgb;
  vec2 flow = (f.rg * 2.0 - 1.0) * f.b; flow.y = -flow.y;
  float t = uTime * 0.17 + vnoise(uv * 3.0);
  float t0 = fract(t), t1 = fract(t + 0.5);
  float s = uStrength * (1.0 + uVoice * 1.1);
  vec3 c0 = texture2D(uTex, uv - flow * s * (t0 - 0.5)).rgb;
  vec3 c1 = texture2D(uTex, uv - flow * s * (t1 - 0.5)).rgb;
  return mix(c0, c1, abs(1.0 - 2.0 * t0));
}
void main(){
  vec2 uv = vUv;
  vec2 d = (uv - uMouth) * vec2(uAspect, 1.0);
  float r = length(d) + 1e-4;
  uv += (d / r) * vec2(1.0 / uAspect, 1.0) * sin(r * 48.0 - uTime * 7.5) * exp(-r * 2.4) * smoothstep(0.03, 0.14, r) * uVoice * 0.007;
  vec2 dl = (uv - vec2(0.5, uView.y - 0.05)) * vec2(uAspect, 1.0);
  float rl = length(dl) + 1e-4;
  uv += (dl / rl) * vec2(1.0 / uAspect, 1.0) * sin(rl * 40.0 + uTime * 9.0) * exp(-rl * 1.6) * uListen * 0.006;
  vec3 col = sampleFlow(uv);
  float gx = lum(texture2D(uTex, uv + vec2(uTexel.x, 0.0)).rgb) - lum(texture2D(uTex, uv - vec2(uTexel.x, 0.0)).rgb);
  float gy = lum(texture2D(uTex, uv + vec2(0.0, uTexel.y)).rgb) - lum(texture2D(uTex, uv - vec2(0.0, uTexel.y)).rgb);
  vec3 n = normalize(vec3(-gx * 5.0, -gy * 5.0, 1.0));
  vec3 L = normalize(vec3(uLight, 0.75));
  col *= 0.86 + 0.26 * dot(n, L);
  col += pow(max(0.0, dot(reflect(-L, n), vec3(0.0, 0.0, 1.0))), 28.0) * 0.14;
  vec3 night = col * vec3(0.28, 0.38, 0.78) + pow(lum(col), 3.0) * vec3(0.3, 0.38, 0.62) + vec3(0.015, 0.02, 0.06);
  float screenY = (vUv.y - uView.y) / (uView.w - uView.y);
  float sky = smoothstep(0.45, 0.66, screenY);
  vec3 stars = vec3(0.0);
  for (int i = 0; i < 9; i++) {
    float fi = float(i);
    vec2 sp = mix(uView.xy, uView.zw, vec2(0.06 + fract(fi * 0.618) * 0.88, 0.68 + fract(fi * 0.371) * 0.27));
    vec2 sd = (vUv - sp) * vec2(uAspect, 1.0);
    float sr = length(sd);
    float tw = 0.8 + 0.2 * sin(uTime * 2.3 + fi * 1.7);
    float swirl = 0.5 + 0.5 * sin(sr * 110.0 - uTime * 1.6 + atan(sd.y, sd.x) * 2.0);
    stars += vec3(1.0, 0.88, 0.5) * (exp(-sr * sr / 0.0003) * 2.2 + exp(-sr * 11.0) * 0.85 * swirl) * tw;
  }
  vec2 md = (vUv - mix(uView.xy, uView.zw, vec2(0.56, 0.9))) * vec2(uAspect, 1.0);
  float moon = smoothstep(0.04, 0.035, length(md)) * smoothstep(0.028, 0.035, length(md - vec2(0.019, 0.01)));
  stars += vec3(1.0, 0.86, 0.45) * (moon * 1.4 + exp(-length(md) * 14.0) * 0.5);
  night += stars * sky;
  col = mix(col, night, uNight);
  if (uSepia > 0.001) {
    vec2 cp = vUv * vec2(uAspect, 1.0) * 46.0 + vec2(vnoise(vUv * 9.0), vnoise(vUv * 9.0 + 7.0)) * 1.4;
    vec2 ci = floor(cp), cf = fract(cp);
    float d1 = 8.0, d2 = 8.0;
    for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) {
      vec2 o = vec2(float(x), float(y));
      vec2 pt = o + vec2(h21(ci + o), h21(ci + o + 17.0));
      float dd = length(pt - cf);
      if (dd < d1) { d2 = d1; d1 = dd; } else if (dd < d2) d2 = dd;
    }
    float crack = (1.0 - smoothstep(0.0, 0.035, d2 - d1)) * (0.55 + 0.45 * vnoise(vUv * 30.0));
    float l = lum(col);
    col = mix(col, vec3(l * 1.08, l * 0.9, l * 0.66) * 0.82 * (1.0 - crack * 0.3), uSepia);
  }
  float v = smoothstep(1.05, 0.18, length((vUv - 0.5) * vec2(1.15, 1.0)));
  col *= mix(0.4, 1.0, v);
  col = mix(col, col * vec3(0.8, 0.88, 1.06), 0.3 * (1.0 - uSepia));
  gl_FragColor = vec4(col, 1.0);
}`;

// Positions are in pixels of the 843 x 1074 self-portrait: eyes at (290, 399) and (456, 404),
// the line between the lips at y = 598.5, centred at x = 362.
const PORTRAIT_VS = `
uniform float uOpen, uWide, uRound, uLip, uBlink, uBrow, uDepth;
uniform vec2 uGaze;
varying vec2 vUv; varying vec2 vImg;
const vec2 IMG = vec2(843.0, 1074.0);
const float PW = 0.78492;
const vec2 MC = vec2(362.0, 598.5);
const float MW = 70.0;
vec2 eyeWarp(vec2 p, vec2 c, float hw, float blink){
  float top = c.y - 26.0, bottom = c.y + 11.0, lid = c.y - 7.0;
  float wx = 1.0 - smoothstep(0.62, 1.0, abs(p.x - c.x) / (hw + 10.0));
  float inside = step(top, p.y) * step(p.y, bottom);
  float t = clamp((p.y - top) / (bottom - top), 0.0, 1.0);
  float tE = (lid - top) / (bottom - top);
  float tt = mix(t, min(1.0, t / tE), blink * wx * inside);
  p.y = mix(p.y, top + tt * (bottom - top), inside);
  return p;
}
vec2 irisWarp(vec2 p, vec2 c, vec2 g){
  float d = length((p - c) / vec2(15.0, 10.0));
  return p + g * vec2(4.5, 2.5) * (1.0 - smoothstep(0.45, 1.0, d));
}
void main(){
  vUv = uv;
  vec2 p = vec2(uv.x, 1.0 - uv.y) * IMG;
  vImg = p;
  vec2 q = irisWarp(p, vec2(289.0, 398.0), uGaze);
  q = irisWarp(q, vec2(455.0, 405.0), uGaze);
  q = eyeWarp(q, vec2(290.0, 399.0), 30.0, uBlink);
  q = eyeWarp(q, vec2(456.0, 404.0), 32.0, uBlink);
  float brow = exp(-pow((p.y - 372.0) / 16.0, 2.0)) * (1.0 - smoothstep(0.8, 1.25, abs(p.x - 372.0) / 140.0));
  q.y -= uBrow * 3.5 * brow;
  float dx = p.x - MC.x, ax = abs(dx) / MW;
  float tp = cos(clamp(dx / MW, -1.0, 1.0) * 1.5707963);
  float tpo = pow(max(tp, 0.0), 0.8);
  float below = smoothstep(MC.y - 1.0, MC.y + 6.0, p.y);
  float lipBand = below * (1.0 - smoothstep(MC.y + 30.0, MC.y + 95.0, p.y));
  float jaw = below * (1.0 - smoothstep(738.0, 810.0, p.y))
    * (1.0 - smoothstep(0.55, 1.0, length((p - vec2(392.0, 668.0)) / vec2(195.0, 125.0))))
    * clamp((612.0 - p.x) / 240.0, 0.15, 1.0);
  float open = uOpen * (1.0 - uLip * 0.85);
  float dy = open * (8.0 * tpo * lipBand + 5.5 * jaw);
  float above = (1.0 - smoothstep(MC.y - 2.0, MC.y + 1.0, p.y)) * smoothstep(MC.y - 40.0, MC.y - 2.0, p.y);
  dy -= open * 2.2 * tp * above;
  dy -= uLip * 3.0 * tp * lipBand * (1.0 - smoothstep(MC.y + 12.0, MC.y + 30.0, p.y));
  dy += uRound * 2.0 * tp * lipBand;
  float corner = exp(-pow((p.y - MC.y) / 16.0, 2.0)) * smoothstep(0.25, 0.85, ax) * (1.0 - smoothstep(1.05, 1.7, ax));
  q += vec2((uWide * 5.0 - uRound * 6.0) * sign(dx) * corner, dy);
  vec3 pos = vec3((q.x / IMG.x - 0.5) * PW, 0.5 - q.y / IMG.y, 0.0);
  pos.z = exp(-pow(length((p - vec2(400.0, 520.0)) / vec2(230.0, 300.0)), 2.0) * 1.5) * uDepth;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
}`;

const PORTRAIT_FS = `
precision highp float;
uniform sampler2D uTex; uniform float uOpen, uGlow, uScan;
uniform vec2 uLight, uTexel;
varying vec2 vUv; varying vec2 vImg;
float lum(vec3 c){ return dot(c, vec3(0.3, 0.59, 0.11)); }
void main(){
  vec3 col = texture2D(uTex, vUv).rgb;
  float gx = lum(texture2D(uTex, vUv + vec2(uTexel.x, 0.0)).rgb) - lum(texture2D(uTex, vUv - vec2(uTexel.x, 0.0)).rgb);
  float gy = lum(texture2D(uTex, vUv + vec2(0.0, uTexel.y)).rgb) - lum(texture2D(uTex, vUv - vec2(0.0, uTexel.y)).rgb);
  vec3 n = normalize(vec3(-gx * 6.0, -gy * 6.0, 1.0));
  vec3 L = normalize(vec3(uLight, 0.8));
  col *= 0.86 + 0.24 * dot(n, L);
  col += pow(max(0.0, dot(reflect(-L, n), vec3(0.0, 0.0, 1.0))), 26.0) * 0.12;
  float tpf = cos(clamp((vImg.x - 362.0) / 70.0, -1.0, 1.0) * 1.5707963);
  float cav = exp(-pow((vImg.y - 598.5) / 3.6, 2.0)) * pow(max(tpf, 0.0), 0.8);
  col = mix(col, vec3(0.16, 0.05, 0.045) * (0.75 + 0.25 * tpf), clamp(cav * uOpen * 1.35, 0.0, 0.9));
  col *= 0.9 + 0.16 * smoothstep(0.9, 0.0, length((vUv - vec2(0.48, 0.7)) * vec2(1.0, 1.3)));
  vec2 e = min(vUv, 1.0 - vUv);
  col *= 0.72 + 0.28 * smoothstep(0.0, 0.05, min(e.x, e.y));
  col += uGlow * vec3(0.07, 0.05, 0.025);
  if (uScan > 0.0 && uScan < 1.0) {
    float band = 1.0 - smoothstep(0.0, 0.16, abs(vUv.y - (1.15 - uScan * 1.3)));
    vec2 gq = abs(fract(vUv * vec2(42.0, 54.0)) - 0.5);
    col = mix(col, vec3(0.5, 0.88, 1.0), smoothstep(0.43, 0.5, max(gq.x, gq.y)) * band * 0.75);
    col += vec3(0.15, 0.4, 0.6) * band * 0.18;
  }
  gl_FragColor = vec4(col, 1.0);
}`;

const FRAME_FS = `
precision highp float;
uniform vec2 uSize; uniform float uBorder;
varying vec2 vUv;
void main(){
  vec2 p = (vUv - 0.5) * uSize;
  vec2 q = abs(p) - (uSize * 0.5 - vec2(uBorder));
  float o = max(q.x, q.y);
  if (o < 0.0) discard;
  float b = clamp(o / uBorder, 0.0, 1.0);
  bool vertical = q.x > q.y;
  vec2 n = vertical ? vec2(sign(p.x), 0.0) : vec2(0.0, sign(p.y));
  float lit = clamp(0.55 + 0.45 * dot(n, normalize(vec2(-0.55, 0.85))) * cos(b * 9.4248), 0.0, 1.0);
  float along = vertical ? p.y : p.x;
  float orn = smoothstep(0.32, 0.4, b) * (1.0 - smoothstep(0.62, 0.7, b)) * (0.5 + 0.5 * sin(along * 150.0));
  float bead = smoothstep(0.84, 0.9, b) * (1.0 - smoothstep(0.95, 1.0, b));
  vec3 col = mix(vec3(0.24, 0.15, 0.05), vec3(0.68, 0.49, 0.19), 0.35 + 0.65 * lit);
  col = mix(col, vec3(1.0, 0.87, 0.55), pow(lit, 4.0) * 0.75 + bead * 0.45 + orn * 0.25);
  col *= mix(0.25, 1.0, smoothstep(0.0, 0.07, b));
  col *= mix(1.0, 0.55, smoothstep(0.97, 1.0, b));
  gl_FragColor = vec4(col, 1.0);
}`;

const SHADOW_FS = `
precision highp float;
uniform vec2 uSize; uniform vec2 uPad;
varying vec2 vUv;
void main(){
  vec2 p = (vUv - 0.5) * uPad;
  vec2 q = abs(p) - uSize * 0.5;
  float d = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0);
  gl_FragColor = vec4(0.0, 0.0, 0.0, (1.0 - smoothstep(-0.02, 0.1, d)) * 0.7);
}`;

// A cited painting paints itself in the order of its own brushstrokes (an order map made offline).
const CANVAS_FS = `
precision highp float;
uniform sampler2D uTex; uniform sampler2D uOrder; uniform float uP;
varying vec2 vUv;
void main(){
  vec3 paint = texture2D(uTex, vUv).rgb;
  float o = texture2D(uOrder, vUv).r;
  float r = smoothstep(o - 0.05, o + 0.004, uP);
  vec2 w = fract(vUv * vec2(170.0, 133.0));
  vec3 canvas = vec3(0.9, 0.86, 0.77) * (0.95 + 0.05 * (step(0.5, w.x) + step(0.5, w.y)) * 0.5);
  float wet = smoothstep(0.0, 0.035, uP - o) * (1.0 - smoothstep(0.035, 0.11, uP - o));
  gl_FragColor = vec4(mix(canvas, paint * (1.0 + wet * 0.3), r), 1.0);
}`;

function makeFrame(w, h, b) {
  const mat = new THREE.ShaderMaterial({ uniforms: { uSize: { value: new THREE.Vector2(w + 2 * b, h + 2 * b) }, uBorder: { value: b } }, vertexShader: SIMPLE_VS, fragmentShader: FRAME_FS });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w + 2 * b, h + 2 * b), mat);
  m.position.z = 0.004;
  return m;
}
function makeShadow(w, h) {
  const pw = w * 1.3, ph = h * 1.25;
  const mat = new THREE.ShaderMaterial({ uniforms: { uSize: { value: new THREE.Vector2(w, h) }, uPad: { value: new THREE.Vector2(pw, ph) } }, vertexShader: SIMPLE_VS, fragmentShader: SHADOW_FS, transparent: true, depthWrite: false });
  const m = new THREE.Mesh(new THREE.PlaneGeometry(pw, ph), mat);
  m.position.set(0.035, -0.05, -0.04);
  return m;
}

// ------------------------------------------------------------------ Van Gogh
export const vg = {
  scene: new THREE.Scene(), camera: new THREE.PerspectiveCamera(32, 1, 0.1, 60), camZ: 4.6, dolly: 1,
  ready: false, mode: 'idle', blinkT: -1, nextBlink: 1.5, twice: false, modeS: { think: 0, search: 0, away: 0, listen: 0 },
  baseScale: 1, baseX: 0, baseY: 0, slot: new THREE.Vector3(), slotScale: 1, W0: 1, H0: 1,
  painting: null, paintAnim: false, listenLevel: 0,
};

async function buildVg() {
  const [paint, flow, face] = await Promise.all(['wheat-field.jpg', 'wheat-flow.png', 'self-portrait.jpg'].map((f) => texLoader.loadAsync(ART + f)));
  const aniso = renderer.capabilities.getMaxAnisotropy();
  paint.anisotropy = aniso; face.anisotropy = aniso;
  flow.minFilter = THREE.LinearFilter; flow.generateMipmaps = false;
  vg.paintAspect = paint.image.width / paint.image.height;
  vg.u = {
    uTex: { value: paint }, uFlow: { value: flow }, uTime: { value: 0 }, uStrength: { value: 0.016 }, uVoice: { value: 0 },
    uAspect: { value: vg.paintAspect }, uNight: { value: 0 }, uSepia: { value: 0 }, uListen: { value: 0 },
    uMouth: { value: new THREE.Vector2(0.4, 0.45) }, uLight: { value: new THREE.Vector2(0.3, 0.5) },
    uTexel: { value: new THREE.Vector2(1 / paint.image.width, 1 / paint.image.height) }, uView: { value: new THREE.Vector4(0.2, 0.2, 0.8, 0.8) },
  };
  vg.bg = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.ShaderMaterial({ uniforms: vg.u, vertexShader: SIMPLE_VS, fragmentShader: PAINT_FS, depthWrite: false }));
  vg.bg.renderOrder = -1;
  vg.scene.add(vg.bg);

  vg.group = new THREE.Group();
  vg.scene.add(vg.group);
  vg.pu = {
    uTex: { value: face }, uOpen: { value: 0 }, uWide: { value: 0 }, uRound: { value: 0 }, uLip: { value: 0 }, uBlink: { value: 0 }, uBrow: { value: 0 },
    uGaze: { value: new THREE.Vector2() }, uDepth: { value: 0.06 }, uGlow: { value: 0 }, uScan: { value: 0 },
    uLight: vg.u.uLight, uTexel: { value: new THREE.Vector2(1 / face.image.width, 1 / face.image.height) },
  };
  vg.portrait = new THREE.Mesh(new THREE.PlaneGeometry(PW, 1, 160, 204), new THREE.ShaderMaterial({ uniforms: vg.pu, vertexShader: PORTRAIT_VS, fragmentShader: PORTRAIT_FS }));
  vg.portrait.frustumCulled = false;
  vg.portrait.position.z = 0.012;
  vg.group.add(vg.portrait, makeFrame(PW, 1, 0.085), makeShadow(PW + 0.17, 1.17));
  vg.ready = true;
  vgLayout();
}

function vgLayout() {
  const aspect = state.W / state.H;
  vg.camera.aspect = aspect; vg.camera.updateProjectionMatrix();
  const tanH = Math.tan((vg.camera.fov * Math.PI) / 360);
  const H0 = 2 * vg.camZ * tanH, W0 = H0 * aspect;
  vg.W0 = W0; vg.H0 = H0;
  const wide = aspect > 1.1;
  vg.baseScale = wide ? H0 * 0.7 : Math.min(H0 * 0.56, (W0 * 0.74) / PW);
  vg.baseX = wide ? -W0 * 0.16 : 0;
  vg.baseY = wide ? -H0 * 0.015 : H0 * 0.055;
  vg.slot.set(wide ? W0 * 0.255 : W0 * 0.22, wide ? -H0 * 0.13 : -H0 * 0.27, 0.25);
  vg.slotScale = wide ? H0 * 0.3 : H0 * 0.18;
  const zb = -2.4;
  const hb = 2 * (vg.camZ * 1.45 - zb) * tanH * 1.08, wbView = hb * aspect;
  let bw, bh;
  if (wbView / hb > vg.paintAspect) { bw = wbView; bh = wbView / vg.paintAspect; } else { bh = hb; bw = hb * vg.paintAspect; }
  vg.bg.scale.set(bw, bh, 1);
  vg.bg.position.set(0, 0, zb);
  vg.u.uAspect.value = bw / bh;
  const hv = (2 * (vg.camZ - zb) * tanH) / 2, wv = hv * aspect;
  vg.u.uView.value.set(0.5 - wv / bw, 0.5 - hv / bh, 0.5 + wv / bw, 0.5 + hv / bh);
}

function vgUpdate(dt, t) {
  const p = state.pointer;
  vg.u.uTime.value = t;
  const speaking = talking('vg');
  const lvl = speaking ? Sound.level : 0;

  vg.nextBlink -= dt;
  if (vg.nextBlink <= 0 && vg.blinkT < 0) { vg.blinkT = 0; vg.nextBlink = 2.2 + Math.random() * 4; if (Math.random() < 0.2) vg.twice = true; }
  if (vg.blinkT >= 0) {
    vg.blinkT += dt;
    const k = vg.blinkT / 0.18;
    vg.pu.uBlink.value = k < 0.42 ? smooth(k / 0.42) : smooth(clamp(1 - (k - 0.42) / 0.58, 0, 1));
    if (k >= 1) { vg.blinkT = -1; vg.pu.uBlink.value = 0; if (vg.twice) { vg.twice = false; vg.nextBlink = 0.14; } }
  }

  const m = vg.modeS;
  m.think = follow(m.think, vg.mode === 'thinking' ? 1 : 0, 4, dt);
  m.search = follow(m.search, vg.mode === 'searching' ? 1 : 0, 4, dt);
  m.away = follow(m.away, vg.mode === 'away' ? 1 : 0, 3, dt);
  m.listen = follow(m.listen, vg.mode === 'listening' ? 1 : 0, 5, dt);
  let gx = clamp(p.x * 1.1, -1, 1), gy = clamp(-p.y * 0.7, -1, 1);
  gx = lerp(gx, 0.05, m.listen); gy = lerp(gy, 0.15, m.listen);
  gx = lerp(gx, -0.8, m.think); gy = lerp(gy, -1.0, m.think);
  gx = lerp(gx, 0.3, m.search); gy = lerp(gy, 1.0, m.search);
  gx = lerp(gx, -0.9, m.away); gy = lerp(gy, 0.7, m.away);
  const g = vg.pu.uGaze.value;
  g.x = follow(g.x, gx, 7, dt); g.y = follow(g.y, gy, 7, dt);

  vg.pu.uOpen.value = speaking ? mouth.open : follow(vg.pu.uOpen.value, 0, 20, dt);
  vg.pu.uWide.value = speaking ? mouth.wide : follow(vg.pu.uWide.value, 0, 20, dt);
  vg.pu.uRound.value = speaking ? mouth.round : follow(vg.pu.uRound.value, 0, 20, dt);
  vg.pu.uLip.value = speaking ? mouth.lip : follow(vg.pu.uLip.value, 0, 20, dt);
  vg.pu.uBrow.value = follow(vg.pu.uBrow.value, (speaking ? mouth.emph * 0.9 : 0) + m.listen * 0.35 - m.think * 0.2, 12, dt);
  vg.pu.uGlow.value = lvl * 0.6;

  const grp = vg.group, breath = Math.sin(t * 1.25);
  const nod = speaking ? mouth.emph * 0.02 : 0;
  grp.rotation.y = follow(grp.rotation.y, p.x * 0.17 - m.think * 0.05 - m.away * 0.16 + m.listen * 0.03, 4, dt);
  grp.rotation.x = follow(grp.rotation.x, -p.y * 0.09 + m.think * 0.03 + m.search * 0.05 + nod - m.listen * 0.02, 6, dt);
  grp.rotation.z = Math.sin(t * 0.45) * 0.006 + lvl * Math.sin(t * 5.3) * 0.004 - m.away * 0.015;
  grp.scale.setScalar(vg.baseScale * (1 + breath * 0.003 + lvl * 0.008 + m.listen * 0.015));
  grp.position.set(vg.baseX, vg.baseY + breath * 0.004 * vg.baseScale, 0);

  vg.u.uVoice.value = follow(vg.u.uVoice.value, state.reduce ? 0 : lvl, 10, dt);
  vg.u.uListen.value = follow(vg.u.uListen.value, state.reduce ? 0 : vg.listenLevel, 12, dt);
  vg.u.uStrength.value = (state.reduce ? 0.004 : 0.016) * (1 + m.think * 1.2);
  // the light raking across the paint follows the visitor, and drifts on its own when nobody moves
  const idle = performance.now() - p.moved > 2500;
  const lx = idle ? Math.cos(t * 0.35) * 0.7 : p.x * 0.9, ly = idle ? 0.35 + Math.sin(t * 0.35) * 0.4 : p.y * 0.8 + 0.2;
  vg.u.uLight.value.set(follow(vg.u.uLight.value.x, lx, 3, dt), follow(vg.u.uLight.value.y, ly, 3, dt));

  vg.camera.position.x = follow(vg.camera.position.x, p.x * 0.16, 3, dt);
  vg.camera.position.y = follow(vg.camera.position.y, p.y * 0.1, 3, dt);
  vg.camera.position.z = vg.camZ * vg.dolly;
  vg.camera.lookAt(vg.group.position.x * 0.15, 0, 0);

  // the voice ripples out through the paint from where his mouth is
  _v.set((362 / 843 - 0.5) * PW, 0.5 - 600 / 1074, 0.02).applyMatrix4(vg.portrait.matrixWorld);
  const cam = vg.camera.position;
  _d.copy(_v).sub(cam);
  const hit = (vg.bg.position.z - cam.z) / _d.z;
  vg.u.uMouth.value.set((cam.x + _d.x * hit - vg.bg.position.x) / vg.bg.scale.x + 0.5, (cam.y + _d.y * hit - vg.bg.position.y) / vg.bg.scale.y + 0.5);

  const pt = vg.painting;
  if (pt && pt.group.visible && !vg.paintAnim) {
    pt.group.position.set(vg.slot.x, vg.slot.y + Math.sin(t * 1.1) * 0.012, vg.slot.z);
    pt.group.rotation.set(0.02, follow(pt.group.rotation.y, -0.2 + p.x * 0.1, 3, dt), 0.02);
  }
}

export function vgIntro() {
  vg.dolly = 1.45;
  return tween(2200, (k) => { vg.dolly = lerp(1.45, 1, k); }, easeInOut);
}
export function vgNight(on) {
  if (!vg.ready) return Promise.resolve();
  const from = vg.u.uNight.value, to = on ? 1 : 0;
  return tween(on ? 2600 : 1500, (k) => { vg.u.uNight.value = lerp(from, to, k); }, easeInOut);
}
export function vgSepia(on) {
  if (!vg.ready) return Promise.resolve();
  const from = vg.u.uSepia.value, to = on ? 1 : 0;
  return tween(on ? 1300 : 1500, (k) => { vg.u.uSepia.value = lerp(from, to, k); }, easeInOut);
}
export function vgScan() {
  if (!vg.ready) return Promise.resolve();
  return tween(2200, (k) => { vg.pu.uScan.value = k; }).then(() => { vg.pu.uScan.value = 0; });
}
export function vgBlink() { vg.blinkT = 0; vg.twice = true; }

const paintings = new Map();
function noiseTexture() {
  const n = 64, data = new Uint8Array(n * n * 4);
  for (let i = 0; i < n * n; i++) { const v = Math.random() * 255; data.set([v, v, v, 255], i * 4); }
  const t = new THREE.DataTexture(data, n, n); t.needsUpdate = true; t.magFilter = THREE.LinearFilter;
  return t;
}
function loadPainting(entry) {
  if (!paintings.has(entry.image)) {
    paintings.set(entry.image, Promise.all([texLoader.loadAsync(ART + entry.image), entry.order ? texLoader.loadAsync(ART + entry.order) : Promise.resolve(noiseTexture())])
      .then(([tex, order]) => {
        tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
        order.minFilter = THREE.LinearFilter; order.generateMipmaps = false;
        const a = tex.image.width / tex.image.height;
        const u = { uTex: { value: tex }, uOrder: { value: order }, uP: { value: 0 } };
        const group = new THREE.Group();
        const mesh = new THREE.Mesh(new THREE.PlaneGeometry(a, 1), new THREE.ShaderMaterial({ uniforms: u, vertexShader: SIMPLE_VS, fragmentShader: CANVAS_FS }));
        mesh.position.z = 0.01;
        group.add(mesh, makeFrame(a, 1, 0.07), makeShadow(a + 0.14, 1.14));
        group.visible = false;
        vg.scene.add(group);
        return { group, u, entry };
      }));
  }
  return paintings.get(entry.image);
}
// A painting the answer cites flies in as a blank canvas and paints itself.
export async function vgPaint(entry) {
  if (!vg.ready) return;
  const p = await loadPainting(entry);
  vgHidePainting();
  vg.painting = p;
  const g = p.group;
  g.visible = true; vg.paintAnim = true; p.u.uP.value = 0;
  const to = vg.slot.clone(), from = to.clone().add(new THREE.Vector3(vg.W0 * 0.75, vg.H0 * 0.2, 1.4));
  g.scale.setScalar(vg.slotScale);
  await tween(900, (k) => {
    g.position.lerpVectors(from, to, k);
    g.rotation.set(0.2 * (1 - k), -1.25 * (1 - k) - 0.2, 0.18 * (1 - k));
  }, easeOutBack);
  vg.paintAnim = false;
  let lastSwish = 0;
  await tween(3400, (k, raw) => {
    p.u.uP.value = k * 1.08;
    if (raw - lastSwish > 0.11 && raw < 0.95) { lastSwish = raw; Sound.burst({ type: 'bandpass', freq: 1800 + Math.random() * 1500, q: 1.4, gain: 0.05, len: 0.12 }); }
  }, (x) => 1 - Math.pow(1 - x, 1.6));
}
export function vgHidePainting() {
  if (vg.painting) vg.painting.group.visible = false;
  vg.painting = null;
}
// Where to put the painting's label on screen, or null.
export function paintingLabelAt() {
  const p = vg.painting;
  if (!p || !p.group.visible || sceneOf(state.current) !== 'vg' || vg.paintAnim) return null;
  _v.set(0, 0.62, 0).applyMatrix4(p.group.matrixWorld).project(vg.camera);
  return { x: (_v.x * 0.5 + 0.5) * state.W, y: (-_v.y * 0.5 + 0.5) * state.H - 6 };
}

// ------------------------------------------------------------------ T. rex
export const tr = {
  scene: new THREE.Scene(), camera: new THREE.PerspectiveCamera(36, 1, 0.1, 400), ready: false, state: 'loading',
  u: { dissolve: { value: 0 }, minY: { value: 0 }, height: { value: 3 } }, awake: 0, shake: 0, jaw: 0, chomp: 0, snort: 0, wiggle: 0, wiggleOn: false,
  bones: {}, rest: {}, look: { yaw: 0, pitch: 0 }, lookAt: null, lookUntil: 0, thinking: 0, listening: 0, walkPrev: 0, roaring: false,
  base: new THREE.Vector3(), fwd: new THREE.Vector3(0, 0, 1), right: new THREE.Vector3(1, 0, 0), focus: { def: null, k: 0, target: 0 },
};
const FOCUS = {
  body: { bone: 'Shoulders', dist: 5.4, az: 0.1, h: 0.4 },
  arms: { bone: 'FrontLowLeg.L', dist: 4.6, az: -0.25, h: 0.05 },
  head: { bone: 'Head', dist: 4.0, az: -0.45, h: 0.3 },
  tail: { bone: 'Tail3', dist: 5.8, az: 0.95, h: 0.5 },
  legs: { bone: 'BackLowLeg.L', dist: 5.4, az: 0.25, h: 0.3 },
};
const REGIONS = [
  { bones: ['Head', 'Head_end', 'Neck'], q: 'How strong was your bite?' },
  { bones: ['FrontUpLeg.L', 'FrontLowLeg.L', 'FrontFoot.L', 'FrontUpLeg.R', 'FrontLowLeg.R', 'FrontFoot.R'], q: 'Why were your arms so short?' },
  { bones: ['BackUpLeg.L', 'BackLowLeg.L', 'BackFoot.L', 'BackUpLeg.R', 'BackLowLeg.R', 'BackFoot.R'], q: 'How fast could you run?' },
  { bones: ['Tail1', 'Tail2', 'Tail3', 'Tail4', 'Tail5'], q: 'What was your long tail for?' },
  { bones: ['Torso', 'Shoulders', 'Hips', 'Back'], q: 'Did you have scales or feathers?' },
];

function softDot() {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const x = c.getContext('2d');
  const g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.35, 'rgba(255,255,255,.5)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g; x.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

const NOISE3 = `
float h31(vec3 p){ p = fract(p * 0.1031); p += dot(p, p.zyx + 31.32); return fract((p.x + p.y) * p.z); }
float vnoise3(vec3 p){ vec3 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(h31(i), h31(i + vec3(1.0, 0.0, 0.0)), f.x), mix(h31(i + vec3(0.0, 1.0, 0.0)), h31(i + vec3(1.0, 1.0, 0.0)), f.x), f.y),
             mix(mix(h31(i + vec3(0.0, 0.0, 1.0)), h31(i + vec3(1.0, 0.0, 1.0)), f.x), mix(h31(i + vec3(0.0, 1.0, 1.0)), h31(i + vec3(1.0, 1.0, 1.0)), f.x), f.y), f.z); }
`;
// Flesh that burns in over the fossil, bottom first, with a glowing edge.
function fleshMaterial(color) {
  const m = new THREE.MeshStandardMaterial({ color, roughness: 0.8, metalness: 0, flatShading: true });
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uDissolve = tr.u.dissolve; sh.uniforms.uMinY = tr.u.minY; sh.uniforms.uHeight = tr.u.height;
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWPos;')
      .replace('#include <skinning_vertex>', '#include <skinning_vertex>\nvWPos = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWPos;\nuniform float uDissolve; uniform float uMinY; uniform float uHeight;\n' + NOISE3)
      .replace('#include <clipping_planes_fragment>', `#include <clipping_planes_fragment>
        float dn = vnoise3(vWPos * 2.2) * 0.65 + vnoise3(vWPos * 6.0) * 0.35;
        float dh = clamp((vWPos.y - uMinY) / uHeight, 0.0, 1.0);
        float dk = mix(dn, dh, 0.45);
        if (dk > uDissolve) discard;
        float edgeGlow = smoothstep(uDissolve - 0.07, uDissolve, dk) * step(uDissolve, 1.0);`)
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += vec3(1.0, 0.45, 0.12) * edgeGlow * 4.0;');
  };
  return m;
}

async function buildTrex() {
  const sc = tr.scene;
  sc.fog = new THREE.Fog(0x050507, 16, 70);
  tr.fogA = new THREE.Color(0x050507); tr.fogB = new THREE.Color(0x3a1b16);
  tr.skyU = { uAwake: { value: 0 } };
  sc.add(new THREE.Mesh(new THREE.SphereGeometry(150, 32, 16), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, uniforms: tr.skyU,
    vertexShader: 'varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: `uniform float uAwake; varying vec3 vDir;
      void main(){ float h = vDir.y;
        vec3 hall = mix(vec3(0.04, 0.042, 0.05), vec3(0.012, 0.013, 0.018), smoothstep(-0.05, 0.5, h));
        vec3 dusk = mix(vec3(1.0, 0.46, 0.17), vec3(0.42, 0.12, 0.1), smoothstep(0.0, 0.16, h));
        dusk = mix(dusk, vec3(0.09, 0.045, 0.11), smoothstep(0.16, 0.7, h));
        dusk += vec3(1.0, 0.34, 0.07) * pow(max(0.0, dot(normalize(vDir), normalize(vec3(-0.42, 0.1, -1.0)))), 16.0) * 0.9;
        dusk = mix(dusk, vec3(0.07, 0.035, 0.03), smoothstep(0.0, -0.25, h));
        gl_FragColor = vec4(mix(hall, dusk, uAwake), 1.0); }`,
  })));
  const ground = new THREE.Mesh(new THREE.CircleGeometry(90, 48), new THREE.MeshStandardMaterial({ color: 0x15110e, roughness: 0.92 }));
  ground.rotation.x = -Math.PI / 2; sc.add(ground);
  tr.hemi = new THREE.HemisphereLight(0x9aa6b8, 0x120c08, 0.35); sc.add(tr.hemi);
  tr.spot = new THREE.SpotLight(0xfff0d8, 3.2, 0, 0.36, 0.6, 0); tr.spot.position.set(1.2, 11, 3.5); sc.add(tr.spot, tr.spot.target);
  tr.key = new THREE.DirectionalLight(0xff8a4a, 0); tr.key.position.set(-7, 5, -9); sc.add(tr.key);
  tr.fill = new THREE.DirectionalLight(0xa07cff, 0); tr.fill.position.set(7, 3, 7); sc.add(tr.fill);
  tr.front = new THREE.DirectionalLight(0xffd2a6, 0); tr.front.position.set(3, 4, 9); sc.add(tr.front);

  tr.plinth = new THREE.Group();
  const pl = new THREE.Mesh(new THREE.BoxGeometry(6.6, 0.5, 2.8), new THREE.MeshStandardMaterial({ color: 0x17181d, roughness: 0.55, transparent: true }));
  const trim = new THREE.Mesh(new THREE.BoxGeometry(6.7, 0.05, 2.9), new THREE.MeshStandardMaterial({ color: 0x6d5323, emissive: 0x2a1e08, roughness: 0.4, metalness: 0.6, transparent: true }));
  pl.position.y = 0.25; trim.position.y = 0.5; tr.plinth.add(pl, trim); sc.add(tr.plinth);
  tr.plinthMats = [pl.material, trim.material];

  tr.volcano = new THREE.Group();
  const cone = new THREE.Mesh(new THREE.CylinderGeometry(2.6, 17, 15, 9, 1, true), new THREE.MeshStandardMaterial({ color: 0x1c1210, roughness: 1, flatShading: true, transparent: true }));
  const lava = new THREE.Mesh(new THREE.CircleGeometry(2.5, 12), new THREE.MeshBasicMaterial({ color: 0xff6a1f, transparent: true, fog: false }));
  lava.rotation.x = -Math.PI / 2; cone.position.y = 7.5; lava.position.y = 15;
  tr.volcano.add(cone, lava); tr.volcano.position.set(-24, 0, -58);
  sc.add(tr.volcano); tr.volcanoMats = [cone.material, lava.material];

  // rocks only behind and beside the T. rex, never between it and the visitor
  const rockMat = new THREE.MeshStandardMaterial({ color: 0x241b16, roughness: 1, flatShading: true, transparent: true, opacity: 0 });
  for (const [x, z] of [[-14, -9], [-9, -16], [-4, -24], [3, -19], [9, -13], [15, -21], [-18, -3], [17, -6], [-11, -30], [12, -32], [-6, -12], [6, -27]]) {
    const r = new THREE.Mesh(new THREE.DodecahedronGeometry(0.5 + Math.random() * 1.2, 0), rockMat);
    r.position.set(x + (Math.random() - 0.5) * 2, 0.1, z + (Math.random() - 0.5) * 2); r.rotation.set(Math.random(), Math.random(), Math.random());
    sc.add(r);
  }
  tr.rockMat = rockMat;

  const dot = softDot();
  const EN = 280;
  tr.emberPos = new Float32Array(EN * 3); tr.emberVel = new Float32Array(EN);
  for (let i = 0; i < EN; i++) {
    tr.emberPos[i * 3] = (Math.random() - 0.5) * 30; tr.emberPos[i * 3 + 1] = Math.random() * 12; tr.emberPos[i * 3 + 2] = -Math.random() * 30 + 6;
    tr.emberVel[i] = 0.3 + Math.random() * 0.9;
  }
  const eg = new THREE.BufferGeometry(); eg.setAttribute('position', new THREE.BufferAttribute(tr.emberPos, 3));
  tr.embers = new THREE.Points(eg, new THREE.PointsMaterial({ map: dot, color: 0xff8a3c, size: 0.12, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
  sc.add(tr.embers);
  const DN = 260;
  tr.dust = { pos: new Float32Array(DN * 3), vel: new Float32Array(DN * 3), col: new Float32Array(DN * 3), life: new Float32Array(DN), next: 0, n: DN };
  for (let i = 0; i < DN; i++) tr.dust.pos[i * 3 + 1] = -50;
  const dg = new THREE.BufferGeometry();
  dg.setAttribute('position', new THREE.BufferAttribute(tr.dust.pos, 3));
  dg.setAttribute('color', new THREE.BufferAttribute(tr.dust.col, 3));
  tr.dustPts = new THREE.Points(dg, new THREE.PointsMaterial({ map: dot, size: 0.55, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
  sc.add(tr.dustPts);
  tr.smoke = [];
  for (let i = 0; i < 9; i++) {
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: dot, color: 0x3a2a24, transparent: true, opacity: 0, depthWrite: false }));
    s.userData.phase = i / 9; tr.smoke.push(s); sc.add(s);
  }

  const gltf = await new GLTFLoader().loadAsync('/static/live/trex.glb');
  const model = gltf.scene;
  const skinned = [];
  // three.js drops the dot from bone names ("BackFoot.L" becomes "BackFootL"), so keep both spellings
  model.traverse((o) => {
    if (o.isSkinnedMesh) skinned.push(o);
    if (o.isBone) { tr.bones[o.name] = o; const alias = o.name.replace(/([a-z])([LR])$/, '$1.$2'); if (alias !== o.name) tr.bones[alias] = o; }
  });
  const COLORS = { Green: '#3b4a2c', LightGreen: '#706c3d', LightYellow: '#cdb88f', Black: '#121212', Red: '#6e1f17' };
  tr.wire = new THREE.MeshBasicMaterial({ color: 0xf2e6c9, wireframe: true, transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false, fog: false });
  tr.ghost = new THREE.MeshBasicMaterial({ color: 0xd8cbb0, transparent: true, opacity: 0.08, blending: THREE.AdditiveBlending, depthWrite: false, fog: false });
  for (const m of skinned) {
    m.material = fleshMaterial(new THREE.Color(COLORS[m.material.name] || '#4b5732'));
    m.frustumCulled = false;
    for (const mat of [tr.wire, tr.ghost]) {
      const twin = new THREE.SkinnedMesh(m.geometry, mat);
      twin.bind(m.skeleton, m.bindMatrix);
      twin.frustumCulled = false;
      twin.position.copy(m.position); twin.quaternion.copy(m.quaternion); twin.scale.copy(m.scale);
      m.parent.add(twin);
    }
  }
  tr.pivot = new THREE.Group(); tr.pivot.add(model); sc.add(tr.pivot);
  model.updateMatrixWorld(true);
  let box = new THREE.Box3().setFromObject(model);
  const size = box.getSize(new THREE.Vector3());
  model.scale.multiplyScalar(6.4 / Math.max(size.x, size.z));
  model.updateMatrixWorld(true);
  box = new THREE.Box3().setFromObject(model);
  const c = box.getCenter(new THREE.Vector3());
  model.position.x -= c.x; model.position.z -= c.z; model.position.y -= box.min.y;
  model.updateMatrixWorld(true);
  box = new THREE.Box3().setFromObject(model);
  tr.modelHeight = box.max.y - box.min.y;
  tr.u.height.value = tr.modelHeight;
  const head = tr.bones.Head.getWorldPosition(new THREE.Vector3());
  const hips = (tr.bones.Hips || tr.bones.Body).getWorldPosition(new THREE.Vector3());
  const f = head.sub(hips); f.y = 0; f.normalize();
  tr.az = 0.5;
  const want = tr.az - 0.62;
  tr.pivot.rotation.y = want - Math.atan2(f.x, f.z);
  tr.fwd.set(Math.sin(want), 0, Math.cos(want));
  tr.right.crossVectors(tr.fwd, new THREE.Vector3(0, 1, 0)).normalize();
  for (const n of ['Neck', 'Head', 'FrontUpLeg.L', 'FrontUpLeg.R', 'FrontLowLeg.L', 'FrontLowLeg.R']) if (tr.bones[n]) tr.rest[n] = tr.bones[n].quaternion.clone();
  tr.mixer = new THREE.AnimationMixer(model);
  const clip = (n) => gltf.animations.find((a) => a.name.endsWith(n));
  tr.actions = { idle: tr.mixer.clipAction(clip('TRex_Idle')), walk: tr.mixer.clipAction(clip('TRex_Walk')), attack: tr.mixer.clipAction(clip('TRex_Attack')) };
  tr.walkDur = clip('TRex_Walk').duration;
  tr.actions.idle.play(); tr.actions.idle.paused = true; tr.active = tr.actions.idle;
  tr.base.set(0, 0.5, 0);
  tr.pivot.position.copy(tr.base);
  tr.u.minY.value = 0.5;
  tr.ready = true; tr.state = 'fossil';
  trLayout();
}

function trLayout() {
  const aspect = state.W / state.H;
  tr.camera.aspect = aspect; tr.camera.updateProjectionMatrix();
  tr.dist = 11.5 * Math.max(1, Math.pow(1.35 / aspect, 0.85));
}

function fadeTo(name, dur = 0.35, { once = false, scale = 1 } = {}) {
  const next = tr.actions[name], prev = tr.active;
  next.reset(); next.enabled = true; next.paused = false;
  next.setEffectiveTimeScale(scale); next.setEffectiveWeight(1);
  if (once) { next.setLoop(THREE.LoopOnce, 1); next.clampWhenFinished = true; } else next.setLoop(THREE.LoopRepeat, Infinity);
  next.play();
  if (prev && prev !== next) { prev.paused = false; prev.crossFadeTo(next, dur, false); }
  tr.active = next;
}

const _q = new THREE.Quaternion(), _pq = new THREE.Quaternion(), _pqi = new THREE.Quaternion();
const UP = new THREE.Vector3(0, 1, 0);
// Turn a bone about an axis given in world space, whatever its own axes are.
function rotateWorld(bone, axis, angle) {
  if (!bone || !angle) return;
  bone.parent.getWorldQuaternion(_pq);
  _pqi.copy(_pq).invert();
  _q.setFromAxisAngle(axis, angle);
  bone.quaternion.premultiply(_pqi.multiply(_q).multiply(_pq));
}

function emitDust(pos, count, power = 1, dir = null) {
  const d = tr.dust;
  for (let k = 0; k < count; k++) {
    const i = d.next; d.next = (d.next + 1) % d.n;
    const a = Math.random() * Math.PI * 2, sp = (0.6 + Math.random() * 1.8) * power;
    d.pos[i * 3] = pos.x + Math.cos(a) * 0.2; d.pos[i * 3 + 1] = (dir ? pos.y : 0.1) + Math.random() * 0.2; d.pos[i * 3 + 2] = pos.z + Math.sin(a) * 0.2;
    d.vel[i * 3] = dir ? dir.x * sp + Math.cos(a) * 0.3 : Math.cos(a) * sp;
    d.vel[i * 3 + 1] = dir ? 0.2 + Math.random() * 0.4 : 0.4 + Math.random() * 1.1 * power;
    d.vel[i * 3 + 2] = dir ? dir.z * sp + Math.sin(a) * 0.3 : Math.sin(a) * sp;
    d.life[i] = 1;
  }
}
function vibrate(pattern) { try { if (navigator.vibrate) navigator.vibrate(pattern); } catch (e) { /* not allowed */ } }
function footstep(boneName) {
  Sound.thud(1);
  tr.shake = Math.max(tr.shake, 0.05);
  const b = tr.bones[boneName];
  if (b) emitDust(b.getWorldPosition(_v), 16, 0.8);
  vibrate(30);
}

const _hp = new THREE.Vector3(), _tp = new THREE.Vector3(), _dir = new THREE.Vector3(), _fp = new THREE.Vector3(), _ct = new THREE.Vector3();
const raycaster = new THREE.Raycaster();
function trUpdate(dt, t) {
  const a = tr.awake, p = state.pointer;
  tr.skyU.uAwake.value = a;
  tr.scene.fog.color.copy(tr.fogA).lerp(tr.fogB, a);
  tr.scene.fog.near = lerp(16, 12, a); tr.scene.fog.far = lerp(70, 85, a);
  tr.hemi.intensity = lerp(0.35, 0.9, a);
  tr.hemi.color.setRGB(lerp(0.6, 1.0, a), lerp(0.65, 0.6, a), lerp(0.72, 0.5, a));
  tr.spot.intensity = lerp(3.2, 0.6, a);
  tr.key.intensity = 3.2 * a; tr.fill.intensity = 0.8 * a; tr.front.intensity = 1.2 * a;
  tr.embers.material.opacity = state.reduce ? 0 : a * 0.9;
  tr.volcanoMats.forEach((m) => { m.opacity = a; }); tr.volcano.visible = a > 0.01;
  tr.rockMat.opacity = a;
  tr.plinthMats.forEach((m) => { m.opacity = 1 - a; }); tr.plinth.visible = a < 0.99;
  tr.plinth.position.y = -a * 0.55;
  tr.wire.opacity = 0.55 * clamp(1 - tr.u.dissolve.value * 1.15, 0, 1);
  tr.ghost.opacity = 0.08 * clamp(1 - tr.u.dissolve.value, 0, 1);

  const ep = tr.emberPos;
  for (let i = 0; i < tr.emberVel.length; i++) {
    ep[i * 3 + 1] += tr.emberVel[i] * dt;
    ep[i * 3] += Math.sin(t * 0.7 + i) * dt * 0.25;
    if (ep[i * 3 + 1] > 13) { ep[i * 3 + 1] = 0; ep[i * 3] = (Math.random() - 0.5) * 30; ep[i * 3 + 2] = -Math.random() * 30 + 6; }
  }
  tr.embers.geometry.attributes.position.needsUpdate = true;
  for (const s of tr.smoke) {
    const k = (t * 0.05 + s.userData.phase) % 1;
    s.position.set(-24 + Math.sin(k * 6 + s.userData.phase * 9) * 2 + k * 6, 15.5 + k * 16, -58);
    s.scale.setScalar(4 + k * 14);
    s.material.opacity = a * 0.55 * Math.sin(k * Math.PI);
  }
  const d = tr.dust;
  for (let i = 0; i < d.n; i++) {
    if (d.life[i] <= 0) continue;
    d.life[i] -= dt * 0.7;
    d.vel[i * 3 + 1] -= 0.9 * dt;
    for (let k = 0; k < 3; k++) { d.vel[i * 3 + k] *= 1 - 1.6 * dt; d.pos[i * 3 + k] += d.vel[i * 3 + k] * dt; }
    const l = Math.max(0, d.life[i]) * 0.55;
    d.col[i * 3] = 0.62 * l; d.col[i * 3 + 1] = 0.46 * l; d.col[i * 3 + 2] = 0.34 * l;
    if (d.life[i] <= 0) d.pos[i * 3 + 1] = -50;
  }
  tr.dustPts.geometry.attributes.position.needsUpdate = true;
  tr.dustPts.geometry.attributes.color.needsUpdate = true;

  // the animation first, then the head, jaw and arms move on top of it
  for (const n in tr.rest) tr.bones[n].quaternion.copy(tr.rest[n]);
  tr.mixer.update(dt);
  if (tr.state === 'walking') {
    const wt = tr.actions.walk.time % tr.walkDur;
    for (const [at, foot] of [[0.08, 'BackFoot.L'], [0.08 + tr.walkDur / 2, 'BackFoot.R']]) {
      if ((tr.walkPrev < at && wt >= at) || (tr.walkPrev > wt && wt >= at)) footstep(foot);
    }
    tr.walkPrev = wt;
  }
  tr.thinkingS = follow(tr.thinkingS || 0, tr.thinking, 4, dt);
  tr.listenS = follow(tr.listenS || 0, tr.listening, 5, dt);
  tr.snort = Math.max(0, tr.snort - dt * 1.1);
  tr.wiggle = follow(tr.wiggle, tr.wiggleOn ? 1 : 0, 3, dt);
  if (tr.state === 'alive' || tr.state === 'walking') {
    let nx = p.x, ny = p.y;
    if (tr.lookAt && performance.now() < tr.lookUntil) { nx = tr.lookAt.x; ny = tr.lookAt.y; }
    raycaster.setFromCamera({ x: nx * 0.8, y: ny * 0.6 }, tr.camera);
    _tp.copy(raycaster.ray.origin).addScaledVector(raycaster.ray.direction, 5);
    tr.bones.Head.getWorldPosition(_hp);
    _dir.copy(_tp).sub(_hp);
    const yawT = clamp(Math.atan2(tr.fwd.z * _dir.x - tr.fwd.x * _dir.z, tr.fwd.x * _dir.x + tr.fwd.z * _dir.z), -0.7, 0.7);
    const pitchT = clamp(Math.atan2(_dir.y, Math.hypot(_dir.x, _dir.z)), -0.3, 0.35);
    const w = tr.roaring ? 0.25 : 1;
    tr.look.yaw = follow(tr.look.yaw, yawT * w + tr.listenS * 0.1, 3.5, dt);
    tr.look.pitch = follow(tr.look.pitch, pitchT * w - tr.listenS * 0.08 + tr.thinkingS * 0.14, 3.5, dt);
    rotateWorld(tr.bones.Neck, UP, tr.look.yaw * 0.45);
    rotateWorld(tr.bones.Head, UP, tr.look.yaw * 0.55 + Math.sin(t * 17) * 0.22 * tr.snort + (talking('tr') ? Math.sin(t * 5.1) * Sound.level * 0.05 : 0));
    rotateWorld(tr.bones.Head, tr.right, tr.look.pitch * 0.6 + tr.listenS * Math.sin(t * 13) * 0.02);
    // In this model the lower jaw is skinned to the neck, so tipping the neck down
    // and the head up by the same amount drops the jaw while the skull stays level.
    tr.jaw = follow(tr.jaw, Math.max(talking('tr') ? mouth.open : 0, tr.chomp), 26, dt);
    const A = tr.roaring ? 0.55 : 0.34;
    rotateWorld(tr.bones.Neck, tr.right, -tr.jaw * A * 0.55);
    rotateWorld(tr.bones.Head, tr.right, tr.jaw * A);
    if (tr.wiggle > 0.01) {
      for (const [n, ph, amp] of [['FrontUpLeg.L', 0, 0.5], ['FrontUpLeg.R', 1.4, 0.5], ['FrontLowLeg.L', 0.7, 0.45], ['FrontLowLeg.R', 2.1, 0.45]]) {
        rotateWorld(tr.bones[n], tr.right, Math.sin(t * 11 + ph) * amp * tr.wiggle);
      }
    }
  }

  // the camera keeps a low, heroic angle and moves in on whatever the answer is about
  tr.shake *= Math.exp(-dt * 3.2);
  const s = state.reduce ? 0 : tr.shake;
  const fo = tr.focus;
  fo.k = follow(fo.k, fo.target, 1.8, dt);
  _ct.set(tr.pivot.position.x * 0.5, tr.modelHeight * 0.6 + tr.pivot.position.y * 0.5, tr.pivot.position.z * 0.5);
  let dist = tr.dist, az = tr.az + p.x * 0.12, camH = 1.15 + p.y * 0.35;
  if (fo.def && fo.k > 0.001) {
    tr.bones[fo.def.bone].getWorldPosition(_fp);
    _ct.lerp(_fp, fo.k);
    dist = lerp(dist, fo.def.dist, fo.k);
    az = lerp(az, tr.az + fo.def.az + p.x * 0.06, fo.k);
    camH = lerp(camH, _fp.y + fo.def.h, fo.k);
  }
  tr.camera.position.set(_ct.x + Math.sin(az) * dist + (Math.random() - 0.5) * s, camH + (Math.random() - 0.5) * s, _ct.z + Math.cos(az) * dist + (Math.random() - 0.5) * s);
  tr.camera.lookAt(_ct);
}

// The fossil turns to flesh, steps off its plinth and walks towards the visitor.
export async function trWake() {
  if (tr.state !== 'fossil') return;
  tr.state = 'waking';
  Sound.sweep(2.8, 50, 160, 0.7, 'lowpass');
  tr.shake = 0.06;
  await tween(2600, (k) => {
    tr.u.dissolve.value = k * 1.08;
    tr.awake = smooth(clamp((k - 0.15) / 0.85, 0, 1));
    tr.pivot.position.y = tr.base.y * (1 - tr.awake);
    tr.u.minY.value = tr.pivot.position.y;
  });
  tr.actions.idle.paused = false;
  tr.state = 'walking'; tr.walkPrev = 0;
  fadeTo('walk', 0.5);
  const from = tr.pivot.position.clone(), to = from.clone().addScaledVector(tr.fwd, 2.4);
  await tween(2900, (k) => { tr.pivot.position.lerpVectors(from, to, k); });
  tr.state = 'alive';
  fadeTo('idle', 0.5);
  await wait(450);
}

// The roar's body language; app.js plays the sound itself.
export async function trRoar() {
  tr.roaring = true;
  fadeTo('attack', 0.2, { once: true, scale: 0.5 });
  tr.shake = 0.28;
  for (const foot of ['BackFoot.L', 'BackFoot.R']) if (tr.bones[foot]) emitDust(tr.bones[foot].getWorldPosition(_v), 40, 1.6);
  vibrate([90, 40, 220]);
  await wait(state.reduce ? 400 : 1950);
  fadeTo('idle', 0.45);
  tr.roaring = false;
}
export function trSnort(growlUrl) {
  tr.snort = 1;
  if (growlUrl) Sound.playUrl(growlUrl, { voice: false, gain: 0.35, offset: 0.1, duration: 0.7, rate: 0.7 });
  Sound.burst({ type: 'lowpass', freq: 600, gain: 0.4, len: 0.5 });
  if (tr.bones.Head_end) emitDust(tr.bones.Head_end.getWorldPosition(new THREE.Vector3()), 30, 1.2, tr.fwd);
}
export async function trChomp() {
  await tween(260, (k) => { tr.chomp = Math.sin(k * Math.PI * 0.5); });
  await tween(120, (k) => { tr.chomp = 1 - k; });
  tr.chomp = 0;
  Sound.burst({ type: 'highpass', freq: 1600, gain: 0.35, len: 0.08 });
  Sound.thud(0.5);
  tr.shake = Math.max(tr.shake, 0.1);
}
export function trFocus(name) {
  if (name && FOCUS[name]) { tr.focus.def = FOCUS[name]; tr.focus.target = 1; } else tr.focus.target = 0;
  tr.wiggleOn = name === 'arms';
}
// The body part under a tap, with a question about it, or null.
export function trRegionAt(px, py) {
  if (!tr.ready || tr.state !== 'alive') return null;
  let best = null, bestD = Infinity;
  for (const reg of REGIONS) for (const n of reg.bones) {
    const b = tr.bones[n];
    if (!b) continue;
    b.getWorldPosition(_v).project(tr.camera);
    const dd = Math.hypot((_v.x * 0.5 + 0.5) * state.W - px, (-_v.y * 0.5 + 0.5) * state.H - py);
    if (dd < bestD) { bestD = dd; best = reg; }
  }
  if (!best || bestD > Math.max(70, state.W * 0.09)) return null;
  tr.lookAt = { x: (px / state.W) * 2 - 1, y: -((py / state.H) * 2 - 1) };
  tr.lookUntil = performance.now() + 1800;
  tr.shake = Math.max(tr.shake, 0.06);
  return best.q;
}

// ------------------------------------------------------------------ time travel
const warp = { stars: Array.from({ length: 240 }, () => ({ a: Math.random() * Math.PI * 2, r: Math.random(), v: 0.4 + Math.random() * 1.2 })) };
// k runs from 0 to 1; `back` is true when travelling into the past.
export function drawWarp(k, back) {
  if (!warpCtx) return;
  const c = warpCtx, w = warpCanvas.width, h = warpCanvas.height, cx = w / 2, cy = h / 2, R = Math.hypot(cx, cy);
  const env = smooth(clamp(k / 0.18, 0, 1)) * (1 - smooth(clamp((k - 0.82) / 0.18, 0, 1)));
  warpCanvas.style.opacity = String(env);
  c.globalCompositeOperation = 'source-over';
  c.fillStyle = 'rgba(4, 4, 8, 0.38)'; c.fillRect(0, 0, w, h);
  c.globalCompositeOperation = 'lighter';
  const p = back ? k : 1 - k;
  const speed = 0.4 + Math.sin(k * Math.PI) * 2.6;
  c.lineCap = 'round';
  for (const s of warp.stars) {
    s.r += s.v * speed * 0.016;
    if (s.r > 1.15) { s.r = Math.random() * 0.15; s.a = Math.random() * Math.PI * 2; }
    const r0 = s.r * s.r * R, r1 = r0 + (0.02 + speed * 0.05) * R * s.r;
    c.strokeStyle = `rgba(${Math.round(lerp(150, 255, p))}, ${Math.round(lerp(185, 130, p))}, ${Math.round(lerp(255, 70, p))}, ${0.25 + s.r * 0.7})`;
    c.lineWidth = (0.6 + s.r * 2.2) * DPR;
    c.beginPath(); c.moveTo(cx + Math.cos(s.a) * r0, cy + Math.sin(s.a) * r0); c.lineTo(cx + Math.cos(s.a) * r1, cy + Math.sin(s.a) * r1); c.stroke();
  }
  const flash = Math.exp(-Math.pow((k - 0.5) / 0.045, 2));
  if (flash > 0.01) { c.globalCompositeOperation = 'source-over'; c.fillStyle = `rgba(255, 240, 220, ${flash * 0.9})`; c.fillRect(0, 0, w, h); }
}
export function clearWarp() {
  if (!warpCtx) return;
  warpCanvas.style.opacity = '0';
  warpCtx.clearRect(0, 0, warpCanvas.width, warpCanvas.height);
}
