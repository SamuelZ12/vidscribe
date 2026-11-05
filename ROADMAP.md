# Roadmap: video understanding

Goal: make vidscribe give agents a good understanding of videos, not just audio. Do these in order, each as a small verified change.

## Evidence

Omni2Web (https://arxiv.org/html/2609.23417), Gemini 3.5 Flash: transcript only 18.2, frames + transcript 38.1, native audio+video 47.5. Frames roughly double usefulness; timing and scene coverage close part of the remaining gap.

## 1. Measure first (done)
On a 30+ minute YouTube video, run `vidscribe <url> -v` and record how many frames it produces (even + ref) and runtime. Use that to choose a frame cap for long videos.

## 2. Frames by default for video (done)
- If the input has a video stream (check with ffprobe; for URLs, download video), enable visual mode automatically.
- Add `-a/--audio-only` to opt out.
- Audio-only inputs behave exactly as today.
- Cap total frames on long videos (from step 1).

## 3. Timestamps everywhere in index.txt (done)
Each frame line gets the cue start/end of the text next to it, not only the frame time.

## 4. Scene-change frames (done)
Add frames at scene changes (ffmpeg `select='gt(scene,0.3)'` or similar) on top of evenly spaced ones; dedupe near-identical frames.

## 5. Later
- Frames on demand for long videos (done): `vidscribe <frames-dir> --at TIMES`; the agent finds the moment in the transcript and extracts frames from `video.<ext>`. 37.5 → 69/72 on 12 long videos (see `MEASUREMENTS.md`, "Frames on demand"). Choosing better scenes within the 40-frame cap had been tried first and didn't help: on long videos the frame count, not the choice, limits pinpoint questions ("Scene choice on long videos").
- OCR of on-screen text into index.txt: not built. A hard eval of moments the transcript never names scored 31/36 with `--at` (11/36 without), above the 75% bar set beforehand; the 5 misses are moments no speech relates to (see `MEASUREMENTS.md`, "Hard eval"). Revisit if agents report failing to find on-screen content.
- Hosted-model escalation (Gemini Flash behind a flag): rejected 2026-11-05. It is paid and sends media off the device; the user won't use a paid option. Google's agentic video (https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-agentic-video-in-gemini/) informs the local design instead: scan cheaply, then inspect.
- Contact-sheet scan (done): `vidscribe <frames-dir> --scan RANGES|all` finds moments the transcript never hints at; the agent views 4x4 sheets, then confirms with `--at`. Hard set dev 31 → 36/36 with the same image budget; holdout 12/12 both, at ceiling (see `MEASUREMENTS.md`, "Scan probe" and "Scan eval").

## Testing (done for steps 2-4)
Before shipping steps 2-4, run on 10-15 real clips (demos, slides, talking-head, Mandarin, short social clips) and compare answers to questions about each video with and without the change. Results are in `MEASUREMENTS.md`.
