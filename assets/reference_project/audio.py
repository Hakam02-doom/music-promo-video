#!/usr/bin/env python3
"""Sound mix for v5 (57.25 s).

Songs
- "Raw Rich Rare" (Arjan Dhillon, MXRCI) plays from 0:00 in sync with picture. Very low (-22 dB) until
  the bar before its drop, then an accelerating climb to a loud, softly limited level at 22.70 s.
- Handoff to "National Treasures" (Drake) as a smooth breakdown: NT's downbeat at song time 19.299 s is laid
  onto RRR's downbeat at film 30.283 s (SWAP). Over RRR's last bar it darkens (low-pass) and drops ~26 dB,
  with a soft echo drifting away; NT fades in underneath (-40 -> -22 dB) with its bass filtered out, then
  climbs from low to high (-22 -> -4 dB) through its build while the bass returns over the first bar,
  and hits its own drop at 0:27.7 (film 38.67 s).
- From the diamonds lifting off (52.6 s) to the end NT goes from high to low (-34 dB) and darkens.

SFX
- SaaS SFX Pack cues on taps, zooms and moves; the diamond "ting" (freesound_community-diamond-slot)
  on each of the first eight diamonds, on every sixth diamond of the pour (varied pitch and pan),
  when the glove locks, and when the logo forms.

Writes out/mix_full.wav (songs + SFX) and out/mix_sfx_only.wav (same SFX, no songs).
"""
import subprocess, os, sys, wave
import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import render as R  # timeline constants and the diamond landing schedule

A = os.path.join(ROOT, 'src', 'audio')
SR = 48000
DUR = R.DUR
N = int(round(SR * DUR))
t = np.arange(N) / SR
BEAT = R.BEAT
SWAP, NT_OFF, NT_BEAT = R.SWAP, R.NT_OFF, R.NT_BEAT

