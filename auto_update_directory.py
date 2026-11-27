#!/usr/bin/env python3
"""
Auto-expands tools.json with new real AI tools / Telegram bots for video creators.

Pipeline:
  1. read tools.json, collect existing domains + names (duplicate protection)
  2. ask Gemini for candidates (key rotation + model carousel, 429/503 fallback)
  3. validate schema, drop duplicates, check that url answers with HTTP < 400
  4. append to tools.json, rebuild SEO layer (index.html prerender, sitemap.xml)
  5. send a report to Telegram

Standard library only — no pip install needed.

Env:
  GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_API_KEY_3   at least one is required
  GEMINI_MODELS        optional comma-separated override of the model carousel
  COUNT                how many tools to add (default 3)
  TARGET_CATEGORY      any | shorts | captions | dubbing | thumbnails | analytics | telegram
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID                 optional report
  SITE_URL             used by build_seo.py

CLI:
  python auto_update_directory.py --count 3 --category any [--dry-run] [--no-notify]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

from validate_tools import (
    CATEGORIES, load_catalog, normalize_domain, normalize_name,
    save_catalog, slugify, validate_catalog, validate_tool,
)

DEFAULT_MODELS = ["gemini-flash-latest", "gemini-3.8-flash", "gemini-3.7-flash", "gemini-pro-latest"]
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
RETRYABLE = {429, 500, 502, 503, 504}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36 CreatorDirectoryBot/1.0"
)
MAX_ROUNDS = 3


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------- Gemini

class GeminiError(RuntimeError):
    pass


def gemini_keys() -> list[str]:
    names = ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]
    keys = [os.environ.get(n, "").strip() for n in names]
    return [k for k in keys if k]


def gemini_models() -> list[str]:
    override = os.environ.get("GEMINI_MODELS", "").strip()
    return [m.strip() for m in override.split(",") if m.strip()] if override else list(DEFAULT_MODELS)


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 90) -> tuple[int, str]:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        return 0, str(err)


def ask_gemini(prompt: str) -> str:
    """Rotate over models x keys. Skips dead models (404) and dead keys (401/403)."""
    keys, models = gemini_keys(), gemini_models()
    if not keys:
        raise GeminiError("No GEMINI_API_KEY* environment variables set")

    dead_keys: set[int] = set()
    dead_models: set[str] = set()
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"},
    }

    for rnd in range(3):
        for model in models:
            if model in dead_models:
                continue
            for ki, key in enumerate(keys):
                if ki in dead_keys:
                    continue
                label = f"{model} / key#{ki + 1}"
                status, body = _post_json(GEMINI_URL.format(model=model), payload, {"x-goog-api-key": key})
                if status == 200:
                    try:
                        data = json.loads(body)
                        parts = data["candidates"][0]["content"]["parts"]
                        text = "".join(p.get("text", "") for p in parts)
                        if text.strip():
                            log(f"  gemini: OK via {label}")
                            return text
                        log(f"  gemini: empty answer from {label}")
                    except (KeyError, IndexError, json.JSONDecodeError):
                        log(f"  gemini: unexpected response from {label}: {body[:200]}")
                    continue
                if status in RETRYABLE or status == 0:
                    wait = min(30, 2 ** rnd + random.random() * 2)
                    log(f"  gemini: {status or 'network error'} on {label}, next in {wait:.1f}s")
                    time.sleep(wait)
                    continue
                if status in (401, 403) or "API_KEY_INVALID" in body or "API key not valid" in body:
                    log(f"  gemini: key#{ki + 1} rejected ({status}), disabling it")
                    dead_keys.add(ki)
                    continue
                if status in (400, 404):
                    log(f"  gemini: model {model} unavailable ({status}): {body[:160]}")
                    dead_models.add(model)
                    break
                log(f"  gemini: HTTP {status} on {label}: {body[:160]}")
        if len(dead_keys) == len(keys) or len(dead_models) == len(models):
            break
        time.sleep(5 * (rnd + 1))
    raise GeminiError("All Gemini keys/models failed")


def build_prompt(n: int, category: str, exclude_names: list[str], exclude_domains: list[str]) -> str:
    cat_rule = (
        f'All tools MUST have category "{category}".' if category != "any"
        else f"Spread tools across categories: {', '.join(CATEGORIES)}."
    )
    return f"""You are a researcher for CreatorDirectory, a curated catalog of AI tools and Telegram bots
for YouTube, TikTok, Instagram Reels and Telegram channel creators.

Return {n} REAL, currently operating products that are NOT in the exclusion lists.
Only include products you are confident exist, with their official https homepage.
Never invent products or URLs. Prefer well-known, actively maintained tools.

