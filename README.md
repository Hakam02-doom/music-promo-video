# music-promo-video: a Claude skill

A [Claude skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) for making polished vertical (1080×1920) promo and edit videos for music apps, artists, albums, playlists and songs, in the style of a Spotify ad, an Instagram reel or a TikTok edit. Claude builds the whole video in code from your logo, app screenshots, songs, sound effects and music-video clips, then renders, checks and exports it.

## What it does
- **Starts from your references.** It asks for 3–4 reference videos or images and what you like about each, studies them frame by frame, and writes a style brief that shapes the result.
- **Official high-res cover art.** It finds the original artwork online (Apple Music up to 3000 px, JioSaavn) and checks each one against your screenshot before using it.
- **Everything merges.** It uses smooth, eased zooms in and out, matched cuts, zoom-throughs into a logo, a tapped tile or a dark area of a cover, and a logo-first opening with a matching end card so the video loops.
- **Clean kinetic typography.** Three type roles (sans, serif italic, mono); words never sit on top of artwork and are never left hidden behind logos; reveals slide out from behind edges or rise through mask lines.
- **Songs on the beat.** It maps the beat grid and finds the drop. Songs go low → high into the drop, hand off seamlessly and beat-matched to a second song, and fade high → low at the end. Sound effects land on taps and moves.
- **Showpieces.** A recreated now-playing player with a live progress bar and heart tap; a piece-by-piece particle cover animation (e.g. diamonds assembling into a cover, then spiralling into the logo); official music-video footage in lip sync, cropped per shot.
- **QA and delivery.** Motion checks for jumps, freezes and dark frames; loudness checks; partial re-render and splice for small fixes; 60 fps for posting (120 fps on request); a sound-effects-only version; and an editable project zip.

## Contents
```
SKILL.md                      workflow Claude follows
references/
  direction.md                visual and editorial rules, each with its reason
  audio.md                    song envelopes, seamless handoffs, SFX, loudness
  references-analysis.md      how the 3-4 references are studied and briefed
  engine-notes.md             render engine architecture and solved pitfalls
  qa-and-delivery.md          checks, splicing, encoding, packaging
scripts/
  beat_grid.py                tempo, downbeats, strong onsets, drop
  find_cover.py               official cover search + screenshot match + provenance
  av_sync.py                  music-video vs song offset (lip sync)
  shot_cuts.py                camera cuts inside footage
  motion_qa.py                frame jumps, stop-motion steps, freezes, dark frames
assets/reference_project/     complete worked example (render.py, audio.py, style.json)
```

## Install
- **Claude Code:** clone into your skills folder:
  ```bash
  git clone https://github.com/Hakam02-doom/music-promo-video ~/.claude/skills/music-promo-video
  ```
- **Claude app:** download `music-promo-video.skill` from the [latest release](https://github.com/Hakam02-doom/music-promo-video/releases/latest) and add it in Claude's Skills settings, or share the file in a chat and click **Save skill**.

Then ask, for example: *"Make a 30-second Spotify-style promo with these screenshots and this song, the hook is 0:45–1:05."*

## Requirements
- `ffmpeg`
- Python 3 with `numpy`, `pillow`, `opencv-python-headless` and `scipy`
- Optional: `faster-whisper`, for transcription

## Notes
- No media is included. The worked example's songs, cover art and video frames are copyrighted and aren't part of this repo; the code shows the expected file layout.
- Videos made with it may contain copyrighted music, artwork and footage. That's fine for personal edits, but platforms may mute or claim public posts. The sound-effects-only export lets you add the song from the platform's own music library.
- Use brand logos and assets only for your own brand, for clients who have given permission, or in clearly labelled fan or concept work.
