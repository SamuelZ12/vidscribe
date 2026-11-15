# Long-video eval set

12 long YouTube videos (39-111 min), 6 questions each, used for the frame-selection and frames-on-demand tests in `docs/measurements.md`. Videos and transcripts are not in git (~4 GB); rebuild them from the IDs below.

| ID | Kind | Set |
|---|---|---|
| `LCEmiRjPEtQ` | Karpathy keynote | dev |
| `Unzc731iCUY` | MIT lecture | dev |
| `wYSncx9zLIU` | Google I/O keynote | dev |
| `H3KnMyojEQU` | Apple event | dev |
| `gDvwRpl9erE` | PyCon UK keynote | dev |
| `xAcTmDO6NTI` | MIT 6.100L lecture | dev |
| `ej5RsTtVvQE` | PyCon Austria talk | holdout |
| `JKbtWimlzAE` | Stanford CS25 lecture | holdout |
| `hF8swzNR1-o` | WWDC 2026 keynote | holdout |
| `yQ6VOOd73MA` | NOVA documentary | holdout |
| `x-wqMcYMNdg` | Jon Stewart podcast | holdout |
| `v9DuQ1C3xH8` | Food Network cooking | holdout |

Holdout clips must not be used to tune wording or code; run them once, after dev results are in.

## Files

- `questions/<ID>.json`: 6 questions with reference answers: `v1`-`v4` visual-only (one per quarter of the video), `mixed` (speech + screen), `speech` (transcript only). Fields: `qid`, `time_s`, `visible_s` (span the answer is on screen), `question`, `answer`, `notes`. Give answer agents only `qid` and `question`.
- `grades.json`: blind grades per clip, condition and question (`score` 1 / 0.5 / 0, `reason`; `skill` also keeps `answer` and `confidence`). Conditions: `master` (frames as of 4438e45), `scene_b` (content-score scene choice, not shipped), `at` (master frames + `--at`), `skill` (current SKILL.md, "SKILL.md re-test" below). Totals /72: 37.5, 36.5, 69, 69.
- `sheet.py VIDEO OUT.jpg t1 t2 ...`: contact sheet of labelled 320 px frames (`uv run --with pillow eval/sheet.py ...`); used to write questions.

## Rebuild

```
W=/tmp/vseval; mkdir -p $W/src $W/tr
for id in LCEmiRjPEtQ Unzc731iCUY wYSncx9zLIU H3KnMyojEQU gDvwRpl9erE xAcTmDO6NTI ej5RsTtVvQE JKbtWimlzAE hF8swzNR1-o yQ6VOOd73MA x-wqMcYMNdg v9DuQ1C3xH8; do
  yt-dlp -q --no-warnings -f "bv*[height<=720]+ba/b[height<=720]/b" --merge-output-format mp4 -o "$W/src/%(id)s.%(ext)s" "https://www.youtube.com/watch?v=$id"
  VIDSCRIBE_OUTDIR=$W/tr VIDSCRIBE_FRAMES_DIR=$W/frames vidscribe $W/src/$id.mp4 -f srt   # 5-10 min per video
done
```

Then for each clip and condition, build an answer folder with `transcript.srt`, `frames/` (`index.txt`, the jpgs, `video.mp4` for `--at`) and `questions.json` (qid + question only). Label folders neutrally (`<ID>_x`/`_y`) and keep the condition map out of the agents' reach. A re-downloaded video may differ from the original (re-encodes, edits); spot-check a few `time_s` before trusting old grades.

## Prompts (verbatim)

Answer agents ran as generic `task` subagents with the context below and the task `FOLDER = <ID>_<label>`, about 6-10 at a time. Telling them to view every frame matters: without it some skipped frames.

### Answer agent: master / scene_b

Lost when the eval was recovered from session logs. The hard set's `frames` prompt ("Hard set", "Prompts") reconstructs it: the `at` prompt below minus "Getting more frames" and the `--at` rule.

### Answer agent: `at`

```
# Goal
You are testing how well an AI agent can answer questions about a video using a transcript, a set of still frames from it, and a command that extracts more frames on demand. Answer honestly from your folder; a wrong guess is worse than "unknown".

# Your folder: /tmp/vseval2/ans/<FOLDER>/
- transcript.srt: the full timestamped transcript.
- frames/index.txt: one line per frame: time, frame file name, spoken span, text spoken around that time.
- frames/*.jpg: the frames (about 40).
- frames/video.mp4: the video. Do not open it directly; use the command below.
- questions.json: 6 questions.

# Getting more frames
Long videos keep at most 40 frames, so a moment you need often has none. Find it in the transcript (srt times), then run `vidscribe /tmp/vseval2/ans/<FOLDER>/frames --at 8:14` for an exact second or `--at 7:50-8:50` (4 frames) when unsure, and view what it prints. Several times or ranges fit in one call (`--at 8:14,31:00-31:40`). Ask for the moments you need, not the whole video.

# Rules
- Use ONLY files inside your folder and the vidscribe --at command above. Do not open anything else under /tmp/vseval2, do not search the web, do not run ffmpeg or any other tool on the video.
- First read index.txt and the transcript. Then view EVERY frame image in frames/ with the read tool, one by one; do not skip any, even if there are many. Keep a count.
- Then, for any question the frames and transcript don't answer, get more frames as described above and view every frame the command prints.
- Answer each question. If the frames and transcript do not show the answer, answer exactly "unknown". Do not guess from general knowledge.

# Output
Write /tmp/vseval2/ans/<FOLDER>/answers.json: a JSON list of {"qid", "question", "answer", "frame": "<file name you used, or null>", "confidence": "high"|"low"}.
In your final message, state how many of the original frames you viewed out of how many exist, and how many extra frames you extracted and viewed.
```

