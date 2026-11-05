# Spec: contact-sheet scan (ROADMAP 5)

## Objective
`--at` finds moments the speech points to; moments no speech relates to stay hard. The hard eval's 5 misses were all "not found" after searches of 40-52 extra frames (`MEASUREMENTS.md`, "Hard eval"). Let the agent scan a stretch of video cheaply, many small frames per image, then confirm the moment with `--at` (scan cheaply, then inspect; idea from Google's agentic video, done locally). The probe (`MEASUREMENTS.md`, "Scan probe") located all 5 misses with scene tiles plus even fill, at 5-7 sheets per 10 min.

User: an AI agent following `skill/SKILL.md` after a normal `vidscribe` run. Local and free: ffmpeg and system python3 only.

## Interface
```
vidscribe <frames-dir> --scan RANGES
```
- `RANGES`: comma-separated ranges in `--at` syntax (`50:00-60:00`, `3000-3600`), or `all` for the whole video. Single times are an error ("use --at for single times").
- Tiles per range: the last frame of each scene (same cut detection and dedupe as normal-run scene frames) plus evenly spaced fill so no gap between tiles, or between a range edge and a tile, exceeds 10 s.
- Sheets: 4x4 grid, 1280x720 JPEG (tiles 318x178 with 2 px white padding), `-q:v 3`, written to the frames folder as `scan_<start>-<end>_NN.jpg` (e.g. `scan_50m00s-60m00s_01.jpg`). The last sheet of a range may be partly empty.
- Stdout, one line per sheet: `path<TAB>t1 t2 ... t16` (tile times `MM:SS.s`, reading order). Times are not drawn on the image: this ffmpeg build has no `drawtext`, and the probe agents mapped tiles from the printed times without trouble.
- Stderr before sheets, per range: tile count and sheet count (e.g. `50:00-60:00: 93 tiles, 6 sheets`), so the agent sees the cost.
- Does not transcribe, does not touch `index.txt` or other frames.
- Errors (exit 1, stderr), all checked before any extraction, as `--at` does: no `video.*` (pruned: re-run on the source); bad syntax; a range past the end; a backwards range; `--scan` with other flags.

## Code shape
Early branch in `bin/vidscribe` next to `--at`. Range parsing reuses the `--at` awk (ranges only). Scene detection is the normal run's (2 fps, 160 px, score > 0.3, skip < 1 s and flat frames, dHash dedupe), run with `-ss/-to` on the range only (~7 s per 10 min, ~85 s for 111 min). It lives in one place both paths use; the normal run's transcript, `index.txt` and frames stay byte-identical to master. Tiles are extracted with `ffmpeg -ss` and tiled with ffmpeg's `tile` filter. Bash 3.2, no new dependencies. Target: ~40 lines.

## Docs
- `skill/SKILL.md`: new step after "Get missing frames": if the question is about something on screen and the transcript gives no lead (or `--at` found nothing), `--scan` the stretch where it most likely is (10 min ≈ 6 sheets), view every sheet, then `--at` the tile's time and answer from that frame. Never answer from a tile (the probe's one misread came from a 4x4 tile). `all` only as a last resort: a 111-min video is ~64 sheets.
- `README.md`: flag + one example. Usage comment at the top of `bin/vidscribe`.
- `MEASUREMENTS.md`: eval section. `ROADMAP.md`: mark done or record why not. `eval/README.md`: the holdout set and the `scan` condition.

## Testing strategy
No harness; smoke runs:
- `bash -n` and a run under `/bin/bash` 3.2.
- testsrc mp4 with hard cuts (concat of different lavfi sources) and one long static stretch: one range, several ranges, `all`; check tile times include the cuts and no gap exceeds 10 s; sheets are 1280x720; stdout lines match the sheets.
- Errors: single time, past end, backwards, bad syntax, pruned folder, extra flags; nothing written on error.
- Symlinked local video with spaces in the path.
- Normal run byte-identical to master (transcript, `index.txt`, frames) with `VIDSCRIBE_OUTDIR`/`VIDSCRIBE_FRAMES_DIR` in a scratch dir.
- Tile times on the probe windows match `eval/scan_probe.py --method fill10`.

## Eval
Same method as the hard eval (`eval/README.md`, "Hard set"): fresh agents, blind x/y labels, the same grader, leakage check.
- Conditions: `at` (frames + `--at`, the current SKILL.md) and `scan` (frames + `--at` + `--scan`, new SKILL.md). Record per question: score, confidence, `--at`/`--scan` calls, extra frames and sheets (tokens at ~1.2k each), miss type.
- Dev: the 12 hard-set videos and 36 questions (now all dev, since the probe used 5). `at` grades exist (31/36); run `scan` only. SKILL.md wording may be tuned on dev, then frozen.
- Holdout: 3-4 new long videos (≥ 45 min; at least one keynote with montage/demo shots, one documentary, one lecture or talk), rebuilt and transcribed like the others. 3 hard questions each from the frozen hard-set writer prompt, validated by both checks, committed under `eval/hard/questions/` before any answer run. Both `at` and `scan` run once.
- Frame folders are pruned after 3 days: build them with `eval/frames_only.sh` right before the answer runs.

## Success criteria
- Interface behaves as above; all smoke checks pass; normal runs byte-identical.
- Ship (SKILL.md recommends `--scan`) if all hold:
  1. Dev: `scan` ≥ 33/36 (at least 2 of the 5 `at` misses recovered, no other losses beyond 0.5 grader noise).
  2. Holdout: `scan` ≥ `at`.
  3. Confident wrong answers (graded 0 with high confidence) in `scan` no more than in `at` + 1, dev and holdout combined.
- Cost is recorded, not gated; if `scan` uses more than 2x `at`'s extra tokens per video, report it with the results.
- Otherwise: record in `MEASUREMENTS.md`, keep the flag out of SKILL.md; the user decides whether the code stays.

## Boundaries
- Always: feature branch `scan`; small Conventional Commits; README + SKILL.md updated with the code; bash 3.2; one reviewer subagent over the branch diff before asking to merge.
- Ask first: merge, push; changing normal-run output, the frame cap or scene detection settings; downloading the holdout videos (list proposed first); deleting `/tmp/vseval` or `/tmp/vsprobe`.
- Never: tune SKILL.md wording, G or the grid on holdout results; touch `/tmp/vidscribe` contents other than fresh test folders; send media off the device.

## Open questions
1. `all`: allow it (agents may burn ~64 sheets on a long keynote), or require explicit ranges? Proposed: allow, with the stderr cost line and SKILL.md guidance.
2. Fill gap 10 s and 4x4 grid were chosen on the 5 probe windows; fix them now (proposed), or tune on dev?
3. Ship bar as above?
