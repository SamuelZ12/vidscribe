# Long-video eval set

12 long YouTube videos (39-111 min), 6 questions each, used for the frame-selection and frames-on-demand tests in `MEASUREMENTS.md`. Videos and transcripts are not in git (~4 GB); rebuild them from the IDs below.

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
- `grades.json`: blind grades per clip, condition and question (`score` 1 / 0.5 / 0, `reason`). Conditions: `master` (frames as of 4438e45), `scene_b` (content-score scene choice, not shipped), `at` (master frames + `--at`). Totals /72: 37.5, 36.5, 69.
- `frames_only.sh SCRIPT SRT VIDEO OUTDIR`: runs the frame-selection heredoc of any vidscribe script on an existing srt, so frame code can be compared without transcribing again.
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

The 72 questions above all name their moment through speech ("when the speaker says ..."), which is the case `--at` is built for (`MEASUREMENTS.md`, "Frames on demand", caveat). The hard set asks about moments the transcript never points to: the agent must find the moment from what is on screen. Its result decides whether the OCR timeline (ROADMAP 5) is built.

Run 2026-11-05: `frames` 11/36, `at` 31/36; OCR not built (`MEASUREMENTS.md`, "Hard eval"). Files: `hard/questions/<ID>.json` (same fields as above plus `anchor`, `anchor_s`), `hard/grades.json` (per clip, condition and question: `score`, `answer`, `confidence`, `reason`; `miss` = not found / misread on misses; `extra_frames` on `at` h1), `hard/transcript_only.json` (validation check 2 on the final 36: `answer`, `score`), `hard/check_transcript.py` (validation check 1).

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
- Answer prompts: `at` as above with the question count changed. The original `master` answer prompt was lost in recovery (the section above holds the question-writer prompt by mistake); `frames` uses the `at` prompt minus "Getting more frames" and the `--at` rule, and is recorded here as a reconstruction.
- Dev clips first, then holdout once. Same grader. Leakage check per agent (paths outside its folder, `ffmpeg`).
- Per miss, record whether any frame the agent viewed (the 40 or `--at`) falls inside `anchor_s`: **not found** if none did, **misread** otherwise.
- Results go in `eval/hard/grades.json` and `MEASUREMENTS.md`.

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
