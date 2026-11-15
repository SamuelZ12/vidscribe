# Implementation Plan: overview sheets (V1)

Source spec: SPEC.md

## Overview

Replace the default frame selector in `bin/vidscribe` (even + ref + scene frames under a 40 cap) with evenly spaced 4x4 overview sheets, make `-v N` mean exactly N full-size even frames, and add a per-range count to `--at` (`A-B/N`). Then update `docs/usage.md` and `skill/SKILL.md`, run the eval behind its own approval, and write the ADR and README table only if every bar is met. Task status lives in `tasks/todo.md`.

## Architecture Decisions

- **One sheet builder, shared.** A python function in the shared heredoc takes a video, a list of times and a file prefix; it grabs the tiles, renumbers them without gaps, removes old sheets with that prefix, tiles them 4x4 and returns which times gave a picture. `--scan` and the overview both call it and print their own messages (spec, Code Style: "do not copy it").
- **`scene_ends` becomes scan-only.** Once the main run stops using it (Task 3) it moves into the `--scan` heredoc.
- **Order: refactor, `--at`, remove, add.** Task 1 changes no behaviour and is checked against master before anything else moves. Task 3 deletes the old selector and Task 4 adds the overview, so each commit reverts cleanly. Between Tasks 3 and 4 a run without `-v N` gives 8 even frames; that state exists only on the branch.
- **`-v 0` is rejected while parsing arguments**, before any download or transcription.
- **One-decimal spacing is formatted in python** (`f"{D/K:.1f}"`; checked: 30/16 prints `1.9`, 1000/96 prints `10.4`).
- **The header comment and `-h` text change in the task that changes the behaviour**, so the comment is true at every commit. `docs/usage.md` and `skill/SKILL.md` are separate tasks.

## How each task is checked

No test harness (spec, Testing Strategy). The smoke cases S1-S12 in `SPEC.md` are the tests, run under `/bin/bash` 3.2.57 from copies in `/tmp/vs_smoke`.

- **RED:** copy the script before the edit to `/tmp/vs_smoke/vidscribe.new`, run the task's cases, record that they fail.
- **GREEN:** edit, copy again, run the same cases, record that they pass.
- **Regression:** run every case that passed before the task. "Build" is `/bin/bash -n bin/vidscribe`.
- Task 1 is a refactor, so it has no RED: master's `--scan` output is captured first and the refactored script must reproduce it byte for byte.
- Each run transcribes ~9 s of speech with the model already in the Hugging Face cache: no download, a few seconds each.
- Before S9/S10 are trusted, `master` is run twice on `speech.m4a`; if the two transcripts differ, S9 and S10 are reported void, not passed.

## Tasks

### Task 0: Fixtures and golden output (no commit)

Build `/tmp/vs_smoke` per `SPEC.md` (speech, `v3`/`v30`/`v200`/`v1000.mp4`, `speech.m4a`, `vidscribe.master`). Run `master v200.mp4` once to make `frames_m/v200`, then capture master's stdout, stderr and jpgs for `--scan 0:00-3:20`, `--scan all` and `--at 0:10,0:20-1:00`. Run `master speech.m4a` twice and compare.

- Done when the fixtures exist, the golden output is saved under `/tmp/vs_smoke/golden/`, and the determinism check has a recorded result.
- Dependencies: none. Files: none in the repo.

### Task 1: Shared sheet builder for `--scan` (refactor)

Move tile grabbing, renumbering and 4x4 tiling out of the `--scan` heredoc into a function in the shared heredoc. `--scan` calls it.

- Acceptance:
  - `--scan 0:00-3:20` and `--scan all` on `frames_m/v200`: stdout and stderr equal the golden output; every sheet is `cmp`-identical.
  - A normal run is unchanged (`new v200.mp4`: same stderr `frames:` lines and same file list as `master v200.mp4`).
- Verification: `/bin/bash -n`; the two comparisons above.
- Dependencies: Task 0. Files: `bin/vidscribe`. Scope: S.

### Task 2: `--at A-B/N`

- Acceptance:
  - S7: `--at 0:10-1:50/8` prints 8 lines, first `00:16.3`, last `01:43.8`; `--at 0:10-1:50` prints 4, first `00:22.5`.
  - S8: `--at 0:30/3`, `/0`, `/41` and `--scan 0:10-1:50/8` exit 1 with `a count needs a range`, `must be 1-40`, `must be 1-40`, `bad time`.
  - `--at 0:10,0:20-1:00` stdout and frames equal the golden output (S11, `--at` half). The header comment and the usage message name `/N`.
- Verification: RED on S7/S8 (today: `bad time "0:10-1:50/8"`), then GREEN; Task 1's comparisons again.
- Dependencies: Task 0. Files: `bin/vidscribe`. Scope: S.

### Task 3: `-v N` gives exactly N even frames; old selector removed

Delete ref frames and their regex, scene frames in the main run, the cap and its sharing rule, thinning, the 3-second de-duplication and the `_even`/`_ref`/`_scene` suffixes. `scene_ends` moves into the `--scan` heredoc.

- Acceptance:
  - S5: `-v 5` on `v200.mp4` prints `(5 frames, one every 40.0 s)`; files `000_00m20.0s.jpg` to `004_03m00.0s.jpg`, 720 px high; `index.txt` has 5 lines.
  - S6: `-v 0` exits 1 with `-v N: N must be at least 1`, before transcription. `-v 1` prints `1 frame`.
  - S12: `rg -c 'DEIX|thin\(|capped at|_even|_ref|_scene' bin/vidscribe` finds nothing. Header comment matches.
