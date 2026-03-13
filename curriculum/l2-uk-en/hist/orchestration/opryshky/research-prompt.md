# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-072
level: HIST
sequence: 72
slug: opryshky
version: '2.0'
title: 'Опришки Карпат: Легенда Довбуша'
subtitle: 'Opryshky of the Carpathians: The Legend of Dovbush'
focus: history
pedagogy: CBI
phase: B2.3b [Українська історія]
word_target: 5000
objectives:
- Учень може пояснити причини виникнення опришківства
- Учень може охарактеризувати постать Олекси Довбуша
- Учень може порівняти опришківство з іншими європейськими рухами
- Учень може проаналізувати фольклорний образ опришка
content_outline:
- section: 'Вступ: Пролог у сакральному Холодному Яру та Горганах'
  points:
  - Карпати як простір свободи та спротиву — концепція «natural fortress» та гір як зони, недосяжної для імперської влади
  - Феномен «соціального розбійництва» у світовому контексті — [!context] паралелі з балканськими гайдуками та грецькими клефтами
  - Чому саме гори породили опришківство — етимологія слова (лат. oppressor або укр. опріч/осторонь)
  words: 350
- section: 'Соціально-економічне тло: Анатомія колоніального гніту на Західній Україні'
  points:
  - Польське та австрійське панування в Галичині — посилення панщини до 4-5 днів на тиждень у XVIII ст.
  - Кріпосницький гніт на Гуцульщині — [!history-bite] втеча в гори не від праці, а від втрати гідності («право першої ночі»,
    тілесні покарання)
  - Економічна нерівність як рушій спротиву — роль орендарів-іноземців та зубожіння через неродючі ґрунти
  - Селянські повстання до Довбуша — 1738 рік як початок організованої «опришківської війни»
  words: 350
- section: 'Культура Гуцульщини: Духовний фундамент карпатських месників'
  points:
  - 'Гуцульська ідентичність та традиції — психологія горян: індивідуалізм та фізична витривалість'
  - 'Язичницькі вірування та християнство — релігійний синкретизм: віра в Бога та допомогу мольфарів'
  - Роль полонини у житті горян — полонинське господарство як тилова база постачання загонів
  - Мистецтво та ремесла Карпат — естетика побуту як частина ідентичності
  words: 350
- section: 'Олекса Довбуш: Від бідного легіня до легендарного вождя нації'
  points:
  - Біографія (1700-1745) — народження в Печеніжині, конфлікт із системою, перші згадки 1738 р.
  - Формування ватаги та методи боротьби — ядро з 30-50 побратимів, мобільна тактика нападів
  - Територія дій — від Карпат до Поділля — [!myth-buster] Довбуш не велетень-чаклун, а кульгавий стратег (поранення 1739
    р.)
  - 'Довбуш як «Робін Гуд» українських гір — найуспішніший рейд: захоплення Богородчанського замку (серпень 1744)'
  words: 350
- section: 'Опришківська медицина: Трави полонин, народне знахарство та сила віри'
  points:
  - Лікарські рослини Карпат — [!culture] використання живиці, моху сфагнуму та прополісу як антисептиків
  - Лікування поранень у польових умовах — виживання без антибіотиків завдяки народній медицині
  - Роль знахарів у ватазі — сакральні практики, замовляння та обереги («згарди»)
  words: 350
- section: 'Жінки в опришківстві: Марічка Дзвінчук та невідомі героїні гір'
  points:
  - Дзвінка — кохана Довбуша (легенда vs історія) — Марічка як дружина ґазди, а не просто коханка
  - Жінки як помічниці та інформатори — [!decolonization] жінки не пасивні жертви, а розвідниці та утримувачки «явочних квартир»
  - Гендерні ролі в карпатському суспільстві — жінка як берегиня тилу, поки чоловік «на збої»
  words: 350
- section: 'Скарби Довбуша: Легенди, містика та незгасна золота спадщина'
  points:
  - Легенди про заховані скарби — міфи про «закляте золото», що відкривається раз на рік
  - Скелі Довбуша як туристичний об'єкт — ймовірний пункт базування в с. Бубнище
  - Археологічні пошуки — [!myth-buster] реальний скарб — це зброя (кріси, пістолі), а не золото
  words: 350
- section: 'Загибель та безсмертя: Трагедія в селі Космач 1745 року'
  points:
  - Обставини зради та смерті — 24 серпня 1745 р., постріл Стефана Дзвінчука через ревнощі та нагороду
  - Роль Штефана Дзвінки — зрада побратима та співпраця зі шляхтою
  - Посмертна слава та культ — четвертування тіла для залякування (Коломия, Станіславів)
  words: 350
