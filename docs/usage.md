# Usage

```
vidscribe <file-or-URL> [-o DIR] [-l LANG] [-f txt|srt|vtt|json] [-c "hotwords"] [-m MODEL] [-a]
vidscribe -h | --help
```

- Transcripts go to `/tmp/vidscribe/transcripts/<name>.<fmt>`; txt is also printed to stdout. Use `-o DIR` to keep them elsewhere.
- A video input (a video stream, checked with ffprobe; URLs are downloaded as video, up to 720p) writes srt + txt and prints `video: <path>` to stderr, so an agent can look at the picture with `ffmpeg`. Downloaded videos are saved as `/tmp/vidscribe/videos/<id>.<ext>`; a local file is used where it is. Audio files, including mp3/m4a with cover art, give a transcript only.
- A video with no audio track gets empty srt and txt files and its video path. Transcript-only runs require audio.
- `-a`/`--audio-only`: transcript only; URLs ask yt-dlp for audio only. `-f vtt|json` also gives a transcript only.
- `-v`, `--at` and `--scan` were removed in November 2026 ([ADR-0009](decisions/0009-drop-picture-commands.md)). To keep using them, check out the `v1` tag.
- The language is detected separately in every ~30 s piece, so mixed-language media and music breaks need no flag. `-l zh|hi|en|...` (or the full name, `-l Chinese`; Whisper takes only the code) forces one language: use `-l en` for Hindi or other speech mixed with English terms to keep those terms in Latin script. `-c "Letta, Qwen"` biases rare names; `-m` picks another mlx-audio model.
- Long media is transcribed to the end. Applause or music can show up as a short run of one repeated word ("oh, oh, oh"). `warning: transcript cut off in 00:12:03-00:12:09` means the model got stuck there (almost always such a loop): that stretch keeps only its first words, and the rest of the file is unaffected. A `WARNING: last cue ... < duration` line means the transcript ends before the media does: either the model stopped early or there is no speech near the end.
- Old outputs in `/tmp/vidscribe` (transcripts, videos, and v1's frames folders) are pruned after 3 days, checked at the start of each run.

## Install

Requirements: an Apple Silicon Mac (M1 or later; MLX doesn't run on Intel or Linux), `uv`, `ffmpeg` (with `ffprobe`), `yt-dlp`, [`mlx-audio`](https://github.com/Blaizzy/mlx-audio), and `python3` to write the txt transcript of a video (standard library only; the Xcode Command Line Tools one is enough).

`install.sh` runs `brew install uv ffmpeg yt-dlp` and `uv tool install --force mlx-audio --prerelease=allow`, then symlinks `bin/vidscribe` into `~/.local/bin`. To install by hand, run those two commands and put `bin/vidscribe` anywhere on your `PATH`; the script finds `mlx_audio.stt.generate` on `PATH` and also adds `~/.local/bin` and `/opt/homebrew/bin` itself.

Uninstall: `rm ~/.local/bin/vidscribe` and `uv tool uninstall mlx-audio`. The model stays in the Hugging Face cache (`~/.cache/huggingface`) until you delete it.

## Environment

- `VIDSCRIBE_MODEL`: default model (same as `-m`).
- `VIDSCRIBE_OUTDIR`: transcript folder (same as `-o`).

## Licenses

`mlx-community/Qwen3-ASR-1.7B-8bit` (default) is converted from [`Qwen/Qwen3-ASR-1.7B`](https://huggingface.co/Qwen/Qwen3-ASR-1.7B), Apache 2.0. `mlx-community/whisper-large-v3-turbo-asr-fp16` is converted from OpenAI's [`whisper-large-v3-turbo`](https://huggingface.co/openai/whisper-large-v3-turbo), MIT (the original's; the MLX copy states none). `ffmpeg` and `yt-dlp` come under their own licenses.
