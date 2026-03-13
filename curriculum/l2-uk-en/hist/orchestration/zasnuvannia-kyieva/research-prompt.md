# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-006
level: HIST
sequence: 6
slug: zasnuvannia-kyieva
version: '2.0'
title: Заснування Києва
subtitle: Legend and Archaeology of the Capital
focus: history
pedagogy: seminar
phase: HIST.1 [Origins]
word_target: 5000
objectives:
- Учень може розповісти легенду про заснування Києва братами Києм, Щеком, Хоривом та сестрою Либідь
- Учень може пояснити геополітичне значення Києва в контексті шляху «з варягів у греки»
- Учень може порівняти легендарні та археологічні свідчення про виникнення міста
- Учень може спростувати імперські міфи про походження Києва
sources:
- name: Повість минулих літ (Нестор)
  url: https://litopys.org.ua/pvl/pvl01.htm
  type: primary
- name: Про управління імперією (Костянтин Багрянородний)
  url: http://litopys.org.ua/izborn79/izb79_03.htm
  type: primary
content_outline:
- section: Вступ
  points:
  - 'Значення Києва як сакрального серця держави — концепція «Єрусалима землі руської» та символізм «міста на семи пагорбах»
    (паралель з Римом); engagement hook: [!context]'
  words: 550
- section: Читання
  points:
  - 'Аналіз «Повісті минулих літ» як джерела — легенда про Кия, Щека, Хорива і Либідь; engagement hook: [!source]'
  - 'Нестор про Кия: спростування версії «Кия-перевізника» на користь «Кия-князя», що ходив до Царгорода'
  words: 550
- section: Варяги та хозари
  points:
  - Шлях «з варягів у греки» та Кенугард — Київ як транзитний хаб Північ-Південь
  - Хозарський вплив — легенда про данину мечами (двосічна зброя полян як символ майбутньої перемоги над хозарами)
  - 'Загадка назви «Самбатас» у Костянтина Багрянородного — можливі єврейські (субота) або скандинавські (укріплення човнів)
    корені; engagement hook: [!history-bite]'
  words: 550
- section: Первинні джерела
  points:
  - Літописні свідчення та візантійські описи — «Повість минулих літ» (патріотичний погляд) vs «Про управління імперією» (зовнішній,
    комерційний погляд)
  - 'Цитата: «Зробили вони городок і на честь брата їх найстаршого назвали його Києвом»; engagement hook: [!quote]'
  words: 550
- section: Деколонізаційний погляд
  points:
  - 'Спростування міфу про «спільну колиску» — Кий як полянський (праукраїнський) князь, а не спільний предок «трьох братніх
    народів»; engagement hook: [!myth-buster]'
  - Критика дати 482 рік — штучний ювілей 1982 року для «збалансування» радянської історіографії
  words: 550
- section: Археологічні свідчення
  points:
  - Язичницьке капище на Старокиївській горі — фундамент і жертовник як доказ сакрального центру
  - 'Римські монети II ст. як свідчення давніх торгових зв''язків, але не дати заснування міста; engagement hook: [!history-bite]'
  words: 550
- section: 'Хронологія: Легенди та археологія'
  points:
  - Legend of Kyi, Shchek, Khoryv — етимологія топонімів (Щекавиця, Хоривиця, Либідь)
  - Archaeological evidence (Starokyivska Hora) — рови і вали V-VI ст., культура празького типу
  - Strategic location — контроль переправи через Дніпро і оборона на пагорбах
  words: 550
- section: Підсумок
  points:
  - Узагальнення значення заснування Києва — синтез легенди (ідентичність) та археології (фактаж)
  words: 550
- section: Потрібно більше практики?
  points:
  - Ресурси для самостійного поглиблення знань — віртуальні тури Національним музеєм історії України
  words: 600
vocabulary_hints:
  required:
  - засновник (founder) — засновник міста/династії
  - легенда (legend) — літописна легенда, за легендою
  - літопис (chronicle) — Повість минулих літ, Нестор Літописець
  - пагорб (hill) — на семи пагорбах, Старокиївська гора
  - данина (tribute) — платити данину, збирати данину
  - каганат (khaganate) — Хозарський каганат
  - варяги (Varangians) — шлях із варягів у греки
  - торговельний шлях (trade route) — контроль над шляхом
  - капіще (pagan sanctuary) — язичницьке капище
  - дитинець (citadel) — укріплений центр міста
  - переправа (ferry/crossing) — дніпровська переправа
  - транзитна торгівля (transit trade) — міжнародна торгівля
  - деколонізація (decolonization) — історична пам'ять
  - ідентичність (identity) — національна ідентичність
  - артефакт (artifact) — археологічний артефакт
activity_hints:
- type: reading
  focus: Аналіз літописної легенди
- type: critical-analysis
  focus: Зіставлення легенди та археології
- type: essay-response
  focus: Геополітичне значення Києва
connects_to:
- 'hist-07: Хозарський каганат і слов''яни'
prerequisites:
- 'hist-04: Слов''яни: Походження'
persona:
  voice: Senior Professor of History
  role: Chronicler Monk
grammar:
- Безособові речення на -но, -то (було засновано, названо)
- Складнопідрядні речення з підрядними з'ясувальними
- Вживання дієприкметників у пасивному стані
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Заснування Києва** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Заснування Києва

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Заснування Києва"
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
