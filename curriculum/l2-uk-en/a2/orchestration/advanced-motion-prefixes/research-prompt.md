# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-042
level: A2
sequence: 42
slug: advanced-motion-prefixes
version: '2.0'
title: Advanced Motion Prefixes
subtitle: Crossing, Passing, and Approaching
focus: grammar
pedagogy: PPP
phase: A2.3
word_target: 2000
objectives:
- Learner can describe crossing streets and spaces
- Learner can describe passing by or through places
- Learner can describe approaching an object
- Learner can describe reaching a destination
- Learner can describe "popping in" or stopping by
- Learner can describe moving around an obstacle
sources:
- name: Ukrainian State Standard 2024 - Advanced Verbs of Motion
  url: https://mon.gov.ua/
  type: reference
  notes: Standards for complex spatial trajectories and prefixed verbs at A2
- name: Grammar of Ukrainian Language - Verb Prefixes
  url: https://uk.wikipedia.org/wiki/Префікси_дієслів_руху
  type: reference
  notes: Detailed semantics of spatial prefixes with motion stems
content_outline:
- section: Вступ (Introduction)
  words: 275
  points:
  - 'Beyond In and Out: The geometry of complex paths — introduce the ''GPS instructions'' metaphor: root is the engine, prefix
    is the steering wheel'
  - Navigating the city like a local — alignment with State Standard §3 (Travel and City themes) for precise trajectories
    in urban environments
  - 'The logic of distance: How prefixes signal proximity — distinguishing ''near'' (під-) vs ''touch/arrival'' (до-) as a
    bridge to B1 word formation (§4.3.8)'
- section: 'Геометрія руху: Пере-, Про-, Об- (Geometry of Motion: Crossing, Through, Around)'
  words: 475
  points:
  - 'The Bridge: Пере- (Across) vs Про- (Through) — visual: X -> Y vs -> | | ->; cultural hook: the ''black cat crossing the
    path'' (чорний кіт перейшов дорогу) superstition and rituals to ward off bad luck'
  - 'The Circle: Об- (Around) — visual: O ->; context: bypassing obstacles (обійти перешкоду) or walking around a building,
    using text-based diagrams for geometric clarity'
  - 'Vocabulary in Motion: Deep dive into ''пройти повз'' (pass by) and ''перейти на українську'' (switch to Ukrainian) as
    high-frequency Core A2 collocations'
- section: 'Наближення та Прибуття: Під-, До-, За-, При- (Approach and Arrival: Approaching, Reaching, Popping in, Arriving)'
  words: 525
  points:
  - 'The Reach: До- (Getting there/Reach) vs Під- (Approaching) — grammatical harmony: State Standard §4.2.2.4 (В/У/НА for
    destination) vs ''ДО'' for proximity/approach (підійти до)'
  - 'The Visit: За- (Stopping by) vs При- (Arriving) — cultural hook: the ''Returning'' superstition (bad luck to return home
    shortly after leaving) and the ''mirror ritual'' to neutralize it'
  - 'Abstract Motion: High-value idioms derived from spatial logic: ''мені підходить'' (it suits me) and ''дійти згоди'' (reach
    agreement)'
- section: Практика та Корекція (Practice and Correction)
  words: 400
  points:
  - 'Common Learner Errors: Explicitly correcting ''Preposition Mismatch'' (підійти в vs підійти до) and ''Coming vs Going''
    (прийшов vs пішов) confusion'
  - 'Perfective Future Logic: Drills for conjugating prefixed motion verbs without the auxiliary ''буду'' (e.g., ''прийду''
    instead of ''буду прийти''), aligning with State Standard §4.2.3.1'
  - 'Directional drills: Giving complex instructions in a Lviv/Kyiv context using ''пройти 5 кілометрів'' and ''перейти міст'''
- section: Діалоги та Сценарії (Dialogues and Scenarios)
  words: 325
  points:
  - 'Travel stories: A journey through the mountains or a complex commute — integrate ''сонце зайшло'' (sun set) and ''час
    пройшов'' (time passed) for natural narrative flavor'
  - 'Conversational immersion: Roleplay scenario involving ''зайти до друга'' (visit a friend) and using ''руки не доходять''
    (never get around to it) for tasks'
vocabulary_hints:
  required:
  - перейти / переходити (to cross) — перейти вулицю, перейти міст, перейти на українську (switch to Ukrainian); high frequency
    Core A2
  - пройти / проходити (to pass, walk distance) — пройти повз (pass by), пройти 5 кілометрів, час пройшов (time passed); high
    frequency Core A2
  - 'підійти / підходити (to approach, suit) — підійти до карти (requires ''до'' + Gen), потяг підходить, мені це підходить
    (idiom: this suits me); med-high frequency'
  - дійти / доходити (to reach, get to) — як дійти до...?, дійти згоди (reach agreement); med-high frequency
  - зайти / заходити (to enter, stop by) — зайти в магазин (pop in), сонце зайшло (sun set), зайти до друга; high frequency
  - обійти / обходити (to go around) — обійти навколо, обійти перешкоду (bypass obstacle); medium frequency
  - прийти / приходити (to arrive, come) — прийти додому, прийти вчасно; very high frequency
  recommended:
  - 'руки не доходять (idiom: never get around to it) — high-value conversational phrase'
  - чорний кіт перейшов дорогу (superstition phrase) — bad omen involving crossing
  - подивитися у дзеркало (to look in the mirror) — ritual to neutralize the 'returning' superstition
  - повернутися / вернутися (to return) — contrast with 'зайти' or 'піти' in narrative contexts
persona:
  voice: Encouraging Cultural Guide
  role: Logistics Expert
grammar:
- prefix пере- (crossing)
- prefix про- (passing/through)
- prefix під- (approaching)
- prefix до- (reaching)
- prefix за- (stopping by / behind)
- prefix об- (around)
- prefix при- (arriving)
module_type: grammar
immersion: 60-75% Ukrainian
prerequisites:
- basic-motion-prefixes
connects_to:
- action-verb-prefixes
register: розмовний
activity_hints:
- type: quiz
  focus: Identify correct forms
  items: 10
- type: fill-in
  focus: Complete with correct grammar
  items: 8
- type: match-up
  focus: Match forms to categories
  items: 10
- type: error-correction
  focus: Find and fix errors
  items: 6
- type: group-sort
  focus: Classify by grammatical feature
  items: 8
- type: essay-response
  focus: Write using target structures

```

**Level constraints quick-ref:**

```
# A2 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `2000`, `TARGET: 55-75% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for all content — dialogues, examples, section intros, cultural context.
- ENGLISH: Only for abstract grammar concepts that need explicit explanation.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English. Dialogues, examples, section intros all stay Ukrainian-only.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Aspect pairs introduced. No participles.`, ``, etc.

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

Research **Advanced Motion Prefixes** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Advanced Motion Prefixes

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
