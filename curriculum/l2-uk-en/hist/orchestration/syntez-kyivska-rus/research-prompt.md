# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-020
level: HIST
sequence: 20
slug: syntez-kyivska-rus
version: '2.0'
title: 'Синтез: Київська Русь — спадщина'
focus: history
pedagogy: CBI
phase: HIST.1 [Kyivan Rus]
word_target: 5000
objectives:
- Summarize the political and cultural development of Kyivan Rus
- Evaluate the legacy of Rus in modern Ukrainian identity
- Critically analyze conflicting historical claims to the Rus heritage
sources:
- name: Київська Русь (Вікіпедія)
  url: https://uk.wikipedia.org/wiki/Київська_Русь
  type: reference
  notes: Comprehensive overview for synthesis
- name: Спадщина Київської Русі
  url: https://uk.wikipedia.org/wiki/Спадщина_Київської_Русі
  type: reference
  notes: Legacy and claims
content_outline:
- section: Вступ — Три століття Русі
  points:
  - Огляд періоду 882-1240 — від «суперсоюзу племен» до монархії з елементами федерації
  - 'Від племен до держави, від єдності до роздроблення — три етапи: становлення, розквіт, роздробленість'
  - Головні теми модулів 09-19 — синтез здобутків перед катастрофою 1240 року
  - Мета синтезу — узагальнення та оцінка — [!quote] Цитата Іларіона про «не в плохій бо країні...»
  words: 700
- section: Політичний розвиток
  points:
  - Етапи державотворення — 882 (Олег), 988 (Володимир), 1019–1054 (Ярослав)
  - Від Олега до Мономаха — піднесення — останнє посилення за Мономаха (1113–1125)
  - Роздроблення — криза чи розвиток? — [!myth-buster] «Феодальна роздробленість» як європейська норма децентралізації, а
    не катастрофа
  - Система влади — князь, віче, бояри — демократична роль віче та боярської ради як обмеження князівської влади
  words: 700
- section: Культурні досягнення
  points:
  - Софія Київська та архітектура — символ мудрості, Десятинна церква як перша кам'яна споруда
  - Літописання та література — «Повість минулих літ», «Слово о полку Ігоревім», «Повчання» Мономаха
  - Руська Правда та правова традиція — захист власності та честі, відсутність смертної кари
  - Мистецтво та ремесла — [!history-bite] Графіті Софії Київської як свідчення грамотності населення
  words: 700
- section: Суспільство та економіка
  points:
  - Соціальна структура — поділ на привілейованих, вільних (смерди), напіввільних (закупи) та невільних (холопи)
  - Місто і село — Гардаріки («країна міст»); Київ, Чернігів, Галич як центри
  - Торгівля — шлях «із варяг у греки» — експорт (хутро, мед) та імпорт (шовк, зброя)
  - Рівень життя порівняно з Європою — [!fact] «Руська Правда» і система штрафів (віри) замість кровної помсти
  words: 700
- section: Русь у Європі
  points:
  - Міжнародні зв'язки — інтеграція в «Pax Christiana», відсутність ізоляції
  - Династичні шлюби — [!context] Ярослав Мудрий як «тесть Європи» (Франція, Норвегія, Угорщина)
  - Культурний обмін — Анна Ярославна та її кириличний підпис у Франції
  - Русь очима сучасників — Тітмар Мерзебурзький про велич Києва (400 церков)
  words: 700
- section: Спадщина Русі — хто спадкоємець?
  points:
  - Український погляд — пряма спадкоємність — схема М. Грушевського (Русь -> ГВК -> Литовсько-Руська держава)
  - Російські претензії — критичний аналіз — [!decolonization] Розвінчання міфу про «колиску трьох братніх народів»
  - Схема Грушевського vs імперська схема — штучність перенесення столиці у Володимир-на-Клязьмі (колонізована периферія)
  - Русь як спільна спадщина? — політична традиція віче перейшла лише Україні, Московія обрала деспотію
  words: 700
- section: Ключові терміни та дати
  points:
  - Огляд термінології — полюддя, віче, вотчина, дитинець, посад
  - Найважливіші дати — 882, 988, 1019, 1097 (Любеч), 1169 (Боголюбський), 1240
  - Ключові постаті — Олег, Ольга, Святослав, Володимир, Ярослав, Мономах, Нестор, Аліпій
  - Головні джерела — Літописи, Руська Правда, твори Іларіона
  - Значення Київської Русі для України — фундамент державності та європейської ідентичності
  - Що залишилося після монголів — перехід центру до Галицько-Волинського князівства
  - Перехід до монгольської навали — руйнування Києва 1240 року як кінець епохи
  words: 800
vocabulary_hints:
  required:
  - спадщина (legacy/heritage) — спільна спадщина, культурна спадщина
  - спадкоємець (heir) — прямий спадкоємець, вважати себе спадкоємцем
  - державотворення (state formation) — етапи державотворення, процес державотворення
  - узагальнення (generalization) — робити узагальнення
  - піднесення (rise) — економічне піднесення, культурне піднесення
  - занепад (decline) — політичний занепад, період занепаду
  - культурний обмін (cultural exchange) — активний культурний обмін
  - претензії (claims) — територіальні претензії, безпідставні претензії
  - схема (scheme/framework) — імперська схема історії
  - джерело (source) — писемне джерело, історичне джерело
  recommended:
  - 'імперська схема (imperial scheme) — learner error: confusing with imperial plan'
  - пряма спадкоємність (direct succession) — доводити пряму спадкоємність
  - Грушевський (Hrushevsky) — Михайло Грушевський, схема Грушевського
  - деколонізація (decolonization) — деколонізація історії, деколонізаційний погляд
  - віче (veche) — народні збори
  - роздробленість (fragmentation) — феодальна роздробленість
  - міжусобиці (internecine strife) — князівські міжусобиці
activity_hints:
- type: comparative-study
  focus: Ukrainian vs Russian views on Rus legacy
  output: Critical analysis table
- type: essay-response
  focus: Чому Київська Русь важлива для української ідентичності?
- type: essay-response
  focus: Хто є справжнім спадкоємцем Київської Русі?
connects_to:
- hist-21 (Mongol invasion — Phase 3)
- 'hist-28 (Synthesis: Mongol era and Galicia)'
prerequisites:
- All Phase 2 modules (hist-09 through hist-19)
persona:
  voice: Senior Professor of History
  role: Dynastic Historian
grammar:
- Synthesis and review register
- Academic historical terminology
immersion: 100% Ukrainian

```

---

## PART 1: Deep Research

Research **Синтез: Київська Русь — спадщина** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Синтез: Київська Русь — спадщина

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Синтез: Київська Русь — спадщина"
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
