# vidscribe

Lets AI agents watch videos, locally on Apple Silicon. Give it a file or any URL yt-dlp handles; it returns a transcript and, for video, overview sheets (small, evenly spaced pictures) with an `index.txt` mapping each one to what was being said. The agent then fetches full-size frames at the moments that matter. Runs on-device with [MLX](https://github.com/ml-explore/mlx): no API keys, no cloud.

## Does it help?

Agents answered 156 questions about 21 videos, 36 of them about moments the speech never names: once from the transcript alone, once with vidscribe (overview sheets, `--at` and `--scan`). A blind grader scored the answers.

| | Transcript only | vidscribe |
|---|---|---|
| Score | 15% | 98% |

Method and caveats: [docs/measurements.md](docs/measurements.md#overview-sheets-against-the-current-default-frames). Questions, grades and scripts: [eval/](eval/).

## Install

Needs an Apple Silicon Mac and [Homebrew](https://brew.sh). The default model (~2.5 GB) downloads on first run.

```sh
git clone https://github.com/SamuelZ12/vidscribe.git
cd vidscribe && ./install.sh
```

Make sure `~/.local/bin` is on your `PATH`, then check with `vidscribe -h`. Update with `git pull`. Manual install and uninstall: [docs/usage.md](docs/usage.md#install).

## Usage

```sh
vidscribe talk.mp4                                         # transcript + overview sheets
vidscribe "https://www.youtube.com/watch?v=<id>" -a        # transcript only
vidscribe memo.m4a -f srt -o ~/transcripts                 # srt, kept outside /tmp
vidscribe /tmp/vidscribe/frames/<name> --at 8:14,7:50-8:50 # full-size frames from a run
vidscribe /tmp/vidscribe/frames/<name> --scan 50:00-60:00  # find an unnamed moment
```

txt transcripts print to stdout; the transcript path and frames folder go to stderr. Outputs stay in `/tmp/vidscribe/` for 3 days. The default model is Qwen3-ASR (~30 languages); for others, use `-m mlx-community/whisper-large-v3-turbo-asr-fp16`. Full reference: [docs/usage.md](docs/usage.md).

## Agent skill

```sh
npx skills add SamuelZ12/vidscribe
```

Needs Node.js 22.20+. Without Node, copy `skill/` into your agent's skills folder (Claude Code: `.claude/skills/vidscribe`).

## Limits

- Speech only: music and other sounds aren't described.
- No OCR or word timestamps; agents read on-screen text from the frames.

Design decisions: [docs/decisions/](docs/decisions/).

## License

MIT. The models, ffmpeg and yt-dlp come under their own licenses: [docs/usage.md](docs/usage.md#licenses).
