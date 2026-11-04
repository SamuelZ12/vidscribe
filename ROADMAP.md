# Roadmap: video understanding

Goal: make vidscribe give agents a good understanding of videos, not just audio. Do these in order, each as a small verified change.

## Evidence

Omni2Web (https://arxiv.org/html/2609.23417), Gemini 3.5 Flash: transcript only 18.2, frames + transcript 38.1, native audio+video 47.5. Frames roughly double usefulness; timing and scene coverage close part of the remaining gap.

## 1. Measure first
On a 30+ minute YouTube video, run `vidscribe <url> -v` and record how many frames it produces (even + ref) and runtime. Use that to choose a frame cap for long videos.

## 2. Frames by default for video
- If the input has a video stream (check with ffprobe; for URLs, download video), enable visual mode automatically.
- Add `-a/--audio-only` to opt out.
- Audio-only inputs behave exactly as today.
- Cap total frames on long videos (from step 1).

## 3. Timestamps everywhere in index.txt
Each frame line gets the cue start/end of the text next to it, not only the frame time.

## 4. Scene-change frames
Add frames at scene changes (ffmpeg `select='gt(scene,0.3)'` or similar) on top of evenly spaced ones; dedupe near-identical frames.

## 5. Later
- OCR of on-screen text into index.txt.
- Optional escalation to a hosted model (Gemini Flash via Google's `gemini-api` CLI, `gemini-api agent run`) behind an explicit flag; needs `GEMINI_API_KEY`. Never default.

## Testing
Before shipping steps 2-4, run on 10-15 real clips (demos, slides, talking-head, Mandarin, short social clips) and compare answers to questions about each video with and without the change.
