# vidscribe

Lets AI agents watch videos, locally on Apple Silicon. Give it a file or any URL yt-dlp handles. It returns a transcript and, for video, the path of the video file, so the agent can look at the picture with `ffmpeg`. Videos without an audio track get an empty transcript and the path. Runs on-device with [MLX](https://github.com/ml-explore/mlx): no API keys, no cloud.

## Does it help?

The transcript does. On 12 long talks, an agent with only `ffmpeg` scored 54% on the 12 questions about what was said. With vidscribe's transcript it scored 100%.

vidscribe used to have its own picture commands: overview sheets, `--at` and `--scan`. They did not beat an agent that runs `ffmpeg` on the video file. On the public [Video-Index v1.1](https://github.com/Espere-1119-Song/Video-Index) benchmark, they scored 38.2% and plain `ffmpeg` scored 37.7%, and they cost 23% more per question. So they were removed in November 2026 ([ADR-0009](docs/decisions/0009-drop-picture-commands.md)). The `v1` tag keeps them.

Tables, method, and limits: [docs/benchmark.md](docs/benchmark.md). Every run used Codex with `gpt-6.2-sol`.

## Install

Needs an Apple Silicon Mac and [Homebrew](https://brew.sh). The default model (~2.5 GB) downloads on first run.

```sh
git clone https://github.com/SamuelZ12/vidscribe.git
cd vidscribe && ./install.sh
```

Make sure `~/.local/bin` is on your `PATH`, then check with `vidscribe -h`. Update with `git pull`. Manual install and uninstall: [docs/usage.md](docs/usage.md#install).

## Usage

```sh
vidscribe talk.mp4                                     # transcript; the video path goes to stderr
vidscribe "https://www.youtube.com/watch?v=<id>"       # downloads the video too
vidscribe "https://www.youtube.com/watch?v=<id>" -a    # transcript only
vidscribe memo.m4a -f srt -o ~/transcripts             # srt, kept outside /tmp
```

On YouTube's first video:

```console
$ vidscribe "https://www.youtube.com/watch?v=jNQXAC9IVRw"
video: /tmp/vidscribe/videos/jNQXAC9IVRw.mp4
transcript: /tmp/vidscribe/transcripts/jNQXAC9IVRw.txt
All right, so here we are, one of the elephants. Cool thing about these guys is that they have really, really, really long trunks, and that's that's cool. And that's pretty much all there is to say.
```

txt transcripts print to stdout; the transcript and video paths go to stderr. On an M5 Pro Mac mini, a 64-minute lecture took 50 s, download included. Outputs stay in `/tmp/vidscribe/` for 3 days. The default model is Qwen3-ASR (~30 languages); for others, use `-m mlx-community/whisper-large-v3-turbo-asr-fp16`. Full reference: [docs/usage.md](docs/usage.md).

## Agent skill

```sh
npx skills add SamuelZ12/vidscribe
```

Needs Node.js 22.20+. Without Node, copy `skill/` into your agent's skills folder (Claude Code: `.claude/skills/vidscribe`).

## Limits

- Speech only: music and other sounds aren't described.
- No OCR: agents read on-screen text from frames they take with `ffmpeg`.
- Coarse timing: each `.srt` cue covers a ~30 s piece of audio, with no word timestamps, so a spoken moment is located only to within that piece.

Design decisions: [docs/decisions/](docs/decisions/).

## License

MIT. The models, ffmpeg and yt-dlp come under their own licenses: [docs/usage.md](docs/usage.md#licenses).
