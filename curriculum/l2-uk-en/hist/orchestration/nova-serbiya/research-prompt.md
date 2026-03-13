# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-078
level: HIST
sequence: 78
slug: nova-serbiya
version: '2.0'
title: Нова Сербія та Слов'яносербія
subtitle: 'New Serbia and Slavo-Serbia: The Balkan Factor'
focus: history
pedagogy: CBI
phase: HIST.8 [Imperial Era]
word_target: 5000
objectives:
- Учень може описати створення Нової Сербії та Слов'яносербії
- Учень може пояснити роль військової колонізації
- Учень може проаналізувати взаємодію балканських колоністів з місцевим населенням
- Учень може оцінити вплив цієї політики на ліквідацію Січі
content_outline:
- section: 'Вступ: Чужинці на українській землі'
  points:
  - 'Середина XVIII століття: новий проект імперії — 1750-ті роки як період «затишшя перед бурею» перед остаточною ліквідацією
    Січі'
  - Хто такі «нові серби»? — Граничари (прикордонники) з Австрійської імперії, які втратили привілеї після реформ Марії-Терезії
  - 'Чому саме Південь України — [!history-bite] «Серби» як бренд: чому українські селяни масово записувалися у «серби», щоб
    уникнути кріпацтва та отримати землю'
  words: 850
- section: Створення військових поселень
  points:
  - 'Нова Сербія (1752): задум та реалізація — центр Новомиргород, ініціатор Іван Хорват, територія сучасної Кіровоградщини
    (Буго-Гардівська паланка)'
  - 'Слов''яносербія: продовження політики — 1753 рік, центр Бахмут (Слов''яносербськ), лідери Йован Шевич та Райко Прерадович'
  - 'Балканські офіцери та солдати — [!context] Балканський вектор: чому Австрія «відпустила» цих військових; етнічна строкатість
    (волохи, македонці, болгари)'
  - Пільги та умови переселення — Імператорський указ від 24 грудня 1751 року як юридична основа
  words: 850
- section: Життя в колоніях
  points:
  - Військова організація — система шанців (рот), принцип «однією рукою за плуг, іншою за шаблю»
  - 'Взаємодія з українським населенням — [!culture] Гусарський стиль: вплив балканської моди на український військовий одяг'
  - Конфлікти та асиміляція — постійні суперечки із запорожцями за «віковічні ґрунти»; швидка асиміляція рядових через православ'я
  - Місцева адміністрація — корупція та зловживання Івана Хорвата, приписки «мертвих душ»
  - 'Долі колоністів після ліквідації — 1764 рік: включення земель до Новоросійської губернії, перетворення еліти на дворянство'
  words: 850
- section: Первинні джерела
  points:
  - 'Укази про створення поселень — цитата з указу 1751: «...Сербовъ, желающихъ поселиться въ Россіи...»'
  - Скарги запорожців — [!quote] фрагмент скарги кошового отамана на конфіскацію худоби та захоплення земель
  - Карти та описи — накладання нових шанців на старі козацькі топоніми як картографічна колонізація
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Імперська тактика: «розділяй і володарюй» — [!myth-buster] Міф про «Дике Поле»: Нова Сербія виникла не в пустелі, а на
    заселених землях Запорожжя'
  - Колоністи як інструмент проти козаків — створення лояльного «етнічного бар'єру» для ізоляції Січі від Гетьманщини
  - 'Знищення автохтонного населення — contested term: «Заселення Півдня» vs «Анексія козацьких земель»'
  words: 850
- section: 'Підсумок: Наслідки для Півдня'
  points:
  - Від Нової Сербії до «Новоросії» — [!decolonization] тимчасові колонії як перехідний етап до повної імперської анексії
  - Мультиетнічність як результат колонізації — топоніми (Панчеве, Суботиці) та прізвища (Вуйчич, Попович) як спадок
  - Історична пам'ять — урок використання імперією одних поневолених народів проти інших
  words: 750
