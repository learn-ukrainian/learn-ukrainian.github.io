# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-026
level: HIST
sequence: 26
slug: kinets-halytsko-volyni
version: '2.0'
title: Занепад Галицько-Волинської держави
subtitle: Трагедія 1340 року та боротьба за спадщину
focus: history
pedagogy: CBI
phase: B2.3a [Українська історія]
word_target: 5000
objectives:
- Учень може пояснити причини занепаду держави Романовичів
- Учень розуміє наслідки отруєння Юрія ІІ
- Учень може аналізувати боротьбу сусідніх держав за руську спадщину
content_outline:
- section: Вступ
  points:
  - Криза династії Романовичів — смерть Андрія та Лева ІІ (1323), ймовірно у битві проти ординців, обриває пряму чоловічу
    лінію
  - 1340 рік як переломний момент — початок 50-річної війни за спадщину та «Гри престолів» Центральної Європи; [!context]
  words: 850
- section: Читання
  points:
  - Останні Романовичі (1264-1323) — спроби балансування між Литвою та Ордою
  - Юрій ІІ Болеслав — князь-чужинець — син мазовецького князя Тройдена, курс на «вестернізацію» (німецькі колоністи, католицтво)
    та конфлікт з боярами; [!history-bite]
  - Боротьба за спадщину — правління боярської олігархії на чолі з Дмитром Дедьком (1340–1344) та отруєння Юрія ІІ у Володимирі
  - Польща vs Литва vs Угорщина — напад Казимира ІІІ на Львів, пограбування скарбниці та Вишеградська угода 1339 року
  words: 850
- section: Первинні джерела
  points:
  - Галицько-Волинський літопис обривається 1292 роком — дослідження подій «очима ворогів» через відсутність власної хроніки
  - Польські хроніки про події 1340 року — цитата Яна Длугоша про «величезні скарби»; печатка Юрія ІІ з латинським титулом
    «Dux Russiae»; [!source]
  words: 850
- section: Деколонізаційний погляд
  points:
  - Чому занепад держави не означав кінець народу — спростування міфу про «мирне успадкування» Русі Казимиром (це була збройна
    агресія); [!myth-buster]
  - Галицьке боярство під польською владою — трансформація суверенної «Regnum Russiae» в провінційну «Ruś Czerwona»
  words: 850
- section: Підсумок — Уроки державності
  points:
  - Причини краху — внутрішні чвари еліти (бояр), що ставлять власні інтереси вище державних; [!reflection]
  - Паралелі з іншими періодами історії — геополітична пастка між католицьким Заходом та Литвою/Ордою
  words: 850
- section: Потрібно більше практики?
  points:
  - Додаткові ресурси
  words: 750
vocabulary_hints:
  required:
  - історія (history) — трагічна історія, переписувати історію
  - держава (state) — занепад держави, розбудова держави
  - народ (people) — воля народу, історична пам'ять народу
  - влада (power) — вакуум влади, захоплення влади, боротьба за владу
  - період (period) — переломний період, період руїни
  - подія (event) — трагічні події 1340 року, хід подій
  - джерело (source) — першоджерело, польські джерела, надійне джерело
  - спадщина (heritage) — боротьба за спадщину, культурна спадщина
  recommended:
  - аналіз (analysis) — критичний аналіз, аналіз причин
  - контекст (context) — історичний контекст, геополітичний контекст
  - вплив (influence) — західний вплив, польський вплив
  - наслідки (consequences) — катастрофічні наслідки, довготривалі наслідки
  - отруєння (poisoning) — отруєння князя, таємне отруєння
  - загарбання (annexation/seizure) — польське загарбання, збройне загарбання
  - олігархія (oligarchy) — боярська олігархія, правління олігархії
  - титул (title) — князівський титул, королівський титул
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
  role: Last Boyar
grammar:
- Expressing cause and effect
- Tragic narrative style
prerequisites:
- boiare-i-shliakhta
connects_to:
- krymske-khanstvo

```

---

## PART 1: Deep Research

Research **Занепад Галицько-Волинської держави** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Занепад Галицько-Волинської держави

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Занепад Галицько-Волинської держави"
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
