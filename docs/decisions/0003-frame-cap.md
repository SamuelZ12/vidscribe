# ADR-0003: Cap automatic frames at 40, split between refs and scenes

## Status
Superseded by [ADR-0007](0007-overview-sheets.md)

## Date
2026-11-04

## Context
Frames are cheap to make (~60 ms) but cost the reading agent ~1.2k image tokens each. Speech-triggered ("ref") frames grow with talk length (~0.5 per minute), so a 2-hour talk would give ~72 frames, ~90k tokens, and scene-change frames add hundreds more on long videos. Agents also skip frames in large sets: before being told to view every frame, 3 of 15 looked at only part of theirs. Evidence: [Frame cap: 40](../measurements.md#frame-cap-40), [clip test](../measurements.md#clip-test-frames-vs-transcript-only-cap-vs-no-cap), [scene-change frames](../measurements.md#scene-change-frames).

## Decision
- At most 40 frames per run, or N if `-v N` asks for more (then even frames only). Ref frames alone stay under the cap up to ~60 min; with scene frames, the cap binds on most videos over ~10 min.
- The N evenly spaced frames are always kept. Ref and scene frames share the remaining slots ("split"); a side's unused share goes to the other, and each is thinned evenly over time.

## Alternatives considered
- **No cap.** Tested on the two clips where the cap bit: MIT 3/4 either way, Google I/O 0 uncapped vs 1 capped. No sign more frames help; 4 questions per clip only rule out a large effect.
- **"Replace": scenes and refs first, even frames only fill empty slots.** Tied with split (34/48 on the free check). Split won because it keeps even spacing on videos without hard cuts (animated charts) and leaves `-v N` unchanged.

## Consequences
- Long videos are bounded at ~50k image tokens.
- On long videos only ~16 of hundreds of scenes fit; better choice among them didn't help ([ADR-0004](0004-frames-on-demand.md)), so pinpoint questions rely on `--at`.
