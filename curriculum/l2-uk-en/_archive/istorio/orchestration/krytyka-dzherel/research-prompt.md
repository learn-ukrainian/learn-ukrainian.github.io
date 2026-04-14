# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: istorio-009
level: ISTORIO
sequence: 9
slug: krytyka-dzherel
version: '1.0'
title: 'Критика джерел: Принципи та практика'
focus: history
pedagogy: seminar
word_target: 5000
objectives:
- 'Analyze the causes and consequences of критика джерел: принципи та практика'
- Evaluate the historical significance of чому джерела брешуть
- Trace the development of особливості українських джерел
sources:
- name: Джерелознавство (Вікіпедія)
  url: https://uk.wikipedia.org/wiki/Джерелознавство
  type: reference
  notes: Source studies overview
- name: Історичне джерело
  url: https://uk.wikipedia.org/wiki/Історичне_джерело
  type: reference
  notes: Types of historical sources
- name: Критика джерел
  url: https://uk.wikipedia.org/wiki/Критика_джерел
  type: reference
  notes: Source criticism methods
- name: Леопольд фон Ранке
  url: https://uk.wikipedia.org/wiki/Ранке_Леопольд_фон
  type: reference
  notes: Founder of modern source criticism
content_outline:
- section: Вступ — Чому джерела брешуть
  points:
  - Кожне джерело має автора з інтересами
  - Історик як детектив
  - Від наївного читання до критичного
  - Мета модуля — практичні навички
  words: 700
- section: Типи історичних джерел
  points:
  - Первинні — документи, листи, хроніки
  - Вторинні — дослідження, підручники
  - Матеріальні — артефакти, археологія
  - Усні — свідчення, інтерв'ю
  - Візуальні — фото, карти, фільми
  - Цифрові — нові виклики
  words: 700
- section: Зовнішня критика (автентичність)
  points:
  - Чи справжній документ?
  - Датування — коли створено
  - Авторство — хто написав
  - Походження — звідки потрапив до нас
  - Збереженість — що могло змінитися
  - Приклад — «Слово о полку Ігоревім» (дебати)
  words: 700
- section: Внутрішня критика (достовірність)
  points:
  - Чи правду каже автор?
  - Упередження автора — політичне, релігійне, особисте
  - Мета тексту — для кого писав
  - Що опущено — аналіз мовчання
  - Порівняння з іншими джерелами
  - Внутрішня логіка тексту
  - Приклад — козацькі літописи
  words: 700
- section: П'ять ключових питань до джерела
  points:
  - ХТО? — авторство і позиція
  - КОЛИ? — датування і контекст
  - ДЛЯ КОГО? — аудиторія і мета
  - ЧОМУ? — інтереси автора
  - ЩО ОПУЩЕНО? — аналіз мовчання
  - Практичний чекліст
  words: 700
- section: Практикум — аналіз джерела
  points:
  - Вибране джерело (Universal Хмельницького або інше)
  - Крок за кроком — застосування методу
  - Що ми дізналися
  - Що залишається невідомим
  words: 700
- section: Особливості українських джерел
  points:
  - Знищення архівів — що втрачено
  - Радянська фільтрація — що залишилося
  - Діаспорні архіви — альтернатива
  - Цифровізація — нові можливості
  words: 800
vocabulary_hints:
  required:
  - історія (history)
  - подія (event)
  - джерело (source)
  - аналіз (analysis)
  recommended:
  - контекст (context)
  - інтерпретація (interpretation)
  - наслідки (consequences)
vocabulary:
- джерелознавство
- первинне джерело
- вторинне джерело
- автентичність
- достовірність
- зовнішня критика
- внутрішня критика
- упередження
- контекст
- верифікація
- палеографія
- дипломатика
- провенанс
- інтерполяція
- редакція
activity_hints:
- type: reading
  focus: Первинні джерела
  items: 4
- type: essay-response
  focus: Критичний аналіз
- type: true-false
  focus: Факти та інтерпретації
  items: 10
activities:
- type: reading
  focus: A short primary source (e.g., Khmelnytsky's Universal or letter)
- type: critical-analysis
  focus: Apply 5 questions to the provided source
- type: comparative-study
  focus: Compare two sources describing the same event — what differs?
- type: reading
  focus: Evaluate a Wikipedia article as a source — strengths and weaknesses
- type: essay-response
  focus: Чи може історик бути об'єктивним?
persona:
  voice: Academic Historiographer
  role: Forensic Source Critic
prerequisites:
- metodolohiia-dekolonizatsii
connects_to:
- istorychna-pamiat-i-polityka

```

---

## PART 1: Deep Research

Research **Критика джерел: Принципи та практика** for the **istorio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Критика джерел: Принципи та практика

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Критика джерел: Принципи та практика"
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