- section: Опришківський етос та лицарські традиції карпатського спротиву
  points:
  - Кодекс честі опришків — присяга на бартці, вступний ритуал до ватаги
  - 'Кого грабували, кого захищали — розподіл здобичі: церква, бідні, зброя («побратимські»)'
  words: 350
- section: 'Читання: Опришківська бартка як символ та кодекс лицарської честі воїна гір'
  points:
  - Бартка — зброя та символ — статусний предмет, аналог лицарського меча
  - Майстерність карпатських ковалів — інкрустація металом як ознака рангу
  - Ритуальне значення зброї — бартка як сакральний предмет та інструмент
  words: 350
- section: 'Деколонізаційний погляд: Міфи імперій та справжня українська реальність'
  points:
  - Польська історіографія — «розбійники» та «бандити» — термін «latrones» у судових документах
  - Радянська інтерпретація — «класова боротьба» — міф про «атеїстів»-більшовиків
  - Українська деколонізація — національно-визвольний рух — асиметрична війна проти окупації, порівняння з УПА
  words: 350
- section: 'Міжнародні паралелі: Опришки та Європа у боротьбі за гідність'
  points:
  - Робін Гуд (Англія), Яношик (Словаччина) — Яношик як сучасник Довбуша
  - Балканські гайдуки — спільна гірська тактика боротьби
  - Спільні риси «соціального розбійництва» — відновлення справедливості злочинним шляхом (за Е. Гобсбаумом)
  words: 350
- section: 'Сучасна спадщина: Уроки незламності для України XXI століття та нашого майбутнього'
  points:
  - Опришки у сучасній культурі — фільм «Довбуш» (2023) та літературні твори
  - Туризм на Гуцульщині — місця пам'яті (Печеніжин, Космач, Скелі Довбуша)
  - Символ спротиву окупації — «Довбуш живий, поки живі Карпати»
  words: 350
- section: 'Первинні джерела: Голос народу та дзеркало героїчної епохи українського спротиву'
  points:
  - Австрійські судові протоколи — цитати з вироку Василю Баюраку (1754) про четвертування
  - Народні пісні та легенди — «Ой попід гай зелененький» як джерело образу
  words: 350
- section: Підсумок
  points:
  - Довбуш як символ українського спротиву — вічний архетип Героя
  - Від історії до міфу — трансформація реальної людини в легенду
  words: 100
vocabulary_hints:
  required:
  - 'опришок (opryshok rebel) — collocations: піти в опришки, ватага опришків; context: учасник повстанського руху'
  - 'ватага (band/group) — collocations: зібрати ватагу, опришківська ватага; context: організований загін'
  - 'бартка (Carpathian axe) — symbol: символ влади і честі; context: присяга на бартці'
  - 'легінь (young man) — dialect: парубок, молодий хлопець; context: гуцульський легінь'
  - 'полонина (mountain pasture) — context: місце випасу та схованки опришків'
  - 'гуцул (Hutsul) — context: етнографічна група українців Карпат'
  - 'Карпати (Carpathians) — context: природна фортеця, гори'
  - 'зрада (betrayal) — context: ціна зради, зрада Дзвінчука'
  recommended:
  - 'скарб (treasure) — context: золото Довбуша, скарби на зброю'
  - 'ватажок (leader) — context: ватажок загону, Олекса як ватажок'
  - 'месник (avenger) — context: народний месник, відновлення справедливості'
  - 'кріпак (serf) — context: втікач від панщини'
  - 'шляхта (nobility) — context: польська шляхта, боротьба проти шляхти'
  - 'мольфар (shaman/sorcerer) — context: карпатський чаклун, допомога опришкам'
activity_hints:
- type: reading
  focus: Народні пісні про Довбуша
  items: 4
- type: essay-response
  focus: Порівняння Довбуша з Робін Гудом
- type: map-study
  focus: Територія діяльності опришків
- type: critical-analysis
  focus: 'Верифікація фактів: Легенди vs історичні факти'
  items: 5
persona:
  voice: Senior Professor of History
  role: Mountain Guide
grammar:
- Діалектизми в історичному тексті
- Описові конструкції
register: публіцистичний
prerequisites:
- koliivshchyna
connects_to:
- petro-kalnyshevskyi

