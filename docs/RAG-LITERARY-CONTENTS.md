# Literary RAG Database Contents

> **Collection**: `literary_texts` in Qdrant (server mode)
> **Search tool**: `mcp__rag__search_text` with `subject` filter, or `scripts/rag/query.py:search_literary()`
> **Total**: ~78,100 chunks across 134 JSONL files (11 waves)

## How to Use

**MCP search** (from Claude Code):
```
mcp__rag__search_text(query="хрещення Русі", subject="literary")
```

**Python** (from pipeline scripts):
```python
from rag.query import search_literary
results = search_literary("Мазепа", limit=5, genre="chronicle")
```

**Filters**: `genre`, `language_period`, `work`, `author`, `year`

---

## Wave Summary

| Wave | Chunks | Files | Category |
|------|--------|-------|----------|
| 0 | 177 | 3 | Foundations (Slovo, PVL, Samovydets) |
| 1 | 4,941 | 7 | OES Chronicles & Legal |
| 2 | 2,579 | 8 | RUTH Chronicles & Grammars |
| 3 | 1,121 | 6 | RUTH Vernacular & Admin |
| 4 | 14,696 | 11 | Scholarly Reference (Hrushevsky, Chyzhevsky, etc.) |
| 5 | 7,286 | 17 | Old Literature & Primary Sources |
| 6 | 6,503 | 17 | Chronicles & Diaries |
| 7 | 20,904 | 32 | History & Political Thought |
| 8 | 10,297 | 12 | Literary Studies |
| 9 | 1,991 | 13 | Linguistics & Grammars |
| 10 | 7,608 | 8 | Shevchenko |
| **Total** | **78,103** | **134** | |

---

## Contents by Genre & Period

### Chronicles (`genre: chronicle`)

| Work | Period | Year | Chunks | Wave | Tracks |
|------|--------|------|--------|------|--------|
| Повість временних літ (Іпатський список) | old_east_slavic | 1113 | 1,075 | 1 | OES, ISTORIOHRAFIIA |
| Повість временних літ (Лаврентіївський список) | old_east_slavic | 1113 | 694 | 1 | OES, ISTORIOHRAFIIA |
| Повість временних літ (переклад Яременка) | old_east_slavic | 1113 | 55 | 0 | OES |
| Київський літопис | old_east_slavic | 1198 | 1,083 | 1 | OES, ISTORIOHRAFIIA |
| Галицько-Волинський літопис | old_east_slavic | 1292 | 1,010 | 1 | OES, ISTORIOHRAFIIA |
| ГВЛ (переклад Коструби) | middle_ukrainian | 1292 | 260 | 6 | OES |
| Синопсис (Київ, 1674) | middle_ukrainian | 1674 | 557 | 6 | RUTH, ISTORIOHRAFIIA |
| Литовсько-білоруські літописи та хроніки | middle_ukrainian | 1550 | 1,359 | 6 | RUTH, ISTORIOHRAFIIA |
| Феодосій Софонович — Хроніка | middle_ukrainian | 1672 | 647 | 6 | RUTH |
| Львівський та Острозький літописці | middle_ukrainian | 1649 | 53 | 6 | RUTH |
| Південноруські літописи (Білозерський) | middle_ukrainian | 1856 | 87 | 6 | ISTORIOHRAFIIA |
| Добірка літописів (Київська археогр. комісія) | middle_ukrainian | 1878 | 419 | 6 | ISTORIOHRAFIIA |
| Київський літопис XVII ст. | middle_ukrainian | 1625 | 26 | 6 | RUTH |
| Чернігівський літопис (1587-1750) | middle_ukrainian | 1750 | 64 | 2 | RUTH, ISTORIOHRAFIIA |
| Літопис Самовидця | middle_ukrainian | 1702 | 111 | 0 | RUTH, ISTORIOHRAFIIA |
| Літопис Грабянки | middle_ukrainian | 1710 | 214 | 2 | RUTH, ISTORIOHRAFIIA |
| Літопис Величка | middle_ukrainian | 1720 | 1,676 | 2 | RUTH, ISTORIOHRAFIIA |
| Історія Русів | middle_ukrainian | 1829 | 434 | 2 | RUTH, ISTORIOHRAFIIA |
| Історія Русів (переклад Драча) | modern | 1829 | 364 | 6 | ISTORIOHRAFIIA |
| Шерер — Літопис Малоросії | modern | 1788 | 258 | 6 | ISTORIOHRAFIIA |
| Симоновський — Короткий опис козацького народу | modern | 1765 | 241 | 6 | ISTORIOHRAFIIA |
| Рігельман — Літописна оповідь про Малу Росію | modern | 1847 | 955 | 6 | ISTORIOHRAFIIA |

