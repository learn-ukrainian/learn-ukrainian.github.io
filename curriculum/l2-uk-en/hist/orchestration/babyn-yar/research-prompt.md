# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-106
level: HIST
sequence: 106
slug: babyn-yar
version: '2.0'
title: Бабин Яр та Голокост в Україні
subtitle: Babi Yar and the Holocaust in Ukraine
focus: history
pedagogy: seminar
phase: HIST.10 [Soviet Period & Tragedies]
word_target: 5000
objectives:
- Учень може описати події Голокосту на території України та їхній масштаб
- Учень може проаналізувати трагедію Бабиного Яру в контексті нацистської окупації
- Учень може оцінити роль місцевого населення — від співучасті до порятунку
- Учень може зрозуміти радянську політику замовчування та сучасну меморіалізацію
content_outline:
- section: 'Вступ: Україна напередодні трагедії'
  points:
  - Єврейська громада України до 1941 року — Київ як центр єврейського життя
  - Нацистська окупація та початок масових розстрілів — вибухи на Хрещатику як привід для знищення євреїв
  - Чому Україна стала «кривавими землями» — [!context] Концепція Тімоті Снайдера про подвійний терор (сталінський та нацистський)
  words: 850
- section: 'Бабин Яр: 29-30 вересня 1941'
  points:
  - 'Хронологія подій: наказ, збір, розстріл — «Дорога смерті», технологія вбивства (роздягання, побиття)'
  - 'Масштаб трагедії: 33 771 жертва за два дні — згідно зі звітом айнзацгрупи № 101'
  - 'Свідчення вцілілих: Діна Проничева та інші — [!quote] Уривок про момент перед розстрілом («Я закрила очі...»)'
  - Роль нацистських айнзацгруп та місцевої поліції — зондеркоманда 4а (Пауль Блобель) як виконавці, поліція як оточення
  words: 850
- section: Голокост на території України
  points:
  - «Голокост від куль» — специфіка знищення на Сході — [!history-bite] Відмінність від газових камер у Європі
  - 'Інші місця масових розстрілів: Дробицький Яр, Богданівка — понад 50 тис. жертв у Богданівці (Миколаївщина)'
  - Доля ромів, військовополонені, психічно хворих — знищення пацієнтів Кирилівської лікарні
  words: 850
- section: Первинні джерела
  points:
  - 'Німецькі документи: звіти айнзацгруп — бюрократична мова («оброблено», «ліквідовано»)'
  - Свідчення вцілілих та очевидців — Діна Проничева, Геня Баташева
  - 'Поезія: «Бабин Яр» Євгена Євтушенка (1961) — [!culture] Прорив інформаційної блокади в СРСР'
  words: 850
- section: Праведники народів світу
  points:
  - Українці, які рятували євреїв — [!myth-buster] Понад 2600 Праведників проти міфу про тотальну колаборацію
  - Митрополит Шептицький та греко-католицька церква — пастирське послання «Не убий!» та порятунок дітей (Курт Левін)
  - 'Ціна порятунку: ризик для рятівників — смертна кара для всієї родини'
  words: 850
- section: Замовчування та пам'ять
  points:
  - 'Радянська політика: «тут загинули радянські громадяни» — знеособлення єврейських жертв, пам''ятники «жертвам фашизму»'
  - Куренівська трагедія 1961 року — [!history-bite] «Помста Бабиного Яру» за спробу залити яр пульпою
  - Меморіалізація після незалежності та сучасні дебати — Менора, пам'ятник Олені Телізі, виступ Івана Дзюби
  words: 750
vocabulary_hints:
  required:
  - Голокост (Holocaust) — термін «Голокост від куль» (Holocaust by Bullets)
  - айнзацгрупа (Einsatzgruppe) — мобільні каральні підрозділи (Sonderkommando 4a)
  - розстріл (execution by shooting) — масові розстріли (mass shootings)
  - меморіал (memorial) — меморіальний центр, вшанування пам'яті
  - жертва (victim) — невинні жертви, кількість жертв
  - окупація (occupation) — нацистська окупація Києва
  - геноцид (genocide) — політика геноциду проти євреїв та ромів
  - Праведник народів світу (Righteous Among the Nations) — звання, яке надає Яд Вашем
  recommended:
  - гетто (ghetto) — створення гетто в містах України
  - колабораціонізм (collaborationism) — співпраця з окупаційною владою
  - свідчення (testimony) — свідчення очевидців (eyewitness accounts)
  - замовчування (silencing) — політика замовчування (policy of silence)
  - меморіалізація (memorialization) — культура пам'яті
activity_hints:
- type: reading
  focus: Свідчення Діни Проничевої
  source: Архівні матеріали
  items: 4
- type: essay-response
  focus: Чому пам'ять про Голокост важлива для України
connects_to:
- hist-107 (УПА)
- 'hist-108 (Синтез: Трагедії)'
prerequisites:
- 'hist-105 (Друга світова: Початок)'
persona:
  voice: Senior Professor of History
  role: Local Witness
grammar:
- Минулий час у трагічному наративі
- Пасивні конструкції для опису злочинів
- Лексика пам'яті та меморіалізації
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Бабин Яр та Голокост в Україні** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Бабин Яр та Голокост в Україні

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Бабин Яр та Голокост в Україні"
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
