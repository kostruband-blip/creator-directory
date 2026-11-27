#!/usr/bin/env python3
"""
Semi-automatic outreach to the makers of the tools in CreatorDirectory.

Nothing is ever sent to the makers automatically (Telegram bans cold messages, cold e-mail lands
in spam). Instead YOU get a Telegram message per tool with the contacts found on its website
and a ready-to-paste personal message — sending it takes ~1 minute.

    python outreach.py prepare --ids klap,munch   # these tools
    python outreach.py prepare --next 5           # next 5 tools that were never prepared
    python outreach.py prepare --new              # tools added in the last 8 days (used by auto-update)
    python outreach.py badges                     # which sites link back to CreatorDirectory
    add --dry-run to print instead of sending to Telegram / saving outreach.json

State: outreach.json  {"tools": {"<id>": {"prepared_at", "contacts", "badge_seen", "badge_checked"}}}
Env:   TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (same secrets as auto-update), SITE_URL
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

from validate_tools import load_catalog

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "outreach.json"
SITE_URL = os.environ.get("SITE_URL", "https://creator-directory-chi.vercel.app").rstrip("/")
BOT = "https://t.me/remtex_shorts_ai_bot"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/130.0 Safari/537.36 CreatorDirectoryBot/1.0")
OWN_HOSTS = ("koshorts.vercel.app", "creator-studio-ai-psi.vercel.app", "creator-directory-chi.vercel.app")
# Huge brands almost never add catalog badges -> contacted last
BIG_BRANDS = {"canva", "capcut", "adobe-firefly", "midjourney", "telegram-ads", "clipchamp", "hootsuite",
              "descript", "synthesia", "elevenlabs", "heygen", "picsart", "remove-bg", "photoroom", "rev", "veed",
              "kapwing", "riverside", "leonardo-ai", "ideogram", "speechify"}
CAT = {
    "en": {"shorts": "Shorts & Clips", "captions": "Captions", "dubbing": "AI Dubbing & Voice",
           "thumbnails": "Thumbnails", "analytics": "Analytics", "telegram": "Telegram Tools"},
    "ru": {"shorts": "Shorts и клипы", "captions": "Субтитры", "dubbing": "ИИ-дубляж и голос",
           "thumbnails": "Превью", "analytics": "Аналитика", "telegram": "Инструменты Telegram"},
}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}")
EMAIL_JUNK = re.compile(r"(\.(png|jpe?g|gif|svg|webp|css|js)$)|example\.|sentry|wixpress|domain\.com|email\.com|"
                        r"yourcompany|@\d|noreply|no-reply|donotreply|privacy@|abuse@|legal@|dpo@|gdpr@", re.I)
EMAIL_PRIORITY = ("partner", "marketing", "growth", "hello", "hi@", "contact", "team", "founder", "press",
                  "business", "info", "support", "help")
SOCIAL_SKIP = re.compile(r"/(share|intent|sharer|home|search|hashtag|i/|login|signup)\b|t\.me/(share|joinchat)", re.I)


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------- state

def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"tools": {}}


def save_state(state: dict) -> None:
    state["tools"] = dict(sorted(state["tools"].items()))
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- fetching

def fetch(url: str, timeout: int = 15, limit: int = 1_500_000) -> tuple[str, str]:
    """(final_url, html) or ("", "") on any error."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.6",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.geturl(), resp.read(limit).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001 - DNS, SSL, timeouts, 4xx/5xx...
        return "", ""


def host_of(url: str) -> str:
    h = urllib.parse.urlparse(url).netloc.lower().split(":")[0]
    return h[4:] if h.startswith("www.") else h


def base_domain(host: str) -> str:
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


# --------------------------------------------------------------------------- contact extraction