### Grader (`completion()`, blind: sees only question, reference, one candidate)

```python
GRADE_SYS = "You grade answers to questions about a video. You get a question, the reference answer, and one candidate answer. Score: 1 = correct (matches the reference in substance), 0.5 = partially correct (some key part right, some missing or wrong), 0 = wrong, or 'unknown'. Return JSON."
schema = {"type": "object", "properties": {"score": {"type": "number", "enum": [0, 0.5, 1]}, "reason": {"type": "string"}}, "required": ["score", "reason"]}
# one call per question, model "default", user message:
f"Question: {q['question']}\nReference answer: {q['answer']}\nCandidate answer: {answer or 'unknown'}"
```

### Question writer (one agent per video; `sheet_*.jpg` = dense contact sheets from `sheet.py`, every ~20-60 s)

```
# Goal
Build an evaluation set for a tool that gives AI agents a video's transcript plus a limited set of still frames. You write the questions and reference answers for ONE video. You will never see the tool's frames; you get a dense, evenly spaced set of frames instead.

# Inputs (per video ID)
- Dense contact sheets: /tmp/vseval2/q/<ID>/sheet_*.jpg. Each tile is labeled `#k m:ss.s` (video time). Frames are evenly spaced (every ~20-60 s). View EVERY sheet (use the read tool on each jpg).
- Transcript with timestamps: /tmp/vseval2/master/tr/<ID>.srt (cues are ~30 s chunks).
- The video itself: /tmp/vseval2/src/<ID>.mp4. You MAY extract extra frames to check details: `ffmpeg -nostdin -loglevel error -y -ss <seconds> -i /tmp/vseval2/src/<ID>.mp4 -frames:v 1 -vf scale=-2:720 /tmp/vseval2/q/<ID>/check_<seconds>.jpg` then read it. Delete your check_*.jpg files when done.

# Questions to write: exactly 6
- v1..v4: VISUAL-ONLY. The answer is visible on screen and is NOT said in the transcript near that moment (check the transcript). One question from each quarter of the video (v1 from 0-25%, v2 25-50%, v3 50-75%, v4 75-100% of duration). Ask about whatever a viewer might plausibly want to know about what is shown at that point: on-screen text, numbers on a slide or chart, a UI or code detail, an object, product, setting, what someone wears or holds, etc. Vary the kinds; do not make them all about slides. The visual must be on screen for at least ~3 seconds.
- mixed: needs BOTH what is said and what is shown (e.g. "When the speaker says X, what is shown on screen?").
- speech: answerable from the transcript alone.
- Each question names its moment only through speech or context the answering agent can find (e.g. "When the speaker introduces Y, ..."). Do NOT put timestamps in the question text.
- Answers: short, unambiguous, checkable (a word, number, short phrase). Avoid questions whose answer could be guessed from general knowledge or from the title.

