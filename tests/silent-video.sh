#!/usr/bin/env bash
set -euo pipefail
cli="$(cd "$(dirname "$0")/.." && pwd)/bin/vidscribe"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export VIDSCRIBE_OUTDIR="$tmp/text" VIDSCRIBE_FRAMES_DIR="$tmp/frames"
ffmpeg -nostdin -loglevel error -f lavfi -i testsrc=duration=10:size=320x240:rate=10 -an "$tmp/silent.mp4"

"$cli" "$tmp/silent.mp4"
for ext in txt srt; do
  transcript="$VIDSCRIBE_OUTDIR/silent.$ext"
  [[ -f "$transcript" && ! -s "$transcript" ]]
done
frames="$VIDSCRIBE_FRAMES_DIR/silent"
[[ -s "$frames/overview_01.jpg" ]]
awk -F '\t' '$3 != "-" || $4 != "" { exit 1 } END { if (NR != 16) exit 1 }' "$frames/index.txt"
