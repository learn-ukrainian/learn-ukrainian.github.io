# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-056
level: A2
sequence: 56
slug: hobbies-leisure
version: '2.0'
title: Hobbies and Leisure
subtitle: What We Do for Fun
focus: vocabulary
pedagogy: PPP
phase: A2.5 [Vocabulary Expansion]
word_target: 2000
objectives:
- Learner can talk about hobbies and interests
- Learner can use 'грати' and 'займатися' correctly
- Learner can describe weekend plans
- Learner can ask others about their free time
content_outline:
- section: Вступ (Introduction)
  words: 275
  points:
  - 'Cultural Hook: Mushroom Picking («Тихе полювання») — explain the national tradition of ''silent hunting'' in Ukrainian
    forests and its popularity among city dwellers.'
  - 'Cultural Hook: Embroidery (Вишивання) — explore how embroidery is a vital cultural act used to preserve regional patterns
    in ''vyshyvanka'' and ''rushnyky''.'
  - 'State Standard §3.4 Alignment: Introduction to ways of spending free time and standard terminology for leisure activities.'
- section: 'Лексика: Світ хобі (Vocabulary: World of Hobbies)'
  words: 400
  points:
  - 'High-frequency collocations for leisure: «вільний час», «мати вільний час», «проводити дозвілля», «культурне дозвілля».'
  - 'Categorizing hobbies: Indoor activities (читати, малювати, грати на гітарі) vs. Outdoor activities (займатися спортом,
    подорожувати).'
  - 'Vocabulary expansion: Cultural events like «концерт», «виставка», and «театр» as part of leisure planning.'
- section: 'Граматика: Грати чи займатися? (Grammar: To Play or to Do?)'
  words: 600
  points:
  - 'Learner error correction: The calque ''Я граю спорт'' vs. the correct ''Я займаюся спортом'' — explain that ''грати''
    is only for games with rules or instruments.'
  - 'Grammar Rule: «грати у + Accusative» for games (футбол, шахи, теніс) vs. «грати на + Locative» for musical instruments
    (гітара, піаніно).'
  - 'Grammar Rule: «займатися + Instrumental» for general sports, hobbies, and activities (спортом, йогою, танцями, фотографією)
    — drill endings.'
  - 'Frequency expressions: Using «часто», «рідко», «іноді» to describe habits and intensity of involvement in hobbies.'
- section: Практика та діалоги (Practice and Dialogues)
  words: 525
  points:
  - 'Dialogue: Asking ''Як ти проводиш вільний час?'' and answering using ''у вільний час'' with frequency adverbs.'
  - 'Case application drill: Mixing instruments and sports to force learners to choose between ''грати у'', ''грати на'',
    and ''займатися''.'
  - 'Describing weekend plans: Role-play planning a ''культурне дозвілля'' trip to a forest or an exhibition.'
- section: Підсумок (Summary)
  words: 200
  points:
  - Summary of key collocations and the грати/займатися distinction.
  - 'Self-reflection: Learners describe their own ''тихе полювання'' or other interests using the correct grammatical structures.'
vocabulary_hints:
  required:
  - 'хобі (hobby) — high frequency; collocations: «моє хобі», «цікаве хобі»'
  - 'дозвілля (leisure) — med-high frequency; collocations: «проводити дозвілля», «культурне дозвілля»'
  - 'вільний час (free time) — high frequency; phrase: «у вільний час», «мати вільний час»'
  - грати (to play) — high frequency; «грати у футбол» (games + Acc), «грати на гітарі» (instruments + Loc)
  - 'займатися (to do/practice) — high frequency; requires Instrumental: «займатися спортом», «займатися йогою»'
  - 'тихе полювання (mushroom picking) — cultural hook: literal ''silent hunting'', the tradition of gathering mushrooms'
  - 'вишивання (embroidery) — cultural hook: preservation of identity through patterns; verb: «вишивати»'
  - 'музика (music) — collocation: «слухати музику», «цікавитися музикою»'
  - 'спорт (sport) — usage note: «займатися спортом» (not «грати спорт»)'
  - читати (to read)
  - малювати (to draw)
  recommended:
  - вишиванка (embroidered shirt) — cultural item produced via «вишивання»
  - 'гітара (guitar) — usage: «грати на гітарі»'
  - 'шахи (chess) — usage: «грати в шахи»'
  - 'фотографія (photography) — usage: «займатися фотографією»'
  - 'подорож (travel) — verb: «подорожувати»'
  - концерт (concert)
  - виставка (exhibition)
activity_hints:
- type: match-up
  focus: Hobbies and activities
  items: 30
- type: match-up
  focus: Match verbs to activities
  items: 20
- type: cloze
  focus: Weekend plans conversation
  items: 10
- type: quiz
  focus: Describe your hobbies
  items: 8
connects_to:
- a2-57 (Education and Learning)
- a2-59 (Sports and Fitness)
prerequisites:
- a2-55 (Technology and Media)
persona:
  voice: Encouraging Cultural Guide
  role: Event Organizer
grammar:
- Verbs for hobbies (грати на, займатися)
- Accusative vs instrumental (футбол vs тенісом)
- Expressing frequency and interests
register: розмовний
immersion: 75-90% Ukrainian

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

Research **Hobbies and Leisure** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Hobbies and Leisure

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
