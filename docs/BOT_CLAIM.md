# Кнопка «Это мой сервис»: обработка в боте @remtex_shorts_ai_bot

На странице каждого сервиса в каталоге (кроме ваших собственных) есть блок **«Вы автор сервиса …?»** с кнопкой. Она открывает бот со ссылкой:

```
https://t.me/remtex_shorts_ai_bot?start=claim_<id>
```

`<id>` — это `id` карточки из `tools.json`, например `claim_opus-clip`. Та же ссылка стоит в готовых сообщениях авторам, которые присылает `outreach.py`.

Бот получает команду `/start claim_opus-clip`. Нужно сделать три вещи:

1. Ответить автору: дать ссылку на его карточку, код бейджа и кнопки «Исправить карточку», «Fast-Track $19», «ТОП-3 $49».
2. Сообщить вам (админу), кто и какую карточку подтвердил.
3. Всё, что автор напишет после кнопки «Исправить карточку», переслать вам.

Данные карточки бот берёт из опубликованного `https://creator-directory-chi.vercel.app/tools.json`, поэтому ничего синхронизировать не нужно.

## Тексты ответа

**RU** (если `language_code` пользователя `ru` или `uk`):

> 👋 Здравствуйте! Это карточка **{name}** в CreatorDirectory: {url}
>
> Что можно сделать:
> 🏅 **Бейдж** — вставьте код ниже на свой сайт (например, в футер). Так посетители увидят, что вы есть в каталоге.
> ✏️ **Исправить описание или цену** — нажмите кнопку и напишите, что поменять. Исправим за 24 часа.
> ⚡ **Fast-Track** — отметка «Verified» и приоритет · 🏆 **ТОП-3** — закрепление на 30 дней.

**EN** (all other users):

> 👋 Hi! This is the **{name}** listing on CreatorDirectory: {url}
>
> What you can do:
> 🏅 **Badge** — paste the code below on your website (e.g. in the footer).
> ✏️ **Fix the description or pricing** — tap the button and tell us what to change. Fixed within 24 hours.
> ⚡ **Fast-Track** — "Verified" mark and priority · 🏆 **Top-3** — pinned for 30 days.

## Пример кода (aiogram 3)

Вставьте в ваш бот. `ADMIN_CHAT_ID` — ваш chat id, на который приходят уведомления.

```python
import html, re, time, aiohttp
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

SITE = "https://creator-directory-chi.vercel.app"
BOT_LINK = "https://t.me/remtex_shorts_ai_bot"
ADMIN_CHAT_ID = 123456789  # <- ваш chat id
router = Router()
_cache = {"at": 0, "tools": {}}


class Claim(StatesGroup):
    waiting_fix = State()


async def get_tool(tool_id: str) -> dict | None:
    if time.time() - _cache["at"] > 600:  # обновлять раз в 10 минут
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{SITE}/tools.json") as r:
                data = await r.json(content_type=None)
        _cache.update(at=time.time(), tools={t["id"]: t for t in data["tools"]})
    return _cache["tools"].get(tool_id)


@router.message(CommandStart(deep_link=True, magic=F.args.regexp(r"^claim_[A-Za-z0-9_-]+$")))
async def claim(message: Message, command: CommandObject, state: FSMContext):
    tool_id = command.args.removeprefix("claim_")
    tool = await get_tool(tool_id)
    if not tool:
        await message.answer("Карточка не найдена / Listing not found: " + SITE)
        return
    ru = (message.from_user.language_code or "").startswith(("ru", "uk"))
    url = f"{SITE}/tools/{tool_id}/" + ("ru/" if ru else "")
    name = html.escape(tool["name"])
    badge = (f'<a href="{SITE}/tools/{tool_id}/" target="_blank" rel="noopener">'
             f'<img src="{SITE}/assets/badge-featured.svg" alt="Featured on CreatorDirectory" width="220" height="54" /></a>')
    if ru:
        text = (f"👋 Здравствуйте! Это карточка <b>{name}</b> в CreatorDirectory: {url}\n\n"
                "🏅 <b>Бейдж</b> — вставьте код ниже на свой сайт (например, в футер).\n"
                "✏️ <b>Исправить описание или цену</b> — нажмите кнопку и напишите, что поменять.\n"
                "⚡ <b>Fast-Track</b> — отметка «Verified» · 🏆 <b>ТОП-3</b> — закрепление на 30 дней.")
        b_fix, b_fast, b_top = "✏️ Исправить карточку", "⚡ Fast-Track $19", "🏆 ТОП-3 $49"
    else:
        text = (f"👋 Hi! This is the <b>{name}</b> listing on CreatorDirectory: {url}\n\n"
                "🏅 <b>Badge</b> — paste the code below on your website (e.g. in the footer).\n"
                "✏️ <b>Fix the description or pricing</b> — tap the button and tell us what to change.\n"
                "⚡ <b>Fast-Track</b> — \"Verified\" mark · 🏆 <b>Top-3</b> — pinned for 30 days.")
        b_fix, b_fast, b_top = "✏️ Fix my listing", "⚡ Fast-Track $19", "🏆 Top-3 $49"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=b_fix, callback_data=f"fix:{tool_id}")],
        [InlineKeyboardButton(text=b_fast, url=f"{BOT_LINK}?start=submit_fast19"),
         InlineKeyboardButton(text=b_top, url=f"{BOT_LINK}?start=submit_top49")],
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)
    await message.answer(f"<pre>{html.escape(badge)}</pre>", parse_mode="HTML")
    u = message.from_user
    await message.bot.send_message(
        ADMIN_CHAT_ID,
        f"🙋 Claim: <b>{name}</b> ({tool_id})\nот {html.escape(u.full_name)} "
        f"{'@' + u.username if u.username else ''} (id {u.id})\n{url}",
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("fix:"))
async def fix_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Claim.waiting_fix)
    await state.update_data(tool_id=cb.data.split(":", 1)[1])
    ru = (cb.from_user.language_code or "").startswith(("ru", "uk"))
    await cb.message.answer("Напишите одним сообщением, что исправить 👇" if ru else "Tell us in one message what to change 👇")
    await cb.answer()


@router.message(Claim.waiting_fix)
async def fix_text(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.forward(ADMIN_CHAT_ID)
    await message.bot.send_message(ADMIN_CHAT_ID, f"✏️ Правка для карточки {data.get('tool_id')} (сообщение выше)")
    ru = (message.from_user.language_code or "").startswith(("ru", "uk"))
    await message.answer("Спасибо! Исправим в течение 24 часов." if ru else "Thanks! We'll update it within 24 hours.")
    await state.clear()
```

Зарегистрируйте роутер **до** общего обработчика `/start`: `dp.include_router(router)`.

Если бот написан на другой библиотеке, логика та же. В `/start` проверьте, что аргумент начинается с `claim_`. Затем возьмите карточку из `tools.json` по `id`, отправьте автору тексты выше и уведомите себя.

## Как проверить, что пишет действительно автор

Иногда «это мой сервис» может нажать не автор. Прежде чем вносить правки или давать бесплатные бонусы, попросите одно из двух:

- письмо с почты на домене сервиса (например, `@klap.app`);
- поставить бейдж на сайт. Еженедельная проверка `outreach.py badges` сама сообщит, когда ссылка появится.
