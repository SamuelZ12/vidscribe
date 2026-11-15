# Spec: vidscribe overview sheets — V1

Status: implemented

## Objective

vidscribe lets an AI agent watch a video locally: it returns a transcript and pictures of what is on screen. The user is one person who mostly hands an agent long videos (podcasts, interviews, talks) and asks it to summarise or explain them; short clips are secondary.

Today a video run saves up to 40 full-size frames chosen by three rules (8 evenly spaced, frames where a regex finds speech pointing at the screen, frames at scene ends), sharing a cap. That costs the agent about 48k image tokens per video, clusters frames where cuts are dense, and is the most complicated part of the script. Measurements show that fetching frames on demand (`--at`, `--scan`) carries the score, not the choice of default frames (`docs/measurements.md`, "Table re-run", "Scene choice on long videos").

This version replaces the default frames with a cheap, evenly spaced overview that tells the agent whether the picture matters and where to look, and leaves the looking to the agent's tools.

### Current behaviour (master)

- Video run: `NNN_MMmSS.Ss_{even,ref,scene}.jpg` frames at 720 px height, at most `max(40, N)`, plus `index.txt` (`bin/vidscribe:256-327`).
- `-v N`: N even frames (default 8) plus ref and scene frames up to the cap.
- `--at A-B`: always 4 frames per range.
- `--scan`: 4x4 contact sheets of a range.

### New behaviour

**Default video run** (input has a video stream; no `-a`; `-f txt` or `-f srt`):

- Picture length `D`: unchanged rule. The container length when it exceeds the audio length by more than 1 s, otherwise the audio length.
- Tile count `K = min(96, max(16, ceil(D / 10)))`: one tile per 10 s, at least 16, at most 96.
- Tile times: `D * (i + 0.5) / K` for `i = 0 .. K-1`.
- Tiles go on 4x4 contact sheets with the same geometry as `--scan` (318x178 tiles, 1280x720 sheets), saved as `overview_NN.jpg` (`NN` from `01`) in the frames folder. A last sheet with fewer than 16 tiles is padded white, as `--scan` does.
- `index.txt` has one tab-separated line per tile, in time order: `mm:ss.s`, `overview_NN.jpg#PP`, start-end of the spoken text, spoken text. `PP` is the tile's position on its sheet, `01`-`16`, reading left to right, top to bottom. The text is the sentence spoken at that time plus one sentence either side; `-` and empty text where nothing is spoken.
- A tile with no picture at its time (picture shorter than `D`) is left out: no row, later tiles close the gap, and stderr prints the existing line `frames: no picture at M of K times (first-last), left out`.
- Stderr summary: `frames: <dir> (<k> tiles on <s> sheets, one every <x> s)`, where `k` and `s` count what was saved, `x` is `D / K` with one decimal, and `sheets` is `sheet` when `s` is 1.
- If `D` is 0 or unknown: no tiles, an empty `index.txt`, and `frames: <dir> (no picture length, no tiles)`.
- No scene detection runs in a normal run. The frames folder still holds `video.<ext>`, so `--at` and `--scan` work as before.

**`-v N`**: exactly N evenly spaced full-size frames (720 px height) instead of overview sheets.

- Times: `D * (i + 0.5) / N`. Files: `NNN_MMmSS.Ss.jpg` (no kind suffix). `index.txt`: time, file, span, text, as today.
- Summary: `frames: <dir> (<k> frames, one every <x> s)`, `frame` when `k` is 1.
- `-v 0` exits 1 with `-v N: N must be at least 1`. There is no upper limit.
- Bare `-v` forces a video run with the default overview. `-v` still forces srt + txt and still conflicts with `-a`.

**`--at` range count**: `A-B/N` gives N evenly spaced frames inside the range, at `A + (B - A) * (j + 0.5) / N`.

- `N` is 1 to 40. Without `/N` a range still gives 4.
- `--at: "8:14/3" is a single time: a count needs a range` (exit 1).
- `--at: count in "7:50-8:50/41" must be 1-40` (exit 1).
- `--scan` does not accept `/N` (existing `bad time` error).

**Removed**: ref frames and their regex, scene frames in the main run, the 40-frame cap and its sharing rule, thinning, the 3-second de-duplication rules, the `frames: capped at ...` message, and the `_even`/`_ref`/`_scene` file suffixes.

**Unchanged, byte for byte against master**: audio-only inputs, `-a`, `-f vtt|json` without `-v`, the transcript of every run, `--scan`, and `--at` without `/N`.

Exceptions, made at the owner's request after the eval (2026-11-15):

