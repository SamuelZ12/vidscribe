# vidscribe

Local speech-to-text and video frame capture for AI agents, on Apple Silicon. Give it a file or a URL (YouTube, X, podcasts, anything yt-dlp handles) and it returns a transcript. For video it also saves key frames plus an `index.txt` that maps each frame to what was being said, so an agent can actually "watch" the video.

Transcription runs on-device with [MLX](https://github.com/ml-explore/mlx). No API keys, no cloud service; the network is only used to download the model once and to fetch URLs.

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
```

The transcript path is printed to stderr as `transcript: <path>`; frame runs also print `frames: <dir> (...)`.

## Usage

```
vidscribe <file-or-URL> [-o DIR] [-l LANG] [-f txt|srt|vtt|json] [-c "hotwords"] [-m MODEL] [-v [N] | -a]
vidscribe <frames-dir> --at TIMES
vidscribe -h | --help
```

- Transcripts go to `/tmp/vidscribe/transcripts/<name>.<fmt>`; txt is also printed to stdout. Use `-o DIR` to keep them elsewhere.
- Frames are on by default when the input has a video stream (checked with ffprobe; URLs are downloaded as video, up to 720p). Audio files, including mp3/m4a with cover art, give a transcript only.
- Frame mode writes srt + txt and saves N evenly spaced frames (default 8), a frame at every spoken on-screen reference ("look at this", "as you can see", 你看...), and a frame at the end of each distinct scene (ffmpeg cut detection; repeated shots like a return to the same slide are dropped). At most 40 frames in total (or N, if `-v N` asks for more): on long videos reference and scene frames share the room and are thinned out evenly (see `MEASUREMENTS.md`). Output: `/tmp/vidscribe/frames/<name>/` with `index.txt`, one tab-separated line per frame: frame time, frame file (`_even`, `_ref` or `_scene`), start-end of the spoken text, spoken text (`-` and empty text where nothing is being said).
- `-v [N]`: force frame mode, with N evenly spaced frames. `-a`/`--audio-only`: transcript only, never download or save video. `-f vtt|json` on a video without `-v` also gives a transcript only.
- `-l zh|en|...` forces a language; `-c "Letta, Qwen"` biases rare names; `-m` picks another mlx-audio model.
- Long media is transcribed to the end. Applause or music can show up as a short run of one repeated word ("oh, oh, oh"). A `WARNING: last cue ... < duration` line means the transcript ends before the media does: either the model stopped early or there is no speech near the end.
- Old outputs in `/tmp/vidscribe` are pruned after 3 days.

### Frames on demand (`--at`)

The frames folder also holds `video.<ext>`: the downloaded video for URLs, a symlink to the original for local files. `vidscribe <frames-dir> --at 494,8:14,7:50-8:50` pulls more frames from it without transcribing again: one per time, 4 evenly spaced inside each range (seconds, `M:SS` or `H:MM:SS`, fractions with a dot). Frames are saved as `at_<mm>m<ss.s>s.jpg` in the same folder and each prints as `mm:ss.s<TAB>path`; `index.txt` is left as is. `--at` takes no other flags, and fails once the folder has been pruned: re-run on the source.

### Environment

- `VIDSCRIBE_MODEL`: default model (same as `-m`).
- `VIDSCRIBE_OUTDIR`: transcript folder (same as `-o`).
- `VIDSCRIBE_FRAMES_DIR`: frames root instead of `/tmp/vidscribe/frames`.

## Model

Default: `mlx-community/Qwen3-ASR-1.7B-8bit` via [mlx-audio](https://github.com/Blaizzy/mlx-audio). It beats Whisper large-v3 on most published benchmarks and is strong on Mandarin. For languages outside its ~30, use `-m mlx-community/whisper-large-v3-turbo-asr-fp16`.

## Agent skill

`skill/SKILL.md` is a drop-in skill for Claude Code, Letta Code, and other agents that read SKILL.md files. Copy or symlink the `skill/` folder into your agent's skills directory (for Claude Code, `~/.claude/skills/vidscribe`).

## Measurements and eval

`MEASUREMENTS.md` records how the frame defaults were chosen and how agents score with and without frames and `--at`. `eval/` holds the question set, reference answers, grades, prompts and helper scripts; the videos are not in git and can be rebuilt from their YouTube IDs (see `eval/README.md`).

## License

MIT
