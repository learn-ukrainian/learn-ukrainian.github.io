# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-136
level: HIST
sequence: 136
slug: voienna-ekonomika
version: '2.0'
title: Воєнна економіка України
subtitle: Ukraine's War Economy
focus: history
pedagogy: CBI
phase: HIST.13 [Russian Aggression]
word_target: 5000
objectives:
- Учень може описати трансформацію української економіки під час війни
- Учень може пояснити роль волонтерського руху
- Учень може проаналізувати економічні виклики та досягнення
- Учень може оцінити стійкість української економіки
content_outline:
- section: 'Вступ: Економіка на війні'
  points:
  - Економічний шок 2022 року — падіння ВВП на 29.1%, інфляція 26.6% (найбільше за часи незалежності) — але менше прогнозованих
    40-50%
  - Як Україна вистояла — феномен стійкості банківської системи та фіксація курсу НБУ; [!history-bite] Банківська система
    2022 vs 2014 — чому не сталося «банкопаду» завдяки реформам
  - '''Воєнна економіка: що це означає'' — гібридна модель: ринкові механізми + державне регулювання (відмінність від планової
    економіки СРСР часів Другої світової)'
  words: 850
- section: Виклики та руйнування
  points:
  - Втрата території та підприємств — окупація ~20% території (металургія півдня, агросектор сходу); [!context] Втрата гігантів
    («Азовсталь», ММК ім. Ілліча) — мінус 30-40% експорту металів
  - Руйнування інфраструктури — прямі збитки понад $150 млрд (KSE Institute) станом на 2023 рік
  - Енергетичний терор — ракетні удари (жовтень 2022 — березень 2023), втрата 50% генерації — понад 1200 ракет і дронів
  - Блокада портів — зупинка 90% експорту на початку вторгнення — логістичний зашморг до відкриття морського коридору
  words: 850
- section: Адаптація та мобілізація
  points:
  - Перенесення виробництв — державна програма релокації (800+ підприємств на захід, зокрема Львівщина та Закарпаття)
  - Оборонна промисловість — зростання виробництва у 3 рази (2024), «Армія дронів», спільні підприємства (Rheinmetall, Baykar)
  - Волонтерський рух — «тіньова» економіка донатів як суспільний договір; [!culture] Феномен «донату» — банки Monobank та
    великі фонди (Притула, Чмут)
  - Зернова угода — від ініціативи ООН до самостійного морського коридору (серпень 2023) після виходу РФ з угоди
  - Міжнародна допомога — макрофінансова стабілізація та ріст резервів НБУ до рекордних $40+ млрд; [!history-bite] Економіка
    генераторів — децентралізована енергосистема бізнесу
  words: 850
- section: Первинні джерела
  points:
  - Економічна статистика — дані ЦЕС (Центр економічної стратегії) та звіти НБУ — інфляція впала до 5.1% у 2023 році
  - Свідчення підприємців — бізнес під час блекаутів («пункти незламності» в кав'ярнях) — адаптивність ММСП (99.98% суб'єктів)
  - Волонтерські звіти — фонди Притули/Чмута як ефективні менеджери ресурсів — прозорість як зброя
  words: 850
- section: Деколонізаційний погляд
  points:
  - '''Російська стратегія: знищити економіку'' — логіка колоніального покарання та спроба створити «Failed State»; [!myth-buster]
    Міф про нездатність вижити без РФ — спростування наративу про «404»'
  - '''Реальність: стійкість нації'' — цифровізація (Дія), сплата податків як акт опору — військовий ПДФО як основа місцевих
    бюджетів'
  - Економіка як фронт — переорієнтація логістики з Півночі/Сходу на Захід («Шляхи солідарності» ЄС) — остаточний розрив з
    імперією
  words: 850
- section: 'Підсумок: Відбудова майбутнього'
  points:
  - План відбудови — оцінка потреб $486 млрд (Світовий банк), принцип «Build Back Better» — не відновлювати радянське, а будувати
    нове
  - Інтеграція з ЄС — статус кандидата як якір реформ (червень 2022) та початок переговорів (грудень 2023)
  - Економічне майбутнє України — відмова від радянської спадщини на користь «зеленої» економіки та технологій; [!decolonization]
    Відновлення чи Модернізація?
  words: 750
vocabulary_hints:
  required:
  - 'економіка (economy) — collocations: воєнна економіка, тіньова економіка — usage: ''Економіка адаптувалася до війни'''
  - 'війна (war) — collocations: повномасштабна війна, економічний фронт — context: війна на виснаження ресурсів'
  - 'волонтер (volunteer) — collocations: волонтерський рух, збір коштів (донати) — cultural hook: донат як національна звичка'
  - 'інфраструктура (infrastructure) — collocations: критична інфраструктура, енергетична інфраструктура — context: удари
    по інфраструктурі'
  - 'виробництво (production) — collocations: релокація виробництва, оборонне виробництво — context: зростання ОПК'
  - 'допомога (aid) — collocations: міжнародна фінансова допомога, макрофінансова стабілізація — context: роль партнерів'
  - 'відбудова (reconstruction) — collocations: повоєнна відбудова, план відновлення — principle: Build Back Better'
  - 'стійкість (resilience) — collocations: економічна стійкість, фінансова стабільність — context: стійкість банківської
    системи'
  recommended:
  - 'енергетика (energy) — collocations: енергетична система, блекаут — history: зима 2022-2023'
  - 'експорт (export) — collocations: зерновий коридор, експортна виручка — context: розблокування портів'
  - 'санкції (sanctions) — collocations: санкційний тиск, обхід санкцій — context: вплив на агресора'
  - 'інвестиції (investments) — collocations: залучення інвестицій, інвестиційний клімат — future: страхування воєнних ризиків'
  - 'підприємство (enterprise) — collocations: малі та середні підприємства (ММСП), релоковане підприємство — fact: 74% робочих
    місць'
  - 'ВВП (GDP) — collocations: падіння ВВП, реальний ВВП — stat: -29.1% (2022) vs +5.3% (2023)'
activity_hints:
- type: reading
  focus: Історії українських підприємців на війні
  source: Медіа-матеріали
  items: 4
- type: essay-response
  focus: Як волонтерський рух допоміг українській економіці вистояти?
connects_to:
- hist-139 (Злочини і стійкість)
- hist-138 (Міжнародна підтримка)
prerequisites:
- hist-135 (Каховська ГЕС)
persona:
  voice: Senior Professor of History
  role: Logistics Strategist
grammar:
- Теперішній та минулий час
- Економічна лексика
- Складнопідрядні речення
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Воєнна економіка України** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Воєнна економіка України

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Воєнна економіка України"
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
