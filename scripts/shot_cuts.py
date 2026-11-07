#!/usr/bin/env python3
"""Find the camera cuts inside a span of a video (e.g. an official music video).

usage: shot_cuts.py video.mp4 --start 34.4 --dur 7.4 [--fps 24]

Prints each cut as a frame index (relative to --start, at the video's own fps) and a video time. Use the cuts
to (1) re-centre a vertical crop on the subject per shot and (2) avoid frame-blending across a cut.
Also prints a per-shot horizontal brightness centroid as a rough hint of where the lit subject sits (0-1).
"""
import argparse, subprocess
import numpy as np

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video'); ap.add_argument('--start', type=float, default=0.0); ap.add_argument('--dur', type=float, default=10.0)
    ap.add_argument('--fps', type=float, default=24.0); ap.add_argument('--thresh', type=float, default=4.0)
    a = ap.parse_args()
    w, h = 160, 90
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(a.start), '-i', a.video, '-t', str(a.dur), '-an',
                          '-vf', f'scale={w}:{h}', '-pix_fmt', 'gray', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    d = np.abs(np.diff(fr, axis=0)).mean((1, 2)); med = np.median(d)
    cuts = [i + 1 for i, v in enumerate(d) if v > a.thresh * med and v > 8]
    print(f'{len(fr)} frames read; median frame change {med:.2f}')
    bounds = [0] + cuts + [len(fr)]
    for j in range(len(bounds) - 1):
        s0, s1 = bounds[j], bounds[j + 1]
        m = fr[s0:s1].mean(0); col = m.mean(0); col = col - col.min()
        cx = float((col * np.arange(w)).sum() / (col.sum() + 1e-6) / w)
        label = f'cut at frame {s0} (t={a.start + s0 / a.fps:.3f}s)' if j else 'start'
        print(f'{label:34s} shot {s0}-{s1 - 1}  brightness centroid x~{cx:.2f}')

if __name__ == '__main__':
    main()
