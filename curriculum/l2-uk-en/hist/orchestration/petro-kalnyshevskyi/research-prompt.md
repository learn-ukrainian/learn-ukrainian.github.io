# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-073
level: HIST
sequence: 73
slug: petro-kalnyshevskyi
version: '2.0'
title: 'Петро Калнишевський: Останній кошовий'
subtitle: 'Petro Kalnyshevskyi: The Last Koshovyi'
focus: history
pedagogy: CBI
phase: B2.3b [Українська історія]
word_target: 5000
objectives:
- Учень може охарактеризувати постать Петра Калнишевського
- Учень може пояснити причини руйнування Запорозької Січі
- Учень може проаналізувати значення соловецького ув'язнення
- Учень може оцінити роль Калнишевського в українській пам'яті
content_outline:
- section: 'Вступ: Трагічна велич останнього отамана та епоха великих надій'
  points:
  - Петро Калнишевський як останній кошовий отаман Запорозької Січі (1765-1775) — дати життя 1690-1803 рр., прожив 112 років,
    канонізований як Петро Багатостраждальний
  - Золота доба Нової Січі під протекторатом Російської імперії — період економічного розквіту та заселення степу («Золота
    осінь» козацтва)
  - Трагічний фінал незалежності запорозького козацтва — [!myth-buster] Калнишевський не був немічним дідом; у 80 років він
    керував військом і будував економічну імперію
  words: 450
- section: 'Шлях до булави: Від козака до стратега вільної республіки'
  points:
  - Походження та рання кар'єра Калнишевського в Запорозькому Війську — родом із с. Пустовійтівка, шляхетського походження,
    пройшов шлях від осавула до судді
  - Обрання кошовим отаманом тричі (1765, 1768, 1775) — переобирався 10 років поспіль, що було порушенням традиції щорічної
    зміни, але ознакою стабільності
  - Військові кампанії проти турків та участь у російсько-турецькій війні (1768-1774) — отримав найвищі ордени імперії, які
    не врятували його від репресій
  - 'Економічне зміцнення Січі через торгівлю та землеробство — [!history-bite] Калнишевський був «олігархом» XVIII ст.: експортував
    зерно/рибу до Європи та фінансував церкви'
  words: 450
- section: 'Чорна рада 1775 року: Кінець Війська Запорозького та тріумф підступності'
  points:
  - Указ Катерини II від 3 серпня 1775 року про ліквідацію Запорозької Січі — [!context] Знищення відбулося одразу після перемоги
    над турками, здобутої руками козаків
  - Військова операція генерала Текелія з оточення та захоплення Січі — 4 червня 1775 р., 100-тисячне військо оточило Січ,
    повертаючись з фронту
  - Арешт Калнишевського та старшини без опору — легендарна фраза «Не чиніть опору, бо погубите себе і Україну»; арешт судді
    Головатого та писаря Глоби
  - 'Причини руйнування: геополітичні інтереси імперії та земельна колонізація Півдня — після Кючук-Кайнарджійського миру
    козаки стали «непотрібні» імперії'
  words: 450
- section: 'Соловецька в''язниця: Чверть століття у темряві та холоді Білого моря'
  points:
  - Ув'язнення Калнишевського в Соловецькому монастирі 1776-1801 рр. — прибув 29 липня 1776 р., провів у «кам'яному мішку»
    25 років
  - Умови утримання в камері з мінімальним світлом і контактом — [!history-bite] Камера 1x3 м, виводили лише тричі на рік
    (Великдень, Різдво, Преображення)
  - 25 років в'язниці без суду та вироку — повна ізоляція, навіть варту постійно змінювали, щоб уникнути спілкування
  - Звільнення Павлом I у 1801 році у віці понад 110 років — звільнений Олександром I (указ 1801 р.), але відмовився повертатися
  words: 450
- section: 'Духовна медицина Соловків: Як вижити у пеклі та зберегти душу'
  points:
  - Глибока релігійність як джерело витривалості — отримував 1 рубль на день (величезні кошти), купував книги та ремонтував
    камеру
  - Відмова від волі після звільнення та залишення в монастирі — [!quote] «Тут я знайшов спокій, тут і залишуся з Богом»
  - Смерть 1803 року як завершення духовного шляху — помер 31 жовтня 1803 р. у віці 112 років, похований біля Преображенського
    собору
  words: 450
