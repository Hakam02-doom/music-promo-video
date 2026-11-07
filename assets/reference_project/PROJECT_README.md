# Spotify — dark editorial film, v8 (editable project)

Output: 1080×1920, 120 fps (a 60 fps export is also provided), 58.2 s, H.264 + AAC. All-dark stage.
v8 = v7 with the "your LIBRARY" title fixed: it now scrolls with the page above the covers (never covered), LIBRARY rises through a mask line with a green underline, and Playlists / Albums chips sit under it (Albums lights up on the beat). v7 = v6 with the opening redesigned like the end card (nothing hidden behind the logo) and rendered at 120 fps. v6 = v5 with a smooth low-to-high handoff between the songs (the DJ roll and its camera punches are gone) and a high-to-low fade at the end.

## Files
- `render.py` — the whole picture edit as code: scenes, camera, text, diamond particles, timing (TIMELINE section).
- `audio.py` — the mix: song envelopes, the DJ-style handoff between the two songs, and an SFX cue table.
- `style.json` — look settings: background, ink, green, grain, bloom, fps, stepped-text rate, fonts.
- `src/logo.png`, `src/covers/` (official cover art + `provenance.json`), `src/audio/` (both songs, SFX used).
- `src/video/mv_frames/`: the frames used from the official video (video time 34.4–41.8 s, 24 fps). The full source video is external: `Drake - National Treasures 1440P.mp4`.

## Rebuild
```
python3 -m venv .venv && .venv/bin/pip install numpy pillow opencv-python-headless scipy
.venv/bin/python audio.py                  # -> out/mix_full.wav, out/mix_sfx_only.wav
.venv/bin/python render.py                 # -> out/picture.mp4 (fps from style.json: 120)
.venv/bin/python render.py --stills 24,33  # test frames
ffmpeg -i out/picture.mp4 -i out/mix_full.wav -map 0:v -map 1:a -c:v libx264 -crf 20 -tune grain -pix_fmt yuv420p -c:a aac -b:a 256k final.mp4
```
External dependencies: macOS system fonts (Helvetica Neue, Didot, Menlo) and ffmpeg.

## Structure
| Film time | Scene |
|---|---|
| 0–5.0 | Spotify logo with the same repeat ring as the end card; LISTEN rises letter by letter below it through a mask line (nothing hidden), "*on repeat*"; the words drop away, a tap, zoom into the green |
| 5.0–10.1 | Library grid. The "your LIBRARY" title scrolls with the page above the first row: LIBRARY rises letter by letter through a mask line, a green underline draws, and Playlists / Albums chips pop in, with Albums lighting up green on the downbeat. Tiles land on the beat, tap Saroor, zoom in. |
| 10.1–15.1 | "EVERY *album*," carousel, ends on Enigma |
| 15.1–22.7 | Now playing Raw Rich Rare, heart tap, push into the cover while the song climbs |
| 22.7–25.3 | Drop: **RAW** rises out from behind the poster, *rich* drops out from behind it, **RARE** rises through a mask line with a green underline. No word touches the artwork. |
| 25.2–30.3 | Wall of covers, then a dive through the 48 Rhymes chain into black |
| 30.3–37.8 | National Treasures (song 0:19): a faint ghost of the glove appears. Eight diamonds fly in one by one on the beat, then hundreds pour in and lock into place. |
| 37.8–40.9 | The full ICEMAN cover. On Drake's drop, **NATIONAL** rises from behind the poster and *treasures* drops from behind it. |
| 40.9–45.2 | Now playing National Treasures (live progress), heart tap, diamonds glint on the beat |
| 45.2–46.2 | The camera dives through the hole of the glove's OK sign into black |
| 46.0–48.9 | The official video fades up out of that black, full-screen and in sync with the song (vertical crop that follows Drake shot by shot, slow zoom-out) |
| 48.9–51.9 | The video reframes into a 16:9 top panel while the ICEMAN cover rises into the bottom half; its diamonds glint on the beat |
| 51.9–52.6 | The panel slides away; the cover glides back to centre |
| 52.6–55.4 | Every diamond lifts off and spirals into the Spotify logo |
| 55.4–58.2 | End card: the logo glides up, a white repeat ring with an arrowhead draws itself around it and keeps turning, **LISTEN** rises letter by letter through a mask line below it (nothing hidden), "*on repeat*" settles underneath, fade to black (matches frame 0) |

## Sound
- Raw Rich Rare plays from 0:00 in sync with the picture: −22 dB, then an accelerating climb to loud at the drop (22.70 s).
- Handoff at 30.283 s, as a smooth breakdown. National Treasures' downbeat at song time 0:19.3 is laid onto Raw Rich Rare's downbeat. Over RRR's last bar (from 27.76 s) it darkens with a low-pass filter and drops about 26 dB, with a soft echo of its last half-beat drifting away. NT fades in underneath (−40 → −22 dB) with its bass filtered out, then climbs from low to high (−22 → −4 dB) through its build while the bass returns over its first bar, and hits Drake's drop at 0:27.7 (film 38.67 s).
- Measured: about −12 dB RMS at the end of RRR, −34 dB at the handoff, rising through −29, −24 and −22 dB to −13 dB after the drop.
- Ending: from the diamonds lifting off (52.6 s), NT goes from high to low (−34 dB) and darkens into the distance; the last 0.2 s is silence.
- SFX: the SaaS pack on taps, zooms and moves. The diamond "ting" (quieter in v6) plays on each of the first eight diamonds, on every sixth diamond of the pour (varied pitch and pan), when the glove locks, on the drop, as the player's glints, and when the logo forms.

## Covers
| Cover | Source |
|---|---|
| ICEMAN (Drake), 3000 px | Apple Music artwork |
| Saroor, Majhaestic, Young G.O.A.T, ANYWAY, 48 Rhymes, Dhurandhar The Revenge art, 1200 px | Apple Music artwork |
| Enigma, 500 px | JioSaavn |
| Liked Songs | redrawn |