Category meanings:
- shorts: AI clipping / repurposing long videos into Shorts, Reels, TikToks; short-form editors
- captions: automatic subtitles and caption styling
- dubbing: AI dubbing, voice cloning, voiceover, video translation
- thumbnails: thumbnail / cover generation, image editing for thumbnails, A/B tests
- analytics: YouTube / TikTok / Instagram analytics, SEO, research, scheduling with analytics
- telegram: Telegram bots and services for channel owners (analytics, ads, posting, monetization)
{cat_rule}

Exclude these names: {json.dumps(exclude_names, ensure_ascii=False)}
Exclude these domains: {json.dumps(exclude_domains)}

Output ONLY a JSON array. Each item must have exactly these keys:
{{
  "name": "Product name (latin)",
  "category": "one of {list(CATEGORIES)}",
  "pricing_type": "free | freemium | paid",
  "pricing_en": "short price line in English, max 60 chars",
  "pricing_ru": "the same in Russian",
  "pricing_uk": "the same in Ukrainian",
  "desc_en": "2-3 sentences in English: what pain it solves and who it is for (120-380 chars, no Cyrillic)",
  "desc_ru": "the same description in natural Russian",
  "desc_uk": "the same description in natural Ukrainian",
  "tags": ["3-7 lowercase english keywords"],
  "url": "https://official-site",
  "tg": "https://t.me/BotName or empty string if there is no official Telegram bot"
}}"""


def parse_candidates(text: str) -> list[dict]:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", text, re.S)
        if not m:
            return []
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return []
    if isinstance(data, dict):
        data = data.get("tools") or data.get("items") or []
    return [x for x in data if isinstance(x, dict)] if isinstance(data, list) else []


# --------------------------------------------------------------------------- URL checks

def check_url(url: str, timeout: int = 15) -> tuple[bool, str]:
    """True if the site answers with HTTP status < 400 (HEAD, then GET fallback)."""
    last = ""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={
            "User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status < 400:
                    return True, f"{resp.status} {resp.geturl()}"
                last = str(resp.status)
        except urllib.error.HTTPError as err:
            last = f"HTTP {err.code}"
            if err.code < 400:
                return True, last
        except Exception as err:  # noqa: BLE001 - DNS errors, SSL errors, timeouts...
            last = type(err).__name__ + ": " + str(err)[:80]
    return False, last


def check_tg(url: str) -> bool:
    """t.me answers 200 even for unknown names; a real bot/channel page has a title block."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read(200_000).decode("utf-8", "replace")
            return resp.status < 400 and "tgme_page_title" in body
    except Exception:  # noqa: BLE001
        return False


# --------------------------------------------------------------------------- Telegram report

def notify_telegram(text: str) -> None:
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        log("telegram: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set, report skipped")
        return
    status, body = _post_json(
        f"https://api.telegram.org/bot{token}/sendMessage",
        {"chat_id": chat, "text": text[:4000], "parse_mode": "HTML", "disable_web_page_preview": True},
        {}, timeout=20,
    )
    log("telegram: report sent" if status == 200 else f"telegram: failed {status} {body[:200]}")


def html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------- main logic

def prepare(raw: dict, category: str, used_ids: set[str]) -> dict:
    """Map a Gemini candidate to our strict schema."""
    name = str(raw.get("name", "")).strip()
    tool = {
        "id": "",
        "name": name,
        "category": str(raw.get("category", "")).strip().lower(),
        "featured": False,
        "pricing_type": str(raw.get("pricing_type", "")).strip().lower(),
        "pricing_en": str(raw.get("pricing_en", "")).strip(),
        "pricing_ru": str(raw.get("pricing_ru", "")).strip(),
        "pricing_uk": str(raw.get("pricing_uk", "")).strip(),
        "desc_en": str(raw.get("desc_en", "")).strip(),
        "desc_ru": str(raw.get("desc_ru", "")).strip(),
        "desc_uk": str(raw.get("desc_uk", "")).strip(),
        "tags": [],
        "url": str(raw.get("url", "")).strip(),
        "added_at": date.today().isoformat(),
    }
    tags = raw.get("tags") if isinstance(raw.get("tags"), list) else []
    clean_tags: list[str] = []
    for tag in tags:
        tg = re.sub(r"[^a-z0-9 ./+#-]", "", str(tag).lower()).strip()[:31]
        if tg and tg not in clean_tags:
            clean_tags.append(tg)
    tool["tags"] = clean_tags[:7]
    tg_link = str(raw.get("tg") or "").strip()
    if tg_link.startswith("https://t.me/"):
        tool["tg"] = tg_link
    if category != "any":
        tool["category"] = tool["category"] if tool["category"] == category else ""

    base = slugify(name)
    slug, i = base, 2
    while slug in used_ids:
        slug, i = f"{base}-{i}", i + 1
    tool["id"] = slug
    return tool


