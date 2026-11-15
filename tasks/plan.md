# Implementation Plan: full overview sheets (V1)

Source spec: SPEC.md

## Overview

Change the overview's tile count in `bin/vidscribe` from one per 10 s (16 to 96) to 16 per sheet, with one sheet per 160 s of picture rounded to the nearest (1 to 6), so every overview sheet is full. Then update `docs/usage.md` and `skill/SKILL.md`, and record the decision in ADR-0008. Task status lives in `tasks/todo.md`. Work happens on branch `feat/full-sheets` in the worktree `/Users/samuelzhang/dev/vidscribe-full-sheets`; nothing is pushed or merged without the owner's go-ahead.

## Architecture Decisions

- **One line of code.** Only the count changes (`bin/vidscribe`, the `if not full:` line). Tile spacing, the sheet builder, `index.txt`, `-v N`, `--at` and `--scan` are not touched.
- **`math.floor(dur/160 + 0.5)`, not `round()`** (spec, Code Style): `round()` sends 1.5 and 2.5 both to 2.
- **The script's comments change with the code** (header line 6 and the comment above the count), so they are true at every commit. `docs/usage.md` and `skill/SKILL.md` are separate tasks.
- **Nearest sheet, new ADR-0008, spec deleted after shipping** (owner, 2026-11-15; spec, Decisions).

## How each task is checked

No test harness (spec, Testing Strategy). Checks are real runs under `/bin/bash` 3.2.57 from copies in `/tmp/vs_smoke/full`, never the file being edited.

- `run.sh m|n` runs `vidscribe.master` or `vidscribe.new` on the six clips with `-f srt`; `check.sh m|n` checks success criterion 1 on those runs: the `frames:` line, the line count of `index.txt`, the number of sheets, and that slot 16 of the last sheet holds a picture (an empty slot is white).
- **RED:** `check.sh m` (master's runs) fails on the clips whose count changes.
- **GREEN:** edit, copy to `vidscribe.new`, `run.sh n`, `check.sh n` passes on all six.
- **Regression:** `.srt` and `.txt` compared with master's for every clip; `index.txt` compared where the count does not change. "Build" is `/bin/bash -n bin/vidscribe`.
- Before transcripts are compared, master is run twice on `full_150.mp4`; if the two runs differ, the transcript comparison is reported void, not passed.
- Doc tasks have no RED: they are checked by reading the diff and by `rg` finding no "one per 10 s" statement of the overview count.

## Tasks

### Task 0: Fixtures and golden output (no commit)

Cut `full_150`, `full_239`, `full_241`, `full_401`, `full_881` and `full_1000.mp4` from `/tmp/vsov/src/Unzc731iCUY.mp4` (`-t <seconds> -c copy`) into `/tmp/vs_smoke/full`. Save `master:bin/vidscribe` as `vidscribe.master`, run it on all six, and run it a second time on `full_150.mp4`.

- Done when the clips exist, master's transcripts, sheets and stderr are saved under `out_m/`, `frames_m/` and `log_m/`, and the determinism check has a recorded result.
- Dependencies: none. Files: none in the repo.

### Task 1: Tile count gives full sheets

Change the count line to `n = 16 * min(6, max(1, math.floor(dur/160 + 0.5)))` and reword the comment above it and header line 6 (which `-h` prints).

- Acceptance:
  - The `Count formula` command in `SPEC.md` prints `[16, 16, 32, 32, 48, 80, 96, 96, 96]`.
  - `check.sh n` passes: 150 s gives 16 tiles on 1 sheet, 239 s 16/1, 241 s 32/2, 401 s 48/3, 881 s 96/6, 1000 s 96/6; `index.txt` has that many lines; the last sheet is full (criterion 1).
  - `full_150` and `full_1000` have the same `index.txt` as master (criterion 3); `.srt` and `.txt` are byte-identical to master for all six (criterion 4); `-v 5` on `full_150.mp4` gives the same `index.txt` and frame files as master.
- Verification: RED with `check.sh m` (master gives 24, 25, 41 and 89 tiles on the 239, 241, 401 and 881 s clips), then GREEN; `/bin/bash -n`.
- Dependencies: Task 0. Files: `bin/vidscribe`. Scope: XS.

### Task 2: `docs/usage.md`

Replace "one tile per 10 s of picture, at least 16 and at most 96" with the new rule: 16 tiles per sheet, one sheet per 160 s of picture rounded to the nearest, 1 to 6 sheets, every sheet full. Keep the 2-hour example (96 tiles, one every 75 s).

- Acceptance: the sentence states the new rule with exact numbers and matches what Task 1's runs printed; nothing else in the file changes.
- Verification: read the diff; `rg -n "per 10 s" docs/usage.md` finds only the `--scan` sentence.
- Dependencies: Task 1. Files: `docs/usage.md`. Scope: XS.

### Task 3: `skill/SKILL.md`

Step 3, the same sentence for agents: every overview sheet is a full 4x4 sheet, 1 to 6 sheets, tiles about 10 s apart on videos up to 16 minutes and further apart on longer ones.

- Acceptance: step 3 states the new rule and no longer says "one per 10 s of video, 16 to 96 in all"; no other step changes.
- Verification: read the diff; `rg -n "one per 10 s|16 to 96" skill/SKILL.md` finds nothing.
- Dependencies: Task 1. Files: `skill/SKILL.md`. Scope: XS.

### Task 4: ADR-0008 and the eval note

Write `docs/decisions/0008-full-sheets.md` (context: part-empty last sheets cost a full image, 6 of 21 eval videos; decision: the new rule, nearest not up; consequences: the 2:40-3:59 band drops to 16 tiles up to 15 s apart; the eval ran with the old counts). Add it to the ADR index, add a pointer in ADR-0007, and add a note under "Overview sheets" in `docs/measurements.md` that the eval ran with the old counts (issue #10 covers a re-run).

- Acceptance: ADR-0008 exists in the format of 0007 and is in the index; 0007 points to it; `docs/measurements.md` has the note; no measured number is changed (criterion 6).
- Verification: read the diff; every relative link in the new and changed files resolves.
- Dependencies: Task 1. Files: `docs/decisions/0008-full-sheets.md`, `docs/decisions/README.md`, `docs/decisions/0007-overview-sheets.md`, `docs/measurements.md`. Scope: S.

### Checkpoint: before merge

- Run the owner's test video (`https://youtu.be/dQw4w9WgXcQ`, 3:33; one download): `16 tiles on 1 sheet` (criterion 2).
- Unchanged paths against master on the same input (criterion 5): `-a`, an audio file, `--at`, `--scan` (`-v 5` is checked in Task 1; repeat it only if the script changed after Task 1).
- `rg -n "one per 10 s|one tile per 10 s" bin docs/usage.md skill` finds nothing.
- Stop and report. Merge, push and the deletion of `SPEC.md` and `tasks/` wait for the owner's go-ahead.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Transcripts differ between two runs of the same script | Criterion 4 cannot be shown | Determinism check in Task 0; a difference is reported as void |
| A clip's length lands on the wrong side of a boundary after `-c copy` | Wrong expected count | Clip lengths are 1 s away from the 240, 400 and 880 s boundaries; probed lengths are within 0.04 s of the request |
| Picture shorter than the audio leaves the last sheet part empty | Not every sheet is full | Out of scope (issue #3); the test clips have picture and audio of the same length |
| The untracked `SPEC.md` in the main checkout blocks the merge | Merge stops | The copy in the main checkout is removed, with the owner's go-ahead, before the merge |

## Open Questions

None.