vocabulary_hints:
  required:
  - колонія (colony) — військова колонія, заснувати колонію
  - поселення (settlement) — військові поселення, система поселень
  - колоніст (colonist) — іноземні колоністи, права колоністів
  - військовий (military) — військовий устрій, військова служба
  - імперія (empire) — Російська імперія, Австрійська імперія, імперська політика
  - переселення (resettlement) — масове переселення, умови переселення
  - пільги (privileges) — отримати пільги, податкові пільги
  - асиміляція (assimilation) — швидка асиміляція, культурна асиміляція
  recommended:
  - автохтонний (autochthonous) — автохтонне населення, витіснення автохтонів
  - губернія (province) — Новоросійська губернія, утворення губернії
  - адміністрація (administration) — місцева адміністрація, зловживання адміністрації
  - мультиетнічність (multi-ethnicity) — етнічна строкатість, мультиетнічний регіон
  - гусари (hussars) — гусарські полки, гусарська форма
  - полк (regiment) — сформувати полк, командир полку
activity_hints:
- type: reading
  focus: Укази про створення поселень
  source: Архівні документи
  items: 4
- type: essay-response
  focus: Як військова колонізація допомогла імперії знищити Січ?
connects_to:
- hist-74 (Кінець Гетьманщини)
- 'hist-77 (Південь: «Новоросія»)'
prerequisites:
- hist-71 (Коліївщина)
persona:
  voice: Senior Professor of History
  role: Fortress Commandant
grammar:
- Минулий час в історичному наративі
- Військово-адміністративна лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Нова Сербія та Слов'яносербія** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

### Your RAG Tools (USE THEM)

You have access to Ukrainian language tools via MCP. **Use them during research.**

| Tool | When to use | Args |
|------|-------------|------|
| `query_wikipedia` | Get full article text (50K chars) for deep research | `query`, `mode="extract"` |
| `query_wikipedia` | See article structure before diving in | `query`, `mode="sections"` |
| `query_wikipedia` | Read a specific section by index | `query`, `mode="section"`, `section=N` |
| `query_wikipedia` | Find the right article title | `query`, `mode="search"` |
| `search_literary` | Find primary source excerpts (chronicles, poetry, legal texts, testimonies) | `query`, `genre` (optional) |
| `verify_words` | Check Ukrainian words exist in VESUM dictionary | `words` (list of strings) |
| `query_grac` | Check word frequency in Ukrainian corpus | `query`, `mode="frequency"` |

> **Important**: Invoke these tools using your standard tool-calling interface. Do NOT write Python code.

**Workflow**: Search Wikipedia FIRST for factual foundation → search literary RAG for primary quotes → verify vocabulary with VESUM.

### Research Requirements

1. **Sources**: Use `query_wikipedia` (mode=`extract`) for Ukrainian Wikipedia articles. Also consult history.org.ua, litopys.org.ua. Use `search_literary` for primary source excerpts. Russian-language sources are PROHIBITED.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find 2+ quotable primary source excerpts (original Ukrainian text preferred).
4. **Engagement Hooks**: Research and expand upon any hooks already suggested in the `content_outline`, and add new ones to reach a minimum of 6 total hooks mapped to specific content sections:
   - `[!myth-buster]` — Decolonization: correct imperial/Soviet myths
   - `[!history-bite]` — Surprising or lesser-known facts
   - `[!context]` — Broader historical/cultural context
   - `[!quote]` — Primary source citations
   - `[!decolonization]` — Ukraine-centric reframing
   - `[!culture]` — Cultural significance
5. **Decolonization Angle**: Identify how this topic has been distorted by imperial/Soviet historiography (e.g., erasure of identity, stripping of local agency, Soviet tropes) and define the Ukrainian-centric framing (centering local agency, restoring historical truth, using accurate terminology).
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
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Soviet tropes (e.g., erasure of victim identity), imperial terminology, or Moscow-centric timelines
- **Engagement callouts**: map 6+ hooks to specific sections during research (not as afterthought patches)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

===RESEARCH_START===

# Дослідження: Нова Сербія та Слов'яносербія

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Нова Сербія та Слов'яносербія"
type: "event" # "event", "biography", or "phenomenon"
vital_status: "living" # ONLY for biography: "living" or "deceased" (omit for events)
dates:
  start: "YYYY-MM-DD" # Event start OR biography birth (approximate: "~YYYY")
  end: "YYYY-MM-DD"   # Event end OR biography death (omit if living/ongoing)
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
- Section "{section_name}": [!hook_type] — {raw research fact/data to be used for this hook in Phase B}
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

## Friction Report (MANDATORY)

After Output Block 1, include the Friction Report:

===FRICTION_START===
**Phase**: Phase A: Research + Meta (Seminar)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | SOURCE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the plan's content_outline
- Do NOT use Russian-language sources
- Do NOT fabricate quotes or dates — if unsure, mark as "[needs verification]"
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
