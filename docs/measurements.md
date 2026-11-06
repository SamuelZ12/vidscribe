# Measurements

The 12-video long-video eval (scene choice, frames on demand) is in `eval/`: questions, reference answers, grades, prompts and rebuild steps.

## Frame counts on a long talk

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

## Clip test: frames vs transcript only, cap vs no cap

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

By question kind (A → B): visual 1/24 → 11.5/24, mixed 0/12 → 5/12, speech 12/12 → 12/12. B never scored lower than A on any question, and every B miss was "unknown", never a wrong answer. The misses were moments no frame captured (a slide caption, a jug, a hedge): the gap scene-change frames (below) target.

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

2026-11-05. A piece that hit its cap was still cut off silently (the end token is never counted, so hitting the cap exactly means cut off). Now it is split at its quietest 100 ms in the middle half and each half is redone with its own cap. A loop shrinks to a piece under 8 s, which keeps its capped text and prints `warning: transcript cut off in HH:MM:SS-HH:MM:SS`. Under 8 s the cap allows over 29 tok/s, nearly twice the real-speech peak. A 30 s piece that loops throughout costs up to 11 decodes (~3.4k tokens instead of 782), and each leaf's 32-token base lets a split piece slightly exceed its share of the file budget; the 8192 slack covers that unless hours of audio loop. Checked with a 41 s `say` clip in throwaway copies of the script. A cap of 20 on every piece used to give 38 of 174 words with no warning; it now gives 113 words and six warnings. A cap of 20 only on pieces over 20 s recovers all 174 words (6 commas differ) with no warning. txt, srt and frame-mode outputs are byte-identical to master.

MIT lecture (Unzc731iCUY, 63.7 min, `-a -f srt`): 344 s, one warning (`01:03:25-01:03:29`, the closing applause), last cue at 01:03:42 (the end). The loop is now ~105 words, down from 222 with the per-piece cap alone.

## Language default: forced en vs auto-detect

