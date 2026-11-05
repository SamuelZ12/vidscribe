#!/bin/bash
# frames_only.sh SCRIPT SRT VIDEO OUTDIR : run the frame-selection heredoc of a vidscribe script on an existing srt
set -euo pipefail
S="$1"; SRT="$2"; VID="$3"; FDIR="$4"
rm -rf "$FDIR"; mkdir -p "$FDIR"
PYSRC="$(awk '/python3 - "\$OUT.srt"/{f=1; next} f && /^PY$/{exit} f' "$S")"
DUR="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VID")"
TXT="$(mktemp)"
python3 -c "$PYSRC" "$SRT" "$DUR" 8 "$FDIR" "$VID" "$TXT" >&2
rm -f "$TXT"
