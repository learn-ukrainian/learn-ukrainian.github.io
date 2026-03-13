# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-114
level: HIST
sequence: 114
slug: shistdesiatnyky
version: '2.0'
title: 'Шістдесятники: Бунт проти сірості'
focus: history
pedagogy: CBI
phase: HIST.11 [Post-War Soviet Ukraine]
word_target: 5000
objectives:
- 'Analyze the causes and consequences of шістдесятники: бунт проти сірості'
- Evaluate the historical significance of хрущовська відлига
- Trace the development of деколонізаційний погляд
content_outline:
- section: Вступ — Хрущовська відлига
  points:
  - The death of Stalin and the partial liberalization of the regime — context of the 20th Congress of the CPSU (1956) and
    the 'thaw' as a brief respite between terror and stagnation
  - 'The emergence of a new generation of intellectuals who demanded truth — young intelligentsia who believed in ''socialism
    with a human face''; engagement hook: [!context] ''Відлига'' не була справжньою свободою'
  - 'The Club of Creative Youth ''Suchasnyk'' in Kyiv — founded in 1959 at Zhovtnevyi Palace; organizers: Les Tanyuk, Alla
    Horska, Viktor Zaretsky; activities: literary evenings, searching for NKVD victims in Bykivnia'
  words: 1250
- section: Культурний вибух
  points:
  - 'Literature: Vasyl Symonenko, Lina Kostenko, Ivan Drach — works like ''Tysha i hrim'', ''Prominnia zemli'', ''Nizh u sontsi'';
    focus on metaphorical, intellectual, and sincere new quality of word'
  - 'Cinema: Serhiy Parajanov and ''Shadows of Forgotten Ancestors'' — 1964 masterpiece; poetic cinema vs. socrealism; world
    recognition (Argentina, Italy) vs. suspicion at home'
  - 'Art: Alla Horska and the destroyed stained glass window at Kyiv University — ''Shevchenko. Mother'' (1964); destroyed
    by hammer on rector''s orders; engagement hook: [!culture] authorities feared art more than weapons'
  - 'The premiere of ''Shadows'' (1965) as the first public political protest — Sept 4, 1965 at cinema ''Ukraina''; Dzyuba''s
    call ''Who is against tyranny — stand up!''; engagement hook: [!history-bite] only ~50-60 people stood up, but it changed
    history'
  words: 1250
- section: Первинні джерела
  points:
  - 'Excerpts from Vasyl Symonenko''s diary (''Bereh chekan'') — specifically the diary ''Okraitsi dumok'' (1962-1963); quote:
    «Немає нічого страшнішого за необмежену владу...»; engagement hook: [!quote] Symonenko''s disappointment'
  - 'Fragments from Ivan Dzyuba''s treatise ''Internationalism or Russification?'' — 1965 samvydav text sent to leadership;
    engagement hook: [!decolonization] Dzyuba used Marxism to prove Russification contradicted communism'
  - KGB memos reporting on 'bourgeois nationalism' among youth — documenting 'crimes' like caroling, wearing vyshyvankas,
    and speaking Ukrainian in public
  words: 1250
- section: Деколонізаційний погляд
  points:
  - The fight for the Ukrainian language as a political act — speaking Ukrainian in Russified Kyiv as a conscious choice and
    resistance
  - 'Debunking the myth of ''Soviet People'' (homo sovieticus) — the myth as a tool of assimilation; engagement hook: [!myth-buster]
    Sixtiers proved Ukrainian identity was modern and urban, not ''archaic'''
  - 'The regime''s response: The arrests of 1965 and the ''Great Pogrom'' of 1972 — first wave (1965) as intimidation; Operation
    ''Block'' (Jan 1972) targeting Stus, Chornovil, Sverstiuk'
  - The transformation of cultural figures into political dissidents — the shift from culturalism to political opposition
    after the 1965 protest
  - 'The continuity of resistance: From UPA to Sixtiers to the Helsinki Group — bridging armed resistance and human rights
    movement; preserving the national ''genetic code'''
  - The lasting impact on modern Ukrainian culture — creating a high, elite, urban culture that integrated Ukraine into the
    world context
  words: 1250
vocabulary_hints:
  required:
  - історія (history) — переписувати історію (to rewrite history)
  - держава (state) — тоталітарна держава (totalitarian state)
  - народ (people) — радянський народ (Soviet people — myth), український народ (Ukrainian people)
  - влада (power) — радянська влада (Soviet power), необмежена влада (unlimited power)
  - період (period) — період застою (period of stagnation)
  - подія (event) — історична подія (historical event)
  - джерело (source) — первинне джерело (primary source)
  - спадщина (heritage) — культурна спадщина (cultural heritage)
  recommended:
  - аналіз (analysis) — критичний аналіз (critical analysis)
  - контекст (context) — історичний контекст (historical context)
  - вплив (influence) — ідеологічний вплив (ideological influence)
  - наслідки (consequences) — трагічні наслідки (tragic consequences)
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
  role: Samvydav Editor
learning_outcomes: '[]'
connects_to:
- ukrainska-helsinska-hrupa

```

---

## PART 1: Deep Research

Research **Шістдесятники: Бунт проти сірості** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Шістдесятники: Бунт проти сірості

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Шістдесятники: Бунт проти сірості"
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
