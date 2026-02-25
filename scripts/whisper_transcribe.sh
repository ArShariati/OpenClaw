#!/usr/bin/env bash
set -euo pipefail

IN="$1"
MODEL_DIR="$HOME/.cache/whisper"
MODEL="medium"

OUT_DIR="${2:-/tmp}"
mkdir -p "$OUT_DIR"
TRIMMED="$OUT_DIR/trimmed-$(date -u +%F-%H-%M-%S).wav"

ffmpeg -y -i "$IN" -af "silenceremove=start_periods=1:start_silence=0.3:start_threshold=-35dB:stop_periods=1:stop_silence=0.3:stop_threshold=-35dB" "$TRIMMED" >/dev/null 2>&1

"$HOME/.local/bin/whisper" "$TRIMMED" --model "$MODEL" --model_dir "$MODEL_DIR" --output_format txt --output_dir "$OUT_DIR" >/dev/null 2>&1

TXT="$OUT_DIR/$(basename "$TRIMMED" .wav).txt"
cat "$TXT"