- `--scan` rounds a time before splitting it into minutes and seconds, so a tile at 839.97 s reads `14:00.0` where master prints `13:60.0`, a time `--at` rejects.
- The `--at` bad-time hint also names the count form: `(use 494, 8:14, 1:02:05, 7:50-8:50 or 7:50-8:50/8)`.

## Tech Stack

- `bin/vidscribe`: one bash script with embedded python3 heredocs. Must run under `/bin/bash` 3.2.57 (macOS).
- python3 standard library only. `ffmpeg`/`ffprobe`, `yt-dlp`, `mlx-audio` (Qwen3-ASR) as today.
- No new dependencies. Local and free tools only. Apple Silicon Mac.

## Commands

```sh
./install.sh                                  # install (brew + uv, symlinks bin/vidscribe)
/bin/bash -n bin/vidscribe                    # syntax check under bash 3.2
vidscribe -h                                  # usage
vidscribe talk.mp4                            # transcript + overview sheets
vidscribe talk.mp4 -v 12                      # transcript + 12 full-size even frames
vidscribe talk.mp4 -a                         # transcript only
vidscribe <frames-dir> --at 8:14,7:50-8:50,10:00-20:00/12
vidscribe <frames-dir> --scan 50:00-60:00
```

There is no build step, linter or test runner. Smoke checks are run by hand from copies in `/tmp` (see Testing Strategy).

## Project Structure

```
bin/vidscribe                   the whole tool
skill/SKILL.md                  instructions for agents using the tool
README.md                       short; detail goes in docs/
docs/usage.md                   full reference
docs/measurements.md            the tests behind the defaults
docs/decisions/NNNN-*.md        one ADR per changed default
eval/                           questions, prompts, grades, scripts; never videos or transcripts
eval/overview/                  new: grades.json, labels.json, cost.json for this change's eval
install.sh
SPEC.md                         this file
```

## Code Style

Match the script as it is: comments say why, not what; durations are compared in awk by exit status and never printed back through awk (its default format truncates them); status goes to stderr, the txt transcript to stdout.

```bash
  # even frames span the picture: use the container length (as --at does) when the video outlasts the audio;
  # sub-second differences are codec padding, so keep the audio length there (normal runs unchanged)
  FDUR="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$VID")"
  awk -v a="$DUR" -v v="${FDUR:-0}" 'BEGIN{ exit !(v + 0 > a + 1) }' || FDUR="$DUR"  # +0: "N/A" (unknown) means 0, not a string compare
```

- bash 3.2 only: no associative arrays, no `mapfile`, expand possibly empty arrays as `${ARR[@]+"${ARR[@]}"}`.
- One sheet-building routine serves both the overview and `--scan`; do not copy it.
- Clean cutover: no flag or fallback that brings the old selector back.
- Commits: Conventional Commits, subject at most 50 characters, no AI attribution.

## Testing Strategy

No test harness. Every case below is run by hand, under `/bin/bash`, from copies in `/tmp/vs_smoke` so the repo script is never edited mid-run.

Fixtures (speech lasts about 9 s; the videos are longer, so the picture length drives the tile count):

```sh
mkdir -p /tmp/vs_smoke && cd /tmp/vs_smoke
say -o speech.aiff "This is a smoke test for vidscribe. The picture shows a test pattern with a running clock. Look at this counter in the corner."
for d in 3 30 200 1000; do
  ffmpeg -nostdin -loglevel error -y -f lavfi -i "testsrc2=size=1280x720:rate=10:duration=$d" -i speech.aiff -c:v libx264 -pix_fmt yuv420p -c:a aac "v$d.mp4"
done
ffmpeg -nostdin -loglevel error -y -i speech.aiff speech.m4a
cp /Users/samuelzhang/dev/vidscribe-overview-sheets/bin/vidscribe vidscribe.new   # the feature worktree
git -C /Users/samuelzhang/dev/vidscribe show master:bin/vidscribe > vidscribe.master
new()    { VIDSCRIBE_OUTDIR=/tmp/vs_smoke/out   VIDSCRIBE_FRAMES_DIR=/tmp/vs_smoke/frames   /bin/bash /tmp/vs_smoke/vidscribe.new "$@"; }
master() { VIDSCRIBE_OUTDIR=/tmp/vs_smoke/out_m VIDSCRIBE_FRAMES_DIR=/tmp/vs_smoke/frames_m /bin/bash /tmp/vs_smoke/vidscribe.master "$@"; }
```

