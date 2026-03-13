# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-127
level: HIST
sequence: 127
slug: aneksiia-krymu
version: '2.0'
title: 'Анексія Криму: Початок війни'
subtitle: 'Annexation of Crimea: The Beginning of War'
focus: history
pedagogy: CBI
phase: HIST.12 [Independence]
word_target: 5000
objectives:
- Учень може описати механізм анексії Криму та роль «зелених чоловічків»
- Учень може проаналізувати порушення Будапештського меморандуму
- Учень може спростувати основні міфи російської пропаганди про Крим
sources:
- name: Резолюція ГА ООН 68/262
  url: https://undocs.org/ua/A/RES/68/262
  type: primary
  notes: Офіційний міжнародний документ
- name: КримSOS
  url: https://krymsos.com
  type: secondary
  notes: Свідчення очевидців та звіти про порушення прав людини
content_outline:
- section: Вступ
  points:
  - 'Лютий 2014: контекст після Майдану — вакуум влади, втеча Януковича, перемога Революції Гідності — початок операції РФ
    20 лютого, коли Янукович ще перебував у Києві'
  - Поява 'зелених чоловічків' — озброєні люди без розпізнавальних знаків (ГРУ) захоплюють аеропорти Бельбек і Сімферополь;
    include [!history-bite] about medal date 20.02.14 confirming premeditation
  - Стратегічне значення півострова — концепція «непотопного авіаносця», контроль над Чорним морем
  words: 1250
- section: 'Читання: Хроніка злочину'
  points:
  - 'Початок операції: Медаль за повернення — доказ завчасного планування агресії ще до втечі президента (20.02.14—18.03.14)'
  - 'Інформаційна агресія: Міф про «Поїзд дружби» — include [!myth-buster] about nonexistent «Right Sector» trains used to
    mobilize fear — технологія мобілізації паніки'
  - 'Спротив: 26 лютого — include [!context] about Day of Resistance; мітинг 5-10 тисяч кримських татар та українців проти
    «Русского единства», зрив сесії парламенту'
  - Блокада, флот і вода — блокування військових частин «живим щитом», історія тральщика «Черкаси» та вірність присязі
  - 'Фейковий референдум: Театр абсурду — голосування під дулами автоматів, статистична аномалія 96.77%, відсутність списків
    виборців та спостерігачів'
  - Мілітаризація Криму та зміна демографічного ландшафту — include [!decolonization] comparing 2014 to 1783; витіснення 100
    тис. українців і завезення 500 тис.+ росіян (колонізація)
  - Міжнародна реакція та правові наслідки — невизнання анексії цивілізованим світом, Резолюція ГА ООН 68/262 (27 березня
    2014)
  words: 1250
- section: Первинні джерела
  points:
  - Будапештський меморандум (1994) — грубе порушення гарантій безпеки та територіальної цілісності України Росією
  - Виступ Путіна 18 березня 2014 року — аналіз імперських тез про «сакральний Корсунь» та «історичну справедливість» (маніпуляція
    історією)
  - Свідчення очевидців — історія Решата Аметова (перша жертва окупації, закатований за одиночний пікет), спогади учасників
    мітингу 26 лютого (Рефат Чубаров)
  - Резолюція Генасамблеї ООН 68/262 — include [!source] quoting non-recognition of the referendum; supported by 100 nations
    supporting Ukraine's integrity
  words: 1250
- section: Деколонізаційний погляд
  points:
  - 'Міфи та реальність: спростування «споконвічно російського» Криму — імперська присутність лише з 1783 року vs багатовікова
    історія Кримського ханства (корінний народ киримли)'
  - 'Імперські наративи та їх розвінчання — include [!culture] with slogan «Millet! Vatan! Qırım!»; debunking the «Khrushchev''s
    gift» myth (economic necessity: water, logistics)'
  words: 1250
vocabulary_hints:
  required:
  - анексія (annexation) — незаконна ~, спроба ~, невизнання ~; contested term vs «возз'єднання»
  - окупація (occupation) — тимчасова ~, режим ~, початок ~; 20 лютого 2014 року
  - санкції (sanctions) — запровадити ~, економічні ~, персональні ~; міжнародна реакція
  - референдум (referendum) — фейковий ~, незаконний ~, під дулами автоматів; 16 березня
  - меморандум (memorandum) — Будапештський ~, порушення умов ~; гарантії безпеки
  - суверенітет (sovereignty) — державний ~, повага до ~, захист ~
  - територіальна цілісність (territorial integrity) — відновлення ~, гарантії ~; резолюція ООН
  - гібридна війна (hybrid war) — елементи ~, інформаційна складова ~, методи ~; «зелені чоловічки»
  - спротив (resistance) — ненасильницький ~, рух ~, День ~; 26 лютого
  - блокада (blockade) — морська ~, інформаційна ~, військових частин; тральщик «Черкаси»
  recommended:
  - півострів (peninsula) — Кримський ~, стратегічне значення ~; «непотопний авіаносець»
  - аеропорт (airport) — захоплення ~, контроль над ~; Бельбек, Сімферополь
  - парламент (parliament) — Верховна Рада АРК, захоплення будівлі ~; 27 лютого
  - громадяни (citizens) — України, РФ, права ~; заміщення населення
  - переселення (resettlement) — примусове ~, заміщення населення, колонізація; демографічна інженерія
activity_hints:
- type: reading
  focus: Резолюція ООН та Меморандум
- type: critical-analysis
  focus: Порівняння Анексії та Окупації
- type: essay-response
  focus: Наслідки порушення міжнародного права
persona:
  voice: Senior Professor of History
  role: Crimean Journalist
grammar:
- Historical narrative tenses
- Official vs. Informal register
prerequisites:
- revoliutsiia-hidnosti
connects_to:
- krymski-tatary-pislia-2014

```

---

## PART 1: Deep Research

Research **Анексія Криму: Початок війни** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Анексія Криму: Початок війни

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Анексія Криму: Початок війни"
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