def extract(page_url: str, text: str) -> dict:
    """Contacts found in one HTML page."""
    hrefs = [html.unescape(h) for h in re.findall(r'href\s*=\s*["\']([^"\']+)["\']', text, re.I)]
    emails = set()
    for h in hrefs:
        if h.lower().startswith("mailto:"):
            emails.add(urllib.parse.unquote(h[7:].split("?")[0]).strip())
    visible = re.sub(r"<(script|style)\b.*?</\1>", " ", text, flags=re.S | re.I)
    emails |= set(EMAIL_RE.findall(html.unescape(re.sub(r"<[^>]+>", " ", visible))))
    emails = {e.strip(".").lower() for e in emails if EMAIL_RE.fullmatch(e.strip(".")) and not EMAIL_JUNK.search(e)}

    out = {"emails": emails, "x": set(), "telegram": set(), "linkedin": set(), "discord": set(), "pages": set()}
    site = base_domain(host_of(page_url))
    for h in hrefs:
        absu = urllib.parse.urljoin(page_url, h)
        low = absu.lower()
        if not low.startswith("http") or SOCIAL_SKIP.search(low):
            continue
        hh = host_of(absu)
        path = urllib.parse.urlparse(absu).path.strip("/")
        if hh in ("twitter.com", "x.com") and path and "/" not in path:
            out["x"].add("https://x.com/" + path)
        elif hh in ("t.me", "telegram.me") and path and not path.startswith("+"):
            out["telegram"].add("https://t.me/" + path.split("/")[0])
        elif hh.endswith("linkedin.com") and path.startswith("company/"):
            out["linkedin"].add("https://www.linkedin.com/" + "/".join(path.split("/")[:2]))
        elif hh in ("discord.gg", "discord.com") and path:
            out["discord"].add(absu.split("?")[0])
        elif base_domain(hh) == site and re.search(r"contact|about|partner|affiliate|press|support|team", path, re.I):
            out["pages"].add(absu.split("#")[0].split("?")[0])
    return out


def merge(a: dict, b: dict) -> dict:
    return {k: a.get(k, set()) | b.get(k, set()) for k in set(a) | set(b)}


def rank_emails(emails: set[str], site_host: str) -> list[str]:
    site = base_domain(site_host)

    def score(e: str) -> tuple:
        local, _, dom = e.partition("@")
        prio = next((i for i, p in enumerate(EMAIL_PRIORITY) if p.rstrip("@") in local), len(EMAIL_PRIORITY))
        return (base_domain(dom) != site, prio, e)

    return sorted(emails, key=score)


def find_contacts(tool: dict) -> dict:
    final, text = fetch(tool["url"])
    if not text:
        return {"reachable": False}
    found = extract(final, text)
    # contact / about pages: up to 3 extra requests
    pages = sorted(found["pages"], key=lambda u: (not re.search(r"contact", u, re.I), len(u)))[:3]
    for p in pages:
        f2, t2 = fetch(p)
        if t2:
            found = merge(found, extract(f2, t2))
    # the tool's own Telegram bot/channel description often names a support account
    if tool.get("tg"):
        _, tg_html = fetch(tool["tg"])
        m = re.search(r'tgme_page_description[^>]*>(.*?)</div>', tg_html, re.S)
        if m:
            desc = html.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))
            found["emails"] |= {e.lower() for e in EMAIL_RE.findall(desc) if not EMAIL_JUNK.search(e)}
            found["telegram"] |= {"https://t.me/" + u for u in re.findall(r"@([A-Za-z][A-Za-z0-9_]{4,31})", desc)}
    bot_self = tool.get("tg", "").rstrip("/").lower()
    return {
        "reachable": True,
        "emails": rank_emails(found["emails"], host_of(final))[:3],
        "x": sorted(found["x"])[:2],
        "telegram": sorted(u for u in found["telegram"] if u.lower() != bot_self)[:3],
        "linkedin": sorted(found["linkedin"])[:1],
        "discord": sorted(found["discord"])[:1],
        "contact_page": next((p for p in pages if re.search(r"contact", p, re.I)), pages[0] if pages else ""),
        "lang": "ru" if re.search(r'<html[^>]+lang=["\'](ru|uk)', text, re.I)
                or len(re.findall("[А-Яа-яІіЇїЄє]", text)) > 400 else "en",
    }


# --------------------------------------------------------------------------- messages

def card_url(tool: dict, lang: str) -> str:
    return f"{SITE_URL}/tools/{tool['id']}/" + ("ru/" if lang == "ru" else "")


def claim_url(tool: dict) -> str:
    return f"{BOT}?start=claim_{re.sub(r'[^A-Za-z0-9_-]', '', tool['id'])[:57]}"


