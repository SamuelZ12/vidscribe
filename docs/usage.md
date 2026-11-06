# Usage

```
vidscribe <file-or-URL> [-o DIR] [-l LANG] [-f txt|srt|vtt|json] [-c "hotwords"] [-m MODEL] [-v [N] | -a]
vidscribe <frames-dir> --at TIMES | --scan RANGES|all
vidscribe -h | --help
```

- Transcripts go to `/tmp/vidscribe/transcripts/<name>.<fmt>`; txt is also printed to stdout. Use `-o DIR` to keep them elsewhere.
- Frames are on by default when the input has a video stream (checked with ffprobe; URLs are downloaded as video, up to 720p). Audio files, including mp3/m4a with cover art, give a transcript only.
- Frame mode writes srt + txt and saves N evenly spaced frames (default 8), a frame at every spoken on-screen reference ("look at this", "as you can see", 你看...), and a frame at the end of each distinct scene (ffmpeg cut detection; repeated shots like a return to the same slide are dropped). At most 40 frames in total (or N, if `-v N` asks for more): on long videos reference and scene frames share the room and are thinned out evenly (see [`measurements.md`](measurements.md)). Output: `/tmp/vidscribe/frames/<name>/` with `index.txt`, one tab-separated line per frame: frame time, frame file (`_even`, `_ref` or `_scene`), start-end of the spoken text, spoken text (`-` and empty text where nothing is being said).
- If the picture ends before the audio, frames past its end are left out (even frames are not respaced over the shorter picture) and stderr shows `frames: no picture at N of M times (...), left out`; e.g. a 3 s picture with 9.2 s of speech gets 1 even frame instead of 5. If you hit this on a real file, add it to [#3](https://github.com/SamuelZ12/vidscribe/issues/3).
- `-v [N]`: force frame mode, with N evenly spaced frames. `-a`/`--audio-only`: transcript only, never download or save video. `-f vtt|json` on a video without `-v` also gives a transcript only.
- The language is detected separately in every ~30 s piece, so mixed-language media and music breaks need no flag. `-l zh|hi|en|...` (or the full name, `-l Chinese`) forces one language: use `-l en` for Hindi or other speech mixed with English terms to keep those terms in Latin script. `-c "Letta, Qwen"` biases rare names; `-m` picks another mlx-audio model.
- Long media is transcribed to the end. Applause or music can show up as a short run of one repeated word ("oh, oh, oh"). `warning: transcript cut off in 00:12:03-00:12:09` means the model got stuck there (almost always such a loop): that stretch keeps only its first words, and the rest of the file is unaffected. A `WARNING: last cue ... < duration` line means the transcript ends before the media does: either the model stopped early or there is no speech near the end.
- Old outputs in `/tmp/vidscribe` are pruned after 3 days.

## Frames on demand (`--at`)

The frames folder also holds `video.<ext>`: the downloaded video for URLs, a symlink to the original for local files. `vidscribe <frames-dir> --at 494,8:14,7:50-8:50` pulls more frames from it without transcribing again: one per time, 4 evenly spaced inside each range (seconds, `M:SS` or `H:MM:SS`, fractions with a dot). Frames are saved as `at_<mm>m<ss.s>s.jpg` in the same folder and each prints as `mm:ss.s<TAB>path`; `index.txt` is left as is. `--at` takes no other flags, and fails once the folder has been pruned: re-run on the source.

## Contact sheets (`--scan`)

`vidscribe <frames-dir> --scan 50:00-60:00` (several ranges with commas, or `all`) helps find a moment the transcript never leads to. Each range becomes 4x4 contact sheets, 1280x720, saved as `scan_<start>-<end>_NN.jpg` in the frames folder: one tile at the end of each scene (the same cut detection as frame mode) plus evenly spaced tiles so no two are more than 10 s apart. Stderr gives the tile and sheet count per range; stdout prints one line per sheet, `path<TAB>` then the tile times in reading order. A 10-min range is typically 5-8 sheets; scene detection takes ~7 s per 10 min of video. Tiles are too small for reliable reading: confirm with `--at` at the tile's time. Same rules as `--at`: ranges only, no other flags, fails once the folder is pruned. Probe and sizing in [`measurements.md`](measurements.md), "Scan probe".

## Environment

- `VIDSCRIBE_MODEL`: default model (same as `-m`).
- `VIDSCRIBE_OUTDIR`: transcript folder (same as `-o`).
- `VIDSCRIBE_FRAMES_DIR`: frames root instead of `/tmp/vidscribe/frames`.
