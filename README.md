# CreatorDirectory

Нишевый каталог **AI-инструментов и Telegram-ботов для авторов YouTube, TikTok, Reels и Telegram-каналов**.
Статический сайт без сборщиков (HTML + CSS + vanilla JS), хостинг — бесплатный Vercel, автопополнение — GitHub Actions + Gemini.

- 🌐 3 языка: **EN** (по умолчанию, без кириллицы) · **RU** · **UA** — переключатель в шапке, URL `/`, `/ru`, `/uk`
- 🔎 Живой поиск по названию, описанию и тегам, фильтры по 6 категориям и модели оплаты, состояние в URL (`?cat=shorts&price=free&q=...`)
- 🥇 Закреплённые карточки (`featured: true`) с золотой рамкой; KoShorts AI Studio (`pinned: true`) всегда №1 при любом фильтре категории и цены
- 💰 Блок монетизации: Free / Fast-Track $19 / Top-3 $49 → заявка в [@remtex_shorts_ai_bot](https://t.me/remtex_shorts_ai_bot)
- 📈 SEO: пререндер карточек в HTML, JSON-LD (`ItemList` + `SoftwareApplication`), hreflang, `sitemap.xml`, `robots.txt`, OG-картинка
- 📄 Отдельная страница на каждый сервис × 3 языка: `/tools/<id>/`, `/tools/<id>/ru/`, `/tools/<id>/uk/` — «цены, возможности и альтернативы», KoShorts первым в альтернативах
- 🎯 Метки для бота: тарифы `?start=submit_free` / `submit_fast19` / `submit_top49`, промо-блок на странице сервиса `?start=cd_<id>`
- 📱 Адаптивная вёрстка от 320px, контраст текста WCAG AA

## Структура

| Файл | Назначение |
| --- | --- |
| `index.html` | Страница; между маркерами `PRERENDER`/`SEO:*` — автогенерируемый SEO-слой |
| `assets/app.js`, `assets/styles.css` | Логика (переводы, поиск, фильтры) и стили |
| `tools.json` | База каталога (66 сервисов) |
| `tools.schema.json` | JSON Schema карточки |
| `validate_tools.py` | Валидатор без зависимостей (схема, дубли, отсутствие кириллицы в EN) |
| `build_seo.py` | Пересобирает пререндер, JSON-LD, `sitemap.xml`, `robots.txt` и страницы сервисов |
| `build_pages.py` | Шаблон и тексты (EN/RU/UA) страниц сервисов, общий подвал «Бесплатные инструменты для авторов», бейдж; папка `tools/` генерируется целиком — не правьте её руками |
| `build_collections.py` | Подборки под поисковые запросы `/best/<slug>/` (EN/RU/UA): список подборок и их тексты; папка `best/` генерируется целиком |
| `indexnow_submit.py` + `<ключ>.txt` | Мгновенная отправка новых/изменённых страниц в Bing, Yandex, DuckDuckGo (IndexNow) |
| `.github/workflows/indexnow.yml` | IndexNow после каждого деплоя `main`; ручной запуск = отправить весь sitemap |
| `outreach.py`, `outreach.json` | Полуавтоматический аутрич авторам сервисов: контакты + готовое сообщение вам в Telegram, проверка бейджей; журнал |
| `.github/workflows/outreach.yml` | По четвергам: сообщения для следующих 5 сервисов + проверка бейджей; можно запустить вручную |
| `auto_update_directory.py` | Автопополнение через Gemini |
| `.github/workflows/auto_update.yml` | Запуск по понедельникам и вручную |
| `.github/workflows/validate.yml` | Проверка `tools.json` в PR |
| `vercel.json` | Rewrites `/ru` и `/uk`, кэш, заголовки безопасности |

## 1. Секреты GitHub Actions

**Settings → Secrets and variables → Actions → New repository secret**

| Секрет | Обязателен | Где взять |
| --- | --- | --- |
| `GEMINI_API_KEY` | ✅ | [Google AI Studio](https://aistudio.google.com/app/apikey) → Create API key |
| `GEMINI_API_KEY_2` | — | Второй ключ (другой проект/аккаунт) для ротации при лимитах 429 |
| `GEMINI_API_KEY_3` | — | Третий ключ, по желанию |
| `TELEGRAM_BOT_TOKEN` | — | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TELEGRAM_CHAT_ID` | — | ID чата/канала для отчётов (например, через [@userinfobot](https://t.me/userinfobot)); бот должен быть добавлен в канал админом |

Необязательная **переменная** (вкладка *Variables*): `SITE_URL` — ваш домен, например `https://creatordirectory.com` (по умолчанию `https://creator-directory-chi.vercel.app`).

Также включите **Settings → Actions → General → Workflow permissions → Read and write permissions**, чтобы workflow мог пушить коммиты.

## 2. Деплой на Vercel в 2 клика

1. Откройте [vercel.com/new](https://vercel.com/new) → **Import** репозитория `creator-directory`.
2. Framework Preset: **Other**, Build Command и Output Directory оставьте пустыми → **Deploy**.

Готово: каждый пуш в `main` (в том числе автокоммиты бота) автоматически публикуется. Если подключите свой домен, укажите его в переменной `SITE_URL` и выполните `python build_seo.py`.

> Коммиты автопополнения помечены `[skip ci]`: это не даёт запуститься другим workflow GitHub Actions. Vercel по умолчанию такие коммиты деплоит; не добавляйте *Ignored Build Step*, который пропускает `[skip ci]`, иначе новые сервисы не попадут на сайт.

## 3. Google Search Console

1. [search.google.com/search-console](https://search.google.com/search-console) → **Добавить ресурс** → тип **«Ресурс с префиксом в URL»** → `https://creator-directory-chi.vercel.app/` (тип «Домен» для `*.vercel.app` недоступен).
2. Способ подтверждения **«HTML-файл»**: скачайте `googleXXXX.html` → в GitHub *Add file → Upload files* в корень репозитория → Commit. Через минуту файл будет на сайте → **Подтвердить**.
3. **Файлы Sitemap** → введите `sitemap.xml` → **Отправить**.
4. По желанию: **Проверка URL** → `https://creator-directory-chi.vercel.app/tools/opus-clip/` → **Запросить индексирование** для ключевых страниц.

### 3.2. Bing, Yandex, DuckDuckGo — IndexNow (автоматически)

* Ключ IndexNow лежит в корне (`<32 символа>.txt`) — он публичный, так и задумано.
* Новые и изменённые страницы отправляются сами: после слияния PR (`indexnow.yml`), после автопополнения и после ручной правки `tools.json`.
* **Один раз после подключения:** *Actions → IndexNow ping → Run workflow* (галочка «all» включена) — отправит все страницы из `sitemap.xml`.
* [Bing Webmaster Tools](https://www.bing.com/webmasters) → *Импорт из Google Search Console* — там видно, что страницы приняты.
* Google IndexNow не поддерживает; Google Indexing API официально только для вакансий и трансляций — для каталога используйте sitemap в Search Console.

### 3.3. Подборки `/best/` (программное SEO)

Страницы вида `/best/ai-youtube-thumbnails/ru/` («Нейросети для обложек YouTube») собираются из `tools.json` автоматически: рейтинг, FAQ, разметка ItemList + FAQPage. Новая подборка — добавьте блок в `COLLECTIONS` в `build_collections.py` (slug, фильтр по категории или цене, тексты на 3 языках) и запустите `python build_seo.py`.


### 3.4. Аутрич авторам сервисов (обратные ссылки)

Авторам сервисов **ничего не отправляется автоматически**: Telegram банит за холодные сообщения, а холодные письма уходят в спам. Вместо этого вам в Telegram (через те же секреты `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`) приходит отдельное сообщение по каждому сервису:

* контакты, найденные на сайте сервиса: почта (с приоритетом partners@ и hello@), X, Telegram, LinkedIn, Discord, страница контактов;
* тема письма и готовый текст на EN или RU. Язык выбирается по сайту сервиса. Нажмите на текст, чтобы скопировать, и отправьте сами — около минуты.

В сообщении автору есть ссылка на карточку, предложение поставить бейдж «Featured on CreatorDirectory» и кнопка бота `claim_<id>`.

**Когда приходят сообщения:**
* сразу после того, как автопополнение добавило новые сервисы;
* по четвергам — для следующих 5 сервисов из каталога. Крупные бренды вроде Canva и Adobe идут в конце очереди: они бейджи не ставят;
* вручную: *Actions → Outreach to tool makers → Run workflow*. Укажите количество (`count`) и режим `both`, `prepare` или `badges`.

**Проверка бейджей:** раз в неделю скрипт заходит на сайты сервисов и сообщает, у кого появилась или пропала ссылка на каталог.

Всё фиксируется в `outreach.json`: кому подготовлено сообщение, найденные контакты, когда замечен бейдж. Этот файл на сайт не публикуется.

Локально: `python outreach.py prepare --ids klap,munch --dry-run` — только показать сообщения; `python outreach.py badges --dry-run`.

Кнопка **«Это мой сервис»** на страницах сервисов ведёт в бот с параметром `claim_<id>`. Как обработать его в боте — тексты и готовый код в [`docs/BOT_CLAIM.md`](docs/BOT_CLAIM.md).

## 3.1. Автопополнение

- **Автоматически:** каждый понедельник в 10:00 UTC добавляются 3 новых сервиса.
- **Вручную:** *Actions → Auto-expand directory → Run workflow*, параметры `count` (по умолчанию 3) и `target_category` (`any` или конкретная категория).

Как работает скрипт: читает `tools.json` → собирает домены и названия (защита от дублей) → запрашивает у Gemini кандидатов (ротация ключей и моделей `gemini-flash-latest → gemini-3.8-flash → gemini-3.7-flash → gemini-pro-latest`, обход 429/503, пропуск недоступных моделей) → проверяет схему и то, что `url` отвечает HTTP < 400 → дописывает в конец каталога → пересобирает SEO-слой → шлёт отчёт в Telegram. Карусель моделей можно переопределить переменной окружения `GEMINI_MODELS`.

Локально:

```bash
export GEMINI_API_KEY=...
python auto_update_directory.py --count 3 --category any --dry-run   # без записи
python auto_update_directory.py --count 5 --category telegram
```

## 4. Ручное редактирование

👉 Пошаговая инструкция с шаблоном карточки: [docs/ADD_TOOL.md](docs/ADD_TOOL.md). После коммита в `main` workflow *Rebuild site after manual edit* сам проверит `tools.json` и пересоберёт SEO-слой.

1. Добавьте/измените объект в `tools.json` (поля — см. `tools.schema.json`).
2. `python validate_tools.py && python build_seo.py` (скрипт также проставляет `?v=хеш` к `app.js`/`styles.css`, чтобы браузеры не держали старую версию — запускайте его и после правок в `assets/`)
3. Закоммитьте `tools.json`, `index.html`, `sitemap.xml`.

**`pinned: true`** — карточка показывается первой при *любой* категории и цене (сейчас только KoShorts); поиск на неё действует как обычно.

**Платное закрепление (Top-3):** поставьте `"featured": true` и переместите карточку сразу после KoShorts — закреплённые выводятся первыми в порядке следования в файле. Для Fast-Track можно добавить бейдж, например `"badge_en": "Verified"`, `"badge_ru": "Проверено"`, `"badge_uk": "Перевірено"`.

## Локальный просмотр

```bash
python dev_server.py     # http://localhost:8000 (поддерживает /ru и /uk как на Vercel)
```

---

Powered by [KoShorts AI Studio](https://koshorts.vercel.app)
