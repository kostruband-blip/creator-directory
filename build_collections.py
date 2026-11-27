#!/usr/bin/env python3
"""
Programmatic SEO: "best tools for <task>" collection pages, in 3 languages.

    /best/                         hub with all collections
    /best/<slug>/  /best/<slug>/ru/  /best/<slug>/uk/

Every page targets a real search intent ("нейросети для обложек ютуб", "бот для нарезки shorts",
"free ai tools for youtubers"...), lists the matching tools from tools.json with a numbered
ranking, has an FAQ built from the data (free options, Telegram bots, where to start),
JSON-LD (ItemList + FAQPage + BreadcrumbList), canonical + hreflang.
Ordering follows the catalog rules: KoShorts first, then our other pinned tools that fit the page,
then featured, then the rest in file order.

Called from build_seo.py — ./best/ is regenerated on every build.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import build_pages as bp
from build_pages import e

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "best"
LANGS = bp.LANGS

# filter: ("cat", <category>) or ("price", [pricing types])
COLLECTIONS = [
    {
        "slug": "ai-shorts-clippers", "filter": ("cat", "shorts"),
        "en": {"label": "AI Shorts clippers",
               "h1": "Best AI Shorts Clippers and Bots in 2026",
               "title": "Best AI Shorts Clippers & Bots to Turn Videos into Shorts (2026)",
               "intro": "AI tools and Telegram bots that cut long YouTube videos, podcasts and streams into vertical Shorts, TikToks and Reels with captions. Compared by price and features, with free options marked."},
        "ru": {"label": "Нарезка Shorts нейросетью",
               "h1": "Лучшие нейросети и боты для нарезки Shorts в 2026",
               "title": "Нейросети и боты для нарезки Shorts из длинных видео (2026)",
               "intro": "ИИ-сервисы и Telegram-боты, которые нарезают длинные YouTube-видео, подкасты и стримы на вертикальные Shorts, TikTok и Reels с субтитрами. Сравнение цен и возможностей, бесплатные варианты отмечены."},
        "uk": {"label": "Нарізка Shorts нейромережею",
               "h1": "Найкращі нейромережі та боти для нарізки Shorts у 2026",
               "title": "Нейромережі та боти для нарізки Shorts з довгих відео (2026)",
               "intro": "ШІ-сервіси та Telegram-боти, які нарізають довгі YouTube-відео, подкасти й стріми на вертикальні Shorts, TikTok і Reels із субтитрами. Порівняння цін і можливостей, безкоштовні варіанти позначені."},
    },
    {
        "slug": "ai-subtitle-generators", "filter": ("cat", "captions"),
        "en": {"label": "AI subtitle generators",
               "h1": "Best AI Subtitle and Caption Generators for Video",
               "title": "Best AI Subtitle Generators for YouTube, TikTok & Reels (2026)",
               "intro": "Tools that automatically transcribe your video and add animated captions and subtitles in dozens of languages. Ideal for Shorts, Reels and TikTok, where most viewers watch without sound."},
        "ru": {"label": "Субтитры нейросетью",
               "h1": "Нейросети для автоматических субтитров к видео",
               "title": "Нейросети для субтитров к видео: YouTube, TikTok, Reels (2026)",
               "intro": "Сервисы, которые автоматически расшифровывают видео и добавляют анимированные субтитры на десятках языков. Особенно полезны для Shorts, Reels и TikTok, где большинство смотрит без звука."},
        "uk": {"label": "Субтитри нейромережею",
               "h1": "Нейромережі для автоматичних субтитрів до відео",
               "title": "Нейромережі для субтитрів до відео: YouTube, TikTok, Reels (2026)",
               "intro": "Сервіси, які автоматично розшифровують відео й додають анімовані субтитри десятками мов. Особливо корисні для Shorts, Reels і TikTok, де більшість дивиться без звуку."},
    },
    {
        "slug": "ai-dubbing-voiceover", "filter": ("cat", "dubbing"),
        "en": {"label": "AI dubbing & voiceover",
               "h1": "Best AI Dubbing and Voiceover Tools for Creators",
               "title": "Best AI Dubbing & Voiceover Tools for YouTube (2026)",
               "intro": "AI voice generators, voice cloning and video translation tools that dub your content into other languages and help you reach a global audience without a studio."},
        "ru": {"label": "ИИ-озвучка и дубляж",
               "h1": "ИИ-озвучка и дубляж видео: лучшие сервисы",
               "title": "ИИ-озвучка и дубляж видео для YouTube: лучшие сервисы (2026)",
               "intro": "Генераторы голоса, клонирование голоса и перевод видео с помощью ИИ: озвучьте ролики на других языках и выйдите на зарубежную аудиторию без студии."},
        "uk": {"label": "ШІ-озвучення та дубляж",
               "h1": "ШІ-озвучення та дубляж відео: найкращі сервіси",
               "title": "ШІ-озвучення та дубляж відео для YouTube: найкращі сервіси (2026)",
               "intro": "Генератори голосу, клонування голосу й переклад відео за допомогою ШІ: озвучте ролики іншими мовами та вийдіть на закордонну аудиторію без студії."},
    },
    {
        "slug": "ai-youtube-thumbnails", "filter": ("cat", "thumbnails"),
        "en": {"label": "AI YouTube thumbnails",
               "h1": "Best AI YouTube Thumbnail Makers",
               "title": "Best AI YouTube Thumbnail Makers and Generators (2026)",
               "intro": "AI thumbnail generators, image models, background removers and A/B testers that help you design click-worthy YouTube thumbnails and raise your CTR."},
        "ru": {"label": "Нейросети для обложек YouTube",
               "h1": "Нейросети для обложек YouTube: лучшие сервисы",
               "title": "Нейросети для обложек и превью YouTube (2026)",
               "intro": "ИИ-генераторы обложек, нейросети для изображений, удаление фона и A/B-тесты превью: всё, чтобы делать кликабельные обложки YouTube и повышать CTR."},
        "uk": {"label": "Нейромережі для обкладинок YouTube",
               "h1": "Нейромережі для обкладинок YouTube: найкращі сервіси",
               "title": "Нейромережі для обкладинок і прев'ю YouTube (2026)",
               "intro": "ШІ-генератори обкладинок, нейромережі для зображень, видалення фону та A/B-тести прев'ю: усе, щоб робити клікабельні обкладинки YouTube і підвищувати CTR."},
    },
    {
        "slug": "youtube-analytics-seo", "filter": ("cat", "analytics"),
        "en": {"label": "YouTube analytics & SEO",
               "h1": "Best YouTube Analytics and SEO Tools",
               "title": "Best YouTube Analytics & SEO Tools for Channel Growth (2026)",
               "intro": "Keyword research, competitor tracking, niche finders and analytics dashboards for YouTube, TikTok and Instagram. Find out what to post next and why some videos take off."},
        "ru": {"label": "Аналитика и SEO для YouTube",
               "h1": "Сервисы аналитики и SEO для YouTube",
               "title": "Аналитика и SEO для YouTube: сервисы для роста канала (2026)",
               "intro": "Подбор ключевых слов, отслеживание конкурентов, поиск ниши и аналитика для YouTube, TikTok и Instagram. Узнайте, что снимать дальше и почему одни ролики выстреливают."},
        "uk": {"label": "Аналітика та SEO для YouTube",
               "h1": "Сервіси аналітики та SEO для YouTube",
               "title": "Аналітика та SEO для YouTube: сервіси для зростання каналу (2026)",
               "intro": "Підбір ключових слів, відстеження конкурентів, пошук ніші та аналітика для YouTube, TikTok та Instagram. Дізнайтеся, що знімати далі й чому одні ролики вистрілюють."},
    },
    {
        "slug": "telegram-channel-tools", "filter": ("cat", "telegram"),
        "en": {"label": "Telegram channel tools",
               "h1": "Best Tools and Bots for Telegram Channels",
               "title": "Best Telegram Channel Tools, Bots & Analytics (2026)",
               "intro": "Analytics, ad exchanges, moderation bots, post schedulers and paid subscription tools for growing and monetizing a Telegram channel."},
        "ru": {"label": "Боты для Telegram-каналов",
               "h1": "Боты и сервисы для Telegram-каналов",
               "title": "Боты и сервисы для Telegram-канала: аналитика, реклама, постинг (2026)",
               "intro": "Аналитика, биржи рекламы, боты-модераторы, отложенный постинг и платные подписки: инструменты для роста и монетизации Telegram-канала."},
        "uk": {"label": "Боти для Telegram-каналів",
               "h1": "Боти та сервіси для Telegram-каналів",
               "title": "Боти та сервіси для Telegram-каналу: аналітика, реклама, постинг (2026)",
               "intro": "Аналітика, біржі реклами, боти-модератори, відкладений постинг і платні підписки: інструменти для зростання та монетизації Telegram-каналу."},
    },
    {
        "slug": "free-ai-tools-for-creators", "filter": ("price", ["free", "freemium"]),
        "en": {"label": "Free AI tools for creators",
               "h1": "Free AI Tools for YouTubers and Video Creators",
               "title": "Free AI Tools for YouTubers, TikTokers & Telegram Creators (2026)",
               "intro": "Every tool in this list is free or has a free plan: Shorts clippers, captions, AI voice, thumbnails, analytics and Telegram bots. Start without a credit card."},
        "ru": {"label": "Бесплатные нейросети для авторов",
               "h1": "Бесплатные нейросети для ютуберов и авторов видео",
               "title": "Бесплатные нейросети для ютуберов, тиктокеров и Telegram (2026)",
               "intro": "Все сервисы в этом списке бесплатные или имеют бесплатный тариф: нарезка Shorts, субтитры, ИИ-озвучка, обложки, аналитика и Telegram-боты. Начните без банковской карты."},
        "uk": {"label": "Безкоштовні нейромережі для авторів",
               "h1": "Безкоштовні нейромережі для ютуберів і авторів відео",
               "title": "Безкоштовні нейромережі для ютуберів, тіктокерів і Telegram (2026)",
               "intro": "Усі сервіси в цьому списку безкоштовні або мають безкоштовний тариф: нарізка Shorts, субтитри, ШІ-озвучення, обкладинки, аналітика та Telegram-боти. Почніть без банківської картки."},
    },
]

CAT_TO_SLUG = {c["filter"][1]: c["slug"] for c in COLLECTIONS if c["filter"][0] == "cat"}

T = {
    "en": {
        "hub_title": "Best AI Tools for Creators: Collections by Task | CreatorDirectory",
        "hub_h1": "Best AI tools for creators, by task",
        "hub_intro": "Hand-picked collections of AI tools and Telegram bots for YouTube, TikTok, Reels and Telegram creators. Pick a task and compare the tools side by side.",
        "collections": "Collections", "tools_n": ("tool", "tools", "tools"), "updated": "Updated {date}",
        "rank_title": "Ranking", "more": "More collections", "pick": "Our pick",
        "faq": "Frequently asked questions",
        "q_free": "Which of these tools are free?",
        "a_free": "Free or with a free plan: {list}.", "a_free_none": "All tools in this list are paid; most of them offer a free trial.",
        "q_tg": "Which of them work in Telegram?",
        "a_tg": "These tools work right inside Telegram: {list}.",
        "q_start": "Which one should I start with?",
        "a_start": "Start with {name}: {why}",
        "q_count": "How many tools are in this list?",
        "a_count": "{tools}, checked by hand or by our automated pipeline. The list is updated every week.",
    },
    "ru": {
        "hub_title": "Лучшие нейросети для авторов: подборки по задачам | CreatorDirectory",
        "hub_h1": "Лучшие нейросети для авторов по задачам",
        "hub_intro": "Подборки ИИ-сервисов и Telegram-ботов для авторов YouTube, TikTok, Reels и Telegram. Выберите задачу и сравните сервисы.",
        "collections": "Подборки", "tools_n": ("сервис", "сервиса", "сервисов"), "updated": "Обновлено {date}",
        "rank_title": "Рейтинг", "more": "Другие подборки", "pick": "Наш выбор",
        "faq": "Частые вопросы",
        "q_free": "Какие из этих сервисов бесплатные?",
        "a_free": "Бесплатно или с бесплатным тарифом: {list}.", "a_free_none": "Все сервисы в этом списке платные, у большинства есть пробный период.",
        "q_tg": "Какие из них работают в Telegram?",
        "a_tg": "Прямо в Telegram работают: {list}.",
        "q_start": "С чего начать?",
        "a_start": "Начните с {name}: {why}",
        "q_count": "Сколько сервисов в подборке?",
        "a_count": "{tools}, проверенных вручную или нашим автоматическим конвейером. Подборка обновляется каждую неделю.",
    },
    "uk": {
        "hub_title": "Найкращі нейромережі для авторів: добірки за задачами | CreatorDirectory",
        "hub_h1": "Найкращі нейромережі для авторів за задачами",
        "hub_intro": "Добірки ШІ-сервісів і Telegram-ботів для авторів YouTube, TikTok, Reels і Telegram. Оберіть задачу та порівняйте сервіси.",
        "collections": "Добірки", "tools_n": ("сервіс", "сервіси", "сервісів"), "updated": "Оновлено {date}",
        "rank_title": "Рейтинг", "more": "Інші добірки", "pick": "Наш вибір",
        "faq": "Часті запитання",
        "q_free": "Які з цих сервісів безкоштовні?",
        "a_free": "Безкоштовно або з безкоштовним тарифом: {list}.", "a_free_none": "Усі сервіси в цьому списку платні, більшість має пробний період.",
        "q_tg": "Які з них працюють у Telegram?",
        "a_tg": "Просто в Telegram працюють: {list}.",
        "q_start": "З чого почати?",
        "a_start": "Почніть із {name}: {why}",
        "q_count": "Скільки сервісів у добірці?",
        "a_count": "{tools}, перевірених вручну або нашим автоматичним конвеєром. Добірка оновлюється щотижня.",
    },
}


def plural(n: int, lang: str) -> str:
    """'52 сервиса', '11 сервисов', '1 tool'."""
    one, few, many = T[lang]["tools_n"]
    if lang == "en":
        return f"{n} {one if n == 1 else few}"
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} {one}"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return f"{n} {few}"
    return f"{n} {many}"


def coll_path(slug: str | None, lang: str) -> str:
    base = "/best/" + (f"{slug}/" if slug else "")
    return base + ("" if lang == "en" else f"{lang}/")


def matches(tool: dict, flt: tuple) -> bool:
    kind, val = flt
    return tool["category"] == val if kind == "cat" else tool["pricing_type"] in val


def items_for(coll: dict, tools: list[dict]) -> list[dict]:
    """KoShorts first, then our other pinned tools that fit, then featured, then file order."""
    flagship = [t for t in tools if t["id"] == bp.FLAGSHIP_ID]
    rest = [t for t in tools if t["id"] != bp.FLAGSHIP_ID and matches(t, coll["filter"])]
    rest.sort(key=lambda t: (not t.get("pinned", False), not t.get("featured", False), tools.index(t)))
    return flagship + rest


def name_list(items: list[dict], limit: int = 8) -> str:
    names = [t["name"] for t in items]
    return ", ".join(names[:limit]) + (" …" if len(names) > limit else "")


def faq(coll: dict, items: list[dict], lang: str) -> list[tuple[str, str]]:
    d = T[lang]
    relevant = [t for t in items if matches(t, coll["filter"])]
    out = []
    free = [t for t in items if t["pricing_type"] in ("free", "freemium")]
    if coll["filter"][0] == "cat":
        out.append((d["q_free"], d["a_free"].format(list=name_list(free)) if free else d["a_free_none"]))
    tg = [t for t in items if t.get("tg")]
    if tg:
        out.append((d["q_tg"], d["a_tg"].format(list=name_list(tg))))
    start = relevant[0] if relevant else items[0]
    out.append((d["q_start"], d["a_start"].format(name=start["name"], why=bp.first_sentence(start[f"desc_{lang}"]))))
    out.append((d["q_count"], d["a_count"].format(tools=plural(len(items), lang))))
    return [(q, a.replace("….", "…")) for q, a in out]


def ld(data) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def rank_card(t: dict, i: int, lang: str) -> str:
    d = bp.T[lang]
    hl = t["id"] == bp.FLAGSHIP_ID or bool(t.get("pinned"))
    pills = []
    if hl:
        pills.append(f'<span class="pill pill--featured"><span class="i i-star" aria-hidden="true"></span> {e(d["featured"])}</span>')
    if t.get(f"badge_{lang}"):
        pills.append(f'<span class="pill pill--badge">{e(t[f"badge_{lang}"])}</span>')
    pills.append(f'<span class="pill">{e(d["cat"][t["category"]])}</span>')
    pills.append(f'<span class="pill pill--{t["pricing_type"]}">{e(d["price"][t["pricing_type"]])}</span>')
    actions = [f'<a class="btn {"btn--gold" if hl else "btn--primary"}" href="{bp.page_path(t["id"], lang)}">{e(d["details"])}</a>']
    if t.get("tg"):
        actions.append(f'<a class="btn btn--tg" href="{e(t["tg"])}" target="_blank" rel="noopener">{e(d["open_tg"])}</a>')
    if t["url"] != t.get("tg"):
        actions.append(f'<a class="btn btn--ghost" href="{e(t["url"])}" target="_blank" rel="{bp.rel_for(t["url"])}">{e(d["visit"])} <span class="i i-arrow" aria-hidden="true"></span></a>')
    return (
        f'<li class="rank__item"><article class="card{" card--featured" if hl else ""}" id="{e(t["id"])}">'
        f'<div class="card__top"><div class="rank__num" aria-hidden="true">{i}</div>'
        f'<div class="card__head"><h3 class="card__title"><a href="{bp.page_path(t["id"], lang)}">{e(t["name"])}</a></h3>'
        f'<div class="card__meta">{"".join(pills)}</div></div></div>'
        f'<p class="card__desc">{e(t[f"desc_{lang}"])}</p>'
        f'<p class="card__price"><strong>{e(bp.T[lang]["f_price"])}:</strong> {e(t[f"pricing_{lang}"])}</p>'
        f'<div class="card__actions">{"".join(actions)}</div></article></li>'
    )


def collection_links(lang: str, tools: list[dict], exclude: str | None = None) -> str:
    d = T[lang]
    return "".join(
        f'<a class="chip chip--link" href="{coll_path(c["slug"], lang)}">{e(c[lang]["label"])}'
        f' <span class="chip__count">{e(plural(len(items_for(c, tools)), lang))}</span></a>'
        for c in COLLECTIONS if c["slug"] != exclude
    )


def render_collection(coll: dict, tools: list[dict], lang: str, site: str, css_v: str, updated: str) -> str:
    d, c = T[lang], coll[lang]
    items = items_for(coll, tools)
    url_self = site + coll_path(coll["slug"], lang)
    qa = faq(coll, items, lang)
    jsonld = [
        {"@context": "https://schema.org", "@type": "ItemList", "name": c["h1"], "numberOfItems": len(items),
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": t["name"],
                              "url": site + bp.page_path(t["id"], lang)} for i, t in enumerate(items)]},
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": bp.T[lang]["home"], "item": site + bp.HOME[lang]},
            {"@type": "ListItem", "position": 2, "name": d["collections"], "item": site + coll_path(None, lang)},
            {"@type": "ListItem", "position": 3, "name": c["label"], "item": url_self}]},
    ]
    faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in qa)
    body = f"""
    <nav class="crumbs" aria-label="Breadcrumb">
      <a href="{bp.HOME[lang]}">{e(bp.T[lang]["home"])}</a> <span aria-hidden="true">&rsaquo;</span>
      <a href="{coll_path(None, lang)}">{e(d["collections"])}</a> <span aria-hidden="true">&rsaquo;</span>
      <span aria-current="page">{e(c["label"])}</span>
    </nav>
    <header class="coll-hero">
      <h1 class="tool-hero__title">{e(c["h1"])}</h1>
      <p class="tool-hero__lead">{e(c["intro"])}</p>
      <p class="coll-hero__meta">{e(plural(len(items), lang))} · {e(d["updated"].format(date=updated))}</p>
    </header>
    <section aria-labelledby="rankTitle">
      <h2 id="rankTitle" class="visually-hidden">{e(d["rank_title"])}</h2>
      <ol class="rank grid">{"".join(rank_card(t, i + 1, lang) for i, t in enumerate(items))}</ol>
    </section>
    <section class="container faq faq--inline" aria-labelledby="faqTitle">
      <h2 id="faqTitle" class="tool-h2">{e(d["faq"])}</h2>
      {faq_html}
    </section>
    <section aria-labelledby="moreTitle">
      <h2 id="moreTitle" class="tool-h2">{e(d["more"])}</h2>
      <div class="chips">{collection_links(lang, tools, exclude=coll["slug"])}</div>
    </section>
{bp.submit_promo(lang)}"""
    return bp.page_shell(
        lang=lang, site=site, css_v=css_v, title=c["title"], desc=bp.meta_description(c["intro"]),
        path_for=lambda l: coll_path(coll["slug"], l), jsonld=ld(jsonld), body=body,
    )


def render_hub(tools: list[dict], lang: str, site: str, css_v: str) -> str:
    d = T[lang]
    cards = "".join(
        f'<article class="card"><h2 class="card__title"><a href="{coll_path(c["slug"], lang)}">{e(c[lang]["h1"])}</a></h2>'
        f'<p class="card__desc">{e(c[lang]["intro"])}</p>'
        f'<div class="card__actions"><a class="btn btn--primary" href="{coll_path(c["slug"], lang)}">'
        f'{e(plural(len(items_for(c, tools)), lang))} <span class="i i-arrow" aria-hidden="true"></span></a></div></article>'
        for c in COLLECTIONS
    )
    jsonld = {"@context": "https://schema.org", "@type": "ItemList", "name": d["hub_h1"],
              "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": c[lang]["h1"],
                                   "url": site + coll_path(c["slug"], lang)} for i, c in enumerate(COLLECTIONS)]}
    body = f"""
    <nav class="crumbs" aria-label="Breadcrumb">
      <a href="{bp.HOME[lang]}">{e(bp.T[lang]["home"])}</a> <span aria-hidden="true">&rsaquo;</span>
      <span aria-current="page">{e(d["collections"])}</span>
    </nav>
    <header class="coll-hero">
      <h1 class="tool-hero__title">{e(d["hub_h1"])}</h1>
      <p class="tool-hero__lead">{e(d["hub_intro"])}</p>
    </header>
    <div class="grid">{cards}</div>
{bp.submit_promo(lang)}"""
    return bp.page_shell(
        lang=lang, site=site, css_v=css_v, title=d["hub_title"], desc=bp.meta_description(d["hub_intro"]),
        path_for=lambda l: coll_path(None, l), jsonld=ld(jsonld), body=body,
    )


def build(tools: list[dict], site: str, updated: str) -> list[list[str]]:
    """Regenerate ./best/. Returns hreflang groups of page paths (for the sitemap)."""
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    css_v = bp.asset_version("styles.css")
    groups = []
    for slug in [None] + [c["slug"] for c in COLLECTIONS]:
        coll = next((c for c in COLLECTIONS if c["slug"] == slug), None)
        group = []
        for lang in LANGS:
            rel = coll_path(slug, lang)
            html_ = render_hub(tools, lang, site, css_v) if coll is None else render_collection(coll, tools, lang, site, css_v, updated)
            target = ROOT / rel.strip("/") / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html_, encoding="utf-8")
            group.append(rel)
        groups.append(group)
    return groups
