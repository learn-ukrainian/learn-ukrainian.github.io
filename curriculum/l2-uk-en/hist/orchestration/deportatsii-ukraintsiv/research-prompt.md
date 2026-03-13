# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-110
level: HIST
sequence: 110
slug: deportatsii-ukraintsiv
version: '2.0'
title: Депортації українців 1944-1951
subtitle: Deportations of Ukrainians 1944-1951
focus: history
pedagogy: CBI
phase: HIST.11 [Post-War Soviet Ukraine]
word_target: 5000
objectives:
- Учень може описати масштаби депортацій українців у повоєнний період
- Учень може пояснити політичні причини та механізми депортацій
- Учень може проаналізувати операцію «Вісла» як етнічну чистку
- Учень може оцінити довготривалі наслідки депортацій
content_outline:
- section: 'Вступ: Післявоєнні переселення'
  points:
  - 'Контекст: нові кордони та «обмін населенням» — Угода 9 вересня 1944 року та встановлення кордону по «Лінії Керзона»;
    engagement hook: [!context] Мапа «Закерзоння» як втрачених етнічних земель'
  - Радянська та польська політика щодо українців — прагнення Сталіна та польських комуністів створити моноетнічні держави
  - 'Масштаб трагедії: сотні тисяч переміщених — сумарно понад 700 тисяч осіб (1944–1951); етапи: 1944–46, 1947 («Вісла»),
    1951 (обмін територіями)'
  words: 850
- section: Депортації до СРСР (1944-1946)
  points:
  - 'Примусове переселення з Закерзоння — від «добровільного» етапу до масового терору з 1945 року; engagement hook: [!myth-buster]
    Радянський термін «евакуація» як прикриття для етнічної чистки'
  - Умови транспортування та прибуття — товарні вагони, мінімальний час на збори, втрата майна та худоби
  - 'Розселення в Україні: нове життя на чужій землі — переважно західні області (Тернопільська, Львівська), заселення в покинуті
    польські хати'
  - Втрата культурної спадщини — розрив родинних зв'язків, втрата локальних традицій та діалектів
  words: 850
- section: Операція «Вісла» (1947)
  points:
  - 'Політичні причини: боротьба з УПА як привід — вбивство генерала Свєрчевського як формальний привід для каральної акції
    проти цивільних'
  - Примусове виселення з Лемківщини, Надсяння, Холмщини — квітень-липень 1947 року, повна депопуляція цілих регіонів
  - 'Розпорошення на «Відновлених землях» Польщі — стратегія асиміляції: заборона селитись більше 3-4 родин на село (не більше
    10% населення)'
  - 'Знищення лемківської та холмської культури — ліквідація греко-католицької церкви, ув''язнення інтелігенції; engagement
    hook: [!history-bite] Концтабір Явожно як місце репресій українців'
  words: 850
- section: Первинні джерела
  points:
  - 'Спогади депортованих — фіксація травми втрати «свого світу» (гір, церков); include quote: «Нас викинули в чисте поле,
    як худобу»'
  - Польські та радянські документи — докази координації дій НКВС та польської безпеки (UB) для знищення українського підпілля
  - 'Листи переселенців — скарги бойків (депортація 1951 року) на нестерпні умови в степах Півдня України; engagement hook:
    [!quote] Уривок про контраст між горами та степом'
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Етнічна чистка як інструмент імперій — спростування тези про «гуманізм», принцип колективної відповідальності; engagement
    hook: [!decolonization] Порівняння аргументації польських комуністів з сучасною російською пропагандою'
  - 'Паралелі: депортації кримських татар — спільний почерк тоталітарного режиму (1944 рік, товарні вагони, спецпоселення)'
  - Сучасне визнання та пам'ять — засудження операції «Вісла» Сенатом Польщі (1990), дискусії навколо терміну «геноцид»
  words: 850
- section: 'Підсумок: Спадщина травми'
  points:
  - Лемки та холмщаки сьогодні — асиміляція в Польщі vs збереження пам'яті в діаспорі
  - Польсько-українське примирення — складний діалог істориків, спільні молитви, відновлення цвинтарів
  - 'Уроки для сучасності — важливість культурної пам''яті; engagement hook: [!culture] Фестиваль «Ватра» як символ єднання
    розсіяної спільноти'
  words: 750
vocabulary_hints:
  required:
  - депортація (deportation) — масова депортація, примусова депортація
  - переселення (resettlement) — «добровільне» переселення (іронічно), угода про переселення
  - етнічна чистка (ethnic cleansing) — класична етнічна чистка, ознаки етнічної чистки
  - виселення (eviction) — насильницьке виселення, раптове виселення
  - репатріація (repatriation) — міф про репатріацію, так звана репатріація
  - розпорошення (dispersal) — розпорошення населення, мета розпорошення
  - операція (operation) — каральна операція, військова операція
  - примус (coercion) — під примусом, елементи примусу
  recommended:
  - ешелон (echelon/train) — товарні ешелони, довгі ешелони
  - табір (camp) — концтабір Явожно, збірний пункт
  - біженець (refugee) — статус біженця, доля біженців
  - репресії (repressions) — політичні репресії, масові репресії
  - колективізація (collectivization) — примусова колективізація на нових місцях
  - асиміляція (assimilation) — мовна асиміляція, повна асиміляція
activity_hints:
- type: reading
  focus: Спогади депортованих лемків
  source: Усна історія
  items: 4
- type: essay-response
  focus: Чому операція «Вісла» — це етнічна чистка?
connects_to:
- hist-111 (Сургунлік)
- hist-107 (УПА)
prerequisites:
- hist-109 (Повоєнна відбудова)
persona:
  voice: Senior Professor of History
  role: Oral Historian
grammar:
- Минулий час у трагічному наративі
- Пасивні конструкції для опису насильства
- Числівники та статистика
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Депортації українців 1944-1951** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

**Workflow**: Search Wikipedia FIRST for factual foundation → search literary RAG for primary quotes → verify vocabulary with VESUM.

### Research Requirements

1. **Sources**: Use `query_wikipedia` (mode=`extract`) for Ukrainian Wikipedia articles. Also consult history.org.ua, litopys.org.ua. Use `search_literary` for primary source excerpts. Russian-language sources are PROHIBITED.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find 2+ quotable primary source excerpts (original Ukrainian text preferred).
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

# Дослідження: Депортації українців 1944-1951

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Депортації українців 1944-1951"
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
