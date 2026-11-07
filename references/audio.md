# Audio: songs, handoffs, SFX, loudness

The user cared most about how the songs feel: "low to high", "seamless", "not so loud at the transition", "high to low at the end". Everything here serves those words.

## Songs under the picture
- Each song plays **in sync with the picture**: film time = song time + offset. That lets cuts land on real downbeats and lets a recreated player show the true song position.
- Get the beat grid with `scripts/beat_grid.py song.mp3 --start A --end B`. Use downbeats for scene changes and beats or eighths for pops. When a strong half-time feel confuses the tempo (64.5 vs 129 BPM), trust the spacing of the strongest onsets. The bar is the gap between recurring big hits.
- The user gives the hook times; use them.

## Envelope shapes the user approved
- **First song: low → very high.** About −22 dB under the opening scenes, then an accelerating climb (`k**2.2` in dB) through the bar before the drop to about −3 dB, with a soft limiter. Measured: about −35 dB RMS early, about −12 dB after the drop. "Decrease the decibels more when it's not peaking."
- **Ending: high → low.** From the last big visual move (e.g. particles lifting) to the end, fade about −34 dB along a cosine curve while a low-pass closes (18 kHz → 900 Hz), with the last 0.2 s silent. Measured: −15, −21, −30, −41, −46 dB per second.
- Don't push the mix to −6 LUFS: songs that already peak above full scale distort under a limiter. About −11 to −14 LUFS integrated with a true peak around −1 dBFS sounded loud and clean.

## Seamless handoff between two songs (approved version)
Treat the handoff as a smooth breakdown and rebuild, never a loud effect. A playful DJ stutter roll was tried and rejected: it was "so loud" and "not seamless".

1. **Beat-align:** put a downbeat of song B exactly on a downbeat of song A (the SWAP time). Pick B's downbeat at or just after the user's hook start.
2. **Song A over its last bar:** low-pass sweep 16 kHz → 500 Hz while the level falls about 26 dB (cosine), then out by SWAP + 0.85 s. Add a soft ping-pong echo of A's last half-beat (lowpassed, halving each repeat, on B's beat) to carry the tail.
3. **Song B:** enters one bar before SWAP at −40 dB, rising to −22 dB at SWAP, high-passed (1 kHz → 20 Hz over its first bar after SWAP so the bass returns gradually). Then it climbs from low to high (−22 → −4 dB, `k**1.6`) through its build and reaches full at its own drop. Hand the gain back to the normal level (−6 dB) inside its pre-drop pause, where nobody hears the move.
4. **Quiet glue:** the riser at about −16 dB, one small accent half a bar after SWAP at about −18 dB. Measured shape: −12 → −34 dB at the handoff → −29, −24, −22 dB → −13 dB after B's drop.
5. Avoid any one-frame visual event at SWAP. Tie the visual to the same breakdown (e.g. fly into black while A fades).

Block-wise time-varying Butterworth filters (`sweep()` in the reference `audio.py`, 512-sample blocks, state carried) are enough for these sweeps.

## SFX placement
- Characterise each file first: length, peak time, spectral centroid. Typical roles: click (taps), bright whooshes (zoom-ins, slides), dark rumble (long pushes), riser (peaks on a drop), pop (things landing), chime (logo, liked heart). Skip very long or irrelevant files.
- Cue by the **peak**: start = event time − peak offset (divided by pitch factor if resampled).
- Each tap gets a click on the press frame. A liked heart gets click + chime.
- For a stream of identical events (hundreds of diamonds), play a special sound on each of the first few (e.g. 8), then on every 6th with random pitch (0.85–1.35×) and pan, quieter. One per event becomes noise.
- Keep SFX lower in quiet song passages: in a low section, −10 dB tings read clearly; −3 dB is too loud.
- A soft-limited sum, normalised to −1 dBFS peak. Write two mixes with the **same** normalisation: songs + SFX, and SFX only (for posting with platform-licensed music).

## Checks you can actually do
You cannot listen. Measure instead:
- RMS per second across the whole mix, and per quarter-second around each handoff;
- integrated LUFS and true peak (`ffmpeg -af ebur128=peak=true`);
- crest factor of the loud section (around 10 dB is healthy; much lower means over-limiting);
- the share of samples near full scale.

Tell the user what you measured and ask them to listen to the handoffs.
