#!/usr/bin/env python3
"""Beat grid, downbeats, energy and drop for a song window.

usage: beat_grid.py song.mp3 [--start 10] [--end 48] [--json out.json]

Prints: tempo (and its double/half), beat phase, downbeats, the strongest onsets, RMS per 0.5 s, and the
largest sudden energy jump (usually the drop). Needs ffmpeg and numpy.

Tip: when a track has a half-time feel the tempo may come out halved (e.g. 64.5 instead of 129). Check the
spacing of the strongest onsets: the big hits recur once per bar.
"""
import argparse, json, subprocess
import numpy as np

def decode(path, sr=22050):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32), sr

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('audio'); ap.add_argument('--start', type=float, default=0.0); ap.add_argument('--end', type=float)
    ap.add_argument('--json')
    a = ap.parse_args()
    x, sr = decode(a.audio)
    end = a.end if a.end else len(x) / sr
    seg = x[int(a.start * sr):int(end * sr)]
    hop, n = 256, 1024
    fr = np.lib.stride_tricks.sliding_window_view(seg, n)[::hop] * np.hanning(n)
    Sp = np.log1p(10 * np.abs(np.fft.rfft(fr, axis=1)))
    f = np.fft.rfftfreq(n, 1 / sr)
    flux = np.maximum(0, np.diff(Sp, axis=0)).sum(1)
    low = np.maximum(0, np.diff(Sp[:, f < 150], axis=0)).sum(1)
    rate = sr / hop
    best = None
    for bpm in np.arange(60, 180, 0.05):
        per = 60 / bpm
        for ph in np.arange(0, per, 0.01):
            idx = (np.arange(ph, end - a.start, per) * rate).astype(int); idx = idx[idx < len(flux)]
            sc = flux[idx].mean()
            if best is None or sc > best[0]: best = (sc, bpm, ph)
    _, bpm, ph = best
    per = 60 / bpm
    beats = np.arange(a.start + ph, end, per)
    lowsc = [low[((beats[k::4] - a.start) * rate).astype(int).clip(0, len(low) - 1)].mean() for k in range(4)]
    k0 = int(np.argmax(lowsc))
    downbeats = beats[k0::4]
    fn = flux / (flux.max() + 1e-9); tt = np.arange(len(fn)) / rate + a.start
    peaks = sorted([(float(fn[i]), float(tt[i])) for i in range(1, len(fn) - 1) if fn[i] > 0.45 and fn[i] >= fn[i - 1] and fn[i] >= fn[i + 1]], reverse=True)[:16]
    rms = [(round(s, 1), round(float(20 * np.log10(np.sqrt(np.mean(x[int(s * sr):int((s + .5) * sr)] ** 2)) + 1e-9)), 1))
           for s in np.arange(a.start, end - 0.5, 0.5)]
    # drop: the moment where the next half-second is loudest relative to the second before it
    h = int(sr * 0.05)
    e = 20 * np.log10(np.array([np.sqrt(np.mean(seg[i:i + h] ** 2)) for i in range(0, len(seg) - h, h)]) + 1e-6)
    jump = np.full(len(e), -99.0)
    for i in range(20, len(e) - 10): jump[i] = e[i:i + 10].mean() - e[i - 20:i].mean()
    i = int(np.argmax(jump))
    j0, j1 = max(1, i - 5), min(len(e) - 1, i + 5)                      # refine to the sharpest step nearby
    k = j0 + int(np.argmax(np.diff(e[j0 - 1:j1])))
    drop = float(a.start + k * h / sr)
    out = {'bpm': round(float(bpm), 2), 'bpm_double': round(float(bpm * 2), 2), 'bpm_half': round(float(bpm / 2), 2),
           'beat_s': round(per, 4), 'bar_s': round(per * 4, 4),
           'downbeats': [round(float(v), 3) for v in downbeats], 'beats': [round(float(v), 3) for v in beats],
           'strong_onsets': [round(t, 3) for _, t in sorted(peaks, key=lambda p: p[1])], 'largest_energy_jump_s': round(drop, 3),
           'rms_db_per_half_second': rms}
    print(f"tempo ~{out['bpm']} BPM (or {out['bpm_double']} / {out['bpm_half']}); beat {out['beat_s']} s, bar {out['bar_s']} s")
    print('downbeats:', out['downbeats'])
    print('strong onsets:', out['strong_onsets'])
    print('largest energy jump (likely drop):', out['largest_energy_jump_s'])
    print('RMS dB / 0.5 s:', ' '.join(f'{t}:{v:.0f}' for t, v in rms))
    if a.json: json.dump(out, open(a.json, 'w'), indent=1)

if __name__ == '__main__':
    main()
