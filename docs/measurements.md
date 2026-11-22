# Measurements

The tests behind vidscribe's defaults. The first section is the latest run of the four agent conditions on the three question sets, on the default frames of the time. The second and third test the overview sheets that replaced those frames ([ADR-0007](decisions/0007-overview-sheets.md)); the README's numbers came from them until [benchmark.md](benchmark.md) replaced them. The later sections are earlier tests, which the ADRs in [`decisions/`](decisions/) cite. Questions, prompts, grades and rebuild steps are in [`eval/`](https://github.com/SamuelZ12/vidscribe/tree/7a119b4786de1198ab533ebe85c0314ae35d90d7/eval).

The `eval/` folder these sections cite (questions, grades, prompts and scripts) is no longer in the repository. Every `eval/...` path below refers to [the last commit that has it](https://github.com/SamuelZ12/vidscribe/tree/7a119b4786de1198ab533ebe85c0314ae35d90d7/eval).

Terms used throughout:

- **Scores** are graded blind per question (the grader sees the question, the reference and one answer): 1 correct, 0.5 partial, 0 wrong or "unknown".
- **Conditions**: `transcript` (transcript only), `frames` (+ the run's frames and `index.txt`), `at` (+ `--at`), `scan` (+ `--scan`).
- **Frame kinds**: `even` (evenly spaced), `ref` (where the speech points at the screen: "look at this", "as you can see"), `scene` (the end of each detected scene).
- **Question IDs**: `v1`-`v4` visual-only, `mixed` and `speech` on the long set; `h1`-`h3` on the hard set (one per third of the video).
- **Dev / holdout**: holdout clips run once, after dev, with nothing changed in between. Each section's holdout is its own set of clips.
- **Cost**: one 1280x720 frame or contact sheet is ~1.2k image tokens for Claude (w*h/750).
- **Leakage**: from "Hard eval" on, every agent run was checked for opening paths outside the agent's folder and for running `ffmpeg`; no agent did either.

## Table re-run: every condition on every set

2026-11-08, master `c6aa0a6`. All four conditions on all three sets in one run, with the same downloads, code, prompts and grader, so every cell is comparable: 192 fresh agents, one per clip, set and condition. "(was N)" is the latest earlier run of that cell with the frame code then current: clips `frames` 33 is "Scene-change frames", not the clip test's 28.5, which predates scene frames. Method, prompts and deviations: `eval/README.md`, "Table re-run"; grades: `eval/table/grades.json`.

| Set | `transcript` | `frames` | `at` | `scan` |
|---|---|---|---|---|
| Clips, 2-111 min, 48 questions | 13 (was 13) | 34 (was 33) | 47 | 47 |
| Long videos, 39-111 min, 72 questions anchored on speech | 12.5 | 35.5 (was 37.5) | 68 (was 69) | 69.5 |
| Same videos, 36 questions on moments the speech never names | 0 (was 0, forced guess) | 9 (was 11) | 31 (was 31) | 35 (was 36) |

By kind (`transcript` → `frames` → `at` → `scan`):

| Set | Kind | Questions | Scores |
|---|---|---|---|
| Clips | visual | 24 | 1 → 16 → 24 → 24 |
| Clips | mixed | 12 | 0 → 6 → 11 → 11 |
| Clips | speech | 12 | 12 → 12 → 12 → 12 |
| Long | visual | 48 | 0 → 18 → 46 → 47 |
| Long | mixed | 12 | 0.5 → 5.5 → 10 → 10.5 |
| Long | speech | 12 | 12 → 12 → 12 → 12 |

- **Earlier numbers hold.** Every re-measured cell is within 2 of its earlier value, about the run-to-run noise (±1 per 12 questions).
- **Transcript only answers the speech questions and almost nothing else**: 12/12 speech on both sets, 1.5 in total on the 96 visual and mixed questions. The hard set's 0 now holds with "unknown" allowed, as in the other rows, not only under the forced-guess check.
- **Frames alone nearly triple it**: 13 → 34 on clips, 12.5 → 35.5 on long videos. `--at` closes most of the rest (47/48, 68/72). On speech-anchored questions `--scan` adds almost nothing (47, 69.5): speech already leads `--at` to the moment.
- **On moments the speech never names, `--scan` matters**: `at` 31 → `scan` 35. The one `scan` miss, `yQ6VOOd73MA` h3, is one of the 5 questions the scan probe was tuned on.
- **Cost per video** (from files on disk): long set `at` 16 extra frames, `scan` 17 frames + 0.25 sheets; hard set `at` 37 frames, `scan` 16 frames + 9 sheets; clips `at` 7, `scan` 6 frames. Agents viewed every original frame in 69 of 72 `frames`, `at` and `scan` folders on the long sets and 33 of 36 on clips.
- **Every condition missed `Gjnup-PuquQ` q3** ("AWS and Google Cloud", on screen at 1:07 per the time check). It may be too brief or too small to read; check it before the clip set is reused.

README headline until the overview-sheets run below replaced it: the three rows summed, 156 questions on 21 videos (3 clips are also long videos, with different questions): 25.5, 78.5, 146, 151.5. Caveats that come with it:

- The 36 hard questions were kept only if a transcript-only agent failed them, so their 0 is by construction and pulls the first column down.
- The `--scan` gain is optimistic: its design was tuned on the 5 questions `--at` missed, and a 4-video holdout scored 12/12 with and without it ([#2](https://github.com/SamuelZ12/vidscribe/issues/2)).
- These agents got eval prompts that also required viewing every frame and fetching more. Given only `skill/SKILL.md`, agents scored 69/72 on the long set but 33-34/36 on the hard set across four runs and three wordings (searches stopped sooner; see "SKILL.md re-test").
- Outside evidence: [Omni2Web](https://arxiv.org/html/2609.23417) saw a similar frames jump on its instruction-recovery track (Gemini 3.5 Flash on screen-recorded web edits: transcript only 18.2, silent video + transcript 38.1). On sound, [SleuthVLM](https://arxiv.org/abs/2611.06083)'s audio-captioning tool added 9.8 points on 448 music questions, which vidscribe doesn't cover.

## Overview sheets against the current default frames

2026-11-15, branch `overview-sheets` at `fdb5961` against master `28966e5`. The branch replaces the default frames (up to 40 full-size) with overview sheets: 4x4 contact sheets of evenly spaced tiles, one per 10 s, 16 to 96 in all. The question, with bars set before the run: does that cost answers? (The bars and the smoke cases were in `SPEC.md`, deleted after the merge: `git show fb6618c:SPEC.md`.)

Since this run the tile count has changed ([ADR-0008](decisions/0008-full-sheets.md)): 16 tiles per sheet and one sheet per 160 s of picture, rounded to the nearest, 1 to 6 sheets. This run used the old counts. Under the new rule 15 of the 21 videos get the same tiles; six clips get 1 to 5 tiles more or fewer (37 to 32, 44 to 48, 47 to 48, 52 to 48, 61 to 64, 79 to 80). The `vidscribe` arm was run again with the new counts: [Re-run of the `vidscribe` arm with the shipped script](#re-run-of-the-vidscribe-arm-with-the-shipped-script).

One run, three arms on the three question sets, 108 fresh agents (one per video, set and arm): `transcript` (transcript only), `current` (master's default frames and `skill/SKILL.md`), `vidscribe` (the branch's overview sheets and `skill/SKILL.md`). Both picture arms got only the SKILL.md as instructions and could run `--at` and `--scan`; in both arms those calls ran master's script (see "`--at A-B/N` was not tested" below). All arms share downloads, transcripts (byte-identical between the two scripts on all 21 videos), prompts and grader. **The agents were Codex (`gpt-6.1-sol`, medium effort), not Claude subagents as in every other section, so compare arms within this table, not with numbers elsewhere in this file.** Method, prompts and deviations: `eval/README.md`, "Overview sheets"; grades: `eval/overview/grades.json`.

| Set | `transcript` | `current` | `vidscribe` |
|---|---|---|---|
| Clips, 2-111 min, 48 questions | 12 | 47.5 | 46.5 |
| Long videos, 39-111 min, 72 questions anchored on speech | 12 | 71 | 70 |
| Same videos, 36 questions on moments the speech never names | 0 | 33 | 36 |
| All 156 questions | 24 | 151.5 | 152.5 |

Bars, the same on each set: `vidscribe` at most 2 points below `current`, and at most one more wrong answer that is not "unknown".

| Set | Score, `vidscribe` − `current` | Wrong, not "unknown": `current` → `vidscribe` | Bars |
|---|---|---|---|
| Clips | −1 | 0 → 0 | met |
| Long | −1 | 1 → 2 | met (wrong answers at the limit) |
| Hard | +3 | 3 → 0 | met |

- **Every bar is met; the two arms differ on 5 of 156 questions.** `vidscribe` lost 2 and gained 3. No time-check question was dropped.
- **Both losses are moments where master's default full-size frame happened to show the answer.** Clip `Yv2iYYewdf0` (5 min) q3: `current` read the formula off `005_03m38.6s_even.jpg`; the `vidscribe` agent fetched frames at 3:30, 3:32.8, 3:40.5 and 3:43.6, scanned 3:25-3:41, missed 3:37 and answered "unknown". Long `ej5RsTtVvQE` v3: `current` read the diagram off a default scene frame at 36:21; the `vidscribe` agent fetched 35:48 and named the wrong node with high confidence.
- **All three gains are hard questions `current` got wrong** (`yQ6VOOd73MA` h2 and h3, `x-wqMcYMNdg` h3); `vidscribe` scored 36/36 there. One run, so this is within noise, not evidence that sheets search better.
- **Wrong answers that are not "unknown"**: `vidscribe` 0 / 2 / 0, `current` 0 / 1 / 3 (clips / long / hard). On the long set one is shared: both arms read the wrong text near the end card of `H3KnMyojEQU` (v4).
- **No answer was read off a sheet.** Of the 132 visual, mixed and hard answers, `vidscribe` cited a full-size frame its agent had opened in 131; the other is the "unknown" above. `current`: 131, and one answer citing a frame the agent never opened (wrong).
- **Agents opened every sheet**: all sheets in 36 of 36 `vidscribe` folders; every default frame in 34 of 36 `current` folders.
- **Images viewed per video**, counted from the agents' logs:

  | Set | Arm | Default pictures | `--at` frames | Scan sheets | Total |
  |---|---|---|---|---|---|
  | Clips | `current` | 27.8 | 6.1 | 0.4 | 34.3 |
  | Clips | `vidscribe` | 3.7 | 5.4 | 0.5 | 9.6 |
  | Long | `current` | 39.6 | 9.6 | 0.8 | 50.0 |
  | Long | `vidscribe` | 6.0 | 9.1 | 0.6 | 15.7 |
  | Hard | `current` | 39.5 | 9.1 | 6.2 | 55.2 |
  | Hard | `vidscribe` | 6.0 | 8.0 | 6.7 | 20.8 |

  With sheets, agents did not fetch more frames to make up for the smaller default: `--at` and `--scan` use is about the same in both arms. Input tokens per agent, summed over its requests, fell by about half (311k vs 636k, 464k vs 999k, 745k vs 1,393k).
- **`--at A-B/N` was not tested** (found after the run, 2026-11-15). Codex runs each command in a login shell, which put the installed `vidscribe` (master) ahead of the arm's copy on `PATH`, so every `--at` and `--scan` call in both arms ran master's script. Without a count the two scripts print the same lines and save the same files (smoke case S11 of the spec), so the scores stand as sheets against frames, each with its own SKILL.md. But the 6 `--at` calls that gave a count, of 95 in the `vidscribe` arm, all failed with `bad time`. The six agents went on to fetch frames without a count, and each scored full marks, as `current` did on the same questions.
- **Re-check of those six with the branch script** (`8a165f2`, path fixed, six fresh agents on rebuilt folders; `eval/overview/recheck.json`). All 33 `--at` and `--scan` calls ran the branch script. Four of the six agents gave counts: 12 ranges in 8 calls, 3 to 8 frames each, every call succeeded and every frame fetched was viewed. One (`hard` `wYSncx9zLIU`) used counts on stretches of 6-15 s and fetched 44 frames where it had fetched 27.
- **The re-check scored 20 of 23, where the first run's agents on the same folders scored 23** (same grader, 23 calls). No miss came from a failed call or a wrong frame; in each the agent looked at the wrong moment or read the frame differently:

  | Question | Re-check answer | What happened |
  |---|---|---|
  | `hard` `v9DuQ1C3xH8` h2 (bread rolls in a painting) | "Croissants" | A single time, no count. The first run read the same moment as "Croissants (bread rolls)" and got the point. |
  | `hard` `wYSncx9zLIU` h3 (trail number, at 104:10) | "unknown" | The agent looked for the signpost at 93:55-95:08 with 32 counted frames and fetched nothing after 99 min. |
  | `main` `yQ6VOOd73MA` `mixed` (a square, at 16:04-16:09) | "An upside-down U" | The agent fetched 16:12 and `16:14-16:20/3`. Its frame at 16:17 does show that shape: a later pair of shapes in the same test. |

  This neither confirms nor refutes the headline for the shipped script. Six agents that all had full marks can only stay level or drop when re-run, and each of the three questions was also missed in an earlier run (`eval/hard/grades.json` `skill_old`; `eval/table/grades.json` `at`). But two of the three misses came with counted ranges on the wrong stretch, and with these six in place of the first run's, `main` would be 69 of 72 with 3 wrong answers, one over its limit of 2, and `hard` 34 of 36 (149.5 of 156, 96%). The fair test is the whole `vidscribe` arm re-run with the path fixed: the next section.
- **Leakage**: no agent opened a path outside its folder, ran `ffmpeg` or searched the web; every image an agent was shown matched a file in its own folder.

Caveats:

- One run per cell; earlier runs put the noise at about ±1 per 12 questions, so differences of 1 mean nothing and the hard set's +3 may not either.
- Codex agents, at the owner's choice, and they ran with the owner's global Codex instructions (commands prefixed with `rtk`). `current` scored 71 and 33 here where Claude agents given the SKILL.md of the time scored 69 and 33-34 ("SKILL.md re-test"), so the two kinds of agent look close on these sets, but that is a comparison across runs.

README headline: `transcript` from this run and `vidscribe` from the re-run in the next section, summed over the 156 questions: 24 and 150.5, so 15% and 96%. (Until that re-run the README gave this run's `vidscribe` column: 152.5, 98%.) Besides the caveats above:

- The 36 hard questions were kept only if a transcript-only agent failed them, so `transcript`'s 0 there is by construction. On the other 120 questions the two columns are 24 and 116.5: 20% and 97%.
- `vidscribe` here means overview sheets, `--at` and `--scan` in the hands of an agent given `skill/SKILL.md`; the answers come from the full-size frames it fetched, not from the sheets alone.
- The two columns come from two runs on the same day, with the same downloads, transcripts, agent model, prompt and grader.

## Re-run of the `vidscribe` arm with the shipped script

2026-11-15, master `6b9ef04` ([#10](https://github.com/SamuelZ12/vidscribe/issues/10)). In the run above the `vidscribe` arm had the tile counts from before ADR-0008 and master's `--at` and `--scan`. Here 36 fresh agents (one per video and set; the same Codex model, prompt and grader) got the shipped script's output and `skill/SKILL.md`, with the shipped script first on `PATH`: all 125 of their `--at` and `--scan` commands ran it. The transcripts are the first run's (byte-identical on the ten videos transcribed again). The `transcript` and `current` arms were not re-run, so each comparison below is with a score recorded in the section above, and run-to-run noise sits on top of any difference. Rule set before the run: the README takes this arm's number whatever it is. Method: `eval/README.md`, "Overview sheets". Per agent and question: `eval/overview/rerun.json`.

| Set | `current`, first run | `vidscribe`, first run | `vidscribe`, re-run |
|---|---|---|---|
| Clips, 48 questions | 47.5 | 46.5 | 47.5 |
| Long videos, 72 questions | 71 | 70 | 69 |
| Hard, 36 questions | 33 | 36 | 34 |
| All 156 questions | 151.5 | 152.5 | 150.5 |

The same bars, against the recorded `current`:

| Set | Score, re-run − `current` | Wrong, not "unknown": `current` → re-run | Bars |
|---|---|---|---|
| Clips | 0 | 0 → 0 | met |
| Long | −2 | 1 → 3 | score met at the limit; wrong answers missed (limit 2) |
| Hard | +1 | 3 → 1 | met |

- **The long set misses its wrong-answer bar by one; every other bar is met.** Its three wrong answers:

  | Question | Re-run answer | What happened |
  |---|---|---|
  | `ej5RsTtVvQE` v3 (which node the arrow leaves; reference "Throw Away") | "Abstract" | The same answer from the same frame (35:48.3) as the first run's `vidscribe` agent. `current` read the diagram off a default scene frame at 36:21. |
  | `H3KnMyojEQU` v4 (text on the end card) | The legal text at 71:50 | Wrong in all three arms. |
  | `Unzc731iCUY` v4 (time in the "LIVE" graphic; reference "11:23 pm ET") | "8:23 pm PT", from 60:43 | The first run's `vidscribe` agent gave the same answer from 60:30 and the grader gave it 1, as the same moment in another time zone. This time the grader gave it 0. `current` read "11:23 pm ET" at 59:55. |

  So the bar is missed on an answer the grader has scored both ways. With the first run's grade for it, the long set would be 70 with 2 wrong answers, the first run's result. It is the only grade that moved without the answer changing: in the 175 cases where a re-run answer has the same text as a first-run answer to the same question (either picture arm), the grade is the same.
- **None of the three came with a counted range.** The check agreed before the run, should the long set fail on wrong answers, was the `/N` wording in `skill/SKILL.md`: these three agents gave no count in any call.
- **`--at A-B/N` in agents' hands**: 7 of the 36 agents gave counts, for 15 ranges in 11 calls, 3 to 15 frames each. Ten calls worked; one failed for the reason in the next point and worked when repeated. One answer gained traces to a count: clip `Yv2iYYewdf0` q3, "unknown" in the first run, was read off the third frame of `3:29-3:38/4`.
- **Five commands failed, each for giving `--at` and `--scan` together** (five agents). The script printed its usage line and each agent ran the two separately. The other 120 commands succeeded.
- **Against the first run's `vidscribe` arm, 4 of 156 questions differ**: the clip gain and the grader change above, and two hard questions lost. `yQ6VOOd73MA` h2: the agent read a caption at 17:55.5 ("University of California, Santa Barbara"; the reference caption is at 24:21), the same wrong answer `current` gave; no count. `wYSncx9zLIU` h3 (trail number at 104:10): "unknown", as in the re-check. The agent scanned 92:30-95:30 and 98:00-100:15, fetched 15 counted frames inside 93:54-94:46 and fetched nothing later. Both agents whose `--at` took counts (the re-check's and this one) missed this question on the same stretch; both first-run picture agents found it. Two runs cannot tell whether counts keep an agent on a wrong stretch.
- **No answer was read off a sheet**: 131 of the 132 visual, mixed and hard answers cite a full-size frame the agent had opened; the other is the "unknown" above. Every agent opened every sheet (186 sheets in 36 folders).
- **Images viewed per video** are about what they were in the first run: 3.5 sheets, 5.6 `--at` frames and 0.2 scan sheets on clips (9.3 in all), 6.0, 9.5 and 0.9 on the long set (16.4), 6.0, 9.2 and 6.6 on the hard set (21.8). Input tokens per agent: 233k, 465k, 769k.
- **Leakage**: no agent opened a path outside its folder, ran `ffmpeg` or searched the web; all 573 images shown matched a file in the agent's own folder.

Caveats: one run, with the noise described above (about ±1 per 12 questions), so 150.5 and the first run's 152.5 are not told apart, and neither is 150.5 from `current`'s 151.5. Codex agents with the owner's global Codex instructions, as before.

## Frame cap: 40

2026-11-04, master `bb029cd`. Frames take ~60 ms each to extract, so the cap is about the agent reading them. On the Karpathy keynote (`LCEmiRjPEtQ`, 39.5 min, 720p) a run took 4m00s (~3m45s transcription, 10 s download, 3 s audio conversion) and gave 25 frames: 7 even (one of 8 dropped for a ref frame within 3 s) and 18 ref, 1.9 MB of JPEGs.

- Ref frames grow with speech: 0.46-0.57 per minute on full transcripts (Karpathy 18, MIT 36, Google I/O 57). With 8 even frames, the cap starts trimming refs at about 60-65 min; a 2 h talk would give ~72 frames, ~90k image tokens.
- Rule: always keep the N even frames. If even + ref exceeds 40, keep `40 - even` ref frames spread evenly over the list of refs. `-v N` with N > 40 is honored with even frames only. Scene frames later took a share of the same slots ("Scene-change frames").

## Clip test: frames vs transcript only, cap vs no cap

2026-11-04, branch `video-default` (`fbddc2b`).

Method: 12 YouTube clips (2-111 min), 4 questions each (2 visual-only, 1 mixed, 1 speech), written by one agent per clip from the full transcript and dense frames (questions: `eval/clips/`). A: transcript only. B: + vidscribe's frames and `index.txt`. C: B without the cap, on the 2 clips where it triggered. The model cut the 3 long clips short ("Long audio"), so in every condition they used transcripts merged from 30-min chunks.

A → B: 13 → 28.5/48; visual 1 → 11.5/24, mixed 0 → 5/12, speech 12 → 12/12. B never scored lower than A on any question, and every B miss was "unknown", never a wrong answer. The misses were moments no frame captured (a slide caption, a jug, a hedge), which scene frames target.

- **Cap: no sign that more frames help.** MIT lecture B = C (3/4). Google I/O C did worse (0 vs 1): with 65 frames it answered even the speech question "unknown". 4 questions per clip can only detect large effects.
- **Agents skip frames in large sets.** Before being told to view every frame, 3 of 15 frame-condition agents viewed only part of their set (8/16, 8/13 and 2/65 frames).

## Long audio: token budget, not audio length

2026-11-04. The model stopped early on long talks: at 2021 s of 2371 s (Karpathy), 2862 s (MIT, 64 min) and 2876 s (Google I/O, 111 min). mlx-audio decodes ~30 s pieces but spends one `--max-tokens` budget (default 8192) across the whole file, so where it stops depends on how many tokens the speech needs:

| Speech | tok/s | Budget runs out at |
|---|---|---|
| English lecture (MIT) | ~2.5 | ~55 min |
| English talk (Karpathy) | ~3.5 | ~39 min |
| Hindi, Devanagari (C-39pLx6QTQ) | ~10 | ~13.5 min |

Raising the budget alone (`--max-tokens 32768`, MIT) transcribed to the end, matching the chunked transcript in every 5-min window, but took 1744 s: 17 s of closing applause looped as "oh, oh, ..." for 22k tokens until the budget ran out. Such loops are common: 4 of the 8 videos with SRTs on this machine had one, and in one a 30 s "hey, hey" piece used 8148 tokens, the whole budget.

- `repetition_penalty=1.1` (mlx-audio's built-in) stopped the loop (MIT 298 s) but changed real words: 0-1% on English and Mandarin clips, with errors like "stock or" → "stockor" and "google" → "g o o g l e", and 15.8% on the Hindi clip. Rejected.
- Per-piece cap (shipped): each piece may use at most `32 + 25 tok/s × piece length`. Real speech peaks at 15.9 tok/s per piece (Hindi; 816 cues measured). The file budget becomes `8192 + 32 × seconds`, so it never binds first.

Result: 9 short clips byte-identical to uncapped output; MIT 319 s, full coverage, every cue identical to the uncapped run except the loop, which is 222 words instead of 3840.

2026-11-05, split and retry. A piece that hit its cap was still cut off silently (the end token is never counted, so reaching the cap means cut off). Now such a piece is split at its quietest 100 ms in the middle half and each half is redone with its own cap. A loop shrinks to a piece under 8 s, which keeps its capped text and prints `warning: transcript cut off in HH:MM:SS-HH:MM:SS`. Under 8 s the cap allows over 29 tok/s, nearly twice the real-speech peak.

- A 30 s piece that loops throughout costs up to 11 decodes (~3.4k tokens instead of 782). Each leaf's 32-token base lets a split piece slightly exceed its share of the file budget; the 8192 slack covers that unless hours of audio loop.
- Checked on a 41 s `say` clip in throwaway copies of the script. A cap of 20 on every piece used to give 38 of 174 words with no warning; it now gives 113 words and six warnings. A cap of 20 only on pieces over 20 s recovers all 174 words (6 commas differ) with no warning. txt, srt and frame-mode outputs are byte-identical to master.
- MIT lecture (`-a -f srt`): 344 s, one warning (`01:03:25-01:03:29`, the closing applause), last cue at 01:03:42 (the end). The loop is ~105 words, down from 222 with the per-piece cap alone.
- MIT lecture again, 2026-11-15, under the current default (language detected per piece, ADR-0006): the full file (63:42, a fresh download, run as `vidscribe <video> -f srt` for the overview-sheets eval, not `-a -f srt`) gave no warning and no loop. The cue before the applause ends "(Laughter) (Applause)"; the last cue (`01:03:25-01:03:42`) has no text. Master (`28966e5`) and the overview-sheets branch gave the same transcript. The run does not isolate the cause: the download differs from the earlier run's, and so may anything else changed since (issue #5).

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

- The 0.197 is mostly digits ("1.19" vs "一点一九").
- D1PjB0cwiKg, SXqUyVzHgeE (no subtitles) and English 30 s followed by Mandarin 60 s read the same in every mode except spacing around English words and digits. English (up1xuwn_euk, 360 words): 2 quote marks differ.
- Hindi (C-39pLx6QTQ, ZwJ1zktkSfk): auto-detect and `Hindi` write English terms in Devanagari without punctuation, once wrongly (`VideoWriter` → `वीडियो राइट करता`); forced `en` and `English` keep them in Latin script. `-l zh` gave the same text as `-l Chinese`; `-l hi` was a mix of the `en` and `Hindi` outputs.
- The last 80 s of the MIT lecture alone didn't loop in either mode, so the applause there is inconclusive. (The full lecture did not loop in a later run: "Long audio".)

Decision: [ADR-0006](decisions/0006-detect-language-per-piece.md).

## Scene-change frames

2026-11-04. Cut detection: ffmpeg at 2 fps and 160 px, `scene > 0.3`; ~0.75 s per minute of video (84 s for 111 min), ~15% on top of transcription. Cuts per minute ranged from 0.2 (animated charts: gradual changes don't register) to 8.5 (Mandarin slides); every clip over ~10 min has more cuts than the cap.

One frame per scene, at its last sampled frame, so slide builds and typed text are complete. Dropped: scenes under 1 s, flat frames, scenes within 3 s of a ref frame, and repeats of an earlier scene (dHash on a 9x8 thumbnail, ≤ 6 of 64 bits). Dedupe removes less on long talks than hoped (MIT 262 → 218, Google I/O 817 → 599): wide and close-up stage shots don't count as repeats.

Two ways to share the 40-frame cap, compared on the 12 clips with a free check (is there a frame in the same scene as the question's moment?):

| Frame set | Visual | Mixed | Speech | All (48) |
|---|---|---|---|---|
| master (even + ref) | 12/24 | 6/12 | 10/12 | 28 |
| split: keep all even frames, refs and scenes share the rest | 17/24 | 7/12 | 10/12 | 34 |
| replace: scenes and refs first, even frames only fill empty slots | 18/24 | 7/12 | 9/12 | 34 |

A tie, so split shipped: it keeps even spacing for videos without hard cuts and leaves `-v N` unchanged.

Agent test, same method as the clip test, with every agent viewing every frame (checked from transcripts). Holdout: 4 new clips (screencast, coding tutorial, cooking, Mandarin explainer) whose questions a separate agent wrote after the frame code was fixed.

| Set | Transcript only | master | scene frames |
|---|---|---|---|
| 12 original clips | 13/48 | 28.5/48 | 33/48 |
| 4 holdout clips | 5/16 | 11.5/16 | 12.5/16 |

9 questions changed: 8 gained, 1 lost (sign test p ≈ 0.04). All 6 gains traced to the frame the agent cited were scene frames, so the gain is not just from more frames (332 vs 206 on the 12 clips). The loss: MIT, where scenes took half of the slots refs used to have. No new wrong answers; misses stayed "unknown". The three long talks gained nothing (1, 1, 2 of 4): 16 of hundreds of scenes fit the cap, and a third of the Karpathy picks were stage shots.

## Scene choice on long videos (not shipped)

2026-11-04. On long videos only ~16 of 100-650 scenes fit the cap, and master thins them evenly over the scene list. Two ways to pick better were tried:

- **A: skip recurring shots.** Count how often a scene's look (9x8 dHash within 10 bits) recurs; prefer looks seen fewer than 3 (or 8) times, and keep one frame of each recurring look. It works when one camera angle dominates (Karpathy's close-up). It backfires on lectures, where the same slide template or IDE recurs and handheld lecturer shots don't. On Google I/O every slide shown on the stage screen hashes like the stage; a 32x18 dHash didn't separate them either (two slides 88 bits apart, two close-ups of one speaker 73).
- **B: content score.** Score each scene by the share of 32x18 pixels at its most common brightness (plain backgrounds = slides, screens, cards), split the video into as many equal spans as slots, and keep the best scene per span. Same ffmpeg pass; uncapped clips byte-identical.

Probe: of the 16 scene frames picked, how many mainly show content (slide, screen, graphic) rather than speaker, stage or audience. Counted by hand, not blind.

| Clip | master | A | B |
|---|---|---|---|
| Karpathy keynote | 5 | 13 | 12 |
| MIT lecture (Unzc731iCUY) | 3 | 1 | 5 |
| MIT 6.100L lecture (xAcTmDO6NTI) | 7 | 1-2 | 13 |
| Google I/O | 8 | 9 | 13 |
| PyCon UK keynote (gDvwRpl9erE) | 9 | 10 | 10 |
| Apple event (H3KnMyojEQU) | ~8 | ~7 | 16 |

Agent test of B on the 12-video long set (`eval/README.md`; per-clip grades under `master` and `scene_b` in `eval/grades.json`). Both conditions used the same transcript; only the frame-selection code differed, and every answer agent viewed every frame.

- master 37.5 vs B 36.5 of 72. Visual 19 vs 19/48, mixed 6.5 vs 6.5/12, speech 12 vs 11/12 (agent noise: same transcript). 7 questions changed, 3 up and 4 down. Free check (a frame inside the span where the answer is on screen): 23 vs 23 of 60.
- B does pick more content. A blind judge labeled the 209 scene frames of each condition as content / speaker or stage with a legible slide / speaker, stage or audience only / blank: 71 / 37 / 101 / 0 (master) and 122 / 21 / 57 / 9 (B; the blanks are near-black or logo-only cards, which a plain-background score favors).
- But with 16 slots across hundreds of scenes, whether a frame lands on the moment a question asks about is luck either way: on long videos the number of frames limits pinpoint questions, not which scenes are chosen. Not shipped; see [ADR-0004](decisions/0004-frames-on-demand.md).

## Frames on demand

2026-11-04. `vidscribe <frames-dir> --at TIMES` extracts frames from the run's `video.<ext>` at chosen times (a range gives 4); SKILL.md tells agents to find the moment in the transcript and fetch it. Same 12 long videos, 72 questions, transcripts and master frame folders as the scene-choice test; the only change is that answer agents may run `--at`. Master scores are the existing grades. Dev clips ran first; SKILL.md wording was then frozen for the holdout.

master 37.5 → `at` 69/72 (per clip: `eval/grades.json`). Visual 19 → 46/48 (holdout 10 → 22/24), mixed 6.5 → 11/12, speech 12 → 12/12. 33 questions went up, 1 down. Well past the ship bar set beforehand (≥ +6/48 visual, holdout visual not lower, speech within ±1).

- Cost: 1-3 `--at` calls and 4-23 extra frames per video, 16 on average (about 19k tokens); extraction takes ~0.05 s per frame. Agents asked for single times or 10-50 s ranges around the cue the question pointed at.
- The 3 misses are all precision, not missing coverage, and all three are confident wrong answers: a card on screen for 0.75 s (the agent read the next card), a 4 s phone screen in a collage (a neighbouring outlet; master got this one right), and a slide whose bullets appeared 6 s after the agent's last frame (it guessed instead of fetching a wider range).
- One agent passed a range past the end; the call fails as a whole with a clear message, and it retried.
- Caveat: the questions anchor on speech ("when the speaker says ..."), which is the case `--at` is built for. Moments the transcript never hints at still depend on the automatic 40 frames; "Hard eval" tests them.

## Hard eval: moments the transcript never names

2026-11-05. Same 12 videos, re-downloaded and transcribed with master `b3fa881`. 36 new questions, 3 per video (one per third), each naming its moment only by what is on screen: the anchor is not spoken within 60 s and the answer is never spoken. A transcript-only agent that had to guess scored 0/36. Method, validation and prompts: `eval/README.md`, "Hard set"; grades: `eval/hard/grades.json`. Conditions: `frames` (the run's 39-40 frames) and `at` (the same plus `--at`).

`frames` 11 → `at` 31/36. Dev 3 → 15/18, holdout 8 → 16/18.

- **Decision (rule set before the run): OCR timeline not built.** `at` scored 31/36 (86%), above the 75% bar. All 5 misses are "not found" (no viewed frame inside the anchor span), the kind OCR would target, but there are too few to justify it. See [ADR-0005](decisions/0005-no-ocr.md).
- Agents find unnamed moments from related speech, not the anchor itself: presenter hand-overs ("Here's Raja") for name captions, or the topic being discussed (Photoshop mentioned before a slide comparing it with Unreal; "LLMs click stuff" before an Operator screenshot; a Logan Airport story before a terminal map). On talks and keynotes, what is shown is usually what is being discussed.
- The misses are where that link is missing: three brief shots in the 111-min Google I/O keynote that the speech never describes (a montage clip, a demo slide, a 5 s photo; `wYSncx9zLIU`, 40 extra frames, 0/3), and two NOVA documentary shots (stock footage of a watch movement; an interviewee whose caption appears once) that the agent searched for with 52 extra frames.
- Searching costs more than with speech-anchored questions: 0-67 extra frames per video, 263 in total (about 26k tokens per video, against ~19k in "Frames on demand"). The largest were long searches: `hF8swzNR1-o` 67 (3/3), `yQ6VOOd73MA` 52 (1/3), `wYSncx9zLIU` 40 (0/3).
- Every miss in both conditions was an honest "unknown"; no confident wrong answers.
- `frames` alone got 11/36, mostly where the answer stays on screen (a podcast's background shelves, 3/3) or lands on a default frame by chance.
- Caveat: 36 questions, 5 misses, and one video (`wYSncx9zLIU`) accounts for 3 of them; the 75% bar rules out a large gap, not a small one.

## Scan probe: contact sheets for the hard-eval misses

2026-11-05, before any code. Can an agent find a moment the transcript never hints at by scanning contact sheets (many small frames per image, each sheet costing about one frame)? For each of the 5 `at` misses, a 10-min window containing the answer (offset random, seed 7; `eval/hard/scan_probe.json`) was cut into 1280x720 sheets by `eval/scan_probe.py`: two tile choices × two grids. 20 fresh agents, one per cell, got only the question, their sheets and each tile's time, with no tool but `read`. Asked: which tiles show the moment, and the answer if readable.

| Miss | scene 3x3 | scene 4x4 | even 5 s 3x3 | even 5 s 4x4 |
|---|---|---|---|---|
| `wYSncx9zLIU` h1 coffee bag brand (3.75 s on screen) | read | read | not found | not found |
| `wYSncx9zLIU` h2 class time on app slide | read | read (low conf.) | read | found, misread 12:30 |
| `wYSncx9zLIU` h3 signpost trail number (5 s) | not found | not found | found, unreadable | found, unreadable |
| `yQ6VOOd73MA` h2 caption institution (4 s) | read | read | not found | not found |
| `yQ6VOOd73MA` h3 number on clockwork | not found | not found | read | read |
| **Located** | 3/5 | 3/5 | 3/5 | 3/5 |
| Sheets per window | 4-10 | 3-6 | 14 | 8 |

- Scene and even tiles fail on different moments. Scene tiles (the last frame of each detected scene, as in normal runs) miss content in the middle of long scenes (the clockwork, an 18 s scene; the signpost, inside a 22 s run of soft transitions with no detected cut). Even 5 s tiles miss shots shorter than the spacing. Every "not found" was a window with no tile inside the answer span, not a tile the agent overlooked.
- 4x4 located exactly what 3x3 did, with ~40% fewer sheets, but produced the only confident misread (12:30 for 12:15). Tiles are for finding a moment; answers need a full-size `--at` frame.
- Combining them: scene tiles plus even fill so no gap exceeds G seconds. On these 5 windows (coverage only, no agents):

| G | windows covered | tiles per 10 min | whole video, 4x4 sheets (`wYSncx9zLIU` 111 min / `yQ6VOOd73MA` 54 min) |
|---|---|---|---|
| 5 s | 5/5 | 137-160 | 102 / 54 |
| 10 s | 5/5 | 77-109 | 64 / 38 |
| 15 s | 4/5 | 60-94 | 52 / 33 |
| 30 s | 3/5 | 41-88 | 42 / 31 |

- At G = 10 s, a 10-min window is 5-7 sheets (6-8k tokens), where the failed `at` searches on these two videos spent 40 and 52 extra frames (48k, 62k tokens). A whole long video is 38-64 sheets, so scanning should target windows.
- Scene detection (2 fps, 160 px) took 7.4 s for 10 min and 85 s for the 111-min keynote on an M-series laptop.
- Caveats: 5 questions, chosen because they were misses; one run per cell; the window was given, while a real agent must choose it; G was picked on these same 5, so it may be fitted to them. `yQ6VOOd73MA` was a hard-eval holdout clip and is now dev.

## Scan eval: `--scan`

2026-11-05. `vidscribe <frames-dir> --scan RANGES` as built, on the hard set: fresh answer agents, the same frames and grader as "Hard eval". `scan` agents had `--at` and `--scan`, with SKILL.md's scan step as of `b103a4c`, unchanged during the run. Method, prompt and holdout list: `eval/README.md`, "Scan eval"; grades and per-clip costs: `eval/hard/grades.json`.

| Set | `at` | `scan` | Images viewed, `at` | Images viewed, `scan` |
|---|---|---|---|---|
| Dev (the 12 hard-eval videos), /36 | 31 | 36 | 263 frames | 188 frames + 75 sheets = 263 |
| Holdout (4 new videos), /12 | 12 | 12 | 91 frames | 76 frames + 6 sheets = 82 |

Dev `at` counts are the hard eval's agent-reported extra frames; the rest are distinct `at_*.jpg` / `scan_*.jpg` files each agent viewed, from its transcript.

- **Decision (rule set before the run): ship.** Dev 36/36 (bar 33), holdout `scan` 12 = `at` 12 (bar: not lower), no confident wrong answers in either condition (bar: at most `at` + 1).
- All 5 `at` misses were recovered, each by scanning a window the agent chose: the three `wYSncx9zLIU` shots (0:00-2:00, 66:30-68:30 and 103:00-104:40, among 7 windows tried) and two NOVA shots. No question was lost. The scan agents spent sheets where `at` agents had spent frames searching.
- Agents scanned only when the transcript gave no lead: 8 of 16 clips used no `--scan`. Every scan answer was confirmed with `--at` at the tile's time.
- `wYSncx9zLIU` h2 was answered from a second appearance of the same app screen (67:08, same "12:15 PM"): correct, but the anchor was not unique.
- **Holdout at ceiling.** `at` agents reached every holdout moment from the transcript's topic, a presenter hand-over or a default frame that already showed the caption; the widest search was 52 extra frames for the Samsung name caption, which the `scan` agent found with 3 sheets and 30 frames. So the holdout shows that `--scan` costs nothing when it isn't needed, not that it helps. 5 of the 12 first-round holdout questions failed validation because speech described the moment, and 1 replacement was guessed from general knowledge: on keynotes and lectures almost everything shown is talked about, which is also why `at` does well there.
- Caveats: the dev gain is on the 5 questions the probe used to choose the design (fill gap, grid), so it is optimistic, and the holdout can't confirm it ([#2](https://github.com/SamuelZ12/vidscribe/issues/2) tracks a footage-heavy holdout). One dev agent cropped its frames with `sips` to read small text (outside the rules; 3/3 in both runs, so no effect).

## Scan sheets filled to 16 tiles

2026-11-15, no agent runs. `--scan` padded a short last sheet white: `--scan 1:26-1:40` on `dQw4w9WgXcQ` gave 5 tiles on a 1280x720 sheet, and a sheet costs the same image tokens however many tiles it holds. Of the 309 `scan_*.jpg` sheets left by the overview-sheets eval (`/tmp/vsov`), 185 had at least one blank row and 349 of 1,236 rows were blank (a row counted as blank when its first cell was white, so a white video frame there is miscounted).

Change: the tile count per range is rounded up to a multiple of 16. Each extra tile goes into the gap where tiles are furthest apart, and that gap's fill tiles are respaced evenly. Scene tiles, the 10 s limit and the sheet count per range stay as they were, so no range costs more.

| Range on `dQw4w9WgXcQ` (3:33) | Tiles before | Tiles after | Sheets |
|---|---|---|---|
| 1:26-1:40 | 5 | 16, one per ~0.9 s | 1 |
| 0:00-2:40 | 24 | 32 | 2 |
| `all` | 32 | 32, sheets and output byte-identical | 2 |

- All 5 scene tiles of 1:26-1:40 are on the new sheet. In 0:00-2:40, 7 fill tiles moved (their gaps were respaced) and every scene tile stayed.
- A range of a few seconds gets 16 near-identical tiles (1:26-1:29: one per 0.18 s). Left as is: no extra cost.
- Not measured: whether denser tiles change answers. The scan eval above scored the old picks, and its ranges mostly gain a few tiles on the last sheet. [#9](https://github.com/SamuelZ12/vidscribe/issues/9) (items on screen under 5 s) would need its own question set.

## Word timestamps (forced aligner): not built

2026-11-05, a paper check with no runs: would word-level times from Qwen3-ForcedAligner-0.6B (in mlx-audio 0.5.7, `stt/models/qwen3_asr/qwen3_forced_aligner.py`) sharpen frame and `--at` times? Today mlx-audio's srt cues are ~30 s pieces, and frame text is matched to a sentence by interpolating its time from its character offset within the cue (`bin/vidscribe`, frame heredoc).

- Of the 3 `at` misses on the 72 speech-anchored questions ("Frames on demand"), only one could be timing: the 0.75 s card (`yQ6VOOd73MA` v3), where the agent read the next card. The collage phone screen (`x-wqMcYMNdg` v1) was a misread inside the right frame, and the slide bullets (`Unzc731iCUY` mixed) appeared 6 s after the speech, beyond the agent's range. At most 1 of 72.
- The hard set names moments the transcript never speaks about, so speech timing can't help there; `--scan` already reaches 36/36 dev and 12/12 holdout.
- Cost: a second model (1.28 GB 8-bit), a pass per 30 s piece (it accepts up to 5 min of speech), and only 11 of Qwen3-ASR's ~30 languages (Chinese, Cantonese, English, German, Spanish, French, Italian, Portuguese, Russian, Korean, Japanese), so the rest would keep interpolated times.
- **Decision: not built.** Revisit if someone needs word-level output, or if a new eval shows frame-timing misses.
- Outside support (2026-11-06): in [SleuthVLM](https://arxiv.org/abs/2611.06083)'s ablation (Table 5: Qwen3.8-27B as the agent, the same Qwen3-ASR plus this aligner), dropping word-level times cost 1.3 points on both Daily-Omni and LVOmniBench, with no change in turns. Most of the loss was on LVOmniBench's music and sound questions (6.6 and 6.1 points), which vidscribe doesn't cover (README "Limits").

## Readable transcript (S1-mini): not built

2026-11-05, a paper check with no runs: should vidscribe offer a "readable" output that cleans the raw transcript with [S1-mini](https://huggingface.co/mlx-community/S1-mini-MLX-8bit) by Superwhisper (8-bit MLX, 0.65 GB)? Its model card lists punctuation, truecasing and text normalization for dictation, in English only.

- The reader is an agent, which already reads the raw transcript well: speech questions scored 11-12/12 in every eval that had them (the one miss was agent noise on an unchanged transcript). It can tidy text itself when a person needs it.
- A rewrite risks changing words an agent quotes or matches against frames (`index.txt` maps each frame to what was being said), so the raw transcript would still have to be kept and output twice.
- Cost: a second model and pass, English only (the default handles ~30 languages), and a custom license (`other`, `s1-mini-license`) that requires crediting "S1-mini" by "Superwhisper".
- **Decision: not built.** Revisit if people (not agents) become the main readers.

## SKILL.md re-test

2026-11-05. Every earlier score came from eval prompts that paraphrase SKILL.md as of `55c8e8b`, which `0434746` rewrote. Do agents score the same given the current SKILL.md itself, with "view every frame" and "fetch more" left to the skill instead of the eval prompt? All 12 long videos were re-downloaded and transcribed with master `c5fbe83`; every reference answer was still on screen at its time. Method, prompts, decision rules and per-miss detail: `eval/README.md`, "SKILL.md re-test"; grades in `eval/grades.json` and `eval/hard/grades.json`.

| Run (SKILL.md wording) | Main /72 | Hard /36 | Hard agents viewing all ~40 frames | Hard sheets viewed |
|---|---|---|---|---|
| Eval prompt (recorded `at` / `scan`) | 69 | 36 | required | |
| `skill` (current) | 69 | 33 | 7 of 12, self-reported | |
| `skill_2` (current, repeat) | | 34 | 9 of 12 | 65 |
| `skill_old` (`55c8e8b`) | | 34 | 0 of 12 | 104 |
| `skill_done` (current + step 5 "Done when") | | 34 | 8 of 12 | 68 |
| **Bar (set before)** | ≥ 68 | ≥ 35 | | |

Counts from `skill_2` on come from the agents' `read` calls; self-reports proved approximate (one agent listed 4 `--at` frames that were never written).

- **Main passes; hard fails in all four runs** (33, 34, 34, 34). All misses are "unknown": searches that stopped early ("not found" after 5 or 8 sheets) or small-text misreads (S read as 5). They are spread over 8 questions, none missed by more than 2 of the 4 runs: a gap of about 2 in 36, not a step agents reliably skip.
- **The rewrite didn't cause the drop**: the old wording also scores 34. Both stop short of the eval prompt, which required a fetch or scan for every unanswered question.
- **The current step 3 ("View every frame") works**: 9 of 12 agents viewed every frame, against 0 of 12 under the old "view the frame images". In the first `skill` run, by their own count, 6 of 12 main agents viewed no frames and went straight from the transcript to `--at`. No miss traces to a skipped frame: none of the missed moments had one among the ~40.
- **Step 5 "Done when" not kept**: "answer from a full frame you viewed, or every plausible stretch scanned" scored 34, below the bar, and barely moved sheets viewed (68 vs 65), so step 5 went back to the earlier wording.
- **Not fixable by wording, as far as these runs show.** Closes [#8](https://github.com/SamuelZ12/vidscribe/issues/8). The scan holdout was not run: it was only needed to confirm a gain.
