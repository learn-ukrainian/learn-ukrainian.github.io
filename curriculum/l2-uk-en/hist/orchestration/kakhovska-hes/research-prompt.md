# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-135
level: HIST
sequence: 135
slug: kakhovska-hes
version: '2.0'
title: 'Каховська ГЕС: Екоцид'
subtitle: 'Kakhovka Dam: Ecocide'
focus: history
pedagogy: CBI
phase: HIST.13 [Russian Aggression]
word_target: 5000
objectives:
- Учень може описати знищення Каховської ГЕС та його наслідки
- Учень може пояснити екологічну катастрофу
- Учень може проаналізувати екоцид як воєнний злочин
- Учень може обговорити довготривалі наслідки для регіону
content_outline:
- section: 'Вступ: 6 червня 2023'
  points:
  - 'Підрив греблі: що сталося — 02:50 ночі, внутрішній підрив у машинній залі (сейсмічні дані NORSAR); include quote from
    [BBC News Україна]'
  - 'Каховська ГЕС: історія та значення — «Великий план перетворення природи» (1950), затоплення історичного Великого Лугу
    (Січей)'
  - Чому це — безпрецедентний злочин — свідомий екоцид, найбільша техногенна катастрофа в Європі за десятиліття
  words: 850
- section: Катастрофа
  points:
  - Хронологія подій — від вибуху 6 червня до зникнення водосховища 18 червня
  - 'Затоплення: масштаб та швидкість — хвиля 4-5 метрів, 80 населених пунктів у зоні лиха, 6800 км² забруднено'
  - Евакуація населення — ~40 тис. людей у зоні ризику, виклики окупації лівого берега
  - Загиблі та зниклі безвісти — розмиті кладовища та скотомогильники
  - Знищення інфраструктури — зруйновано 11 прольотів та машинну залу; відновленню не підлягає
  words: 850
- section: Екологічні наслідки
  points:
  - 'Знищення Каховського водосховища — феномен повернення Великого Лугу; cultural hook: «Козацька Атлантида» (Довженко)'
  - Загибель флори та фауни — 150 тонн мастила у воді, масовий мор риби, знищення ендеміків (мурахи Нижньодніпровських пісків)
  - 'Загроза для Криму: питна вода — втрата джерела водопостачання'
  - Ризики для Запорізької АЕС — загроза системі охолодження
  - Довготривалі наслідки для сільського господарства — втрата зрошення для Херсонщини та Запоріжжя (пустелізація vs заліснення)
  words: 850
- section: Первинні джерела
  points:
  - Свідчення жителів затоплених міст — спогади про «день народження» ГЕС (1955) vs день її смерті (2023)
  - Звіти екологічних організацій — Texty.org.ua про швидке відновлення вербових лісів (сукцесія)
  - Супутникові знімки — моніторинг зміни ландшафту (з води у ліс)
  words: 850
- section: Екоцид як воєнний злочин
  points:
  - Визначення екоциду в міжнародному праві — «свідоме знищення середовища існування» (Офіс Генпрокурора)
  - Докази російської відповідальності — контроль станції з лютого 2022, дані ГУР про замінування восени 2022
  - Перспективи правосуддя — кваліфікація як воєнний злочин та екоцид
  words: 850
- section: 'Підсумок: Відбудова'
  points:
  - 'Масштаб необхідної відбудови — дебати: відновлювати ГЕС чи зберегти Великий Луг (історична справедливість vs енергетика)'
  - Міжнародна допомога — реакція світу на катастрофу
  - 'Екологічна відновлення — «природа забирає своє»: унікальний природний експеримент'
  words: 750
vocabulary_hints:
  required:
  - гребля (dam) — підрив греблі, руйнування греблі
  - екоцид (ecocide) — вчинити екоцид, наслідки екоциду
  - затоплення (flooding) — зона затоплення, наслідки затоплення
  - водосховище (reservoir) — Каховське водосховище, дно водосховища
  - екологічна катастрофа (ecological disaster) — масштаби катастрофи
  - інфраструктура (infrastructure) — критична інфраструктура
  - евакуація (evacuation) — примусова евакуація, евакуаційні маршрути
  - відбудова (reconstruction) — плани відбудови, повоєнна відбудова
  recommended:
  - гідроелектростанція (hydroelectric power plant) — машинна зала ГЕС
  - зрошення (irrigation) — система зрошення, втрата зрошення
  - біорізноманіття (biodiversity) — втрата біорізноманіття
  - забруднення (pollution) — хімічне забруднення, забруднення води
  - ґрунтові води (groundwater) — рівень ґрунтових вод
  - екосистема (ecosystem) — відновлення екосистеми
  - Великий Луг (Velykyi Luh) — історична місцевість, повернення Великого Лугу
  - сукцесія (succession) — екологічна сукцесія, відновлення рослинності
activity_hints:
- type: reading
  focus: Свідчення постраждалих від затоплення
  source: Українські медіа
  items: 4
- type: essay-response
  focus: Чому знищення Каховської ГЕС — це екоцид?
connects_to:
- hist-136 (Воєнна економіка)
- hist-139 (Злочини і стійкість)
prerequisites:
- hist-134 (Буча та Ірпінь)
persona:
  voice: Senior Professor of History
  role: Environmental Inspector
grammar:
- Минулий час для опису подій
- Теперішній час для наслідків
- Екологічна та юридична лексика
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Каховська ГЕС: Екоцид** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Каховська ГЕС: Екоцид

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Каховська ГЕС: Екоцид"
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
