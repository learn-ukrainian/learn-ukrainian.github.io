# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-133
level: HIST
sequence: 133
slug: mariupol-azovstal
version: '2.0'
title: Маріуполь та Азовсталь
subtitle: 'Mariupol and Azovstal: The Siege'
focus: history
pedagogy: CBI
phase: HIST.13 [Russian Aggression]
word_target: 5000
objectives:
- Учень може описати облогу Маріуполя
- Учень може пояснити значення оборони Азовсталі
- Учень може проаналізувати гуманітарну катастрофу
- Учень може оцінити символічне значення Маріуполя для України
content_outline:
- section: 'Вступ: Місто-герой'
  points:
  - 'Маріуполь: історія та значення — до 2022 року вітрина відновленого Донбасу, культурний та IT-хаб; cultural hook: козацька
    фортеця Домаха як історична основа (Кальміуська паланка) замість імперського міфу про Катерину II'
  - '24 лютого 2022: початок облоги — перші обстріли та повне оточення військами РФ вже 1 березня 2022 року; include quote
    from [Свої.City]'
  - Чому Маріуполь став символом — місто-щит, яке 86 днів стримувало просування ворога на Запоріжжя та Дніпро (так званий
    «Маріупольський ефект»); [!context]
  words: 850
- section: Облога міста
  points:
  - 'Оточення та блокада — тактика «випаленої землі», відсутність світла, води, газу та зв''язку; sensory detail: приготування
    їжі на вогнищах у дворах, топлення снігу для води'
  - 'Бомбардування житлових кварталів — [!myth-buster] про «точні удари»: 90% житлового фонду пошкоджено або знищено, тактика
    килимових бомбардувань'
  - 'Драматеатр: трагедія мирних жителів — авіаудар 16 березня попри напис «ДІТИ», загибель сотень цивільних; [!history-bite]'
  - 'Пологовий будинок: цинізм агресора — авіаудар 9 березня, що викликав світовий резонанс; learner error: цинізм = cynicism
    (attitude) vs atrocity (act)'
  words: 850
- section: Оборона Азовсталі
  points:
  - Полк «Азов» та морська піхота — прорив 36-ї бригади на з'єднання з гарнізоном заводу 15 квітня 2022 року; [!military]
  - 'Підземна фортеця: цивільні та військові — життя в бункерах («місто під землею»), операції без анестезії, роль медиків
    «Янголи Азова»'
  - 82 дні оборони — хронологія стійкості від повного оточення до наказу про вихід (20 травня)
  - Евакуація цивільних — складні перемовини, «зелені коридори» та фільтраційні табори окупантів (термін «фільтрація» як евфемізм
    репресій)
  - 'Рішення про здачу: врятувати життя — наказ вищого командування 20 травня 2022 року заради збереження особового складу;
    include quote from [Денис Прокопенко]'
  words: 850
- section: Первинні джерела
  points:
  - Відеозвернення захисників — «Волина», «Калина», «Пташка» як голоси з підземелля; include quote from [Волина] (звернення
    до світових лідерів)
  - 'Свідчення евакуйованих — історії тих, хто вирвався з пекла, відеощоденники та фото «Ореста» (Дмитро Козацький); learner
    error: survivor = виживший (calque) -> вцілілий'
  - Супутникові знімки руйнувань — фото Maxar, фіксація масових поховань у Мангуші та Старому Криму як доказ воєнних злочинів
  words: 850
- section: Деколонізаційний погляд
  points:
  - Російська пропаганда про «визволення» — [!decolonization] порівняння тактики в Маріуполі з Грозним та Алеппо (знищення
    міст)
  - 'Реальність: геноцид міста — урбіцид, знищення культурного коду (музей Куїнджі, мозаїки Алли Горської); [!myth-buster]'
  - Маріуполь як доказ на трибуналі — документування воєнних злочинів для майбутніх судів (Гаага)
  words: 850
- section: 'Підсумок: Пам''ять та відбудова'
  points:
  - Полонені захисники — трагедія в Оленівці (вбивство полонених), боротьба родин за повернення героїв
  - 'Обмін: Азов повертається — 21 вересня 2022 року та повернення командирів з Туреччини; [!reflection]'
  - Майбутня відбудова Маріуполя — візія «Mariupol Reborn», місто має стати символом українського відродження, а не лише скорботи
  words: 750
vocabulary_hints:
  required:
  - 'облога (siege) — тримати облогу, зняти облогу, перебувати в облозі; collocation: повна блокада міста'
  - 'оборона (defense) — лінія оборони, територіальна оборона, тримати оборону; collocation: героїчна оборона Азовсталі'
  - 'евакуація (evacuation) — примусова евакуація, евакуаційна колона, зрив евакуації; context: гуманітарні коридори'
  - бомбардування (bombardment) — килимове бомбардування, авіаційне бомбардування, масований обстріл
  - 'полонений (prisoner of war) — військовополонений, обмін полоненими, катування полонених; collocation: звільнення з полону'
  - 'захисник (defender) — захисники Азовсталі, захисники України; context: гарнізон Маріуполя'
  - 'блокада (blockade) — морська блокада, прорив блокади, жити в блокаді; context: гуманітарна катастрофа'
  - руйнування (destruction) — масштабні руйнування, зазнати руйнувань, вщент зруйнований
  recommended:
  - 'підземелля (underground) — бункери Азовсталі, жити в підземеллі; context: розгалужена система тунелів'
  - 'гуманітарний коридор (humanitarian corridor) — «зелений коридор», погодження коридорів; note: часто зривалися ворогом'
  - цивільний (civilian) — цивільне населення, жертви серед цивільних, мирні жителі
  - обмін (exchange) — великий обмін, процедура обміну, обмінний фонд
  - пропаганда (propaganda) — російські наративи, жертва пропаганди, інформаційна війна
  - трибунал (tribunal) — міжнародний трибунал, Гаазький трибунал, воєнні злочини
  - урбіцид (urbicide) — свідоме знищення міста, стирання ідентичності
  - фільтрація (filtration) — фільтраційні табори, проходити фільтрацію, депортація
activity_hints:
- type: reading
  focus: Звернення захисників Азовсталі
  source: Відеоматеріали
  items: 4
- type: essay-response
  focus: Чому оборона Маріуполя стала символом українського спротиву?
connects_to:
- hist-135 (Каховська ГЕС)
- hist-139 (Злочини і стійкість)
prerequisites:
- 'hist-133 (Війна 2022: початок)'
persona:
  voice: Senior Professor of History
  role: Steelworks Defender
grammar:
- Минулий та теперішній час
- Військова та гуманітарна лексика
- Пасивні конструкції для опису подій
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Маріуполь та Азовсталь** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Маріуполь та Азовсталь

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Маріуполь та Азовсталь"
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
