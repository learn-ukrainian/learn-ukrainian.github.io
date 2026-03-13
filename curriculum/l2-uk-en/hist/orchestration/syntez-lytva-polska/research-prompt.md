# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-040
level: HIST
sequence: 40
slug: syntez-lytva-polska
version: '2.0'
title: 'Синтез: Литовсько-польська доба'
subtitle: Узагальнення литовсько-польського періоду в історії України
focus: history
pedagogy: CBI
phase: HIST.4
word_target: 5000
objectives:
- Синтезувати знання з модулів про ВКЛ і Річ Посполиту
- Аналізувати причинно-наслідкові зв'язки литовсько-польської доби
- Формулювати аргументовані висновки про цей період
content_outline:
- section: Вступ
  points:
  - Литовсько-польська доба — 300 років української історії (1340-1648)
  - 'Три ключові теми: державність, суспільство, ідентичність'
  - Зв'язок з Хмельниччиною як результатом цього періоду
  words: 450
- section: Первинні джерела
  points:
  - Історичні джерела литовсько-польської доби
  words: 450
- section: Деколонізаційний погляд
  points:
  - Критичний аналіз імперських наративів
  words: 450
- section: Читання
  points:
  - Історіографічні підходи до литовсько-польської доби
  words: 450
- section: 'Хронологія: Литовсько-польська доба'
  points:
  - Ключові дати від 1340 до 1648 року
  - Хронологічне завдання — 10+ подій
  - Причинно-наслідкові ланцюги
  words: 450
- section: 'Огляд термінів: Литовсько-польська доба'
  points:
  - Політична лексика — шляхта, магнат, воєводство
  - Релігійна лексика — унія, братство, митрополит
  - Соціальна лексика — кріпак, посполитий, фільварок
  words: 450
- section: Зв'язок із сьогоденням
  points:
  - Спадщина литовсько-польської доби в сучасній Україні
  - Україно-польські стосунки сьогодні
  words: 450
- section: Підсумок
  points:
  - Загальна оцінка епохи
  - Ключові висновки епохи
  words: 450
- section: Модулі цієї епохи
  points:
  - Список модулів цього періоду
  words: 450
- section: Що далі?
  points:
  - Перехід до козацької доби
  words: 450
- section: Потрібно більше практики?
  points:
  - Посилання на додаткові ресурси
  words: 500
vocabulary_hints:
  required:
  - історія (history)
  - держава (state)
  - народ (people)
  - влада (power)
  - період (period)
  - подія (event)
  - джерело (source)
  - спадщина (heritage)
  recommended:
  - аналіз (analysis)
  - контекст (context)
  - вплив (influence)
  - наслідки (consequences)
activity_hints:
- type: reading
  focus: Первинні джерела
  items: 4
- type: essay-response
  focus: Критичний аналіз
- type: critical-analysis
  focus: Аналіз причинно-наслідкових зв'язків між подіями
  items: 3
- type: critical-analysis
  focus: Критична оцінка історичних тверджень та міфів
  items: 5
persona:
  voice: Senior Professor of History
  role: Visiting Professor from Kyiv-Mohyla Academy
grammar:
- Analytical writing
- Cause-effect structures
- Historical argumentation
prerequisites:
- liudy-ricchi-pospolytoi
connects_to:
- kozatstvo-vytoky

```

---

## PART 1: Deep Research

Research **Синтез: Литовсько-польська доба** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

### Your RAG Tools (USE THEM)

You have access to Ukrainian language tools via MCP. **Use them during research.**

| Tool | When to use | Example |
|------|-------------|---------|
| `query_wikipedia` mode=`extract` | Get full article text (50K chars) for deep research | `query_wikipedia("Богдан Хмельницький", mode="extract")` |
| `query_wikipedia` mode=`sections` | See article structure before diving in | `query_wikipedia("Запорізька Січ", mode="sections")` |
| `query_wikipedia` mode=`section` | Read a specific section by index | `query_wikipedia("Запорізька Січ", mode="section", section=3)` |
| `query_wikipedia` mode=`search` | Find the right article title | `query_wikipedia("Переяславська рада", mode="search")` |
| `search_literary` | Find primary source excerpts (chronicles, poetry, legal texts) | `search_literary("Хмельницький", genre="chronicle")` |
| `verify_word` / `verify_words` | Check Ukrainian words exist in VESUM dictionary | `verify_words(["гетьман", "козацтво"])` |
| `query_grac` | Check word frequency in Ukrainian corpus | `query_grac("упокорення", mode="frequency")` |

**Workflow**: Search Wikipedia FIRST for factual foundation → search literary RAG for primary quotes → verify vocabulary with VESUM.

### Research Requirements

1. **Sources**: Use `query_wikipedia` (mode=`extract`) for Ukrainian Wikipedia articles. Also consult history.org.ua, litopys.org.ua. Use `search_literary` for primary source excerpts. Russian-language sources are PROHIBITED.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find 2+ quotable primary source excerpts (original Ukrainian text preferred).
4. **Engagement Hooks**: Identify 6+ engagement hooks mapped to specific content sections:
   - `[!myth-buster]` — Decolonization: correct imperial/Soviet myths
   - `[!history-bite]` — Surprising or lesser-known facts
   - `[!context]` — Broader historical/cultural context
   - `[!quote]` — Primary source citations
   - `[!decolonization]` — Ukraine-centric reframing
   - `[!culture]` — Cultural significance
5. **Decolonization Angle**: Identify how this topic has been distorted by imperial/Soviet historiography and what the Ukrainian-centric framing should be.
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
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Engagement callouts**: map 6+ hooks to specific sections during research (not as afterthought patches)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Синтез: Литовсько-польська доба

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Синтез: Литовсько-польська доба"
vital_status: "deceased" # or "alive"
dates:
  birth: "YYYY-MM-DD"    # or approximate: "~YYYY"
  death: "YYYY-MM-DD"    # omit if alive
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
- Section "{section_name}": [!hook_type] — description
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
```

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Research + Meta (Seminar)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | SOURCE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the plan's content_outline
- Do NOT use Russian-language sources
- Do NOT fabricate quotes or dates — if unsure, mark as "[needs verification]"
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
