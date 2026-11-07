# Engine notes (assets/reference_project)

`render.py` is a frame-by-frame compositor in numpy/OpenCV/Pillow that pipes raw RGB frames to ffmpeg (libx264). Every frame is a pure function of its index, so any range can be re-rendered and spliced.

## Architecture
- **Coordinates:** 3×3 affine matrices (`T`, `S`, `R`, `place`). Each scene has a camera function `cam*(t)` returning a matrix that maps world to screen. Things that belong to a page (titles, tiles, labels) are drawn through the camera; screen-fixed text is drawn without it.
- **Layer order in a frame:** background → text that goes behind objects → objects (covers, logo, UI) → front text → bloom → grain. Clean authored text can be drawn after the grain if it must stay crisp.
- `blit(canvas, rgb, alpha, M, op, mask_acc, clip)`: warps only into the destination's bounding box, prefilters strong downscales (prevents shimmering on big covers shown small), and `clip` gives mask-line reveals in screen space.
- `shadow()`: blurred alpha rendered at quarter resolution.
- `Text`: roles `sans`, `serif_italic`, `mono`; per-letter or per-word groups; eased rise, blur and fade in; drift and blur out; optional stepped (stop-motion) entry; optional camera `C` for page-attached text.
- `word()`, `listen_rise()`, `library_title()`: slide-from-behind and mask-line reveals.
- `tap()` and `press()`: the tap ripple and press scale. `player_ui()`: the vector now-playing UI with live progress. `repeat_ring()`: the end-card ring.
- **Particles:** `_diamonds()` finds the pieces; `reveal_alpha()` builds the splat-map reveal; landing schedule arrays `LAND`, `FLY` and `D_ORDER`; finale targets `_logo_targets()` (Poisson disc inside the logo).
- **Music video:** `mv_frame(t)` gives frame-blended footage synced via `MV_SYNC`, never blending across `MV_CUTS`; `mv_x()` gives the per-shot crop centre.
- `style.json`: universal look settings (colours, grain, bloom, fps, stepped rate, fonts). Keep project timecodes out of it.
- `audio.py` imports `render` for shared timeline constants (SWAP, drops, landing times), so picture and sound can't drift apart.

## Pitfalls already solved (don't reintroduce)
- **The PNG logo's arcs were transparent holes:** a photo showed through them. Back the logo disc with white.
- **Zoom target swing:** move the target's screen position, not the world focus.
- **Ease-in-only zooms:** detail flashes across the frame; ease both ends and aim at solid colour.
- **One-frame disappearances**, even of dark layers, read as pops. Fade over 0.2–0.3 s.
- **Shell variable splitting:** zsh doesn't split `$VAR` into words; write ffmpeg options out in full.
- **`rm` with globs** after `cd` can be blocked by safety checks. Write test stills to a new folder (env `STILLS=name`) instead of deleting.
- **Stepped clock:** rate must divide fps exactly (15 for 60 and 120). 12.5 suits 25 fps only.
- **Covers from screenshots** look soft: use official art.
- **AV1 sources (some downloaded music videos):** extract the needed span to JPEG frames once (`ffmpeg -ss a -i mv.mp4 -t d -q:v 2 frames/f%04d.jpg`) and read frames from disk.

## Performance
On an Apple-silicon laptop, about 5 frames/s at 1080×1920. So 60 s takes about 12 min at 60 fps and about 25 min at 120 fps. Run full renders in the background and wait for the notification. Stills (`--stills t1,t2,...`) take seconds; use them for every layout decision first.