### Travelogues & Diaries (`genre: travelogue, diary`)

| Work | Period | Year | Chunks | Wave | Tracks |
|------|--------|------|--------|------|--------|
| Боплан — Опис України (1660) | modern | 1660 | 170 | 6 | ISTORIOHRAFIIA |
| Шевальє — Історія війни козаків проти Польщі | modern | 1663 | 165 | 6 | ISTORIOHRAFIIA |
| Даніел Крман — Подорожній щоденник (1708-1709) | modern | 1709 | 75 | 6 | ISTORIOHRAFIIA |
| Щоденник Миколи Ханенка (1719-1754) | middle_ukrainian | 1754 | 810 | 6 | RUTH, ISTORIOHRAFIIA |
| Де ля Фліз — Етнографічний опис (1854) | modern | 1854 | 57 | 6 | ISTORIOHRAFIIA |

### Poetry & Literature (`genre: poetry, fable, interlude, prose, drama, anthology`)

| Work | Period | Year | Chunks | Wave | Tracks |
|------|--------|------|--------|------|--------|
| Слово о полку Ігоревім | old_east_slavic | 1187 | 11 | 0 | OES, LIT |
| Слово о полку (поетичні переклади) | old_east_slavic | 1187 | 325 | 1 | OES, LIT |
| Українська поезія XVI-XVII ст. | middle_ukrainian | 1650 | 286 | 3 | RUTH, LIT |
| Українські інтермедії XVII-XVIII ст. | middle_ukrainian | 1700 | 172 | 3 | RUTH, LIT |
| Байки XVII-XVIII ст. | middle_ukrainian | 1700 | 257 | 3 | RUTH, LIT |
| Іван Величковський — Твори | middle_ukrainian | 1690 | 164 | 5 | RUTH, LIT |
| Климентій Зіновіїв — Вірші | middle_ukrainian | 1700 | 403 | 5 | RUTH, LIT |
| Українська драматургія XIX ст. | modern | 1840 | 208 | 5 | LIT |
| Українська література XI-XIII ст. | old_east_slavic | 1250 | 2 | 5 | OES |
| Українська література XIV-XVI ст. | middle_ukrainian | 1500 | 3 | 5 | RUTH |
| Українська література XVII ст. | middle_ukrainian | 1680 | 662 | 5 | RUTH, LIT |
| Українська література XVIII ст. | middle_ukrainian | 1780 | 466 | 5 | LIT |
| Хрестоматія давньої укр. літ. (Білецький) | modern | 1952 | 359 | 5 | OES, RUTH, LIT |
| Сковорода — Повне зібрання творів | middle_ukrainian | 1794 | 1,352 | 5 | LIT, RUTH |
| Прокопович — Філософські твори | middle_ukrainian | 1716 | 1,602 | 5 | LIT, RUTH |
| Довгалевський — Поетика | middle_ukrainian | 1736 | 316 | 5 | LIT, RUTH |

### Polemic & Political Thought (`genre: polemic, scholarly`)

| Work | Period | Year | Chunks | Wave | Tracks |
|------|--------|------|--------|------|--------|
| Суспільно-політична думка XVI-XVII ст. | middle_ukrainian | 1650 | 821 | 5 | RUTH, ISTORIOHRAFIIA |
| Дзюба — Інтернаціоналізм чи русифікація? | modern | 1965 | 377 | 7 | ISTORIOHRAFIIA |
| Драгоманов — Вибрані праці | modern | 1891 | 1,042 | 7 | ISTORIOHRAFIIA |
| Грінченко-Драгоманов — Діалоги | modern | 1894 | 330 | 7 | ISTORIOHRAFIIA |
| Волошин — Вибрані твори | modern | 1959 | 240 | 7 | ISTORIOHRAFIIA |
| Ґренджа-Донський — Карпатська Україна | modern | 1939 | 639 | 7 | ISTORIOHRAFIIA |

### Religious & Hagiographic (`genre: religious, hagiography`)

| Work | Period | Year | Chunks | Wave | Tracks |
|------|--------|------|--------|------|--------|
| Патерик Києво-Печерський | old_east_slavic | 1462 | 361 | 1 | OES, BIO |
| Борис та Гліб — пам'ятки | old_east_slavic | 1200 | 64 | 5 | OES, BIO |

### Grammars & Lexicons (`genre: grammar, lexicon, rhetoric, reference`)

