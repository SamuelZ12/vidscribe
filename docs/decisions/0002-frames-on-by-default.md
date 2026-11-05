# ADR-0002: Frames on by default for video

## Status
Accepted

## Date
2026-11-04

## Context
Frames used to be opt-in (`-v`), so agents only got them when they knew to pass the flag, and a transcript alone can't answer questions about what is shown. In the [clip test](../measurements.md#clip-test-frames-vs-transcript-only-cap-vs-no-cap) (12 clips, 48 questions, blind grading), transcript + frames scored 28.5/48 against 13/48 for transcript only: visual 11.5 vs 1/24, mixed 5 vs 0/12, speech 12/12 both. Frames never scored lower on any question, and their misses were "unknown", not wrong answers.

## Decision
- An input with a video stream (ffprobe, `-select_streams v`) gets frames and `index.txt` without any flag. `-a`/`--audio-only` opts out; `-v N` sets the number of evenly spaced frames (default 8).
- Audio-only inputs, including mp3/m4a with cover art (an attached picture, not a video stream), behave exactly as before.
- URLs download video up to 720p whenever frames are wanted (not with `-a` or `-f vtt|json`).
- Frame mode writes srt + txt; `-f vtt|json` without `-v` keeps giving a transcript only, so existing `-f json` users don't break.

## Alternatives considered
- **Keep `-v` opt-in.** Rejected: it leaves the 2x gain to agents that happen to know the flag.

## Consequences
- URL runs without `-a` download much more data (a long podcast as 720p video instead of audio).
- Frame runs cost the agent image tokens (~1.2k per frame), which [ADR-0003](0003-frame-cap.md) bounds.
