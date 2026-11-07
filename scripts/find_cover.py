#!/usr/bin/env python3
"""Find official high-resolution cover art that matches a cover seen in a screenshot.

usage:
  find_cover.py --screenshot shot.jpg --box 33,750,333,1050 --query "Saroor" --query "Arjan Dhillon" \
                --name saroor --out covers/
  find_cover.py --crop tile.png --query "National Treasures Drake" --name iceman --out covers/

Searches Apple/iTunes (albums + songs, several storefronts; artwork up to 3000 px) and JioSaavn (500 px),
ranks every candidate by similarity to the screenshot crop (normalised 32x32 correlation, 1.0 = identical),
downloads the best one if it scores >= --min (default 0.95), and records provenance in <out>/provenance.json.
Always check the top candidates it prints: the album art of a track may differ from what you'd guess, and the
now-playing thumbnail in the user's screenshot is the ground truth.
"""
import argparse, io, json, os, urllib.parse, urllib.request
import numpy as np
from PIL import Image

UA = {'User-Agent': 'Mozilla/5.0 (cover-lookup)'}
def get(u, timeout=25): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout).read()
def feat(im):
    a = np.asarray(im.convert('RGB').resize((32, 32), Image.LANCZOS)).astype(np.float32); a -= a.mean()
    return a / (np.linalg.norm(a) + 1e-6)

def itunes(q, countries):
    out = []
    for c in countries:
        for ent in ('album', 'song'):
            try: d = json.loads(get(f'https://itunes.apple.com/search?term={urllib.parse.quote(q)}&entity={ent}&limit=25&country={c}'))
            except Exception: continue
            for r in d.get('results', []):
                u = r.get('artworkUrl100')
                if u: out.append({'thumb': u, 'hi': u.replace('100x100bb', '3000x3000bb'), 'title': r.get('collectionName'),
                                  'artist': r.get('artistName'), 'source': 'Apple Music / iTunes', 'link': r.get('collectionViewUrl')})
    return out

def saavn(q):
    out = []
    try:
        d = json.loads(get('https://www.jiosaavn.com/api.php?__call=autocomplete.get&query=' + urllib.parse.quote(q) +
                           '&_format=json&_marker=0&ctx=web6dot0'))
    except Exception: return out
    for sec in ('albums', 'songs'):
        for r in d.get(sec, {}).get('data', []):
            u = r.get('image')
            if u: out.append({'thumb': u.replace('50x50', '150x150'), 'hi': u.replace('50x50', '500x500'), 'title': r.get('title'),
                              'artist': r.get('description'), 'source': 'JioSaavn', 'link': r.get('url')})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--screenshot'); ap.add_argument('--box', help='x0,y0,x1,y1 of the cover in the screenshot')
    ap.add_argument('--crop', help='an image of just the cover (instead of --screenshot/--box)')
    ap.add_argument('--query', action='append', required=True); ap.add_argument('--name', required=True)
    ap.add_argument('--out', default='covers'); ap.add_argument('--min', type=float, default=0.95)
    ap.add_argument('--countries', default='us,in,gb,ca')
    a = ap.parse_args()
    if a.crop: ref = Image.open(a.crop)
    else:
        x0, y0, x1, y1 = map(int, a.box.split(',')); ref = Image.open(a.screenshot).crop((x0, y0, x1, y1))
    rf = feat(ref)
    cands, seen = [], set()
    for q in a.query:
        for c in itunes(q, a.countries.split(',')) + saavn(q):
            if c['thumb'] in seen: continue
            seen.add(c['thumb'])
            try: c['score'] = float((feat(Image.open(io.BytesIO(get(c['thumb'])))) * rf).sum())
            except Exception: continue
            cands.append(c)
    cands.sort(key=lambda c: -c['score'])
    for c in cands[:6]: print(f"{c['score']:.3f}  {c['title']} | {c['artist']} | {c['source']}")
    if not cands or cands[0]['score'] < a.min:
        print('no confident match; try other queries (artist name, album name, track name) or redraw/omit this cover'); return
    # among near-identical matches prefer the higher-resolution source (Apple artwork goes up to 3000 px)
    top = [c for c in cands if c['score'] >= cands[0]['score'] - 0.01]
    best = sorted(top, key=lambda c: (c['source'] != 'Apple Music / iTunes', -c['score']))[0]
    os.makedirs(a.out, exist_ok=True)
    data = None
    for u in (best['hi'], best['hi'].replace('3000x3000bb', '1200x1200bb')):
        try: data = get(u, 60); break
        except Exception: continue
    path = os.path.join(a.out, a.name + '.jpg'); open(path, 'wb').write(data)
    w, h = Image.open(path).size
    pv = os.path.join(a.out, 'provenance.json')
    prov = json.load(open(pv)) if os.path.exists(pv) else {}
    prov[a.name] = {'title': best['title'], 'artist': best['artist'], 'source': best['source'], 'artwork_url': best['hi'],
                    'link': best['link'], 'size': [w, h], 'match_vs_screenshot': round(best['score'], 3)}
    json.dump(prov, open(pv, 'w'), indent=1)
    print(f'saved {path} ({w}x{h}), match {best["score"]:.3f}')

if __name__ == '__main__':
    main()
