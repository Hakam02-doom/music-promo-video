# Studying the user's references

The 3–4 references are the main input to the look. Study them properly; a single cover frame says nothing about motion.

## Getting at them
- Video files: make a contact sheet (one frame every 2–4 s) and dense sequences around interesting moments (every 2–3 frames for 2–3 s):
  ```bash
  ffmpeg -i ref.mp4 -vf "fps=1/2,scale=320:-2,tile=8x6:padding=2" -frames:v 1 ref_contact.jpg
  ffmpeg -ss 12.0 -t 2.4 -i ref.mp4 -vf "fps=10,scale=320:-2,tile=6x4:padding=2" -frames:v 1 ref_dense_12s.jpg
  ```
- Images: open each at full size.
- Links: try them, but social links usually show only a login wall or cover image. Ask for the file or screenshots, and never claim to have watched what you couldn't open.
- Measure: cuts per bar (frame-difference spikes), typical hold length for words, zoom speed, palette (k-means on downsampled frames), texture (grain or none, bloom, vignette).

## The reference brief (write it, show it in a few lines)
- **Palette:** background, accent and text colours.
- **Typography:** which roles appear (sans, serif italic, mono, handwritten?), case, size hierarchy, and how words enter and exit.
- **Pacing:** shots per bar, holds, where the energy peaks.
- **Transitions:** zoom-throughs, matched cuts, slides, splits, whip pans and so on.
- **Text and image interaction:** words around objects, slide-out reveals, captions over footage (and where).
- **Texture and optics:** grain, bloom, halation, paper or none.
- **Sound character:** quiet build to drop, constant energy, SFX density.
- For each choice, note which reference it came from. Where references disagree, say which one you followed and why.

## Mapping references onto the house rules
The references set the look; the rules in `direction.md` keep the result readable and smooth. Examples:
- A reference puts captions over footage: allowed on video footage with a shade behind them, but still never across cover art or posters.
- A reference uses hard cuts: use cuts on downbeats inside a section, but keep scene-to-scene changes continuous unless the user says otherwise.
- A reference is bright or paper-textured: follow it. The dark stage is only the default.