| Work | Period | Year | Chunks | Wave | Tracks |
|------|--------|------|--------|------|--------|
| Федорович — Буквар (1574) | middle_ukrainian | 1574 | 11 | 2 | RUTH |
| Зизаній — Лексис (1596) | middle_ukrainian | 1596 | 20 | 2 | RUTH |
| Смотрицький — Граматіки Словенскія (1619) | middle_ukrainian | 1619 | 116 | 2 | RUTH |
| Беринда — Лексикон словенороський (1627) | middle_ukrainian | 1627 | 44 | 2 | RUTH |
| Іван Федорович — Азбука (Острог, 1578) | middle_ukrainian | 1578 | 1 | 9 | RUTH |
| Тимофій Вербицький — Буквар (1627) | middle_ukrainian | 1627 | 8 | 9 | RUTH |
| Іван Ужевич — Граматика (1643) | middle_ukrainian | 1645 | 2 | 9 | RUTH |
| Ужевич — Паризький рукопис (1970 переклад) | middle_ukrainian | 1645 | 104 | 9 | RUTH |
| Реч жидовського — глосарій (1282) | old_east_slavic | 1282 | 26 | 9 | OES |
| Тлкованіє — глосарій (1431) | middle_ukrainian | 1431 | 24 | 9 | RUTH |
| Синоніма славенороська | middle_ukrainian | 1640 | 27 | 9 | RUTH |
| Східнослов'янські граматики XVI-XVII ст. | modern | 1982 | 60 | 9 | RUTH |
| Український правопис 2015 | modern | 2015 | 297 | 9 | RUTH |

### Legal & Administrative (`genre: legal, manual, letter`)

| Work | Period | Year | Chunks | Wave | Tracks |
|------|--------|------|--------|------|--------|
| Грамоти XIV ст. | middle_ukrainian | 1350 | 335 | 3 | RUTH |
| Грамоти XV ст. | middle_ukrainian | 1450 | 1 | 5 | RUTH |
| Волинські грамоти XVI ст. | middle_ukrainian | 1550 | 1 | 5 | RUTH |
| Руська Правда (Юшков) | old_east_slavic | 1072 | 364 | 5 | OES |
| Другий статут ВКЛ 1566 року | middle_ukrainian | 1566 | 270 | 7 | RUTH |
| Лікарські порадники XVIII ст. | middle_ukrainian | 1750 | 70 | 3 | RUTH |
| Старовинний письмовник | middle_ukrainian | 1750 | 1 | 3 | RUTH |

### Scholarly History & Culture (`genre: scholarly`)

