# ADR-0009: Drop the picture commands

## Status
Accepted. Supersedes [ADR-0002](https://github.com/SamuelZ12/vidscribe/blob/v1/docs/decisions/0002-frames-on-by-default.md), [ADR-0004](https://github.com/SamuelZ12/vidscribe/blob/v1/docs/decisions/0004-frames-on-demand.md), [ADR-0007](https://github.com/SamuelZ12/vidscribe/blob/v1/docs/decisions/0007-overview-sheets.md) and [ADR-0008](https://github.com/SamuelZ12/vidscribe/blob/v1/docs/decisions/0008-full-sheets.md). Removes the contact sheets of [ADR-0005](0005-no-ocr.md).

## Date
2026-11-22

## Context
vidscribe gave agents two things: a transcript, and its own ways to see the picture (overview sheets, `-v N`, `--at` and `--scan`). Every earlier test compared those commands with a transcript-only agent or with older versions of themselves. None compared them with an agent that runs `ffmpeg` on the video file.

The [benchmark](../benchmark.md) made that comparison with Codex and `gpt-6.2-sol` at medium effort:

- On all 144 questions of Video-Index v1.1, with three runs each, transcript + plain `ffmpeg` scored 3.0 points below vidscribe (−7.2 to +0.9) at 3.1 cents less per question.
- On 12 long talks (108 questions, one run), it scored 0.5 points below vidscribe (−3.2 to +2.3) at 30% less cost.
- A seven-step guidance file for `ffmpeg` raised cost and did not raise scores.

The transcript is the part that helped. On the long talks, an agent without one scored 54% on the questions about what was said, against 100% with it.

## Decision
- Remove overview sheets, `index.txt`, `-v`, `--at` and `--scan`. `-v`, `--at` and `--scan` now exit with a message pointing here.
- A txt or srt run on a video writes srt + txt and prints `video: <path>` to stderr. Downloads move to `/tmp/vidscribe/videos/` and are pruned after 3 days. There is no setting for that folder, so pruning never touches a folder the user chose. A local file is used where it is.
- `skill/SKILL.md` tells agents to transcribe, look with `ffmpeg` on the printed path, and answer from evidence. It gives no `ffmpeg` method, since the guidance file did not help.
- The last commit with the picture commands is tagged `v1`.

## Alternatives considered
- **Keep the commands, change the default.** Keeps code and skill text that measured no benefit, and skill text steers agents toward them.
- **Write an `ffmpeg` guidance skill.** Tested as `ffmpeg-guided`: +2.8 points (−1.4 to +6.9) at 3.3 cents more per question on Video-Index, 0.0 on the long talks.

## Consequences
- The script goes from 366 to 175 lines, and video runs no longer spend time making sheets.
- Anyone calling `-v`, `--at` or `--scan` gets an error. They can check out `v1`.
- The evidence covers one agent and model. A model that uses `ffmpeg` less well may have needed the sheets. On the 36 hard long-talk questions about moments the speech never names, plain `ffmpeg` scored 94.4% against 100%, within noise.
