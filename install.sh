#!/usr/bin/env bash
set -euo pipefail
[[ "$(uname -sm)" == "Darwin arm64" ]] || { echo "vidscribe needs an Apple Silicon Mac (MLX)" >&2; exit 1; }
command -v brew >/dev/null || { echo "install Homebrew first: https://brew.sh" >&2; exit 1; }
brew install uv ffmpeg yt-dlp
uv tool install --force mlx-audio --prerelease=allow
mkdir -p "$HOME/.local/bin"
ln -sf "$(cd "$(dirname "$0")" && pwd)/bin/vidscribe" "$HOME/.local/bin/vidscribe"
echo "installed: ~/.local/bin/vidscribe (make sure ~/.local/bin is on PATH)"
echo "agent skill: run 'npx skills add SamuelZ12/vidscribe' in your project"