| Work | Author | Year | Chunks | Wave | Tracks |
|------|--------|------|--------|------|--------|
| Грушевський — Історія України-Руси (т.1-10) | Грушевський М. | 1898 | 9,763 | 4 | ISTORIOHRAFIIA, HIST, OES |
| Грушевський — Історія укр. літератури (т.1-6) | Грушевський М. | 1923 | 1,341 | 4 | LIT, RUTH |
| Грушевський — Вибрані статті | Грушевський М. | 1930 | 185 | 7 | ISTORIOHRAFIIA |
| Чижевський — Історія укр. літератури | Чижевський Д. | 1956 | 933 | 4 | LIT |
| Чижевський — Укр. літературне бароко | Чижевський Д. | 1941 | 693 | 8 | LIT |
| Чижевський — Нариси з історії філософії | Чижевський Д. | 1931 | 263 | 8 | LIT |
| Чижевський — Філософія Сковороди | Чижевський Д. | 1934 | 395 | 8 | LIT |
| Грабович — До історії укр. літератури | Грабович Г. | 1997 | 750 | 8 | LIT |
| Німчук — Мовознавство XIV-XVII ст. | Німчук В. | 1985 | 368 | 4 | RUTH |
| Оглоблін — Гетьман Мазепа та його доба | Оглоблін О. | 1960 | 810 | 4 | ISTORIOHRAFIIA, BIO |
| Войтович — Князівські династії | Войтович Л. | 2000 | 1,242 | 4 | ISTORIOHRAFIIA, BIO |
| Перетц — Слово о полку Ігоревім | Перетц В. | 1926 | 393 | 1 | OES, LIT |
| Укр. мова — Енциклопедія | Колектив | 2004 | 239 | 4 | RUTH |
| Дворнік — Слов'яни в Європейській історії | Дворнік Ф. | 1962 | 919 | 7 | ISTORIOHRAFIIA |
| Крип'якевич — Галицько-Волинське князівство | Крип'якевич І. | 1984 | 193 | 7 | ISTORIOHRAFIIA |
| Івакін — Історичний розвиток Києва XIII-XVI | Івакін Г. | 1996 | 339 | 7 | ISTORIOHRAFIIA |
| Щербак — Українське козацтво | Щербак В. | 2000 | 357 | 7 | ISTORIOHRAFIIA |
| Голобуцький — Запорозьке козацтво | Голобуцький В. | 1994 | 712 | 7 | ISTORIOHRAFIIA |
| Литвинов — Ренесансний гуманізм | Литвинов В. | 2000 | 657 | 7 | ISTORIOHRAFIIA, LIT |
| Гвоздик-Пріцак — Візія Хмельницького | Гвоздик-Пріцак Л. | 2005 | 180 | 7 | ISTORIOHRAFIIA |
| Мацьків — Мазепа в зх.-європ. джерелах | Мацьків Т. | 1988 | 408 | 7 | ISTORIOHRAFIIA, BIO |
| Когут — Російський централізм | Когут З. | 1996 | 455 | 7 | ISTORIOHRAFIIA |
| Попович — Нарис історії культури | Попович М. | 1998 | 1,197 | 7 | ISTORIOHRAFIIA |
| Іст. укр. культури. Т.1 — Київська Русь | Колектив | 2001 | 587 | 7 | ISTORIOHRAFIIA, OES |
| Іст. укр. культури. Т.2 — XIII-XVII ст. | Колектив | 2001 | 1,524 | 7 | ISTORIOHRAFIIA, RUTH |
| Крип'якевич — Іст. укр. культури (1937) | Крип'якевич І. | 1937 | 883 | 7 | ISTORIOHRAFIIA |
| Антонович — Укр. культура (лекції) | Антонович В. | 1993 | 981 | 7 | ISTORIOHRAFIIA |
| Наливайко — Очима Заходу | Наливайко Д. | 1998 | 778 | 7 | ISTORIOHRAFIIA |
| Огієнко — Українська церква | Огієнко І. | 1993 | 351 | 7 | ISTORIOHRAFIIA |
| Антонович — Вибрані праці | Антонович В. | 2003 | 785 | 7 | ISTORIOHRAFIIA |
| Укр. державність у XX ст. | Колектив | 1996 | 452 | 7 | ISTORIOHRAFIIA |
| Енциклопедія українознавства | Кубійович В. | 1955 | 3,242 | 7 | ISTORIOHRAFIIA, BIO |
| Костомаров — Слов'янська міфологія | Костомаров М. | 1847 | 958 | 7 | ISTORIOHRAFIIA, LIT |
| Томпсон — Трубадури імперії | Томпсон Е. | 2006 | 485 | 7 | ISTORIOHRAFIIA |
| Героїчне у українській культурі | Колектив | 1999 | 517 | 7 | ISTORIOHRAFIIA |
| Юшков — Нариси з іст. феодалізму | Юшков С. | 1939 | 480 | 7 | ISTORIOHRAFIIA, OES |
| Дзюба, Павленко — Літопис культури X-XVII | Дзюба О. | 2001 | 380 | 7 | ISTORIOHRAFIIA |

### Literary Studies (`genre: scholarly`)

| Work | Author | Year | Chunks | Wave | Tracks |
|------|--------|------|--------|------|--------|
| Генсьорський — ГВЛ як пам'ятка літератури | Генсьорський А. | 1958 | 133 | 8 | OES, LIT |
| Генсьорський — ГВЛ лексичні особливості | Генсьорський А. | 1961 | 328 | 8 | OES, LIT |
| Огієнко — Іст. укр. друкарства | Огієнко І. | 1925 | 551 | 8 | RUTH, LIT |
| Ісаєвич — Українське книговидання | Ісаєвич Я. | 2002 | 825 | 8 | RUTH, LIT |
| Маслюк — Латиномовні поетики і риторики | Маслюк В. | 1983 | 318 | 8 | RUTH, LIT |
| Білецький — Руська Правда й іст. її тексту | Білецький О. | 1958 | 244 | 8 | OES |
| Укр. літературна енциклопедія (1988-1995) | Колектив | 1995 | 5,555 | 8 | LIT |
| Філософська думка — біобібліогр. словник | Колектив | 2002 | 242 | 8 | LIT |

### Linguistics (`genre: scholarly, grammar`)

| Work | Author | Year | Chunks | Wave | Tracks |
|------|--------|------|--------|------|--------|
| Шевельов — Іст. фонологія укр. мови | Шевельов Ю. | 1979 | 383 | 9 | OES, RUTH |
| Огієнко — Іст. укр. літ. мови (1949) | Огієнко І. | 1949 | 376 | 9 | RUTH |
| Русанівський — Іст. укр. літ. мови | Русанівський В. | 2001 | 509 | 9 | RUTH |
| Півторак — Походження українців | Півторак Г. | 2001 | 174 | 9 | OES |