```

---

## PART 1: Deep Research

Research **Опришки Карпат: Легенда Довбуша** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

### Your RAG Tools (USE THEM)

You have access to Ukrainian language tools via MCP. **Use them during research.**

| Tool | When to use | Args |
|------|-------------|------|
| `query_wikipedia` | Get full article text (50K chars) for deep research | `query`, `mode="extract"` |
| `query_wikipedia` | See article structure before diving in | `query`, `mode="sections"` |
| `query_wikipedia` | Read a specific section by index | `query`, `mode="section"`, `section=N` |
| `query_wikipedia` | Find the right article title | `query`, `mode="search"` |
| `search_literary` | Find primary source excerpts (chronicles, poetry, legal texts, testimonies) | `query`, `genre` (optional) |
| `verify_words` | Check Ukrainian words exist in VESUM dictionary | `words` (list of strings) |
| `query_grac` | Check word frequency in Ukrainian corpus | `query`, `mode="frequency"` |

> **Important**: Invoke these tools using your standard tool-calling interface. Do NOT write Python code.

### Mandatory Research Workflow (follow ALL 4 steps in order)

**Step 1 — Wikipedia foundation**: Call `query_wikipedia(mode="extract")` for the main topic article. If the article is long, use `mode="sections"` then `mode="section"` to read key sections. This gives you the factual backbone.

**Step 2 — Literary RAG deep search (MANDATORY)**: Call `search_literary` at least **3 times** with different queries targeting different aspects of the topic. Search for:
- The main subject (person/event/concept name)
- Related figures, institutions, or movements
- The historical period or genre

This is where primary source quotes come from — chronicles, legal texts, poetry, testimonies, scholarly works. Our RAG has 125K+ chunks from litopys.org.ua, izbornyk.org.ua, and scholarly monographs. **Do NOT skip this step even if Wikipedia gave good results.** Wikipedia is secondary; literary RAG has primary sources.

**Step 3 — Cross-verify**: Use `verify_words` to check any Ukrainian vocabulary you plan to highlight. Use `query_grac(mode="frequency")` for frequency data on key terms.

**Step 4 — Fill gaps**: If Steps 1-2 left gaps in any `content_outline` section, do targeted `query_wikipedia` or `search_literary` calls for those specific sections.

### Research Requirements

1. **Sources**: Minimum **4 distinct sources** — at least 1 from Wikipedia AND at least 2 from `search_literary` (RAG). Also consult history.org.ua, litopys.org.ua. Russian-language sources are PROHIBITED. Every factual claim must be traceable to a cited source.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find **3+** quotable primary source excerpts using `search_literary`. Use guillemet quotes «...» for Ukrainian text. If `search_literary` returns relevant chunks, extract and attribute them properly. Mark unverified quotes as `[needs verification]`.
4. **Engagement Hooks**: Research and expand upon any hooks already suggested in the `content_outline`, and add new ones to reach a minimum of 6 total hooks mapped to specific content sections:
   - `[!myth-buster]` — Decolonization: correct imperial/Soviet myths
   - `[!history-bite]` — Surprising or lesser-known facts
   - `[!context]` — Broader historical/cultural context
   - `[!quote]` — Primary source citations
   - `[!decolonization]` — Ukraine-centric reframing
   - `[!culture]` — Cultural significance
5. **Decolonization Angle**: Identify how this topic has been distorted by imperial/Soviet historiography (e.g., erasure of identity, stripping of local agency, Soviet tropes) and define the Ukrainian-centric framing (centering local agency, restoring historical truth, using accurate terminology).
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
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Soviet tropes (e.g., erasure of victim identity), imperial terminology, or Moscow-centric timelines
- **Engagement callouts**: map 6+ hooks to specific sections during research (not as afterthought patches)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

===RESEARCH_START===

# Дослідження: Опришки Карпат: Легенда Довбуша

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Опришки Карпат: Легенда Довбуша"
type: "event" # "event", "biography", or "phenomenon"
vital_status: "living" # ONLY for biography: "living" or "deceased" (omit for events)
dates:
  start: "YYYY-MM-DD" # Event start OR biography birth (approximate: "~YYYY")
  end: "YYYY-MM-DD"   # Event end OR biography death (omit if living/ongoing)
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
- Section "{section_name}": [!hook_type] — {raw research fact/data to be used for this hook in Phase B}
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

## Friction Report (MANDATORY)

After Output Block 1, include the Friction Report:

===FRICTION_START===
**Phase**: Phase A: Research + Meta (Seminar)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | SOURCE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the plan's content_outline
- Do NOT use Russian-language sources
- Do NOT fabricate quotes or dates — if unsure, mark as "[needs verification]"
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
