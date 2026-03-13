# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-082
level: B1
sequence: 82
slug: regions-south
version: '2.0'
title: 'Українські регіони: Південь'
subtitle: Southern Ukraine - Black Sea Coast and Steppe Heritage
focus: culture
pedagogy: CBI
phase: B1.7 [Contemporary Ukraine]
word_target: 4000
objectives:
- Learner can discuss Southern Ukraine's geography and coastal culture
- Learner can understand authentic texts about Odesa, Mykolaiv, and Kherson
- Learner can use regional vocabulary to describe Southern Ukrainian traditions
- Learner can compare Southern Ukraine with other regions
content_outline:
- section: 'Вступ: Море та Степ (Introduction: Sea and Steppe)'
  words: 600
  points:
  - Introduction to the Southern identity defined by the duality of the Black Sea (Chorne more) and the Sea of Azov (Azovske
    more) coasts (§3.14)
  - Defining the 'Steppe' (Степ) and its historical role as the 'Wild Field' (Дике Поле) — a land of freedom where the wind
    meets the waves
  - 'Geographic deep-dive: explaining ''Estuaries'' (Лимани) as a defining feature of the Southern landscape and their ecological
    importance'
- section: Одеса — Перлина Чорного моря (Odesa — Pearl of the Black Sea)
  words: 1000
  points:
  - 'Odesa''s founding and its multicultural DNA: how Ukrainian, Jewish, Greek, and Italian influences created a unique linguistic
    melting pot'
  - 'Linguistic analysis of Odesa Humor: the story behind the phrase «Вода — не фонтан» and the role of paradoxical phrasing
    and self-irony (самоіронія)'
  - 'Spelling and identity: master the Ukrainian spelling ''Odesa'' (single ''s'') to avoid common learner errors based on
    Russian transliteration'
- section: Від Миколаєва до Олешківських пісків (From Mykolaiv to Oleshky Sands)
  words: 1000
  points:
  - 'Mykolaiv as the ''City of Shipbuilders'' (корабели): the story of the frigate ''Saint Nicholas'' (1790) and the city''s
    maritime layout'
  - 'The ''Ukrainian Sahara'': exploring the Oleshky Sands (Олешківські піски) in the Kherson region, Europe''s largest sand
    mass with 5-meter dunes (§3.13)'
  - 'State Standard §3.13: Identification of key tourist attractions, from Kherson''s river ports to the unique flora of the
    artificially planted Southern forests'
- section: Крим та кримськотатарська спадщина (Crimea and Crimean Tatar Heritage)
  words: 800
  points:
  - 'Crimean Tatar culture: the symbolic language of ''Ornek'' (UNESCO heritage) featuring the rose (woman), tulip (man),
    and carnation (elder) symbols'
  - 'Historical weight: a respectful discussion of the 1944 Deportation (депортація) and its impact on the region''s demography
    and national memory'
  - 'The contemporary narrative of de-occupation: why the return of Crimea to the Black Sea family is a central national goal'
- section: Практика та мовні нюанси (Practice and Linguistic Nuances)
  words: 400
  points:
  - 'Learner error drill: master the preposition ''на'' for cardinal directions («на півдні») versus the incorrect usage of
    ''в'' («в півдні»)'
  - 'Directional cases mastery: contrast ''Я їду на море'' (Destination/Accusative) with ''Я на морі'' (Location/Locative)
    through 15 minimal-pair exercises'
  - 'Regional naming conventions: distinguishing ''В Одесі'' (City) from ''На Одещині'' (Region) to ensure proper prepositional
    agreement'
