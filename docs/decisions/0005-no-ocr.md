# ADR-0005: No OCR timeline; contact sheets for unnamed moments

## Status
Accepted. [ADR-0009](0009-drop-picture-commands.md) removed the contact sheets; OCR is still not built.

## Date
2026-11-05

## Context
`--at` ([ADR-0004](https://github.com/SamuelZ12/vidscribe/blob/v1/docs/decisions/0004-frames-on-demand.md)) relies on speech pointing to the moment. For moments the speech never names, OCR of on-screen text into `index.txt` was the candidate. A [hard eval](../measurements.md#hard-eval-moments-the-transcript-never-names) tested whether it was needed: 36 questions whose anchor isn't spoken within 60 s and whose answer is never spoken, all failed by a transcript-only agent. The bar, set before the run: build OCR if `--at` scores below 75%.

## Decision
Don't build OCR. `--at` scored 31/36 (86%; 11/36 with the automatic frames alone). For the 5 misses, add `vidscribe <frames-dir> --scan RANGES|all`: 4x4 contact sheets the agent scans cheaply before confirming with `--at`.

## Alternatives considered
- **OCR timeline in `index.txt`.** All 5 misses were "not found", the kind OCR targets, but too few to justify it.

## Consequences
- [Scan eval](../measurements.md#scan-eval---scan): dev 31 → 36/36 with the same image budget; holdout 12/12 with and without `--scan`, so the gain is unconfirmed ([#2](https://github.com/SamuelZ12/vidscribe/issues/2)).
- The 75% bar rules out a large gap, not a small one; 3 of the 5 misses came from one video.
- Revisit if agents report failing to find on-screen content, or if a footage-heavy holdout shows `--scan` isn't enough.
