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
