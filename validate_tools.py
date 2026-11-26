#!/usr/bin/env python3
"""
Dependency-free validator for tools.json (mirrors tools.schema.json).

Usage:
    python validate_tools.py            # validates ./tools.json, exit code 1 on errors
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
TOOLS_PATH = ROOT / "tools.json"

CATEGORIES = ("shorts", "captions", "dubbing", "thumbnails", "analytics", "telegram")
PRICING_TYPES = ("free", "freemium", "paid")
LANGS = ("en", "ru", "uk")

REQUIRED = (
    "id", "name", "category", "featured", "pricing_type",
    "pricing_en", "pricing_ru", "pricing_uk",
    "desc_en", "desc_ru", "desc_uk",
    "tags", "url", "added_at",
)

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TAG_RE = re.compile(r"^[a-z0-9][a-z0-9 ./+#-]{0,30}$")
TG_RE = re.compile(r"^https://t\.me/[A-Za-z0-9_]{4,}")
CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")


def normalize_domain(url: str) -> str:
    """'https://www.Opus.pro/path' -> 'opus.pro'. For t.me links keep the bot name."""
    p = urlparse(url.strip().lower())
    host = p.netloc.split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    if host in ("t.me", "telegram.me"):
        name = p.path.strip("/").split("/")[0]
        return f"t.me/{name}"
    return host


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)[:60].strip("-") or "tool"


def validate_tool(tool: dict) -> list[str]:
    """Return a list of human-readable problems (empty list = valid)."""
    errs: list[str] = []
    if not isinstance(tool, dict):
        return ["tool is not an object"]
    tid = tool.get("id", "?")

    for key in REQUIRED:
        if key not in tool:
            errs.append(f"{tid}: missing field '{key}'")
    if errs:
        return errs

    if not isinstance(tool["id"], str) or not ID_RE.match(tool["id"]) or len(tool["id"]) > 60:
        errs.append(f"{tid}: invalid id (lowercase latin slug expected)")
    if not isinstance(tool["name"], str) or not (1 <= len(tool["name"]) <= 80):
        errs.append(f"{tid}: invalid name")
    if tool["category"] not in CATEGORIES:
        errs.append(f"{tid}: category must be one of {CATEGORIES}")
    if not isinstance(tool["featured"], bool):
        errs.append(f"{tid}: featured must be boolean")
    if "pinned" in tool and not isinstance(tool["pinned"], bool):
        errs.append(f"{tid}: pinned must be boolean")
    if tool["pricing_type"] not in PRICING_TYPES:
        errs.append(f"{tid}: pricing_type must be one of {PRICING_TYPES}")

    for lang in LANGS:
        price = tool.get(f"pricing_{lang}")
        desc = tool.get(f"desc_{lang}")
        if not isinstance(price, str) or not (1 <= len(price) <= 80):
            errs.append(f"{tid}: pricing_{lang} must be 1-80 chars")
        if not isinstance(desc, str) or not (40 <= len(desc) <= 420):
            errs.append(f"{tid}: desc_{lang} must be 40-420 chars")
        badge = tool.get(f"badge_{lang}")
        if badge is not None and (not isinstance(badge, str) or len(badge) > 32):
            errs.append(f"{tid}: badge_{lang} must be a string up to 32 chars")

    # English fields must never contain Cyrillic
    for key in ("name", "desc_en", "pricing_en", "badge_en"):
        if isinstance(tool.get(key), str) and CYRILLIC_RE.search(tool[key]):
            errs.append(f"{tid}: '{key}' contains Cyrillic characters")
    # RU / UK descriptions must actually be translated
    for lang in ("ru", "uk"):
        if isinstance(tool.get(f"desc_{lang}"), str) and not CYRILLIC_RE.search(tool[f"desc_{lang}"]):
            errs.append(f"{tid}: desc_{lang} does not look translated")

    tags = tool["tags"]
    if not isinstance(tags, list) or not (3 <= len(tags) <= 7):
        errs.append(f"{tid}: tags must be a list of 3-7 items")
    else:
        if len(set(tags)) != len(tags):
            errs.append(f"{tid}: duplicate tags")
        for tag in tags:
            if not isinstance(tag, str) or not TAG_RE.match(tag):
                errs.append(f"{tid}: bad tag {tag!r} (lowercase latin, up to 31 chars)")

    if not isinstance(tool["url"], str) or not tool["url"].startswith("https://") or not urlparse(tool["url"]).netloc:
        errs.append(f"{tid}: url must be an absolute https:// URL")
    if "tg" in tool and tool["tg"] not in (None, ""):
        if not isinstance(tool["tg"], str) or not TG_RE.match(tool["tg"]):
            errs.append(f"{tid}: tg must look like https://t.me/<bot>")
    if "case_study" in tool and (not isinstance(tool["case_study"], str) or not tool["case_study"].startswith("https://")):
        errs.append(f"{tid}: case_study must be an https:// URL")
    if not isinstance(tool["added_at"], str) or not DATE_RE.match(tool["added_at"]):
        errs.append(f"{tid}: added_at must be YYYY-MM-DD")
    return errs


def validate_catalog(data: dict) -> list[str]:
    errs: list[str] = []
    if not isinstance(data, dict) or not isinstance(data.get("tools"), list):
        return ["root must be an object with a 'tools' array"]
    seen_ids, seen_domains, seen_names = set(), {}, {}
    for tool in data["tools"]:
        errs.extend(validate_tool(tool))
        if not isinstance(tool, dict):
            continue
        tid = tool.get("id")
        if tid in seen_ids:
            errs.append(f"{tid}: duplicate id")
        seen_ids.add(tid)
        if isinstance(tool.get("url"), str):
            # Same domain is allowed for different product pages (e.g. site.app/ and site.app/thumbnails),
            # an identical domain + path is a duplicate.
            dom = normalize_domain(tool["url"])
            if not dom.startswith("t.me/"):
                dom += urlparse(tool["url"].strip().lower()).path.rstrip("/")
            if dom in seen_domains:
                errs.append(f"{tid}: duplicate url {dom} (also {seen_domains[dom]})")
            seen_domains[dom] = tid
        if isinstance(tool.get("name"), str):
            nn = normalize_name(tool["name"])
            if nn in seen_names:
                errs.append(f"{tid}: duplicate name (also {seen_names[nn]})")
            seen_names[nn] = tid
    if data["tools"] and data["tools"][0].get("id") != "koshorts-ai-studio":
        errs.append("koshorts-ai-studio must stay the first tool in the list")
    return errs


def load_catalog(path: Path = TOOLS_PATH) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_catalog(data: dict, path: Path = TOOLS_PATH) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def main() -> int:
    try:
        data = load_catalog()
    except json.JSONDecodeError as err:
        lines = TOOLS_PATH.read_text(encoding="utf-8").splitlines()
        print(f"tools.json is not valid JSON: {err.msg} at line {err.lineno}, column {err.colno}")
        print("Usually a missing/extra comma or wrong quotes near this place:")
        for n in range(max(1, err.lineno - 3), min(len(lines), err.lineno + 1) + 1):
            print(f"  {n:>5} | {lines[n - 1]}")
        return 1
    errs = validate_catalog(data)
    if errs:
        print(f"tools.json: {len(errs)} problem(s)")
        for e in errs:
            print("  -", e)
        return 1
    counts: dict[str, int] = {}
    for t in data["tools"]:
        counts[t["category"]] = counts.get(t["category"], 0) + 1
    print(f"tools.json OK: {len(data['tools'])} tools", counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
