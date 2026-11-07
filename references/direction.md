# Direction: what makes these videos land

These rules come from a long edit in which the user corrected each version. Each rule carries its reason, so you can apply its spirit to new situations. The user's explicit words and their references override these defaults.

## Contents
1. Overall feel
2. Opening and ending
3. Transitions: everything merges
4. Typography and text placement
5. Images and covers
6. App interface and taps
7. Motion and frame rate
8. Texture
9. Particle assemblies
10. Music-video footage
11. Process lessons

---

## 1. Overall feel
- **Dark stage by default** (near-black, about #0A0A0B, with a faint radial lift in the centre). An early "archival paper collage" version was rejected: the user wanted "the whole dark", like the app itself. Use paper, cream or collage textures only when the references clearly call for them.
- One focal point per moment: a logo, a cover, a word or a player.
- Brand colour (e.g. Spotify green #1ED760) is an accent: glow behind the logo, the liked heart, underlines, the active chip. It isn't a background wash.
- Don't invent content. Titles, artists, years and interface states must match the screenshots or verified sources.

## 2. Opening and ending
- **Open on the logo.** The logo appears (scale 0.82 → 1 with a fade and a soft green glow) and words reveal around it. Then a tap on the logo and a zoom into it carries us into the app.
- **End on an end card that mirrors the opening**: same logo position and size, so the last frame flows into the first and the video loops.
- The approved end card: the logo plus a **white repeat ring** (a 300° arc that draws on clockwise from the top, with an arrowhead, then keeps turning slowly), with **LISTEN** fully visible below it, rising letter by letter through a mask line, and *on repeat* in serif italic underneath. Then a fade to black.
- **Rejected:** LISTEN placed behind the logo with letters hidden ("hidden between the logo"). Logos must never cover words.

## 3. Transitions: everything merges
The user's most repeated requests were "every frame should merge into the next one", "smooth zoom in and zoom out", and "one item merges with the next one". Hard cuts between scenes were not acceptable. Proven mechanisms:

| Mechanism | How |
|---|---|
| Zoom into a solid area | Tap the logo, then zoom 24× into a solid-green point (not an arc or other detail). Ease in and out, glide that point to frame centre, fill the frame completely, then dissolve the colour to dark while the next page zooms out from 1.35× to 1×. |
| Tap → matched zoom | Tap a tile; the camera carries that exact tile to the next scene's hero rectangle (same position and size), so the cut is invisible. |
| Carousel | Pull back (1 → 0.56), slide one item per beat, push back in on the target cover, which becomes the next scene's hero. |
| Push into a UI element | Zoom into the now-playing bar; it becomes its own layer with exactly the same pixels while the rest of the page dissolves. |
| Zoom-out reveal | The hero cover stays put while the camera pulls back to reveal a wall of covers popping in ring by ring on eighth notes. |
| Fly-through | Pick the darkest roomy area of a cover in the wall (distance transform on a dark mask), fly into it at about 13× until black fills the frame, then start the next section from black. |
| Dive through a hole | A cover with a hole (the OK-sign glove) lets the camera dive through at about 32× into black, then the music video fades up out of that black. |
| Particles | The cover's diamonds lift off and spiral into the logo shape; the clean logo then crossfades in. |

Rules:
- **Ease both ends** of every zoom (cubic in-out); interpolate zoom exponentially. A zoom that keeps accelerating to the end (ease-in only) "slams" and flashes details across the frame.
- Move the focus point's **screen position** linearly towards centre while zooming. Interpolating the world focus instead makes the target swing outward first.
- **Fade anything that disappears**, even when it's dark: a dark tile vanishing in one frame shows as a background pop (measured at 2/255, still flagged).
- Check both sides of each transition on consecutive frames.

## 4. Typography and text placement
- **Three type roles only:** sans bold (Helvetica Neue Bold) for main words; editorial serif italic (Didot Italic) for accent words; mono (Menlo) for credits and labels. Use the pairing *"your* **LIBRARY**", **"EVERY** *album*,". Big word large, explanation quieter, credit small in mono.
- **Never place words on top of artwork or posters.** The user flagged *rich* sitting across the Enigma cover as a clear mistake.
- **Never leave words hidden behind objects.** Text behind an object is allowed only as a *reveal*: the word slides out from behind the poster's top or bottom edge, or rises through a horizontal mask line, and then sits fully visible. Exits reverse the entry (slide back behind, drop back through the line).
- **Titles above scrolling content belong to that content.** A screen-fixed title above a grid that scrolls up got covered by the tiles ("your library text is hiding behind the images"). Draw it in the page's world coordinates, with clear space above the first row.
- Kinetic words land on beats (one word per beat at the drop). Give them a hold long enough to read, about 1–2 beats minimum; words that exit as they arrive (*treasures*) were missed. Add a green underline drawn on for emphasis.
- Spotify-like filter chips (Playlists, Albums) are a good playful element under a library title; light up the next scene's chip on a downbeat to foreshadow it.
- Stop-motion (stepped) entries: use them sparingly, at 15 updates/s, which must divide the output fps exactly (60 and 120 both work). The user's priority was smoothness.

## 5. Images and covers
- Use **official high-resolution art** (`scripts/find_cover.py`). Screenshot crops of 100–300 px looked blurry and the user rejected them.
- Verify every cover against the user's screenshot (match ≥ 0.98) and keep provenance. The track's album art may differ from what you'd guess. The now-playing thumbnail is the ground truth.
- For small sources (e.g. a 500 px JioSaavn image), upscale once with Lanczos plus a gentle unsharp mask, and avoid long holds at more than 2× the source size.
- Rounded corners about 2.2% of the size, like the app; soft dark shadows; grain at half strength on covers and UI so they stay crisp.
- Make things big: the user asked for larger images twice. A hero cover about 820 px wide on 1080 works well; library tiles about 440.

## 6. App interface and taps
- Recreate the player as clean vector UI rather than an upscaled screenshot:
  - cover, title (sans), artist (mono, dim);
  - heart outline that becomes green filled with a little bounce when tapped;
  - progress bar driven by the **real song position** (film t − offset) with the real duration;
  - previous / pause / next controls.
- **Taps:** a soft white press disc plus an expanding thin ring, the target scales down about 4.5% and back, and a click SFX lands on the same frame.
- Only show interface text that exists (song title, artists, section names like "Jump back in").

## 7. Motion and frame rate
- 60 fps by default; the user later asked for 120. Social platforms play at 60 fps at most, so keep the 60 fps export for posting and say so.
- Keep camera moves in a scene subtle (2–6% push or drift). Save big moves for transitions.
- Pops that land on beats can use a stepped clock, but keep every camera move smooth.

## 8. Texture
- Fine monochrome grain, freshly seeded every frame (seed = frame index), weighted towards midtones, lighter on covers and UI.
- Subtle bloom on highlights (threshold about 0.7, amount about 0.14).
- No paper, dust, scratches or vignettes on the dark style.

## 9. Particle assemblies (the "diamonds align in the glove" effect)
Requested: "all the diamonds come one by one and align in the glove".
- Find the pieces: local brightness maxima inside the object mask, thinned to a minimum spacing (about 10 px at 1500 px), capped at about 650.
- Show a **faint ghost** of the object (about 11% alpha) from the start. Without it, the first diamonds land in empty black and don't read as "aligning".
- The first 8 pieces come one by one on the beat (big, with a glint and a diamond-ting SFX each). Then the rest pour in, accelerating, ordered from base to tip.
- Reveal the underlying image through an accumulated, blurred splat map of landed pieces. Then fill the object, then the whole cover.
- On the next song's drop: every diamond glints, the cover punches 3.5%, and the title words slide out from behind its edges.
- The finale reverses it: pieces lift off (top first) and spiral as a vortex into Poisson-disc targets inside the logo, coloured by the logo, and the clean logo crossfades in.

## 10. Music-video footage
- Sync the video to the song by audio cross-correlation (`scripts/av_sync.py`), so lips match what's heard.
- Full-bleed vertical crop of 16:9 footage: crop centre per shot following the subject (`scripts/shot_cuts.py`). The crop may jump only at the footage's own cuts.
- Frame-blend 24 → 60/120 fps, but never blend across a cut.
- Good flow: dive into black → video fades up full-bleed with a slow zoom-out → on a downbeat it reframes into a 16:9 top panel while the cover rises into the bottom half → the panel slides away and the cover recentres → finale.
- It's fine to extend the song past the stated hook to cover the footage, but say so.

## 11. Process lessons
- **Don't remove parts of the previous version** when adding a section. The user worried the earlier video had been replaced. Insert new sections, keep the rest frame-identical, and state exactly what changed.
- When asked to fix one thing, change only that and prove the rest is identical (frame diffs at sample times = 0).
- Send a watchable version as soon as one is complete; users interrupt to ask for it.
- Messages often arrive cut off mid-sentence. Act on the clear part and ask for the rest.