2026-11-05. Without `-l`, mlx-audio's `--language` default prompted every piece with `language en`. Each clip was transcribed over 90 s from its middle (16 kHz mono) four ways: forced `en` (old default), mlx-audio's auto-detect (`language=None`, which locks later pieces to the first piece's language), auto-detect per piece (shipped), and the full name (`Chinese`/`Hindi`). CER is per character against the uploader's human subtitles, after converting to simplified characters and removing punctuation and spaces.

| Clip | Kind | forced `en` | auto, locked | per piece | full name |
|---|---|---|---|---|---|
| ive5H8hCBFs | Mandarin vlog, CER | 0.197 | 0.197 | 0.197 | 0.197 |
| bjO2ijV5izQ | Mandarin + English terms, CER | 0.074 | 0.074 | 0.074 | 0.074 |
| Pe6xbLd94z0 (276-366 s) | Mandarin vlog, CER | 0.173 | 0.173 | 0.168 | 0.173 |
| Pe6xbLd94z0 (138-228 s) | background music with vocals | 4704 chars of "oh, oh", 176 s | empty | empty | 11 chars |
| speech 30 s + that music 60 s, English | | 6 warnings, 66 s | 2 warnings, 47 s | clean, 7 s | |
| speech 30 s + that music 60 s, Mandarin | | 6 warnings, 65 s | 2 stray words | clean, 6 s | |

The 0.197 is mostly digits ("1.19" vs "一点一九"). D1PjB0cwiKg, SXqUyVzHgeE (no subtitles) and English 30 s followed by Mandarin 60 s read the same in every mode except spacing around English words and digits. English (up1xuwn_euk, 360 words): 2 quote marks differ. Hindi (C-39pLx6QTQ, ZwJ1zktkSfk): auto-detect and `Hindi` write English terms in Devanagari without punctuation, once wrongly (`VideoWriter` → `वीडियो राइट करता`); forced `en` and `English` keep them in Latin script. `-l zh` gave the same text as `-l Chinese`; `-l hi` was a mix of the `en` and `Hindi` outputs. The last 80 s of the MIT lecture alone didn't loop in either mode, so the applause there is inconclusive. Decision: [ADR-0006](decisions/0006-detect-language-per-piece.md).

## Scene-change frames

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

## Scene choice on long videos (not shipped)

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

## Frames on demand

2026-11-04. `vidscribe <frames-dir> --at TIMES` extracts frames from the run's `video.<ext>` at chosen times (a range gives 4); SKILL.md tells agents to find the moment in the transcript and fetch it. Same 12 long videos, 72 questions, transcripts and master frame folders as the scene-choice test; the only change is that answer agents may run `--at` (prompt otherwise identical, including "view every frame"). Grading: same blind grader prompt; master scores are the existing grades. Dev clips ran first; SKILL.md wording was then frozen for the holdout clips.

| Clip | master | C: + `--at` | extra frames |
|---|---|---|---|
| LCEmiRjPEtQ | 3 | 6 | 13 |
| Unzc731iCUY | 4 | 5 | 23 |
| wYSncx9zLIU | 2 | 6 | 16 |
| H3KnMyojEQU | 2 | 6 | 22 |
| gDvwRpl9erE | 3 | 6 | 16 |
| xAcTmDO6NTI | 5 | 6 | 4 |
| ej5RsTtVvQE (holdout) | 4 | 6 | 12 |
| JKbtWimlzAE (holdout) | 2 | 6 | 20 |
| hF8swzNR1-o (holdout) | 2.5 | 6 | 20 |
| yQ6VOOd73MA (holdout) | 2 | 5 | 21 |
| x-wqMcYMNdg (holdout) | 5 | 5 | 14 |
| v9DuQ1C3xH8 (holdout) | 3 | 6 | 12 |
| **Total /72** | **37.5** | **69** | 16 per clip |

By kind (master → C): visual 19 → 46/48 (holdout 10 → 22/24), mixed 6.5 → 11/12, speech 12 → 12/12. 33 questions went up, 1 down. Well past the agreed ship bar (≥ +6/48 visual, holdout visual not lower, speech within ±1).

- Cost: 1-3 `--at` calls and 4-23 extra frames per video (about 19k tokens at ~1.2k per frame); extraction takes ~0.05 s per frame. Agents asked for single times or 10-50 s ranges around the cue the question pointed at.
- The 3 misses are all precision, not missing coverage: a card on screen for 0.75 s (the agent read the next card), a 4 s phone screen in a collage (a neighbouring outlet; master got this one right), and a slide whose bullets appeared 6 s after the agent's last frame (it guessed instead of fetching a wider range). All three are confident wrong answers.
- One agent passed a range past the end; the call fails as a whole with a clear message, and it retried.
- Caveat: the questions anchor on speech ("when the speaker says ..."), which is the case `--at` is built for. Moments the transcript never hints at still depend on the automatic 40 frames. Tested in "Hard eval" below.

## Hard eval: moments the transcript never names

2026-11-05. Same 12 videos (re-downloaded, transcribed with master `b3fa881`), 36 new questions, 3 per video, one per third. Each names its moment only by what is on screen; the anchor is not spoken within 60 s and the answer is never spoken. All 36 also defeated a transcript-only agent that had to guess (score 0/36). Method, prompts and validation in `eval/README.md`, "Hard set"; grades in `eval/hard/grades.json`. Two conditions, fresh agents, blind grader: `frames` (the run's 39-40 frames) and `at` (the same plus `--at`). Dev clips ran first, then holdout; nothing changed between.

| Clip | frames | at | extra frames |
|---|---|---|---|
| LCEmiRjPEtQ | 0 | 3 | 12 |
| Unzc731iCUY | 1 | 3 | 12 |
| wYSncx9zLIU | 0 | 0 | 40 |
| H3KnMyojEQU | 0 | 3 | 20 |
| gDvwRpl9erE | 1 | 3 | 16 |
| xAcTmDO6NTI | 1 | 3 | 12 |
| ej5RsTtVvQE (holdout) | 2 | 3 | 4 |
| JKbtWimlzAE (holdout) | 1 | 3 | 16 |
| hF8swzNR1-o (holdout) | 1 | 3 | 67 |
| yQ6VOOd73MA (holdout) | 0 | 1 | 52 |
| x-wqMcYMNdg (holdout) | 3 | 3 | 0 |
| v9DuQ1C3xH8 (holdout) | 1 | 3 | 12 |
| **Total /36** | **11** | **31** | 22 per clip |

Dev 3 → 15/18, holdout 8 → 16/18. No leakage (each agent's tool calls stayed in its folder; no `ffmpeg`).

- **Decision (rule set before the run): OCR timeline not built.** `at` scored 31/36 (86%), above the 75% bar. All 5 misses are "not found" (no viewed frame inside the anchor span), so the misses are the kind OCR would target, but there are too few to justify it.
- Agents find unnamed moments from related speech, not the anchor itself: presenter hand-overs ("Here's Raja") for name captions, the topic being discussed (Photoshop mentioned before a slide comparing it with Unreal; "LLMs click stuff" before an Operator screenshot; a Logan Airport story before a terminal map). The new questions keep anchors unspoken, but on talks and keynotes the content shown is usually what is being discussed.
- The misses are where that link is missing: a 111-minute Google I/O keynote with three brief shots (a montage clip, a demo slide, a 5 s photo) the speech never describes (`wYSncx9zLIU`, 40 extra frames, 0/3), and two NOVA documentary shots (stock footage of a watch movement; an interviewee whose caption appears once) that the agent searched for with 52 extra frames.
- Searching costs more than in the speech-anchored eval: 0-67 extra frames per video, 263 total (about 26k tokens per video at ~1.2k per frame, against ~19k there). The largest were long searches: `hF8swzNR1-o` 67 (3/3), `yQ6VOOd73MA` 52 (1/3), `wYSncx9zLIU` 40 (0/3).
- Every miss in both conditions was an honest "unknown"; no confident wrong answers. Four low-confidence answers were graded right: a small painting (`at`), and in `frames` a small shirt print, a blurry book spine and a half-hidden Siri prompt the agent completed.
- `frames` alone got 11/36, mostly where the answer stays on screen (a podcast's background shelves, 3/3) or lands on a default frame by chance.
- Caveat: 36 questions, 5 misses, and one video (`wYSncx9zLIU`) accounts for 3 of them; the 75% bar rules out a large gap, not a small one.

## Scan probe: contact sheets for the hard-eval misses

2026-11-05. Can an agent find a moment the transcript never hints at by scanning contact sheets (many small frames per image, ~1.2k tokens per sheet like one frame)? Taken on the 5 `at` misses above, before any code. For each, a 10-min window containing the answer (offset random, seed 7; `eval/hard/scan_probe.json`) was cut into 1280x720 sheets by `eval/scan_probe.py`, two tile choices × two grids. 20 fresh agents, one per cell, got only the question, their sheets and each tile's time; no tool but `read` on their own sheets (checked in every transcript). Asked: which tiles show the moment, and the answer if readable.

| Miss | scene 3x3 | scene 4x4 | even 5 s 3x3 | even 5 s 4x4 |
|---|---|---|---|---|
| `wYSncx9zLIU` h1 coffee bag brand (3.75 s on screen) | read | read | not found | not found |
| `wYSncx9zLIU` h2 class time on app slide | read | read (low conf.) | read | found, misread 12:30 |
| `wYSncx9zLIU` h3 signpost trail number (5 s) | not found | not found | found, unreadable | found, unreadable |
| `yQ6VOOd73MA` h2 caption institution (4 s) | read | read | not found | not found |
| `yQ6VOOd73MA` h3 number on clockwork | not found | not found | read | read |
| **Located** | 3/5 | 3/5 | 3/5 | 3/5 |
| Sheets per window | 4-10 | 3-6 | 14 | 8 |

- Scene and even tiles fail on different moments: scene tiles (the last frame of each detected scene, as in normal runs) miss content in the middle of long scenes (the clockwork, 18 s scene; the signpost, inside a 22 s run of soft transitions with no detected cut). Even 5 s tiles miss shots shorter than the spacing. Every "not found" was a window with no tile inside the answer span, not a tile the agent overlooked.
- 4x4 located exactly what 3x3 did, with ~40% fewer sheets, but produced the only confident misread (12:30 for 12:15). Tiles are for finding a moment; answers need a full-size `--at` frame.
- Combining them: scene tiles plus even fill so no gap exceeds G seconds. On these 5 windows (coverage only, no agents):

| G | windows covered | tiles per 10 min | whole video, 4x4 sheets (`wYSncx9zLIU` 111 min / `yQ6VOOd73MA` 54 min) |
|---|---|---|---|
| 5 s | 5/5 | 137-160 | 102 / 54 |
| 10 s | 5/5 | 77-109 | 64 / 38 |
| 15 s | 4/5 | 60-94 | 52 / 33 |
| 30 s | 3/5 | 41-88 | 42 / 31 |

- At G = 10 s, a 10-min window is 5-7 sheets (6-8k tokens); the failed `at` searches on these two videos spent 40 and 52 extra frames (48k, 62k tokens). A whole long video is 38-64 sheets, so scanning should target windows.
- Scene detection (2 fps, 160 px) took 7.4 s for 10 min and 85 s for the 111-min keynote on an M-series laptop.
- Caveats: 5 questions, chosen because they were misses; one run per cell; the window was given, while a real agent must choose it; G was picked on these same 5, so it may be fitted to them. `yQ6VOOd73MA` was a hard-eval holdout clip and is now dev.

## Scan eval: `--scan`

2026-11-05. `vidscribe <frames-dir> --scan RANGES` as built, tested on the hard set. Fresh answer agents, the same frames and grader as "Hard eval"; `scan` agents had `--at` and `--scan` with the SKILL.md scan step as of `b103a4c`, which was not changed during the run. Method, prompt and holdout list in `eval/README.md`, "Scan eval"; grades in `eval/hard/grades.json`.

| Clip | at | scan | at extra frames | scan extra frames + sheets |
|---|---|---|---|---|
| LCEmiRjPEtQ | 3 | 3 | 12 | 12 + 0 |
| Unzc731iCUY | 3 | 3 | 12 | 24 + 30 |
| wYSncx9zLIU | 0 | 3 | 40 | 23 + 15 |
| H3KnMyojEQU | 3 | 3 | 20 | 21 + 0 |
| gDvwRpl9erE | 3 | 3 | 16 | 20 + 0 |
| xAcTmDO6NTI | 3 | 3 | 12 | 9 + 3 |
| ej5RsTtVvQE | 3 | 3 | 4 | 4 + 0 |
| JKbtWimlzAE | 3 | 3 | 16 | 2 + 3 |
| hF8swzNR1-o | 3 | 3 | 67 | 23 + 6 |
| yQ6VOOd73MA | 1 | 3 | 52 | 36 + 18 |
| x-wqMcYMNdg | 3 | 3 | 0 | 2 + 0 |
| v9DuQ1C3xH8 | 3 | 3 | 12 | 12 + 0 |
| **Dev /36** | **31** | **36** | 263 | 188 + 75 = 263 |
| Nul7mPL7Nt4 (holdout) | 3 | 3 | 52 | 30 + 3 |
| FFMm454fxNA (holdout) | 3 | 3 | 11 | 22 + 0 |
| 8qVbE9DHkEk (holdout) | 3 | 3 | 8 | 12 + 0 |
| 114i2Kz-LZA (holdout) | 3 | 3 | 20 | 12 + 3 |
| **Holdout /12** | **12** | **12** | 91 | 76 + 6 = 82 |

Dev `at` numbers are from the hard eval (agent-reported extra frames); `scan` counts and the holdout's are distinct `at_*.jpg` / `scan_*.jpg` files each agent viewed, from its transcript. One sheet costs about one frame (~1.2k tokens).

- **Decision (rule set before the run): ship.** Dev 36/36 (bar 33), holdout `scan` 12 = `at` 12 (bar: not lower), no confident wrong answers in either condition (bar: at most `at` + 1).
- All 5 `at` misses were recovered, each by scanning a window the agent chose: the three `wYSncx9zLIU` shots (0:00-2:00, 66:30-68:30, 103:00-104:40 among 7 windows tried) and two NOVA shots. No question was lost. Same total images on dev (263 vs 263): the scan agents spent sheets where `at` agents had spent frames searching.
- Agents scanned only when the transcript gave no lead: 8 of 16 clips used no `--scan`. Every scan answer was confirmed with `--at` at the tile's time; one agent first pulled the wrong tile's time and corrected it.
- `wYSncx9zLIU` h2 was answered from a second appearance of the same app screen (67:08, same "12:15 PM") rather than the reference span; correct, but the anchor was not unique.
- **Holdout at ceiling.** Both conditions scored 12/12. `at` agents reached every holdout moment from the transcript's topic, a presenter hand-over or a default frame that already showed the caption; the widest search was 52 extra frames for the Samsung name caption, which the `scan` agent found with 3 sheets and 30 frames. So the holdout shows that `--scan` costs nothing when it isn't needed (82 vs 91 images), not that it helps. 5 of the 12 first-round holdout questions failed validation because speech described the moment, and 1 replacement was guessed from general knowledge: on keynotes and lectures almost everything shown is talked about, which is also why `at` does well there.
- Caveats: the dev gain is on the 5 questions the probe used to choose the design (fill gap, grid), so it is an optimistic estimate; the holdout can't confirm it ([#2](https://github.com/SamuelZ12/vidscribe/issues/2) tracks a footage-heavy holdout). One dev agent cropped its frames with `sips` to read small text (outside the rules; no effect: 3/3 in both runs). No agent opened a path outside its folder or ran ffmpeg.

## Word timestamps (forced aligner): not built

2026-11-05. A paper check, no runs: would word-level times from Qwen3-ForcedAligner-0.6B (in mlx-audio 0.5.7, `stt/models/qwen3_asr/qwen3_forced_aligner.py`) sharpen frame and `--at` times? Today mlx-audio's srt cues are ~30 s pieces, and frame text is matched to a sentence by interpolating its time from its character offset within the cue (`bin/vidscribe`, frame heredoc).

- Of the 3 `at` misses on the 72 speech-anchored questions ("Frames on demand"), only one could be timing: the 0.75 s card (`yQ6VOOd73MA` v3), where the agent read the next card. The collage phone screen (`x-wqMcYMNdg` v1) was a misread inside the right frame, and the slide bullets (`Unzc731iCUY` mixed) appeared 6 s after the speech, beyond the agent's range. At most 1 of 72.
- The hard set names moments the transcript never speaks about, so speech timing can't help there; `--scan` already reaches 36/36 dev and 12/12 holdout.
- Cost: a second model (1.28 GB 8-bit), a pass per 30 s piece (it accepts up to 5 min of speech), and only 11 of Qwen3-ASR's ~30 languages (Chinese, Cantonese, English, German, Spanish, French, Italian, Portuguese, Russian, Korean, Japanese), so the rest would keep interpolated times.
- **Decision: not built.** Revisit if someone needs word-level output, or if a new eval shows frame-timing misses.

## Readable transcript (S1-mini): not built

2026-11-05. A paper check, no runs: should vidscribe offer a "readable" output that cleans the raw transcript with [S1-mini](https://huggingface.co/mlx-community/S1-mini-MLX-8bit) by Superwhisper (8-bit MLX, 0.65 GB)? Its model card lists punctuation, truecasing and text normalization for dictation, in English only.

- The reader is an agent, which already reads the raw transcript well: speech questions scored 11-12/12 in every eval that had them (the one miss was agent noise on an unchanged transcript). It can tidy text itself when a person needs it.
- A rewrite risks changing words an agent quotes or matches against frames (`index.txt` maps each frame to what was being said), so the raw transcript would still have to be kept and output twice.
- Cost: a second model and pass, English only (the default handles ~30 languages), and a custom license (`other`, `s1-mini-license`) that requires crediting "S1-mini" by "Superwhisper".
- **Decision: not built.** Revisit if people (not agents) become the main readers.
