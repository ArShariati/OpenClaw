import os
import re
import json
import time
import sqlite3
import hashlib
import tempfile
from typing import List, Optional

import requests
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import trafilatura
import pdfplumber
from fastembed import TextEmbedding

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except Exception:
    YouTubeTranscriptApi = None

# Optional: twikit for X
try:
    from twikit import Client as TwikitClient
    import asyncio
except Exception:
    TwikitClient = None

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("RAG_DATA_DIR", "/home/alireza/.openclaw/rag")
DB_PATH = os.path.join(DATA_DIR, "rag.sqlite3")
MODEL_NAME = os.environ.get("RAG_EMBED_MODEL", "BAAI/bge-small-en-v1.5")

os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(title="OpenClaw RAG", version="0.1.0")

_model = None

def get_model():
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=MODEL_NAME)
    return _model


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db():
    conn = connect_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            type TEXT,
            title TEXT,
            added_at INTEGER,
            raw_text TEXT,
            meta_json TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            chunk_index INTEGER,
            content TEXT,
            embedding BLOB,
            FOREIGN KEY(source_id) REFERENCES sources(id)
        );
        """
    )
    conn.commit()
    conn.close()


init_db()


class IngestRequest(BaseModel):
    url: str


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    source_id: int
    url: str
    title: Optional[str]
    score: float
    snippet: str


YOUTUBE_RE = re.compile(r"(youtube\.com|youtu\.be)")
X_RE = re.compile(r"(x\.com|twitter\.com)")


def normalize_vec(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n == 0:
        return v
    return v / n


def chunk_text(text: str, size: int = 1000, overlap: int = 200) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i + size]
        if chunk:
            chunks.append(chunk)
        i += size - overlap
    return chunks


def embed_texts(texts: List[str]) -> np.ndarray:
    model = get_model()
    vectors = list(model.embed(texts))
    arr = np.array(vectors, dtype=np.float32)
    # normalize
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    arr = arr / norms
    return arr


def fetch_article(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ValueError("Failed to download article")
    text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
    if not text:
        raise ValueError("Failed to extract article text")
    return text


def fetch_pdf(url: str) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(resp.content)
        tmp = f.name
    try:
        text_parts = []
        with pdfplumber.open(tmp) as pdf:
            for page in pdf.pages:
                txt = page.extract_text() or ""
                text_parts.append(txt)
        return "\n".join(text_parts).strip()
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass


def youtube_video_id(url: str) -> Optional[str]:
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    return None


def fetch_youtube(url: str) -> str:
    vid = youtube_video_id(url)
    if not vid:
        raise ValueError("Unable to parse YouTube ID")

    if YouTubeTranscriptApi is not None:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(vid)
            return "\n".join([t["text"] for t in transcript])
        except Exception:
            pass

    # Fallback: try yt-dlp to fetch captions if available
    try:
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            cmd = ["yt-dlp", "--skip-download", "--write-auto-sub", "--sub-lang", "en", "-o", os.path.join(td, "video"), url]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # find .vtt
            vtts = [f for f in os.listdir(td) if f.endswith(".vtt")]
            if not vtts:
                raise ValueError("No captions found")
            vtt_path = os.path.join(td, vtts[0])
            with open(vtt_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.read().splitlines()
            # simple VTT text extraction
            text_lines = [ln for ln in lines if ln and not ln.startswith("WEBVTT") and not re.match(r"\d\d:\d\d", ln)]
            return "\n".join(text_lines).strip()
    except Exception as e:
        raise ValueError(f"YouTube transcript unavailable: {e}")


def fetch_x(url: str) -> str:
    # Prefer twikit if configured
    if TwikitClient is not None:
        cfg_path = os.path.join(DATA_DIR, "x_config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)

            async def _get():
                client = TwikitClient('en-US')
                if "cookies" in cfg:
                    await client.set_cookies(cfg["cookies"])
                elif "username" in cfg and "password" in cfg:
                    await client.login(auth_info_1=cfg["username"], auth_info_2=cfg.get("email"), password=cfg["password"], totp_secret=cfg.get("totp"))

                tweet_id = re.sub(r".*/status/", "", url).split("?")[0]
                t = await client.get_tweet_by_id(tweet_id)
                if not t:
                    return None

                parts = []
                if getattr(t, "full_text", None):
                    parts.append(t.full_text)
                elif getattr(t, "text", None):
                    parts.append(t.text)

                # Best-effort: collect replies if available
                try:
                    replies = getattr(t, "replies", None)
                    if replies:
                        for r in replies:
                            txt = getattr(r, "full_text", None) or getattr(r, "text", None)
                            if txt:
                                parts.append(txt)
                except Exception:
                    pass

                return "\n".join(parts)

            try:
                text = asyncio.run(_get())
                if text:
                    return text
            except Exception:
                pass

    # Fallback: FxTwitter
    tweet_id = re.sub(r".*/status/", "", url).split("?")[0]
    api_url = f"https://api.fxtwitter.com/status/{tweet_id}"
    r = requests.get(api_url, timeout=20)
    r.raise_for_status()
    data = r.json()
    text = data.get("tweet", {}).get("text") or data.get("text")
    if not text:
        raise ValueError("Unable to extract tweet text")
    return text


def detect_type(url: str) -> str:
    if YOUTUBE_RE.search(url):
        return "youtube"
    if X_RE.search(url):
        return "x"
    if url.lower().endswith(".pdf"):
        return "pdf"
    return "article"


def ingest_url(url: str) -> int:
    url = url.strip()
    kind = detect_type(url)

    if kind == "youtube":
        text = fetch_youtube(url)
    elif kind == "x":
        text = fetch_x(url)
    elif kind == "pdf":
        text = fetch_pdf(url)
    else:
        text = fetch_article(url)

    if not text or len(text) < 50:
        raise ValueError("Extracted text is too short")

    title = None
    meta = {"kind": kind}

    chunks = chunk_text(text)
    vectors = embed_texts(chunks)

    conn = connect_db()
    cur = conn.cursor()
    now = int(time.time())
    cur.execute(
        "INSERT OR REPLACE INTO sources(url, type, title, added_at, raw_text, meta_json) VALUES (?, ?, ?, ?, ?, ?)",
        (url, kind, title, now, text, json.dumps(meta))
    )
    source_id = cur.lastrowid
    cur.execute("DELETE FROM chunks WHERE source_id=?", (source_id,))
    for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
        cur.execute(
            "INSERT INTO chunks(source_id, chunk_index, content, embedding) VALUES (?, ?, ?, ?)",
            (source_id, i, chunk, vec.tobytes())
        )
    conn.commit()
    conn.close()
    return source_id


def search(query: str, top_k: int = 5) -> List[SearchResult]:
    qvec = embed_texts([query])[0]

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT c.id, c.source_id, c.content, c.embedding, s.url, s.title FROM chunks c JOIN sources s ON c.source_id = s.id")
    rows = cur.fetchall()
    conn.close()

    scored = []
    for _cid, source_id, content, emb_blob, url, title in rows:
        emb = np.frombuffer(emb_blob, dtype=np.float32)
        score = float(np.dot(qvec, emb))
        scored.append((score, source_id, url, title, content))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, source_id, url, title, content in scored[:top_k]:
        snippet = content[:240] + ("..." if len(content) > 240 else "")
        results.append(SearchResult(source_id=source_id, url=url, title=title, score=score, snippet=snippet))
    return results


@app.post("/ingest")
def ingest(req: IngestRequest):
    try:
        source_id = ingest_url(req.url)
        return {"ok": True, "source_id": source_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/query")
def query(req: QueryRequest):
    results = search(req.query, req.top_k)
    return {"ok": True, "results": [r.dict() for r in results]}


@app.get("/health")
def health():
    return {"ok": True}
