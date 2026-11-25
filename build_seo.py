#!/usr/bin/env python3
"""
Regenerates the static SEO layer from tools.json:
  * pre-rendered English cards inside index.html (crawlers + no-JS fallback)
  * JSON-LD (WebSite + ItemList of SoftwareApplication)
  * canonical / hreflang / og:url tags
  * sitemap.xml and robots.txt

Run after every change of tools.json:
    SITE_URL=https://your-domain.com python build_seo.py
"""
from __future__ import annotations

import html
import json
import os
import re
from datetime import date
from pathlib import Path

from validate_tools import CATEGORIES, load_catalog

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
SITE_URL = os.environ.get("SITE_URL", "https://creator-directory.vercel.app").rstrip("/")

CAT_EN = {
    "shorts": "Shorts & Clips", "captions": "Captions", "dubbing": "AI Dubbing & Voice",
    "thumbnails": "Thumbnails", "analytics": "Analytics", "telegram": "Telegram Tools",
}
PRICE_EN = {"free": "Free", "freemium": "Freemium", "paid": "Paid"}
LANG_PATHS = {"en": "/", "ru": "/ru", "uk": "/uk"}


def e(s: str) -> str:
    return html.escape(str(s), quote=True)


def sorted_tools(tools: list[dict]) -> list[dict]:
    return sorted(tools, key=lambda t: (not t.get("featured", False), tools.index(t)))


def initials(name: str) -> str:
    parts = re.sub(r"[^A-Za-z0-9 ]", " ", name).split()
    return ((parts[0][0] if parts else "?") + (parts[1][0] if len(parts) > 1 else "")).upper()


def card_html(t: dict) -> str:
    own = "koshorts.vercel.app" in t["url"]
    rel = "noopener" if own else "noopener nofollow"
    meta = []
    if t.get("featured"):
        meta.append('<span class="pill pill--featured">&#9733; Featured</span>')
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
        actions.append(f'<a class="btn {cls}" href="{e(t["url"])}" target="_blank" rel="{rel}">Visit website &rarr;</a>')
    return (
        f'<article class="card{" card--featured" if t.get("featured") else ""}" id="{e(t["id"])}">'
        f'<div class="card__top"><div class="card__logo" aria-hidden="true">{e(initials(t["name"]))}</div>'
        f'<div class="card__head"><h3 class="card__title"><a href="{e(t["url"])}" target="_blank" rel="{rel}">{e(t["name"])}</a></h3>'
        f'<div class="card__meta">{"".join(meta)}</div></div></div>'
        f'<p class="card__desc">{e(t["desc_en"])}</p>'
        f'<p class="card__price"><strong>Price:</strong> {e(t["pricing_en"])}</p>'
        f'<div class="tags">{tags}</div>'
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


def build_sitemap(updated: str) -> str:
    urls = []
    for cat in [None, *CATEGORIES]:
        for lang, path in LANG_PATHS.items():
            base = SITE_URL + ("/" if path == "/" else path)
            loc = base + (f"?cat={cat}" if cat else "")
            alts = "".join(
                f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE_URL + ("/" if p == "/" else p) + (f"?cat={cat}" if cat else "")}"/>'
                for l, p in LANG_PATHS.items()
            )
            urls.append(
                f"  <url>\n    <loc>{e(loc)}</loc>{alts.replace('&', '&amp;')}\n"
                f"    <lastmod>{updated}</lastmod>\n    <changefreq>weekly</changefreq>\n"
                f"    <priority>{'1.0' if not cat and lang == 'en' else '0.8' if not cat else '0.6'}</priority>\n  </url>"
            )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(urls) + "\n</urlset>\n"
    )


def main() -> None:
    data = load_catalog()
    tools = sorted_tools(data["tools"])
    text = INDEX.read_text(encoding="utf-8")
    text = replace_block(text, "SEO:HEAD", head_tags())
    text = replace_block(text, "SEO:JSONLD", f'  <script type="application/ld+json">{jsonld(tools)}</script>')
    text = replace_block(text, "PRERENDER", "\n".join("        " + card_html(t) for t in tools))
    INDEX.write_text(text, encoding="utf-8")

    updated = data.get("updated_at") or date.today().isoformat()
    (ROOT / "sitemap.xml").write_text(build_sitemap(updated), encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    print(f"SEO layer rebuilt for {len(tools)} tools ({SITE_URL})")


if __name__ == "__main__":
    main()
