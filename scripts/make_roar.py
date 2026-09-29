"""Synthesize the T. rex roar used on the phone page.

    python scripts/make_roar.py                      # writes personas/t-rex/sounds/roar.wav
    python scripts/make_roar.py --style rumble --out other.wav

No recording of a real animal is used: the sound is built from scratch, so it
has no licence restrictions. Nobody knows what Tyrannosaurus sounded like. Our
sources only say it heard low sounds best and that low-frequency sounds were
important to tyrannosaurs, so the roar is deep, and the persona says it is a
sound the museum made up.

How it's built: a buzzing source (many harmonics of a low, wobbling pitch that
rises and falls), roughened by fast amplitude flutter and a half-pitch
undertone, mixed with breathy noise, shaped by three resonances like a large
throat and mouth, and gently distorted.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
SR = 24000

STYLES = {
    # pitch contour (seconds, Hz), flutter rate and depth, noise amount, formants (Hz), drive
    "roar": {"contour": [(0, 75), (0.35, 120), (1.1, 100), (2.0, 70), (2.8, 48)],
             "flutter": (30, 0.55), "noise": 0.45, "formants": (380, 850, 1600), "drive": 2.6},
    "rumble": {"contour": [(0, 45), (0.5, 62), (1.6, 55), (2.6, 38)],
               "flutter": (22, 0.45), "noise": 0.25, "formants": (250, 520, 1100), "drive": 2.0},
    "mixed": {"contour": [(0, 60), (0.4, 95), (1.2, 82), (2.1, 58), (2.8, 40)],
              "flutter": (26, 0.5), "noise": 0.35, "formants": (300, 700, 1350), "drive": 2.3},
}


def smooth_noise(rng, n, cutoff_hz):
    """Random wobble between -1 and 1 that changes about `cutoff_hz` times a second."""
    points = max(4, int(n / SR * cutoff_hz) + 2)
    anchors = rng.uniform(-1, 1, points)
    return np.interp(np.linspace(0, points - 1, n), np.arange(points), anchors)


def resonator(x, freq, q):
    """Two-pole band-pass filter (a single formant)."""
    w = 2 * np.pi * freq / SR
    alpha = np.sin(w) / (2 * q)
    b0, b2 = alpha, -alpha
    a0, a1, a2 = 1 + alpha, -2 * np.cos(w), 1 - alpha
    b0, b2, a1, a2 = b0 / a0, b2 / a0, a1 / a0, a2 / a0
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i, xi in enumerate(x):
        yi = b0 * xi + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, xi, y1, yi
        y[i] = yi
    return y


def lowpass(x, cutoff_hz, passes=2):
    """Gentle low-pass (one-pole, applied `passes` times) to take the hiss off."""
    a = np.exp(-2 * np.pi * cutoff_hz / SR)
    for _ in range(passes):
        y = np.zeros_like(x)
        prev = 0.0
        for i, xi in enumerate(x):
            prev = (1 - a) * xi + a * prev
            y[i] = prev
        x = y
    return x


def make(style, seed=7):
    spec = STYLES[style]
    duration = spec["contour"][-1][0]
    n = int(SR * duration)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)

    times, pitches = zip(*spec["contour"])
    f0 = np.interp(t, times, pitches)
    f0 *= 1 + 0.07 * smooth_noise(rng, n, 5)          # slow, uneven wobble
    f0 *= 1 + 0.025 * np.sin(2 * np.pi * 6.0 * t)     # vibrato
    phase = 2 * np.pi * np.cumsum(f0) / SR

    source = np.zeros(n)
    for k in range(1, int(5000 / max(pitches)) + 1):  # band-limited buzz
        source += np.sin(k * phase) / k ** 0.8
    source += 0.5 * np.sin(phase / 2)                 # undertone for roughness
    rate, depth = spec["flutter"]
    source *= 1 + depth * np.sin(2 * np.pi * rate * t + 4 * smooth_noise(rng, n, 3))
    source /= np.max(np.abs(source))

    breath = lowpass(rng.normal(0, 1, n), 1200)
    breath /= np.max(np.abs(breath))
    voiced = source + spec["noise"] * breath * (0.6 + 0.4 * np.abs(source))

    f1, f2, f3 = spec["formants"]
    shaped = (1.0 * resonator(voiced, f1, 3.0) + 0.7 * resonator(voiced, f2, 4.0)
              + 0.35 * resonator(voiced, f3, 5.0) + 0.05 * voiced)

    envelope = np.interp(t, [0, 0.2, 0.5, duration - 0.9, duration],
                         [0, 0.85, 1.0, 0.8, 0]) ** 1.3
    audio = np.tanh(spec["drive"] * shaped / np.max(np.abs(shaped))) * envelope
    audio = lowpass(audio, 3200)
    body_phase = 2 * np.pi * np.cumsum(np.interp(t, times, pitches) / 2) / SR
    audio += 0.2 * np.max(np.abs(audio)) * np.sin(body_phase) * envelope  # deep body an octave down
    fade = int(0.01 * SR)
    audio[:fade] *= np.linspace(0, 1, fade)
    audio[-fade:] *= np.linspace(1, 0, fade)
    return (0.9 * audio / np.max(np.abs(audio))).astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description="Synthesize the T. rex roar.")
    parser.add_argument("--style", choices=sorted(STYLES), default="roar")
    parser.add_argument("--out", default=str(ROOT / "personas" / "t-rex" / "sounds" / "roar.wav"))
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, make(args.style), SR, subtype="PCM_16")
    print(f"wrote {out} ({args.style})")


if __name__ == "__main__":
    sys.exit(main())