def load(path, start=0.0, seconds=None):
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(start), '-i', path] + (['-t', str(seconds)] if seconds else []) + \
          ['-f', 'f32le', '-ac', '2', '-ar', str(SR), '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()
def db(x): return 10 ** (np.asarray(x) / 20)
def cos_ramp(x): x = np.clip(x, 0, 1); return 0.5 - 0.5 * np.cos(np.pi * x)
def place(buf, x, start_s):
    s = int(round(start_s * SR)); a, b = max(s, 0), min(s + len(x), N)
    if b > a: buf[a:b] += x[a - s:b - s]

def sweep(x, kind, f_of_t, t0, block=512):
    """2nd-order Butterworth filter whose cutoff follows f_of_t(time) (block-wise, state carried)."""
    y = np.empty_like(x); zi = None
    for i in range(0, len(x), block):
        fc = float(np.clip(f_of_t(t0 + i / SR), 20, SR * 0.45))
        sos = butter(2, fc, btype=kind, fs=SR, output='sos')
        if zi is None: zi = np.stack([sosfilt_zi(sos)] * x.shape[1], axis=-1) * x[0]
        y[i:i + block], zi = sosfilt(sos, x[i:i + block], axis=0, zi=zi)
    return y

# ---------------------------------------------------------------- Raw Rich Rare (film 0 -> SWAP + 0.9)
RRR_END = SWAP + 0.9
rrr = load(os.path.join(A, 'raw_rich_rare.mp3'), 0, RRR_END)
rrr = np.pad(rrr, ((0, max(0, int(RRR_END * SR) - len(rrr))), (0, 0)))[:int(RRR_END * SR)]
tr = np.arange(len(rrr)) / SR
k = np.clip((tr - 20.177) / (R.D_DROP - 20.177), 0, 1) ** 2.2
rrr *= db(-22.0 + 19.0 * k)[:, None]                              # -22 dB -> -3 dB into the drop
# ---- the handoff, a smooth breakdown: RRR fades down and darkens over its last bar, NT rises from low to high
F0 = SWAP - 4 * BEAT                                              # 27.757: RRR's last downbeat before the swap
seg = slice(int(F0 * SR), len(rrr))
rrr[seg] = sweep(rrr[seg], 'lowpass', lambda s: 16000 * (500 / 16000) ** np.clip((s - F0) / (SWAP + 0.6 - F0), 0, 1) ** 1.2, F0)  # gets darker
rrr *= db(-26.0 * cos_ramp((tr - F0) / (SWAP + 0.5 - F0)))[:, None]                                            # and quieter
rrr *= (1 - cos_ramp((tr - SWAP) / 0.85))[:, None]
# a soft echo of its last half-beat drifts away under the new song
echo = np.zeros((int(5.0 * SR), 2), np.float32)
src = rrr[int((SWAP - 0.33) * SR):int(SWAP * SR)].copy()
for r in range(1, 6):
    e = sweep(src, 'lowpass', lambda s, r=r: 3500 / (1.4 ** r), 0) * (0.5 ** r)
    if r % 2: e = e[:, ::-1]                                       # ping-pong
    o = int(((r - 1) * NT_BEAT) * SR); echo[o:o + len(e)] += e
songs = np.zeros((N, 2), np.float32)
songs[:len(rrr)] += rrr
place(songs, echo, SWAP)

# ---------------------------------------------------------------- National Treasures: low -> high, and high -> low at the end
NT_IN = SWAP - R.NT_BAR                                           # 28.42: fades in under RRR's fade
nt = load(os.path.join(A, 'national_treasures.mp3'), NT_IN - NT_OFF, DUR - NT_IN + 0.05)
tn = NT_IN + np.arange(len(nt)) / SR
NT_FULL_BASS = SWAP + R.NT_BAR                                    # bass returns gradually over the first bar
nt = sweep(nt, 'highpass', lambda s: 1000 * (20 / 1000) ** np.clip((s - NT_IN) / (NT_FULL_BASS - NT_IN), 0, 1) ** 1.4, NT_IN)
END0, END1 = R.LIFT, DUR - 0.2                                    # 52.6 -> end: high to low
nt[int((END0 - NT_IN) * SR):] = sweep(nt[int((END0 - NT_IN) * SR):], 'lowpass',
                                      lambda s: 18000 * (900 / 18000) ** np.clip((s - END0) / (END1 - END0), 0, 1), END0)  # fades into the distance
ND0 = R.NT_DROP - 0.75                                            # inside Drake's pre-drop pause
g = np.empty_like(tn)
m0 = tn < SWAP;              g[m0] = -40.0 + 18.0 * cos_ramp((tn[m0] - NT_IN) / (SWAP - NT_IN))          # -40 -> -22 (low)
m1 = (tn >= SWAP) & (tn < ND0); g[m1] = -22.0 + 18.0 * ((tn[m1] - SWAP) / (ND0 - SWAP)) ** 1.6          # climbs to -4 (high)
m2 = tn >= ND0;              g[m2] = -4.0 - 2.0 * cos_ramp((tn[m2] - ND0) / 0.6)                        # -6 for the loud drop
g -= 34.0 * cos_ramp((tn - END0) / (END1 - END0))                                                         # high -> low at the end
nt *= (db(g) * np.clip((DUR - 0.02 - tn) / 0.2, 0, 1))[:, None]
place(songs, nt, NT_IN)

# ---------------------------------------------------------------- SFX
cache = {}
def sfx_file(name):
    if name not in cache: cache[name] = load(os.path.join(A, name), 0, 6)
    return cache[name]
def pitch(x, f):  # resample: f > 1 = higher and shorter
    n = int(len(x) / f); idx = np.arange(n) * f
    return np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(2)], 1).astype(np.float32)
def pan(x, p):    # p in [-1, 1]
    a = (p + 1) * np.pi / 4
    return x * np.array([np.cos(a), np.sin(a)], np.float32) * np.sqrt(2)

sfx = np.zeros((N, 2), np.float32)
CLICK, W2, W3, POP, RUMBLE, RISER, BLEEP, DIAMOND = ('5. Click.mp3', '2..mp3', '3..mp3', '6..mp3', '4..mp3', '1. Riser.mp3',
                                                    '8. Bleep Bloop.wav', 'diamond_slot.mp3')
