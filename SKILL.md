---
name: music-promo-video
description: Build a polished vertical promo or edit video for a music app, artist, album, playlist or song (Spotify-style ad, reel, TikTok/Instagram edit). It starts by asking for 3-4 style references that shape the result, then assembles the video in code from the user's logo, app screenshots, songs, sound effects and music-video clips. It covers official high-res cover art, kinetic typography, smooth matched zooms, beat-synced songs with seamless low-to-high handoffs, particle cover animations, 60/120 fps exports, QA and delivery. Use this skill whenever someone wants a video made from a logo, screenshots, album covers, songs or a music video, even when they don't say "promo", e.g. "make an ad with these Spotify screenshots and this song", "edit a reel for this track", "put this music video and cover into an animation", or when continuing or revising such a video.
---

# Music promo video

Make a vertical (default 1080×1920) promo video that feels like one continuous, premium piece. A logo opens it. App pages, covers and players flow into each other through smooth camera moves. Songs play under the picture on the beat. A matching end card closes it, so the video loops.

This skill packages a workflow that was refined through many rounds of real user feedback. The rules in `references/direction.md` are that feedback, turned into principles. Read them before designing anything: they are the difference between "nice" and "this is what I wanted".

## 0. Intake: ask for references first

Before planning or building anything, ask the user for **3–4 references** that should shape the output. The references decide the look, so the video depends on them. Ask in one friendly message, together with the asset checklist below, so the user answers once.

Ask for:
- **3–4 references**: videos (best: they carry motion and pacing), reels, images, or links to them. For each, ask what they like about it: the look, the colour, the typography, the transitions, the pacing, the sound. If the user offers only links you can't open (Instagram, Pinterest, TikTok), ask for the downloaded file or screenshots. Never claim to have watched something you couldn't open.
- If they send fewer than 3, ask once more and explain that more references give a closer result. If they still can't, proceed with what you have and say which choices you made yourself.
- If they send more than 4, ask which 4 matter most, or weight the first ones.

