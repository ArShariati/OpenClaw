#!/usr/bin/env bash
set -euo pipefail

IN="$1"
MODEL_DIR="$HOME/.cache/whisper"
MODEL="${WHISPER_MODEL:-small}"

OUT_DIR="${2:-/tmp}"
mkdir -p "$OUT_DIR"

"$HOME/.local/bin/whisper" "$IN" --model "$MODEL" --model_dir "$MODEL_DIR" --output_format txt --output_dir "$OUT_DIR" >/dev/null 2>&1

TXT="$OUT_DIR/$(basename "$IN" .ogg).txt"
if [ ! -f "$TXT" ]; then
  TXT=$(ls -t "$OUT_DIR"/*.txt | head -n1)
fi
cat "$TXT"
