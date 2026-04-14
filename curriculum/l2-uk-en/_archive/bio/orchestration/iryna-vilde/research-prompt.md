# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: bio-177
level: BIO
sequence: 177
slug: iryna-vilde
version: '2.0'
title: 'Ірина Вільде: Метелик на шпильках'
focus: biography
pedagogy: immersion
phase: BIO
word_target: 5000
objectives:
- Проаналізувати творчий шлях Ірини Вільде як першої жінки-лауреатки Шевченківської премії
- Дослідити стратегії виживання галицької інтелігенції під чотирма режимами
- Оцінити внесок Вільде у розвиток української жіночої прози та феміністичної традиції
sources:
- name: Ірина Вільде (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Ірина_Вільде
  type: primary
  notes: Біографія, творчість, громадянська позиція, Шевченківська премія
- name: Жінки в ОУН та УПА
  url: https://uk.wikipedia.org/wiki/Жінки_в_ОУН_та_УПА
  type: reference
  notes: Контекст жінок у національному русі
content_outline:
- section: Вступ — Дика і нескорена
  points:
  - Псевдонім «Вільде» — від слова «дикий», вільний дух серед неволі
  - Перша жінка-лауреатка Шевченківської премії (1965)
  - Авторка найбільшого роману серед українських письменниць
  - Жінка, яка пережила чотири режими й жодному не скорилася
  words: 850
- section: Буковинське дитинство та станиславівська юність (1907-1930)
  points:
  - Народження в Чернівцях у родині вчителя-письменника Дмитра Макогона
  - Брати в УВО та дивізії «Галичина» — національна родина
  - Румунська окупація Буковини, переїзд до Станиславова
  - Гімназія, Пласт, перші оповідання під впливом неоромантизму
  - Львівський університет, пацифікації, вимушене покидання навчання
  words: 850
- section: Становлення письменниці (1930-1939)
  points:
  - Коломия, редакція «Жіночої долі» та «Світу молоді»
  - «Метелики на шпильках» — проза про дівчаче дорослішання як літературна сенсація
  - Премія імені Франка — Михайло Рудницький називає її талант «європейським»
  - Дружба з Богданом-Ігорем Антоничем, його рецензія на ранні твори
  - Початок роману «Сестри Річинські» — справа чверті століття
  words: 850
- section: Війна та виживання (1939-1944)
  points:
  - Прийняття до Спілки письменників УРСР (1940)
  - Німецька окупація — переховування в Микуличині, чоловік у мережі ОУН
  - Контакти з партизанським загоном Ковпака
  - Донос місцевих поляків, арешт чоловіка, розстріл гітлерівцями
  - Втеча з дітьми, прихисток у родичів, прихід «других совітів»
  words: 850
- section: Радянський Львів — між конформізмом та опором (1944-1965)
  points:
  - Спецкореспондентка «Правды Украины», депутатство завдяки Ковпаку
  - Гоніння 1949-1951 за «націоналізм» разом із Рудницьким
  - Шлюб із полковником КДБ Дроб'язком — захист чи компроміс?
  - «Сестри Річинські» — вершина творчості, сімейний роман-хроніка Галичини
  - Шевченківська премія 1965 — тріумф галицької жіночої прози
  words: 850
- section: Нанашка шістдесятників та спадщина (1962-1982)
  points:
  - Літературні салони, маскаради, запрошення Дзюби, Драча, Вінграновського до Львова
  - Захист дисидента Богдана Гориня — лист до суду
  - Очолення Львівської організації Спілки письменників, традиція «Останньої сторінки»
  - Особисті трагедії — хвороба, доля синів Яреми та Максима
  - Похорон на Личаківському цвинтарі, премія імені Ірини Вільде
  - Деколонізаційне значення: галицька жінка створила літературу світового рівня
  words: 750
vocabulary_hints:
  required:
  - письменниця (female writer)
  - феміністичний (feminist)
  - Шевченківська премія (Shevchenko Prize)
  - пацифікація (pacification)
  - окупація (occupation)
  - дисидент (dissident)
  - конформізм (conformism)
  - неоромантизм (neo-romanticism)
  - психологізм (psychologism)
  - спадщина (legacy)
  recommended:
  - '«Метелики на шпильках» (Butterflies on Pins)'
  - '«Сестри Річинські» (The Richynski Sisters)'
  - Спілка письменників (Writers'' Union)
  - шістдесятники (the Sixties generation)
  - гоніння (persecution)
activity_hints:
- type: reading
  focus: Жіноча проза та національна ідентичність
  source: Біографія та фрагменти творчості
  items: 3 passages
- type: essay-response
  focus: Як Вільде поєднувала виживання в радянській системі з підтримкою опозиції?
  output: Критичне есе
connects_to:
- bio-72 (Леся Українка)
- bio-42 (Марко Вовчок)
- bio-123 (Богдан-Ігор Антонич)
- bio-135 (Євген Сверстюк)
prerequisites:
- bio-54 (Іван Франко)
persona:
  voice: Senior Historian
  role: Women's Literature Specialist
module_type: biography
immersion: 100% Ukrainian

```

---

## Downstream Audit Gates (know these BEFORE you start)

Phase B content must pass these gates — plan your research accordingly:
- **Word count**: minimum **5000** words
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Soviet tropes
- **Engagement callouts**: map 6+ hooks to specific sections during research
- **Duplicate headers**: ensure outline section names don't share keywords

---

## PART 1: Deep Research

Research **Ірина Вільде: Метелик на шпильках** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

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
- `query_wikipedia(query="Ірина Вільде: Метелик на шпильках", mode="extract")` — factual backbone
- `search_literary(query="Ірина Вільде: Метелик на шпильках")` — primary source excerpts
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

# Дослідження: Ірина Вільде: Метелик на шпильках

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Ірина Вільде: Метелик на шпильках"
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
