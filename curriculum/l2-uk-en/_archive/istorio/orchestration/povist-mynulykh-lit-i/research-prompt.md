# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: istorio-011
level: ISTORIO
sequence: 11
slug: povist-mynulykh-lit-i
version: '1.0'
title: 'Повість минулих літ I: Структура та автори'
focus: history
pedagogy: seminar
word_target: 5000
objectives:
- 'Analyze the causes and consequences of повість минулих літ i: структура та автори'
- Evaluate the historical significance of найстаріший літопис русі
sources:
- name: Повість минулих літ (Вікіпедія)
  url: https://uk.wikipedia.org/wiki/Повість_минулих_літ
  type: reference
  notes: Overview of the chronicle
- name: Повість минулих літ (повний текст)
  url: https://litopys.org.ua/pvlyar/yar.htm
  type: primary
  notes: Full text of Laurentian redaction
- name: Нестор Літописець
  url: https://uk.wikipedia.org/wiki/Нестор_Літописець
  type: reference
  notes: Traditional attribution
content_outline:
- section: Вступ — Найстаріший літопис Русі
  points:
  - Що таке Повість минулих літ (ПМЛ)?
  - Чому це найважливіше джерело для ранньої історії?
  - Редакції — Лаврентіївська, Іпатіївська
  - Що ми розглянемо в цьому модулі
  words: 700
- section: Структура літопису
  points:
  - Вступна частина — «звідки пішла Руська земля»
  - Недатована частина — легенди, походження
  - Датована частина — від 852 року
  - Принцип погодного запису
  - Що включено і що пропущено
  words: 700
- section: Питання авторства
  points:
  - Нестор — традиційна атрибуція
  - Хто насправді писав? Кілька авторів
  - Шахматов — реконструкція шарів
  - Як визначити різних авторів?
  - Політичні замовники — князі та церква
  words: 700
- section: Редакції та рукописи
  points:
  - Лаврентіївський список (1377)
  - Іпатіївський список (XV ст.)
  - Радзивіллівський список (з мініатюрами)
  - Чим відрізняються редакції?
  - Що додано, що прибрано
  words: 700
- section: Мова літопису
  points:
  - Давньоруська як основа
  - Церковнослов'янські елементи
  - Як читати сьогодні — глосарій
  - Приклади з текстами
  words: 700
- section: Чому важлива критика джерела
  points:
  - ПМЛ — не об'єктивна історія
  - Легенди vs. історичні факти
  - Політична заангажованість
  - Як використовувати критично
  words: 700
- section: Підсумок
  points:
  - ПМЛ як фундамент історичної пам'яті
  - Підготовка до читання фрагментів
  - Зв'язок із наступним модулем
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
- літопис
- редакція
- рукопис
- атрибуція
- погодний запис
- компіляція
- давньоруський
- церковнослов'янський
- реконструкція
- шар / пласт
- палеографія
- кодекс
- автограф
- копіїст
- інтерполяція
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
  focus: Opening passage \"Откуда есть пошла Руская земля\" — modern translation
- type: critical-analysis
  focus: Who benefits from specific passages? Identify political purpose
- type: comparative-study
  focus: Compare Laurentian vs. Hypatian redaction on one event
- type: essay-response
  focus: Чи можна довіряти Повісті минулих літ як історичному джерелу?
persona:
  voice: Academic Historiographer
  role: Monastic Chronicler
prerequisites:
- istorychna-pamiat-i-polityka
connects_to:
- povist-mynulykh-lit-ii

```

---

## PART 1: Deep Research

Research **Повість минулих літ I: Структура та автори** for the **istorio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Повість минулих літ I: Структура та автори

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Повість минулих літ I: Структура та автори"
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
