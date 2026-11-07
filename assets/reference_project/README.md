# Reference project (worked example)

The complete code of a finished 58 s, 1080×1920, 60/120 fps Spotify promo, made with this workflow:
- logo opening with a repeat ring;
- library grid with a scrolling title and filter chips;
- album carousel;
- Raw Rich Rare now-playing screen, drop words and a cover wall;
- a seamless handoff into Drake's "National Treasures";
- the diamond glove assembly and player;
- an in-sync music-video section (full-bleed, then split with the cover);
- diamonds forming the logo, and the end card.

`PROJECT_README.md` is that project's own README: the timeline table and sound notes.

Media isn't included (copyrighted and large). The code expects this layout next to it:
```
src/logo.png                      logo with transparency
src/covers/<name>.jpg             official covers (scripts/find_cover.py) + provenance.json
src/video/mv_frames/f0000.jpg...  frames extracted from the music video span used
src/audio/<song>.mp3, SFX files   songs and sound effects named in audio.py
```
Use it as an engine. Keep the building blocks (compositing, Text, reveals, taps, player UI, particles, music-video playback, filter sweeps, cue placement), and replace the TIMELINE constants, scene blocks and content with the new project's.

Run:
```
python render.py --stills 2,9,24       # quick frames for layout checks -> out/$STILLS/
python audio.py                        # mixes -> out/mix_full.wav, out/mix_sfx_only.wav
python render.py --out out/master.mp4  # full render at style.json fps
python render.py --range 4.6,10.2 --out out/fix.mp4   # partial re-render for splicing
```
