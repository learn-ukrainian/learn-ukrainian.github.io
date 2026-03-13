# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-111
level: HIST
sequence: 111
slug: surgunlik
version: '3.0'
title: 'Sürgünlik: Депортації кримських татар та інших народів'
subtitle: Sürgünlik and Soviet Deportations of Minorities 1941-1949
focus: history
pedagogy: CBI
phase: HIST.11 [Post-War Soviet Ukraine]
word_target: 5000
objectives:
- Учень може описати депортацію кримських татар 1944 року
- Учень може пояснити механізм та наслідки Sürgünlik
- Учень може порівняти депортації різних народів (татари, греки, німці)
- Учень може проаналізувати радянську політику етнічних чисток
- Учень може проаналізувати боротьбу кримських татар за повернення
- Учень може оцінити Sürgünlik як геноцид
content_outline:
- section: 'Вступ: Радянська політика депортацій'
  points:
  - 'Контекст: депортації як інструмент Сталіна — системна політика «соціальної інженерії» та «колективної провини» для контролю
    територій; cultural hook: [!context] Сталінська політика «колективної провини» як інструмент тоталітарного контролю'
  - 'Хронологія: 1941-1949 — хвиля депортацій почалася з німців (серпень 1941) і досягла піку в Криму у травні-червні 1944
    року'
  - 'Sürgünlik: 18 травня 1944 як найтрагічніша дата — початок основної фази депортації о 3-й годині ранку'
  words: 850
- section: 'Сургунлік: Депортація кримських татар'
  points:
  - 'Механізм депортації (700 слів) — блискавична операція НКВС із залученням 32 тисяч співробітників; history bite: [!history-bite]
    «15 хвилин на збори»: як раптовість стала частиною терору'
  - 'Сталінський наказ: звинувачення у «зраді» — постанова ДКО №5859сс від 11 травня 1944 року; myth buster: [!myth-buster]
    Міф про «народ-зрадник» проти факту участі 17 тисяч кримських татар у Червоній армії (в т.ч. Амет-Хан Султан)'
  - Як відбувалась депортація 18 травня — 15 хвилин на збори, люди встигали взяти лише Коран або джезве (спогади Усніє Чолпан)
  - Вагони для худоби та смерть у дорозі — перевезення у «телятниках» без води та їжі протягом 2-3 тижнів, викидання померлих
    на ходу
  - 'Життя в засланні (900 слів) — спецпоселення з комендантським режимом та каторжною працею; destinations: Узбекистан (більшість),
    Казахстан, Урал, Марійська АРСР'
  - Узбекистан та інші місця заслання — основна маса депортованих опинилася в Узбекистані, також Казахстан, Урал, Марійська
    АРСР
  - 'Голод, хвороби, смертність: 46% загиблих — дані національного руху про смертність у перші роки заслання; fact: [!fact]
    46% загиблих: демографічна катастрофа, яку приховувала радянська статистика'
  - Заборона повертатись до 1989 — кримінальна відповідальність (20 років каторги) за втечу зі спецпоселення
  - Втрата землі, мови та культури — цілеспрямоване знищення ідентичності та топоніміки Криму
  words: 850
- section: 'Інші жертви: Греки, німці та інші народи'
  points:
  - 'Греки Криму та Приазов''я (1944-1949) — депортація 27-28 червня 1944 року (понад 15 тис. греків); history bite: [!history-bite]
    Зачистка після зачистки: депортація греків та болгар через місяць після татар'
  - Депортація до Казахстану та Середньої Азії — розселення у спецпоселеннях, аналогічні умови виживання
  - Втрата грецької мови та культури — розпорошення громад призвело до асиміляції
  - Німці України / Volksdeutsche (1941-1945) — перша хвиля депортації у серпні-вересні 1941 року (бл. 60 тис. осіб) як «превентивний
    захід»
  - Депортація на початку війни — превентивний захід сталінського режиму перед окупацією
  - Спецпоселення в Сибіру та Казахстані — використання німців у Трудармії
  - 'Інші: болгари, вірмени, румуни (коротко) — червнева депортація 1944 року охопила також 12 тис. болгар і 9 тис. вірмен'
  words: 850
