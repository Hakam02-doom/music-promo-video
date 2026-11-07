#!/usr/bin/env python3
"""Spotify — dark editorial film, v6 (57 s: "Raw Rich Rare" -> "National Treasures" + its official video).

All-dark stage, no paper. Opens on the Spotify logo, then moves through
library -> album carousel -> now playing -> drop -> cover wall -> logo,
joined by continuous camera zooms and matched cuts (the same cover in the
same place on both sides of each change).

  python render.py                  # full render -> out/picture.mp4
  python render.py --stills 3,9     # PNG test frames -> out/$STILLS (default stills)

Programme time == song time ("Raw Rich Rare" plays from 0:00 under the film).
95 BPM; downbeats 2.494, 5.02, 7.546, 10.07, 12.6, 15.125, 17.651, 20.177,
22.704 (drop), 25.23, 27.756, 30.283.
"""
import json, math, os, subprocess, argparse
import numpy as np, cv2
from PIL import Image, ImageFont, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
STYLE = json.load(open(os.path.join(ROOT, 'style.json')))
W, H = 1080, 1920
FPS = STYLE['fps']
DUR = 58.2
NFRAMES = int(round(DUR * FPS))
BEAT = 60 / 95.0
SONG_LEN = 182.24
# National Treasures (Drake): its downbeat at song time 19.299 s is mixed onto RRR's downbeat at 30.283 s
SWAP = 30.283
NT_OFF = SWAP - 19.299            # film t -> National Treasures song time: t - NT_OFF
NT_LEN = 208.33
NT_BAR = 1.8597; NT_BEAT = NT_BAR / 4
NT_DROP = 27.69 + NT_OFF          # 38.674: the hook's drop
def ntdb(k): return SWAP + k * NT_BAR   # National Treasures downbeats in film time

def rgb(c): return np.array(c, np.float32) / 255.0
BG = rgb(STYLE['bg_rgb']); INK = rgb(STYLE['ink_rgb']); DIM = rgb(STYLE['dim_rgb']); GREEN = rgb(STYLE['green_rgb'])

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def e_io(x): x = clamp(x); return 4*x*x*x if x < .5 else 1 - (-2*x + 2)**3 / 2
def e_out(x): x = clamp(x); return 1 - (1 - x)**3
def e_in(x): x = clamp(x); return x**3
def e_sine(x): x = clamp(x); return -(math.cos(math.pi*x) - 1) / 2
def ramp(t, a, b, f=e_io): return f((t - a) / (b - a)) if b > a else float(t >= a)
def lerp(a, b, k): return a + (b - a) * k
def lerp_exp(a, b, k): return math.exp(lerp(math.log(a), math.log(b), k))
def stepped(t, rate=STYLE['stepped_text_fps']): return math.floor(t * rate + 1e-6) / rate

# ---------------------------------------------------------------- affine helpers
def T(x, y): return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], np.float64)
def S(s): return np.array([[s, 0, 0], [0, s, 0], [0, 0, 1]], np.float64)
def R(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float64)
def place(cx, cy, scale, rot, ax, ay): return T(cx, cy) @ R(rot) @ S(scale) @ T(-ax, -ay)
def apply(M, x, y): p = M @ np.array([x, y, 1.0]); return p[0], p[1]
def mscale(M): return math.sqrt(abs(np.linalg.det(M[:2, :2])))
I3 = np.eye(3)
def zoom_about(px, py, z): return T(px, py) @ S(z) @ T(-px, -py)

# ---------------------------------------------------------------- compositing
def blit(canvas, img, alpha, M, op=1.0, mask_acc=None, clip=None):
    if op <= 0.002: return
    h, w = alpha.shape
    pts = np.array([apply(M, x, y) for x, y in [(0, 0), (w, 0), (0, h), (w, h)]])
    x0, y0 = np.floor(pts.min(0)).astype(int) - 2
    x1, y1 = np.ceil(pts.max(0)).astype(int) + 2
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    if clip is not None:
        x0, y0, x1, y1 = max(x0, int(clip[0])), max(y0, int(clip[1])), min(x1, int(clip[2])), min(y1, int(clip[3]))
    if x1 <= x0 or y1 <= y0: return
    sc = mscale(M)
    if sc < 0.6:  # prefilter strong downscales (no aliasing on big covers shown small)
        k = 0.5 / sc * 0.6
        img = cv2.GaussianBlur(img, (0, 0), k); alpha = cv2.GaussianBlur(alpha, (0, 0), k)
    Mr = (T(-x0, -y0) @ M)[:2].astype(np.float32)
    interp = cv2.INTER_CUBIC if sc > 1.05 else cv2.INTER_LINEAR
    ri = cv2.warpAffine(img, Mr, (x1 - x0, y1 - y0), flags=interp, borderValue=0)
    ra = np.clip(cv2.warpAffine(alpha, Mr, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=0), 0, 1) * op
    ra = ra[..., None]
    reg = canvas[y0:y1, x0:x1]
    reg *= (1 - ra); reg += np.clip(ri, 0, 1) * ra
    if mask_acc is not None:
        m = mask_acc[y0:y1, x0:x1]; m[:] = np.maximum(m, ra[..., 0])

def shadow(canvas, alpha, M, op=1.0, strength=0.55, blur=26, off=(0, 18)):
    if op <= 0.002: return
    h, w = alpha.shape
    pad = int(blur * 3 + 20)
    pts = np.array([apply(M, x, y) for x, y in [(0, 0), (w, 0), (0, h), (w, h)]])
    x0, y0 = np.floor(pts.min(0)).astype(int) - pad
    x1, y1 = np.ceil(pts.max(0)).astype(int) + pad + max(off)
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    if x1 <= x0 or y1 <= y0: return
    q = 4  # quarter-res shadow for speed
    Mr = (S(1/q) @ T(-x0 + off[0], -y0 + off[1]) @ M)[:2].astype(np.float32)
    ws, hs = max(1, (x1 - x0) // q), max(1, (y1 - y0) // q)
    ra = cv2.warpAffine(alpha, Mr, (ws, hs), flags=cv2.INTER_LINEAR, borderValue=0)
    ra = cv2.GaussianBlur(ra, (0, 0), max(0.5, blur / q))
    ra = cv2.resize(ra, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR) * (strength * op)
    canvas[y0:y1, x0:x1] *= (1 - ra[..., None])

# ---------------------------------------------------------------- media
SRC = os.path.join(ROOT, 'src')
def load_rgba(path):
    a = np.asarray(Image.open(path).convert('RGBA')).astype(np.float32) / 255
    return np.ascontiguousarray(a[..., :3]), np.ascontiguousarray(a[..., 3])

def rounded_mask(w, h, r):
    m = np.zeros((h, w), np.uint8)
    cv2.rectangle(m, (r, 0), (w - r - 1, h - 1), 255, -1); cv2.rectangle(m, (0, r), (w - 1, h - r - 1), 255, -1)
    for cx, cy in [(r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)]: cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
    return m.astype(np.float32) / 255

def prep_cover(img, size=1200):
    if img.shape[1] != size:
        small = img.shape[1] < size
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_LANCZOS4)
        if small:  # gentle unsharp after upscaling (only the 500 px Enigma art)
            soft = cv2.GaussianBlur(img, (0, 0), 1.6); img = np.clip(img + (img - soft) * 0.5, 0, 1)
    return img.astype(np.float32), rounded_mask(size, size, int(size * 0.022))

