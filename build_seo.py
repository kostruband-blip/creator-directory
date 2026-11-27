#!/usr/bin/env python3
"""
Regenerates the static SEO layer from tools.json:
  * pre-rendered English cards inside index.html (crawlers + no-JS fallback)
  * JSON-LD (WebSite + ItemList of SoftwareApplication)
  * canonical / hreflang / og:url tags
  * sitemap.xml and robots.txt
  * static pages for every tool: /tools/<id>/, /tools/<id>/ru/, /tools/<id>/uk/ (build_pages.py)
  * collection landing pages /best/<slug>/ in 3 languages (build_collections.py)

Run after every change of tools.json:
    SITE_URL=https://your-domain.com python build_seo.py
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
from datetime import date
from pathlib import Path

import build_collections
import build_pages
from validate_tools import CATEGORIES, load_catalog

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
SITE_URL = os.environ.get("SITE_URL", "https://creator-directory-chi.vercel.app").rstrip("/")

CAT_EN = {
    "shorts": "Shorts & Clips", "captions": "Captions", "dubbing": "AI Dubbing & Voice",
    "thumbnails": "Thumbnails", "analytics": "Analytics", "telegram": "Telegram Tools",
}
PRICE_EN = {"free": "Free", "freemium": "Freemium", "paid": "Paid"}
LANG_PATHS = {"en": "/", "ru": "/ru", "uk": "/uk"}


def e(s: str) -> str:
    return html.escape(str(s), quote=True)


def sorted_tools(tools: list[dict]) -> list[dict]:
    return sorted(tools, key=lambda t: (not t.get("pinned", False), not t.get("featured", False), tools.index(t)))


def initials(name: str) -> str:
    parts = re.sub(r"[^A-Za-z0-9 ]", " ", name).split()
    return ((parts[0][0] if parts else "?") + (parts[1][0] if len(parts) > 1 else "")).upper()


def card_html(t: dict) -> str:
    rel = build_pages.rel_for(t["url"])
    meta = []
    if t.get("featured"):
        meta.append('<span class="pill pill--featured"><span class="i i-star" aria-hidden="true"></span> Featured</span>')
    if t.get("badge_en"):
        meta.append(f'<span class="pill pill--badge">{e(t["badge_en"])}</span>')
    meta.append(f'<span class="pill">{e(CAT_EN[t["category"]])}</span>')
    meta.append(f'<span class="pill pill--{e(t["pricing_type"])}">{e(PRICE_EN[t["pricing_type"]])}</span>')
    tags = "".join(f'<span class="tag">#{e(tag)}</span>' for tag in t["tags"])
    actions = []
    if t.get("tg"):
        actions.append(f'<a class="btn btn--tg" href="{e(t["tg"])}" target="_blank" rel="noopener">Open in Telegram</a>')
    if t["url"] != t.get("tg"):
        cls = "btn--gold" if t.get("featured") else "btn--ghost"
        actions.append(f'<a class="btn {cls}" href="{e(t["url"])}" target="_blank" rel="{rel}">Visit website <span class="i i-arrow" aria-hidden="true"></span></a>')
    actions.append(f'<a class="btn btn--link" href="/tools/{e(t["id"])}/">Details</a>')
    case = (f'<a class="case-link" href="{e(t["case_study"])}" target="_blank" rel="noopener"><span class="i i-play" aria-hidden="true"></span> Live Case Study: 100% automated Shorts workflow</a>'
            if t.get("case_study") else "")
    return (
        f'<article class="card{" card--featured" if t.get("featured") else ""}" id="{e(t["id"])}">'
        f'<div class="card__top"><div class="card__logo" aria-hidden="true">{e(initials(t["name"]))}</div>'
        f'<div class="card__head"><h3 class="card__title"><a href="/tools/{e(t["id"])}/">{e(t["name"])}</a></h3>'
        f'<div class="card__meta">{"".join(meta)}</div></div></div>'
        f'<p class="card__desc">{e(t["desc_en"])}</p>'
        f'<p class="card__price"><strong>Price:</strong> {e(t["pricing_en"])}</p>'
        f'<div class="tags">{tags}</div>{case}'
        f'<div class="card__actions">{"".join(actions)}</div></article>'
    )


def jsonld(tools: list[dict]) -> str:
    data = [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "CreatorDirectory",
            "url": SITE_URL + "/",
            "inLanguage": ["en", "ru", "uk"],
            "potentialAction": {
                "@type": "SearchAction",
                "target": SITE_URL + "/?q={search_term_string}",
                "query-input": "required name=search_term_string",
            },
        },
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": "Best AI tools and Telegram bots for video creators",
            "numberOfItems": len(tools),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "url": f"{SITE_URL}/#{t['id']}",
                    "item": {
                        "@type": "SoftwareApplication",
                        "name": t["name"],
                        "url": t["url"],
                        "description": t["desc_en"],
                        "applicationCategory": "MultimediaApplication",
                        "operatingSystem": "Web, Telegram" if t.get("tg") else "Web",
                        "keywords": ", ".join(t["tags"]),
                        "offers": {
                            "@type": "Offer",
                            "price": "0",
                            "priceCurrency": "USD",
                            "description": t["pricing_en"],
                        } if t["pricing_type"] in ("free", "freemium") else {
                            "@type": "Offer",
                            "priceCurrency": "USD",
                            "description": t["pricing_en"],
                        },
                    },
                }
                for i, t in enumerate(tools)
            ],
        },
    ]
    # '</' must never appear raw inside a <script> block
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def head_tags() -> str:
    lines = [f'<link rel="canonical" href="{SITE_URL}/" />']
    for lang, path in LANG_PATHS.items():
        href = SITE_URL + ("/" if path == "/" else path)
        lines.append(f'<link rel="alternate" hreflang="{lang}" href="{href}" />')
    lines += [
        f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}/" />',
        f'<meta property="og:url" content="{SITE_URL}/" />',
        f'<meta property="og:image" content="{SITE_URL}/assets/og.png" />',
        f'<meta name="twitter:image" content="{SITE_URL}/assets/og.png" />',
    ]
    return "\n".join("  " + l for l in lines)


def replace_block(text: str, name: str, content: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:START -->)(.*?)(\s*<!-- {name}:END -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"Marker {name} not found in index.html")
    return pattern.sub(lambda m: m.group(1) + "\n" + content + m.group(3), text, count=1)


def sitemap_group(paths: list[str], lastmod: str, freq: str, prio: str) -> list[str]:
    """One <url> per language, each listing all hreflang alternates. paths = [en, ru, uk]."""
    alts = "".join(
        f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE_URL}{p}"/>' for l, p in zip(build_pages.LANGS, paths)
    ) + f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE_URL}{paths[0]}"/>'
    return [
        f"  <url>\n    <loc>{SITE_URL}{p}</loc>{alts}\n    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>{freq}</changefreq>\n    <priority>{prio if i == 0 else f'{float(prio) - 0.1:.1f}'}</priority>\n  </url>"
        for i, p in enumerate(paths)
    ]


def build_sitemap(updated: str, tools: list[dict], collection_groups: list[list[str]]) -> str:
    urls = sitemap_group(["/", "/ru", "/uk"], updated, "daily", "1.0")
    for group in collection_groups:
        urls += sitemap_group(group, updated, "weekly", "0.9")
    for t in tools:
        lastmod = t["added_at"] if t["added_at"] > updated else updated
        urls += sitemap_group([build_pages.page_path(t["id"], l) for l in build_pages.LANGS], lastmod, "monthly", "0.7")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(urls) + "\n</urlset>\n"
    )


def collections_block() -> str:
    """Links to /best/<slug>/ on the home page. app.js swaps label + URL for RU/UA."""
    links = []
    for c in build_collections.COLLECTIONS:
        links.append(f'          <a class="chip chip--link" href="/best/{c["slug"]}/" data-col="{c["slug"]}">{e(c["en"]["label"])}</a>')
    return "\n".join(links)


def update_app_js() -> None:
    """RU/UA labels of the collections live in app.js (index.html must stay Cyrillic-free)."""
    path = ROOT / "assets" / "app.js"
    labels = {l: {c["slug"]: c[l]["label"] for c in build_collections.COLLECTIONS} for l in build_pages.LANGS}
    js = "  var COLLECTION_LABELS = " + json.dumps(labels, ensure_ascii=False) + ";"
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"(/\* COLLECTIONS:START \*/)(.*?)(/\* COLLECTIONS:END \*/)", re.S)
    if not pattern.search(text):
        raise SystemExit("Marker COLLECTIONS not found in assets/app.js")
    path.write_text(pattern.sub(lambda m: m.group(1) + "\n" + js + "\n  " + m.group(3), text, count=1), encoding="utf-8")


def ecosystem_block() -> str:
    return "\n".join(
        f'        <a href="{e(u)}" target="_blank" rel="noopener">{e(n)}</a>' for n, u in build_pages.ECOSYSTEM
    )


def bust_asset_cache(text: str) -> str:
    """/assets/app.js -> /assets/app.js?v=<content hash> so browsers never run stale JS/CSS."""
    for name in ("app.js", "styles.css"):
        digest = hashlib.sha256((ROOT / "assets" / name).read_bytes()).hexdigest()[:10]
        text = re.sub(rf'/assets/{re.escape(name)}(\?v=[0-9a-f]+)?"', f'/assets/{name}?v={digest}"', text)
    return text


def main() -> None:
    data = load_catalog()
    tools = sorted_tools(data["tools"])
    update_app_js()
    text = INDEX.read_text(encoding="utf-8")
    text = replace_block(text, "SEO:HEAD", head_tags())
    text = replace_block(text, "SEO:JSONLD", f'  <script type="application/ld+json">{jsonld(tools)}</script>')
    text = replace_block(text, "PRERENDER", "\n".join("        " + card_html(t) for t in tools))
    text = replace_block(text, "COLLECTIONS", collections_block())
    text = replace_block(text, "ECOSYSTEM", ecosystem_block())
    text = bust_asset_cache(text)
    INDEX.write_text(text, encoding="utf-8")

    updated = data.get("updated_at") or date.today().isoformat()
    pages = build_pages.build(tools, SITE_URL)
    groups = build_collections.build(tools, SITE_URL, updated)
    (ROOT / "sitemap.xml").write_text(build_sitemap(updated, tools, groups), encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    print(f"SEO layer rebuilt for {len(tools)} tools, {len(pages)} tool pages, "
          f"{sum(len(g) for g in groups)} collection pages ({SITE_URL})")


if __name__ == "__main__":
    main()