- section: 'Деколонізаційний погляд: Калнишевський проти імперського міфу забуття'
  points:
  - Радянське замовчування долі Калнишевського та Запорожжя — імперія прагнула стерти не тільки Січ, а й пам'ять про альтернативну
    модель розвитку
  - Реабілітація пам'яті в незалежній Україні — початок досліджень ще у XIX ст. (Єфименко, Яворницький), повернення героя
    у сучасній Україні
  - Ліквідація Січі як акт колоніального геноциду автономії — [!decolonization] Імперія боялася моделі вільного суспільства
    як конкурента кріпацтву
  words: 450
- section: 'Спадщина та канонізація: Повернення святого отамана додому'
  points:
  - 'Канонізація УПЦ Київського Патріархату 1996 року — уточнення: канонізація УПЦ КП відбулася у 2008 р., УПЦ МП — у 2015
    р.'
  - Калнишевський як символ незламності українського духу — шанується як Святий Праведний Петро Багатостраждальний
  words: 450
- section: 'Читання: Останнє слово отамана та голос вічності крізь століття'
  points:
  - Аналіз свідчень про арешт і промову Калнишевського — на основі «Сказки» Хоми Григорієва та народних переказів
  words: 450
- section: 'Первинні джерела: Свідчення незламності та трагедії вільного Війська'
  points:
  - 'Указ Катерини II про ліквідацію Січі — [!source] Цитата: «Сама назва запорозьких козаків віднині і навіки хай зникне»'
  - Мемуари сучасників про долю останніх запорожців — листи Калнишевського до Потьомкіна як спроба дипломатії
  words: 450
- section: 'Підсумок: Вічний отаман нашої пам''яті'
  points:
  - Калнишевський як символ боротьби за волю — місток між козацькою добою та сучасною Україною
  words: 450
- section: Потрібно більше практики?
  points:
  - Додаткові вправи для закріплення лексики про козацтво
  - Практика читання первинних джерел XVIII століття
  - Завдання на розвиток навичок історичного аналізу
  words: 500
vocabulary_hints:
  required:
  - 'кошовий отаман (Koshovyi Otaman) — виборний лідер; common collocation: останній кошовий'
  - 'Запорозька Січ (Zaporozhian Sich) — військово-політичний центр; collocation: ліквідація Січі'
  - 'Соловецький монастир (Solovetsky Monastery) — місце ув''язнення; context: Соловки як тюрма народів'
  - 'Катерина II (Catherine II) — російська імператриця; action: знищила Січ'
  - 'ліквідація (liquidation/destruction) — collocation: ліквідація автономії/Січі'
  - 'канонізація (canonization) — визнання святим; title: Петро Багатостраждальний'
  - незламність (indomitability/unbreakability) — ключова риса характеру
  - 'в''язниця (prison) — context: 25 років у в''язниці'
  recommended:
  - Нова Січ (New Sich) — період 1734–1775 рр.
  - генерал Текелій (General Tekeli) — виконавець наказу про руйнування
  - релігійність (religiosity) — джерело сили
  - витривалість (endurance) — фізична та духовна стійкість
activity_hints:
- type: reading
  focus: аналіз указу про ліквідацію Січі
- type: essay-response
  focus: причини знищення козацької вольниці
- type: critical-analysis
  focus: 'Критичний аналіз послідовності: життя Калнишевського від обрання до смерті'
  items: 3
- type: critical-analysis
  focus: 'Верифікація фактів: факти про соловецьке ув''язнення'
  items: 4
persona:
  voice: Senior Professor of History
  role: Exiled Otaman
grammar:
- Релігійна та тюремна лексика
- Опис душевного стану
register: публіцистичний
prerequisites:
- opryshky
connects_to:
- kinets-hetmanshchyny

```

---

## PART 1: Deep Research

Research **Петро Калнишевський: Останній кошовий** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Петро Калнишевський: Останній кошовий

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Петро Калнишевський: Останній кошовий"
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
