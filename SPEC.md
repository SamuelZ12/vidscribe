# Spec: frames on demand (ROADMAP 5, first bullet)

## Objective
On long videos the 40-frame cap leaves most moments unseen; pinpoint visual questions fail because no frame lands where the answer is on screen (MEASUREMENTS.md, "Scene choice on long videos": master 37.5/72, visual 19/48, free check 23/60). Let the agent fetch frames at moments it picks from the transcript, from the `video.<ext>` already kept in the frames folder, without re-downloading or re-transcribing.

User: an AI agent following `skill/SKILL.md` after a normal `vidscribe` run.

## Interface
```
vidscribe <frames-dir> --at TIMES
```
- `<frames-dir>`: the folder the normal run printed (`frames: /tmp/vidscribe/frames/<name> ...`); must contain `video.*`.
- `TIMES`: comma-separated; each is a time (`494`, `8:14`, `1:02:05`, decimals allowed) or a range `A-B`.
  - time → 1 frame; range → 4 frames evenly spaced inside it (at (i+0.5)/4, like even frames).
- Writes `at_08m14.0s.jpg` (same scale/quality as other frames: 720p, `-q:v 3`) into the frames folder; prints one line per frame to stdout: `MM:SS.s<TAB>path`.
- Does not transcribe, does not touch `index.txt`, does not prune or recreate the folder.
- Errors (exit 1, message on stderr): no `video.*` in the folder (pruned after 3 days → "re-run vidscribe on the source"); unparseable time; time beyond the video's duration; `--at` combined with other flags.

## Code shape
Early branch in `bin/vidscribe` before any download/transcription: parse `--at`, validate, loop `ffmpeg -ss T -i video -frames:v 1`, exit. Bash 3.2 + awk for time parsing, no new dependencies. Target: ~25 lines.

## Docs
- `skill/SKILL.md` step 4: after viewing the frames, if the question is about something on screen at a moment no frame covers, find that moment in the transcript and run `--at` (a range when unsure of the exact second); view the new frames before answering. Keep requests small (guidance, not enforced).
- `README.md`: flag + one example. Usage comment at top of `bin/vidscribe`.
- `MEASUREMENTS.md`: eval section. `ROADMAP.md`: mark the bullet done or record why not.

## Testing strategy
No harness in the repo; smoke runs:
- `bash -n`, and run under `/bin/bash` (3.2).
- Short testsrc mp4: single time, range, `M:SS` and `H:MM:SS`, multiple items; frames exist, timestamps in names match; ffprobe confirms 720p jpg.
- Errors: missing folder, pruned folder (no `video.*`), time past duration, bad syntax.
- Symlinked local video with spaces in the path.
- Normal run unchanged: a short clip's transcript and `index.txt` byte-identical to master.

Eval (same method as the scene-choice test, `/tmp/vseval2`):
- 12 long videos × 6 questions; same transcripts and master frame folders (`master/frames/<ID>/`, which link `video.mp4`).
- Condition C: answer agents get the new SKILL.md text and may run `--at` on their folder; everything else as for master. They see questions, never `time_s`/`visible_s`.
- Blind grading with the same `completion()` grader; compare to the existing master grades (37.5/72, visual 19/48). Also record per question: `--at` calls, extra frames, whether any extra frame fell inside `visible_s`.
- Dev clips first; holdout clips run once with the SKILL.md wording frozen.

## Success criteria
- Interface behaves as above; all smoke checks pass; normal runs byte-identical.
- Ship (docs recommend `--at`) if C beats master on visual questions by clearly more than agent noise, holdout included: proposed bar ≥ +6/48 visual overall and holdout visual not lower than master, speech within ±1.
- Otherwise: record the result in MEASUREMENTS.md and don't recommend it in SKILL.md (user decides whether the flag stays).

## Boundaries
- Always: feature branch; small Conventional Commits; README + SKILL.md updated with the code; bash 3.2 compatible; one reviewer subagent over the branch diff before asking to merge.
- Ask first: merge, push, deleting `/tmp/vseval2`, changing normal-run output or the frame cap.
- Never: edit `bin/vidscribe` while another run uses it on master (work on the branch; the installed symlink follows the checkout, so switch back to master between sessions); touch `/tmp/vidscribe` contents other than fresh test folders; tune SKILL.md wording on holdout results.

## Decisions (approved 2026-11-04)
1. Address by frames folder path, not the original source.
2. Print only; `index.txt` untouched.
3. Range: fixed 4 frames.
4. Ship bar as proposed.
