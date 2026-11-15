# ADR-0007: Overview sheets instead of default frames

## Status
Accepted. Supersedes [ADR-0003](0003-frame-cap.md). The tile count is amended by [ADR-0008](0008-full-sheets.md).

## Date
2026-11-15

## Context
A video run saved up to 40 full-size frames, picked by three rules sharing a cap ([ADR-0003](0003-frame-cap.md)): 8 evenly spaced, "ref" frames where the speech points at the screen, and scene ends. That is ~48k image tokens on a long video, and the selection was the most complicated part of the script.

The choice of default frames is not what answers questions. In the [table re-run](../measurements.md#table-re-run-every-condition-on-every-set), the default frames alone took agents to 78.5 of 156; fetching frames on demand (`--at`, `--scan`) took them to 151.5. Two ways of choosing better scene frames had already failed to improve answers ([ADR-0004](0004-frames-on-demand.md)).

## Decision
- A video run saves overview sheets instead of frames: 4x4 contact sheets (`overview_NN.jpg`, the `--scan` geometry) of evenly spaced tiles, one per 10 s of picture, at least 16 and at most 96 tiles (1 to 6 sheets). `index.txt` has one line per tile: its time, its sheet and position (`overview_NN.jpg#PP`) and the speech around it.
- Ref frames, scene frames in the main run, the 40-frame cap and its sharing rule are removed. `--scan` still adds scene ends to its sheets.
- `-v N` gives exactly N evenly spaced full-size frames in place of the sheets. Bare `-v` forces a video run with sheets.
- `--at A-B/N` gives N frames (1-40) inside a range; without `/N` a range still gives 4.
- `skill/SKILL.md` tells agents to view every sheet, and never to state on-screen text, numbers or names from a tile: fetch the full-size frame with `--at` first.

## Alternatives considered
- **Keep the 40 frames.** In the eval below they scored 1 point higher on two sets and 3 lower on the third, for about three times the images viewed.
- **Full-size frames by default on short videos.** The fallback if short clips lost answers. They did not beyond the bar (46.5 vs 47.5 of 48), so one rule covers every length.
- **Scene-aware tiles.** Not built: even spacing bounds the gap between tiles, and `--scan` adds scene ends on request.
- **Time labels drawn on the tiles.** Not built: needs ffmpeg's `drawtext` and costs tile pixels; `index.txt` gives each tile's time.
- **A ceiling of 160 tiles (10 sheets).** The owner chose 96.

## Consequences
- [Eval](../measurements.md#overview-sheets-against-the-current-default-frames), sheets against master's frames, both with `--at` and `--scan` and only `skill/SKILL.md` as instructions: clips 46.5 vs 47.5 of 48, long videos 70 vs 71 of 72, hard questions 36 vs 33 of 36. Every bar set before the run is met. It is one run, so differences of this size are noise, and its agents were Codex, not the Claude agents of the earlier tests.
- `--at A-B/N` rests on smoke cases and a small re-check. The eval's agents ran master's `--at` by mistake, so the 6 calls that gave a count failed. Re-run with the branch script, those six agents gave counts for 12 ranges and all worked, but their answers scored 20 of 23 where the first run's scored 23. Six agents cannot tell noise from an effect of the count; the eval's `vidscribe` arm has not been re-run with the shipped script.
- Agents viewed 10-21 images per video where they viewed 34-55. No answer was read off a sheet: 131 of 132 on-screen answers cite a full-size frame the agent fetched, and the other is "unknown".
- A tile is 318x178, too small to read text from, so every on-screen detail now costs an `--at` call. Both answers lost in the eval were ones a default full-size frame happened to show.
- Past 16 minutes the tiles are more than 10 s apart (one per 75 s on a 2-hour video); `--scan` covers a chosen stretch at 10 s or closer.
- Frame files lose the `_even`/`_ref`/`_scene` suffix (`-v N`), and a default run has no frame files at all: anything that matched those names stops working.
- Sections of `docs/measurements.md` before this eval, and the `frames`, `at` and `scan` prompts in `eval/README.md`, describe the frames this ADR removes.