- section: 'Підсумок: Туристичні принади Півдня (Summary: Tourist Attractions of the South)'
  words: 200
  points:
  - Synthesis of Southern 'Resorts' (Курорти) and their economic/cultural importance in modern Ukraine (§3.5)
  - 'Closing reflections: the persona (Odesa Tour Guide) invites the learner to see the South as Ukraine''s vibrant ''Window
    to the World'''
vocabulary_hints:
  required:
  - Одеса (Odesa) — single 's'; перлина Чорного моря; high frequency
  - Миколаїв (Mykolaiv) — місто-корабель; center of shipbuilding
  - Херсон (Kherson) — ворота до Олешківських пісків; maritime hub
  - узбережжя (coast) — чорноморське узбережжя, відпочинок на узбережжі; high frequency
  - порт (port) — морський порт, порт-хаб; vital for trade
  - степ (steppe) — широкий степ, Дике Поле; cultural and geographic anchor
  - торгівля (trade) — морська торгівля; economic driver of the region
  - курорт (resort) — морський курорт, курортний сезон; State Standard §3.13
  - лиман (estuary) — Дніпровський лиман; specific Southern geographic feature
  recommended:
  - суднобудування (shipbuilding) — миколаївські корабели, спустити на воду; professional heritage
  - кримські татари (Crimean Tatars) — корінний народ, орнамент Орьнек; indigenous heritage
  - багатокультурний (multicultural) — багатокультурна Одеса; describes the regional melting pot
  - рибальство (fishing) — традиційне рибальство; coastal economy and lifestyle
  - депортація (deportation) — трагедія 1944 року; historical context for Crimea
  - самоіронія (self-irony) — одеська самоіронія; key to understanding regional humor
  - бархан (dune) — піщаний бархан; relevant for Oleshky Sands descriptions
activity_hints:
- type: reading
  focus: Authentic texts about Southern Ukraine
  items: 15
- type: match-up
  focus: Match cities to characteristics
  items: 20
- type: fill-in
  focus: Complete regional descriptions
  items: 15
- type: quiz
  focus: Discuss Southern Ukrainian culture
  items: 10
connects_to:
- 'b1-83 (Українські регіони: Центр)'
prerequisites:
- 'b1-81 (Українські регіони: Схід)'
persona:
  voice: Senior Language & Culture Specialist
  role: Odesa Tour Guide
grammar:
- Reading comprehension strategies
- Cultural vocabulary in context
- Geographic and maritime vocabulary
register: розмовний

```

**Level constraints quick-ref:**

```
# B1 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. Grammar explained IN Ukrainian. English only for disambiguation of false friends. Sentences max 30 words.`, etc.

## Grammar Scope

**Allowed:** All grammar constructions. Participles. Complex subordinate clauses.
Max 30 words per Ukrainian sentence. Max 4 clauses.

## Immersion Strategy (B1)

| Phase | Modules | Immersion | Notes |
|-------|---------|-----------|-------|
| B1.0 (Bridge) | M01-05 | Mixed | Teach grammar metalanguage; English scaffolding for abstract concepts |
| B1.1+ (Core) | M06-92 | **100%** | Full Ukrainian. English ONLY in vocabulary table translations |

**B1.0 Bridge modules:** English grammar term explanations allowed as transition from A2.

**B1.1+ Hard rule:** No English in prose, titles, callouts, or explanations.
No English in parentheses to clarify Ukrainian concepts:
- Wrong: **поки** — дія на тлі іншої дії (While she was cooking...)
- Right: **поки** — дія на тлі іншої дії, тобто одночасні процеси

## B1-Specific Writing Notes

- Content quality: equal treatment for all items in a category (same depth, same format)
- Example variety: mix standalone, table, inline, dialogue — no 5+ consecutive examples in same format
- Tables must have narrative context (2+ sentences before and after)
- Parallel sections use identical internal structure

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `B1` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Українські регіони: Південь** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

### Your RAG Tools

| Tool | When to use |
|------|-------------|
| `search_text` | Find how this topic is taught in Ukrainian textbooks |
| `verify_words` | Check vocabulary exists in VESUM dictionary |
| `query_grac` mode=`frequency` | Get word frequency data |
| `query_wikipedia` mode=`summary` | Quick fact-check for cultural hooks |

### Research Requirements

1. **State Standard Reference**: Look up the §section in `state-standard-2024-mapping.yaml`, then read ONLY that section from `UKRAINIAN-STATE-STANDARD-2024.txt`. Quote the relevant requirement.
2. **Vocabulary Frequency**: Use `query_grac` (mode=`frequency`) for key vocabulary items. Do NOT rely on memory alone.
3. **Cultural Hook**: Use `query_wikipedia` to find 1-2 verified cultural facts to anchor the lesson.
4. **Cross-References**: Note which modules this builds on and prepares for (check the plan's `connects_to` field).
5. **Common Errors**: Identify 2-3 common learner mistakes for this grammar point/topic.

### Decolonized Framing

When researching, frame Ukrainian independently — **never as a derivative or variant of Russian:**
- Describe Ukrainian features positively ("Ukrainian has...", "Ukrainian uses...")
- Do NOT use Russian as the baseline for comparisons ("Unlike Russian...", "Different from Russian...")
- If comparing language systems is useful, use non-Russian languages (Polish, Portuguese, etc.)
- Note how topics have been historically misframed by Russian/Soviet sources and provide the Ukrainian-centric perspective

### Research Output Cap
Keep research notes under **1500 words**. Focus on density: facts, dates, quotes, tables — not prose.

### Additional for Core B (B1.6+, B2, C1, C2, PRO)

- Domain-specific vocabulary collocations from professional glossaries (PRO tracks)
- Stylistic/dialectal features from academic sources (C2)
- Register distinctions (formal vs. informal usage)

## Downstream Audit Gates (Phase B content will be checked for)

Plan your outline knowing that Phase B content must pass these gates:
- **Word count**: minimum **4000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Українські регіони: Південь

## State Standard Reference
§{section_number}: "{quoted requirement}"
Alignment: {how this module addresses the standard}

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| ...  | ...               | ...              |

## Cultural Hooks
1. {Verified fact with source}
2. {Verified fact with source}

## Common Learner Errors
1. {Error pattern} → {Correct form} — {Why it happens}
2. ...

## Cross-References
- Builds on: {module slugs}
- Prepares for: {module slugs}

## Multimedia Resources
(If you naturally encountered relevant Ukrainian-language YouTube videos or audio resources during your web research, note them here. Do NOT search specifically for videos — the discover phase handles that. Maximum 3 entries.)
- {Channel — Title — URL — 1-sentence relevance note}
- (none encountered)

## Notes for Content Writing
- {Any additional observations for Phase B}

===RESEARCH_END===
```

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | STATE_STANDARD_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT fabricate State Standard references — if you can't find the exact §, say so
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