# Output
Write /tmp/vseval2/q/<ID>/questions.json: a JSON list of 6 objects:
{"qid": "v1"|"v2"|"v3"|"v4"|"mixed"|"speech", "time_s": <video second where the answer is visible/said>, "visible_s": [<start>, <end>] (approximate span in seconds the visual answer stays on screen; for speech use the cue span), "question": "...", "answer": "...", "notes": "why it is visual-only / how you verified"}
Do not modify anything else under /tmp/vseval2.
```

## Noise

Speech questions move by about ±1 per 12 between runs from agent noise alone, even with identical transcripts. Compare conditions within a run when the expected difference is small.

## Hard set

The 72 questions above all name their moment through speech ("when the speaker says ..."), which is the case `--at` is built for (`docs/measurements.md`, "Frames on demand", caveat). The hard set asks about moments the transcript never points to: the agent must find the moment from what is on screen. Its result decides whether an OCR timeline is built.

Run 2026-11-05: `frames` 11/36, `at` 31/36; OCR not built (`docs/measurements.md`, "Hard eval"). Files: `hard/questions/<ID>.json` (same fields as above plus `anchor`, `anchor_s`), `hard/grades.json` (per clip, condition and question: `score`, `answer`, `confidence`, `reason`; `miss` = not found / misread on misses; `extra_frames` on `at` h1), `hard/transcript_only.json` (validation check 2 on the final 36: `answer`, `score`), `hard/check_transcript.py` (validation check 1).

Scan probe (`docs/measurements.md`, "Scan probe"): `scan_probe.py VIDEO START END OUTDIR [--method scene|even5|fill10] [--grid 4]` builds the contact sheets and prints each sheet's tile times; `hard/scan_probe.json` has the 5 windows and the 20 agents' answers (`located` = a reported tile lies inside `visible_s`). The probe used the 5 `at` misses, so the whole hard set (both splits) is now dev data.

Blind folder maps (per clip, condition → folder label `x`/`y`; kept out of the answer agents' reach during runs): `hard/labels.json` for the `frames`/`at` run, `hard/labels_scan.json` for the scan-eval holdout (`at`/`scan`). Grades are already stored by condition; these record how the folders were unblinded.

### Questions

- 3 per video, 36 total, `qid` `h1`-`h3`: one from each third of the video.
- Each question names its moment only by what is on screen: a slide title, a caption, a scene, an object, a UI ("On the slide titled X, ...", "In the shot of the kitchen with the red mixer, ..."). No speech reference.
- The answer is on screen for at least ~3 s and is short and checkable. It must not be guessable from general knowledge or the title. Vary the kinds; do not make them all slides.
- Fields: those of the main set plus `anchor` (the on-screen cue the question names) and `anchor_s` ([start, end] it is on screen).
- Same videos and dev/holdout split as above. The question-writer prompt (based on the one above: new paths, sheet description, question rules and output schema) is tuned on a pilot of 2 dev videos (`LCEmiRjPEtQ`, `H3KnMyojEQU`), then frozen.

### Validation (a failing question is replaced, then re-checked)

1. Transcript check (script, reviewed by hand): the answer is not said anywhere in the transcript, and the anchor is not said within 60 s of `anchor_s`.
2. Transcript-only agent: an agent given only `transcript.srt` answers every question, guessing from general knowledge when the transcript has nothing ("unknown" not allowed). Any question the grader scores 0.5 or 1 is replaced.

Questions are committed under `eval/hard/questions/<ID>.json` before any answer run.

Pilot (`LCEmiRjPEtQ`, `H3KnMyojEQU`): 1 of 6 failed check 2 (a famous compute cluster, guessed from general knowledge) and one asked for two facts, with the "accept either" rule only in the notes the grader never sees. The two rules marked *(pilot)* in the writer prompt come from these; pilot questions were fixed to meet them.

Full set: of the 30 first-round questions on the other 10 videos, 2 failed check 1 on hand review (the speaker describes the moment: "Sundar used Google Antigravity ... to fix a bug" over the code-review screen; "Python Tutor" named over its web page) and 4 failed check 2 (IAP 2018 on the famous MIT "How to Speak" lecture, Piazza for an MIT course, Anil Seth's University of Sussex, an editable-install `.pth` file at 0.5). All 6 replacements passed both checks. One position hint ("In the opening montage") was removed from a replacement by hand. Final transcript-only score on all 36: 0.

### Runs

- Videos and transcripts rebuilt per "Rebuild" with master `b3fa881` (`/tmp/vseval`). Questions are written on these downloads, so there is no re-download drift.
- Conditions, blind folder labels as above:
  - `frames`: the master frame folder (`index.txt` + up to 40 frames), no `--at`.
  - `at`: the same plus `vidscribe <frames-dir> --at`.
- Answer prompts: `at` as above with the question count changed. `frames` uses the `at` prompt minus "Getting more frames" and the `--at` rule, a reconstruction of the lost `master` prompt.
- Dev clips first, then holdout once. Same grader. Leakage check per agent (paths outside its folder, `ffmpeg`).
- Per miss, record whether any frame the agent viewed (the 40 or `--at`) falls inside `anchor_s`: **not found** if none did, **misread** otherwise.
- Results go in `eval/hard/grades.json` and `docs/measurements.md`.

### Decision rule (set before the run)

Build the OCR timeline if `at` scores below 27/36 (75%) **and** at least half its misses are "not found". OCR helps an agent find a moment, not read it; if misses are mostly misreads, or `at` is at 75% or above, OCR is not built and the result is recorded.

### Prompts (verbatim)

Contact sheets: one tile every 20 s (first at 10 s), 36 per sheet, from `sheet.py`.

Question writer (one fresh `task` subagent per video, task `ID = <ID>`; a failed question goes back to the same writer with the reason and a request for one replacement):

```
# Goal
Write hard evaluation questions for a tool that gives AI agents a video's transcript, ~40 still frames, and a command to fetch more frames at chosen times. These questions test whether an agent can find and read a moment that the transcript never points to. Write 3 questions with reference answers for ONE video. You will never see the tool's frames.

# Inputs
- Contact sheets: /tmp/vseval/q/<ID>/sheet_*.jpg. One tile every 20 s, labeled `#k m:ss.s` (video time). View EVERY sheet with the read tool.
- Transcript with timestamps: /tmp/vseval/tr/<ID>.srt
- The video: /tmp/vseval/src/<ID>.mp4. To check details, extract frames: `ffmpeg -nostdin -loglevel error -y -ss <seconds> -i /tmp/vseval/src/<ID>.mp4 -frames:v 1 -vf scale=-2:720 /tmp/vseval/q/<ID>/check_<seconds>.jpg`, then read the file. Delete your check_*.jpg files when done.

# Questions: exactly 3
- h1 from the first third of the video, h2 from the middle third, h3 from the last third.
- The ANCHOR: each question names its moment ONLY by something visible on screen (a slide title, a caption, a scene, an object, a UI screen). Examples: "On the slide titled X, ...", "In the shot of the kitchen with the red mixer, ...". No reference to speech, no timestamps, no position hints like "near the end".
- The anchor must match exactly one moment. Check the sheets: if the same slide or scene appears again elsewhere with a different answer, pick another.
- The anchor must NOT be spoken within 60 s of when it is on screen. Search the transcript for its key words.
- The ANSWER: visible on screen for at least ~3 s; NOT spoken anywhere in the transcript (search for it, including numbers written as words); short and checkable (a word, number, short phrase); not guessable from general knowledge, the video title, or the anchor itself.
- Before keeping a question, ask: could someone who knows this field answer it without the video? If yes, pick another.
- Ask for one fact only.
- Vary the kinds. If the video has non-slide shots (people, products, demos, places, name captions), use at least one. Prefer things a viewer might plausibly ask about.

# Output
Write /tmp/vseval/q/<ID>/questions.json: a JSON list of 3 objects:
{"qid": "h1"|"h2"|"h3", "time_s": <second the answer is clearly visible>, "visible_s": [<start>, <end>] (span the answer is on screen), "anchor": "<the on-screen cue the question names>", "anchor_s": [<start>, <end>] (span the anchor is on screen), "question": "...", "answer": "...", "notes": "transcript words you searched and why neither anchor nor answer is spoken"}
Do not modify anything else under /tmp/vseval.
```

The two lines "Before keeping a question ..." and "Ask for one fact only." are the *(pilot)* additions.

Transcript-only agent (fresh `task` subagent, task `ID = <ID>`; folder holds `transcript.srt` and `questions.json` with `qid` + `question` only):

```
# Goal
You are checking whether questions about a video can be answered WITHOUT seeing it. You get only the video's transcript. For each question, find the answer in the transcript if you can; if the transcript doesn't give it, give your best guess anyway (from general knowledge or reasoning). Never answer "unknown".