def run(count: int, category: str, dry_run: bool) -> tuple[list[dict], list[str]]:
    data = load_catalog()
    tools = data["tools"]
    domains = {normalize_domain(t["url"]) for t in tools}
    domains |= {normalize_domain(t["tg"]) for t in tools if t.get("tg")}
    names = {normalize_name(t["name"]) for t in tools}
    ids = {t["id"] for t in tools}
    added: list[dict] = []
    rejected: list[str] = []
    rejected_names: list[str] = []

    for rnd in range(1, MAX_ROUNDS + 1):
        need = count - len(added)
        if need <= 0:
            break
        ask = min(10, need * 2 + 1)  # ask for extra candidates: some will fail checks
        log(f"\nRound {rnd}: requesting {ask} candidates (category={category})")
        prompt = build_prompt(
            ask, category,
            sorted({t["name"] for t in tools} | {t["name"] for t in added} | set(rejected_names)),
            sorted(domains),
        )
        try:
            candidates = parse_candidates(ask_gemini(prompt))
        except GeminiError as err:
            log(f"  {err}")
            break
        log(f"  got {len(candidates)} candidates")

        for raw in candidates:
            if len(added) >= count:
                break
            tool = prepare(raw, category, ids)
            label = tool["name"] or "<no name>"
            if tool["name"]:
                rejected_names.append(tool["name"])  # never ask for the same candidate twice
            if not tool["url"].startswith("https://"):
                rejected.append(f"{label}: no https url")
                continue
            dom = normalize_domain(tool["url"])
            if dom in domains or normalize_name(tool["name"]) in names:
                rejected.append(f"{label}: duplicate ({dom})")
                continue
            errs = validate_tool(tool)
            if errs:
                rejected.append(f"{label}: schema - {errs[0]}")
                continue
            ok, info = check_url(tool["url"])
            if not ok:
                rejected.append(f"{label}: url check failed ({info})")
                continue
            if tool.get("tg") and not check_tg(tool["tg"]):
                log(f"  {label}: tg link not verified, dropping tg field")
                tool.pop("tg")
            log(f"  + {label} [{tool['category']}] {tool['url']} ({info})")
            added.append(tool)
            domains.add(dom)
            names.add(normalize_name(tool["name"]))
            ids.add(tool["id"])

    for r in rejected:
        log(f"  - rejected {r}")

    if added and not dry_run:
        data["tools"] = tools + added  # appended after existing items -> KoShorts stays #1
        data["updated_at"] = date.today().isoformat()
        errs = validate_catalog(data)
        if errs:
            raise SystemExit("Catalog became invalid, nothing saved:\n" + "\n".join(errs))
        save_catalog(data)
        import build_seo  # local module
        build_seo.main()
        log(f"\nSaved {len(added)} new tool(s) to tools.json (total {len(data['tools'])})")
    elif dry_run:
        log("\nDry run: tools.json not modified")
        log(json.dumps(added, ensure_ascii=False, indent=2))
    return added, rejected


def report(added: list[dict], rejected: list[str], category: str, total_before: int) -> str:
    lines = [f"<b>CreatorDirectory auto-update</b> ({date.today().isoformat()})", f"Category: {html_escape(category)}"]
    if added:
        lines.append(f"Added {len(added)} tool(s), catalog size: {total_before + len(added)}")
        for t in added:
            lines.append(f"• <b>{html_escape(t['name'])}</b> [{t['category']}, {t['pricing_type']}]\n  {html_escape(t['url'])}")
    else:
        lines.append("No new tools were added this run.")
    if rejected:
        lines.append(f"Rejected candidates: {len(rejected)}")
        lines += [f"  – {html_escape(r)}" for r in rejected[:8]]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=int(os.environ.get("COUNT") or 3))
    parser.add_argument("--category", default=(os.environ.get("TARGET_CATEGORY") or "any").lower())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-notify", action="store_true")
    args = parser.parse_args()

    count = max(1, min(args.count, 20))
    category = args.category if args.category in CATEGORIES else "any"
    if not gemini_keys():
        log("ERROR: set at least GEMINI_API_KEY (GitHub -> Settings -> Secrets and variables -> Actions)")
        return 1

    total_before = len(load_catalog()["tools"])
    added, rejected = run(count, category, args.dry_run)
    text = report(added, rejected, category, total_before)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(re.sub(r"<[^>]+>", "", text).replace("\n", "  \n") + "\n")
    if not args.no_notify and not args.dry_run:
        notify_telegram(text)
        # Semi-automatic outreach: contacts + ready message for every new tool -> your Telegram
        if added:
            try:
                import outreach
                outreach.cmd_prepare(argparse.Namespace(ids=",".join(t["id"] for t in added), next=None,
                                                        new=False, dry_run=False))
            except Exception as exc:  # noqa: BLE001 - outreach must never break the catalog update
                log(f"outreach: skipped ({exc})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
