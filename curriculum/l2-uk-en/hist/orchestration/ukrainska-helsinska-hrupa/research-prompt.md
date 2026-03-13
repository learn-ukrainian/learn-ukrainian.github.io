# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-115
level: HIST
sequence: 115
slug: ukrainska-helsinska-hrupa
version: '2.0'
title: Українська Гельсінська група
subtitle: The Ukrainian Helsinki Group
focus: history
pedagogy: CBI
phase: HIST.11 [Post-War Soviet Ukraine]
word_target: 5000
objectives:
- Учень може описати створення та діяльність Української Гельсінської групи
- Учень може пояснити значення правозахисного руху
- Учень може проаналізувати долю членів групи
- Учень може оцінити вплив УГГ на здобуття незалежності
content_outline:
- section: 'Вступ: Гельсінські угоди'
  points:
  - '1975: Гельсінський акт — підписаний 1 серпня 1975 року Брежнєвим, легітимізував кордони в обмін на зобов''язання з прав
    людини; engagement hook: [!context] (СРСР вважав це «порожньою формальністю»)'
  - Права людини як зброя — концепція «третього кошика» (гуманітарні питання) як інструмент тиску на режим
  - 'Чому виникли Гельсінські групи — ідея «ловити владу на слові»: вимагати виконання підписаних міжнародних угод'
  words: 850
- section: Створення УГГ (1976)
  points:
  - 'Засновники: Руденко, Тихий, Лук''яненко — також Олесь Бердник, Петро Григоренко, Оксана Мешко; створена 9 листопада 1976
    року'
  - Меморандум групи — Меморандум №1 як декларація принципів про вільний обмін інформацією та акредитацію журналістів
  - 'Цілі та методи — збір фактів порушень, передача на Захід через московських дипломатів; engagement hook: [!history-bite]
    (оголошення в Москві на квартирі Сахарова)'
  - Зв'язок із шістдесятниками — спадкоємність поколінь (Руденко — фронтовик, Бердник — фантаст, пізніше Стус)
  words: 850
- section: Діяльність та репресії
  points:
  - Документування порушень — випуск 30 меморандумів про порушення прав людини, психіатрію та русифікацію
  - Арешти членів групи — початок репресій 5 лютого 1977 року (арешт Руденка і Тихого)
  - Табори та в'язниці — загальний термін ув'язнення членів понад 550 років; умови в таборах (Кучино, ВС-389/36, карцери)
  - Загибель Олекси Тихого та Василя Стуса — смерть Стуса 4 вересня 1985 року в карцері; загибель Литвина і Марченка
  - Група в еміграції — роль Петра Григоренка та Надії Світличної у представництві на Заході; солідарність з кримськими татарами
  words: 850
- section: Первинні джерела
  points:
  - 'Меморандум УГГ — engagement hook: [!quote] («Ми розуміємо, що заліковування ран...» — Меморандум №1)'
  - Документи групи — трактування русифікації як етноциду та порушення прав людини (порушення Конституції)
  - Листи з таборів — способи передачі інформації (в швах одягу, вивчення напам'ять)
  words: 850
- section: Деколонізаційний погляд
  points:
  - 'Радянський наратив: «антирадянська діяльність» — engagement hook: [!myth-buster] (міф про «шпигунів ЦРУ» vs легальна
    діяльність на основі радянських законів)'
  - 'Реальність: мирна боротьба за права — зміна парадигми опору від збройного (УПА) до правового; engagement hook: [!decolonization]'
  - УГГ як передвісник незалежності — єдина Гельсінська група в СРСР, що не саморозпустилася і трансформувалася в політичну
    силу
  words: 850
- section: 'Підсумок: Від УГГ до Руху'
  points:
  - Спадщина групи — трансформація в Українську Гельсінську Спілку (УГС) 7 липня 1988 року
  - 'Члени УГГ в незалежній Україні — Левко Лук''яненко як автор Акту проголошення незалежності; engagement hook: [!culture]'
  - Левко Лук'яненко та День Незалежності — символічний зв'язок між дисидентським рухом і державністю
  words: 750
vocabulary_hints:
  required:
  - правозахисний (human rights) — правозахисний рух, правозахисна діяльність
  - група (group) — Українська Гельсінська група (УГГ), члени-засновники
  - дисидент (dissident) — радянські дисиденти, рух опору, в'язень сумління
  - репресії (repressions) — політичні репресії, жертви репресій, машина терору
  - табір (camp) — виправно-трудовий табір, мордовські табори, табір особливого режиму
  - арешт (arrest) — масові арешти, загроза арешту, перша хвиля арештів
  - меморандум (memorandum) — Меморандум №1, підписати меморандум, оприлюднити документ
  - права людини (human rights) — порушення прав людини, захист прав людини, Загальна декларація
  recommended:
  - політв'язень (political prisoner) — статус політв'язня, українські політв'язні
  - Гельсінкі (Helsinki) — Гельсінські угоди, Заключний акт НБСЄ
  - документування (documentation) — документування злочинів, збір фактів порушень
  - еміграція (emigration) — вимушена еміграція, діаспора, представництво на Заході
  - реабілітація (rehabilitation) — закон про реабілітацію жертв, посмертна реабілітація
  - спадщина (legacy) — історична спадщина, спадкоємність боротьби (УПА -> УГГ -> Рух)
activity_hints:
- type: reading
  focus: Меморандум УГГ
  source: Архівні документи
  items: 4
- type: essay-response
  focus: Яку роль відіграла УГГ у боротьбі за незалежність?
connects_to:
- hist-117 (Чорнобиль)
- hist-118 (Рух)
prerequisites:
- hist-115 (Шістдесятники)
persona:
  voice: Senior Professor of History
  role: Human Rights Defender
grammar:
- Минулий час в історичному наративі
- Правозахисна лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Українська Гельсінська група** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Українська Гельсінська група

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Українська Гельсінська група"
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