def maker_message(tool: dict, lang: str) -> tuple[str, str]:
    """(subject, body) — written to be sent by a human, short and specific."""
    name, cat = tool["name"], CAT[lang][tool["category"]]
    if lang == "ru":
        subject = f"{name} в каталоге CreatorDirectory"
        body = (
            f"Здравствуйте, команда {name}!\n\n"
            f"Я веду CreatorDirectory — бесплатный каталог ИИ-инструментов для авторов YouTube, TikTok, Reels и Telegram. "
            f"Мы добавили {name} в раздел «{cat}»: {card_url(tool, 'ru')}\n\n"
            f"Если понравится, можно поставить на сайт небольшой бейдж «Featured on CreatorDirectory» — код есть на странице, "
            f"в блоке «Вы автор сервиса?». Если в описании или ценах что-то неточно — ответьте, исправлю за день. "
            f"Управлять карточкой можно и через нашего бота: {claim_url(tool)}\n\n"
            f"Спасибо и удачи {name}!"
        )
    else:
        subject = f"{name} is featured on CreatorDirectory"
        body = (
            f"Hi {name} team!\n\n"
            f"I run CreatorDirectory, a free catalog of AI tools for YouTube, TikTok, Reels and Telegram creators. "
            f"We've added {name} to the {cat} section: {card_url(tool, 'en')}\n\n"
            f"If you like it, you can add a small \"Featured on CreatorDirectory\" badge to your site — the code is on the page "
            f"under \"Are you the maker?\". If anything in the description or pricing is off, just reply and I'll fix it within a day. "
            f"You can also manage the listing via our bot: {claim_url(tool)}\n\n"
            f"Thanks, and good luck with {name}!"
        )
    return subject, body


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def telegram_card(tool: dict, c: dict) -> str:
    """Report for YOU (Russian UI): contacts + message to copy (tap on the block copies it)."""
    lines = [f"📬 <b>Связаться с автором: {esc(tool['name'])}</b>",
             f"Карточка: {esc(card_url(tool, 'en'))}", f"Сайт: {esc(tool['url'])}"]
    if not c.get("reachable"):
        lines.append("⚠️ Сайт не открылся при проверке — посмотрите контакты вручную.")
    contacts = []
    for e in c.get("emails", []):
        contacts.append(f"✉️ {esc(e)}")
    for u in c.get("x", []):
        contacts.append(f'𝕏 <a href="{esc(u)}">{esc(u.replace("https://", ""))}</a>')
    for u in c.get("telegram", []):
        contacts.append(f'✈️ <a href="{esc(u)}">{esc(u.replace("https://", ""))}</a>')
    for u in c.get("linkedin", []) + c.get("discord", []):
        contacts.append(f'🔗 <a href="{esc(u)}">{esc(u.replace("https://", ""))}</a>')
    if c.get("contact_page"):
        contacts.append(f'📝 <a href="{esc(c["contact_page"])}">форма / страница контактов</a>')
    lines.append("<b>Контакты:</b>\n" + ("\n".join(contacts) if contacts else "не найдены — загляните в футер сайта или раздел About"))
    lang = c.get("lang", "en")
    subject, body = maker_message(tool, lang)
    best = "почту" if c.get("emails") else "X / Telegram / форму"
    lines.append(f"<b>Тема:</b> <code>{esc(subject)}</code>")
    lines.append(f"<b>Сообщение ({'RU' if lang == 'ru' else 'EN'}) — нажмите, чтобы скопировать, и отправьте через {best}:</b>")
    lines.append(f"<pre>{esc(body)}</pre>")
    return "\n".join(lines)


# --------------------------------------------------------------------------- telegram

def send_telegram(text: str) -> bool:
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        log("telegram: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — printing instead\n" + text)
        return False
    data = json.dumps({"chat_id": chat, "text": text[:4096], "parse_mode": "HTML",
                       "disable_web_page_preview": True}).encode("utf-8")
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as exc:
        log(f"telegram: HTTP {exc.code} {exc.read()[:200]!r}")
    except Exception as exc:  # noqa: BLE001
        log(f"telegram: {exc}")
    return False


# --------------------------------------------------------------------------- commands

def is_own(tool: dict) -> bool:
    return any(h in tool["url"] for h in OWN_HOSTS)