### Shevchenko (`genre: poetry, biography, scholarly`)

| Work | Author | Year | Chunks | Wave | Tracks |
|------|--------|------|--------|------|--------|
| Шевченко — Повне зібрання творів, т.1 | Шевченко Т. | 1861 | 978 | 10 | LIT |
| Літопис життя Шевченка | Анісов, Середа | 1976 | 391 | 10 | LIT, BIO |
| Шевченківський словник | Колектив | 1976 | 2,420 | 10 | LIT |
| Спогади про Шевченка | Колектив | 1982 | 803 | 10 | LIT, BIO |
| Шевченко в епістолярії | Колектив | 1966 | 542 | 10 | LIT |
| Шевченко: Документи та матеріали | Колектив | 1982 | 635 | 10 | LIT |
| Шевченко. Біографія (1984) | Колектив | 1984 | 912 | 10 | LIT, BIO |
| Кониський — Шевченко: Хроніка життя | Кониський Г. | 1990 | 927 | 10 | LIT, BIO |

### Humanities (`genre: prose, scholarly, ethnography`)

| Work | Author | Year | Chunks | Wave | Tracks |
|------|--------|------|--------|------|--------|
| Українські гуманісти епохи Відродження | Колектив | 1971 | 498 | 5 | RUTH, LIT |

---

## Coverage by Curriculum Track

| Track | Key Sources | Approx. Chunks |
|-------|-------------|----------------|
| **OES** (Old East Slavic) | PVL (3 editions), Kyiv/GVL chronicles, Slovo, Pateryk, Peretz, Ruska Pravda, Shevelov, early glossaries | ~6,500 |
| **RUTH** (Ruthenian) | Samovydets, Hrabianka, Velychko, Ist. Rusiv, grammars, lexicons, poetry, Hramoty, Skovoroda, Prokopovych | ~12,000 |
| **ISTORIOHRAFIIA** | Грушевський IUR (10 vol), Войтович, Оглоблін, Енциклопедія українознавства, all chronicles, 30+ scholarly works | ~35,000 |
| **BIO** | Оглоблін (Мазепа), Войтович, Патерик, Шевченко bio sources, Мацьків | ~5,500 |
| **LIT** | Грушевський Іст. літ., Чижевський (4 works), Грабович, Ukr. Lit. Encyclopedia, Shevchenko corpus, poetry collections | ~17,000 |
| **HIST** | Грушевський IUR (early volumes), chronicles, Когут, Щербак | ~5,000 |

---

## Source Sites

All texts scraped from **izbornyk.org.ua** (primary domain; litopys.org.ua and litopys.kiev.ua redirect here).

- Encoding: windows-1251 → UTF-8
- Content: `<div class="dop3">` elements
- Multi-page: follows "Наступна" links
- Parallel texts: original + modern Ukrainian in 2-column tables

---

## JSONL File Format

Each line is a JSON object:
```json
{
  "chunk_id": "wave1-galytsko-volynskyi-0001",
  "text": "Ukrainian text content...",
  "work": "Галицько-Волинський літопис",
  "author": "Anonymous",
  "year": 1292,
  "genre": "chronicle",
  "language_period": "old_east_slavic",
  "source_url": "http://litopys.org.ua/litop/lit22.htm",
  "token_count": 512,
  "original_text": "Old East Slavic original (if parallel text)"
}
```

Files: `data/literary_texts/wave{N}-{slug}.jsonl`

---

## Ingestion Status

- **Waves 0-3**: Fully embedded and indexed in Qdrant (12,049 points)
- **Waves 1, 4**: Ingestion in progress (CPU embedding ~9-20s per batch)
- **Waves 5-10**: JSONL scraped, pending ingestion

**Ingest command** (after waves 1+4 complete):
```bash
.venv/bin/python scripts/rag/ingest_literary.py --wave 5 6 7 8 9 10 --skip-scrape
```

Estimated time: 6-8 hours (CPU-based BGE-M3 embedding, ~66,000 chunks).

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/rag/scrape_litopys.py` | Scrape individual texts from izbornyk.org.ua |
| `scripts/rag/batch_scrape_izbornyk.py` | Batch scrape waves 5-10 (~100 texts) |
| `scripts/rag/ingest_literary.py` | JSONL → Qdrant with BGE-M3 embedding |
| `scripts/rag/query.py` | `search_literary()` function for pipeline |
| `.mcp/servers/rag/server.py` | MCP search_literary tool |
| `tests/test_rag.py` | 94 tests including 38 literary-specific |
