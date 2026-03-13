# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-046
level: HIST
sequence: 46
slug: khotynska-viyna
version: '2.0'
title: 'Хотинська війна 1621: Козацький щит Європи'
subtitle: The Battle That Saved Christian Civilization
focus: history
pedagogy: CBI
phase: HIST.5 [Rise of Cossacks]
word_target: 5000
objectives:
- Learner can describe the causes and scale of the Khotyn War of 1621
- Learner can analyze the tactical role of cossack infantry in the victory
- Learner can understand the geopolitical consequences of the battle for Europe
content_outline:
- section: Вступ
  points:
  - 'The geopolitical context: Ottoman expansion — Ambition of Osman II: revival of Suleiman''s grandeur; ''breakfast in Vienna,
    lunch in Rome'' context'
  - The disaster at Cecora (1620) as a prelude — Stanisław Żółkiewski's defeat and death; panic in Warsaw; King Sigismund
    III ready to flee; [!context] Пояснити масштаб загрози
  words: 600
- section: 'Мобілізація сил: Підготовка до апокаліпсису'
  points:
  - Sultan Osman II's grand army — 150-200k troops (Ottomans + Tatars) vs 76k allies (41k Cossacks)
  - The desperate situation of Poland-Lithuania — The mission of Patriarch Theophanes; legitimization of Cossack hierarchy
  - The cossack council and Sahaidachnyi's decision — Council at Sukha Dibrova (June 1621); 40k Cossacks; demand for religious
    rights; Sahaidachnyi's breakthrough to Warsaw; [!myth-buster] Козаки не були 'найманцями'
  words: 600
- section: 'Тактика і Стратегія: Секрети перемоги'
  points:
  - The layout of the camp and fortifications — Cossacks entrenched faster than Poles; the 'tabor' wagon fort impregnable
    to cavalry; [!history-bite] 'Табір' як неприступна фортеця
  - The decisive role of the cossack 'tabor' and artillery — Volley fire tactics (шеренги); night raids ('вилагазки') creating
    psychological terror
  - 'Logistics and survival in the camp — Contrast: Ottoman luxury vs Ally asceticism; disease and hunger in besieged camp
    (eating horses, lack of water)'
  words: 600
- section: 'Читання: Свідчення очевидця'
  points:
  - 'Analysis of Jakub Sobieski''s diary — Quote: ''True victors were Cossacks''; description of ''rain of lead''; [!quote]
    Яків Собеський про ''дощ зі свинцю'''
  words: 600
- section: 'Герої та Жертви: Ціна перемоги'
  points:
  - The leadership of Petro Sahaidachnyi — Commanded while mortally wounded (poisoned arrow); effective leader after Chodkiewicz's
    death (Sept 24); [!biography] Петро Сагайдачний
  - 'The psychological breaking point of the Ottoman army — Janissary mutiny; Osman II''s shock: ''I can only destroy them,
    not defeat them'' (apocryphal)'
  words: 600
- section: Геополітичні наслідки та пам'ять
  points:
  - The decline of the Ottoman Empire — Start of Janissary corps decline; assassination of Osman II in Istanbul
  - The rise of the Cossack myth in Europe — Ivan Gundulić's poem 'Osman'; Europe applauded 'Polish victory' ignoring Cossacks
  - Khotyn in Ukrainian literature and art — Kasiyan Sakovych's 'Verses on the Sorrowful Funeral of Sahaidachnyi'
  words: 600
- section: Первинні джерела
  points:
  - Excerpts from the Khotyn Chronicle — Hryhoriy Hrubyanka's chronicle; descriptions of Cossack valor
  - Letters of the Sultan — Ottoman chronicles (Naima) about 'infidel Cossacks brought by Shaitan'
  - 'Cossack chronicles on Khotyn — Sahaidachnyi''s letter to the King: demand for Orthodox rights; [!source] Уривок з листа
    Сагайдачного до короля'
  words: 600
- section: Деколонізаційний погляд
  points:
  - Ukraine as a subject of international politics — Sahaidachnyi as equal partner to the King; 'Shield of Europe' concept
  - 'Debunking the myth of ''Polish victory'' — Polish historiography credits Chodkiewicz/Hussars; reality: Cossack infantry
    bore the brunt'
  - 'European context: The Thirty Years'' War — While Europe destroyed itself, Ukraine held the Eastern front; ''Betrayal''
    after victory led to Khmelnytsky Uprising; [!analysis] Чому перемога під Хотином стала початком кінця Речі Посполитої?'
  words: 800
vocabulary_hints:
  required:
  - історія (history) — історія війн (history of wars)
  - держава (state) — козацька держава (cossack state)
  - народ (people) — український народ (Ukrainian people)
  - влада (power) — військова влада (military power)
  - період (period) — історичний період (historical period)
  - подія (event) — вирішальна подія (decisive event)
  - джерело (source) — первинне джерело (primary source)
  - спадщина (heritage) — героїчна спадщина (heroic heritage)
  recommended:
  - аналіз (analysis) — критичний аналіз (critical analysis)
  - контекст (context) — історичний контекст (historical context)
  - вплив (influence) — геополітичний вплив (geopolitical influence)
  - наслідки (consequences) — трагічні наслідки (tragic consequences)
activity_hints:
- type: reading
  focus: Eye-witness accounts of the battle intensity
- type: essay-response
  focus: The strategic importance of the cossack factor in the victory
- type: comparative-study
  focus: Ottoman vs. Cossack military tactics
- type: critical-analysis
  focus: 'The political aftermath: Peace treaty and broken promises'
persona:
  voice: Senior Professor of History
  role: Infantry Commander
grammar:
- 'Historical narrative: detailed battle descriptions'
- Military terminology and formations
register: публіцистичний
prerequisites:
- petro-sahaidachnyi
connects_to:
- kozatska-kultura

```

---

## PART 1: Deep Research

Research **Хотинська війна 1621: Козацький щит Європи** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Хотинська війна 1621: Козацький щит Європи

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Хотинська війна 1621: Козацький щит Європи"
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
