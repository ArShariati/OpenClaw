#!/usr/bin/env python3
"""
Twikit helper for X/Twitter read & write operations.
Uses cookie-based auth to bypass Cloudflare blocks on server IPs.

Cookies file: ~/.openclaw/rag/x_cookies.json
Refresh cookies when they expire (every few weeks/months) using Cookie-Editor in browser.
"""

import asyncio
import json
import sys
from pathlib import Path
from twikit import Client

COOKIES_FILE = Path.home() / ".openclaw/rag/x_cookies.json"


def get_client() -> Client:
    client = Client("en-US")
    with open(COOKIES_FILE) as f:
        raw = json.load(f)
    # Cookie-Editor exports full objects; Twikit needs name:value dict
    cookies = {c["name"]: c["value"] for c in raw}
    client.set_cookies(cookies)
    return client


async def get_tweet(tweet_id: str):
    client = get_client()
    tweet = await client.get_tweet_by_id(tweet_id)
    return {
        "id": tweet.id,
        "text": tweet.text,
        "author": tweet.user.screen_name,
        "created_at": str(tweet.created_at),
        "reply_count": tweet.reply_count,
        "retweet_count": tweet.retweet_count,
        "like_count": tweet.favorite_count,
    }


async def get_replies(tweet_id: str, count: int = 20):
    client = get_client()
    replies = await client.search_tweet(f"conversation_id:{tweet_id}", "Latest", count=count)
    return [{"id": t.id, "author": t.user.screen_name, "text": t.text} for t in replies]


async def post_tweet(text: str, reply_to: str = None):
    client = get_client()
    tweet = await client.create_tweet(text=text, reply_to=reply_to)
    return {"id": tweet.id, "text": tweet.text}


async def search(query: str, count: int = 10):
    client = get_client()
    results = await client.search_tweet(query, "Latest", count=count)
    return [{"id": t.id, "author": t.user.screen_name, "text": t.text} for t in results]


async def get_user_timeline(username: str, count: int = 10):
    client = get_client()
    user = await client.get_user_by_screen_name(username)
    tweets = await client.get_user_tweets(user.id, "Tweets", count=count)
    return [{"id": t.id, "text": t.text, "created_at": str(t.created_at)} for t in tweets]


if __name__ == "__main__":
    # Quick test
    async def main():
        client = get_client()
        user = await client.get_user_by_screen_name("ARshariati")
        print(f"✓ Auth OK — @{user.screen_name} ({user.followers_count} followers)")

    asyncio.run(main())
