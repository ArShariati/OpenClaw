# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

### Whisper (API)

- Use OpenAI Whisper API (openai-whisper-api skill) for voice transcription.
- Script: `scripts/whisper_api_transcribe.sh <audio-file>` (reads key from openclaw.json).
- Local Whisper removed; API only.

### Voice calls (Telnyx)

- Provider: Telnyx
- From number: +31 970 102 84966 (pending approval)
- Webhook: https://debian-oc.taild78267.ts.net/voice/webhook (Tailscale Funnel; signatures verified)
- Config: ~/.openclaw/openclaw.json → plugins.entries.voice-call
- TTS: OpenAI gpt-4o-mini-tts, default voice **coral** (voices: alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer, verse, marin, cedar)
- TTS fallback: Telnyx native
- STT: OpenAI Whisper (whisper-1)
- Per-call override: can switch to Telnyx native or change OpenAI voice

### X/Twitter (Twikit)

- Cookies: `~/.openclaw/rag/x_cookies.json`
- Helper: `~/workspace/skills/twikit/twikit_client.py`
- Use for: read tweet by ID, replies, post, search, user timeline
- Articles: use browser tool (Twikit can’t fetch full article body)
- Cookies expire every few weeks; ask user to refresh via Cookie-Editor

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
