# ADR-0004: Frames on demand (`--at`) instead of smarter scene choice

## Status
Accepted

## Date
2026-11-04

## Context
On long videos the 40-frame cap ([ADR-0003](0003-frame-cap.md)) leaves room for ~16 of 100-650 scenes, and scene frames gave no gain there (1, 1, 2 of 4 correct on the three long clips). Two ways to choose better scenes were tried first ([scene choice on long videos](../measurements.md#scene-choice-on-long-videos-not-shipped)):
- **Skip recurring shots:** backfired on lectures, where slide templates recur.
- **Content score (prefer plain-background frames):** content frames went from 71 to 122 of 209 (blind judge), but answers didn't improve (37.5 vs 36.5 of 72).

With 16 slots, whether a frame lands on the asked-about moment is luck; the number of frames limits pinpoint questions, not which scenes are chosen.

## Decision
Keep the shipped scene selection (thinned evenly over the scene list). Let the agent fetch frames itself: `vidscribe <frames-dir> --at TIMES` extracts frames at chosen times from the run's video. To make that possible, the frames folder keeps `video.<ext>`: URL downloads are moved there, local files are symlinked (not copied, so a multi-GB recording costs nothing in `/tmp`).

## Alternatives considered
- **Content-score selection.** Rejected: no gain (above).
- **Raise the cap on long videos.** Not tried as such: the clip test (2 clips, 4 questions each) showed no sign that more frames help ([ADR-0003](0003-frame-cap.md)), and agents skip frames in large sets.

## Consequences
- [Frames on demand](../measurements.md#frames-on-demand): 37.5 → 69/72 on 12 long videos (visual 19 → 46/48, holdout visual 10 → 22/24), at 1-3 calls and 4-23 extra frames (~19k tokens) per video.
- `--at` only works while the folder exists (3 days) and, for local files, while the original stays where it was.
- Agents must find the moment first; that works when speech leads to it. Moments the speech never names: [ADR-0005](0005-no-ocr.md).