- Verification: RED on S5/S6/S12, then GREEN; regression: Tasks 1-2 comparisons, S9, S10.
- Dependencies: Task 1. Files: `bin/vidscribe`. Scope: S.

### Task 4: Overview sheets by default

A video run without `-v N` (including bare `-v`) saves `overview_NN.jpg` sheets through the shared builder, with `index.txt` rows `mm:ss.s`, `overview_NN.jpg#PP`, span, text.

- Acceptance:
  - S1, S2, S3: tile and sheet counts, summary lines, `index.txt` rows and sheet size as written in `SPEC.md`; `frames/v200` holds only the sheets, `index.txt` and the `video.mp4` symlink.
  - S4: `v3.mp4` saves only tiles before 3 s, prints `frames: no picture at`, and `index.txt` has as many lines as the summary counts tiles; `#PP` values have no gap.
  - `-v 5` still passes S5 with no `overview_*.jpg`; bare `-v` gives the overview. Header comment matches.
- Verification: RED on S1-S4, then GREEN; regression: S5-S12.
- Dependencies: Tasks 1, 3. Files: `bin/vidscribe`. Scope: M.
- Not reachable with fixtures: the "no picture length" branch (`D` is 0). It is kept as the spec says and checked by reading; the result will say so.

### Task 5: `docs/usage.md`

- Acceptance: describes the tile rule, sheet files, `index.txt` rows, `-v N`, bare `-v`, `--at A-B/N` and the short-picture message; no mention of ref frames, scene frames in a normal run, the cap or the old suffixes.
- Verification: `rg -n '_even|_ref|_scene|At most 40|on-screen reference' docs/usage.md` finds nothing; every command and message quoted in the file is run on the fixtures and matches.
- Dependencies: Tasks 2-4. Files: `docs/usage.md`. Scope: XS.

### Task 6: `skill/SKILL.md`

Read the `writing-for-agents` skill first. Rewrite steps 3-5 and the `-v N` reference line for success criterion 6.

- Acceptance: tells the agent to (a) view every overview sheet and map a tile to its time and speech with `index.txt`; (b) never state on-screen text, numbers or names from a tile, and fetch the full frame with `--at` first; (c) use `--at A-B/N` to choose how many frames a stretch gets; (d) use `-v N` on a first run only, since a re-run transcribes again and replaces the frames folder.
- Verification: the four points checked against the text; every command in the file run on the fixtures. Whether agents follow it is the eval's question (Task 7).
- Dependencies: Tasks 2-4. Files: `skill/SKILL.md`. Scope: XS.

### Checkpoint A: before the eval

- S1-S12 all run once more at the branch head under `/bin/bash`, results listed case by case.
- One reviewer subagent reads the branch diff against `SPEC.md`; each accepted finding is fixed in its own commit and the affected cases re-run.
- **Autonomous run stops here** and reports. `SKILL.md` and the bars are frozen from this commit.

### Task 7: Eval (needs its own approval: downloads, 108 answer agents through the Codex CLI, grading)

Per `SPEC.md`, Testing Strategy, "Eval". The request for approval states what must be downloaded and transcribed again, the number of agent runs and the expected time.

- Acceptance: scores per set and arm against the fixed bars; per-agent counts of sheets and frames viewed; `eval/overview/{grades,labels,cost}.json`; a new section in `docs/measurements.md` and in `eval/README.md`, whatever the result (success criterion 10).
- Dependencies: Checkpoint A and approval. Files: `docs/measurements.md`, `eval/README.md`, `eval/overview/*`. Scope: M.

### Task 8: ADR-0007 (only if every bar is met)

- Acceptance: success criterion 8 (`docs/decisions/0007-overview-sheets.md`, ADR-0003 superseded, corrected lines in ADR-0002 and ADR-0004, `docs/decisions/README.md`).
- Dependencies: Task 7 with all bars met. Scope: S.

### Task 9: README (only if every bar is met)

- Acceptance: success criterion 9 (two-column table over 156 questions with this run's percentages, row label "Score", link to the new section); the intro and usage comments say overview sheets, not key frames. `SPEC.md` status becomes `implemented`.
- Dependencies: Task 7 with all bars met. Scope: XS.

### Checkpoint B: merge

Merge and push only on request (spec, Boundaries).

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Refactoring `--scan` changes its sheets | High: breaks "unchanged, byte for byte" | Task 1 lands alone and is compared with master's stdout, stderr and jpgs before any other change |
| Transcription is not deterministic between runs, so S9/S10 cannot show equality | Medium | Task 0 runs master twice; if the transcripts differ, the cases are reported void and the transcription code is shown unchanged by diff instead |
| Editing the script while a run reads it corrupts that run | Medium | Every run uses a copy in `/tmp/vs_smoke` |
| The installed `vidscribe` is a symlink into the main checkout | Medium: every agent on this Mac would run the branch | Work happens in the worktree `~/dev/vidscribe-overview-sheets`; the main checkout stays on master |
| A missing tile shifts later tiles on a sheet, so `#PP` must follow saved order, not planned order | Medium: wrong time for a tile | S4 checks that rows and tiles agree; positions are numbered after the builder reports what it saved |
| S12's pattern matches a new name by accident (`_scene`, `_ref`, `_even`) | Low | Names are chosen to avoid those substrings; S12 runs in Tasks 3 and 4 |
| Agents read small text from tiles and answer wrongly | High for the eval | `SKILL.md` point (b); the eval records whether each on-screen answer cites a full-size frame |

## Open Questions

None. Both spec questions were answered at approval (2026-11-15) and are recorded in `SPEC.md`.
