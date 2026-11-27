#!/usr/bin/env python3
"""
IndexNow: tell Bing, Yandex, Seznam, Naver (and DuckDuckGo / ChatGPT search, which use Bing)
about new or changed pages right after a deploy.

    python indexnow_submit.py --since <git sha>   # pages changed since that commit (used by the workflows)
    python indexnow_submit.py --all               # every URL from sitemap.xml (first run / full resubmit)
    python indexnow_submit.py --dry-run --all     # only print what would be sent

The key is the <32 hex>.txt file in the repository root (public by design: search engines fetch
https://<site>/<key>.txt to verify ownership). No secrets needed.
Never fails the workflow: network problems are reported and the script exits 0.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SITE_URL = os.environ.get("SITE_URL", "https://creator-directory-chi.vercel.app").rstrip("/")
ENDPOINT = os.environ.get("INDEXNOW_ENDPOINT", "https://api.indexnow.org/indexnow")
MAX_URLS = 10000  # IndexNow limit per request


def find_key() -> str:
    for p in sorted(ROOT.glob("*.txt")):
        if re.fullmatch(r"[0-9a-f]{32}", p.stem) and p.read_text(encoding="utf-8").strip() == p.stem:
            return p.stem
    raise SystemExit("IndexNow key file (<32 hex>.txt containing the same key) not found in the repo root")


def file_to_urls(path: str) -> list[str]:
    """index.html -> /, /ru, /uk ; tools/x/ru/index.html -> /tools/x/ru/ ; sitemap etc. -> nothing."""
    if path == "index.html":
        return [f"{SITE_URL}/", f"{SITE_URL}/ru", f"{SITE_URL}/uk"]
    if path.endswith("/index.html") and path.split("/")[0] in ("tools", "best"):
        return [f"{SITE_URL}/{path[: -len('index.html')]}"]
    return []


def changed_urls(since: str) -> list[str]:
    try:
        out = subprocess.run(["git", "diff", "--name-only", f"{since}..HEAD"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as exc:
        print(f"git diff failed ({exc.stderr.strip()}); falling back to the full sitemap")
        return sitemap_urls()
    urls: list[str] = []
    for line in out.splitlines():
        for u in file_to_urls(line.strip()):
            if u not in urls:
                urls.append(u)
    return urls


def sitemap_urls() -> list[str]:
    text = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>([^<]+)</loc>", text)


def submit(urls: list[str], key: str, dry_run: bool) -> None:
    host = urlparse(SITE_URL).netloc
    payload = {"host": host, "key": key, "keyLocation": f"{SITE_URL}/{key}.txt", "urlList": urls[:MAX_URLS]}
    print(f"IndexNow: {len(payload['urlList'])} URL(s) for {host}")
    for u in payload["urlList"][:20]:
        print("  ", u)
    if len(urls) > 20:
        print(f"   … and {len(urls) - 20} more")
    if dry_run:
        print("dry run: nothing sent")
        return
    req = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"IndexNow response: HTTP {resp.status} (200/202 = accepted)")
    except urllib.error.HTTPError as exc:
        hints = {400: "bad request", 403: "key not valid — is <key>.txt deployed?", 422: "URLs do not match the host",
                 429: "too many requests, try later"}
        print(f"::warning::IndexNow HTTP {exc.code}: {hints.get(exc.code, exc.reason)}")
    except Exception as exc:  # network problems must not break the deploy pipeline
        print(f"::warning::IndexNow request failed: {exc}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--since", help="git sha: submit pages changed since this commit")
    g.add_argument("--all", action="store_true", help="submit every URL from sitemap.xml")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key = find_key()
    urls = sitemap_urls() if args.all else changed_urls(args.since)
    if not urls:
        print("IndexNow: no page changes, nothing to submit")
        return
    submit(urls, key, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
