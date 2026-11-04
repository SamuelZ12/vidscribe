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

The run printed `WARNING: last cue 2021s < duration 2371s`: the model stopped ~6 min early, so the last 15% of the talk produced no ref frames. (I first estimated ~21 refs for a full transcript; the full transcript in the clip test below still gives 18.)

## Frame cap: 40

Frames cost almost nothing to produce (~60 ms each), so the cap is about the agent that reads them, not runtime. Each frame is 1280x720, roughly 1.2k image tokens for Claude (w*h/750), and the agent is told to look at every ref frame.

- Ref frames scale with speech length: here ~0.53 per transcribed minute. Even frames are fixed at N.
- At that rate, a 2 h talk would give ~64 refs + 8 even = ~72 frames, ~90k image tokens. A chattier demo would give more.
- A cap of 40 is 1.6x what this 40 min talk produces on a full transcript (25). Talks up to ~60 min stay unchanged, and longer videos are bounded at ~50k image tokens.

Rule: always keep the N even frames. If even + ref exceeds 40, keep `40 - even` ref frames spread evenly across the list of refs. `-v N` with N > 40 is honored (even frames only, no refs). The clip test below checks this.

## Clip test: frames vs transcript only, cap vs no cap (ROADMAP testing)

2026-11-04, branch `video-default` (fbddc2b), 12 YouTube clips, default flags.

Method:
- One agent per clip wrote 4 questions with reference answers from the full transcript plus dense timestamped frames (every 5-62 s, ≤108 per clip): 2 visual-only, 1 mixed, 1 speech-only.
- Separate agents answered from their own folder only. A: transcript only. B: transcript + vidscribe's `index.txt` and frames. C: same as B with the cap removed (only clips where the cap triggered).
- Answers were graded blind (question, reference, one candidate) as correct = 1, partial = 0.5, wrong or "unknown" = 0.
- The model truncates long audio (below), so the 3 long clips used full transcripts made from 30-min chunks in every condition, with frames produced by vidscribe's own frame code on those transcripts.

| Clip | Kind | Length | Run | Frames (ref+even) | A | B | C |
|---|---|---|---|---|---|---|---|
| wpGI6BmhbJU | Figma demo | 8.6 m | 52 s | 2+8 | 1 | 1 | |
| Gjnup-PuquQ | Fireship screencast | 2.1 m | 20 s | 5+7 | 1 | 3 | |
| C-39pLx6QTQ | Python coding tutorial | 13.1 m | 196 s | 0+8 | 2 | 2 | |
| up1xuwn_euk | talking head | 7.7 m | 63 s | 4+8 | 1 | 2 | |
| D1PjB0cwiKg | Mandarin, slides/screen | 6.0 m | 42 s | 10+6 | 1 | 3.5 | |
| ive5H8hCBFs | Mandarin vlog | 7.3 m | 33 s | 6+8 | 1 | 3 | |
| Z50jEi1igNQ | short science clip | 1.6 m | 15 s | 2+6 | 1 | 3 | |
| UMp-IF6uPkk | cooking | 10.1 m | 61 s | 5+8 | 1 | 3 | |
| Yv2iYYewdf0 | charts | 5.3 m | 32 s | 0+8 | 1 | 3 | |
| Unzc731iCUY | MIT lecture | 63.7 m | 259 s | 32+8 (36 uncapped) | 1 | 3 | 3 |
| wYSncx9zLIU | Google I/O keynote | 111.3 m | 288 s | 32+8 (57 uncapped) | 1 | 1 | 0 |
| LCEmiRjPEtQ | Karpathy talk | 39.5 m | 227 s | 18+7 (cap not hit) | 1 | 1 | |
| **Total /48** | | | | | **13** | **28.5** | |

Run time and the long clips' frame counts are from the real vidscribe runs, with truncated transcripts. The long clips' A/B/C scores used the full transcripts.

By question kind (A → B): visual 1/24 → 11.5/24, mixed 0/12 → 5/12, speech 12/12 → 12/12. B never scored lower than A on any question, and every B miss was "unknown", never a wrong answer. The misses were moments no frame captured (a slide caption, a jug, a hedge): this is the gap that ROADMAP step 4 (scene-change frames) targets.

Cap: no evidence that more frames help. On the MIT lecture B = C (3/4). On the I/O keynote C did worse (0 vs 1): with 65 frames it answered even the speech question "unknown". With the full transcript, ref frames run 0.46-0.57 per minute (Karpathy 18, MIT 36, I/O 57), so with 8 even frames the cap starts trimming at about 60-65 min. 4 questions per clip can only detect large effects; keep 40.

Agents skip frames when there are many: before being told explicitly to view every frame, 3 of 15 frame-condition agents looked at only part of their set (8/16, 8/13, and 2/65 frames). Sending more frames doesn't mean more get looked at.

Truncation: the model stopped at 2862 s (MIT, 64 min) and 2876 s (I/O, 111 min) and 2021 s (Karpathy). Both hour-plus clips stop around 48 min, so long videos lose their tail by default. Transcribing in 30-min chunks and merging fixed all three (last cue = duration).
