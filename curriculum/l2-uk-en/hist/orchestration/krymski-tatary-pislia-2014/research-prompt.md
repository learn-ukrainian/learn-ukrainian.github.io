# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-128
level: HIST
sequence: 128
slug: krymski-tatary-pislia-2014
version: '2.0'
title: Кримські татари після 2014
subtitle: Crimean Tatars After Russian Annexation
focus: history
pedagogy: CBI
phase: HIST.12 [Independence & Modern Era]
word_target: 5000
objectives:
- Учень може описати становище кримських татар після анексії
- Учень може пояснити репресії окупаційної влади
- Учень може проаналізувати роль Меджлісу та активістів
- Учень може оцінити зв'язок українців та кримських татар
content_outline:
- section: 'Вступ: Подвійні жертви'
  points:
  - 'Кримські татари: корінний народ Криму — загроза знищення ідентичності на рідній землі; культурна травма повторної втрати
    дому'
  - Депортація 1944 та повернення — історична травма, що повторюється у гібридних формах (викрадення, залякування, культурний
    тиск)
  - 'Нова окупація 2014: історія повторюється — [!history-bite] вбивство Решата Аметова (березень 2014) як перший акт терору
    проти одиночного пікету'
  words: 850
- section: Російська окупація та репресії
  points:
  - Заборона Меджлісу — [!context] визнання органу «екстремістським» (26 квітня 2016, затв. Верховним судом РФ 29 вересня)
    та криміналізація самоврядування
  - Арешти активістів та журналістів — [!myth-buster] сфабриковані справи «Хізб ут-Тахрір» як інструмент боротьби з інакомисленням
    (понад 100 переслідуваних)
  - Обшуки та переслідування — тактика залякування (обшуки о 4-й ранку), викрадення людей (справа Ервіна Ібрагімова) та психологічний
    терор родин
  - Примусова мобілізація — використання призову до армії РФ (з 2022) як інструменту етнічної чистки та «утилізації» нелояльного
    населення
  words: 850
- section: Спротив та еміграція
  points:
  - 'Меджліс в еміграції — діяльність у Києві та координація спротиву (лідери: Мустафа Джемілєв, Рефат Чубаров)'
  - Мустафа Джемілєв та Рефат Чубаров — лідери нації у вигнанні; цитата Чубарова про «вердикт на знищення» кримськотатарського
    народу
  - Кримськотатарський батальйон — створення добровольчого формування ім. Номана Челебіджіхана (2016) для захисту адмінкордону
  - Кримські татари на материковій Україні — збереження зв'язків та адвокація; феномен «вимушеного переміщення» замість «добровільного
    виїзду»
  - Міжнародна адвокація — [!culture] феномен «Кримської солідарності» та акція «Кримський марафон» (збір монет по 10 рублів
    на штрафи)
  words: 850
- section: Первинні джерела
  points:
  - Свідчення репресованих — [!quote] листи Нарімана Джеляла (перший заст. голови Меджлісу, арешт 2021) з в'язниці («Ми не
    зломлені...»)
  - Звіти правозахисних організацій — документація злочинів (ООН, Human Rights Watch, ZMINA, Кримськотатарський Ресурсний
    Центр)
  - Рішення міжнародних судів — ігнорування Росією вимог про скасування заборони Меджлісу як доказ правового нігілізму окупанта
  words: 850
- section: Деколонізаційний погляд
  points:
  - Геноцид корінного народу — концепція «гібридного геноциду» та політика заміщення населення (витіснення корінних, завезення
    колонізаторів)
  - 'Російський колоніалізм: паралелі з 1944 — [!decolonization] мета імперії одна: Крим без кримських татар; методи: від
    товарних вагонів до тюремних камер'
  - Українсько-кримськотатарська солідарність — спільний ворог та формування єдиної політичної нації; спільна трагедія як
    фактор єднання
  words: 850
- section: 'Підсумок: Боротьба триває'
  points:
  - Міжнародне визнання депортації як геноциду — дипломатичні перемоги України на світовій арені
  - Деокупація та повернення — Крим як невід'ємна частина України; відкидання будь-яких компромісів щодо статусу півострова
  - Майбутнє кримськотатарського народу — статус національно-територіальної автономії у вільному Криму як гарантія збереження
    нації
  words: 750
vocabulary_hints:
  required:
  - 'Меджліс (Mejlis) — єдиний легітимний представницький орган, заборонений окупантами у 2016; collocations: заборона Меджлісу,
    члени Меджлісу'
  - 'депортація (deportation) — у контексті 2014 року: «гібридна депортація» (вимушене витіснення); context: прихована депортація'
  - 'репресії (repressions) — системний тиск: обшуки, арешти, викрадення; collocations: масові репресії, політичні репресії'
  - 'окупація (occupation) — тимчасовий контроль РФ над півостровом; context: режим окупації, в умовах окупації'
  - 'корінний народ (indigenous people) — статус, закріплений законодавством України (на відміну від нацменшини); context:
    права корінного народу'
  - 'правозахисник (human rights defender) — активісти «Кримської солідарності», адвокати політв''язнів; collocations: переслідування
    правозахисників'
  - 'анексія (annexation) — спроба незаконного приєднання території; context: спроба анексії, невизнана анексія'
  - 'геноцид (genocide) — політика знищення ідентичності (етноцид/гібридний геноцид); context: визнання геноциду'
  recommended:
  - 'адвокація (advocacy) — міжнародна робота з захисту прав; collocations: міжнародна адвокація, адвокаційна кампанія'
  - 'мобілізація (mobilization) — примусовий призов до армії ворога (воєнний злочин); context: прихована мобілізація'
  - 'переслідування (persecution) — за релігійною та політичною ознаками («Хізб ут-Тахрір»); context: кримінальне переслідування'
  - 'солідарність (solidarity) — громадський рух підтримки («Кримська солідарність»); context: громадянська солідарність'
  - 'деокупація (de-occupation) — процес звільнення території; collocations: стратегія деокупації'
  - 'трибунал (tribunal) — вимога покарання організаторів репресій; context: міжнародний трибунал'
  - 'політв''язень (political prisoner) — особа, ув''язнена з політичних мотивів; collocations: список політв''язнів, допомога
    політв''язням'
activity_hints:
- type: reading
  focus: Свідчення репресованих кримських татар
  source: Правозахисні організації
  items: 4
- type: essay-response
  focus: Як історія депортації 1944 року повторюється після 2014?
connects_to:
- 'hist-133 (Війна 2022: початок)'
- hist-139 (Злочини і стійкість)
prerequisites:
- 'hist-131 (Крим 2014: анексія)'
persona:
  voice: Senior Professor of History
  role: Human Rights Lawyer
grammar:
- Теперішній та минулий час
- Юридична та правозахисна лексика
- Пасивні конструкції для опису репресій
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Кримські татари після 2014** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Кримські татари після 2014

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Кримські татари після 2014"
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