Asset checklist (ask in the same message, and accept "you choose" for anything):
1. Logo (PNG with transparency is best).
2. App screenshots (home screen, library, now playing), which show what's real.
3. Songs: the audio files plus the **hook start and end time** for each (users know their hook; don't guess it from lyrics).
4. Sound-effect pack (optional).
5. Official music video files (optional, for in-sync clips).
6. Format, length goal, frame rate (default 1080×1920, 60 fps), and where it will be posted.

Then study the references properly (see `references/references-analysis.md`): contact sheets and dense frame sequences for motion. Write a short **reference brief**: palette, typography roles, pacing (cuts per bar), transition types, texture (grain, bloom, paper or none), how text and images interact, and the sound character. Show the brief to the user in a few lines with your plan, then build without waiting for more approval unless something blocks you.

When the references conflict with a rule in `references/direction.md`, follow the user's explicit words first, then the references, then the defaults.

## 1. Check the environment

You need ffmpeg and Python with numpy, pillow, opencv-python-headless and scipy (make a venv in the work folder). Fonts are system fonts; check that each of the three type roles resolves. If an essential capability is missing, say exactly what and stop the dependent step; don't present a plan as a finished video.

## 2. Source and verify assets

- **Cover art:** never use crops from screenshots as the visible cover. They're too soft, and users notice. Find the official artwork online with `scripts/find_cover.py`, which searches Apple/iTunes (up to 3000 px) and JioSaavn and matches each candidate against the screenshot crop. Accept only matches of about 0.98 or higher, and record provenance (source URL, title, artist, match score) in `covers/provenance.json`. If nothing matches (e.g. Spotify-generated mixes or radios), redraw a sharp vector version when it's a simple design (Liked Songs), or leave that item out.
- **Songs:** copy them in, then run `scripts/beat_grid.py` on each: tempo, downbeats, energy per half-second, and the biggest energy jump (the drop). Ask the user for hook times rather than inferring them from transcription.
- **Music video:** `scripts/av_sync.py` gives the offset between the video's audio and the song file, so picture and song stay in lip sync. `scripts/shot_cuts.py` finds the video's own cuts, so the crop can follow the subject per shot.
- **SFX:** characterise each file (length, peak position, brightness), give it a role (tap/click, whoosh, riser, pop, chime, rumble, special), and note each file's peak offset so cues land on the peak.

## 3. Plan the timeline on the beat grid

- Treat film time as song time while a song plays (film t = song t + offset). Put scene changes on downbeats, and pops and stop-motion steps on beats or eighths.
- Typical arc, adapt it to the brief: **logo opening** → **library or app page** → **album carousel** → **now playing** (live progress bar) → **drop moment** (big kinetic words) → **wall of covers** → handoff into the **next song** with its own cover animation → its **player** → optional **music-video section** → **particle finale** into the logo → **end card** matching the opening.
- Every change between scenes must be a continuous move: a zoom into an element that becomes the next scene, a matched cut (the same image in the same place on both sides), or a fly-through into a dark area. List each transition's mechanism in the plan.
- Text rules: no word ever sits on top of artwork, and no word is left hidden behind a logo or cover. Words slide out from behind an object's edge, or rise through a mask line, and then sit fully visible. Titles that sit above scrolling content belong to that content (world coordinates), so tiles never cover them.

See `references/direction.md` for the full set of visual rules and why each exists.

## 4. Build

Start from the worked example in `assets/reference_project/`: `render.py` (picture engine plus a full 58 s timeline), `audio.py` (mix) and `style.json`. It already contains tested building blocks:
- compositing with blur prefiltering, soft shadows and clipping;
- per-frame film grain and bloom;
- the three-role `Text` class (sans, serif italic, mono) with eased entries, stop-motion entries and drift exits;
- mask-line word reveals and slide-from-behind reveals;
- tap ripples with a press effect; a vector player UI with a live progress bar and heart tap; the repeat-ring end card;
- the diamond particle system (assemble a cover piece by piece; lift it off into the logo);
- music-video playback with frame blending and per-shot crops;
- the filter-sweep, envelope and SFX cue tools.

Keep the engine; replace the timeline and content with the new project's. Read `references/engine-notes.md` for the architecture and the pitfalls already solved.

Work in this order:
1. Text and layout tests: render 10–20 stills across the timeline, make a contact sheet, look at it, and fix layout problems before any long render.
2. The mix (`audio.py`): it's fast, so measure levels per second and around every handoff (`references/audio.md`).
3. A full render in the background (60 fps takes about 10 minutes for 60 s on a laptop; 120 fps about 25). Don't poll; wait for the completion notice.

## 5. QA the actual export

Run `scripts/motion_qa.py` on the final MP4. It reports frame-to-frame jumps, stop-motion steps, frozen frames and abnormally dark frames. For every spike that isn't an intentional step or a music-video cut, extract the consecutive frames around it and look at them. Then check:
- duration, fps, frame count and full decode;
- loudness (−11 to −14 LUFS integrated, peak about −1 dBFS, no distortion);
- per-second levels and handoff levels;
- both sides of every transition;
- text legibility at phone size.

Report honestly: you can measure audio but can't listen. Say so, and ask the user to check by ear.

For small fixes, re-render only the affected time range (`render.py --range a,b`) and splice it into the master render with frame-exact trims. Re-mux and re-check the seams. See `references/qa-and-delivery.md`.

## 6. Deliver early and iterate

- Send a playable MP4 as soon as a version is complete, even mid-way through a longer change. Users often ask "is it done?" and want to watch while you continue.
- Each round: re-read the user's words carefully. They often type quickly and cut off mid-sentence. Apply exactly what they asked, keep everything else frame-identical, and say what changed. If a message is cut off, do the clear part and ask for the rest.
- Keep previous versions (`archive_vN/`), and name deliverables with the version and fps.

Deliverables each round:
- main MP4 (60 fps for posting; 120 fps only on request, and explain that social platforms play at 60 at most);
- the same video with sound effects only, no songs (for posting with platform-licensed music);
- an editable project zip: code, style settings, covers with provenance, frames used from the video, SFX used, the mix WAVs and a README with the timeline;
- a short note on what changed, what was checked and what wasn't, plus a reminder that the songs, cover art and video clips are copyrighted: fine for personal edits, but platforms may mute or claim public posts.

## Reference files

- `references/direction.md`: the visual and editorial rules learned from user feedback. Read before designing.
- `references/references-analysis.md`: how to study the user's 3–4 references and write the brief.
- `references/audio.md`: song envelopes (low to high, high to low), seamless beat-matched handoffs, SFX placement, loudness.
- `references/engine-notes.md`: architecture of the reference engine, and pitfalls already solved.
- `references/qa-and-delivery.md`: checks, partial re-render and splice, encoding, packaging.
- `scripts/`: `beat_grid.py`, `find_cover.py`, `av_sync.py`, `shot_cuts.py`, `motion_qa.py` (run each with `-h` for usage).
- `assets/reference_project/`: the complete worked example (Spotify promo, "Raw Rich Rare" into Drake's "National Treasures").
