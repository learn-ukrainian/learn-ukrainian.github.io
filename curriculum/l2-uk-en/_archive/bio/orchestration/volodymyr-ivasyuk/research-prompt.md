# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: bio-149
level: BIO
sequence: 149
slug: volodymyr-ivasyuk
version: '2.0'
title: 'Володимир Івасюк: Автор Червоної рути'
focus: biography
phase: BIO
word_target: 5000
objectives:
- 'Analyze the life and legacy of володимир івасюк: автор червоної рути'
- Evaluate the contributions of пісня, яка стала гімном
- Trace the career and influence of мистецтво як опір
sources:
- name: Володимир Івасюк (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Івасюк_Володимир_Михайлович
  type: primary
  notes: Основна біографічна інформація
- name: Музей Володимира Івасюка
  url: https://ivasyuk.org.ua/
  type: reference
  notes: Архівні матеріали та творча спадщина
- name: Фестиваль Червона рута
  url: https://chervona-ruta.org/
  type: reference
  notes: Культурний вплив
content_outline:
- section: Вступ — Пісня, яка стала гімном
  points:
  - Червона рута як символ українського відродження
  - Від студента-медика до легенди
  - Трагічна загадкова смерть
  words: 700
- section: Буковинське дитинство
  points:
  - Народження в Кіцмані (1949)
  - Музична родина
  - Ранній талант до музики
  words: 700
- section: Студентські роки та перші пісні
  points:
  - Медичний інститут у Чернівцях
  - Початок композиторської діяльності
  - Перші успіхи
  words: 700
- section: Тріумф Червоної рути
  points:
  - Створення легендарної пісні (1968)
  - Фестиваль у Чернівцях
  - Національний та міжнародний успіх
  words: 700
- section: Творча спадщина
  points:
  - Інші відомі пісні (Водограй, Два перстені)
  - Вплив на українську естраду
  - Синтез фольклору та сучасності
  words: 700
- section: Загадкова смерть
  points:
  - Переслідування КДБ
  - Загибель у 1979 році
  - Версії про причини смерті
  words: 700
- section: Дискусія — Мистецтво як опір
  points:
  - Чому пісня стала небезпечною для влади
  - Івасюк у національній пам'яті
  words: 800
vocabulary_hints:
  required:
  - композитор (composer)
  - естрада (pop music/variety show)
  - пісня (song)
  - фестиваль (festival)
  - фольклор (folklore)
  - мелодія (melody)
  - переслідування (persecution)
  - КДБ (KGB)
  - спадщина (legacy)
  - відродження (revival)
  recommended:
  - аранжування (arrangement)
  - текстовик (lyricist)
  - гімн (anthem)
  - культурний опір (cultural resistance)
  - самобутність (authenticity)
activity_hints:
- type: reading
  focus: Тексти пісень Івасюка
  source: Первинні джерела
  items: 3 passages
- type: essay-response
  focus: Чому Червона рута стала символом?
  output: Культурологічний есей
connects_to:
- bio-83-kvitka-tsisyk
- bio-77-vasyl-stus
- bio-23-mykola-lysenko
prerequisites:
- bio-75-vasyl-symonenko
persona:
  voice: Senior Biographer
  role: Pop Composer
module_type: biography
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Володимир Івасюк: Автор Червоної рути** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Володимир Івасюк: Автор Червоної рути

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Володимир Івасюк: Автор Червоної рути"
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
