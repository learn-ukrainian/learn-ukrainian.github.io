# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-051
level: A2
sequence: 51
slug: home-and-furniture
version: '2.0'
title: Home and Furniture
subtitle: Where I Live
focus: vocabulary
pedagogy: PPP
phase: A2.5 [Vocabulary Expansion]
word_target: 2000
objectives:
- Learner can name rooms in a house
- Learner can describe furniture and appliances
- Learner can say where things are located
- Learner can describe their own home
content_outline:
- section: 'Вступ: Типи житла та помешкання (Introduction: Types of Housing)'
  words: 325
  points:
  - 'State Standard §3.2 compliance: Differentiating between ''квартира'' (apartment) and ''приватний будинок'' (private house)
    as primary housing types.'
  - Introduce the 'Room Map' visual concept to group vocabulary by function (living, sleeping, cooking) for logical retention.
  - 'Cultural motivator: The folklore of ''Domovyk'' (household spirit) who protects the home and lives behind the stove or
    in a corner.'
- section: 'Презентація: Кімнати та меблі (Presentation: Rooms and Furniture)'
  words: 525
  points:
  - 'Essential furniture list based on frequency: ''стіл'' (table), ''стілець'' (chair), ''ліжко'' (bed), ''шафа'' (wardrobe),
    and ''диван'' (sofa).'
  - 'Parts of the room and interior: ''підлога'' (floor), ''стіна'' (wall), and ''килим'' (carpet) with associated collocations.'
  - 'Household appliances: ''холодильник'' (refrigerator) and ''пральна машина'' (washing machine), building on a2-45 context.'
- section: 'Граматика: Місцевий відмінок та прийменники (Grammar: Locative Case and Prepositions)'
  words: 475
  points:
  - 'State Standard §4.2.2.6: Using ''у/в'' and ''на'' in the Locative case to describe the location of persons or objects
    (e.g., на столі, в лікарні).'
  - 'High-friction point: Consonant mutations [г]→[з], [к]→[ц], [х]→[с] explicitly drilled (e.g., ''підлога'' -> ''на підлозі'',
    ''полиця'' -> ''на полиці'').'
  - 'Prepositional usage: Contrasting ''у/в'' (inside) with ''на'' (on surface), and highlighting ''на кухні'' as a required
    idiomatic exception.'
- section: 'Практика: Опис оселі та етикет (Practice: Home Description and Etiquette)'
  words: 400
  points:
  - 'Practice drills for Learner Error: Location (static Locative) vs Direction (motion Accusative), correcting ''Я йду в
    кімнаті'' to ''Я йду в кімнату''.'
  - 'Cultural Etiquette: The Threshold (Поріг) taboo—instruction on why shaking hands across the threshold is forbidden in
    Ukrainian culture.'
  - 'Social Superstition: Sitting at the corner of the table (''на розі столу'') and the associated 7-year marriage warning
    for unmarried people.'
- section: 'Підсумок: Мій дім — моя фортеця (Summary: My Home is My Castle)'
  words: 275
  points:
  - Synthesizing vocabulary for describing one's own dwelling and the items within each room.
  - Useful invitation phrases incorporating proper etiquette for entering a Ukrainian home.
  - Reviewing objectives and previewing connections to a2-61 (Hotel) and a2-47 (Locative expansion in Nature).
vocabulary_hints:
  required:
  - стіл (table) — на столі (on the table), ставити стіл (to set the table), письмовий стіл (desk)
  - стілець (chair) — на стільці (on the chair), сидіти на стільці (to sit on a chair)
  - ліжко (bed) — у ліжку (in bed), двоспальне ліжко (double bed), стелити ліжко (to make the bed)
  - шафа (wardrobe) — у шафі (in the wardrobe/closet), книжкова шафа (bookcase), шафа-купе (sliding wardrobe)
  - диван (sofa) — на дивані (on the sofa), лежати на дивані (to lie on the sofa)
  - 'кімната (room) — learner error: confusion with ''місце'' (place); drill location vs direction'
  - кухня (kitchen) — на кухні (in the kitchen) [exception where 'on' replaces 'in']
  - спальня (bedroom) — у спальні (in the bedroom)
  - вітальня (living room) — у вітальні (in the living room)
  - ванна (bathroom) — у ванній (in the bathroom)
  - меблі (furniture) — collective noun; меблі для дому
  recommended:
  - підлога (floor) — на підлозі (on the floor); high-frequency word highlighting [г]→[з] mutation
  - стіна (wall) — на стіні (on the wall); high-frequency location point
  - килим (carpet) — на килимі (on the carpet)
  - холодильник (refrigerator) — common appliance; builds on a2-45
  - пральна машина (washing machine) — essential appliance
  - квартира (apartment) — у квартирі (in the apartment)
  - будинок (house) — у будинку (in the house); reference to Domovyk lore
activity_hints:
- type: match-up
  focus: Rooms and furniture
  items: 30
- type: match-up
  focus: Match furniture to rooms
  items: 20
- type: fill-in
  focus: Complete home descriptions
  items: 15
- type: quiz
  focus: Describe your home
  items: 8
connects_to:
- a2-52 (Nature and Weather)
- a2-64 (Hotel Accommodation)
prerequisites:
- a2-50 (Food and Cooking)
persona:
  voice: Encouraging Cultural Guide
  role: Professional Mover
grammar:
- Locative case for location (у вітальні)
- Prepositions of place review
- Adjectives for home description
register: розмовний
immersion: 60-75% Ukrainian

```

**Level constraints quick-ref:**

```
# A2 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `2000`, `TARGET: 70-90% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for everything.
- ENGLISH: Only in vocabulary tables and one-line grammar notes where absolutely necessary.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Near-full Ukrainian immersion. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Full aspect pairs. No participles.`, ``, etc.

## Grammar Scope

**Allowed:** All 7 cases. Simple subordinate clauses (який/що/коли). Aspect pairs introduced.
Max 15 words per Ukrainian sentence. Max 2 clauses per sentence.

**Forbidden:** Participles. Complex subordinate clauses.

## Immersion Strategy (A2)

A2 uses graduated immersion (50-90%) across three bands:

| Band | Modules | Target | English used for |
|------|---------|--------|-----------------|
| Core grammar | M01-20 | 45-65% | Grammar theory (cases, aspect) |
| Applied grammar | M21-50 | 55-75% | Abstract concepts only |
| Consolidation | M51-70 | 70-90% | Vocabulary tables only |

**Critical rule:** NEVER mix languages within a sentence at A2.
Each sentence is 100% Ukrainian OR 100% English.
Ukrainian paragraph first, then English translation paragraph below if needed.

## A2-Specific Writing Notes

- No Latin transliteration — stress marks (´) only
- No IPA or phonetic brackets
- Register: A2 only. Concrete everyday vocabulary (їсти, ходити, купувати)
- No literary/poetic language, no abstract nouns (почуття, відчуття, стан, сутність)
- No metaphors or figurative speech
- Grammar terms in Ukrainian introduced where relevant (відмінок, називний, etc.)

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `A2` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Home and Furniture** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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
- **Word count**: minimum **2000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Home and Furniture

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
