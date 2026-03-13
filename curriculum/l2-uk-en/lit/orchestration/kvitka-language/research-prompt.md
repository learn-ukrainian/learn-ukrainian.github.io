# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: lit-010
level: LIT
sequence: 10
slug: kvitka-language
version: '2.0'
title: 'Мова як Маніфест: Голос Слобожанщини'
subtitle: 'LIT-010: Як Квітка створив Літературну Норму'
focus: style
pedagogy: literature
phase: LIT.2 Sentimentalism (Kvitka-Osnovianenko)
word_target: 5000
objectives:
- Analyze Kvitka's language strategies
- Compare stylistic registers in his works
- Evaluate his role in establishing literary Ukrainian
sources:
- name: Маруся — мовні особливості
  url: https://www.ukrlib.com.ua/books/printit.php?tid=252
  type: primary
  notes: Сентиментальний стиль
- name: Конотопська відьма — мовні особливості
  url: https://www.ukrlib.com.ua/books/printit.php?tid=254
  type: primary
  notes: Бурлескний стиль
- name: Слобожанський діалект
  url: https://uk.wikipedia.org/wiki/Слобожанський_діалект
  type: reference
  notes: Діалектологічний контекст
content_outline:
- section: Вступ — Як дворянин став \"голосом народу\"
  points:
  - Мовна ситуація Квітки (українська vs російська)
  - Свідомий вибір української мови
  - Роль у становленні літературної норми
  words: 850
- section: '"Грицько Основ''яненко" — літературна маска'
  points:
  - Оповідач-селянин як наративна стратегія
  - Імітація усного мовлення
  - Довіра читача до "свого"
  words: 850
- section: Два стилі — бурлеск vs сентименталізм
  points:
  - '"Конотопська відьма" — лайка, канцеляризми, гротеск'
  - '"Маруся" — пестливість, емотивність, піднесеність'
  - Єдність авторського голосу за різних масок
  words: 850
- section: Слобожанський діалект
  points:
  - Фонетичні особливості (характерні звуки)
  - Лексичні діалектизми
  - Синтаксичні конструкції
  words: 850
- section: Мовні портрети персонажів
  points:
  - '"Макаронічна" мова Пістряка'
  - Солдатський жаргон москаля
  - Мова панства vs мова народу
  words: 850
- section: Підсумок — Слово як зброя
  points:
  - Мова і національна гідність
  - Вплив Квітки на літературну мову
  - Перехід до Шевченка
  words: 750
vocabulary_hints:
  required:
  - діалект (dialect)
  - літературна норма (literary norm)
  - оповідач (narrator)
  - маска (mask)
  - пестлива лексика (diminutive lexicon)
  - канцеляризм (bureaucratic language)
  - емотив (emotive)
  - димінутив (diminutive)
  - макаронічна мова (macaronic language)
  - жаргон (jargon)
  recommended:
  - фонетика (phonetics)
  - лексика (lexicon)
  - синтаксис (syntax)
  - гротеск (grotesque)
  - наратив (narrative)
activity_hints:
- type: reading
  focus: Порівняння уривків з різних творів
  source: UkrLib tid=252, 254
  items: 6+
- type: essay-response
  focus: Як слово стає зброєю в боротьбі за гідність нації?
  output: Мовознавче есе
connects_to:
- lit-15 (Zapovit — мова Шевченка)
- lit-24 (Language Question — мовне питання)
- lit-29 (Language of Realism — мова Нечуя)
prerequisites:
- lit-06 to lit-09 (all Kvitka modules)
- Understanding of Ukrainian dialects
persona:
  voice: Senior Philologist & Critic
  role: Vernacular Advocate
grammar:
- Stylistic contrast (sentimentalism vs burlesque)
- Dialect features (Slobozhanshchyna)
- Emotive syntax and vocabulary
module_type: style
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Мова як Маніфест: Голос Слобожанщини** for the **lit** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Мова як Маніфест: Голос Слобожанщини

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Мова як Маніфест: Голос Слобожанщини"
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