def pick(tools: list[dict], state: dict, args) -> list[dict]:
    candidates = [t for t in tools if not is_own(t)]
    if args.ids:
        wanted = [i.strip() for i in args.ids.split(",") if i.strip()]
        return [t for t in candidates if t["id"] in wanted]
    fresh = [t for t in candidates if t["id"] not in state["tools"] or not state["tools"][t["id"]].get("prepared_at")]
    if args.new:
        since = (date.today() - timedelta(days=8)).isoformat()
        return [t for t in fresh if t["added_at"] >= since]
    fresh.sort(key=lambda t: (t["id"] in BIG_BRANDS, -int(t["added_at"].replace("-", "")), tools.index(t)))
    return fresh[: args.next]


def cmd_prepare(args) -> int:
    tools = load_catalog()["tools"]
    state = load_state()
    chosen = pick(tools, state, args)
    if not chosen:
        log("outreach: nothing to prepare")
        return 0
    log(f"outreach: preparing {len(chosen)} tool(s): {', '.join(t['id'] for t in chosen)}")
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(find_contacts, chosen))
    for tool, c in zip(chosen, results):
        card = telegram_card(tool, c)
        if args.dry_run:
            log("\n" + card)
            continue
        send_telegram(card)
        entry = state["tools"].setdefault(tool["id"], {})
        entry["prepared_at"] = date.today().isoformat()
        entry["contacts"] = {k: v for k, v in c.items() if v and k != "reachable"}
    left = len([t for t in tools if not is_own(t) and not state["tools"].get(t["id"], {}).get("prepared_at")])
    if not args.dry_run:
        save_state(state)
        log(f"outreach: done, {left} tool(s) still waiting")
    return 0


def has_backlink(tool: dict) -> tuple[str, bool | None]:
    _, text = fetch(tool["url"])
    if not text:
        return tool["id"], None
    return tool["id"], host_of(SITE_URL) in text.lower()


def cmd_badges(args) -> int:
    tools = [t for t in load_catalog()["tools"] if not is_own(t)]
    state = load_state()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = dict(pool.map(has_backlink, tools))
    today = date.today().isoformat()
    new, lost, live = [], [], []
    for t in tools:
        ok = results[t["id"]]
        entry = state["tools"].setdefault(t["id"], {})
        if ok is None:          # site did not answer: keep the previous status
            continue
        entry["badge_checked"] = today
        if ok:
            live.append(t)
            if not entry.get("badge_seen"):
                entry["badge_seen"] = today
                new.append(t)
        elif entry.get("badge_seen"):
            entry.pop("badge_seen")
            lost.append(t)
    unreachable = [t["id"] for t in tools if results[t["id"]] is None]
    lines = [f"🏅 <b>Бейджи CreatorDirectory</b> ({today})",
             f"Ссылка на каталог стоит на {len(live)} из {len(tools)} сайтов."]
    if new:
        lines.append("<b>Новые:</b>\n" + "\n".join(f"✅ {esc(t['name'])} — {esc(t['url'])}" for t in new))
        lines.append("Можно поблагодарить автора и, например, дать карточке приоритет в категории.")
    if lost:
        lines.append("<b>Пропали:</b>\n" + "\n".join(f"❌ {esc(t['name'])} — {esc(t['url'])}" for t in lost))
    if unreachable:
        lines.append(f"Не открылись при проверке: {len(unreachable)} ({esc(', '.join(unreachable[:10]))})")
    text = "\n".join(lines)
    if args.dry_run:
        log(text)
        return 0
    save_state(state)
    if new or lost or args.always_report:
        send_telegram(text)
    else:
        log(text + "\n(no changes, Telegram report skipped)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare", help="find contacts and send ready messages to your Telegram")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--ids", help="comma-separated tool ids")
    g.add_argument("--next", type=int, help="next N tools that were never prepared")
    g.add_argument("--new", action="store_true", help="tools added in the last 8 days")
    p.add_argument("--dry-run", action="store_true")
    b = sub.add_parser("badges", help="check which tool websites link back to CreatorDirectory")
    b.add_argument("--dry-run", action="store_true")
    b.add_argument("--always-report", action="store_true", help="send the Telegram report even without changes")
    args = ap.parse_args()
    return cmd_prepare(args) if args.cmd == "prepare" else cmd_badges(args)


if __name__ == "__main__":
    sys.exit(main())
