#!/usr/bin/env python3
"""
Static SEO pages for every tool, in 3 languages:

    /tools/<id>/        English
    /tools/<id>/ru/     Russian
    /tools/<id>/uk/     Ukrainian

Each page: own <title>/description, canonical + hreflang, JSON-LD (SoftwareApplication +
BreadcrumbList), key facts, "Alternatives to <tool>" (KoShorts first) and CTAs.
Called from build_seo.py — the whole ./tools/ directory is regenerated on every build.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "tools"
LANGS = ("en", "ru", "uk")
HOME = {"en": "/", "ru": "/ru", "uk": "/uk"}
OG_LOCALE = {"en": "en_US", "ru": "ru_RU", "uk": "uk_UA"}
BOT = "https://t.me/remtex_shorts_ai_bot"
YOUTUBE_CASE = "https://www.youtube.com/@rem-tex"
FLAGSHIP_ID = "koshorts-ai-studio"
MAX_ALTERNATIVES = 6

T = {
    "en": {
        "title": "{name} — Pricing, Features and Alternatives | CreatorDirectory",
        "home": "Home", "catalog": "Catalog", "submit": "Submit Tool", "skip": "Skip to content",
        "cat": {"shorts": "Shorts & Clips", "captions": "Captions", "dubbing": "AI Dubbing & Voice",
                "thumbnails": "Thumbnails", "analytics": "Analytics", "telegram": "Telegram Tools"},
        "price": {"free": "Free", "freemium": "Freemium", "paid": "Paid"},
        "facts": "Key facts", "f_cat": "Category", "f_model": "Pricing model", "f_price": "Price",
        "f_tg": "Telegram bot", "f_added": "Added to catalog", "yes": "Yes", "no": "No",
        "tags": "Tags", "visit": "Visit website", "open_tg": "Open in Telegram", "featured": "Featured",
        "alts": "Alternatives to {name}",
        "alts_intro": "Other {cat} tools for YouTube, TikTok, Reels and Telegram creators.",
        "alts_pick": "Our pick for turning long YouTube videos into Shorts is KoShorts AI Studio.",
        "details": "Details", "all_tools": "Browse all {cat}",
        "cta_title": "Turn long videos into Shorts in 2 minutes",
        "cta_text": "KoShorts AI Studio works right inside Telegram: paste a YouTube link up to 60 minutes and get 9:16 Shorts with hook titles and dynamic subtitles. 10 videos free, no card required.",
        "cta_btn": "Try KoShorts free",
        "submit_title": "Own an AI tool or Telegram bot?",
        "submit_text": "List it in CreatorDirectory for free, get published in 24 hours or take a Top-3 Featured spot.",
        "submit_btn": "Submit your tool",
        "case": "Live Case Study: 100% automated Shorts workflow",
        "rights": "All rights reserved.", "powered": "Powered by",
    },
    "ru": {
        "title": "{name} — цены, возможности и альтернативы | CreatorDirectory",
        "home": "Главная", "catalog": "Каталог", "submit": "Добавить сервис", "skip": "Перейти к содержимому",
        "cat": {"shorts": "Shorts и клипы", "captions": "Субтитры", "dubbing": "ИИ-дубляж и голос",
                "thumbnails": "Превью", "analytics": "Аналитика", "telegram": "Инструменты Telegram"},
        "price": {"free": "Бесплатно", "freemium": "Условно-бесплатно", "paid": "Платно"},
        "facts": "Коротко о сервисе", "f_cat": "Категория", "f_model": "Модель оплаты", "f_price": "Цена",
        "f_tg": "Telegram-бот", "f_added": "Добавлен в каталог", "yes": "Есть", "no": "Нет",
        "tags": "Теги", "visit": "Перейти на сайт", "open_tg": "Открыть в Telegram", "featured": "Закреплено",
        "alts": "Альтернативы {name}",
        "alts_intro": "Другие сервисы в категории «{cat}» для авторов YouTube, TikTok, Reels и Telegram.",
        "alts_pick": "Наш выбор для нарезки длинных YouTube-видео в Shorts — KoShorts AI Studio.",
        "details": "Подробнее", "all_tools": "Все сервисы: {cat}",
        "cta_title": "Превратите длинное видео в Shorts за 2 минуты",
        "cta_text": "KoShorts AI Studio работает прямо в Telegram: отправьте ссылку на YouTube-видео до 60 минут и получите Shorts 9:16 с цепляющими заголовками и динамическими субтитрами. 10 видео бесплатно, без карты.",
        "cta_btn": "Попробовать KoShorts бесплатно",
        "submit_title": "У вас есть ИИ-сервис или Telegram-бот?",
        "submit_text": "Разместите его в CreatorDirectory бесплатно, опубликуйте за 24 часа или займите место в ТОП-3.",
        "submit_btn": "Добавить сервис",
        "case": "Живой кейс: Shorts на 100% на автомате",
        "rights": "Все права защищены.", "powered": "Работает на",
    },
    "uk": {
        "title": "{name} — ціни, можливості та альтернативи | CreatorDirectory",
        "home": "Головна", "catalog": "Каталог", "submit": "Додати сервіс", "skip": "Перейти до вмісту",
        "cat": {"shorts": "Shorts і кліпи", "captions": "Субтитри", "dubbing": "ШІ-дубляж і голос",
                "thumbnails": "Прев'ю", "analytics": "Аналітика", "telegram": "Інструменти Telegram"},
        "price": {"free": "Безкоштовно", "freemium": "Умовно безкоштовно", "paid": "Платно"},
        "facts": "Коротко про сервіс", "f_cat": "Категорія", "f_model": "Модель оплати", "f_price": "Ціна",
        "f_tg": "Telegram-бот", "f_added": "Додано до каталогу", "yes": "Є", "no": "Немає",
        "tags": "Теги", "visit": "Перейти на сайт", "open_tg": "Відкрити в Telegram", "featured": "Закріплено",
        "alts": "Альтернативи {name}",
        "alts_intro": "Інші сервіси в категорії «{cat}» для авторів YouTube, TikTok, Reels і Telegram.",
        "alts_pick": "Наш вибір для нарізки довгих YouTube-відео в Shorts — KoShorts AI Studio.",
        "details": "Детальніше", "all_tools": "Усі сервіси: {cat}",
        "cta_title": "Перетворіть довге відео на Shorts за 2 хвилини",
        "cta_text": "KoShorts AI Studio працює просто в Telegram: надішліть посилання на YouTube-відео до 60 хвилин і отримайте Shorts 9:16 із чіпкими заголовками та динамічними субтитрами. 10 відео безкоштовно, без картки.",
        "cta_btn": "Спробувати KoShorts безкоштовно",
        "submit_title": "Маєте ШІ-сервіс або Telegram-бота?",
        "submit_text": "Розмістіть його в CreatorDirectory безкоштовно, опублікуйте за 24 години або займіть місце в ТОП-3.",
        "submit_btn": "Додати сервіс",
        "case": "Живий кейс: Shorts на 100% на автоматі",
        "rights": "Усі права захищені.", "powered": "Працює на",
    },
}


def e(s) -> str:
    return html.escape(str(s), quote=True)


def initials(name: str) -> str:
    parts = re.sub(r"[^A-Za-z0-9 ]", " ", name).split()
    return ((parts[0][0] if parts else "?") + (parts[1][0] if len(parts) > 1 else "")).upper()


def page_path(tool_id: str, lang: str) -> str:
    return f"/tools/{tool_id}/" + ("" if lang == "en" else f"{lang}/")


def asset_version(name: str) -> str:
    return hashlib.sha256((ROOT / "assets" / name).read_bytes()).hexdigest()[:10]


def meta_description(text: str, limit: int = 158) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + "…"


def first_sentence(text: str) -> str:
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    return m.group(1) if m else text


def alternatives(tool: dict, tools: list[dict]) -> list[dict]:
    """KoShorts first (unless it is this page), then same-category tools (featured first)."""
    flagship = next((t for t in tools if t["id"] == FLAGSHIP_ID), None)
    same = [t for t in tools if t["category"] == tool["category"] and t["id"] not in (tool["id"], FLAGSHIP_ID)]
    same.sort(key=lambda t: (not t.get("featured", False), tools.index(t)))
    result = ([flagship] if flagship and tool["id"] != FLAGSHIP_ID else []) + same
    return result[:MAX_ALTERNATIVES]


def jsonld(tool: dict, lang: str, site: str) -> str:
    d = T[lang]
    offer = {"@type": "Offer", "priceCurrency": "USD", "description": tool[f"pricing_{lang}"]}
    if tool["pricing_type"] in ("free", "freemium"):
        offer["price"] = "0"
    data = [
        {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": tool["name"],
            "url": tool["url"],
            "description": tool[f"desc_{lang}"],
            "applicationCategory": "MultimediaApplication",
            "operatingSystem": "Web, Telegram" if tool.get("tg") else "Web",
            "keywords": ", ".join(tool["tags"]),
            "inLanguage": lang,
            "offers": offer,
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": d["home"], "item": site + HOME[lang]},
                {"@type": "ListItem", "position": 2, "name": d["cat"][tool["category"]],
                 "item": f"{site}{HOME[lang]}?cat={tool['category']}"},
                {"@type": "ListItem", "position": 3, "name": tool["name"], "item": site + page_path(tool["id"], lang)},
            ],
        },
    ]
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render(tool: dict, tools: list[dict], lang: str, site: str, css_v: str) -> str:
    d = T[lang]
    name, cat = tool["name"], tool["category"]
    own = "koshorts.vercel.app" in tool["url"]
    rel = "noopener" if own else "noopener nofollow"
    url_self = site + page_path(tool["id"], lang)
    home = HOME[lang]
    title = d["title"].format(name=name)
    desc = meta_description(f"{name}: {tool[f'desc_{lang}']}")

    alternates = "\n".join(
        f'  <link rel="alternate" hreflang="{l}" href="{site}{page_path(tool["id"], l)}" />' for l in LANGS
    ) + f'\n  <link rel="alternate" hreflang="x-default" href="{site}{page_path(tool["id"], "en")}" />'
    og_alt = "\n".join(f'  <meta property="og:locale:alternate" content="{OG_LOCALE[l]}" />' for l in LANGS if l != lang)

    current = ' aria-current="page"'
    lang_switch = "".join(
        f'<a class="lang__btn" href="{page_path(tool["id"], l)}" hreflang="{l}" lang="{l}"'
        f'{current if l == lang else ""}>{"UA" if l == "uk" else l.upper()}</a>'
        for l in LANGS
    )

    pills = []
    if tool.get("featured"):
        pills.append(f'<span class="pill pill--featured"><span class="i i-star" aria-hidden="true"></span> {e(d["featured"])}</span>')
    if tool.get(f"badge_{lang}"):
        pills.append(f'<span class="pill pill--badge">{e(tool[f"badge_{lang}"])}</span>')
    pills.append(f'<a class="pill pill--link" href="{home}?cat={cat}">{e(d["cat"][cat])}</a>')
    pills.append(f'<span class="pill pill--{tool["pricing_type"]}">{e(d["price"][tool["pricing_type"]])}</span>')

    actions = []
    if tool.get("tg"):
        actions.append(f'<a class="btn btn--tg" href="{e(tool["tg"])}" target="_blank" rel="noopener">{e(d["open_tg"])}</a>')
    if tool["url"] != tool.get("tg"):
        cls = "btn--gold" if tool.get("featured") else "btn--primary"
        actions.append(f'<a class="btn {cls}" href="{e(tool["url"])}" target="_blank" rel="{rel}">{e(d["visit"])} <span class="i i-arrow" aria-hidden="true"></span></a>')
    case = (f'<a class="case-link" href="{e(tool["case_study"])}" target="_blank" rel="noopener"><span class="i i-play" aria-hidden="true"></span> {e(d["case"])}</a>'
            if tool.get("case_study") else "")

    facts = [
        (d["f_cat"], f'<a href="{home}?cat={cat}">{e(d["cat"][cat])}</a>'),
        (d["f_model"], e(d["price"][tool["pricing_type"]])),
        (d["f_price"], e(tool[f"pricing_{lang}"])),
        (d["f_tg"], f'<a href="{e(tool["tg"])}" target="_blank" rel="noopener">{e(tool["tg"].replace("https://", ""))}</a>'
         if tool.get("tg") else e(d["no"])),
        (d["f_added"], e(tool["added_at"])),
    ]
    facts_html = "".join(f"<div><dt>{e(k)}</dt><dd>{v}</dd></div>" for k, v in facts)
    tags_html = "".join(f'<span class="tag">#{e(t)}</span>' for t in tool["tags"])

    featured_pill = '<span class="pill pill--featured"><span class="i i-star" aria-hidden="true"></span> ' + e(d["featured"]) + "</span>"
    alt_cards = []
    for a in alternatives(tool, tools):
        flagship = a["id"] == FLAGSHIP_ID
        alt_cards.append(
            f'<article class="card{" card--featured" if flagship else ""}">'
            f'<div class="card__top"><div class="card__logo" aria-hidden="true">{e(initials(a["name"]))}</div>'
            f'<div class="card__head"><h3 class="card__title"><a href="{page_path(a["id"], lang)}">{e(a["name"])}</a></h3>'
            f'<div class="card__meta">{featured_pill if flagship else ""}'
            f'<span class="pill pill--{a["pricing_type"]}">{e(d["price"][a["pricing_type"]])}</span></div></div></div>'
            f'<p class="card__desc">{e(first_sentence(a[f"desc_{lang}"]))}</p>'
            f'<div class="card__actions"><a class="btn {"btn--gold" if flagship else "btn--ghost"}" href="{page_path(a["id"], lang)}">{e(d["details"])}</a></div>'
            f"</article>"
        )
    intro = d["alts_intro"].format(cat=d["cat"][cat])
    if tool["id"] != FLAGSHIP_ID:
        intro += " " + d["alts_pick"]

    start = "cd_" + re.sub(r"[^A-Za-z0-9_-]", "", tool["id"])[:60]
    cta = "" if tool["id"] == FLAGSHIP_ID else f"""
    <section class="promo" aria-labelledby="promoTitle">
      <div>
        <h2 id="promoTitle">{e(d["cta_title"])}</h2>
        <p>{e(d["cta_text"])}</p>
      </div>
      <div class="promo__actions">
        <a class="btn btn--gold" href="{BOT}?start={start}" target="_blank" rel="noopener">{e(d["cta_btn"])}</a>
        <a class="case-link" href="{YOUTUBE_CASE}" target="_blank" rel="noopener"><span class="i i-play" aria-hidden="true"></span> {e(d["case"])}</a>
      </div>
    </section>"""

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <meta name="theme-color" content="#0b0d12" />
  <link rel="canonical" href="{url_self}" />
{alternates}
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="CreatorDirectory" />
  <meta property="og:title" content="{e(title)}" />
  <meta property="og:description" content="{e(desc)}" />
  <meta property="og:url" content="{url_self}" />
  <meta property="og:image" content="{site}/assets/og.png" />
  <meta property="og:locale" content="{OG_LOCALE[lang]}" />
{og_alt}
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:image" content="{site}/assets/og.png" />
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml" />
  <link rel="stylesheet" href="/assets/styles.css?v={css_v}" />
  <script type="application/ld+json">{jsonld(tool, lang, site)}</script>
  <script>try{{localStorage.setItem("cd_lang","{lang}")}}catch(e){{}}</script>
</head>
<body>
  <a class="skip-link" href="#main">{e(d["skip"])}</a>
  <header class="header">
    <div class="container header__inner">
      <a class="logo" href="{home}" aria-label="CreatorDirectory">
        <span class="logo__mark" aria-hidden="true"><span class="i i-play" aria-hidden="true"></span></span>
        <span>Creator<b>Directory</b></span>
      </a>
      <nav class="nav" aria-label="Main">
        <a href="{home}#catalog">{e(d["catalog"])}</a>
        <a href="{home}#submit">{e(d["submit"])}</a>
      </nav>
      <div class="lang" role="group" aria-label="Language">{lang_switch}</div>
    </div>
  </header>

  <main id="main" class="container tool-page">
    <nav class="crumbs" aria-label="Breadcrumb">
      <a href="{home}">{e(d["home"])}</a> <span aria-hidden="true">&rsaquo;</span>
      <a href="{home}?cat={cat}">{e(d["cat"][cat])}</a> <span aria-hidden="true">&rsaquo;</span>
      <span aria-current="page">{e(name)}</span>
    </nav>

    <article class="tool-hero card{" card--featured" if tool.get("featured") else ""}">
      <div class="card__top">
        <div class="card__logo card__logo--lg" aria-hidden="true">{e(initials(name))}</div>
        <div class="card__head">
          <h1 class="tool-hero__title">{e(name)}</h1>
          <div class="card__meta">{"".join(pills)}</div>
        </div>
      </div>
      <p class="tool-hero__lead">{e(tool[f"desc_{lang}"])}</p>
      {case}
      <div class="card__actions">{"".join(actions)}</div>
    </article>

    <section class="facts" aria-labelledby="factsTitle">
      <h2 id="factsTitle" class="tool-h2">{e(d["facts"])}</h2>
      <dl class="facts__list">{facts_html}</dl>
      <h3 class="facts__tags-title">{e(d["tags"])}</h3>
      <div class="tags">{tags_html}</div>
    </section>
{cta}
    <section class="alts" aria-labelledby="altsTitle">
      <h2 id="altsTitle" class="tool-h2">{e(d["alts"].format(name=name))}</h2>
      <p class="alts__intro">{e(intro)}</p>
      <div class="grid">{"".join(alt_cards)}</div>
      <p class="alts__more"><a href="{home}?cat={cat}">{e(d["all_tools"].format(cat=d["cat"][cat]))} <span class="i i-arrow" aria-hidden="true"></span></a></p>
    </section>

    <section class="promo promo--submit" aria-labelledby="submitTitle">
      <div>
        <h2 id="submitTitle">{e(d["submit_title"])}</h2>
        <p>{e(d["submit_text"])}</p>
      </div>
      <div class="promo__actions">
        <a class="btn btn--primary" href="{home}#submit">{e(d["submit_btn"])}</a>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div class="container footer__inner">
      <p>&copy; 2026 CreatorDirectory. {e(d["rights"])}</p>
      <p class="footer__case"><a href="{YOUTUBE_CASE}" target="_blank" rel="noopener" class="footer__yt"><span class="i i-play" aria-hidden="true"></span> {e(d["case"])}</a></p>
      <p>{e(d["powered"])} <a href="https://koshorts.vercel.app" target="_blank" rel="noopener">KoShorts AI Studio</a></p>
    </div>
  </footer>
</body>
</html>
"""


def build(tools: list[dict], site: str) -> list[str]:
    """Regenerate ./tools/. Returns the list of page paths (for the sitemap)."""
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    css_v = asset_version("styles.css")
    paths = []
    for tool in tools:
        for lang in LANGS:
            rel = page_path(tool["id"], lang)
            target = ROOT / rel.strip("/") / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render(tool, tools, lang, site, css_v), encoding="utf-8")
            paths.append(rel)
    return paths
