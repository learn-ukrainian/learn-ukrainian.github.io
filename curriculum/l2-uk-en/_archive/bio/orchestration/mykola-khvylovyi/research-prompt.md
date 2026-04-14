# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: bio-100
level: BIO
sequence: 100
slug: mykola-khvylovyi
version: '2.0'
title: 'Микола Хвильовий: Геть від Москви!'
focus: biography
phase: BIO
word_target: 5000
objectives:
- 'Analyze the life and legacy of микола хвильовий: геть від москви!'
- Evaluate the contributions of бунтар, що обрав смерть
- Trace the career and influence of спадщина та реабілітація
sources:
- name: Микола Хвильовий (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Микола_Хвильовий
  type: primary
  notes: Біографія, творчість, літературна дискусія
- name: Літературна дискусія 1925-1928
  url: https://uk.wikipedia.org/wiki/Літературна_дискусія_1925—1928_років
  type: reference
  notes: Контекст полеміки «Геть від Москви!»
- name: Розстріляне відродження
  url: https://uk.wikipedia.org/wiki/Розстріляне_відродження
  type: reference
  notes: Доля української інтелігенції 1920-30-х
content_outline:
- section: Вступ — Бунтар, що обрав смерть
  points:
  - Микола Хвильовий — найяскравіша постать Розстріляного відродження
  - Від комуніста до ідеолога «психологічної Європи»
  - Самогубство як останній акт спротиву
  words: 850
- section: Ранні роки та революція (1893-1921)
  points:
  - Народження на Харківщині (справжнє ім'я — Микола Фітільов)
  - Участь у революції та громадянській війні
  - Вступ до Комуністичної партії
  - Початок літературної діяльності
  words: 850
- section: Літературний злет (1921-1925)
  points:
  - Збірки «Сині етюди» та «Осінь»
  - Організація літературних об'єднань — ВАПЛІТЕ
  - Імпресіоністичний стиль та психологізм
  - Визнання як провідного прозаїка
  words: 850
- section: «Геть від Москви!» (1925-1928)
  points:
  - Літературна дискусія про шляхи української культури
  - Гасло «Геть від Москви!» — орієнтація на Європу
  - Концепція «азійського ренесансу»
  - Конфлікт з партійною лінією та примусове каяття
  words: 850
- section: Останні роки та самогубство (1928-1933)
  points:
  - Тиск влади та творча криза
  - Голодомор та знищення української інтелігенції
  - Самогубство 13 травня 1933 року
  - Передсмертний лист і його значення
  words: 850
- section: Спадщина та реабілітація
  points:
  - Заборона творів на десятиліття
  - Реабілітація у 1980-х роках
  - Вплив на сучасну українську літературу
  - Хвильовий як символ інтелектуального спротиву
  words: 750
vocabulary_hints:
  required:
  - Розстріляне відродження (Executed Renaissance)
  - орієнтація (orientation)
  - імпресіонізм (impressionism)
  - дискусія (discussion/debate)
  - самогубство (suicide)
  - каяття (repentance)
  - ренесанс (renaissance)
  - інтелігенція (intelligentsia)
  - спротив (resistance)
  - ідеологія (ideology)
  recommended:
  - авангард (avant-garde)
  - психологізм (psychologism)
  - модернізм (modernism)
  - тоталітаризм (totalitarianism)
  - цензура (censorship)
activity_hints:
- type: reading
  focus: Уривки з памфлетів та прози Хвильового
  source: Оригінальні твори
  items: 3 passages
- type: essay-response
  focus: Чому гасло «Геть від Москви!» актуальне сьогодні?
  output: Contemporary analysis
connects_to:
- bio-68-olena-teliha
- bio-77-vasyl-stus
prerequisites:
- bio-57-les-kurbas
persona:
  voice: Senior Biographer
  role: Pamphleteer
module_type: biography
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Микола Хвильовий: Геть від Москви!** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Микола Хвильовий: Геть від Москви!

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Микола Хвильовий: Геть від Москви!"
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
