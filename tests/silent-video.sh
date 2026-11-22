#!/usr/bin/env bash
set -euo pipefail
cli="$(cd "$(dirname "$0")/.." && pwd)/bin/vidscribe"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export VIDSCRIBE_OUTDIR="$tmp/text"
ffmpeg -nostdin -loglevel error -f lavfi -i testsrc=duration=10:size=320x240:rate=10 -an "$tmp/silent.mp4"

"$cli" "$tmp/silent.mp4" 2> "$tmp/err" || { cat "$tmp/err" >&2; exit 1; }
for ext in txt srt; do
  transcript="$VIDSCRIBE_OUTDIR/silent.$ext"
  [[ -f "$transcript" && ! -s "$transcript" ]]
done
grep -Fqx "video: $tmp/silent.mp4" "$tmp/err"
# a relative input prints an absolute path
(cd "$tmp" && "$cli" silent.mp4) 2> "$tmp/err" || { cat "$tmp/err" >&2; exit 1; }
grep -Fqx "video: $tmp/silent.mp4" "$tmp/err"
