#!/usr/bin/env python3
"""Offset between a song file and the audio of its music video (or any two recordings of the same audio).

usage: av_sync.py song.mp3 musicvideo.mp4 [--windows 20-50,60-90,120-150]

Prints, per window: video_time = song_time + offset, with a correlation score (1.0 = perfect).
Use the offset so footage stays lip-synced with the song: video_time = film_t - song_offset_in_film + offset.
"""
import argparse, subprocess
import numpy as np
from scipy.signal import fftconvolve

def decode(path, sr=8000):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vn', '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)

def env(x, sr=8000):
    k = int(sr * 0.01); return np.convolve(np.abs(x), np.ones(k) / k, 'same')[::k]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('song'); ap.add_argument('video'); ap.add_argument('--windows', default='20-50,60-90,120-150')
    ap.add_argument('--search', type=float, default=10.0, help='seconds of slack either side')
    a = ap.parse_args(); sr = 8000
    s, v = decode(a.song), decode(a.video)
    for w in a.windows.split(','):
        lo, hi = map(float, w.split('-'))
        A = env(s[int(lo * sr):int(hi * sr)]); A = A - A.mean()
        b0 = max(0.0, lo - a.search)
        B = env(v[int(b0 * sr):int((hi + a.search) * sr)]); B = B - B.mean()
        if len(B) < len(A): print(f'window {w}: video too short'); continue
        c = fftconvolve(B, A[::-1], 'valid'); i = int(np.argmax(c))
        off = i * 0.01 + b0 - lo
        score = c[i] / np.sqrt((A ** 2).sum() * (B[i:i + len(A)] ** 2).sum() + 1e-9)
        print(f'window {w}s: video_time = song_time {off:+.2f}s   (correlation {score:.2f})')

if __name__ == '__main__':
    main()
