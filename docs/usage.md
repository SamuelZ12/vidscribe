# Usage

```
vidscribe <file-or-URL> [-o DIR] [-l LANG] [-f txt|srt|vtt|json] [-c "hotwords"] [-m MODEL] [-v [N] | -a]
vidscribe <frames-dir> --at TIMES | --scan RANGES|all
vidscribe -h | --help
```

- Transcripts go to `/tmp/vidscribe/transcripts/<name>.<fmt>`; txt is also printed to stdout. Use `-o DIR` to keep them elsewhere.
- A video input (a video stream, checked with ffprobe; URLs are downloaded as video, up to 720p) also gets an overview of the picture. Audio files, including mp3/m4a with cover art, give a transcript only.
- A video run writes srt + txt and saves overview sheets: 4x4 contact sheets of 1280x720 named `overview_NN.jpg`, each with 16 evenly spaced tiles. The number of sheets is the picture length divided by 160 s, rounded to the nearest whole number, at least 1 and at most 6, so every sheet is full: 16 tiles up to 3:59, 32 from 4:00, 48 from 6:40, 64 from 9:20, 80 from 12:00 and 96 from 14:40. Tiles are at most 15 s apart on videos up to 24 minutes and further apart on longer ones (a 2-hour video gets a tile every 75 s). Output: `/tmp/vidscribe/frames/<name>/` with the sheets, `video.<ext>` and `index.txt`, one tab-separated line per tile in time order: tile time, `overview_NN.jpg#PP` (`PP` is the tile's position on its sheet, `01`-`16`, left to right, top to bottom), start-end of the spoken text, spoken text (the sentence spoken at that time plus one either side; `-` and empty text where nothing is being said). Stderr reports the count, e.g. `frames: <dir> (48 tiles on 3 sheets, one every 8.4 s)` for a 401 s video. Tiles are too small for reliable reading: get the full frame with `--at` at the tile's time.
- A video with no audio track gets empty srt and txt files. Overview sheets, `-v N`, `--at` and `--scan` use the container duration. Transcript-only runs require audio.
- If the picture ends before the audio, tiles past its end are left out (the rest are not respaced over the shorter picture): they get no row, later tiles move up a position, and stderr shows `frames: no picture at N of M times (...), left out`; e.g. a 3 s picture with 6.9 s of speech gets 7 tiles instead of 16. If you hit this on a real file, add it to [#3](https://github.com/SamuelZ12/vidscribe/issues/3).
- `-v N`: exactly N full-size frames (720 px high, N at least 1), evenly spaced, instead of the overview. They are saved as `NNN_MMmSS.Ss.jpg` and `index.txt` names the frame file in its second column. `-v` alone forces a video run with the overview. `-a`/`--audio-only`: transcript only, never download or save video. `-f vtt|json` on a video without `-v` also gives a transcript only.
- The language is detected separately in every ~30 s piece, so mixed-language media and music breaks need no flag. `-l zh|hi|en|...` (or the full name, `-l Chinese`) forces one language: use `-l en` for Hindi or other speech mixed with English terms to keep those terms in Latin script. `-c "Letta, Qwen"` biases rare names; `-m` picks another mlx-audio model.
- Long media is transcribed to the end. Applause or music can show up as a short run of one repeated word ("oh, oh, oh"). `warning: transcript cut off in 00:12:03-00:12:09` means the model got stuck there (almost always such a loop): that stretch keeps only its first words, and the rest of the file is unaffected. A `WARNING: last cue ... < duration` line means the transcript ends before the media does: either the model stopped early or there is no speech near the end.
- Old outputs in `/tmp/vidscribe` are pruned after 3 days.

## Install

Requirements: an Apple Silicon Mac (M1 or later; MLX doesn't run on Intel or Linux), `uv`, `ffmpeg` (with `ffprobe`), `yt-dlp`, [`mlx-audio`](https://github.com/Blaizzy/mlx-audio), and `python3` for sheets and frames (standard library only; the Xcode Command Line Tools one is enough).

`install.sh` runs `brew install uv ffmpeg yt-dlp` and `uv tool install --force mlx-audio --prerelease=allow`, then symlinks `bin/vidscribe` into `~/.local/bin`. To install by hand, run those two commands and put `bin/vidscribe` anywhere on your `PATH`; the script finds `mlx_audio.stt.generate` on `PATH` and also adds `~/.local/bin` and `/opt/homebrew/bin` itself.

Uninstall: `rm ~/.local/bin/vidscribe` and `uv tool uninstall mlx-audio`. The model stays in the Hugging Face cache (`~/.cache/huggingface`) until you delete it.

## Frames on demand (`--at`)

The frames folder also holds `video.<ext>`: the downloaded video for URLs, a symlink to the original for local files. `vidscribe <frames-dir> --at 494,8:14,7:50-8:50` pulls full-size frames from it without transcribing again: one per time, 4 evenly spaced inside each range, or N with a count after the range (`--at 10:00-20:00/12`; N is 1 to 40). Times are seconds, `M:SS` or `H:MM:SS`, fractions with a dot. Frames are saved as `at_<mm>m<ss.s>s.jpg` in the same folder and each prints as `mm:ss.s<TAB>path`; a time is saved once, so a range shorter than N tenths of a second gives fewer than N frames. `index.txt` is left as is. `--at` takes no other flags, and fails once the folder has been pruned: re-run on the source.

## Contact sheets (`--scan`)

`vidscribe <frames-dir> --scan 50:00-60:00` (several ranges with commas, or `all`) helps find a moment the transcript never leads to. Each range becomes 4x4 contact sheets, 1280x720, saved as `scan_<start>-<end>_NN.jpg` in the frames folder: one tile at the end of each scene (ffmpeg cut detection; repeated shots like a return to the same slide are dropped) plus evenly spaced tiles so no two are more than 10 s apart, then more tiles in the widest gaps until the last sheet is full (a 14 s range gets 16 tiles, not 5 and a mostly blank sheet). Stderr gives the tile and sheet count per range; stdout prints one line per sheet, `path<TAB>` then the tile times in reading order. A 10-min range is typically 5-8 sheets; scene detection takes ~7 s per 10 min of video. Tiles are too small for reliable reading: confirm with `--at` at the tile's time. Same rules as `--at`, except that a range takes no count: ranges only, no other flags, fails once the folder is pruned. Probe and sizing in [`measurements.md`](measurements.md), "Scan probe" and "Scan sheets filled to 16 tiles".

## Environment

- `VIDSCRIBE_MODEL`: default model (same as `-m`).
- `VIDSCRIBE_OUTDIR`: transcript folder (same as `-o`).
- `VIDSCRIBE_FRAMES_DIR`: frames root instead of `/tmp/vidscribe/frames`.

## Licenses

`mlx-community/Qwen3-ASR-1.7B-8bit` (default) is converted from [`Qwen/Qwen3-ASR-1.7B`](https://huggingface.co/Qwen/Qwen3-ASR-1.7B), Apache 2.0. `mlx-community/whisper-large-v3-turbo-asr-fp16` is converted from OpenAI's [`whisper-large-v3-turbo`](https://huggingface.co/openai/whisper-large-v3-turbo), MIT (the original's; the MLX copy states none). `ffmpeg` and `yt-dlp` come under their own licenses.
