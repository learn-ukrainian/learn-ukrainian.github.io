# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: bio-002
level: BIO
sequence: 2
slug: kniaz-sviatoslav
version: '2.0'
title: 'Князь Святослав: Воїн-завойовник'
subtitle: 'Prince Sviatoslav: The Warrior Conqueror'
focus: biography
pedagogy: CBI
phase: C1.3 Biographies
word_target: 5000
objectives:
- Learner understands the geopolitical strategy of Sviatoslav Ihorovych
- Learner can analyze the impact of the destruction of the Khazar Khaganate
- Learner masters biographical and military terminology at C1 level
- Learner can compare the leadership styles of Olga and Sviatoslav
sources:
- name: Святослав Ігорович (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Святослав_Ігорович
  type: primary
  notes: Military campaigns, death, historical significance
- name: Повість минулих літ
  url: https://uk.wikipedia.org/wiki/Повість_минулих_літ
  type: primary
  notes: Chronicle accounts of campaigns
- name: Хозарський каганат
  url: https://uk.wikipedia.org/wiki/Хозарський_каганат
  type: reference
  notes: Context for Khazar campaign
content_outline:
- section: Вступ — Воїн на троні
  points:
  - Контраст між 'м'якою силою' Ольги та 'твердою силою' Святослава — архетип воїна-захисника
  - 'Значення постаті: Святослав як ''український Александр Македонський'' — єдиний син Ігоря та Ольги, перший князь зі слов''янським
    іменем'
  - Чому він важливий для сучасної мілітарної ідентичності (гасло ССО) — [!history-bite] Опис зовнішності Левом Дияконом (оселедець,
    сережка, біла сорочка)
  words: 450
- section: Життєпис
  points:
  - 'Основні етапи життя князя — Хронологія: 964 (В''ятичі), 965 (Хазарія), 967 (Балкани), 972 (Загибель)'
  words: 450
- section: 'Біографія: Ранні роки та становлення'
  points:
  - Дитинство в Києві та вплив трагічної загибелі Ігоря — необхідність сили як урок
  - Виховання варязькими воєводами Асмудом та Свенельдом — формування характеру у військових таборах
  - 'Похід на древлян 946 року: перший кинутий спис у 4 роки — «Князь уже почав, потягніте, дружино, за князем»'
  - 'Відмова хреститися — аргумент: «Дружина моя сміятиметься з цього»'
  words: 450
- section: Східний похід та крах Хазарії
  points:
  - Економічна логіка знищення хазарської монополії на Волзі — [!context] Хазарія як «паразит» на торгових шляхах
  - Стратегія обходу степу через ліси в'ятичів та басейн Оки — звільнення в'ятичів від данини (964)
  - Падіння Ітіля у 965 році та зникнення Каганату з мапи історії — також взяття Саркела (Біла Вежа) та Семендера
  - Результат — відкриття шляху на Схід, але й оголення кордону для печенігів
  words: 450
- section: Балканська мрія та облога Доростола
  points:
  - Проект перенесення столиці до Переяславця на Дунаї — [!quote] «Тут сходяться блага... бо то є середина землі моєї»
  - 'Конфлікт із Візантією: Битва під Аркадіополем — героїчна боротьба проти імперії'
  - 'Облога Доростола 971 року: героїчний опір та договір з Цимісхієм — 3 місяці оборони, голод, особиста зустріч на Дунаї'
  words: 450
- section: 'Останні роки: Загибель на порогах'
  points:
  - 'Повернення до Києва: зимівля в Білобережжі та голод — ціна конячої голови пів гривні'
  - Пастка печенігів біля порогів та роль візантійської дипломатії — [!myth-buster] Це не випадкова засідка, а спланована
    операція Візантії
  - 'Легенда про чашу з черепа: визнання доблесті ворогом — напис хана Курі «Чужого шукаючи, своє втратив»'
  - Попередження воєводи Свенельда — «Обійди, княже, пороги на конях»
  words: 450
- section: Внесок у розбудову держави
  points:
  - Вихід Русі на глобальну арену — ствердження суб'єктності через знищення Хазарії та тиск на Візантію
  - 'Основи імперського мислення Києва — [!analysis] Парадокс: майже не бував у Києві, але перетворив Русь на гравця світової
    політики'
  - Адміністративна реформа — призначення синів намісниками (Ярополк, Олег, Володимир) замість племінних князів
  words: 450
- section: 'Історичний контекст: Русь у X столітті'
  points:
  - 'Геополітичний ландшафт: Між Другим Римом та Шовковим шляхом — Зіткнення цивілізацій: Степ, Імперія, Ліс'
  - 'Війська організація: ''Ефект пардуса'' (швидкість та мобільність) — використання моноксилів (ладдей) та пішої фаланги'
  - 'Мова та культура: Зіткнення язичницького етосу та християнської дипломатії — культ Перуна, зброї та клятви'
  words: 450
- section: 'Порівняльний аналіз: Творець (Ольга) vs Завойовник (Святослав)'
  points:
  - Порівняння внутрішньої розбудови інституцій та зовнішньої експансії — «м'яка сила» vs «тверда сила»
  - 'Симбіоз: Чому Русі потрібен був і Скелет (Ольга), і М''язи (Святослав) — Ольга забезпечила тил для походів сина'
  - 'Спадщина: Як перемоги Святослава уможливили реформи Володимира — фундамент імперії'
  words: 450
- section: 'Спадщина: Від Князя до ЗСУ'
  points:
  - 'Деколонізація: Повернення ''оселедця'' та ''сережки'' як українських символів — [!decolonization] Святослав як носій
    степового етосу, попередник козацтва'
  - 'Сучасна військова символіка: Святослав як патрон Сил спеціальних операцій — тяглість традиції'
  - Кодекс честі 'Іду на ви!' — відмова від підступності
  - Цитата під Доростолом — «Мертві сорому не мають»
  words: 450
- section: Підсумок
  points:
  - Квінтесенція правління Святослава Хороброго — кульмінація язичницької Русі, спалах, що освітив шлях імперії
  words: 500
vocabulary_hints:
  required:
  - 'воїн (warrior) — collocations: хоробрий воїн, полеглий воїн; learner error: soldier (сучасний солдат)'
  - 'завойовник (conqueror) — collocations: жорстокий завойовник, світ завойовників'
  - 'каганат (khaganate) — context: Хозарський каганат; знищення каганату'
  - 'похід (campaign/march) — collocations: військовий похід, піти в похід, східний похід'
  - 'дружина (retinue/warband) — collocations: княжа дружина, вірна дружина; learner error: wife (жінка)'
  - 'печеніги (Pechenegs) — context: кочові племена, напад печенігів'
  - 'пороги (rapids) — context: Дніпровські пороги, загибель на порогах'
  - 'засідка (ambush) — collocations: влаштувати засідку, потрапити в засідку'
  - 'данник (tributary) — collocations: брати данину, звільнити від данини'
  - 'договір (treaty) — collocations: укласти договір, мирний договір'
  recommended:
  - 'чаша (cup/goblet) — context: чаша з черепа, пити з чаші'
  - 'череп (skull) — context: череп ворога, зробити чашу з черепа'
  - 'здобич (spoils/booty) — collocations: багата здобич, ділити здобич'
  - 'облога (siege) — collocations: тримати облогу, зняти облогу Доростола'
  - 'перемога (victory) — collocations: здобути перемогу, велика перемога'
activity_hints:
- type: reading
  focus: Chronicle description of Sviatoslav's campaigns
  source: Повість минулих літ (adapted)
  items: 3 passages
- type: essay-response
  focus: Evaluate Sviatoslav's legacy - conqueror or destroyer?
  output: Balanced argument with evidence
connects_to:
- bio-03 (Volodymyr Velykyi - son)
- bio-04 (Yaroslav Mudryi - grandson's era)
- bio-06 (Mykhailo Chernihivskyi - later Mongol threat parallel)
prerequisites:
- bio-01 (Knyahynia Olha - mother)
- Understanding of Kyivan Rus geography
persona:
  voice: Senior Biographer
  role: Conqueror
grammar:
- Historical narrative register
- Quoted speech conventions in chronicles
- Participial constructions in formal descriptions
module_type: biography
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Князь Святослав: Воїн-завойовник** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

### Your RAG Tools (USE THEM)

You have access to Ukrainian language tools via MCP. **Use them during research.**

| Tool | When to use | Example |
|------|-------------|---------|
| `query_wikipedia` mode=`extract` | Get full article text (50K chars) for deep research | `query_wikipedia("Богдан Хмельницький", mode="extract")` |
| `query_wikipedia` mode=`sections` | See article structure before diving in | `query_wikipedia("Запорізька Січ", mode="sections")` |
| `query_wikipedia` mode=`section` | Read a specific section by index | `query_wikipedia("Запорізька Січ", mode="section", section=3)` |
| `query_wikipedia` mode=`search` | Find the right article title | `query_wikipedia("Переяславська рада", mode="search")` |
| `search_literary` | Find primary source excerpts (chronicles, poetry, legal texts) | `search_literary("Хмельницький", genre="chronicle")` |
| `verify_word` / `verify_words` | Check Ukrainian words exist in VESUM dictionary | `verify_words(["гетьман", "козацтво"])` |
| `query_grac` | Check word frequency in Ukrainian corpus | `query_grac("упокорення", mode="frequency")` |

**Workflow**: Search Wikipedia FIRST for factual foundation → search literary RAG for primary quotes → verify vocabulary with VESUM.

### Research Requirements

1. **Sources**: Use `query_wikipedia` (mode=`extract`) for Ukrainian Wikipedia articles. Also consult history.org.ua, litopys.org.ua. Use `search_literary` for primary source excerpts. Russian-language sources are PROHIBITED.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find 2+ quotable primary source excerpts (original Ukrainian text preferred).
4. **Engagement Hooks**: Identify 6+ engagement hooks mapped to specific content sections:
   - `[!myth-buster]` — Decolonization: correct imperial/Soviet myths
   - `[!history-bite]` — Surprising or lesser-known facts
   - `[!context]` — Broader historical/cultural context
   - `[!quote]` — Primary source citations
   - `[!decolonization]` — Ukraine-centric reframing
   - `[!culture]` — Cultural significance
5. **Decolonization Angle**: Identify how this topic has been distorted by imperial/Soviet historiography and what the Ukrainian-centric framing should be.
6. **Section-Mapped Content**: Structure notes with headings that match the `content_outline` sections from the plan. This makes Phase B content writing mechanical.

### Research Output Cap
Keep research notes under **4000 words** (seminar tracks need depth for historiographical mapping).
Focus on density: Key Facts Ledger, timeline, primary quotes, section-mapped notes.

If this topic involves contested narratives (Ukrainian vs. Russian/Soviet/Polish historiography), include a Contested Terms Table:

```markdown
## Contested Terms

| Concept | Imperial framing | Ukrainian (decolonized) framing |
|---------|-----------------|-------------------------------|
| ...     | ...             | ...                           |
```

---

## Downstream Audit Gates (Phase B content will be checked for)

Plan your research and outline knowing that Phase B content must pass these gates:
- **Word count**: minimum **5000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Engagement callouts**: map 6+ hooks to specific sections during research (not as afterthought patches)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Князь Святослав: Воїн-завойовник

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Князь Святослав: Воїн-завойовник"
vital_status: "deceased" # or "alive"
dates:
  birth: "YYYY-MM-DD"    # or approximate: "~YYYY"
  death: "YYYY-MM-DD"    # omit if alive
  key_events:
    - year: YYYY
      event: "Event description (Ukrainian)"
    - year: YYYY
      event: "Event description"
primary_quotes:
  - text: "Exact Ukrainian quote"
    source: "Source name, year"
    attribution: "Who said/wrote it"
  - text: "..."
    source: "..."
    attribution: "..."
forbidden_claims:
  - "Common myth or Russian propaganda claim to avoid"
  - "..."
```

## Використані джерела
1. [Source name](URL) — brief description
2. ...
3. ...

## Хронологія
- {date}: {event}
- ...

## Ключові факти та цитати
- ...

## Engagement Hooks (mapped to sections)
- Section "{section_name}": [!hook_type] — description
- ...

## Деколонізаційний контекст
- Imperial/Soviet myth: ...
- Ukrainian reality: ...

## Contested Terms (if applicable)
| Concept | Imperial framing | Ukrainian framing |
|---------|-----------------|-------------------|
| ...     | ...             | ...               |

## Відеоресурси
(Якщо під час дослідження ви натрапили на релевантні відеоматеріали — документальні фільми, архівні записи, інтерв'ю — зазначте їх тут. НЕ шукайте відео спеціально — це робить фаза discover. Максимум 3 записи.)
- {Канал — Назва — URL — Короткий опис релевантності}
- (нічого не знайдено)

## Section-Mapped Research Notes

### {Section 1 from content_outline}
Key facts, dates, sources for this section...

### {Section 2 from content_outline}
...

===RESEARCH_END===
```

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Research + Meta (Seminar)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | SOURCE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the plan's content_outline
- Do NOT use Russian-language sources
- Do NOT fabricate quotes or dates — if unsure, mark as "[needs verification]"
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