- section: Первинні джерела
  points:
  - 'Свідчення вижилих кримських татар — спогади про ранок 18 травня, хаос і страх; include quote from Усніє Чолпан: «Нам
    заборонялося все, окрім смерті»'
  - Спогади греків та німців — паралелі у досвіді вигнання та виживання
  - Документи НКВД про депортації — сухі звіти про кількість ешелонів, що контрастують з емоційними спогадами жертв
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Радянський наратив: «зрадники» та «колаборанти» — виправдання злочину нібито масовою зрадою (міф про 20 тис. дезертирів)'
  - 'Реальність: етнічна чистка за національною ознакою — покарання цілих народів (татари, чеченці, калмики), а не окремих
    колаборантів'
  - Визнання Sürgünlik як геноциду — системність дій, намір знищити групу, умови для фізичного вимирання
  - Паралелі з іншими депортаціями — чеченці, інгуші, калмики як жертви аналогічної політики
  words: 850
- section: 'Підсумок: Пам''ять та боротьба'
  points:
  - Рух за повернення кримських татар — початок боротьби ще в місцях заслання (петиції, демонстрації), роль Мустафи Джемілєва
  - Повернення після 1989 — скасування заборони на повернення лише в часи Перебудови
  - 'Окупація Криму 2014 та нові репресії — «гібридна депортація», заборона Меджлісу, нові арешти; context: Історія повторюється'
  words: 750
vocabulary_hints:
  required:
  - депортація (deportation) — масова/примусова депортація, сталінська депортація, хвиля депортацій
  - геноцид (genocide) — визнання геноцидом, акт геноциду, ознаки геноциду
  - заслання (exile) — місця заслання, роки заслання, померти у засланні
  - кримські татари (Crimean Tatars) — корінний народ, депортація кримських татар, повернення кримських татар, Sürgünlik
  - греки (Greeks) — кримські греки, депортація греків, греки Приазов'я
  - німці (Germans) — кримські німці, депортація німців, спецпоселення німців
  - репресії (repressions) — політичні репресії, жертви репресій, сталінські репресії
  - повернення (return) — право на повернення, рух за повернення, довгоочікуване повернення
  - етнічна чистка (ethnic cleansing) — спланована етнічна чистка, ознаки етнічної чистки
  - пам'ять (memory) — історична пам'ять, збереження пам'яті, день пам'яті
  - спецпоселення (special settlement) — режим спецпоселення, життя у спецпоселенні, втеча зі спецпоселення (20 років каторги)
  recommended:
  - вагон (wagon) — товарний вагон, вагон для худоби («телятник»), ешелони з вагонами
  - смертність (mortality) — висока смертність, рівень смертності, дитяча смертність (46% загиблих)
  - реабілітація (rehabilitation) — політична реабілітація, закон про реабілітацію
  - батьківщина (homeland) — туга за батьківщиною, повернення на батьківщину
  - вижилі (survivors) — спогади вижилих, свідчення вижилих (Усніє Чолпан)
  - меджліс (Mejlis) — Меджліс кримськотатарського народу, заборона Меджлісу
  - Приазов'я (Azov region) — греки Приазов'я, села Приазов'я
  - колаборант (collaborator) — звинувачення у колабораціонізмі, міф про колаборантів
  - звинувачення (accusation) — безпідставні звинувачення, колективне звинувачення
activity_hints:
- type: reading
  focus: Свідчення вижилих кримських татар
  source: Усна історія
  items: 4
- type: reading
  focus: Спогади греків Приазов'я про депортацію
  source: Усна історія
  items: 3
- type: critical-analysis
  focus: 'Верифікація фактів: Історичні факти про депортації народів'
  items: 5
- type: essay-response
  focus: Чому депортація кримських татар є геноцидом?
connects_to:
- hist-110 (Депортації українців)
- hist-128 (Кримські татари після 2014)
- hist-128 (Анексія Криму 2014)
prerequisites:
- 'hist-105 (Друга світова: Початок)'
persona:
  voice: Senior Professor of History
  role: Elder Witness
grammar:
- Минулий час в історичному наративі
- Лексика репресій та депортацій
- Пасивні конструкції
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Sürgünlik: Депортації кримських татар та інших народів** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Sürgünlik: Депортації кримських татар та інших народів

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Sürgünlik: Депортації кримських татар та інших народів"
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
