#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "" ]]; then
  echo "Usage: whisper_api_transcribe.sh <audio-file> [--model whisper-1] [--out /path/to/out.txt] [--language en] [--prompt 'hint'] [--json]" >&2
  exit 2
fi

IN="$1"
shift || true

KEY=$(python3 - <<'PY'
import json
p='/home/alireza/.openclaw/openclaw.json'
with open(p) as f:
    d=json.load(f)
print(d.get('skills',{}).get('entries',{}).get('openai-whisper-api',{}).get('apiKey',''))
PY
)

if [[ -z "$KEY" ]]; then
  echo "Missing OPENAI_API_KEY in openclaw.json (skills.entries.openai-whisper-api.apiKey)" >&2
  exit 1
fi

OPENAI_API_KEY="$KEY" bash /usr/lib/node_modules/openclaw/skills/openai-whisper-api/scripts/transcribe.sh "$IN" "$@"
