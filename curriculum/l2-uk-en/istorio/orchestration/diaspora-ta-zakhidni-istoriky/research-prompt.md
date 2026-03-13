# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: istorio-006
level: ISTORIO
sequence: 6
slug: diaspora-ta-zakhidni-istoriky
version: '1.0'
title: Діаспора та західні історики
focus: history
pedagogy: seminar
word_target: 5000
objectives:
- Analyze the causes and consequences of діаспора та західні історики
- Evaluate the historical significance of історія в екзилі
- Trace the development of діалог із україною після 1991
sources:
- name: Harvard Ukrainian Research Institute (HURI)
  url: https://huri.harvard.edu/
  type: reference
  notes: Key Western academic institution
- name: Омелян Пріцак
  url: https://uk.wikipedia.org/wiki/Пріцак_Омелян_Йосипович
  type: reference
  notes: Founder of HURI
- name: Орест Субтельний
  url: https://uk.wikipedia.org/wiki/Субтельний_Орест
  type: reference
  notes: Author of most popular English-language history
- name: 'Ukraine: A History (book info)'
  url: https://www.utpress.utoronto.ca/9781442609914/ukraine
  type: secondary
  notes: Subtelny's standard text
content_outline:
- section: Вступ — Історія в екзилі
  points:
  - Чому діаспора писала історію
  - Держава без держави — наука як замінник
  - Збереження пам'яті для майбутнього
  - Зв'язок із батьківщиною
  words: 700
- section: Українські наукові інституції на Заході
  points:
  - НТШ (Наукове товариство імені Шевченка)
  - У|ван (Українська Вільна Академія Наук)
  - Гарвардський українознавчий інститут (HURI)
  - Канадський інститут українських студій (CIUS)
  - Чому університети, а не уряд
  words: 700
- section: Омелян Пріцак і Гарвард
  points:
  - Біографія — від Львова до Гарварду
  - Створення HURI (1973)
  - Методологія — тюркологія, орієнталістика
  - «Походження Русі» — контроверсійна праця
  - Спадщина — журнали, конференції, кадри
  words: 700
- section: Орест Субтельний — популяризатор
  points:
  - Біографія — другe покоління діаспори
  - '«Ukraine: A History» (1988) — чому стала класикою'
  - Доступність для неспеціалістів
  - Критика — що застаріло
  - Переклад українською
  words: 700
- section: Інші ключові постаті
  points:
  - Пол Роберт Маґочі — Закарпаття
  - Джон-Пол Химка — соціальна історія
  - Сергій Плохій — сучасний лідер
  - Тімоті Снайдер — глобальна аудиторія
  - Марк фон Гаґен — імперська історія
  words: 700
- section: Методологічні особливості західної школи
  points:
  - Об'єктивність vs. національний наратив
  - Доступ до архівів — переваги і межі
  - Аудиторія — хто читає
  - Вплив на політику — експертиза
  words: 700
- section: Діалог із Україною після 1991
  points:
  - Повернення праць на батьківщину
  - Спільні проєкти
  - Нове покоління — вже не діаспора
  - Що далі
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
- діаспора
- українознавство
- наукова інституція
- архів
- методологія
- орієнталістика
- популяризація
- об'єктивність
- експертиза
- спадщина
- екзиль
- академічна свобода
- наукова школа
- рецензія
- синтез
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
  focus: 'Preface from Subtelny''s «Ukraine: A History»'
- type: reading
  focus: Explore HURI website — list 3 current research projects
- type: comparative-study
  focus: Compare chapter on Khmelnytsky in Subtelny vs. Soviet textbook
- type: essay-response
  focus: Яку роль відіграла діаспора у збереженні української історичної пам'яті?
persona:
  voice: Academic Historiographer
  role: Historiographical Liaison
prerequisites:
- polskyi-pohliad
connects_to:
- nova-ukrainska-istorio

```

---

## PART 1: Deep Research

Research **Діаспора та західні історики** for the **istorio** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Діаспора та західні історики

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Діаспора та західні історики"
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
