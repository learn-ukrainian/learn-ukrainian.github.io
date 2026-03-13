# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-117
level: HIST
sequence: 117
slug: chornobyl
version: '2.0'
title: 'Чорнобиль: Трагедія і Попередження'
focus: history
pedagogy: CBI
phase: HIST.11 [Post-War Soviet Ukraine]
word_target: 5000
objectives:
- 'Analyze the causes and consequences of чорнобиль: трагедія і попередження'
- Evaluate the historical significance of мирний атом?
- Trace the development of деколонізаційний погляд
content_outline:
- section: Вступ — Мирний атом?
  points:
  - Pripyat as a Soviet model city of the future — founded Feb 4, 1970, 'City of Roses', average age 26, better supplies than
    Kyiv
  - The narrative of the 'safe' peaceful atom — Academician Alexandrov's claim that RBMK reactors were safe enough for Red
    Square; [!myth-buster] military origins (plutonium production) and critical design flaws kept secret from staff
  - Ukraine's role as the energy hub of the USSR — concentration of nuclear plants (Chornobyl, Rivne, South Ukraine, Zaporizhzhia,
    Khmelnytskyi) as the empire's 'atomic workshop'
  words: 1250
- section: Аварія 1986 року
  points:
  - 'The night of April 26: The explosion and the first firefighters — 01:23 am, two explosions destroyed 4th block during
    turbine rundown experiment; AZ-5 button fatal flaw led to reactor runaway; Pravyk and Kibenko''s guard worked on the roof
    without radiation protection'
  - The 36-hour delay in evacuation and the radioactive cloud — evacuation began April 27 at 14:00; [!history-bite] 'Red Forest'
    pines died instantly turning red; silence of Soviet media while Sweden (Forsmark NPP) detected radiation first
  - 'The ''Liquidators'': heroism and sacrifice of mobilized reservists — term ''biorobots'' for those clearing graphite from
    the roof manually (90 seconds max exposure); 600,000 people involved'
  - The construction of the Sarcophagus — 'Shelter' object built in 206 days (finished Nov 1986) under extreme radiation conditions
  words: 1250
- section: Первинні джерела
  points:
  - 'Transcripts of emergency calls to the fire station — [!quote] chaos and confusion: «— Алло! Це ВПЧ-2? ... 3-й, 4-й блок,
    горить дах!»'
  - The official announcement of evacuation (short, dry) — bureaucratic phrasing «неблагоприятная радиационная обстановка»
    (unfavorable radiation situation) vs. reality of deadly danger; people urged to take ID and food for 3 days
  - Excerpts from diaries of Pripyat residents — metallic taste in mouth ('iodine taste'), strange glow above the station,
    silence of radio
  words: 1250
- section: Деколонізаційний погляд
  points:
  - 'Moscow''s criminal silence: The May 1st Parade in Kyiv under radiation — [!decolonization] Gorbachev threatening Shcherbytsky
    («покладеш партквиток»); thousands of children exposed for imperial ''picture'' of calmness'
  - Colonial exploitation of Ukrainian territory for dangerous industries — center viewing Ukraine as a resource base/energy
    hub without regard for ecological risks to the local population
  - Chornobyl as the catalyst for the Ukrainian independence movement (eco-nationalism) — [!context] 'Green World' (Zelenyi
    Svit) movement; truth about Chornobyl became the first legal form of anti-Soviet protest
  - The Exclusion Zone as a nature reserve and tourist site — [!culture] nature reclaiming the territory; tourism as a method
    of trauma processing and historical memory
  - The spiritual trauma of the nation — silence, lies, and the total loss of trust in the Soviet system
  - Chornobyl in modern pop culture (HBO series, STALKER game) — global visualization of the Ukrainian tragedy; from 'Zone'
    of death to cultural phenomenon
  words: 1250
vocabulary_hints:
  required:
  - історія (history) — новітня історія (modern history); переписувати історію (to rewrite history)
  - держава (state) — тоталітарна держава (totalitarian state); інтереси держави (state interests)
  - народ (people) — український народ (Ukrainian people); злочин проти народу (crime against the people)
  - влада (power/authorities) — радянська влада (Soviet authorities); злочинна недбалість влади (criminal negligence of authorities)
  - період (period) — радянський період (Soviet period); період напіврозпаду (half-life period)
  - подія (event) — трагічні події (tragic events); хронологія подій (chronology of events)
  - джерело (source) — першоджерело (primary source); джерело радіації (radiation source)
  - спадщина (heritage/legacy) — важка спадщина (heavy legacy); культурна спадщина (cultural heritage)
  recommended:
  - аналіз (analysis) — критичний аналіз (critical analysis); аналіз причин (analysis of causes)
  - контекст (context) — історичний контекст (historical context); у контексті подій (in the context of events)
  - вплив (influence/impact) — вплив радіації (radiation impact); екологічний вплив (ecological impact)
  - наслідки (consequences) — ліквідація наслідків (liquidation of consequences); довготривалі наслідки (long-term consequences)
  - вибух (explosion) — ядерний вибух (nuclear explosion); причина вибуху (cause of explosion)
  - евакуація (evacuation) — термінова евакуація (urgent evacuation); зона евакуації (evacuation zone)
  - радіація (radiation) — рівень радіації (radiation level); радіаційний фон (radiation background)
  - зона (zone) — зона відчуження (exclusion zone); 30-кілометрова зона (30-kilometer zone)
activity_hints:
- type: reading
  focus: Первинні джерела
  items: 4
- type: essay-response
  focus: Критичний аналіз
- type: critical-analysis
  focus: Аналіз причинно-наслідкових зв'язків між подіями
  items: 3
- type: critical-analysis
  focus: Критична оцінка історичних тверджень та міфів
  items: 5
prerequisites: '[]'
persona:
  voice: Senior Professor of History
  role: Plant Engineer
learning_outcomes: '[]'
connects_to:
- diaspora

```

---

## PART 1: Deep Research

Research **Чорнобиль: Трагедія і Попередження** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Чорнобиль: Трагедія і Попередження

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Чорнобиль: Трагедія і Попередження"
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