| Case | Command | Expected |
|---|---|---|
| S1 short | `new v30.mp4` | stderr `frames: /tmp/vs_smoke/frames/v30 (16 tiles on 1 sheet, one every 1.9 s)`; one `overview_01.jpg`, 1280x720; `index.txt` has 16 lines |
| S2 medium | `new v200.mp4` | stderr `(20 tiles on 2 sheets, one every 10.0 s)`; `index.txt` has 20 lines, line 1 starts `00:05.0<TAB>overview_01.jpg#01<TAB>`, line 17 starts `02:45.0<TAB>overview_02.jpg#01<TAB>`; `video.mp4` is a symlink; no other jpg files |
| S3 cap | `new v1000.mp4` | stderr `(96 tiles on 6 sheets, one every 10.4 s)`; `index.txt` has 96 lines |
| S4 short picture | `new v3.mp4` | only tiles before 3 s are saved; stderr has `frames: no picture at`; `index.txt` line count equals the tile count in the summary |
| S5 exact frames | `new v200.mp4 -v 5` | stderr `(5 frames, one every 40.0 s)`; files `000_00m20.0s.jpg` to `004_03m00.0s.jpg`, each 720 px high; `index.txt` has 5 lines; no `overview_*.jpg` |
| S6 bad count | `new v200.mp4 -v 0` | exit 1, stderr `-v N: N must be at least 1` |
| S7 range count | `new v200.mp4`, then `new /tmp/vs_smoke/frames/v200 --at 0:10-1:50/8` | 8 stdout lines, first `00:16.3`, last `01:43.8`; `--at 0:10-1:50` still prints 4 lines, first `00:22.5` |
| S8 count errors | `--at 0:30/3`; `--at 0:10-1:50/0`; `--at 0:10-1:50/41`; `--scan 0:10-1:50/8` | each exits 1; stderr contains `a count needs a range`, `must be 1-40`, `must be 1-40`, `bad time` |
| S9 audio | `new speech.m4a`; `master speech.m4a` | `cmp out/speech.txt out_m/speech.txt` is silent; no frames folder made |
| S10 transcript-only video | `-a` and `-f vtt` on `v200.mp4` with both copies | `cmp` of each output pair is silent |
| S11 tools unchanged | on `frames/v200`: `--scan 0:00-3:20` and `--at 0:10,0:20-1:00` with `master`, then `new` | stdout of each command is identical between the two copies |
| S12 old code gone | `rg -c 'DEIX\|thin\(\|capped at\|_even\|_ref\|_scene' bin/vidscribe` | no match |

If two runs of `master` on the same file give different transcripts, S9 and S10 are void: say so instead of reporting a pass.

**Eval** (needs approval before it starts; see Boundaries). One run, at the feature-branch commit, with `skill/SKILL.md` frozen at that commit:

- Sets: `clips` (12 clips, 48 questions, `eval/clips/questions/`), `main` (12 videos, 72 questions, `eval/questions/`), `hard` (the same 12 videos, 36 questions, `eval/hard/questions/`).
- Agents run through the Codex CLI (`codex exec`, `gpt-6.1-sol`, medium effort, default tier), not as Claude `task` subagents like the earlier runs (owner's choice, 2026-11-15, before any agent started). Scores recorded with Claude agents are therefore not baselines for this run: every bar compares two arms of this run.
- Arms, one fresh answer agent per video, set and arm (108 agents), each on all three sets:
  - `transcript`: the `transcript` prompt in `eval/README.md`, "Table re-run".
  - `vidscribe`: the `skill` prompt in `eval/README.md`, "SKILL.md re-test", with the new `SKILL.md` body and the folder description changed to name the overview sheets. Agents may run `--at` and `--scan`.
  - `current`: the same `skill` prompt with master's `SKILL.md`, on frames made by master's script.
- Videos are downloaded and transcribed per `eval/README.md`, "Rebuild"; the time check there applies, and a question whose answer is no longer on screen is dropped from every arm with the denominator shown.
- Same blind grader. Labels are assigned at random and kept out of the agents' folders. Per-agent leakage check as before.
- Recorded per agent, from the image views and commands in its Codex log, not its own report: overview sheets viewed, `at_` frames viewed, scan sheets viewed, and for each visual, mixed or hard answer whether the frame it cites is a full-size frame it opened or only a sheet.
- Bars, fixed now, the same on `clips`, `main` and `hard`:
  - Score: `vidscribe` no more than 2 points below `current`.
  - Wrong answers that are not "unknown": at most `current` + 1.
  - A dropped question is dropped from every arm, so the bars need no adjustment.
  - For reference only: Claude agents with master's `SKILL.md` scored 69 of 72 on `main` (`eval/grades.json` → `skill`) and 33, 34, 34, 34 of 36 on `hard`.
- Outcomes:
  - **All bars met:** ship (success criteria 7-10).
  - **Clips bar fails, others met:** do not ship. Record the result, list the clips that lost points with their lengths, and propose a delta spec for full-size frames on short videos (Open Question 1).
  - **`main` or `hard` fails:** do not ship. Master stays as it is; the result is recorded in `docs/measurements.md`; no ADR.

## Boundaries

- **Always:**
  - Keep the script running under `/bin/bash` 3.2 with python3 standard library only.
  - Run smoke cases and the eval from copies in `/tmp`, never from the repo script while editing it.
  - Record the eval in `docs/measurements.md` and `eval/README.md` whatever the result.
  - Freeze `SKILL.md` and the bars before the eval run.
- **Ask first:**
  - Any download (videos, models) and any agent or eval run, each separately, with its cost stated.
  - Every commit, push and merge.
  - Checking out the feature branch in this checkout: `~/.local/bin/vidscribe` is a symlink into it, so every agent on this Mac would run the branch.
  - Deleting eval data or scratch folders.
- **Never:**
  - Change transcription, download or audio-only behaviour.
  - Add a dependency, or use a paid or hosted service.
  - Commit videos or transcripts.
  - Change the bars, the prompts or `SKILL.md` after the eval run has started.
  - Edit the README results table before the eval result exists.

## Success Criteria

1. Smoke cases S1-S12 pass under `/bin/bash` 3.2.57.
2. A default video run saves only `overview_NN.jpg` sheets, `index.txt` and `video.<ext>`; tile count, times, file names, `index.txt` rows and the summary line match "New behaviour".
3. `-v N` saves exactly N full-size frames and no sheets; `-v 0` is rejected.
4. `--at A-B/N` returns N frames for N from 1 to 40, rejects other counts and single times with a count, and behaves as master without `/N`.
5. Audio-only, `-a` and `-f vtt` outputs, `--scan` output and `--at` output without `/N` are identical to master's (S9-S11).
6. `skill/SKILL.md` tells the agent to: view every overview sheet and use `index.txt` to map a tile to its time and speech; never state on-screen text, numbers or names from a tile, but fetch the full frame with `--at` first; use `--at A-B/N` to choose how many frames a stretch gets; and treat `-v N` as a first-run option only, since a re-run transcribes again and replaces the frames folder. The header comment of `bin/vidscribe`, `vidscribe -h` and `docs/usage.md` describe the new behaviour and no longer mention ref frames, scene frames or the cap.
7. The eval meets every bar in Testing Strategy.
8. `docs/decisions/0007-overview-sheets.md` exists, supersedes ADR-0003 (whose status becomes "Superseded by ADR-0007"), corrects the `-v N` line in ADR-0002 and the "keep the shipped scene selection" line in ADR-0004, and cites the eval. `docs/decisions/README.md` lists it.
9. `README.md` shows one two-column table over all 156 questions, "Transcript only" and "vidscribe", row label "Score", with this run's two percentages. The sentence above it keeps "36 of them about moments the speech never names", and the "Method and caveats" link points at the new measurements section.
10. `docs/measurements.md` has a section for this eval with scores per set and arm, images viewed per video, and the share of on-screen answers confirmed on a full-size frame.

Criteria 8 and 9 are done only if criterion 7 is met.

## Out of Scope (Deferred)

- Summary-style eval prompts graded against a checklist: closer to real use, but more setup and noisier grading; the owner chose the headline eval only.
- Full-size frames by default on short videos: the fallback if the clips bar fails (Open Question 1).
- A ceiling of 160 tiles (10 sheets): the owner chose 96.
- Scene-aware tiles in the overview: evenly spaced tiles are the point of this version; `--scan` already adds scene ends on request.
- Time labels drawn onto tiles: would need ffmpeg's `drawtext` and costs tile pixels; `index.txt` positions cover the mapping.
- A `test/smoke.sh` harness: the owner chose hand-run smoke cases.
- `eval/frames_only.sh`: its pattern no longer matches the script and it extracts nothing; repair or delete it separately.

## Open Questions

None. Answered on 2026-11-15:

1. **Short-video fallback.** If the clips bar fails, the threshold for full-size frames on short videos is picked from the lengths of the clips that lose points, in a follow-up delta spec (not the 2-minute threshold first chosen: the eval clips run 2 to 111 minutes, so it would change none of them).
2. **Where to work.** A separate git worktree, `~/dev/vidscribe-overview-sheets`, on branch `overview-sheets`. The installed `vidscribe` points at the main checkout and stays on master until the merge.
