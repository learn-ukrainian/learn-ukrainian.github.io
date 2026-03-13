# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

> **Focus on**: `title`, `content_outline`, `objectives`, `vocabulary_hints`, `connects_to`, `prerequisites`.
> **Ignore for research**: `grammar`, `register`, and voice/role fields — these are used in later phases, not research. Do NOT reference persona or voice instructions.

```yaml
module: hist-047
level: HIST
sequence: 47
slug: kozatska-kultura
version: '2.0'
title: Козацька культура — кобзарі, думи та бароко
subtitle: 'Cossack Culture: Kobzars, Dumas, and Baroque'
focus: history
pedagogy: CBI
phase: HIST.5 [Rise of Cossacks]
word_target: 5000
objectives:
- Learner can explain the role of kobzars in preserving national memory
- Learner can analyze the genre of dumas as a unique Ukrainian epic
- Learner can characterize Cossack Baroque and its geopolitical significance
sources:
- name: History of Ukrainian Culture
  url: https://litopys.org.ua/istkult/istkult.htm
  type: reference
  notes: Comprehensive overview of the era
- name: Cossack Baroque - Encyclopedia of Ukraine
  url: https://www.encyclopediaofukraine.com/display.asp?linkpath=pages%5CB%5CA%5CBaroque.htm
  type: reference
  notes: Detailed description of the style
content_outline:
- section: Вступ та Контекст
  points:
  - 'Cultural intersection: East and West — synthesis of Western European influences and Byzantine-Rus traditions; not passive
    borrowing but active creation'
  - The Golden Age of Hetmanate culture — [!context] Ukrainian Baroque was a dialogue where tradition reimagined European
    forms; period of 1687 (Mazepa's election) marked the peak
  words: 550
- section: 'Кобзарі та лірники: голос народу'
  points:
  - The guild system (cekhy) and hierarchy — organized brotherhoods with statutes, treasury, courts, and strict hierarchy
    (masters, apprentices)
  - 'Lebiiska language: the secret code — [!history-bite] kobzars used a secret argot (''lebiiska'') for safety and preserving
    guild secrets'
  - Social and political functions of kobzars — not beggars but professional performers; acted as 'live newspapers', moral
    authorities, and sometimes scouts
  words: 550
- section: 'Українські Думи: Духовний хребет нації'
  points:
  - The uniqueness of the genre (recitative) — [!culture] dumas were chanted, not sung, allowing for improvisation based on
    audience reaction (like jazz)
  - Improvisation and emotional depth — focus on themes of captivity, escape, and death (e.g., 'Дума про Марусю Богуславку')
  - The role of dumas in shaping language — formed the national ethos and historical consciousness of the illiterate population
  words: 550
- section: 'Козацьке бароко: Тріумф національного стилю'
  points:
  - 'Differences from Western Baroque — [!decolonization] reverse influence vector: Ukrainian masters brought Baroque to Muscovy
    (''Naryshkin Baroque'')'
  - Symbolism and decorative richness — pear-shaped domes, 'torn' pediments, lush stucco decor with plant motifs (grapes,
    sunflowers)
  - Major architectural monuments — Troitska Church (Hustyn), Pokrovsky Cathedral (Kharkiv), Vydubychi Monastery (Kyiv)
  words: 550
- section: 'Мистецтво: Феномен козацького бароко'
  points:
  - Synthesis of Western and Byzantine traditions — combination of masonry architecture of the princely era with Baroque splendor
  - Architecture (Mazepa baroque) — term emphasizing the hetman's role; massive reconstruction of ancient temples (Sophia,
    St. Michael's)
  - Portraiture (Parsuna) — transition from iconography to secular portrait; flat and static but with individual features
    (e.g., portraits of Khmelnytsky, Sulyma)
  words: 550
- section: Меценатство як державна стратегія
  points:
  - 'The role of Ivan Mazepa and other hetmans — [!myth-buster] Mazepa was not a ''greedy traitor'' but spent millions on
    40+ churches and schools; quote: «Все гине там, де володар не є готовий... захищати свою владу»'
  - Legitimizing the state through art — church construction legitimized the hetman as defender of the faith; support extended
    to Athos, Jerusalem, Syria (1708 Arabic Gospel)
  words: 550
- section: 'Інтелектуальний центр: Києво-Могилянська академія'
  points:
  - Petro Mohyla's reforms — [!quote] «Гарно й почесно бути свічкою... але свічка має світити»; 1632 merger of Lavra and Brotherhood
    schools
  - The seven liberal arts and Latin education — 12-year course, Latin as language of science; focus on poetics, rhetoric,
    drama
  - Impact on the entire Eastern European region — graduates (spudei) formed the elite of the Hetmanate and Empire (Prokopovych,
    Yavorsky)
  words: 550
- section: Первинні джерела та Читання
  points:
  - Analysis of Dumas and Academy statutes — examine structure of dumas and student requirements in statutes
  words: 550
- section: Деколонізаційний погляд
  points:
  - Debunking the 'peasant culture' myth — Hetmanate had high elite culture integrated into Europe; distinct from Russian
    isolationism before Peter I
  - Imperial appropriation of Ukrainian achievements — Kyiv as a donor of culture to Moscow (transfer of ideas, styles, personnel)
  words: 600
vocabulary_hints:
  required:
  - кобзар (kobzar/minstrel) — professional performer, member of a guild, keeper of 'lebiiska' secret language
  - бандура (bandura) — multi-stringed instrument used for accompanying dumas
  - дума (duma/epic poem) — recitative heroic poem, distinct from songs; 'Дума про Марусю Богуславку'
  - козацьке бароко (Cossack Baroque) — unique synthesis of Western and Byzantine styles; 'pear-shaped domes'
  - меценатство (patronage) — Mazepa's state strategy of funding arts/church; 'build the state'
  - речитатив (recitative) — chanting style of duma performance, allows improvisation
  - лебійська мова (Lebiiska language) — secret argot of kobzars used for safety
  - спудей (spudei/student) — student of Kyiv-Mohyla Academy; future elite
  - епос (epic) — heroic narrative poetry; distinct from byliny
  - фасад (facade) — architectural front, often with 'torn' pediments in Baroque
  recommended:
  - парсуна (parsuna) — early secular portrait retaining iconographic flatness
  - цех (guild) — professional organization of kobzars with courts and treasury
  - грушоподібний (pear-shaped) — characteristic shape of Ukrainian Baroque domes
  - баня (dome) — architectural feature of churches
  - ліпнина (stucco molding) — decorative element with plant motifs
activity_hints:
- type: reading
  focus: Linguistic analysis of Duma texts and Academy rules
- type: essay-response
  focus: The impact of kobzarstvo on national identity
- type: comparative-study
  focus: Cossack Baroque vs. Western Baroque styles
- type: critical-analysis
  focus: 'Верифікація фактів: Facts about education and guilds'
  items: 4
persona:
  voice: Senior Professor of History
  role: Wandering Kobzar
grammar:
- 'Historical narrative: cultural synthesis'
- Artistic and academic terminology
register: публіцистичний
prerequisites:
- khotynska-viyna
connects_to:
- kozatske-viisko

```

---

## PART 1: Deep Research

Research **Козацька культура — кобзарі, думи та бароко** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Козацька культура — кобзарі, думи та бароко

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — review phase verifies prose against this -->
```yaml
subject: "Козацька культура — кобзарі, думи та бароко"
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
