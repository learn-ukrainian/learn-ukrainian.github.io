# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-041
level: A2
sequence: 41
slug: basic-motion-prefixes
version: '2.0'
title: Basic Motion Prefixes
subtitle: In and Out
focus: grammar
pedagogy: PPP
phase: A2.3
word_target: 2000
objectives:
- Learner can describe entering and exiting places
- Learner can use prefixes в-/у- and ви- correctly
- Learner can choose the correct preposition for motion verbs
- Learner can describe daily commute actions
sources:
- name: Ukrainian State Standard 2024 - Verbs of Motion
  url: https://mon.gov.ua/
  type: reference
  notes: Standards for prefixed verbs of motion and spatial orientation at A2
- name: Morphology of Ukrainian Verb - Prefixes
  url: https://uk.wikipedia.org/wiki/Префікси_в_українській_мові
  type: reference
  notes: Structural rules for V- and VY- prefixes with motion stems
content_outline:
- section: Вступ (Introduction)
  words: 275
  points:
  - Prefixes as the GPS of Slavic verbs — direction is 'built-in' in Ukrainian verbs, unlike English phrasal verbs where direction
    is external to the stem
  - Why direction is 'built-in' in Ukrainian — emphasizes the vector of movement (into vs out of) as a fundamental part of
    the verb's semantic core
  - 'Alignment with State Standard §4.2.3.1: Reinforce the conjugation of base motion verbs (іти, їхати, ходити, їздити) as
    the essential foundation for prefixed forms'
- section: 'Презентація: В- та Ви- (Presentation: V- and VY-)'
  words: 600
  points:
  - 'The Binary: В- (Into) vs Ви- (Out) — use the ''Box Analogy'' from research: В- is an arrow INTO the box, Ви- is an arrow
    OUT OF the box to visualize spatial relations'
  - 'Prepositional Hooks: Alignment with State Standard §4.2.2.4.2 — pairing ''в, у, на'' with ''входити/зайти'' for destinations
    (e.g., ''зайти в кімнату'') using the Accusative case'
  - 'Perfective Shift: How a prefix creates a ''result'' state — explicitly teach the aspectual difference between ''входити''
    (process/habit) and ''увійти'' (one-time completed result)'
  - 'Euphony and the Apostrophe: В’їхати vs Виїхати — rules for ''увійти'' vs ''ввійти'' vs ''увіходити'' and how they trigger
    constant phonetic adjustments in spoken Ukrainian'
  - 'The Space Rule: Distinguish enclosed spaces (В) vs surfaces/open areas (На) — ''входити в кімнату'' vs ''виходити на
    вулицю/балкон'''
- section: Культурний контекст (Cultural Context)
  words: 325
  points:
  - 'The Threshold (Поріг): Explore the cultural prohibition of shaking hands or passing money ''через поріг'', illustrating
    the in/out binary as a sacred boundary in Ukrainian homes'
  - 'Kyiv Metro Navigation: Practical application of ''Вхід'' (Entrance) and ''Вихід'' (Exit) signs; common warnings like
    ''Не притулятися'' (Do not lean) on transit doors'
  - 'Urban Narratives: Applying ''в''їжджати/виїжджати'' to city commutes and ''входити/виходити'' to office and building
    navigation as part of daily life'
- section: Практика та помилки (Practice and Errors)
  words: 525
  points:
  - 'Learner error: Using ''в/у'' with ''виходити'' instead of ''з'' (e.g., error ''Я виходжу в офісу'') — teach the ''З +
    Genitive'' requirement for the ''out of'' vector'
  - 'Learner error: Confusing mode of transport — explain why ''Машина входить у гараж'' is incorrect and must be ''Машина
    в''їжджає у гараж'' (strict separation of foot vs vehicle)'
  - 'Directional transformation drills: Practicing the shift from base verbs (іти/їхати) to prefixed verbs based on specific
    destination and origin cues'
  - 'Aspect confusion drills: Identifying when to use ''входжу'' (daily habit like the gym) vs ''увійшов'' (specific completed
    action) to avoid common A2 mistakes'
- section: Підсумок та діалоги (Summary and Dialogues)
  words: 275
  points:
  - 'Morning Routine Dialogue: Constructing a narrative from house (вийти) to car (в''їхати на дорогу) to office (ввійти),
    practicing logical prefix sequencing'
  - 'Idiomatic Review: High-frequency collocations like ''входити в моду'', ''виходити заміж'', and ''виїжджати на природу''
    to demonstrate register variety'
  - 'Summary of Prefix-Preposition Logic: A final checklist of ''В- + В/На'' (Acc) and ''Ви- + З/Із'' (Gen) pairings for student
    reference and review'
vocabulary_hints:
  required:
  - входити (to enter [on foot]) — входити в кімнату, входити в моду (idiom), входити в історію; high frequency verb
  - виходити (to exit [on foot]) — виходити з дому, виходити на вулицю, виходити заміж (idiom), виходити з себе (idiom); high
    frequency verb
  - в'їжджати (to drive in/enter [by vehicle]) — в'їжджати до міста, в'їжджати в гараж, в'їжджати в нову квартиру (move in);
    medium frequency
  - виїжджати (to drive out/exit [by vehicle]) — виїжджати за кордон, виїжджати з парковки, виїжджати на природу; medium frequency
  recommended:
  - вхід (entrance) — ubiquitous sign in Kyiv Metro and public buildings; often paired with 'Вхід заборонено'
  - вихід (exit) — ubiquitous sign in Kyiv Metro and public buildings; 'Запасний вихід' (Emergency exit)
  - поріг (threshold) — cultural boundary; 'не вітатися через поріг' (superstition)
  - увійти (to enter [perfective]) — common digital UI term for 'Login' or 'Enter' on websites
persona:
  voice: Encouraging Cultural Guide
  role: Taxi Driver
grammar:
- prefix в-/у- (entering)
- prefix ви- (exiting)
- prepositions with motion verbs
- motion verb pairs
module_type: grammar
immersion: 60-75% Ukrainian
prerequisites:
- checkpoint
connects_to:
- advanced-motion-prefixes
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

Research **Basic Motion Prefixes** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Basic Motion Prefixes

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
