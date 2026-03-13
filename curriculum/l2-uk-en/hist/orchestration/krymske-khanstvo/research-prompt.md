# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-027
level: HIST
sequence: 27
slug: krymske-khanstvo
version: '2.0'
title: 'Кримське ханство: Золотоординська спадщина'
subtitle: Виникнення та державність Гіреїв
focus: history
pedagogy: CBI
phase: B2.3c [Українська історія]
word_target: 5000
objectives:
- Учень може описати процес виникнення Кримського ханства
- Учень розуміє державний устрій та роль роду Гіреїв
- Учень може аналізувати відносини між ханством та українськими землями
content_outline:
- section: Вступ
  points:
  - Кримське ханство як ключовий гравець регіону — спадкоємець Улусу Джучі (Золотої Орди) у геополітичному трикутнику Крим-Стамбул-Москва
  - 'Складні відносини з українськими землями — [!myth-buster] спростування міфу про «одвічну ворожнечу»: історія динамічних
    змін від набігів до військових союзів'
  words: 700
- section: Читання
  points:
  - Народження ханства (1441-1478) — проголошення незалежності Хаджі I Ґераєм (1441) та перехід під османський протекторат
    за Менґлі I Ґерая (1478)
  - 'Державний устрій Гіреїв — баланс влади: хан як верховний правитель, обмежений Курултаєм та чотирма родами карачі-беїв
    (Ширін, Барин, Аргин, Кипчак)'
  - Ясир — трагедія степового кордону — роль Кафи (Кефе) як невільничого ринку та економічний вимір работоргівлі (5-15% бюджету)
  words: 700
- section: Первинні джерела
  points:
  - Європейські свідчення про Крим — [!quote] Гійом Левассер де Боплан про витривалість татар та їхню військову організацію
    (1650)
  - Опис Кафи та невільничого ринку — [!quote] контрастний опис розкоші Бахчисарайського палацу Евлією Челебі (1666) як свідчення
    високої культури
  words: 700
- section: Деколонізаційний погляд
  points:
  - 'Кримсько-козацькі союзи проти Польщі — [!decolonization] замовчувані радянською історіографією угоди: Михайло Дорошенко
    (1624) та Богдан Хмельницький (1648)'
  - Культурні зв'язки та запозичення — взаємовплив у побуті (шаровари, жупани), мові (майдан, кіш, тютюн) та зброї
  - Крим як частина української історії — Qırımlı як корінний народ, що сформувався на півострові, а не «прийшлі варвари»
  words: 700
- section: 'Економіка: Сади, сіль та каравани'
  points:
  - Економічна основа ханства — експорт солі (Сиваш) та шкір, розвинене садівництво та ремісництво (ювелірна справа, сап'ян)
  words: 700
- section: Підсумок — Спадщина для сучасності
  points:
  - Анексія 1783 року та депортація 1944-го — [!legacy] руйнування державності Російською імперією та сталінський геноцид
    (Сюрґюн)
  - Кримські татари як корінний народ — сучасний статус Qırımlı, закон України 2021 року та опір окупації з 2014 року
  words: 700
- section: Потрібно більше практики?
  points:
  - Додаткові ресурси
  words: 800
vocabulary_hints:
  required:
  - хан (khan) — титул монарха, походить від тюрко-монгольської традиції
  - ясир (captives/slaves) — бранці, захоплені під час набігів; економічна складова
  - курултай (assembly) — загальні збори знаті для вирішення державних питань
  - спадщина (legacy/heritage) — Золотоординська спадщина; культурний спадок
  - союз (alliance) — військово-політичний союз; укласти угоду
  - анексія (annexation) — насильницьке приєднання (1783)
  - депортація (deportation) — примусове виселення народу (1944)
  - беї (beys) — титул знаті, голови родів (карачі-беї)
  recommended:
  - протекторат (protectorate) — форма залежності від Османської імперії (з 1478)
  - династія (dynasty) — династія Ґераїв (Чингізидів)
  - корінний (indigenous) — корінний народ Криму
  - набіг (raid) — військова операція з метою захоплення здобичі
  - степ (steppe) — Половецький степ (Дешт-і-Кипчак)
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
  role: Khan's Ambassador
grammar:
- Historical narrative style
- Descriptive constructions
prerequisites:
- kinets-halytsko-volyni
connects_to:
- syntez-dvokniazivstvo

```

---

## PART 1: Deep Research

Research **Кримське ханство: Золотоординська спадщина** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Кримське ханство: Золотоординська спадщина

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Кримське ханство: Золотоординська спадщина"
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
