# Measurements

## Frame counts on a long talk (ROADMAP step 1)

2026-11-04, Apple Silicon Mac, `master` (bb029cd), default model `mlx-community/Qwen3-ASR-1.7B-8bit`.

Command: `./bin/vidscribe https://www.youtube.com/watch?v=LCEmiRjPEtQ -v`
Video: "Andrej Karpathy: Software Is Changing (Again)", 39:31 (2371 s), slide-heavy keynote, downloaded at 1280x720 (107 MB).

| Metric | Value |
|---|---|
| Even frames | 7 (8 requested; one dropped for a ref frame within 3 s) |
| Ref frames (spoken on-screen references) | 18 |
| Total frames | 25 |
| Frame JPEGs on disk | 1.9 MB (~76 KB each) |
| Frames dir incl. kept video | 104 MB |
| SRT cues | 68 (~30 s each) |
| Wall time, whole run | 4m00s |

Phase split (timed separately on the same video, outside vidscribe; frame extraction used 27 test timestamps):

| Phase | Time |
|---|---|
| yt-dlp download (720p) | 10 s |
| ffmpeg to 16 kHz wav | 3 s |
| Frame extraction | ~60 ms per frame (27 frames in 1.6 s) |
| Transcription (remainder) | ~3m45s |

The run printed `WARNING: last cue 2021s < duration 2371s`: the model stopped ~6 min early, so the last 15% of the talk produced no ref frames. Extrapolating, the full talk would have ~21 refs, ~28 frames total.

## Frame cap: 40

Frames cost almost nothing to produce (~60 ms each), so the cap is about the agent that reads them, not runtime. Each frame is 1280x720, roughly 1.2k image tokens for Claude (w*h/750), and the agent is told to look at every ref frame.

- Ref frames scale with speech length: here ~0.53 per transcribed minute. Even frames are fixed at N.
- At that rate, a 2 h talk would give ~64 refs + 8 even = ~72 frames, ~90k image tokens. A chattier demo would give more.
- A cap of 40 is ~1.4x what this 40 min talk would produce on a full transcript (~28). Talks up to ~40-60 min stay unchanged, and longer videos are bounded at ~50k image tokens.

Rule: always keep the N even frames. If even + ref exceeds 40, keep `40 - even` ref frames spread evenly across the list of refs. `-v N` with N > 40 is honored (even frames only, no refs). The 40 rests on one video; ROADMAP's 10-15 clip test should revisit it.
