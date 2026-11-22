# ADR-0008: Every overview sheet is full

## Status
Superseded by [ADR-0009](0009-drop-picture-commands.md). Amends the tile count of [ADR-0007](0007-overview-sheets.md); the rest of ADR-0007 stands.

## Date
2026-11-15

## Context
A video run saves overview sheets: 4x4 contact sheets of evenly spaced tiles ([ADR-0007](0007-overview-sheets.md)). The tile count was one per 10 s of picture, at least 16 and at most 96, so the last sheet was often part empty. An empty slot is padded white and the sheet stays 1280x720, so a part-empty sheet costs an agent the same image tokens as a full one.

Of the 21 videos in the [overview-sheets eval](../measurements.md#overview-sheets-against-the-current-default-frames), 6 ended on a part-empty sheet; the emptiest had 4 tiles and 12 blanks (an 8:37 video, 52 tiles). The owner's 3:33 test video got 22 tiles: one full sheet and a second with 6 tiles.

## Decision
- Sheets = picture length / 160 s, rounded to the nearest whole number (a half rounds up), at least 1 and at most 6.
- Tiles = 16 x sheets, evenly spaced, each in the middle of its share, as before.

| Picture length | Sheets | Tiles | Seconds per tile | Tiles before |
|---|---|---|---|---|
| under 2:40 | 1 | 16 | under 10 | 16 (unchanged) |
| 2:40 to 3:59 | 1 | 16 | 10 to 15 | 16 to 24 |
| 4:00 to 6:39 | 2 | 32 | 7.5 to 12.5 | 24 to 40 |
| 6:40 to 9:19 | 3 | 48 | 8.3 to 11.7 | 40 to 56 |
| 9:20 to 11:59 | 4 | 64 | 8.75 to 11.25 | 56 to 72 |
| 12:00 to 14:39 | 5 | 80 | 9 to 11 | 72 to 88 |
| 14:40 to 15:59 | 6 | 96 | 9.2 to 10 | 88 to 96 |
| 16:00 and over | 6 | 96 | 10 or more | 96 (unchanged) |

`-v N`, `--at`, `--scan`, the tile size, the sheet layout and the format of `index.txt` do not change.

## Alternatives considered
- **Round up to the next sheet.** Up to 16:00, tiles would never be more than 10 s apart, but a 2:41 video would get 32 tiles where it got 17, and the 3:33 video 32 where it got 22. The owner chose nearest: the count stays closest to one tile per 10 s.
- **Crop a part-empty sheet to the rows it uses.** Not built: sheets would come in four sizes, and it is not needed once every sheet is full.
- **Fill `--scan` sheets too.** Not built: their tile count comes from scene changes plus a 10 s fill, not from a formula.

## Consequences
- Videos under 2:40 and of 16:00 or more get the same tiles as before (`index.txt` identical on a 150 s and a 1000 s clip). In between, the count moves by up to 8 tiles either way: clips of 239, 241, 401 and 881 s went from 24, 25, 41 and 89 tiles to 16, 32, 48 and 96. Transcripts are byte-identical on all six test clips.
- From 2:40 to 3:59 a video gets 16 tiles where it got up to 24, so tiles are up to 15 s apart there. From 4:00 to 16:00 they are 7.5 to 12.5 s apart. `--scan` still covers a chosen stretch at 10 s or closer.
- The eval ran with the old counts. Under the new rule 15 of its 21 videos get the same tiles: the 12 long ones (96), and clips of 1:39, 2:07 and 5:18. The other six clips change by 1 to 5 tiles (37 to 32, 44 to 48, 47 to 48, 52 to 48, 61 to 64, 79 to 80), and two of them get one sheet fewer. Its sheets arm was [run again](../measurements.md#re-run-of-the-vidscribe-arm-with-the-shipped-script) with the new counts: the six clips scored 24 of 24, as they did with the old counts.
- A last sheet can still be part empty in two cases: the picture is shorter than the audio, so tiles past its end are left out ([#3](https://github.com/SamuelZ12/vidscribe/issues/3)), and `--scan` sheets.
