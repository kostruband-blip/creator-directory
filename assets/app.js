/* CreatorDirectory front-end: no frameworks, no build step. */
(function () {
  "use strict";

  var LANGS = ["en", "ru", "uk"];
  var CATS = ["shorts", "captions", "dubbing", "thumbnails", "analytics", "telegram"];
  var PRICES = ["all", "free", "freemium", "paid"];

  /* ---------- Translations (EN must stay 100% Latin) ---------- */
  var I18N = {
    en: {
      htmlTitle: "CreatorDirectory - Best AI Tools and Telegram Bots for YouTube, TikTok, Reels and Telegram Creators",
      metaDesc: "Curated directory of the best AI tools and Telegram bots for video creators: Shorts clippers, auto captions, AI dubbing, thumbnails, analytics and Telegram channel growth. Free, freemium and paid.",
      skip: "Skip to catalog",
      navCatalog: "Catalog", navSubmit: "Submit Tool",
      heroTitle: "Best AI Tools and Telegram Bots for Video Creators",
      heroSub: "A curated catalog for YouTube, TikTok, Reels and Telegram creators: Shorts clippers, captions, AI dubbing, thumbnails, analytics and channel growth.",
      searchLabel: "Search tools", searchPh: "Search by name, description or tag...",
      catalogTitle: "Tool catalog", filterCategory: "Category", filterPrice: "Pricing",
      catAll: "All tools",
      cat: { shorts: "Shorts & Clips", captions: "Captions", dubbing: "AI Dubbing & Voice", thumbnails: "Thumbnails", analytics: "Analytics", telegram: "Telegram Tools" },
      price: { all: "All prices", free: "Free", freemium: "Freemium", paid: "Paid" },
      found: function (n, total) { return "Showing " + n + " of " + total + " tools"; },
      empty: "Nothing found. Try another keyword or reset the filters.",
      reset: "Reset filters",
      visit: "Visit website", openTg: "Open in Telegram", featured: "Featured",
      pricingLabel: "Price:", loadError: "Could not load the live catalog. Showing a cached version.",
      submitTitle: "Submit Your Tool",
      submitSub: "Get your AI tool or Telegram bot in front of thousands of YouTube, TikTok and Telegram creators. Choose a listing plan:",
      t1Name: "Standard Listing", t1Price: "Free",
      t1f1: "Moderation queue up to 14 days", t1f2: "Regular card in your category", t1f3: "EN / RU / UA description",
      t2Name: "Fast-Track Review", t2Price: "$19 (790 UAH)",
      t2f1: "Published within 24 hours", t2f2: "\"Verified\" check mark", t2f3: "Priority moderation and editing",
      t3Name: "Top-3 Featured Spot", t3Price: "$49 (1990 UAH)",
      t3f1: "Pinned at the top of the home page and category", t3f2: "30 days of placement", t3f3: "Gold frame and Featured badge",
      tCta: "Submit via Telegram", tPopular: "Most popular",
      faqTitle: "FAQ",
      q1: "How are tools selected?",
      a1: "Every tool is checked by hand or by our automated pipeline: the website must be live, the product must solve a real task for video creators, and pricing must be transparent.",
      q2: "How often is the catalog updated?",
      a2: "New tools are added every week. Paid Fast-Track listings are published within 24 hours.",
      q3: "Which tool should I start with for Shorts?",
      a3: "If you already have long YouTube videos, start with KoShorts AI Studio: it turns a link into ready 9:16 Shorts with subtitles right inside Telegram, and the first 10 videos are free.",
      footerRights: "All rights reserved.", poweredBy: "Powered by"
    },
    ru: {
      htmlTitle: "CreatorDirectory — лучшие ИИ-инструменты и Telegram-боты для авторов YouTube, TikTok, Reels и Telegram",
      metaDesc: "Каталог лучших ИИ-инструментов и Telegram-ботов для видеоавторов: нарезка Shorts, автосубтитры, ИИ-дубляж, превью, аналитика и рост Telegram-каналов. Бесплатные, условно-бесплатные и платные сервисы.",
      skip: "Перейти к каталогу",
      navCatalog: "Каталог", navSubmit: "Добавить сервис",
      heroTitle: "Лучшие ИИ-инструменты и Telegram-боты для видеоавторов",
      heroSub: "Отобранный каталог для авторов YouTube, TikTok, Reels и Telegram: нарезка Shorts, субтитры, ИИ-дубляж, превью, аналитика и рост каналов.",
      searchLabel: "Поиск сервисов", searchPh: "Поиск по названию, описанию или тегу…",
      catalogTitle: "Каталог сервисов", filterCategory: "Категория", filterPrice: "Стоимость",
      catAll: "Все сервисы",
      cat: { shorts: "Shorts и клипы", captions: "Субтитры", dubbing: "ИИ-дубляж и голос", thumbnails: "Превью", analytics: "Аналитика", telegram: "Инструменты Telegram" },
      price: { all: "Любая цена", free: "Бесплатно", freemium: "Условно-бесплатно", paid: "Платно" },
      found: function (n, total) { return "Показано " + n + " из " + total; },
      empty: "Ничего не найдено. Попробуйте другой запрос или сбросьте фильтры.",
      reset: "Сбросить фильтры",
      visit: "Перейти на сайт", openTg: "Открыть в Telegram", featured: "Закреплено",
      pricingLabel: "Цена:", loadError: "Не удалось загрузить актуальный каталог. Показана сохранённая версия.",
      submitTitle: "Добавить сервис",
      submitSub: "Покажите свой ИИ-сервис или Telegram-бота тысячам авторов YouTube, TikTok и Telegram. Выберите тариф размещения:",
      t1Name: "Базовое размещение", t1Price: "Бесплатно",
      t1f1: "Очередь модерации до 14 дней", t1f2: "Обычная карточка в категории", t1f3: "Описание на EN / RU / UA",
      t2Name: "Ускоренная публикация", t2Price: "$19 (790 грн)",
      t2f1: "Публикация за 24 часа", t2f2: "Отметка «Проверено»", t2f3: "Приоритетная модерация и редактура",
      t3Name: "Закрепление в ТОП-3", t3Price: "$49 (1990 грн)",
      t3f1: "Закрепление вверху главной страницы и категории", t3f2: "30 дней размещения", t3f3: "Золотая рамка и бейдж «Закреплено»",
      tCta: "Оставить заявку в Telegram", tPopular: "Самый популярный",
      faqTitle: "Частые вопросы",
      q1: "Как отбираются сервисы?",
      a1: "Каждый сервис проверяется вручную или автоматической системой: сайт должен работать, продукт — решать реальную задачу видеоавторов, а цены — быть прозрачными.",
      q2: "Как часто обновляется каталог?",
      a2: "Новые сервисы добавляются каждую неделю. Платные заявки с ускоренной публикацией размещаются в течение 24 часов.",
      q3: "С какого инструмента начать делать Shorts?",
      a3: "Если у вас уже есть длинные видео на YouTube, начните с KoShorts AI Studio: он превращает ссылку в готовые Shorts 9:16 с субтитрами прямо в Telegram, а первые 10 видео бесплатны.",
      footerRights: "Все права защищены.", poweredBy: "Работает на"
    },
    uk: {
      htmlTitle: "CreatorDirectory — найкращі ШІ-інструменти та Telegram-боти для авторів YouTube, TikTok, Reels і Telegram",
      metaDesc: "Каталог найкращих ШІ-інструментів і Telegram-ботів для відеоавторів: нарізка Shorts, автосубтитри, ШІ-дубляж, прев'ю, аналітика та зростання Telegram-каналів. Безкоштовні, умовно безкоштовні та платні сервіси.",
      skip: "Перейти до каталогу",
      navCatalog: "Каталог", navSubmit: "Додати сервіс",
      heroTitle: "Найкращі ШІ-інструменти та Telegram-боти для відеоавторів",
      heroSub: "Добірний каталог для авторів YouTube, TikTok, Reels і Telegram: нарізка Shorts, субтитри, ШІ-дубляж, прев'ю, аналітика та зростання каналів.",
      searchLabel: "Пошук сервісів", searchPh: "Пошук за назвою, описом або тегом…",
      catalogTitle: "Каталог сервісів", filterCategory: "Категорія", filterPrice: "Вартість",
      catAll: "Усі сервіси",
      cat: { shorts: "Shorts і кліпи", captions: "Субтитри", dubbing: "ШІ-дубляж і голос", thumbnails: "Прев'ю", analytics: "Аналітика", telegram: "Інструменти Telegram" },
      price: { all: "Будь-яка ціна", free: "Безкоштовно", freemium: "Умовно безкоштовно", paid: "Платно" },
      found: function (n, total) { return "Показано " + n + " з " + total; },
      empty: "Нічого не знайдено. Спробуйте інший запит або скиньте фільтри.",
      reset: "Скинути фільтри",
      visit: "Перейти на сайт", openTg: "Відкрити в Telegram", featured: "Закріплено",
      pricingLabel: "Ціна:", loadError: "Не вдалося завантажити актуальний каталог. Показано збережену версію.",
      submitTitle: "Додати сервіс",
      submitSub: "Покажіть свій ШІ-сервіс або Telegram-бота тисячам авторів YouTube, TikTok і Telegram. Оберіть тариф розміщення:",
      t1Name: "Базове розміщення", t1Price: "Безкоштовно",
      t1f1: "Черга модерації до 14 днів", t1f2: "Звичайна картка в категорії", t1f3: "Опис EN / RU / UA",
      t2Name: "Прискорена публікація", t2Price: "$19 (790 грн)",
      t2f1: "Публікація за 24 години", t2f2: "Позначка «Перевірено»", t2f3: "Пріоритетна модерація та редагування",
      t3Name: "Закріплення в ТОП-3", t3Price: "$49 (1990 грн)",
      t3f1: "Закріплення вгорі головної сторінки та категорії", t3f2: "30 днів розміщення", t3f3: "Золота рамка та бейдж «Закріплено»",
      tCta: "Залишити заявку в Telegram", tPopular: "Найпопулярніший",
      faqTitle: "Часті запитання",
      q1: "Як відбираються сервіси?",
      a1: "Кожен сервіс перевіряється вручну або автоматичною системою: сайт має працювати, продукт — розв'язувати реальне завдання відеоавторів, а ціни — бути прозорими.",
      q2: "Як часто оновлюється каталог?",
      a2: "Нові сервіси додаються щотижня. Платні заявки з прискореною публікацією розміщуються протягом 24 годин.",
      q3: "З якого інструмента почати робити Shorts?",
      a3: "Якщо у вас уже є довгі відео на YouTube, почніть із KoShorts AI Studio: він перетворює посилання на готові Shorts 9:16 із субтитрами просто в Telegram, а перші 10 відео безкоштовні.",
      footerRights: "Усі права захищені.", poweredBy: "Працює на"
    }
  };

  /* ---------- State ---------- */
  var state = { lang: "en", cat: "all", price: "all", q: "", tools: [] };

  var $ = function (sel) { return document.querySelector(sel); };
  var grid = $("#grid"), stats = $("#stats"), empty = $("#empty"), search = $("#search");
  var catBox = $("#catFilters"), priceBox = $("#priceFilters");

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function safeUrl(u) { return /^https:\/\//i.test(u || "") ? u : "#"; }
  function t() { return I18N[state.lang]; }
  function field(tool, base) { return tool[base + "_" + state.lang] || tool[base + "_en"] || ""; }

  /* ---------- URL <-> state ---------- */
  function readUrl() {
    var params = new URLSearchParams(location.search);
    var pathLang = (location.pathname.match(/^\/(ru|uk)\/?$/) || [])[1];
    var lang = params.get("lang") || pathLang || safeStorage("cd_lang") || "en";
    state.lang = LANGS.indexOf(lang) >= 0 ? lang : "en";
    var cat = params.get("cat");
    state.cat = CATS.indexOf(cat) >= 0 ? cat : "all";
    var price = params.get("price");
    state.price = PRICES.indexOf(price) >= 0 ? price : "all";
    state.q = (params.get("q") || "").slice(0, 100);
  }
  function writeUrl() {
    var params = new URLSearchParams();
    if (state.cat !== "all") params.set("cat", state.cat);
    if (state.price !== "all") params.set("price", state.price);
    if (state.q) params.set("q", state.q);
    var path = state.lang === "en" ? "/" : "/" + state.lang;
    // Opened as a local file: /ru and /uk paths can't be rewritten to index.html, so fall back to ?lang=
    if (location.protocol === "file:") {
      path = location.pathname;
      if (state.lang !== "en") params.set("lang", state.lang);
    }
    var qs = params.toString();
    history.replaceState(null, "", path + (qs ? "?" + qs : "") + location.hash);
  }
  function safeStorage(key, val) {
    try {
      if (val === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, val);
    } catch (e) { return null; }
  }

  /* ---------- Static UI translation ---------- */
  function applyStaticI18n() {
    var d = t();
    document.documentElement.lang = state.lang;
    document.title = d.htmlTitle;
    var md = document.querySelector('meta[name="description"]');
    if (md) md.setAttribute("content", d.metaDesc);
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var v = d[el.getAttribute("data-i18n")];
      if (typeof v === "string") el.textContent = v;
    });
    document.querySelectorAll("[data-i18n-ph]").forEach(function (el) {
      el.setAttribute("placeholder", d[el.getAttribute("data-i18n-ph")]);
    });
    document.querySelectorAll("[data-i18n-aria]").forEach(function (el) {
      el.setAttribute("aria-label", d[el.getAttribute("data-i18n-aria")]);
    });
    document.querySelectorAll(".lang__btn").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-lang") === state.lang));
    });
  }

  /* ---------- Filters ---------- */
  function renderFilters() {
    var d = t();
    // Chip counts = what the grid will show for that category (pinned tools appear everywhere)
    var counts = { all: state.tools.length };
    CATS.forEach(function (c) {
      counts[c] = state.tools.filter(function (x) { return x.pinned === true || x.category === c; }).length;
    });

    catBox.innerHTML = ["all"].concat(CATS).map(function (c) {
      var label = c === "all" ? d.catAll : d.cat[c];
      return '<button type="button" class="chip" data-cat="' + c + '" aria-pressed="' + (state.cat === c) + '">' +
        esc(label) + ' <span class="chip__count">' + (counts[c] || 0) + "</span></button>";
    }).join("");

    priceBox.innerHTML = PRICES.map(function (p) {
      return '<button type="button" class="chip" data-price="' + p + '" aria-pressed="' + (state.price === p) + '">' +
        esc(d.price[p]) + "</button>";
    }).join("");
  }

  function normalize(s) { return String(s).toLowerCase().replace(/ё/g, "е"); }

  function matches(tool, words) {
    if (!words.length) return true;
    var hay = normalize([
      tool.name, tool.id, field(tool, "desc"), tool.desc_en, field(tool, "badge"),
      (tool.tags || []).join(" "), t().cat[tool.category], tool.category
    ].join(" "));
    return words.every(function (w) { return hay.indexOf(w) >= 0; });
  }

  function filtered() {
    var words = normalize(state.q).split(/\s+/).filter(Boolean);
    return state.tools.filter(function (x) {
      // Pinned tools (KoShorts) ignore category/price filters and stay on top; search still applies
      if (x.pinned === true) return matches(x, words);
      return (state.cat === "all" || x.category === state.cat) &&
        (state.price === "all" || x.pricing_type === state.price) &&
        matches(x, words);
    });
  }

  /* ---------- Cards ---------- */
  function initials(name) {
    var parts = String(name).replace(/[^A-Za-z0-9 ]/g, " ").trim().split(/\s+/);
    return ((parts[0] || "?")[0] + (parts[1] ? parts[1][0] : "")).toUpperCase();
  }

  function card(x) {
    var d = t();
    var badge = field(x, "badge");
    var isOwn = /koshorts\.vercel\.app/.test(x.url);
    var rel = isOwn ? "noopener" : "noopener nofollow";
    var html = '<article class="card' + (x.featured ? " card--featured" : "") + '" id="' + esc(x.id) + '">' +
      '<div class="card__top">' +
        '<div class="card__logo" aria-hidden="true">' + esc(initials(x.name)) + "</div>" +
        '<div class="card__head">' +
          '<h3 class="card__title"><a href="' + esc(safeUrl(x.url)) + '" target="_blank" rel="' + rel + '">' + esc(x.name) + "</a></h3>" +
          '<div class="card__meta">' +
            (x.featured ? '<span class="pill pill--featured">&#9733; ' + esc(d.featured) + "</span>" : "") +
            (badge ? '<span class="pill pill--badge">' + esc(badge) + "</span>" : "") +
            '<span class="pill">' + esc(d.cat[x.category]) + "</span>" +
            '<span class="pill pill--' + esc(x.pricing_type) + '">' + esc(d.price[x.pricing_type]) + "</span>" +
          "</div>" +
        "</div>" +
      "</div>" +
      '<p class="card__desc">' + esc(field(x, "desc")) + "</p>" +
      '<p class="card__price"><strong>' + esc(d.pricingLabel) + "</strong> " + esc(field(x, "pricing")) + "</p>" +
      '<div class="tags">' + (x.tags || []).map(function (tag) {
        return '<button type="button" class="tag" data-tag="' + esc(tag) + '">#' + esc(tag) + "</button>";
      }).join("") + "</div>" +
      '<div class="card__actions">' +
        (x.tg ? '<a class="btn btn--tg" href="' + esc(safeUrl(x.tg)) + '" target="_blank" rel="noopener">' + esc(d.openTg) + "</a>" : "") +
        (x.url !== x.tg ? '<a class="btn ' + (x.featured ? "btn--gold" : "btn--ghost") + '" href="' + esc(safeUrl(x.url)) + '" target="_blank" rel="' + rel + '">' + esc(d.visit) + " &rarr;</a>" : "") +
      "</div>" +
    "</article>";
    return html;
  }

  function renderGrid() {
    var list = filtered();
    grid.innerHTML = list.map(card).join("");
    empty.hidden = list.length > 0;
    stats.textContent = t().found(list.length, state.tools.length);
  }

  function renderAll() {
    applyStaticI18n();
    renderFilters();
    renderGrid();
    writeUrl();
  }

  /* ---------- Data ---------- */
  function sortTools(list) {
    // Featured first (keeps file order inside each group => KoShorts stays #1)
    return list.map(function (x, i) { return { x: x, i: i }; })
      .sort(function (a, b) {
        return (b.x.pinned === true) - (a.x.pinned === true) ||
          (b.x.featured === true) - (a.x.featured === true) || a.i - b.i;
      })
      .map(function (o) { return o.x; });
  }

  function load() {
    return fetch("/tools.json", { cache: "no-cache" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (data) {
        var tools = Array.isArray(data) ? data : data.tools;
        state.tools = sortTools((tools || []).filter(function (x) {
          return x && x.id && x.name && CATS.indexOf(x.category) >= 0;
        }));
      });
  }

  /* ---------- Events ---------- */
  var debounce;
  search.addEventListener("input", function () {
    clearTimeout(debounce);
    debounce = setTimeout(function () { state.q = search.value.trim(); renderGrid(); writeUrl(); }, 120);
  });
  catBox.addEventListener("click", function (e) {
    var b = e.target.closest("[data-cat]"); if (!b) return;
    state.cat = b.getAttribute("data-cat"); renderFilters(); renderGrid(); writeUrl();
  });
  priceBox.addEventListener("click", function (e) {
    var b = e.target.closest("[data-price]"); if (!b) return;
    state.price = b.getAttribute("data-price"); renderFilters(); renderGrid(); writeUrl();
  });
  grid.addEventListener("click", function (e) {
    var b = e.target.closest("[data-tag]"); if (!b) return;
    state.q = b.getAttribute("data-tag"); search.value = state.q; renderGrid(); writeUrl();
    search.scrollIntoView({ behavior: "smooth", block: "center" });
  });
  document.querySelectorAll(".lang__btn").forEach(function (b) {
    b.addEventListener("click", function () {
      state.lang = b.getAttribute("data-lang");
      safeStorage("cd_lang", state.lang);
      renderAll();
    });
  });
  $("#resetFilters").addEventListener("click", function () {
    state.cat = "all"; state.price = "all"; state.q = ""; search.value = "";
    renderAll();
  });

  /* ---------- Boot ---------- */
  var y = document.getElementById("year"); if (y) y.textContent = new Date().getFullYear();
  readUrl();
  search.value = state.q;
  applyStaticI18n();

  load().then(renderAll).catch(function (err) {
    // Fallback: keep the pre-rendered (SEO) cards that are already in the HTML.
    console.warn("CreatorDirectory: tools.json failed to load", err);
    stats.textContent = t().loadError;
  });
})();
