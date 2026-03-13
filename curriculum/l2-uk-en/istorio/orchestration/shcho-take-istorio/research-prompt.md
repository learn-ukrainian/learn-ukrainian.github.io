# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: istorio-001
level: ISTORIO
sequence: 1
slug: shcho-take-istorio
version: '1.0'
title: Що таке історіографія?
focus: history
pedagogy: seminar
word_target: 5000
objectives:
- Analyze the difference between history and historiography
- Evaluate the impact of bias and narrative on historical writing
sources:
- name: Історіографія України (Вікіпедія)
  url: https://uk.wikipedia.org/wiki/Історіографія_України
  type: reference
  notes: Overview of Ukrainian historiographical tradition
- name: Грушевський — Історія України-Руси (вступ)
  url: https://litopys.org.ua/hrushukr/ihu.htm
  type: primary
  notes: Hrushevsky's methodological introduction
- name: What is Historiography? (academic intro)
  url: https://www.historians.org/teaching-and-learning/teaching-resources-for-historians/teaching-and-learning-in-the-digital-age/the-history-of-the-americas/what-is-historiography
  type: reference
  notes: English reference for conceptual framework
content_outline:
- section: Вступ — Історія vs. Історіографія
  points:
  - Що таке історія? Що таке історіографія?
  - Різниця між подіями та інтерпретацією подій
  - Чому один і той самий факт описують по-різному?
  - Приклад — Переяславська рада 1654 (3 версії)
  words: 700
- section: Ключові поняття історіографії
  points:
  - Наратив (narrative) — як розповідь формує розуміння
  - Первинні джерела vs. вторинні джерела
  - Інтерпретація vs. факт
  - Упередження (bias) та перспектива автора
  - Контекст створення тексту
  words: 700
- section: Хто пише історію?
  points:
  - Літописці (Chronicle writers) — середньовічна традиція
  - Академічні історики — університетська традиція
  - Держава як автор історії — офіційні наративи
  - Еміграція та діаспора — альтернативні голоси
  - Сучасність — public history, Wikipedia, соцмережі
  words: 700
- section: Українська історіографічна традиція — огляд
  points:
  - Від літописів до Грушевського
  - Чому українська історія довго писалася як «частина російської»
  - Революція Грушевського — окрема нація, окрема історія
  - Радянські деформації
  - Відродження після 1991
  words: 700
- section: Чому це важливо для вас?
  points:
  - Критичне читання — не вірити одному джерелу
  - Розпізнавання пропаганди
  - Формування власної позиції на основі доказів
  - Україна як об'єкт інформаційної війни
  words: 700
- section: Практичне застосування
  points:
  - Як читати історичний текст критично?
  - 5 питань до кожного джерела (хто? коли? для кого? чому? що опущено?)
  - Приклад аналізу — радянський підручник vs. сучасний
  words: 700
- section: Підсумок та перехід
  points:
  - Ключові терміни модуля
  - Що далі — українська історіографічна традиція детально
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
- історіографія
- наратив
- інтерпретація
- первинне джерело
- вторинне джерело
- упередження
- контекст
- перспектива
- критичний аналіз
- методологія
- літопис
- деконструкція
- переосмислення
- офіційний наратив
- альтернативна історія
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
  focus: Read two descriptions of Pereiaslav 1654 (Ukrainian vs Russian textbook)
- type: critical-analysis
  focus: Apply 5 questions to a Soviet-era text about Ukrainian history
- type: critical-analysis
  focus: Analyze methodology and apply source criticism to historiographical debates
- type: essay-response
  focus: Чому важливо знати, хто написав історію?
persona:
  voice: Academic Historiographer
  role: Historical Methodologist
connects_to:
- ukrainska-istoriohrafichna-tradytsiia

```

---

## PART 1: Deep Research

Research **Що таке історіографія?** for the **istorio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Що таке історіографія?

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Що таке історіографія?"
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
