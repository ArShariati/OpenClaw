#!/usr/bin/env python3
import argparse
import json
import requests

DEFAULT_BASE = "http://127.0.0.1:8799"


def cmd_ingest(args):
    r = requests.post(f"{args.base}/ingest", json={"url": args.url}, timeout=60)
    if r.status_code != 200:
        raise SystemExit(r.text)
    print(json.dumps(r.json(), indent=2))


def cmd_query(args):
    r = requests.post(f"{args.base}/query", json={"query": args.query, "top_k": args.top_k}, timeout=60)
    if r.status_code != 200:
        raise SystemExit(r.text)
    print(json.dumps(r.json(), indent=2))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default=DEFAULT_BASE)
    sub = p.add_subparsers(dest="cmd", required=True)

    p_ing = sub.add_parser("ingest")
    p_ing.add_argument("url")
    p_ing.set_defaults(func=cmd_ingest)

    p_q = sub.add_parser("query")
    p_q.add_argument("query")
    p_q.add_argument("--top-k", type=int, default=5)
    p_q.set_defaults(func=cmd_query)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