def liked_songs(size=1200):
    """Spotify's Liked Songs tile, redrawn sharp: violet->mint gradient + white heart."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
    k = np.clip((xx * 0.55 + yy * 0.45), 0, 1)[..., None]
    img = rgb((69, 10, 245)) * (1 - k) + rgb((196, 239, 217)) * k
    s = size * 2
    im = Image.new('L', (s, s), 0); d = ImageDraw.Draw(im)
    pts = []
    for i in range(200):
        a = 2 * math.pi * i / 200
        x = 16 * math.sin(a)**3; y = -(13*math.cos(a) - 5*math.cos(2*a) - 2*math.cos(3*a) - math.cos(4*a))
        pts.append((s/2 + x * s * 0.0105, s * 0.5 + y * s * 0.0105))
    d.polygon(pts, fill=255)
    heart = np.asarray(im.resize((size, size), Image.LANCZOS)).astype(np.float32)[..., None] / 255
    img = img * (1 - heart) + heart
    return img.astype(np.float32), rounded_mask(size, size, int(size * 0.022))

PROV = json.load(open(os.path.join(SRC, 'covers', 'provenance.json')))
COV = {k: prep_cover(load_rgba(os.path.join(SRC, 'covers', k + '.jpg'))[0]) for k in PROV}
COV['liked'] = liked_songs()

LOGO, LOGO_A = load_rgba(os.path.join(SRC, 'logo.png'))
LOGO_C, LOGO_R = (469.0, 469.5), 455.0
_disc = np.zeros(LOGO_A.shape, np.uint8)  # the arcs are transparent holes in the PNG: fill them white
cv2.circle(_disc, (int(LOGO_C[0]*16), int(LOGO_C[1]*16)), int(LOGO_R*16), 255, -1, cv2.LINE_AA, shift=4)
_disc = _disc.astype(np.float32) / 255
LOGO = LOGO * LOGO_A[..., None] + np.float32(0.985) * (1 - LOGO_A[..., None]) * _disc[..., None]
LOGO_A = np.maximum(LOGO_A, _disc); LOGO = (LOGO / np.maximum(LOGO_A, 1e-4)[..., None]).astype(np.float32)

def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W/2) / W)**2 + ((yy - H*0.45) / H)**2)
    lift = np.clip(1 - d * 1.5, 0, 1) ** 2 * 0.035
    return np.clip(BG + lift[..., None], 0, 1).astype(np.float32)
BGIMG = make_bg()

def glow_img(size=512):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    d = np.sqrt((xx - size/2)**2 + (yy - size/2)**2) / (size/2)
    return np.ones((size, size, 3), np.float32) * GREEN, (np.clip(1 - d, 0, 1) ** 2.2).astype(np.float32)
GLOW, GLOW_A = glow_img()
def glow(cv, cx, cy, radius, op):
    blit(cv, GLOW, GLOW_A, place(cx, cy, radius * 2 / GLOW.shape[0], 0, GLOW.shape[1]/2, GLOW.shape[0]/2), op)

# ---------------------------------------------------------------- type (three roles only)
def _fontpath(p): return p if os.path.exists(p) else p.replace('/Supplemental', '')
FONTS = {k: (_fontpath(v[0]), v[1]) for k, v in STYLE['fonts'].items()}
_fc = {}
def font(role, size):
    k = (role, int(size))
    if k not in _fc: _fc[k] = ImageFont.truetype(FONTS[role][0], int(size), index=FONTS[role][1])
    return _fc[k]

def text_img(txt, role, size):
    f = font(role, size); asc, desc = f.getmetrics(); pad = int(size * 0.35); adv = f.getlength(txt)
    im = Image.new('L', (int(adv + 2*pad), int(asc + desc + 2*pad)), 0)
    ImageDraw.Draw(im).text((pad, pad + asc), txt, font=f, fill=255, anchor='ls')
    return np.asarray(im).astype(np.float32) / 255, (pad, pad + asc), adv

class Text:
    """Authored text. Enter: rise + soft blur + fade (+ optional pop). Optional stepped (stop-motion)
    clock during the entry only. Exit: drift + blur + fade. Optional camera C (world coords)."""
    def __init__(self, txt, role, size, x, y, t0, t1, color=INK, align='left', split=None,
                 stagger=0.0, enter=0.42, exit=0.26, rise=0.22, drift=0.12, steppedin=False, pop=0.0):
        self.__dict__.update(locals()); del self.__dict__['self']
        f = font(role, size)
        units = [txt] if split is None else (list(txt) if split == 'char' else txt.split(' '))
        self.groups = []; cursor = ''
        full = f.getlength(txt); sx = {'left': 0, 'center': -full/2, 'right': -full}[align]
        for u in units:
            ox = sx + f.getlength(cursor)
            a, (px, py), adv = text_img(u, role, size)
            self.groups.append((a, px, py, ox, adv))
            cursor += u + ('' if split in (None, 'char') else ' ')
        self.width = full
    def draw(self, canvas, t, C=None, op_mul=1.0):
        if t < self.t0 - 0.01 or t > self.t1 + 0.01 or op_mul <= 0: return
        for i, (a, px, py, gx, adv) in enumerate(self.groups):
            ts = self.t0 + i * self.stagger
            tq = stepped(t) if (self.steppedin and t < ts + self.enter) else t
            pin = e_out((tq - ts) / self.enter)
            pout = e_in((t - (self.t1 - self.exit)) / self.exit)
            op = pin * (1 - pout) * op_mul
            if op <= 0.003: continue
            dy = (1 - pin) * self.rise * self.size - pout * self.drift * self.size
            blur = (1 - pin) * 0.05 * self.size + pout * 0.05 * self.size
            img_a = cv2.GaussianBlur(a, (0, 0), round(blur * 2) / 2) if blur > 0.4 else a
            col = np.empty(a.shape + (3,), np.float32); col[:] = self.color
            cx = gx + adv / 2
            M = T(self.x, self.y) @ T(cx, dy) @ S(1 + self.pop * (1 - pin)) @ T(-cx, 0) @ T(gx, 0) @ T(-px, -py)
            if C is not None: M = C @ M
            blit(canvas, col, img_a, M, op)

# ---------------------------------------------------------------- vector UI bits
def aa_fill(canvas, draw_fn, color, op, bbox):
    x0, y0, x1, y1 = [int(v) for v in bbox]
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    if x1 <= x0 or y1 <= y0 or op <= 0.003: return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8); draw_fn(m, x0, y0)
    a = (m.astype(np.float32) / 255 * op)[..., None]
    reg = canvas[y0:y1, x0:x1]; reg *= (1 - a); reg += color * a

def circle(canvas, cx, cy, r, color, op=1.0, thick=-1):
    pad = r + 6
    aa_fill(canvas, lambda m, x0, y0: cv2.circle(m, (int((cx - x0)*16), int((cy - y0)*16)), int(r*16), 255,
            -1 if thick < 0 else int(thick), cv2.LINE_AA, shift=4), color, op, (cx - pad, cy - pad, cx + pad, cy + pad))

def poly(canvas, pts, color, op=1.0):
    a = np.array(pts, np.float64)
    bb = (a[:, 0].min() - 3, a[:, 1].min() - 3, a[:, 0].max() + 3, a[:, 1].max() + 3)
    aa_fill(canvas, lambda m, x0, y0: cv2.fillPoly(m, [((a - [x0, y0]) * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4), color, op, bb)

def rect(canvas, x0, y0, x1, y1, color, op=1.0):
    poly(canvas, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], color, op)

def stroke(canvas, pts, color, thick, op=1.0):
    a = np.array(pts, np.float64)
    pad = thick + 4
    bb = (a[:, 0].min() - pad, a[:, 1].min() - pad, a[:, 0].max() + pad, a[:, 1].max() + pad)
    aa_fill(canvas, lambda m, x0, y0: cv2.polylines(m, [((a - [x0, y0]) * 16).astype(np.int32)], False, 255, int(thick), cv2.LINE_AA, shift=4), color, op, bb)

def heart_pts(cx, cy, s, n=72):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x = 16 * math.sin(a)**3; y = -(13*math.cos(a) - 5*math.cos(2*a) - 2*math.cos(3*a) - math.cos(4*a))
        pts.append((cx + x * s / 32, cy + y * s / 32))
    return pts

def tap(canvas, cx, cy, t, t0, r=58):
    """a soft finger tap: press disc, then an expanding ring"""
    if not (t0 - 0.05 < t < t0 + 0.9): return
    kp = ramp(t, t0 - 0.05, t0 + 0.08, e_out) * (1 - ramp(t, t0 + 0.12, t0 + 0.45, e_io))
    if kp > 0.01: circle(canvas, cx, cy, r * lerp(0.7, 1.0, kp), INK, 0.28 * kp)
    kr = ramp(t, t0, t0 + 0.85, e_out)
    if 0 < kr < 1: circle(canvas, cx, cy, r * lerp(0.9, 2.4, kr), INK, 0.7 * (1 - kr), thick=3)

def press(t, t0):
    return 1 - 0.045 * ramp(t, t0 - 0.05, t0 + 0.08, e_out) * (1 - ramp(t, t0 + 0.1, t0 + 0.5, e_io))

def draw_cover(cv, name, cx, cy, size, op=1.0, C=I3, rot=0.0, gmask=None, sh=0.6):
    img, a = COV[name]
    M = C @ place(cx, cy, size / img.shape[1], rot, img.shape[1]/2, img.shape[0]/2)
    s = mscale(M) * img.shape[1]
    shadow(cv, a, M, op, strength=sh, blur=max(6, s * 0.05), off=(0, int(s * 0.03)))
    blit(cv, img, a, M, op, gmask)

# ---------------------------------------------------------------- finishing
def bloom(img):
    p = STYLE['bloom']
    lum = img @ np.array([.299, .587, .114], np.float32)
    k = np.clip((lum - p['threshold']) / (1 - p['threshold']), 0, 1) ** 1.6
    small = cv2.resize(img * k[..., None], (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    acc = np.zeros_like(small)
    for s in p['sigmas']: acc += cv2.GaussianBlur(small, (0, 0), s / 4)
    acc = cv2.resize(acc / len(p['sigmas']), (W, H), interpolation=cv2.INTER_LINEAR) * p['amount']
    return 1 - (1 - img) * (1 - acc)

def grain(img, n, gmask):
    g = STYLE['grain']
    rng = np.random.default_rng(1000 + n)  # fresh, reproducible every output frame
    nz = rng.standard_normal((int(H / g['size']), int(W / g['size'])), dtype=np.float32)
    nz = cv2.resize(nz, (W, H), interpolation=cv2.INTER_LINEAR)
    lum = img @ np.array([.299, .587, .114], np.float32)
    wgt = (0.55 + 2.2 * lum * (1 - lum)) * (1 - gmask * (1 - g['on_covers']))
    return img + (nz * wgt * g['amount'])[..., None]

# ================================================================ TIMELINE
# S1 0.00-5.02   logo + repeat ring, LISTEN rising below it, on repeat, tap, zoom INTO the green
# S2 4.70-10.07  library grid (zoom-out reveal), title scrolls with the page above it (LIBRARY rises through a
#                mask line, green underline, Playlists / Albums chips; Albums lights up), tiles pop, tap Saroor
# S3 10.07-15.13 album carousel: zoom out, slide on beats, zoom back in on Enigma
# S4 15.13-22.70 now playing (Raw Rich Rare), tap the heart, zoom into the cover as the song swells
# S5 22.70-30.28 drop: RAW rises from behind the poster, rich drops from behind it, RARE rises through a
#                mask line (no text ever sits on the artwork); zoom out to a wall; dive through the
#                48 Rhymes chain into black
# D1 30.28-40.90 National Treasures (song 0:19): diamonds fly in one by one, then pour in and lock into
#                the glove (ICEMAN cover); on the drop NATIONAL / treasures slide out from behind it
# D2 40.90-45.16 now playing: National Treasures, heart tap, diamonds glint on the beat
# MV 45.16-52.60 dive through the OK sign's hole into the official video (in sync): full-bleed, then it
#                reframes into a top panel as the cover rises below; panel slides away, cover recentres
# D3 52.60-55.39 every diamond lifts off and spirals into the Spotify logo
# D4 55.39-58.20 end card: logo glides up, a repeat ring draws round it, LISTEN rises below it
#                through a mask line (nothing hidden), on repeat, fade to black (matches frame 0)
D_DROP = 22.704

# ---- S1
L1 = (540.0, 790.0); R1 = 185.0                     # same place and size as the end card (the loop matches)
TAP_LOGO = 4.0
L1_FOCUS = (540.0, L1[1] + (790 - LOGO_C[1]) * R1 / LOGO_R)  # solid green below the lowest arc
def camS1(t):
    # eased in AND out; the green point glides to frame centre; at 24x every corner is inside the green
    k = ramp(t, 4.1, 5.05, e_io)
    fx, fy = L1_FOCUS
    return T(fx, lerp(fy, 960.0, k)) @ S(lerp_exp(1, 24, k)) @ T(-fx, -fy), k

# ---- S2 library grid
GRID = [('liked', 300, 660, 'Liked Songs', 'PLAYLIST'), ('enigma', 780, 660, 'Enigma', 'ARJAN DHILLON, MXRCI'),
        ('saroor', 300, 1240, 'Saroor', 'ARJAN DHILLON, MXRCI'), ('majhaestic', 780, 1240, 'Majhaestic', 'PREM DHILLON'),
        ('anyway', 300, 1820, 'ANYWAY', 'CHEEMA Y, GUR SIDHU'), ('rhymes', 780, 1820, '48 Rhymes', 'KARAN AUJLA')]
TILE = 440
TAP_SAROOR = 9.25
HERO = (540.0, 800.0, 820.0)  # centre x, y, size of the hero cover in S3/S4
def camS2_base(t):
    z = lerp(1.35, 1.0, ramp(t, 4.7, 5.75, e_out)) * (1 + 0.025 * ramp(t, 5.75, 9.3, e_sine))
    pan = 140 * ramp(t, 5.75, 9.3, e_sine)
    return T(540, 960) @ S(z) @ T(-540, -960 - pan)
def camS2(t):
    C0 = camS2_base(min(t, 9.35))
    if t < 9.35: return C0, 0.0
    k = ramp(t, 9.35, 10.07, e_io)
    px, py = apply(C0, 300, 1240); s0 = TILE * mscale(C0)
    Z = lerp_exp(1, HERO[2] / s0, k)
    return T(lerp(px, HERO[0], k), lerp(py, HERO[1], k)) @ S(Z) @ T(-px, -py) @ C0, k

# ---- S3 carousel
CAR = [('saroor', 'Saroor', 'ARJAN DHILLON, MXRCI  ·  2023'),
       ('dhurandhar', 'Dhurandhar The Revenge', 'SHASHWAT SACHDEV'),
       ('majhaestic', 'Majhaestic', 'PREM DHILLON  ·  2026'),
       ('anyway', 'ANYWAY', 'CHEEMA Y, GUR SIDHU  ·  2023'),
       ('enigma', 'Enigma', 'ARJAN DHILLON, MXRCI  ·  2026')]
SP = 940.0
CAR_MOVES = [12.6, 12.6 + BEAT, 12.6 + 2*BEAT, 12.6 + 3*BEAT]
def camS3(t):
    idx = sum(ramp(t, m, m + 0.55, e_io) for m in CAR_MOVES)
    fx = HERO[0] + idx * SP
    if t < 14.4: z = lerp(1.0, 0.56, ramp(t, 11.75, 12.6, e_io))
    else: z = lerp(0.56, 1.0, ramp(t, 14.45, 15.125, e_io))
    return T(540, HERO[1]) @ S(z) @ T(-fx, -HERO[1])

# ---- S4 now playing
TAP_HEART = 17.651
S4_ZOOM = 2.05
def camS4(t):
    k = ramp(t, 20.177, D_DROP, e_in)  # accelerate into the cover as the song swells
    return T(0, 160 * k) @ zoom_about(HERO[0], HERO[1], lerp_exp(1, S4_ZOOM, k)), k

# ---- S5 drop + wall, then a flight through the 48 Rhymes chain into black
HERO5 = (540.0, 900.0, 640.0)
WALL_SP = 700.0
WALL_ORDER = ['saroor', 'rhymes', 'goat', 'liked', 'dhurandhar', 'majhaestic', 'anyway']
WALL = [(gx, gy, WALL_ORDER[(gx * 3 + gy * 5) % len(WALL_ORDER)]) for gy in range(-4, 5) for gx in range(-3, 4) if (gx, gy) != (0, 0)]
RHY = (1, 1)  # the 48 Rhymes tile diagonally below-right of the hero
RHY_DARK = (HERO5[0] + RHY[0] * WALL_SP + (690 / 1200 - 0.5) * HERO5[2],   # black inside the chain's loop
            HERO5[1] + RHY[1] * WALL_SP + (220 / 1200 - 0.5) * HERO5[2])
FLY0 = 28.35
def camS5_wall(t):
    z = lerp(1.0, 0.36, ramp(t, 25.23, 27.4, e_io)) * lerp(1.0, 0.86, ramp(t, 27.4, FLY0, e_sine))
    rot = -4.0 * ramp(t, 25.23, FLY0, e_sine)
    return T(HERO5[0], HERO5[1]) @ R(rot) @ S(z) @ T(-HERO5[0], -HERO5[1]), z, rot
STUTTER_HITS = []   # (v5 had camera punches on a DJ roll; the v6 handoff is a smooth breakdown)
def stutter_pulse(t):
    p = 0.0
    for j, h in enumerate(STUTTER_HITS):
        if t >= h: p += (0.03 if j < 6 else 0.012) * math.exp(-(t - h) / 0.07)
    return p
def camS5(t):
    C = _camS5(t)
    p = stutter_pulse(t)
    return zoom_about(540, 960, 1 + p) @ C if p > 1e-4 else C
def _camS5(t):
    if t <= FLY0: return camS5_wall(t)[0]
    C0, z0, r0 = camS5_wall(FLY0)
    s0 = apply(C0, *RHY_DARK)
    k = ramp(t, FLY0, SWAP, e_io)
    # the dark point glides to frame centre while the camera dives in (13x: the black fills the frame)
    return T(lerp(s0[0], 540, k), lerp(s0[1], 960, k)) @ R(lerp(r0, 0, k)) @ S(lerp_exp(z0, 13.0, k)) @ T(-RHY_DARK[0], -RHY_DARK[1])
S4_END_C = apply(camS4(D_DROP)[0], HERO[0], HERO[1])

# ================================================================ Drake: National Treasures (ICEMAN)
ICE = cv2.resize(load_rgba(os.path.join(SRC, 'covers', 'iceman.jpg'))[0], (1500, 1500), interpolation=cv2.INTER_AREA).astype(np.float32)
ICE_A = rounded_mask(1500, 1500, int(1500 * 0.022))
_g = ICE @ np.array([.299, .587, .114], np.float32)
ICE_BODY = (cv2.GaussianBlur(_g, (0, 0), 12) > 0.28).astype(np.float32); ICE_BODY[1110:] = 0   # the glove, above the cuff
ICE_BODY_SOFT = cv2.GaussianBlur(ICE_BODY, (0, 0), 6)

def _diamonds(max_n=640, md=10):
    gb = cv2.GaussianBlur(_g, (0, 0), 1.0)
    loc = (gb >= cv2.dilate(gb, np.ones((7, 7), np.uint8)) - 1e-6) & (gb > 0.5) & (ICE_BODY > 0)
    ys, xs = np.nonzero(loc); order = np.argsort(-gb[ys, xs])
    keep, cells = [], {}
    for i in order:
        x, y = int(xs[i]), int(ys[i]); cx, cy = x // md, y // md
        if any((qx - x)**2 + (qy - y)**2 < md * md for dx in (-1, 0, 1) for dy in (-1, 0, 1) for qx, qy in cells.get((cx + dx, cy + dy), [])):
            continue
        keep.append((x, y)); cells.setdefault((cx, cy), []).append((x, y))
        if len(keep) >= max_n: break
    return np.array(keep, np.float64)
DIA = _diamonds()                     # diamond centres in 1500 px cover coordinates (brightest first)
ND = len(DIA)
PR = 8
_yy, _xx = np.mgrid[-PR:PR + 1, -PR:PR + 1]
PATCH_A = np.clip((PR + 0.5 - np.sqrt(_xx**2 + _yy**2)) / 2.0, 0, 1).astype(np.float32)
_padded = np.pad(ICE, ((PR, PR), (PR, PR), (0, 0)))
PATCH = [np.ascontiguousarray(_padded[int(y):int(y) + 2*PR + 1, int(x):int(x) + 2*PR + 1]) for x, y in DIA]

def make_glint(s=128):
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32); c = (s - 1) / 2
    dx, dy = np.abs(xx - c), np.abs(yy - c)
    a = np.exp(-(dy / 1.3)**2) * np.exp(-dx / (s * 0.2)) + np.exp(-(dx / 1.3)**2) * np.exp(-dy / (s * 0.2))
    a += np.exp(-(dx**2 + dy**2) / (s * 0.05)**2)
    return np.ones((s, s, 3), np.float32), np.clip(a, 0, 1).astype(np.float32)
GLINT, GLINT_A = make_glint()
def glint(cv, x, y, size, op):
    if op > 0.01: blit(cv, GLINT, GLINT_A, place(x, y, size / GLINT.shape[0], 0, GLINT.shape[1]/2, GLINT.shape[0]/2), op)

# --- D1: diamonds fly in one by one, then pour in, and lock into the glove
CC1, CS1 = (540.0, 900.0), 940.0
S1C = CS1 / 1500
_rng = np.random.default_rng(21)
FIRST = 8
_rest = [i for i in range(ND) if i >= FIRST]
_rest.sort(key=lambda i: -(DIA[i][1] + _rng.normal(0, 60)))         # from the cuff up to the fingertips
D_ORDER = list(range(FIRST)) + _rest                                  # brightest 8 come first, alone
LAND = np.zeros(ND); FLY = np.zeros(ND)
for k, i in enumerate(D_ORDER):
    if k < FIRST:
        LAND[i] = ntdb(2) - (FIRST - 1 - k) * NT_BEAT; FLY[i] = 1.25    # one by one on the beat, last on a downbeat
    else:
        LAND[i] = ntdb(2) + 0.05 + 3.35 * ((k - FIRST + 1) / (ND - FIRST)) ** 0.7; FLY[i] = 0.75
TH0 = _rng.uniform(0, 2 * math.pi, ND); RAD0 = _rng.uniform(950, 1350, ND); SWIRL = _rng.choice([-1, 1], ND) * _rng.uniform(0.4, 1.0, ND)
GLINT_ON = [(k < FIRST) or (k % 4 == 0) for k in range(ND)]
GLINT_ON = np.array([GLINT_ON[D_ORDER.index(i)] for i in range(ND)])
GLOVE_FULL, COVER_FULL = (37.15, 37.75), (37.5, 38.25)
def dia_world(i): return CC1[0] + (DIA[i][0] - 750) * S1C, CC1[1] + (DIA[i][1] - 750) * S1C
def camD1(t):
    k = ramp(t, SWAP, 37.6, e_io)
    z = lerp(1.5, 1.0, k)
    palm = (CC1[0] + (800 - 750) * S1C, CC1[1] + (800 - 750) * S1C)
    fx, fy = lerp(palm[0], CC1[0], k), lerp(palm[1], CC1[1], k)
    punch = 1 + 0.035 * math.sin(math.pi * ramp(t, NT_DROP, NT_DROP + 0.5, e_out))
    return T(540, lerp(960, 900, k)) @ S(z * punch) @ T(-fx, -fy)
REVS = 300
DIA_R = np.clip(np.round(DIA / 5).astype(int), 0, REVS - 1)
def reveal_alpha(t):
    w = np.clip((t - LAND + 0.05) / 0.4, 0, 1)
    acc = np.zeros((REVS, REVS), np.float32)
    np.add.at(acc, (DIA_R[:, 1], DIA_R[:, 0]), w.astype(np.float32))
    a = np.clip(cv2.GaussianBlur(acc, (0, 0), 2.2) * 5.0, 0, 1)
    a = cv2.resize(a, (1500, 1500), interpolation=cv2.INTER_LINEAR)
    a = np.maximum(a, ICE_BODY_SOFT * 0.11 * ramp(t, SWAP - 0.1, SWAP + 1.4, e_sine))   # faint ghost: the slots the diamonds fill
    a = np.maximum(a, ICE_BODY_SOFT * ramp(t, *GLOVE_FULL))
    a = np.maximum(a, ramp(t, *COVER_FULL, e_sine))
    return (a * ICE_A).astype(np.float32)

# --- D2: player.  D3: the diamonds lift off and re-form into the Spotify logo
D2_IN = (40.9, 41.65)                              # cover glides to the player position
TAP_HEART2 = ntdb(7)                                # 43.30
UI2_OUT = ntdb(8)                                   # 45.16
HOLE = (45.25, 46.15)                               # dive through the hole of the OK sign
HOLE_PT, HOLE_Z = (857.0, 681.0), 32.0             # hole centre on the 1500 px cover; 32x fills the frame with its black
MV_FULL_IN = (45.95, 46.45)                         # the official video fades up out of that black
SPLIT = (ntdb(10), ntdb(10) + 0.75)                 # 48.88: video reframes into a top panel, the cover rises below
SPLIT_OUT = (51.85, ntdb(12))                       # panel slides away, cover returns to centre (52.60)
LIFT = ntdb(12)                                     # 52.60: diamonds lift off
LOGO_END = ntdb(13) + 2 * NT_BEAT                   # 55.39: the logo lands
END_L = (540.0, 860.0); END_R = 210.0
def ice_cover_geom(t):
    if t < SPLIT[0]:
        k = ramp(t, *D2_IN, e_io); return 540.0, lerp(900.0, HERO[1], k), lerp(CS1, HERO[2], k)
    if t < SPLIT_OUT[0]:
        k = ramp(t, SPLIT[0], SPLIT[1] + 0.2, e_out); return 540.0, lerp(2450.0, 1400.0, k), 760.0
    k = ramp(t, *SPLIT_OUT, e_io); return 540.0, lerp(1400.0, HERO[1], k), lerp(760.0, HERO[2], k)
def camHole(t):
    k = ramp(t, *HOLE, e_io)
    px = HERO[0] + (HOLE_PT[0] - 750) * HERO[2] / 1500; py = HERO[1] + (HOLE_PT[1] - 750) * HERO[2] / 1500
    return T(lerp(px, 540, k), lerp(py, 960, k)) @ S(lerp_exp(1, HOLE_Z, k)) @ T(-px, -py)

# --- the official music video (src/video/mv_frames = video time 34.4 s onward at 24 fps), in sync with the song
MV_DIR = os.path.join(SRC, 'video', 'mv_frames')
MV_FILES = sorted(f for f in os.listdir(MV_DIR) if f.endswith('.jpg'))
MV_T0, MV_FPS, MV_SYNC = 34.4, 24.0, -0.06          # video time = song time - 0.06 s (audio cross-correlation)
MV_CUTS = {37, 91, 149, 171}                        # first frame of each new shot
MV_SHOT_X = [0.60, 0.53, 0.52, 0.40, 0.40]          # Drake's x in frame for each shot (shots split at MV_CUTS)
MV_A = rounded_mask(2560, 1440, 44)
_mvc = {}
def mv_img(i):
    i = int(np.clip(i, 0, len(MV_FILES) - 1))
    if i not in _mvc:
        if len(_mvc) > 6: _mvc.pop(next(iter(_mvc)))
        _mvc[i] = (cv2.cvtColor(cv2.imread(os.path.join(MV_DIR, MV_FILES[i])), cv2.COLOR_BGR2RGB).astype(np.float32) / 255)
    return _mvc[i]
def mv_frame(t):
    mt = t - NT_OFF + MV_SYNC
    f = (mt - MV_T0) * MV_FPS; i0 = int(math.floor(f)); w = f - i0
    if (i0 + 1) in MV_CUTS: w = 0.0 if w < 0.5 else 1.0     # never blend across a cut
    img = mv_img(i0) if w < 0.02 else (mv_img(i0 + 1) if w > 0.98 else mv_img(i0) * (1 - w) + mv_img(i0 + 1) * w)
    shown = i0 if w < 0.5 else i0 + 1                # the frame actually on screen: the crop follows it, not the clock
    return img, mt, shown
def mv_x(shown):
    return MV_SHOT_X[sum(1 for c in sorted(MV_CUTS) if shown >= c)]
def _logo_targets(n, md=27.0, seed=8):
    rng = np.random.default_rng(seed); pts = []; cells = {}; tries = 0
    while len(pts) < n and tries < 200000:
        tries += 1
        a = rng.uniform(0, 2 * math.pi); r = LOGO_R * 0.95 * math.sqrt(rng.uniform(0, 1))
        x, y = LOGO_C[0] + r * math.cos(a), LOGO_C[1] + r * math.sin(a)
        cx, cy = int(x // md), int(y // md)
        if any((qx - x)**2 + (qy - y)**2 < md * md for dx in (-1, 0, 1) for dy in (-1, 0, 1) for qx, qy in cells.get((cx + dx, cy + dy), [])):
            continue
        pts.append((x, y)); cells.setdefault((cx, cy), []).append((x, y))
    pts = np.array(pts)
    pts = pts[np.argsort(pts[:, 1])]
    cols = np.array([LOGO[int(y), int(x)] for x, y in pts], np.float32)
    return pts, cols
_tgt, _tcol = _logo_targets(ND)
_by_y = np.argsort(DIA[:, 1])                       # glove top -> logo top
TGT = np.zeros((ND, 2)); TCOL = np.zeros((ND, 3), np.float32)
for rank, i in enumerate(_by_y):
    j = min(rank, len(_tgt) - 1)
    TGT[i] = (END_L[0] + (_tgt[j][0] - LOGO_C[0]) * END_R / LOGO_R, END_L[1] + (_tgt[j][1] - LOGO_C[1]) * END_R / LOGO_R)
    TCOL[i] = _tcol[j]
DEP = LIFT + 1.2 * (np.argsort(np.argsort(DIA[:, 1])) / ND)          # fingertips leave first
FLY3 = 1.5

# ---------------------------------------------------------------- text
SANS, SER, MONO = 'sans', 'serif_italic', 'mono'
T_REPEAT = Text('on repeat', SER, 98, 540, 1405, 1.75, 3.85, align='center', split='word', stagger=0.18, enter=0.5, exit=0.35)
# library title lives on the page (world coords) and scrolls with it, above the first row, so tiles never cover it
LIB_BASE = 288.0
T_YOUR = Text('your', SER, 140, 80, LIB_BASE, 5.3, 9.15, steppedin=True, enter=0.45)
LIB_X = 80 + font(SER, 140).getlength('your ')
_lbf = font(SANS, 118); LIB_W = _lbf.getlength('LIBRARY')
LIB_CH = [(text_img(c, SANS, 118), LIB_X + _lbf.getlength('LIBRARY'[:i])) for i, c in enumerate('LIBRARY')]
CHIP_Y, CHIP_H, CHIP_PAD, CHIP_GAP = 348.0, 48.0, 24.0, 16.0          # Spotify-style filter chips under the title
CHIPS = []
_cx = 80.0
for lab in ('Playlists', 'Albums'):
    im = text_img(lab, SANS, 26); w = im[2] + 2 * CHIP_PAD
    CHIPS.append((lab, im, _cx, w)); _cx += w + CHIP_GAP
ALBUMS_LIT = 7.546                                                      # downbeat: Albums lights up, leading into EVERY album

def pill_pts(x0, y0, x1, y1, n=14):
    r = (y1 - y0) / 2; pts = []
    for a in np.linspace(90, 270, n): pts.append((x0 + r + r * math.cos(math.radians(a)), y0 + r + r * math.sin(math.radians(a))))
    for a in np.linspace(-90, 90, n): pts.append((x1 - r + r * math.cos(math.radians(a)), y0 + r + r * math.sin(math.radians(a))))
    return pts

def library_title(cv, t, C, sop):
    T_YOUR.draw(cv, t, C, sop)
    out = ramp(t, 8.85, 9.15, e_io)
    base_s = apply(C, 0, LIB_BASE + 6)[1]                               # the mask line, on screen
    for i, ((a_, (px_, py_), adv_), x_) in enumerate(LIB_CH):           # LIBRARY rises letter by letter through it
        kl = ramp(t, 5.45 + i * 0.05, 5.45 + i * 0.05 + 0.42, e_out) * (1 - out)
        if kl <= 0: continue
        col = np.empty(a_.shape + (3,), np.float32); col[:] = INK
        blit(cv, col, a_, C @ T(x_ - px_, lerp(LIB_BASE + 150, LIB_BASE, kl) - py_), sop, clip=(0, 0, W, base_s))
    ku = ramp(t, 6.0, 6.45, e_io) * (1 - out)                           # green underline draws under LIBRARY
    if ku > 0.005:
        x0s, y0s = apply(C, LIB_X + 4, LIB_BASE + 16); x1s, y1s = apply(C, LIB_X + 4 + (LIB_W - 8) * ku, LIB_BASE + 22)
        rect(cv, x0s, y0s, x1s, y1s, GREEN, sop)
    for k, (lab, (a_, (px_, py_), adv_), x_, w_) in enumerate(CHIPS):   # filter chips pop in; Albums lights up green
        kc = ramp(t, 5.75 + k * 0.12, 5.75 + k * 0.12 + 0.35, e_out) * (1 - ramp(t, 8.85, 9.1, e_io))
        if kc <= 0.003: continue
        lit = ramp(t, ALBUMS_LIT, ALBUMS_LIT + 0.25, e_out) if lab == 'Albums' else 0.0
        bump = 1 + (0.08 * math.sin(math.pi * ramp(t, ALBUMS_LIT, ALBUMS_LIT + 0.3, e_io)) if lab == 'Albums' else 0)
        sc_ = lerp(0.85, 1.0, kc) * bump
        cxw, cyw = x_ + w_ / 2, CHIP_Y + CHIP_H / 2
        Mk = C @ T(cxw, cyw) @ S(sc_) @ T(-cxw, -cyw)
        p0 = apply(Mk, x_, CHIP_Y); p1 = apply(Mk, x_ + w_, CHIP_Y + CHIP_H)
        fill = rgb((42, 42, 42)) * (1 - lit) + GREEN * lit
        poly(cv, pill_pts(p0[0], p0[1], p1[0], p1[1]), fill, sop * kc)
        col = np.empty(a_.shape + (3,), np.float32); col[:] = INK * (1 - lit) + BG * lit
        blit(cv, col, a_, Mk @ T(x_ + CHIP_PAD - px_, CHIP_Y + CHIP_H / 2 + 9 - py_), sop * kc)
GRID_T = []
for name, cx, cy, title, sub in GRID:
    GRID_T.append(Text(title, SANS, 40, cx - TILE/2, cy + TILE/2 + 64, 5.3, 9.6, enter=0.4, exit=0.3))
    GRID_T.append(Text(sub, MONO, 22, cx - TILE/2, cy + TILE/2 + 104, 5.4, 9.6, color=DIM, enter=0.4, exit=0.3))
T_EVERY = Text('EVERY', SANS, 120, 70, 250, 10.35, 14.35, steppedin=True, split='char', stagger=0.05, enter=0.4)
T_ALBUM = Text('album,', SER, 140, 70 + font(SANS, 120).getlength('EVERY '), 250, 10.6, 14.35, steppedin=True, enter=0.45)
CAR_T = []
for i, (name, title, sub) in enumerate(CAR):
    x = HERO[0] + i * SP - HERO[2] / 2
    CAR_T.append(Text(title, SANS, 62, x, 1325, 10.25, 15.0, enter=0.45, exit=0.3))
    CAR_T.append(Text(sub, MONO, 26, x + 2, 1385, 10.35, 15.0, color=DIM, enter=0.45, exit=0.3))
T_NOW = Text('now playing', SER, 112, 540, 270, 15.3, 20.2, align='center', split='word', stagger=BEAT/2, steppedin=True, enter=0.45)
T_SONG = Text('Raw Rich Rare', SANS, 66, 130, 1330, 15.2, 20.5, enter=0.45, exit=0.35)
T_ART = Text('ARJAN DHILLON, MXRCI', MONO, 26, 132, 1390, 15.3, 20.5, color=DIM, enter=0.45, exit=0.35)
W_RAW, W_RICH, W_RARE = text_img('RAW', SANS, 240), text_img('rich', SER, 250), text_img('RARE', SANS, 240)
W_NAT, W_TRE = text_img('NATIONAL', SANS, 150), text_img('treasures', SER, 170)
T_CREDIT = Text('ARJAN DHILLON, MXRCI  ·  ENIGMA', MONO, 28, 540, 1800, 27.2, 28.85, align='center', enter=0.5, exit=0.35)
T_DRAKE = Text('DRAKE  ·  ICEMAN', MONO, 32, 540, 230, ntdb(1), 38.3, align='center', enter=0.5, exit=0.4)
T_NOW2 = Text('now playing', SER, 112, 540, 270, 41.2, UI2_OUT + 0.45, align='center', split='word', stagger=NT_BEAT, steppedin=True, enter=0.45)
T_SONG2 = Text('National Treasures', SANS, 66, 130, 1330, 41.3, UI2_OUT + 0.5, enter=0.45, exit=0.35)
T_ART2 = Text('DRAKE', MONO, 26, 132, 1390, 41.4, UI2_OUT + 0.5, color=DIM, enter=0.45, exit=0.35)
T_MV1 = Text('NATIONAL TREASURES  ·  OFFICIAL VIDEO', MONO, 26, 540, 1835, 46.6, 48.75, align='center', enter=0.5, exit=0.35)
T_MV2 = Text('DRAKE  ·  NATIONAL TREASURES  ·  OFFICIAL VIDEO', MONO, 24, 540, 952, 49.45, 51.8, align='center', enter=0.5, exit=0.35)
# end card: logo above, a repeat ring drawn around it, LISTEN fully visible below (rising through a mask line)
END_CARD_L, END_CARD_R = (540.0, 790.0), 185.0
RING_R, RING_IN = 262.0, (LOGO_END + 0.35, LOGO_END + 1.05)
LISTEN_BASE, LISTEN_SIZE = 1265.0, 150
_lf = font(SANS, LISTEN_SIZE); _lw = _lf.getlength('LISTEN')
LISTEN_CH = [(text_img(c, SANS, LISTEN_SIZE), 540 - _lw / 2 + _lf.getlength('LISTEN'[:i])) for i, c in enumerate('LISTEN')]
def repeat_ring(cv, cx, cy, t, t_in, op=1.0):
    """white repeat ring: draws on clockwise from the top with an arrowhead at its tip, then keeps turning"""
    kr = ramp(t, *t_in, e_out)
    if kr <= 0.002 or op <= 0.003: return
    spin = 38.0 * max(0.0, t - t_in[0])
    a0 = -90.0 + spin; a1 = a0 + 300.0 * kr
    pts = [(cx + RING_R * math.cos(math.radians(a)), cy + RING_R * math.sin(math.radians(a))) for a in np.linspace(a0, a1, max(8, int(120 * kr)))]
    stroke(cv, pts, INK, 7, 0.9 * op)
    ah = math.radians(a1); tx_, ty_ = cx + RING_R * math.cos(ah), cy + RING_R * math.sin(ah)
    dx, dy = -math.sin(ah), math.cos(ah); nx, ny = math.cos(ah), math.sin(ah)
    sa = 26 * ramp(t, t_in[0] + 0.1, t_in[0] + 0.35, e_out)
    if sa > 0.5:
        poly(cv, [(tx_ + dx * sa, ty_ + dy * sa), (tx_ - dx * sa * 0.6 + nx * sa * 0.75, ty_ - dy * sa * 0.6 + ny * sa * 0.75),
                  (tx_ - dx * sa * 0.6 - nx * sa * 0.75, ty_ - dy * sa * 0.6 - ny * sa * 0.75)], INK, 0.9 * op)

def listen_rise(cv, t, t0, out=None):
    """LISTEN, each letter rising up through a mask line (and dropping back through it on the way out)"""
    for i, (w_, x_) in enumerate(LISTEN_CH):
        kl = ramp(t, t0 + i * 0.06, t0 + i * 0.06 + 0.45, e_out)
        if out is not None: kl *= 1 - ramp(t, out[0] + i * 0.04, out[1] + i * 0.04, e_io)
        if kl <= 0: continue
        a_, (px_, py_), adv_ = w_
        col = np.empty(a_.shape + (3,), np.float32); col[:] = INK
        blit(cv, col, a_, T(x_ - px_, lerp(LISTEN_BASE + 175, LISTEN_BASE, kl) - py_), 1.0, clip=(0, 0, W, LISTEN_BASE + 6))

T_REPEAT2 = Text('on repeat', SER, 98, 540, 1405, LOGO_END + 0.95, DUR - 0.05, align='center', split='word', stagger=0.18, enter=0.5, exit=0.5, drift=0.04)

def word(cv, w, cx, base, op, clip=None, M=None, color=INK):
    a, (px, py), adv = w
    col = np.empty(a.shape + (3,), np.float32); col[:] = color
    Mw = T(cx - adv / 2 - px, base - py)
    if M is not None: Mw = M @ Mw
    blit(cv, col, a, Mw, op, clip=clip)

def player_ui(cv, t, pos, length, ui, heart_t):
    if ui <= 0.01: return
    hk = ramp(t, heart_t, heart_t + 0.25, e_out)  # heart: outline -> filled green
    hs = 46 * (1 + 0.25 * math.sin(math.pi * ramp(t, heart_t, heart_t + 0.35, e_io)))
    hx, hy = 945, 1318
    poly(cv, heart_pts(hx, hy, hs), INK, ui * (1 - hk))
    poly(cv, heart_pts(hx, hy + 1, hs * 0.84), BG, ui * (1 - hk))
    poly(cv, heart_pts(hx, hy, hs), GREEN, ui * hk)
    x0, x1, y = 130, 950, 1470  # progress bar: live song position
    f = pos / length
    rect(cv, x0, y - 3, x1, y + 3, rgb((77, 77, 77)), ui)
    rect(cv, x0, y - 3, x0 + (x1 - x0) * f, y + 3, INK, ui)
    circle(cv, x0 + (x1 - x0) * f, y, 10, INK, ui)
    small_text(cv, fmt(pos), MONO, 24, x0, y + 52, DIM, ui)
    small_text(cv, fmt(length), MONO, 24, x1, y + 52, DIM, ui, align='right')
    cy = 1660  # controls: previous, pause (it is playing), next
    circle(cv, 540, cy, 66, INK, ui)
    rect(cv, 520, cy - 24, 532, cy + 24, BG, ui); rect(cv, 548, cy - 24, 560, cy + 24, BG, ui)
    poly(cv, [(330, cy), (372, cy - 28), (372, cy + 28)], INK, ui); rect(cv, 318, cy - 28, 326, cy + 28, INK, ui)
    poly(cv, [(750, cy), (708, cy - 28), (708, cy + 28)], INK, ui); rect(cv, 754, cy - 28, 762, cy + 28, INK, ui)

def fmt(sec): sec = int(sec); return f'{sec // 60}:{sec % 60:02d}'
_tcache = {}
def small_text(cv, s, role, size, x, y, color, op, align='left'):
    k = (s, role, size)
    if k not in _tcache: _tcache[k] = text_img(s, role, size)
    a, (px, py), adv = _tcache[k]
    col = np.empty(a.shape + (3,), np.float32); col[:] = color
    blit(cv, col, a, T(x + {'left': 0, 'right': -adv, 'center': -adv/2}[align] - px, y - py), op)

# ---------------------------------------------------------------- frame
def frame(n):
    t = n / FPS
    cv = BGIMG.copy()
    gm = np.zeros((H, W), np.float32)

    # ===== S1: logo
    if t < 5.3:
        C, kz = camS1(t)
        k0 = ramp(t, 0.15, 1.3, e_out)
        sc = lerp(0.82, 1.0, k0) * (1 + 0.012 * math.sin(t * 1.4)) * press(t, TAP_LOGO)
        glow(cv, *apply(C, *L1), R1 * 2.6 * mscale(C), 0.16 * k0 * (1 - kz))
        ML = C @ T(*L1) @ S(sc * R1 / LOGO_R) @ T(-LOGO_C[0], -LOGO_C[1])
        if kz < 0.2: shadow(cv, LOGO_A, ML, k0, strength=0.5, blur=30, off=(0, 16))
        blit(cv, LOGO, LOGO_A, ML, k0 * (1 - ramp(t, 4.85, 5.25, e_io)))  # green dissolves to dark, library follows
        repeat_ring(cv, *L1, t, (0.6, 1.3), 1 - ramp(t, 3.45, 3.85, e_io))   # the same ring as the end card
        listen_rise(cv, t, 1.0, out=(3.4, 3.75))                            # nothing hidden behind the logo
        T_REPEAT.draw(cv, t)
        if t > 3.5: tap(cv, *L1, t, TAP_LOGO, r=70)

    # ===== S2: library grid
    if 4.7 <= t < 10.15:
        C, kz = camS2(t)
        sop = ramp(t, 5.0, 5.45, e_io)
        library_title(cv, t, C, sop)
        for i, (name, cx, cy, title, sub) in enumerate(GRID):
            te = 5.02 + i * BEAT / 2
            kp = e_out((stepped(t) - te + 0.32) / 0.4)
            other = 1.0 if name == 'saroor' else 1 - ramp(t, 9.35, 9.85, e_io)
            pr = press(t, TAP_SAROOR) if name == 'saroor' else 1.0
            draw_cover(cv, name, cx, cy, TILE * lerp(0.86, 1.0, kp) * pr,
                       sop * ramp(stepped(t), te - 0.32, te - 0.15) * other, C, gmask=gm)
        for tx in GRID_T: tx.draw(cv, t, C, sop * (1 - ramp(t, 9.3, 9.7)))
        if t > 8.5: tap(cv, *apply(camS2_base(TAP_SAROOR), 300, 1240), t, TAP_SAROOR, r=64)

    # ===== S3: carousel
    if 10.07 <= t < 15.125:
        C = camS3(t)
        for i, (name, title, sub) in enumerate(CAR):
            op = 1.0 if (i == 0 or t > 11.6) else ramp(t, 11.6, 12.3)
            draw_cover(cv, name, HERO[0] + i * SP, HERO[1], HERO[2], op, C, gmask=gm)
        for tx in CAR_T: tx.draw(cv, t, C)
        T_EVERY.draw(cv, t); T_ALBUM.draw(cv, t)

    # ===== S4: now playing (Raw Rich Rare)
    if 15.125 <= t < D_DROP:
        C, kz = camS4(t)
        draw_cover(cv, 'enigma', *HERO, 1.0, C, gmask=gm)
        ui = (1 - ramp(t, 20.177, 20.9, e_io)) * ramp(t, 15.15, 15.6)
        T_NOW.draw(cv, t); T_SONG.draw(cv, t); T_ART.draw(cv, t)
        player_ui(cv, t, t, SONG_LEN, ui, TAP_HEART)
        if t > 17.0: tap(cv, 945, 1318, t, TAP_HEART, r=52)

    # ===== S5: drop (words slide out from behind the poster / rise through a mask line), wall, flight into the chain
    if D_DROP <= t < SWAP + 0.04:
        C = camS5(t)
        wop = 1 - ramp(t, 29.95, SWAP, e_io)
        for gx, gy, name in WALL:  # wall tiles pop ring by ring on eighth notes as the camera pulls out
            ring = max(abs(gx), abs(gy))
            te = 25.23 + (ring - 1) * BEAT / 2 + ((gx + gy) % 2) * BEAT / 4
            if t < te: continue
            kp = e_out((stepped(t) - te) / 0.32)
            op = ramp(stepped(t), te, te + 0.08) * (wop if (gx, gy) != RHY else 1 - ramp(t, 29.95, SWAP + 0.03, e_io))
            draw_cover(cv, name, HERO5[0] + gx * WALL_SP, HERO5[1] + gy * WALL_SP, HERO5[2] * lerp(0.7, 1.0, kp), op, C, gmask=gm, sh=0.5)
        k = ramp(t, D_DROP, D_DROP + 0.7, e_out)
        hs = lerp(HERO[2] * S4_ZOOM, HERO5[2], k)
        hx, hy = lerp(S4_END_C[0], HERO5[0], k), lerp(S4_END_C[1], HERO5[1], k)
        if t < 25.4:
            out = ramp(t, 24.85, 25.25, e_io)
            ki = lambda t0: ramp(t, t0, t0 + 0.5, e_out) * (1 - out)
            word(cv, W_RAW, 540, lerp(800, 520, ki(D_DROP)), 1.0)                 # rises out from behind the top edge
            word(cv, W_RICH, 540, lerp(1140, 1460, ki(D_DROP + BEAT)), 1.0)       # drops out from behind the bottom edge
        draw_cover(cv, 'enigma', hx, hy, hs, wop, C, gmask=gm)
        if t < 25.4:
            out = ramp(t, 24.85, 25.25, e_io)
            kr = ramp(t, D_DROP + 2*BEAT, D_DROP + 2*BEAT + 0.5, e_out) * (1 - out)
            word(cv, W_RARE, 540, lerp(1960, 1720, kr), 1.0, clip=(0, 0, W, 1724))  # rises up through a mask line
            ku = ramp(t, D_DROP + 3*BEAT, D_DROP + 3*BEAT + 0.4, e_io) * (1 - out)
            if ku > 0.005:
                hw = W_RARE[2] / 2 * ku
                rect(cv, 540 - hw, 1752, 540 + hw, 1758, GREEN, 1.0)
        if 27.0 < t < 29.4:  # bottom shade so the credit reads over the wall
            sh_op = ramp(t, 27.0, 27.5) * (1 - ramp(t, 28.6, 29.2))
            g = np.linspace(0, 1, 420, dtype=np.float32)[:, None, None] ** 1.5 * 0.85 * sh_op
            reg = cv[H - 420:H]; reg *= (1 - g); reg += BG * g
        T_CREDIT.draw(cv, t)

    # ===== D1: National Treasures — the diamonds come one by one and lock into the glove
    if 29.6 <= t < D2_IN[1] + 0.05:
        C = camD1(t) if t < D2_IN[0] else None
        if t < D2_IN[0]:
            if t > NT_DROP - 0.1:
                kin = lambda t0: ramp(t, t0, t0 + 0.5, e_out) * (1 - ramp(t, 40.5, 40.9, e_io))
                word(cv, W_NAT, 540, lerp(560, 360, kin(NT_DROP)), 1.0, M=C)       # out from behind the top edge
                word(cv, W_TRE, 540, lerp(1290, 1525, kin(NT_DROP + NT_BEAT)), 1.0, M=C)  # out from behind the bottom
            if t > SWAP - 0.1:
                a = reveal_alpha(t)
                blit(cv, ICE, a, C @ place(*CC1, S1C, 0, 750, 750), 1.0, gm)
            for i in range(ND):
                s0 = LAND[i] - FLY[i]
                if t < s0 or t > LAND[i] + 0.4 or t < SWAP - 0.25: continue
                u = clamp((t - s0) / FLY[i]); e = e_out(u)
                tx, ty = dia_world(i)
                ang = TH0[i] + SWIRL[i] * (1 - e)
                rr = RAD0[i] * (1 - e)
                x, y = tx + math.cos(ang) * rr, ty + math.sin(ang) * rr
                big = 6.0 if D_ORDER.index(i) < FIRST else 2.2
                sc = lerp(big, 1.0, e) * S1C
                op = ramp(u, 0, 0.12) * (1 - ramp(t, LAND[i] + 0.1, LAND[i] + 0.4))
                blit(cv, PATCH[i], PATCH_A, C @ T(x, y) @ S(sc) @ T(-PR, -PR), op)
                if GLINT_ON[i] and LAND[i] - 0.03 < t < LAND[i] + 0.45:
                    gk = ramp(t, LAND[i] - 0.03, LAND[i] + 0.05, e_out) * (1 - ramp(t, LAND[i] + 0.05, LAND[i] + 0.45, e_io))
                    gx_, gy_ = apply(C, tx, ty)
                    glint(cv, gx_, gy_, (150 if D_ORDER.index(i) < FIRST else 48), 0.9 * gk)
            if NT_DROP - 0.03 < t < NT_DROP + 0.6:  # every diamond flashes on the drop
                gk = ramp(t, NT_DROP - 0.03, NT_DROP + 0.05, e_out) * (1 - ramp(t, NT_DROP + 0.05, NT_DROP + 0.6, e_io))
                for i in D_ORDER[:40]:
                    gx_, gy_ = apply(C, *dia_world(i)); glint(cv, gx_, gy_, 70, 0.8 * gk)
            T_DRAKE.draw(cv, t)
    # ===== D2: player -> dive through the OK sign -> official video (full, then split) -> cover back; D3 lift
    if D2_IN[0] <= t < LOGO_END + 0.6:
        cx, cy, cs = ice_cover_geom(t)
        Mc = place(cx, cy, cs / 1500, 0, 750, 750)
        if HOLE[0] <= t < SPLIT[0]: Mc = camHole(t) @ Mc
        cop = 1 - ramp(t, LIFT - 0.05, LIFT + 0.5, e_io)
        show_cover = not (MV_FULL_IN[1] <= t < SPLIT[0])
        if cop > 0.002 and show_cover:
            if not (HOLE[0] <= t < SPLIT[0]):
                shadow(cv, ICE_A, Mc, cop, strength=0.6, blur=cs * 0.05, off=(0, int(cs * 0.03)))
            blit(cv, ICE, ICE_A, Mc, cop, gm)
        if MV_FULL_IN[0] <= t < SPLIT_OUT[1] + 0.05:
            img, mt, shown = mv_frame(t)
            ks = ramp(t, *SPLIT, e_io)                       # 0: full-bleed vertical crop -> 1: 16:9 top panel
            ko = ramp(t, *SPLIT_OUT, e_io)                   # panel slides up and away
            xs = float(np.clip(mv_x(shown) * 2560, 405, 2155))
            s_full = 1920 / 1440 * lerp(1.06, 1.0, ramp(t, MV_FULL_IN[0], SPLIT[0], e_sine))   # slow zoom-out
            sc = lerp_exp(s_full, 1080 / 2560, ks)
            M = T(540, lerp(lerp(960, 560, ks), -420, ko)) @ S(sc) @ T(-lerp(xs, 1280, ks), -720)
            blit(cv, img, MV_A, M, ramp(t, *MV_FULL_IN) * (1 - ramp(t, SPLIT_OUT[0] + 0.3, SPLIT_OUT[1], e_io)), gm)
            if MV_FULL_IN[1] - 0.1 < t < SPLIT[0] + 0.3:     # bottom shade for the credit line
                sh_op = ramp(t, 46.4, 46.9) * (1 - ramp(t, SPLIT[0] - 0.2, SPLIT[0] + 0.2))
                g = np.linspace(0, 1, 380, dtype=np.float32)[:, None, None] ** 1.5 * 0.8 * sh_op
                reg = cv[H - 380:H]; reg *= (1 - g); reg += BG * g
            T_MV1.draw(cv, t); T_MV2.draw(cv, t)
        if SPLIT[0] <= t < SPLIT_OUT[1] and cop > 0.002:     # cover drawn over the shrinking video during the split
            shadow(cv, ICE_A, Mc, cop, strength=0.6, blur=cs * 0.05, off=(0, int(cs * 0.03)))
            blit(cv, ICE, ICE_A, Mc, cop, gm)
        ui = ramp(t, 41.35, 41.85) * (1 - ramp(t, UI2_OUT, UI2_OUT + 0.55, e_io))
        T_NOW2.draw(cv, t); T_SONG2.draw(cv, t); T_ART2.draw(cv, t)
        player_ui(cv, t, t - NT_OFF, NT_LEN, ui, TAP_HEART2)
        if TAP_HEART2 - 0.6 < t < UI2_OUT: tap(cv, 945, 1318, t, TAP_HEART2, r=52)
        # sparkle: a few diamonds catch the light on each beat (player and split)
        if 41.8 < t < UI2_OUT or 49.8 < t < SPLIT_OUT[0]:
            b = int((t - SWAP) / NT_BEAT); tb = SWAP + b * NT_BEAT
            gk = ramp(t, tb, tb + 0.06, e_out) * (1 - ramp(t, tb + 0.06, tb + 0.4, e_io))
            rs = np.random.default_rng(500 + b)
            for i in rs.choice(80, 3, replace=False):
                px, py = apply(Mc, *DIA[i]); glint(cv, px, py, 64 * cs / HERO[2], 0.75 * gk)
        if t >= LIFT - 0.1:
            Ml = place(cx, cy, cs / 1500, 0, 750, 750)  # geometry frozen once the push-in has finished
            for i in range(ND):
                p0 = apply(Ml, *DIA[i])
                u = clamp((t - DEP[i]) / FLY3); e = e_io(u)
                r0 = math.hypot(p0[0] - END_L[0], p0[1] - END_L[1]); a0 = math.atan2(p0[1] - END_L[1], p0[0] - END_L[0])
                r1 = math.hypot(TGT[i][0] - END_L[0], TGT[i][1] - END_L[1]); a1 = math.atan2(TGT[i][1] - END_L[1], TGT[i][0] - END_L[0])
                da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi + 2 * math.pi * 0.45   # vortex: everyone turns the same way
                ang = a0 + da * e
                rr = lerp(r0, r1, e) + 140 * math.sin(math.pi * e)
                x, y = END_L[0] + rr * math.cos(ang), END_L[1] + rr * math.sin(ang)
                sc = lerp(cs / 1500, 0.86, e)
                kc = ramp(u, 0.35, 0.95)
                img = PATCH[i] * (1 - kc) + TCOL[i] * kc
                op = ramp(t, LIFT - 0.1, LIFT + 0.3) * (1 - ramp(t, LOGO_END + 0.05, LOGO_END + 0.5))
                blit(cv, img.astype(np.float32), PATCH_A, T(x, y) @ S(sc) @ T(-PR, -PR), op)
    # ===== end card: logo glides up, a repeat ring draws around it, LISTEN rises below, on repeat, fade to black
    if t >= LOGO_END - 0.4:
        k = ramp(t, LOGO_END - 0.2, LOGO_END + 0.4, e_io)
        kg = ramp(t, LOGO_END + 0.2, LOGO_END + 0.85, e_io)
        lx, ly = lerp(END_L[0], END_CARD_L[0], kg), lerp(END_L[1], END_CARD_L[1], kg)
        lr = lerp(END_R, END_CARD_R, kg)
        glow(cv, lx, ly, lr * 2.6, 0.16 * k)
        ML = T(lx, ly) @ S(lr / LOGO_R) @ T(-LOGO_C[0], -LOGO_C[1])
        shadow(cv, LOGO_A, ML, k, strength=0.5, blur=30, off=(0, 16))
        blit(cv, LOGO, LOGO_A, ML, k)
        # repeat ring: draws on clockwise from the top, arrowhead at its tip, then keeps turning
        kr = ramp(t, *RING_IN, e_out)
        if kr > 0.002:
            spin = 38.0 * max(0.0, t - RING_IN[0])                  # degrees
            a0 = -90.0 + spin; a1 = a0 + 300.0 * kr
            pts = [(lx + RING_R * math.cos(math.radians(a)), ly + RING_R * math.sin(math.radians(a)))
                   for a in np.linspace(a0, a1, max(8, int(120 * kr)))]
            stroke(cv, pts, INK, 7, 0.9)
            ah = math.radians(a1); tx_, ty_ = lx + RING_R * math.cos(ah), ly + RING_R * math.sin(ah)
            dx, dy = -math.sin(ah), math.cos(ah)                    # direction of travel (clockwise)
            nx, ny = math.cos(ah), math.sin(ah)
            sa = 26 * ramp(t, RING_IN[0] + 0.1, RING_IN[0] + 0.35, e_out)
            if sa > 0.5:
                poly(cv, [(tx_ + dx * sa, ty_ + dy * sa), (tx_ - dx * sa * 0.6 + nx * sa * 0.75, ty_ - dy * sa * 0.6 + ny * sa * 0.75),
                          (tx_ - dx * sa * 0.6 - nx * sa * 0.75, ty_ - dy * sa * 0.6 - ny * sa * 0.75)], INK, 0.9)
        # LISTEN: each letter rises up through a mask line, one after another
        for i, (w_, x_) in enumerate(LISTEN_CH):
            t0 = LOGO_END + 0.55 + i * 0.06
            kl = ramp(t, t0, t0 + 0.45, e_out)
            if kl <= 0: continue
            a_, (px_, py_), adv_ = w_
            col = np.empty(a_.shape + (3,), np.float32); col[:] = INK
            blit(cv, col, a_, T(x_ - px_, lerp(LISTEN_BASE + 175, LISTEN_BASE, kl) - py_), 1.0, clip=(0, 0, W, LISTEN_BASE + 6))
        T_REPEAT2.draw(cv, t)

    cv = np.clip(cv, 0, 1)
    cv = bloom(cv)
    cv = grain(cv, n, gm)
    f = ramp(t, DUR - 0.55, DUR - 0.02, e_io)  # fade to black (matches frame 0)
    if f > 0: cv = cv * (1 - f) + BGIMG * f
    return np.clip(cv, 0, 1)

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stills'); ap.add_argument('--range'); ap.add_argument('--out', default=os.path.join(ROOT, 'out', 'picture.mp4'))
    a = ap.parse_args()
    sd = os.path.join(ROOT, 'out', os.environ.get('STILLS', 'stills')); os.makedirs(sd, exist_ok=True)
    if a.stills:
        for s in a.stills.split(','):
            n = int(round(float(s) * FPS))
            Image.fromarray((frame(n) * 255 + 0.5).astype(np.uint8)).save(os.path.join(sd, f'f{n:04d}.png'))
        return
    n0, n1 = 0, NFRAMES
    if a.range:
        s0, s1 = map(float, a.range.split(',')); n0, n1 = int(s0 * FPS), int(s1 * FPS)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p',
           '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', a.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(n0, n1):
        p.stdin.write((frame(n) * 255 + 0.5).astype(np.uint8).tobytes())
        if n % 50 == 0: print(f'{n}/{n1}', flush=True)
    p.stdin.close(); p.wait()
    print('done', a.out)

if __name__ == '__main__':
    main()
