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

Truncation: the model stopped at 2862 s (MIT, 64 min) and 2876 s (I/O, 111 min) and 2021 s (Karpathy). Transcribing in 30-min chunks and merging fixed all three (last cue = duration). Cause and fix in the next section.

## Long audio: token budget, not audio length

2026-11-04. mlx-audio decodes ~30 s pieces but spends one `--max-tokens` budget (default 8192) across the whole file, then stops. When transcription stops depends on how many tokens the speech needs:

| Speech | tok/s | Budget runs out at |
|---|---|---|
| English lecture (MIT) | ~2.5 | ~55 min |
| English talk (Karpathy) | ~3.5 | ~39 min |
| Hindi, Devanagari (C-39pLx6QTQ) | ~10 | ~13.5 min |

Raising the budget alone (`--max-tokens 32768`, MIT) transcribed to the end, matching the chunked transcript in every 5-min window, but took 1744 s. The 17 s of closing applause looped as "oh, oh, ..." for 22k tokens until the budget ran out. Such loops are common: 4 of the 8 videos with SRTs on this machine had one, and in one a 30 s "hey, hey" piece used 8148 tokens, the whole budget.

- `repetition_penalty=1.1` (mlx-audio's built-in) stopped the loop (MIT 298 s) but changed real words: 0-1% on English and Mandarin clips, with errors like "stock or" → "stockor" and "google" → "g o o g l e", and 15.8% on the Hindi clip. Rejected.
- Per-piece cap (shipped): each piece may use at most `32 + 25 tok/s × piece length`. Real speech peaks at 15.9 tok/s per piece (Hindi; 816 cues measured). The file budget becomes `8192 + 32 × seconds`, so it never binds first.

Result: 9 short clips byte-identical to uncapped output; MIT 319 s, full coverage, every cue identical to the uncapped run except the loop, which is 222 words instead of 3840.

## Scene-change frames (ROADMAP step 4)

2026-11-04. Cut detection: ffmpeg at 2 fps and 160 px, `scene > 0.3`; ~0.75 s per minute of video (84 s for 111 min), ~15% on top of transcription. Cuts per minute ranged from 0.2 (animated charts: gradual changes don't register) to 8.5 (Mandarin slides); every clip over ~10 min has more cuts than the cap.

One frame per scene, at its last sampled frame, so slide builds and typed text are complete. Scenes under 1 s, flat frames, scenes within 3 s of a ref frame, and repeats of an earlier scene (dHash on a 9x8 thumbnail, ≤ 6 of 64 bits) are dropped. Dedupe removes less on long talks than hoped (MIT 262 → 218, I/O 817 → 599): wide and close-up stage shots don't count as repeats.

Two ways to share the 40-frame cap, compared on the 12 clips with a free check (is there a frame in the same scene as the question's moment?):

| Frame set | Visual | Mixed | Speech | All (48) |
|---|---|---|---|---|
| master (even + ref) | 12/24 | 6/12 | 10/12 | 28 |
| split: keep all even frames, refs and scenes share the rest | 17/24 | 7/12 | 10/12 | 34 |
| replace: scenes and refs first, even frames only fill empty slots | 18/24 | 7/12 | 9/12 | 34 |

A tie, so split shipped: it keeps even spacing for videos without hard cuts and leaves `-v N` unchanged.

Agent test, same method as the clip test above (every agent viewed every frame; checked from transcripts). Holdout: 4 new clips (screencast, coding tutorial, cooking, Mandarin explainer) whose questions a separate agent wrote after the frame code was fixed.

| Set | Transcript only | master | scene frames |
|---|---|---|---|
| 12 original clips | 13/48 | 28.5/48 | 33/48 |
| 4 holdout clips | 5/16 | 11.5/16 | 12.5/16 |

9 questions changed: 8 gained, 1 lost (sign test p ≈ 0.04). Of the 6 gains traced to the frame the agent cited, all 6 were scene frames, so the gain is not just from more frames (332 vs 206 on the 12 clips). The loss: MIT, where scenes took half of the slots refs used to have. No new wrong answers; misses stayed "unknown". The three long talks gained nothing (1, 1, 2 of 4): 16 of hundreds of scenes fit the cap, and a third of the Karpathy picks were stage shots. Better scene choice on long videos is the open problem.

## Scene choice on long videos (ROADMAP 5, not shipped)

2026-11-04. On long videos only ~16 of 100-650 scenes fit the cap, and master thins them evenly over the scene list. Two ways to pick better were tried; neither improved answers, so master's selection stays.

Probe (16 scene slots, frames counted by hand, not blind): picked frames that mainly show content (slide, screen, graphic) rather than speaker, stage or audience.

| Clip | master | A: skip recurring shots | B: content score |
|---|---|---|---|
| Karpathy keynote | 5 | 13 | 12 |
| MIT lecture (Unzc731iCUY) | 3 | 1 | 5 |
| MIT 6.100L lecture (xAcTmDO6NTI) | 7 | 1-2 | 13 |
| Google I/O | 8 | 9 | 13 |
| PyCon UK keynote (gDvwRpl9erE) | 9 | 10 | 10 |
| Apple event (H3KnMyojEQU) | ~8 | ~7 | 16 |

- A: count how often a scene's look (9x8 dHash within 10 bits) recurs; prefer looks seen fewer than 3 (or 8) times, keep one frame of each recurring look. It works when one camera angle dominates (Karpathy's close-up). It backfires on lectures, where the same slide template or IDE recurs and handheld lecturer shots don't. On I/O every slide shown on the stage screen hashes like the stage; a 32x18 dHash didn't separate them either (two slides 88 bits apart, two close-ups of one speaker 73).
- B: score each scene by the share of 32x18 pixels at its most common brightness (plain backgrounds = slides, screens, cards), split the video into as many equal spans as slots, keep the best scene per span. Same ffmpeg pass; uncapped clips byte-identical.

Agent test of B, same method as above: 12 long videos where the cap binds, 6 questions each (4 visual, one per quarter; 1 mixed; 1 speech), written by separate agents from dense contact sheets. Both conditions used the same transcript; only the frame-selection code differed. Every answer agent viewed every frame; grading was blind. Dev = the 6 probe clips; holdout = 6 clips nobody had looked at under B.

| Clip | Kind | Length | master | B |
|---|---|---|---|---|
| LCEmiRjPEtQ | Karpathy keynote | 39 m | 3 | 2 |
| Unzc731iCUY | MIT lecture | 63 m | 4 | 4 |
| wYSncx9zLIU | Google I/O keynote | 111 m | 2 | 2 |
| H3KnMyojEQU | Apple event | 71 m | 2 | 2 |
| gDvwRpl9erE | PyCon UK keynote | 65 m | 3 | 3 |
| xAcTmDO6NTI | MIT 6.100L lecture | 63 m | 5 | 4 |
| ej5RsTtVvQE | PyCon Austria talk (holdout) | 48 m | 4 | 5 |
| JKbtWimlzAE | Stanford CS25 lecture (holdout) | 61 m | 2 | 3 |
| hF8swzNR1-o | WWDC 2026 keynote (holdout) | 76 m | 2.5 | 2.5 |
| yQ6VOOd73MA | NOVA documentary (holdout) | 53 m | 2 | 2 |
| x-wqMcYMNdg | Jon Stewart podcast (holdout) | 88 m | 5 | 4 |
| v9DuQ1C3xH8 | Food Network cooking (holdout) | 47 m | 3 | 3 |
| **Total /72** | | | **37.5** | **36.5** |

By kind (master → B): visual 19 → 19/48, mixed 6.5 → 6.5/12, speech 12 → 11/12 (the speech loss is agent noise: same transcript). 7 questions changed, 3 up and 4 down. Free check (a frame inside the span where the answer is on screen): 23 vs 23 of 60.

B does pick more content: a blind judge labeled the 209 scene frames of each condition as content / speaker or stage with a legible slide / speaker, stage or audience only / blank: 71 / 37 / 101 / 0 (master) and 122 / 21 / 57 / 9 (B; the blanks are near-black or logo-only cards, which a plain-background score favors). But with 16 slots across hundreds of scenes, whether a frame lands on the moment a question asks about is luck either way: on long videos, the number of frames limits pinpoint questions, not which scenes are chosen. Not shipped.

Found on the way: a video stream with side data made ffprobe's csv print `0,` instead of `0`, so `has_video` treated the WWDC 2026 keynote as audio-only and silently skipped frames. Fixed by reading one value per line.
