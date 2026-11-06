# vidscribe

Local speech-to-text and video frame capture for AI agents, on Apple Silicon. Give it a file or a URL (YouTube, X, podcasts, anything yt-dlp handles) and it returns a transcript. For video it also saves key frames plus an `index.txt` that maps each frame to what was being said, so an agent can actually "watch" the video.

Transcription runs on-device with [MLX](https://github.com/ml-explore/mlx). No API keys, no cloud service; the network is only used to download the model once and to fetch URLs.

## Does it help?

Agents answered questions about videos and a blind grader scored them against reference answers (method and per-video results in [`docs/measurements.md`](docs/measurements.md); questions, grades and scripts in [`eval/`](eval/), videos rebuildable from their YouTube IDs):

| Test | Transcript only | + frames | + `--at` | + `--scan` |
|---|---|---|---|---|
| 12 clips, 2-111 min, 48 questions | 13 | 33 | | |
| 12 long videos, 39-111 min, 72 questions anchored on speech | | 37.5 | 69 | |
| Same 12 videos, 36 questions on moments the speech never names | | 11 | 31 | 36 |

Frames more than double what an agent gets right; [Omni2Web](https://arxiv.org/html/2609.23417) saw a similar jump on its instruction-recovery track (Gemini 3.5 Flash on screen-recorded web edits: transcript only 18.2, silent video + transcript 38.1). Caveats: the last row's questions were kept only if a transcript-only agent failed them; the `--scan` gain is optimistic (tuned on the 5 questions `--at` missed; a 4-video holdout scored 12/12 with and without it, [#2](https://github.com/SamuelZ12/vidscribe/issues/2)); scores were measured with the [`55c8e8b`](https://github.com/SamuelZ12/vidscribe/blob/55c8e8b/skill/SKILL.md) wording of `skill/SKILL.md`, and the current one has not been re-tested ([#1](https://github.com/SamuelZ12/vidscribe/issues/1)).

## Requirements

- A Mac with Apple Silicon (M1 or later). Intel Macs and Linux are not supported: MLX needs Apple Silicon.
- [Homebrew](https://brew.sh), used by `install.sh` for the tools below.
- `uv`, `ffmpeg` (with `ffprobe`), `yt-dlp` and [`mlx-audio`](https://github.com/Blaizzy/mlx-audio). `install.sh` installs all four.
- `python3` on `PATH` for frame selection (standard library only; the one from Xcode Command Line Tools, which Homebrew needs anyway, is enough).
- About 2.5 GB of disk for the default model, downloaded from Hugging Face on the first run.

## Install

```sh
git clone https://github.com/SamuelZ12/vidscribe.git
cd vidscribe && ./install.sh
```

`install.sh` runs `brew install uv ffmpeg yt-dlp`, `uv tool install --force mlx-audio --prerelease=allow`, then symlinks `bin/vidscribe` into `~/.local/bin`. Make sure `~/.local/bin` is on your `PATH`.

To install by hand instead, run those two commands yourself and put `bin/vidscribe` anywhere on your `PATH`. The script looks for `mlx_audio.stt.generate` (from `uv tool install`) on `PATH` and also adds `~/.local/bin` and `/opt/homebrew/bin` itself.

Update with `git pull` in the clone (the symlink follows it). Uninstall with `rm ~/.local/bin/vidscribe` and `uv tool uninstall mlx-audio`; the model stays in the Hugging Face cache (`~/.cache/huggingface`) until you delete it.

## Quick start

```sh
vidscribe talk.mp4                                  # transcript to stdout, plus frames for video
vidscribe "https://www.youtube.com/watch?v=<id>"    # any URL yt-dlp handles
vidscribe memo.m4a -f srt -o ~/transcripts          # srt, kept outside /tmp
vidscribe "https://www.youtube.com/watch?v=<id>" -a # transcript only, audio download only
vidscribe /tmp/vidscribe/frames/<name> --at 8:14,7:50-8:50   # more frames from a previous run
vidscribe /tmp/vidscribe/frames/<name> --scan 50:00-60:00   # contact sheets to find an unnamed moment
```

The transcript path is printed to stderr as `transcript: <path>`; frame runs also print `frames: <dir> (...)`.

## Usage

```
vidscribe <file-or-URL> [-o DIR] [-l LANG] [-f txt|srt|vtt|json] [-c "hotwords"] [-m MODEL] [-v [N] | -a]
vidscribe <frames-dir> --at TIMES | --scan RANGES|all
vidscribe -h | --help
```

- Video gets frames by default (at most 40, or N if `-v N` asks for more) plus `index.txt`, mapping each frame to what was being said; `-a` gives a transcript only, `-v N` sets the number of evenly spaced frames (default 8).
- `--at` pulls more frames from a previous run's video; `--scan` builds contact sheets to find a moment the speech never names.
- Outputs live in `/tmp/vidscribe/` for 3 days.

Full reference (frame selection, `index.txt` format, `--at`/`--scan` output, environment variables): [`docs/usage.md`](docs/usage.md).

## Model

Default: `mlx-community/Qwen3-ASR-1.7B-8bit` via [mlx-audio](https://github.com/Blaizzy/mlx-audio). It beats Whisper large-v3 on most published benchmarks and is strong on Mandarin. For languages outside its ~30, use `-m mlx-community/whisper-large-v3-turbo-asr-fp16`.

## Agent skill

`skill/SKILL.md` teaches agents (Claude Code, Codex, Cursor and [others](https://github.com/vercel-labs/skills#supported-agents)) when and how to use vidscribe. Install it from your project with [`npx skills`](https://github.com/vercel-labs/skills) (Node.js 22.20+):

```sh
npx skills add SamuelZ12/vidscribe
```

Without Node, copy the `skill/` folder into your agent's skills directory (for Claude Code, `.claude/skills/vidscribe`).

## Not built

- **A hosted video model** (e.g. Gemini behind a flag): paid, and it sends media off the device ([ADR-0001](docs/decisions/0001-local-only.md)).
- **OCR of on-screen text into `index.txt`**: with `--at`, agents answered 31/36 questions about moments the speech never names, above the bar set beforehand ([ADR-0005](docs/decisions/0005-no-ocr.md)).
- **Smarter scene choice within the 40-frame cap**: two methods were tried on long videos and neither improved answers; fetching frames on demand did ([ADR-0004](docs/decisions/0004-frames-on-demand.md)).
- **Word timestamps (forced aligner)**: at most 1 of 72 misses came from frame timing, and the aligner covers only 11 languages ([measurements](docs/measurements.md#word-timestamps-forced-aligner-not-built)).

Why the shipped defaults are what they are: [`docs/decisions/`](docs/decisions/).

## License

vidscribe is MIT ([`LICENSE`](LICENSE)). It doesn't ship model weights; they download from Hugging Face on first use, under their own licenses:

| Model | License |
|---|---|
| `mlx-community/Qwen3-ASR-1.7B-8bit` (default), converted from [`Qwen/Qwen3-ASR-1.7B`](https://huggingface.co/Qwen/Qwen3-ASR-1.7B) | Apache 2.0 |
| `mlx-community/whisper-large-v3-turbo-asr-fp16` (`-m`), converted from OpenAI's [`whisper-large-v3-turbo`](https://huggingface.co/openai/whisper-large-v3-turbo) | MIT (the original's; the MLX copy states none) |

[mlx-audio](https://github.com/Blaizzy/mlx-audio) is MIT; `ffmpeg` and `yt-dlp` are installed separately under their own licenses.
