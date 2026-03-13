# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-104
level: HIST
sequence: 104
slug: karpatska-ukraina
version: '2.0'
title: Карпатська Україна 1938-1939
subtitle: 'Carpatho-Ukraine: A Brief Independence'
focus: history
pedagogy: CBI
phase: HIST.9 [WWI & Revolution]
word_target: 5000
objectives:
- Учень може описати створення Карпатської України
- Учень може пояснити геополітичний контекст 1938-1939 років
- Учень може проаналізувати опір Карпатської Січі
- Учень може оцінити значення цього досвіду для української незалежності
content_outline:
- section: 'Вступ: Один день незалежності'
  points:
  - '15 березня 1939: проголошення незалежності — ключова дата, Хуст стає тимчасовою столицею поки Гітлер входить у Прагу'
  - 'Чому Карпатська Україна — символ — cultural hook: [!history-bite] Держава проіснувала офіційно менше доби, але мала досконалу
    законодавчу базу (прапор, гімн, мова)'
  - 'Географічний контекст: Закарпаття — втрата Ужгорода і Мукачева ще в листопаді 1938 за Віденським арбітражем'
  words: 850
- section: Передісторія та автономія
  points:
  - Підкарпатська Русь у складі Чехословаччини — невиконана обіцянка автономії за Сен-Жерменським договором
  - Мюнхенська угода та її наслідки — [!context] унікальна ситуація «держави в державі», Закарпаття стає центром тяжіння для
    оунівців
  - Автономія та перші кроки до державності — 11 жовтня 1938 створення першого уряду, 22 листопада прийняття конституційного
    закону Прагою
  - Августин Волошин та його уряд — українізація освіти й преси, формування Організації Народної Оборони «Карпатська Січ»
  words: 850
- section: Незалежність та оборона
  points:
  - Проголошення незалежності в Хусті — прийняття Конституційного Закону Ч.1 (синьо-жовтий прапор, гімн «Ще не вмерла...»)
  - 'Карпатська Січ: добровольці з усієї України — роль міграції свідомих українців (Ольжич, Шухевич) та штабу (Колодзінський,
    Коссак)'
  - 'Угорська агресія та нерівна битва — [!myth-buster] спростування міфу про «німецьку інтригу»: українці билися всупереч
    планам Берліна'
  - 'Оборона Хусту та інших міст — Бій на Красному полі (16 березня) як «Українські Термопіли»: 2000 січовиків проти регулярної
    армії'
  - Поразка та окупація — жорстокість окупантів, розстріли на перевалах, репресії проти вчителів
  words: 850
- section: Первинні джерела
  points:
  - Акт проголошення незалежності — [!quote] цитати з Конституційного Закону Ч.1 про державний устрій
  - Спогади учасників Карпатської Січі — щоденники Василя Ґренджі-Донського («Щастя і горе Карпатської України») та Севастіяна
    Сабола
  - Дипломатичне листування — ігноровані Берліном телеграми Волошина як свідчення відчайдушної дипломатії
  words: 850
- section: Деколонізаційний погляд
  points:
  - Карпатська Україна vs. угорський наратив — [!decolonization] спростування термінів «відновлення порядку» та «маріонеткова
    держава»
  - Чому це був справжній національний рух — вибори 12 лютого 1939 (92% підтримки) як доказ легітимності та суб'єктності
  - Зв'язок з іншими українськими землями — тяглість державницької традиції від УНР/ЗУНР
  words: 850
- section: 'Підсумок: Спадщина та пам''ять'
  points:
  - Символічне значення для незалежності 1991 — прапор і гімн 1939 року стали державними символами сучасної України
  - Пам'ять про Карпатську Січ сьогодні — Меморіал на Красному полі, героїзація захисників
  - Закарпаття в сучасній Україні — [!culture] феномен «Срібної Землі» в літературі (Улас Самчук, Олександр Олесь)
  words: 750
vocabulary_hints:
  required:
  - автономія (autonomy) — здобута в 1938, втрачена в 1939
  - проголошення (proclamation) — ~ незалежності, ~ республіки
  - незалежність (independence) — одноденна ~, боротьба за ~
  - окупація (occupation) — угорська ~, початок ~
  - оборона (defense) — організація народної ~, героїчна ~
  - січовик (Sich member) — героїзм ~ів, розстріли ~ів
  - агресія (aggression) — збройна ~, акт ~
  - уряд (government) — автономний ~, еміграційний ~
  recommended:
  - доброволець (volunteer) — тисячі ~ів з Галичини
  - геополітика (geopolitics) — складна ~ Центральної Європи
  - інтервенція (intervention) — військова ~, іноземна ~
  - анексія (annexation) — незаконна ~, спроба ~
  - спротив (resistance) — чинити ~, збройний ~
  - символ (symbol) — ~ незламності, державний ~
activity_hints:
- type: reading
  focus: Спогади учасників Карпатської Січі
  source: Архівні матеріали
  items: 4
- type: essay-response
  focus: Чому Карпатська Україна важлива для української ідентичності?
connects_to:
- 'hist-105 (Друга світова: початок)'
- hist-118 (Діаспора)
prerequisites:
- hist-103 (Українці в Другій світовій)
persona:
  voice: Senior Professor of History
  role: Sich Guard
grammar:
- Минулий час в історичному наративі
- Географічна та політична лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Карпатська Україна 1938-1939** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Карпатська Україна 1938-1939

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Карпатська Україна 1938-1939"
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
