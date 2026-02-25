---
name: rag-telegram-ingest
description: Handle explicit Telegram RAG commands. Use when a Telegram message starts with "save:" to ingest a URL into the local RAG service, or when the user asks natural-language queries about saved items (e.g., "show me everything I saved about X").
---

# RAG Telegram Ingest

## Overview

Ingest URLs into the local RAG service on explicit `save:` commands and answer natural-language queries against the RAG index.

## Quick Start (Telegram)

### 1) Ingest

When a message starts with:
```
save: <url>
```

Call the local ingest endpoint:
```
POST http://127.0.0.1:8799/ingest
{"url":"<url>"}
```

Then confirm success with a short reply (include the source id if returned).
If ingestion fails, report the error.

### 2) Query

If the user asks for saved items (examples: “show me everything I saved about OpenAI”, “what did I save about X”), call:
```
POST http://127.0.0.1:8799/query
{"query":"<user query>", "top_k": 5}
```

Summarize the results with:
- title (if present)
- URL
- short snippet
- similarity score (optional)

## Notes

- Only ingest on explicit `save:` (do not auto-ingest plain URLs).
- If the RAG service is down, suggest restarting:
  `systemctl --user restart openclaw-rag.service`