# Your folder: /tmp/vseval/tonly/<ID>/
- transcript.srt: the full timestamped transcript.
- questions.json: the questions.

# Rules
- Use ONLY the two files in your folder. Do not open anything else under /tmp/vseval, do not search the web, do not run ffmpeg or open any video or image.

# Output
Write /tmp/vseval/tonly/<ID>/answers.json: a JSON list of {"qid", "answer", "source": "transcript"|"guess", "cue": "<srt time if from transcript, else null>"}.
```

Answer agents (fresh `task` subagents, task `FOLDER = <ID>_<label>`; labels `x`/`y` assigned at random per clip). `at` is the `at` prompt above with `/tmp/vseval2` → `/tmp/vseval` and 6 → 3 questions:

```
# Goal
You are testing how well an AI agent can answer questions about a video using a transcript, a set of still frames from it, and a command that extracts more frames on demand. Answer honestly from your folder; a wrong guess is worse than "unknown".

# Your folder: /tmp/vseval/ans/<FOLDER>/
- transcript.srt: the full timestamped transcript.
- frames/index.txt: one line per frame: time, frame file name, spoken span, text spoken around that time.
- frames/*.jpg: the frames (about 40).
- frames/video.mp4: the video. Do not open it directly; use the command below.
- questions.json: 3 questions.

# Getting more frames
Long videos keep at most 40 frames, so a moment you need often has none. Find it in the transcript (srt times), then run `vidscribe /tmp/vseval/ans/<FOLDER>/frames --at 8:14` for an exact second or `--at 7:50-8:50` (4 frames) when unsure, and view what it prints. Several times or ranges fit in one call (`--at 8:14,31:00-31:40`). Ask for the moments you need, not the whole video.

# Rules
- Use ONLY files inside your folder and the vidscribe --at command above. Do not open anything else under /tmp/vseval, do not search the web, do not run ffmpeg or any other tool on the video.
- First read index.txt and the transcript. Then view EVERY frame image in frames/ with the read tool, one by one; do not skip any, even if there are many. Keep a count.
- Then, for any question the frames and transcript don't answer, get more frames as described above and view every frame the command prints.
- Answer each question. If the frames and transcript do not show the answer, answer exactly "unknown". Do not guess from general knowledge.

# Output
Write /tmp/vseval/ans/<FOLDER>/answers.json: a JSON list of {"qid", "question", "answer", "frame": "<file name you used, or null>", "confidence": "high"|"low"}.
In your final message, state how many of the original frames you viewed out of how many exist, and how many extra frames you extracted and viewed.
```

`frames` (reconstructed: the `at` prompt without `video.mp4`, "Getting more frames" and the `--at` rules; the folder has no `video.mp4`):

```
# Goal
You are testing how well an AI agent can answer questions about a video using a transcript and a set of still frames from it. Answer honestly from your folder; a wrong guess is worse than "unknown".

# Your folder: /tmp/vseval/ans/<FOLDER>/
- transcript.srt: the full timestamped transcript.
- frames/index.txt: one line per frame: time, frame file name, spoken span, text spoken around that time.
- frames/*.jpg: the frames (about 40).
- questions.json: 3 questions.

# Rules
- Use ONLY files inside your folder. Do not open anything else under /tmp/vseval, do not search the web, do not run ffmpeg or any other tool on the video.
- First read index.txt and the transcript. Then view EVERY frame image in frames/ with the read tool, one by one; do not skip any, even if there are many. Keep a count.
- Answer each question. If the frames and transcript do not show the answer, answer exactly "unknown". Do not guess from general knowledge.

# Output
Write /tmp/vseval/ans/<FOLDER>/answers.json: a JSON list of {"qid", "question", "answer", "frame": "<file name you used, or null>", "confidence": "high"|"low"}.
In your final message, state how many of the frames you viewed out of how many exist.
```

## Scan eval (`--scan`)

Condition `scan`: the `frames` folder plus `video.mp4`, with `--at` and `--scan`. Folders `<ID>_z`, built fresh from the master frame folders (`/tmp/vseval/frames/<ID>`: the same 39-40 frames the `at` run had). Graded with the same grader into `hard/grades.json` under `scan`; `h1` also holds the clip's cost from the agent transcript: `extra_frames` (`at_*.jpg` viewed), `sheets` (`scan_*.jpg` viewed), `at_calls`, `scan_calls`.

- Dev: all 36 hard-set questions (the probe made both splits dev), `scan` only, compared with the existing `at` grades. The prompt below ran unchanged; it was not tuned.
- Holdout: 4 new videos, questions from the frozen hard-set writer prompt and both validation checks, committed before any answer run; `at` and `scan` both run once, labels `x`/`y` at random per clip.

Run 2026-11-05: dev `scan` 36/36 (`at` 31); holdout `at` 12/12, `scan` 12/12; shipped (`docs/measurements.md`, "Scan eval"). Holdout validation: 5 of 12 first-round questions failed check 1 (speech described the moment), 1 replacement failed check 2 (guessed from general knowledge); all final 12 scored 0 transcript-only (`hard/transcript_only.json`).

| ID | Kind |
|---|---|
| `Nul7mPL7Nt4` | Samsung Galaxy Unpacked keynote (83 min) |
| `FFMm454fxNA` | Microsoft Build 2026 keynote (143 min) |
| `8qVbE9DHkEk` | DW documentary (51 min) |
| `114i2Kz-LZA` | Stanford CME295 lecture (104 min) |

Answer agent `scan` (the `at` prompt plus the scan section, which mirrors SKILL.md step 6 as of `b103a4c`):

```
# Goal
You are testing how well an AI agent can answer questions about a video using a transcript, a set of still frames from it, and commands that extract more frames and contact sheets on demand. Answer honestly from your folder; a wrong guess is worse than "unknown".

# Your folder: /tmp/vseval/ans/<FOLDER>/
- transcript.srt: the full timestamped transcript.
- frames/index.txt: one line per frame: time, frame file name, spoken span, text spoken around that time.
- frames/*.jpg: the frames (about 40).
- frames/video.mp4: the video. Do not open it directly; use the commands below.
- questions.json: 3 questions.

# Getting more frames
Long videos keep at most 40 frames, so a moment you need often has none. Find it in the transcript (srt times), then run `vidscribe /tmp/vseval/ans/<FOLDER>/frames --at 8:14` for an exact second or `--at 7:50-8:50` (4 frames) when unsure, and view what it prints. Several times or ranges fit in one call (`--at 8:14,31:00-31:40`). Ask for the moments you need, not the whole video.

# Scanning when nothing points to the moment
If a question is about something on screen that the transcript never leads to, or `--at` didn't find it, run `vidscribe /tmp/vseval/ans/<FOLDER>/frames --scan 50:00-60:00` on the stretch where it most likely is. It prints 4x4 contact sheets (a tile at every scene change, at most 10 s apart) with each tile's time. View every sheet, pick the tile, then `--at` its time and answer from that frame, never from the tile (small text misreads). 10 min is 5-8 sheets, each about the cost of one frame; widen the range step by step, and use `--scan all` only as a last resort.

# Rules
- Use ONLY files inside your folder and the vidscribe --at and --scan commands above. Do not open anything else under /tmp/vseval, do not search the web, do not run ffmpeg or any other tool on the video.
- First read index.txt and the transcript. Then view EVERY frame image in frames/ with the read tool, one by one; do not skip any, even if there are many. Keep a count.
- Then, for any question the frames and transcript don't answer, get more frames or scan as described above and view every frame and sheet the commands print.
- Answer each question. If the frames and transcript do not show the answer, answer exactly "unknown". Do not guess from general knowledge.

# Output
Write /tmp/vseval/ans/<FOLDER>/answers.json: a JSON list of {"qid", "question", "answer", "frame": "<file name you used, or null>", "confidence": "high"|"low"}.
In your final message, state how many of the original frames you viewed out of how many exist, how many extra frames you extracted and viewed, and how many scan sheets you viewed.
```

## SKILL.md re-test (`skill`)

Every score above came from prompts that paraphrase `skill/SKILL.md` as of `55c8e8b`/`b103a4c`; `0434746` rewrote it. Condition `skill` gives answer agents the current SKILL.md instead, so the wording itself is what is tested ([#1](https://github.com/SamuelZ12/vidscribe/issues/1)).

- Videos and transcripts rebuilt per "Rebuild" with master `c5fbe83` (`/tmp/vseval`). The main set's reference times were written on older downloads: before answering, every visual, mixed and hard question's `time_s` is checked on a full frame of the new download (one checker agent per video, searching ±60 s if needed), and a question whose answer is no longer on screen there is dropped from both sides of the comparison.
- All 12 videos, both sets: 72 main questions (6 per agent) compared with `at` (69/72; that run had no `--scan`), 36 hard questions (3 per agent) compared with `scan` (36/36). One condition, so no folder labels; the grader is blind as before. Nothing is tuned: the prompt runs once, unchanged.
- Folders `<ID>_main` and `<ID>_hard`: `transcript.srt`, `frames/` (the run's folder: `index.txt`, frames, `video.mp4`), `questions.json` (`qid` + `question`). Same grader. Leakage check per agent (paths outside its folder, `ffmpeg`).
- **Pass bar (set before the run):** main ≥ 68/72 and hard ≥ 35/36, i.e. at most one point below the recorded scores. Below that, each miss is checked against the agent transcript (frame not viewed, moment not fetched, misread) to tell wording from noise; the result is recorded either way.

Run 2026-11-05: no question dropped (all on screen; one slide a few seconds later, inside `visible_s`). Main 69/72 (passes), hard 33/36 (fails by 2; all 3 misses "unknown", "not found"). Most main agents skipped "view every frame"; see `docs/measurements.md`, "SKILL.md re-test". Hard-set `skill` misses carry `miss` as above; cost fields were not recorded (agents' self-counts proved approximate).

Answer agent `skill` (`<SKILL>` = the body of `skill/SKILL.md` at `c5fbe83`, from `# vidscribe` to the end; `<N>` = 6 or 3). Compared with the prompts above, the skill replaces "Getting more frames", "Scanning ..." and the rules that repeat its steps (view every frame, fetch more); the eval's own rules (folder only, "unknown") and output stay:

```
# Goal
You are testing how well an AI agent can answer questions about a video using the vidscribe skill below. vidscribe has already been run on the video (step 1 is done) and its output is in your folder. Answer honestly from your folder; a wrong guess is worse than "unknown".

# Your folder: /tmp/vseval/ans/<FOLDER>/
- transcript.srt: the full timestamped transcript.
- frames/: the run's frames folder (`<dir>` in the skill): index.txt, the frames (about 40), and video.mp4. Do not open video.mp4 directly; use the skill's vidscribe commands.
- questions.json: <N> questions.

# The vidscribe skill
<SKILL>

# Rules
- Use ONLY files inside your folder and the `vidscribe /tmp/vseval/ans/<FOLDER>/frames --at` and `--scan` commands. Do not open anything else under /tmp/vseval, do not search the web, do not run ffmpeg or any other tool on the video.
- Answer each question. If the frames and transcript do not show the answer, answer exactly "unknown". Do not guess from general knowledge.

# Output
Write /tmp/vseval/ans/<FOLDER>/answers.json: a JSON list of {"qid", "question", "answer", "frame": "<file name you used, or null>", "confidence": "high"|"low"}.
In your final message, state how many of the original frames you viewed out of how many exist, how many extra frames you extracted and viewed, and how many scan sheets you viewed.
```

### Control: old wording and a repeat (`skill_old`, `skill_2`)

The hard set failed by 2 ([#8](https://github.com/SamuelZ12/vidscribe/issues/8)), but 2 of the 3 misses came from one agent, and there was no control. Before any rewording, this run asks whether the rewrite caused the drop.

- Hard set only (36 questions, 12 agents per condition), same folders, transcripts, frames, prompt and grader as `skill`. The main set passed and is not re-run.
- `skill_old`: `<SKILL>` = the body of `skill/SKILL.md` at `55c8e8b` (the wording the recorded prompts paraphrased). `skill_2`: the `skill` prompt again, SKILL.md at `c5fbe83` (unchanged at the time of the run).
- Fresh folders `<ID>_p` and `<ID>_q` built from `tr/` and `frames/`; which label gets which condition is random per clip, recorded in `hard/labels_skill2.json` after grading. Each wave of 12 agents mixes both conditions; each clip's two agents run in different waves. Grader blind as before.
- Cost per agent, from files on disk (agents' self-counts proved approximate): `at_files` (`at_*.jpg` written), `scan_files` (`scan_*.jpg` written). Each miss: **not found** / **misread** from the agent transcript, as above.
- **Decision rule (set before the run)**, with `skill` = 33:

| `skill_old` | `skill_2` | Reading | Next |
|---|---|---|---|
| ≥ 35 | ≤ 33 | the rewrite caused the drop | reword steps 4-5, re-run the hard set, then ask before the holdout |
| ≥ 35 | ≥ 35 | the first 33 was agent noise | record, close #8 |
| < 35 | ≥ 35 | the first 33 was agent noise | record, close #8 |
| < 35 | < 35 | neither wording gets agents to search as the scan prompt did | add a "Done when" to step 5, re-run the hard set once |
| ≥ 35 | 33.5-34.5 | unclear | compare searches per miss in the transcripts; record before deciding |

Run 2026-11-05: `skill_old` 34/36, `skill_2` 34/36 (row 4). Misses: `skill_2` `hF8swzNR1-o` h1, h2 (not found; 5 sheets, then stopped), `skill_old` `v9DuQ1C3xH8` h2 (misread: "unknown" with a viewed frame inside the span), `skill_old` `wYSncx9zLIU` h3 (not found after 25 sheets). Costs and viewed counts (counted from the agent transcripts' `read` calls: `orig_viewed`, `at_viewed`, `sheets_viewed`) are on each clip's h1. No agent touched a path outside its folder or ran ffmpeg; the earlier runs' `answers.json` files were last read before this run began. Four agents tried Python (every call failed); one cropped a frame with `sips` (`Unzc731iCUY` `skill_old`, h1, graded correct). The rules cover the video, not frames.

### Step 5 "Done when" (`skill_done`)

Row 4's next step. SKILL.md step 5 gains a "Done when": the answer comes from a full frame you viewed, or every stretch where it could plausibly appear was scanned without finding it. Condition `skill_done`: the `skill` prompt with `<SKILL>` = the body of `skill/SKILL.md` at the commit that adds this section; hard set only, one agent per clip, folders `<ID>_d` built fresh from `tr/` and `frames/`; same grader, cost fields and miss labels as the control. The main set is not re-run: its questions name their moment in speech, which step 4 handles.

- **Bar (set before the run):** ≥ 35/36 keeps the wording, and the 4-video scan holdout is next (it needs downloads and ~1 h of transcription, so it waits for approval). Below 35, step 5 goes back to the `c5fbe83` wording and #8 is recorded as not fixed by wording.

Run 2026-11-05: 34/36, below the bar; step 5 reverted. Misses: `hF8swzNR1-o` h1 (not found after 8 sheets; also missed by `skill_2`), `xAcTmDO6NTI` h1 (misread: "6.5061" for "6.S061" on a viewed `--at` frame). Sheets viewed 68 (`skill_2` 65), 8 of 12 agents viewed every frame.

## Table re-run (`table`)

The README table mixed runs: each row measured only some conditions, on different downloads and code (clips 2026-11-04 at `fbddc2b`, main set on downloads since deleted, hard set at `b3fa881`). This run fills every cell in one go so each row is one run: same downloads, same code, same prompts, same grader.

- Code: master `c6aa0a6`; `bin/vidscribe` is unchanged since `c5fbe83`, so the `/tmp/vseval` rebuild (videos, `tr/`, `frames/`) is master output and is reused for the 12 long videos.
- Sets: `clips` (12 clips, 48 questions, `clips/questions/<ID>.json`), `main` (72), `hard` (36). The clip questions were never committed; they were recovered verbatim from the 2026-11-04 question writers' session logs (fields `qid`, `kind`, `question`, `answer`, `time`). Three clips (`LCEmiRjPEtQ`, `Unzc731iCUY`, `wYSncx9zLIU`) are also in the long set and reuse its download; the other 9 are downloaded and transcribed fresh per "Rebuild" into `/tmp/vstable`.
- Time check (clips only; the main and hard sets were checked on these downloads in the `skill` re-test): one checker agent per clip confirms each visual and mixed answer on a full frame of the new download (±60 s of `time`). A question whose answer is no longer on screen is dropped from every condition and the denominator shown.
- Conditions, all four on every set: `transcript` (`transcript.srt` + `questions.json` only), `frames` (+ `frames/` without `video.mp4`), `at`, `scan`. Prompts: `frames`, `at` and `scan` as above with `/tmp/vseval` → `/tmp/vstable` and the set's question count; `transcript` below. All allow "unknown"; the hard set's earlier 0/36 was the forced-guess validation check, so it is re-measured here under the same rules as the other rows.
- Folders `/tmp/vstable/ans/<set>_<ID>_<label>`, labels `a`-`d` assigned at random per clip and set, map kept outside the folders and committed as `table/labels.json` after grading. Agents run in waves of up to 32 mixing sets and conditions. Same grader. Leakage check per agent (paths outside its folder, `ffmpeg`).
- **Reporting rule (set before the run):** every README cell is replaced by this run's number, whatever it is, and the README prose is rewritten to match. Earlier runs stay in `docs/measurements.md`. No design decision depends on the result.

Answer agent `transcript`:

```
# Goal
You are testing how well an AI agent can answer questions about a video using only its transcript. Answer honestly from your folder; a wrong guess is worse than "unknown".

# Your folder: /tmp/vstable/ans/<FOLDER>/
- transcript.srt: the full timestamped transcript.
- questions.json: <N> questions.

# Rules
- Use ONLY the files inside your folder. Do not open anything else under /tmp/vstable or /tmp/vseval, do not search the web, do not open any video or image.
- Answer each question. If the transcript does not give the answer, answer exactly "unknown". Do not guess from general knowledge.

# Output
Write /tmp/vstable/ans/<FOLDER>/answers.json: a JSON list of {"qid", "question", "answer", "frame": null, "confidence": "high"|"low"}.
```

Run 2026-11-08: `clips` 13 / 34 / 47 / 47 of 48, `main` 12.5 / 35.5 / 68 / 69.5 of 72, `hard` 0 / 9 / 31 / 35 of 36 (`transcript` / `frames` / `at` / `scan`; `docs/measurements.md`, "Table re-run"). All 48 clip questions passed the time check, so no denominator changed (`table/time_check.json`). Files: `table/grades.json` (set → clip → condition → qid: `score`, `answer`, `confidence`, `reason`), `table/labels.json`, `table/cost.json` (per agent: `orig` frames and `orig_viewed`, `at_files`/`at_viewed`, `scan_files`/`sheets_viewed`, counted from files on disk and the agents' `read` calls).

Deviations from the plan above, none touching prompts' rules or the grader:
- The `frames`, `at` and `scan` prompts say "the frames (N)" with the folder's real count instead of "(about 40)", since the short clips have 10-39.
- The first launch used a pool that reuses one agent for several folders; it was cancelled after ~10 s (one `answers.json`, some `--at` frames), every folder was rebuilt, and all 192 agents then ran fresh, one folder each.
- Waves were not mixed across sets: `main` and `hard` (96 agents) ran first while the 9 clips downloaded, then `clips` in three waves as their time checks passed.
- No agent touched a path outside its folder or ran `ffmpeg`. Seven cropped or tiled their own frames with `sips` or PIL (the rules cover the video, not frames); one wrote its crops to `/tmp` (`hard` `x-wqMcYMNdg` `at`, deleted after the run).

## Overview sheets (`overview`)

Tests the branch `overview-sheets` (`fdb5961`: overview sheets replace the default frames, `--at A-B/N`, new `skill/SKILL.md`) against master `28966e5`, with bars set before the run (`SPEC.md`, "Eval"). Result: `docs/measurements.md`, "Overview sheets against the current default frames".

- Sets: `clips` (48 questions), `main` (72), `hard` (36), as in "Table re-run".
- Arms, one fresh agent per video, set and arm (108 agents): `transcript` (the `transcript` prompt above); `current` (the `skill` prompt above with master's SKILL.md, on the frames master's script made); `vidscribe` (the same prompt with the branch's SKILL.md, on the branch script's output).
- Agents: Codex CLI 0.169.0, one `codex exec --ignore-user-config -m gpt-6.1-sol -c model_reasoning_effort="medium" -s workspace-write -C <folder> --skip-git-repo-check --json` per folder (no network, writes only in the folder and `/tmp`). Earlier runs used Claude `task` subagents, so each bar compares two arms of this run, not a recorded score.
- **Which script the agents ran** (found after the run): the harness put a copy of the arm's script first on each agent's `PATH`, but Codex runs every command as `/bin/zsh -lc`, and the login shell puts `~/.local/bin` in front again. All 243 `--at` and `--scan` commands, in both arms, therefore ran the installed script, which was master (`28966e5`, the same file as the `current` arm's copy). For the `vidscribe` arm that leaves the branch's sheets, `index.txt` and SKILL.md, with master's `--at` and `--scan`. Without a count both scripts give the same output; the 6 calls with a count (`--at A-B/N`) failed with `bad time`. A re-run must make the login shell find the arm's script, and check it with `which vidscribe` inside an agent.
- Re-check after that finding: the six `vidscribe` folders whose count call had failed (`clips` `ive5H8hCBFs` and `up1xuwn_euk`, `hard` `H3KnMyojEQU`, `v9DuQ1C3xH8` and `wYSncx9zLIU`, `main` `yQ6VOOd73MA`) were rebuilt under `/tmp/vsov/ans6` and given to six fresh agents with the same prompt. `ZDOTDIR` pointed at an empty folder, so the login shell skipped the owner's profile and kept the arm's folder first on `PATH`; `vidscribe` there was a wrapper that logged each call and ran the branch script at `8a165f2`. Earlier answers, logs and keys had mode 000 meanwhile. The wrapper logged all 33 calls; no leak flags; answers not graded. Per agent: `overview/recheck.json`.
- Bars, the same on every set: `vidscribe` at most 2 points below `current`; wrong answers that are not "unknown" at most `current` + 1.
- Rebuild: all 21 videos downloaded per "Rebuild" into `/tmp/vsov/src`; the branch script run on all 21 (`new/`), master's on all 21 (`cur/`), each as `vidscribe <video> -f srt`. The transcripts of the two runs are byte-identical for every video.
- Time check: one Codex agent per video with the prompt below, on every visual, mixed and hard question (132). 130 "ok", 2 "gone", both overruled: `H3KnMyojEQU` and `x-wqMcYMNdg` `mixed`, whose answers are spoken while the on-screen part (the presenter in grassy hills at 25:39, the producer in the striped top at 81:18) is there; the prompt asked whether the answer is on screen, which does not fit `mixed` questions. No question dropped (`overview/time_check.json`). The prompt offers `--at A-B/N`, which failed for the same reason as above: 6 calls by 3 checkers (`H3KnMyojEQU`, `x-wqMcYMNdg`, `up1xuwn_euk`).
- Folders `/tmp/vsov/ans/<set>_<ID>_<label>`, labels `a`-`c` shuffled per video and set (`overview/labels.json`, with the seed). While agents ran, the labels, the time-check folders and logs sat in a folder outside `/tmp` with mode 000, and each agent's Codex session file was moved out of `~/.codex/sessions` as it finished. The question files in the repo stayed readable; the leakage check covers them.
- Grader: as above, 468 calls.
- Per agent, from its Codex logs and not its own report (`overview/cost.json`): pictures that exist and that it was shown (`overview`, `orig`, `at`, `scan`), `--at` and `--scan` calls, tokens. `codex exec --json` leaves out image views, so they are read from the session file: each image returned to the model is matched by content to a file in the agent's folder. All 2,226 images matched. `overview/grades.json` also records, for each visual, mixed and hard answer, whether the frame it cites is a full-size frame the agent opened (`cite`).
- Leakage check per agent: any command naming a path outside its folder (`/tmp`, `/Users`, `~`, `$HOME`, `../`, `find /`), `ffmpeg`, `ffprobe`, `curl`, `wget`, any picture or video path outside the folder in a tool call, any web search or MCP call. None in 108 agents. One (`hard` `x-wqMcYMNdg` `vidscribe`) cropped a frame inside its folder.
- Code: `overview/harness.py` (folders, prompts, runner, log reader, grader text) and `overview/run_answers.py`.

Run 2026-11-15: `clips` 12 / 47.5 / 46.5 of 48, `main` 12 / 71 / 70 of 72, `hard` 0 / 33 / 36 of 36 (`transcript` / `current` / `vidscribe`). Every bar met. No agent failed or was re-run: 21 time-check agents in 134 s, 36 `clips` agents in 226 s, 72 `main` and `hard` agents in 556 s, 8 at a time.

Changes to the `skill` prompt, the same in both picture arms unless noted:

- `/tmp/vseval` → `/tmp/vsov`; `<SKILL>` is the arm's SKILL.md from `# vidscribe` to the end.
- `current`: "the frames (N)" with the folder's real count, as in "Table re-run".
- `vidscribe`: the folder line reads "index.txt, the overview sheets (S sheets, K tiles), and video.mp4", and the last line asks "how many of the overview sheets you viewed out of how many exist" in place of "original frames".

Things the prompts did not control:

- `--ignore-user-config` drops the owner's Codex `config.toml` (MCP servers, notify hook) but not `~/.codex/AGENTS.md`, so every agent in every arm also had the owner's global instructions: prefix shell commands with `rtk`, and use Context7 for library documentation.
- A probe agent on a smoke fixture (not eval data) ran first, to confirm that Codex views images and runs `--at`. It used a single time, so it did not show which script ran.

Time-check agent (`<F>` = `/tmp/vsov/chk/<ID>`, holding `refs.json` and `frames/video.mp4`):

```
# Goal
Check that the reference answers to questions about a video are still on screen in this download of it. The questions were written on an earlier download; a new download can differ (re-encodes, edits, shifted times).

# Your folder: <F>/
- refs.json: one entry per question: set, qid, question, answer (the reference answer), time_s (when the answer was on screen in the earlier download) and visible_s (the span it was on screen).
- frames/video.mp4: the video. Do not open it directly. Pull full-size frames with `vidscribe <F>/frames --at <seconds or M:SS>` and view them. A range with a count gives that many frames (`--at 8:10-8:20/8`); batch with commas.

# Steps
For each entry, pull the frame at time_s and view it. If the reference answer cannot be read there, look up to 60 s either side of time_s, then decide.

# Rules
- Use only your folder and the `vidscribe <F>/frames --at` command. Do not open anything else under /tmp/vsov, do not search the web, do not run ffmpeg or any other tool on the video.
- verdict "ok": a full-size frame you viewed shows the reference answer. Give that frame's time as seen_s.
- verdict "gone": the reference answer is not on screen within 60 s of time_s in this download.
- Judge only whether the reference answer is on screen, not whether the question is good.

# Output
Write <F>/time_check.json: a JSON list of {"set", "qid", "verdict": "ok"|"gone", "seen_s": <seconds or null>, "note": "<what the frame shows>"}.
```
