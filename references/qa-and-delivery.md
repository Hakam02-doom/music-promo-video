# QA and delivery

## Checks on the exported MP4
```bash
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,nb_frames,duration -of compact final.mp4
ffmpeg -v error -i final.mp4 -f null - && echo decode-ok
ffmpeg -i final.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -A12 Summary | grep -E " I:|Peak:"
python scripts/motion_qa.py final.mp4 --fps 60
```
`motion_qa.py` lists spikes (frame jumps far above their neighbours), near-identical runs (freezes) and very dark frames.

Classify every spike:
- **Expected:** stepped entries (regular spacing at fps/15 frames), the music video's own cuts, an intended fast zoom.
- **Suspicious:** a lone spike at a scene change, at a song handoff, or at a splice point. Extract its neighbourhood and look:
  ```bash
  ffmpeg -i final.mp4 -vf "select='between(n,N-6,N+6)',scale=180:320,tile=13x1" -frames:v 1 around_N.jpg
  ```
- Dark-frame runs are fine at intended dives into black; elsewhere they're defects.

Also look at a contact sheet of the whole video (one frame every 0.25–0.5 s) before sending.

## Small fixes: partial re-render and splice
1. Make the code change; render only the affected range from the master settings: `python render.py --range 4.6,10.2 --out out/fix.mp4`.
2. Splice with frame-exact trims from the high-quality masters (CRF 15 renders), not from delivered encodes:
   ```bash
   ffmpeg -i master.mp4 -i fix.mp4 -i mix_full.wav -filter_complex \
    "[0:v]split=2[p0][p1];[p0]trim=start_frame=0:end_frame=552,setpts=PTS-STARTPTS[a];\
     [1:v]setpts=PTS-STARTPTS[b];[p1]trim=start_frame=1224,setpts=PTS-STARTPTS[c];\
     [a][b][c]concat=n=3:v=1:a=0,fps=120[v]" -map "[v]" -map 2:a \
    -c:v libx264 -preset slow -crf 21 -tune grain -pix_fmt yuv420p \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
    -c:a aac -b:a 256k -movflags +faststart final.mp4
   ```
3. Confirm the new range starts after the old code's last effect and ends before the next one, or include them.
4. Prove the rest is unchanged: compare frames at sample times with the previous delivery (mean difference should be 0.00).

## Encoding
- Master renders: x264 CRF 15. Deliveries: CRF 20 at 60 fps, CRF 21 at 120 fps, `-tune grain`, yuv420p, bt709 tags, AAC 256 kbps, `+faststart`.
- 120 fps: render a separate master with `fps` 120 in `style.json` (don't interpolate). Mention that Instagram and TikTok play at 60 fps at most.

## Package
- `deliver/`: `name_vN_60fps.mp4`, `name_vN_60fps_sfx_only.mp4`, (`_120fps` variants on request), `name_vN_project.zip`.
- The project zip holds: README (timeline table, sound notes, covers with sources), `render.py`, `audio.py`, `style.json`, the logo, covers plus provenance.json, the footage frames used, the songs and SFX used, `out/mix_full.wav`, and `out/mix_sfx_only.wav`.
- Archive each previous version before changing code (`archive_vN/`).

## The message to the user
Say what changed (in their words), what you checked (duration, fps, decode, loudness, motion, seams) and what you couldn't check (listening). Remind them about rights once: songs, cover art and music-video clips are copyrighted, and platforms may mute or claim public posts. The SFX-only version lets them add the song from the platform's library.
