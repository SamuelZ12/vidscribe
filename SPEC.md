# Spec: Full overview sheets (V1)

Status: approved 2026-11-15, not built yet. Plan: `tasks/plan.md`.

## Objective

A video run saves overview sheets: 4x4 contact sheets of evenly spaced tiles ([ADR-0007](docs/decisions/0007-overview-sheets.md)). Today the tile count is one per 10 s of picture, between 16 and 96, so the last sheet is often part empty. An empty slot is padded white and the sheet stays 1280x720, so it costs an agent the same image tokens as a full sheet. In the overview-sheets eval, 6 of 21 videos ended on a padded sheet; one had 4 tiles on it. A 3:33 video gets 22 tiles: one full sheet and a second with 6 tiles and 10 blanks.

Change the tile count so every overview sheet is full, and a video gets the number of sheets nearest to one tile per 10 s.

Users: agents that read the sheets (through `skill/SKILL.md`), and the owner.

### New rule

- Sheets = picture length / 160 s, rounded to the nearest whole number (a half rounds up), at least 1 and at most 6.
- Tiles = 16 x sheets, evenly spaced, each in the middle of its share, as now.

| Picture length | Sheets | Tiles | Seconds per tile | Tiles today |
|---|---|---|---|---|
| under 2:40 | 1 | 16 | under 10 | 16 (unchanged) |
| 2:40 to 3:59 | 1 | 16 | 10 to 15 | 16 to 24 |
| 4:00 to 6:39 | 2 | 32 | 7.5 to 12.5 | 24 to 40 |
| 6:40 to 9:19 | 3 | 48 | 8.3 to 11.7 | 40 to 56 |
| 9:20 to 11:59 | 4 | 64 | 8.8 to 11.3 | 56 to 72 |
| 12:00 to 14:39 | 5 | 80 | 9 to 11 | 72 to 88 |
| 14:40 to 15:59 | 6 | 96 | 9.2 to 10 | 88 to 96 |
| 16:00 and over | 6 | 96 | over 10 | 96 (unchanged) |

"Picture length" is the length the script already spaces tiles over (`FDUR` in `bin/vidscribe`).

## Tech Stack

Unchanged: `bin/vidscribe`, a bash script that must run under `/bin/bash` 3.2.57, with embedded python3 (standard library only) and ffmpeg. No new dependency.

## Commands

```
Run:            /bin/bash bin/vidscribe <video-or-url> -f srt
Count formula:  python3 -c 'import math; print([16*min(6, max(1, math.floor(d/160 + 0.5))) for d in (150, 239, 240, 399, 400, 879, 880, 960, 7200)])'
Test clip:      ffmpeg -nostdin -loglevel error -y -i /tmp/vsov/src/Unzc731iCUY.mp4 -t <seconds> -c copy /tmp/vs_smoke/full_<seconds>.mp4
Sheet size:     ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0 <dir>/overview_NN.jpg
```

Smoke runs use a copy of the script in `/tmp`, never the file being edited.

## Project Structure

```
bin/vidscribe                         the count (one line) and three comments
docs/decisions/0008-full-sheets.md    new ADR; 0007 and the ADR index get a pointer to it
docs/usage.md                         the sentence that states the tile count
skill/SKILL.md                        step 3, the same sentence for agents
docs/measurements.md                  a note under "Overview sheets": the eval ran with the old counts
```

`README.md` does not state the tile count and stays as it is.

## Code Style

The count stays one line next to the `-v N` branch, in the script's existing style:

```python
# overview: 16 tiles per sheet, one sheet per 160 s of picture rounded to the nearest (1 to 6), so every sheet is full;
if not full: n = 16 * min(6, max(1, math.floor(dur/160 + 0.5)))
```

`math.floor(x + 0.5)`, not `round()`: Python's `round()` sends 1.5 and 2.5 both to 2, which would give a 4:00 and a 6:40 video the same two sheets.

Docs use plain words and exact numbers, as the existing docs do.

## Testing Strategy

The repo has no test harness; changes are checked with real runs.

1. Formula: the `Count formula` command prints `[16, 16, 32, 32, 48, 80, 96, 96, 96]`.
2. Real runs under `/bin/bash` on clips cut from an eval video already on disk, at 150, 239, 241, 401, 881 and 1000 s. For each, compare the `frames:` line and the files with the table above.
3. One run of the owner's test video (`https://youtu.be/dQw4w9WgXcQ`, 3:33).
4. Unchanged paths, compared with master's output on the same input: `-v 5`, `-a`, an audio file, `--at`, `--scan`.

About 3 minutes of transcription in all, plus one small download for step 3.

## Boundaries

- Always: run under `/bin/bash` 3.2; transcripts stay byte-identical to master; test from a `/tmp` copy; commit with Conventional Commits, subject at most 50 characters.
- Ask first: every push; any agent run or benchmark; any download other than the step 3 video; deleting scratch data.
- Never: commit videos or transcripts; change `-v N`, `--at`, `--scan`, the tile size or the sheet layout.

## Success Criteria

1. For every clip in test step 2, the `frames:` line reports the table's tile and sheet counts (16/1, 16/1, 32/2, 48/3, 96/6, 96/6), `index.txt` has exactly that many lines, and the last `overview_NN.jpg` has 16 tiles.
2. The 3:33 test video gives `16 tiles on 1 sheet` (22 tiles on 2 sheets today).
3. Videos under 2:40 and of 16:00 or more give the same tiles as master (same `index.txt`).
4. `.srt` and `.txt` are byte-identical to master for every test input.
5. `-v 5`, `-a`, an audio file, `--at` and `--scan` give the same output as master.
6. `docs/usage.md`, `skill/SKILL.md` and the script's comments state the new rule and no longer say "one per 10 s"; ADR-0008 records the decision and that the eval ran with the old counts.

## Out of Scope (Deferred)

- **Full `--scan` sheets.** Their tile count comes from scene changes plus a 10 s fill, not a formula; the last sheet of a range can still be part empty.
- **Picture shorter than the audio** (issue #3). Tiles past the picture's end are still left out, so the last sheet can be part empty there.
- **Cropping a part-empty sheet to the rows it uses.** Not needed once overview sheets are full.
- **Re-running the eval with the new counts.** The 12 long eval videos keep 96 tiles; the short clips change by at most 5 tiles (issue #10 covers a re-run of that arm).

## Decisions (owner, 2026-11-15)

1. **Rounding: nearest sheet.** A video just under 4:00 gets 16 tiles (24 before) and tiles are up to 15 s apart. Rounding up would never go past 10 s but gives the 3:33 video two full sheets (32 tiles); rejected.
2. **ADR: a new short ADR-0008** that amends 0007's tile count.
3. **This file:** `SPEC.md` and `tasks/` are deleted once the change ships, as with the last spec.
