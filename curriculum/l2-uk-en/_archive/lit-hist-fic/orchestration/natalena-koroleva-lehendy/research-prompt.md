# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: lit-hist-fic-23
level: LIT-HIST-FIC
sequence: 23
slug: natalena-koroleva-lehendy
version: '2.0'
title: 'Наталена Королева: Легенди старокиївські'
subtitle: An aristocratic, European, Catholic lens on early Ukrainian history
focus: literature
pedagogy: Seminar
phase: HISTFIC.1
word_target: 5000
objectives:
- Проаналізувати «Легенди старокиївські» як унікальний приклад аристократичної історичної прози
- Дослідити європейський та католицький погляд Наталени Королевої на давньоукраїнську історію
- Зрозуміти контраст між елітарним та популістським підходами до національного минулого
sources:
- name: Наталена Королева — проза
  url: https://www.ukrlib.com.ua/
  type: primary
  notes: Основне джерело
content_outline:
- section: Вступ та культурний контекст
  points:
  - Наталена Королева (1888–1966) — іспанська аристократка, що обрала Україну
  - Біографія — Барселона, Прага, еміграція, латинський обряд
  - Унікальність позиції — «зовнішній погляд зсередини»
  words: 850
- section: '«Легенди старокиївські»: аналіз збірки'
  points:
  - Сюжети — княжий Київ, хрещення, побут давньої Русі-України
  - Структура легенди як жанру — між історією та притчею
  - Образ Київської Русі через католицьку оптику — діалог цивілізацій
  words: 900
- section: Аристократична проза та жіноче письмо
  points:
  - Стильова вишуканість та інтелектуальна елегантність
  - Королева як жіночий голос в чоловічому жанрі історичної прози
  - Порівняння з іншими еміграційними авторками (Докія Гуменна)
  words: 850
- section: Мова, стиль та поетика
  points:
  - Архаїзована, стилізована мова — наближення до літописного регістру
  - Орнаментальність прози — вплив модернізму
  - Латинська та західноєвропейська інтертекстуальність
  words: 800
- section: Деколонізаційний вимір
  points:
  - Альтернатива популістському та народницькому обрамленню історії
  - Київська Русь як частина європейської цивілізації — проти «русского мира»
  - Еміграційна література як збереження забороненого погляду
  words: 800
- section: Підсумок та рецепція
  points:
  - Повернення Королевої в український літературний простір після 1991
  - Актуальність європейського погляду на українську історію
  - Питання для дискусії
  words: 800
vocabulary_hints:
  required:
  - легенда (legend)
  - аристократизм (aristocratism)
  - літописний (chronicle-like)
  - еміграція (emigration)
  recommended:
  - орнаментальність (ornamentalism)
  - Русь-Україна (Rus-Ukraine)
  - інтертекстуальність (intertextuality)
activity_hints:
- type: reading
  focus: Аналіз легенд про княжий Київ — порівняння оптики Королевої з літописною традицією
  source: UkrLib
  items: 5+
- type: essay-response
  focus: Аристократична vs народницька модель національної історії
  output: Аналітичне есе
- type: critical-analysis
  focus: Порівняння Королевої та Загребельного — два погляди на Київську Русь
connects_to:
- zahrebelny-death-in-kyiv
- zahrebelny-dyvo
- lepkyi-mazepa
persona:
  voice: Senior Philologist & Critic
  role: Chronicler of the Kyivan Court
module_type: literature
immersion: 100% Ukrainian

```

---

## Downstream Audit Gates (know these BEFORE you start)

Phase B content must pass these gates — plan your research accordingly:
- **Word count**: minimum **4000** words
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Soviet tropes
- **Engagement callouts**: map 6+ hooks to specific sections during research
- **Duplicate headers**: ensure outline section names don't share keywords

---

## PART 1: Deep Research

Research **Наталена Королева: Легенди старокиївські** for the **lit-hist-fic** track. Produce structured research notes that will drive content writing in Phase B.

### Your RAG Tools

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

### Research Workflow (minimize tool round-trips)

> **Performance rule**: Each tool call forces context re-processing. Batch your calls. Do NOT add narration between tool calls ("I will now search...") — output ONLY the tool call block. Fewer turns = faster completion.

**Batch 1 — Initial sweep (call ALL of these in ONE turn):**
- `query_wikipedia(query="Наталена Королева: Легенди старокиївські", mode="extract")` — factual backbone
- `search_literary(query="Наталена Королева: Легенди старокиївські")` — primary source excerpts
- `verify_words(words=[...])` — check vocabulary_hints from plan

**Batch 2 — Targeted follow-up (1-2 calls MAX):**
Based on Batch 1 results, fill gaps with ONE of:
- `search_literary` with a different query if primary quotes are missing
- `query_wikipedia` for a related article if key context is missing
- Skip this batch entirely if Batch 1 covered everything

**That's it. 2 batches, not 4 sequential steps.** Quality comes from thinking, not from more tool calls.

### Research Requirements

1. **Sources**: Minimum **3 distinct sources** — at least 1 from Wikipedia AND at least 1 from `search_literary` (RAG). Russian-language sources are PROHIBITED. Every factual claim must be traceable to a cited source.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find **3+** quotable primary source excerpts using `search_literary`. Use guillemet quotes «...» for Ukrainian text. If `search_literary` returns relevant chunks, extract and attribute them properly. Mark unverified quotes as `[needs verification]`.
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

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

===RESEARCH_START===

# Дослідження: Наталена Королева: Легенди старокиївські

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Наталена Королева: Легенди старокиївські"
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
