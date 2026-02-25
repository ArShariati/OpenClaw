#!/usr/bin/env python3
import json, re, sys, asyncio
import requests

URL = sys.argv[1] if len(sys.argv) > 1 else None
if not URL:
    print("Usage: x_fetch.py <x-url>")
    sys.exit(2)

def extract_tweet_id(url: str) -> str:
    m = re.search(r"/status/(\d+)", url)
    return m.group(1) if m else ""

# Try Twikit if configured
try:
    from twikit import Client as TwikitClient
    import asyncio
    cfg_path = "/home/alireza/.openclaw/rag/x_config.json"
    if cfg_path and os.path.exists(cfg_path):
        pass
except Exception:
    TwikitClient = None

import os
cfg_path = "/home/alireza/.openclaw/rag/x_config.json"

async def try_twikit(url: str):
    if TwikitClient is None or not os.path.exists(cfg_path):
        return None
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    client = TwikitClient('en-US')
    if "cookies" in cfg:
        await client.set_cookies(cfg["cookies"])
    elif "username" in cfg and "password" in cfg:
        await client.login(auth_info_1=cfg["username"], auth_info_2=cfg.get("email"), password=cfg["password"], totp_secret=cfg.get("totp"))
    tweet_id = extract_tweet_id(url)
    if not tweet_id:
        return None
    t = await client.get_tweet_by_id(tweet_id)
    if not t:
        return None
    parts = []
    txt = getattr(t, "full_text", None) or getattr(t, "text", None)
    if txt:
        parts.append(txt)
    # best-effort replies
    try:
        replies = getattr(t, "replies", None)
        if replies:
            for r in replies:
                rt = getattr(r, "full_text", None) or getattr(r, "text", None)
                if rt:
                    parts.append(rt)
    except Exception:
        pass
    return "\n".join(parts) if parts else None

def try_fxtwitter(url: str):
    tweet_id = extract_tweet_id(url)
    if not tweet_id:
        return None
    api_url = f"https://api.fxtwitter.com/status/{tweet_id}"
    r = requests.get(api_url, timeout=20)
    r.raise_for_status()
    data = r.json()
    text = data.get("tweet", {}).get("text") or data.get("text")
    return text

async def main():
    text = await try_twikit(URL)
    if not text:
        text = try_fxtwitter(URL)
    if not text:
        print("")
        return
    print(text)

if __name__ == "__main__":
    asyncio.run(main())
