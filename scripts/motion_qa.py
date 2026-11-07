#!/usr/bin/env python3
"""Motion QA for a rendered video: jumps, stop-motion steps, freezes and dark frames.

usage: motion_qa.py final.mp4 [--fps 60] [--stepped 15]

Compares consecutive frames on a blurred thumbnail (so film grain doesn't count). Reports:
  - spikes: frames whose change is far above both neighbours. Spikes spaced exactly fps/stepped frames apart are
    labelled 'step' (intentional stop-motion entries); everything else is listed for you to inspect.
  - near-identical consecutive frames (freezes; a final fade to black is expected)
  - frames darker than the background (mean < 8/255), e.g. dives into black
  - the largest frame-to-frame changes (fast zooms, footage cuts)
"""
import argparse
import cv2
import numpy as np

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video'); ap.add_argument('--fps', type=float, default=60.0); ap.add_argument('--stepped', type=float, default=15.0)
    a = ap.parse_args()
    cap = cv2.VideoCapture(a.video); prev = None; d = []; lum = []
    while True:
        ok, f = cap.read()
        if not ok: break
        s = cv2.GaussianBlur(cv2.resize(f, (135, 240), interpolation=cv2.INTER_AREA).astype(np.float32), (0, 0), 1.5)
        lum.append(float(f.mean()))
        if prev is not None: d.append(float(np.abs(s - prev).mean()))
        prev = s
    d = np.array(d); n = len(lum)
    print(f'frames {n}  median change {np.median(d):.3f}  max {d.max():.2f}')
    step = a.fps / a.stepped
    spikes = [i + 1 for i in range(1, len(d) - 1) if d[i] > 2.2 * max(d[i - 1], d[i + 1]) and d[i] > 1.0]
    # stepped (stop-motion) entries change only on the global step grid: frame index is a multiple of fps/stepped
    steps = {i for i in spikes if abs(i / step - round(i / step)) < 0.01 and d[i - 1] < 10}
    other = [i for i in spikes if i not in steps]
    print(f'stop-motion steps: {len(steps)} frames (spacing {step:g})')
    print('other spikes to inspect:', [(i, round(i / a.fps, 2), round(d[i - 1], 2)) for i in other])
    frozen = [i + 1 for i in range(len(d)) if d[i] < 0.02]
    print('near-identical consecutive frames:', len(frozen), frozen[:12], '...' if len(frozen) > 12 else '')
    dark = [i for i, v in enumerate(lum) if v < 8]
    if dark:
        runs, s0 = [], dark[0]
        for p, q in zip(dark, dark[1:] + [None]):
            if q != p + 1: runs.append((round(s0 / a.fps, 2), round(p / a.fps, 2))); s0 = q
        print('dark frame runs (s):', runs)
    top = np.argsort(d)[-8:][::-1]
    print('largest changes:', [(int(i + 1), round(float((i + 1) / a.fps), 2), round(float(d[i]), 1)) for i in top])

if __name__ == '__main__':
    main()
