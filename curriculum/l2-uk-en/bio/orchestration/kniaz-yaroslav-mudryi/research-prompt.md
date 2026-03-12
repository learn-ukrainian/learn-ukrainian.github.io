# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: bio-004
level: BIO
sequence: 4
slug: kniaz-yaroslav-mudryi
version: '2.0'
title: 'Князь Ярослав Мудрий: Законодавець'
focus: biography
pedagogy: seminar
phase: BIO
word_target: 5000
objectives:
- Analyze the impact of Ruska Pravda on medieval society.
- Discuss the strategic importance of dynastic marriages.
- Evaluate the cultural achievements of the "Golden Age".
sources:
- name: Ярослав Мудрий (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Ярослав_Мудрий
  type: primary
  notes: Biography, Ruska Pravda, cultural achievements
- name: Руська правда (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Руська_правда
  type: primary
  notes: Legal code details and significance
- name: Софійський собор (Wikipedia UA)
  url: https://uk.wikipedia.org/wiki/Софійський_собор_(Київ)
  type: reference
  notes: Architectural legacy
content_outline:
- section: Вступ — Будівничий держави
  points:
  - Ярослав як законодавець і культуртрегер
  - Порівняння з європейськими монархами
  - Значення його правління для Русі
  words: 550
- section: Життєпис
  points:
  - Основні етапи життя князя
  words: 550
- section: Шлях до влади
  points:
  - Молодість у Ростові та Новгороді
  - Конфлікт із батьком Володимиром
  - Усобиця після смерті батька
  - Боротьба зі Святополком Окаянним
  words: 550
- section: Руська правда
  points:
  - Перший писаний збірник законів
  - Структура та основні норми
  - Віра (штраф за вбивство)
  - Порівняння з європейським правом
  words: 550
- section: Культурний розквіт
  points:
  - Будівництво Софійського собору
  - Золоті ворота
  - Заснування бібліотеки та скрипторію
  - Переклади та освіта
  words: 550
- section: 'Останні роки: Династична дипломатія'
  points:
  - Шлюби дітей з європейськими монархами
  - Анна — королева Франції
  - Міжнародний престиж Києва
  - Русь як частина європейської спільноти
  words: 550
- section: Внесок у розбудову держави
  points:
  - Формування правового поля
  - Архітектурний канон Києва
  words: 550
- section: Спадщина та канонізація
  points:
  - Завіт синам
  - Смерть та поховання
  - Образ у пізнішій культурі
  words: 550
- section: Підсумок
  points:
  - Квінтесенція правління Ярослава Мудрого
  words: 600
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: reading
  focus: Excerpts from Ruska Pravda
  source: Original text (adapted)
  items: 3 passages
- type: essay-response
  focus: Compare Yaroslav's lawgiving with Justinian or Charlemagne
  output: Comparative analysis
- type: critical-analysis
  focus: Evaluate the title "Mudryi" (The Wise)
  output: Argument with evidence
connects_to:
- bio-05 (Anna Yaroslavna - daughter)
- 'bio-09 (Михайло Чернігівський: Князь-мученик)'
- bio-14 (Pylyp Orlyk - later constitutional tradition)
prerequisites:
- bio-03 (Volodymyr Velykyi - father)
- Understanding of medieval European context
persona:
  voice: Senior Biographer
  role: Lawgiver
grammar:
- Legal terminology (Ruska Pravda)
- Diplomatic register
module_type: biography
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Князь Ярослав Мудрий: Законодавець** for the **bio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Князь Ярослав Мудрий: Законодавець

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Князь Ярослав Мудрий: Законодавець"
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
