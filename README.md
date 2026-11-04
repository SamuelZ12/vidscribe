# vidscribe

Local speech-to-text and video frame capture for AI agents, on Apple Silicon. Give it a file or a URL (YouTube, X, podcasts, anything yt-dlp handles) and it returns a transcript. With `-v` it also saves key video frames plus an `index.txt` that maps each frame to what was being said, so an agent can actually "watch" the video.

Everything runs on-device. No API keys.

## Install

Requires an Apple Silicon Mac and Homebrew.

```sh
git clone https://github.com/SamuelZ12/vidscribe.git
cd vidscribe && ./install.sh
```

This installs `uv`, `ffmpeg`, `yt-dlp`, and `mlx-audio`, then symlinks `bin/vidscribe` into `~/.local/bin`. The first run downloads the model (~2.5 GB).

## Usage

```
vidscribe <file-or-URL> [-o DIR] [-l LANG] [-f txt|srt|vtt|json] [-c "hotwords"] [-m MODEL] [-v [N]]
```

- Transcripts go to `/tmp/vidscribe/transcripts/<name>.<fmt>`; txt is also printed to stdout. Use `-o DIR` to keep them elsewhere.
- `-v [N]`: visual mode. Writes srt + txt, saves N evenly spaced frames (default 8) and a frame at every spoken on-screen reference ("look at this", "as you can see", 你看...). Output: `/tmp/vidscribe/frames/<name>/` with `index.txt` (time, frame, spoken text).
- `-l zh|en|...` forces a language; `-c "Letta, Qwen"` biases rare names.
- A `WARNING: last cue ... < duration` line means the model stopped early; re-run on the tail.
- Old outputs in `/tmp/vidscribe` are pruned after 3 days.

Env overrides: `VIDSCRIBE_MODEL`, `VIDSCRIBE_OUTDIR`, `VIDSCRIBE_FRAMES_DIR`.

## Model

Default: `mlx-community/Qwen3-ASR-1.7B-8bit` via [mlx-audio](https://github.com/Blaizzy/mlx-audio). It beats Whisper large-v3 on most published benchmarks and is strong on Mandarin. For languages outside its ~30, use `-m mlx-community/whisper-large-v3-turbo-asr-fp16`.

## Agent skill

`skill/SKILL.md` is a drop-in skill for Claude Code, Letta Code, and other agents that read SKILL.md files.

## License

MIT