PEAK = {CLICK: 0.05, W2: 0.40, W3: 0.15, POP: 0.40, RUMBLE: 1.15, RISER: 0.65, BLEEP: 0.05, DIAMOND: 0.062}
def cue(name, at, gain, f=1.0, p=0.0):
    x = sfx_file(name)
    if f != 1.0: x = pitch(x, f)
    if p: x = pan(x, p)
    place(sfx, x * db(gain), at - PEAK[name] / f)

# part one (Raw Rich Rare)
cue(BLEEP, 0.55, -12)
cue(CLICK, R.TAP_LOGO, -3); cue(W2, 4.55, -3)
for i in range(6): cue(CLICK, 5.02 + i * BEAT / 2, -13)
cue(CLICK, R.TAP_SAROOR, -3); cue(W3, 9.80, -5)
cue(W2, 12.25, -8)
for m in R.CAR_MOVES: cue(POP, m + 0.25, -15)
cue(W3, 14.90, -7)
cue(CLICK, R.TAP_HEART, -3); cue(BLEEP, R.TAP_HEART + 0.05, -11)
cue(RUMBLE, 21.50, -9); cue(RISER, R.D_DROP, -2)
cue(W2, 25.90, -6)
# the handoff
cue(W2, 29.35, -12)                      # dive through the chain
cue(RISER, SWAP, -16)                    # a soft lift into the new song
cue(DIAMOND, SWAP + R.NT_BAR / 2, -18, 0.7)   # a small sparkle as the new song settles
# diamonds
rng = np.random.default_rng(3)
first_pitch = [1.0, 1.12, 0.94, 1.19, 1.06, 0.89, 1.26, 1.0]
for kk, i in enumerate(R.D_ORDER):
    L = R.LAND[i]
    if kk < R.FIRST:
        cue(DIAMOND, L, -10, first_pitch[kk], rng.uniform(-0.5, 0.5))
    elif kk % 6 == 0:
        cue(DIAMOND, L, -19, rng.uniform(0.85, 1.35), rng.uniform(-0.8, 0.8))
cue(DIAMOND, R.GLOVE_FULL[1], -6, 0.75)   # the glove locks
cue(RISER, R.NT_DROP, -4)
cue(DIAMOND, R.NT_DROP, -6, 0.6)
# player + finale
cue(W3, R.D2_IN[0] + 0.25, -8)
cue(CLICK, R.TAP_HEART2, -3); cue(BLEEP, R.TAP_HEART2 + 0.05, -11)
for b in range(int((R.UI2_OUT - 41.8) / NT_BEAT)):
    cue(DIAMOND, 41.8 + b * NT_BEAT, -24, rng.uniform(1.1, 1.5), rng.uniform(-0.7, 0.7))   # glints
cue(W3, R.HOLE[0] + 0.55, -6)           # dive through the OK sign
cue(POP, R.MV_FULL_IN[0] + 0.3, -14)      # the video opens
cue(W2, R.SPLIT[0] + 0.25, -8)            # video reframes, cover rises
for b in range(int((R.SPLIT_OUT[0] - 49.8) / NT_BEAT)):
    cue(DIAMOND, 49.8 + b * NT_BEAT, -24, rng.uniform(1.1, 1.5), rng.uniform(-0.7, 0.7))   # glints on the cover
cue(W3, R.SPLIT_OUT[0] + 0.35, -8)        # panel away, cover recentres
cue(W2, R.LIFT + 0.35, -5); cue(RUMBLE, R.LIFT + 0.9, -11)
cue(DIAMOND, R.LOGO_END, -5, 0.8); cue(BLEEP, R.LOGO_END + 0.08, -12)

def soft_limit(x, ceiling=0.95): return ceiling * np.tanh(x / ceiling)
full = soft_limit(songs + sfx)
norm = db(-1.0) / np.max(np.abs(full))
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
for name, x in [('mix_full.wav', full * norm), ('mix_sfx_only.wav', soft_limit(sfx) * norm)]:
    with wave.open(os.path.join(ROOT, 'out', name), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())
print('norm %.2f dB' % (20 * np.log10(norm)))
