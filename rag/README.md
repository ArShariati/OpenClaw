# OpenClaw RAG (local)

**Service:** http://127.0.0.1:8799
**Data dir:** `/home/alireza/.openclaw/rag/`

## CLI

```bash
/home/alireza/.openclaw/workspace/rag/ragctl ingest "https://example.com/article"
/home/alireza/.openclaw/workspace/rag/ragctl query "show me everything I saved about OpenAI"
```

## HTTP

```bash
curl -s http://127.0.0.1:8799/ingest -X POST -H 'Content-Type: application/json' -d '{"url":"https://example.com"}'
curl -s http://127.0.0.1:8799/query -X POST -H 'Content-Type: application/json' -d '{"query":"OpenAI", "top_k": 5}'
```

## Telegram usage (explicit)

Send messages like:
```
save: https://example.com/article
```
I’ll ingest and confirm.

For search, ask naturally:
```
show me everything I saved about OpenAI
```

## X/Twitter

- Primary: **twikit** (supports threads/replies best‑effort)
- Fallback: **FxTwitter API** for single tweet reads

Configure credentials in:
`/home/alireza/.openclaw/rag/x_config.json`
(Use the example file `x_config.json.example`)

## YouTube

- Primary: **youtube‑transcript‑api** (uses existing captions)
- Fallback: **yt‑dlp** for auto‑captions if available

## Systemd service

```
systemctl --user status openclaw-rag.service
systemctl --user restart openclaw-rag.service
```
