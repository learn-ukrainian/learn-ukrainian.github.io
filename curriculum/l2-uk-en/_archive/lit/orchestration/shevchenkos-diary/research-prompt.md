# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: lit-019
level: LIT
sequence: 19
slug: shevchenkos-diary
version: '2.0'
title: Щоденник ("Журнал") Шевченка
subtitle: 'Shevchenko''s Diary: The Inner World'
focus: literature
pedagogy: Seminar
phase: LIT.3 The Prophet (Taras Shevchenko)
word_target: 5000
objectives:
- Understand the psychological shift in Shevchenko's diary from exile to freedom.
- Analyze the contrast between his public image ("prophet") and private self ("human").
- Examine his intellectual breadth (arts, technology, literature) and emotional depth.
sources:
- name: Щоденник Шевченка — повний текст
  url: https://www.ukrlib.com.ua/books/printit.php?tid=44
  type: primary
  notes: Щоденник 1857-1858 років
- name: Аналіз "Журналу"
  url: https://www.ukrlib.com.ua/analiz/printit.php?tid=44
  type: secondary
  notes: Літературознавчий аналіз
- name: Заслання Шевченка
  url: https://uk.wikipedia.org/wiki/Заслання_Тараса_Шевченка
  type: reference
  notes: Історичний контекст
content_outline:
- section: Вступ — Публічний vs приватний Шевченко
  points:
  - Кобзар vs Журнал
  - Чому щоденник написаний російською
  - Жанр щоденника в літературі
  words: 850
- section: Контекст написання (1857-1858)
  points:
  - Кінець заслання
  - Шлях з Казахстану до Петербурга
  - Нове життя після неволі
  words: 850
- section: Внутрішній світ поета
  points:
  - Рефлексії про мистецтво
  - Погляди на театр і літературу
  - Технічні інтереси (фотографія)
  words: 850
- section: Мовний аналіз
  points:
  - Розмовна російська XIX століття
  - Інтроспективна лексика
  - Порівняння з поетичною мовою
  words: 850
- section: Психологічний портрет
  points:
  - Самотність і пошук кохання
  - Стосунки з друзями
  - Здоров'я і передчуття смерті
  words: 850
- section: Підсумок — Людина за маскою пророка
  points:
  - Щоденник як документ епохи
  - Демістифікація генія
  - Перехід до рецепції
  words: 750
vocabulary_hints:
  required:
  - щоденник (diary)
  - журнал (journal)
  - рефлексія (reflection)
  - інтроспекція (introspection)
  - заслання (exile)
  - неволя (captivity)
  - демістифікація (demystification)
  - психологічний портрет (psychological portrait)
  - приватний (private)
  - публічний (public)
  recommended:
  - фотографія (photography)
  - самотність (loneliness)
  - передчуття (premonition)
  - стосунки (relationships)
  - епоха (era)
activity_hints:
- type: reading
  focus: Уривки з "Журналу" Шевченка
  source: UkrLib tid=44
  items: 5+
- type: essay-response
  focus: Контраст між "Кобзарем" і "Журналом"
  output: Компаративне есе
connects_to:
- lit-20 (Cult of Shevchenko — рецепція)
- lit-17 (The Artist — автобіографія)
prerequisites:
- lit-11 to lit-18 (all Shevchenko modules)
- Understanding of diary genre
persona:
  voice: Senior Philologist & Critic
  role: Exiled Diarist
grammar:
- Introspective language
- Conversational Russian of 19th c.
module_type: literature
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Щоденник ("Журнал") Шевченка** for the **lit** track. Produce structured research notes that will drive content writing in Phase B.

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
- **Word count**: minimum **4000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Soviet tropes (e.g., erasure of victim identity), imperial terminology, or Moscow-centric timelines
- **Engagement callouts**: map 6+ hooks to specific sections during research (not as afterthought patches)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

===RESEARCH_START===

# Дослідження: Щоденник ("Журнал") Шевченка

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Щоденник ("Журнал") Шевченка"
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
