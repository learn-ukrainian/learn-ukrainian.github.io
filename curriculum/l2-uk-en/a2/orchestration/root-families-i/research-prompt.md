# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-046
level: A2
sequence: 46
slug: root-families-i
version: '2.0'
title: Root Families I
subtitle: The DNA of Vocabulary
focus: grammar
pedagogy: PPP
phase: A2.4
word_target: 2000
objectives:
- Learner can identify root families in complex words
- Learner can guess meanings of derivatives using prefix-root logic
- Learner can build new words from basic roots
- Learner can recognize the 4 core professional roots
sources:
- name: Ukrainian Word Formation - Root Families
  url: https://uk.wikipedia.org/wiki/Словотворення_в_українській_мові
  type: reference
  notes: Standards for root-based vocabulary expansion at A2
- name: Etymological Dictionary of the Ukrainian Language
  url: https://goroh.pp.ua/
  type: reference
  notes: Historical context for hod-, pys-, chyt-, bach- roots
content_outline:
- section: Вступ (Introduction)
  words: 275
  points:
  - 'The ''Lego'' Metaphor: Introduce Ukrainian word formation as a modular system where the root is the core block and the
    prefix is the connector. Align with State Standard §4.3.2 regarding the mastering of productive roots: *пис-* (to write)
    and *ход-* (to walk).'
  - 'Historical DNA: Briefly introduce the ''Big 4'' roots (ход-, пис-, чит-, бач-) as foundational elements for A2 vocabulary,
    explaining that understanding these roots unlocks hundreds of high-frequency words without rote memorization.'
- section: Родини ход- та пис- (The hod- and pys- Families)
  words: 450
  points:
  - 'The ход- (Motion) Family: From Proto-Slavic *xodъ (walking/going). Teach the logic of directional prefixes: *в-* (in)
    for *вхід*, *ви-* (out) for *вихід*, and *пере-* (across) for *перехід*. Reference §4.2.3.1 for the conjugation of *ходити*
    (*ходжу*, *ходиш*).'
  - 'The пис- (Writing) Family: Connect the root to the Proto-Slavic *pьsati* (to paint/decorate), linking the verb *писати*
    to the cultural icon *писанка* (Easter egg). Address the learner error where *записати* is restricted to writing; clarify
    it also means ''to record'' audio/video. Explain *підпис* (signature) as placing a mark ''under'' the text.'
- section: Родини чит- та бач- (The chyt- and bach- Families)
  words: 475
  points:
  - 'The чит- (Reading) Family: Explore the etymology from Proto-Slavic *čisti* (to count/honor), suggesting that reading
    was historically seen as a form of reckoning or honoring text. Introduce derivatives like *читач* (reader) and *прочитати*
    (to read through), emphasizing the agentive suffix *-ач*.'
  - 'The бач- (Vision) Family: Analyze perception through *бачення* (vision) and *передбачити* (to foresee/predict). Highlight
    the cultural term *побачення* (date) as ''mutual seeing''. Contrast *бачити* (passive ability/perception) with *дивитися*
    (active/intentional watching) to prevent common A2 errors.'
- section: Фонетика та префікси (Phonetics and Prefixes)
  words: 400
  points:
  - 'The Kafka-Ptakh Euphony Rule: Teach the phonetic rule for the *с-* prefix (used instead of *з-* before the consonants
    К, Ф, П, Т, Х). Specifically correct the common error *зходити* by drilling the correct form *сходити* (to go/climb/descend).'
  - 'Logic of the ''Big 4'' Prefixes: Focus on the semantic impact of *в-, ви-, при-, під-* across all families. Provide a
    ''Guessing Machine'' challenge where learners combine these prefixes with the core roots to predict meanings (e.g., *при-*
    + *хід* = arrival).'
- section: Практичне застосування (Practical Application)
  words: 400
  points:
  - 'Root Identification Challenge: Provide drills for identifying the core root within complex or unfamiliar words (e.g.,
    finding *пис* in *письменник*). Use ''Translate by Logic'' exercises to guess derivatives like *опис* (description) or
    *вичитати* (to scold/proofread) based on prefix meanings.'
  - 'Library Contextual Dialogue: Create a scenario at a library or bookstore using *читач*, *письменник*, and *опис*. Practice
    aspectual pairs *писати/написати* per State Standard §4.3.2 and use *записати* correctly for both taking notes and recording
    a book recommendation.'
vocabulary_hints:
  required:
  - ходити (to walk/go) — ходжу, ходиш; core motion verb; root ход-
  - вхід (entrance) — вхід до будівлі; prefix в- + хід
  - вихід (exit) — запасний вихід; prefix ви- + хід
  - перехід (crossing/transition) — підземний перехід; prefix пере- + хід
  - писати (to write) — писати листа; core root пис-
  - підпис (signature) — поставити підпис; prefix під- + пис
  - записати (to record/write down) — записати адресу; prefix за- + писати
  - читати (to read) — читати книгу; core root чит-
  - читач (reader) — активний читач; agentive suffix -ач
  - бачити (to see) — бачити різницю; core root бач-
  recommended:
  - писанка (Easter egg) — розписувати писанку; cultural derivative of пис-
  - побачення (date/meeting) — призначити побачення; mutual seeing
  - передбачити (to foresee) — важко передбачити; prefix перед- + бачити
  - письменник (writer) — відомий письменник; agentive derivative of пис-
  - сходити (to descend/go down) — сходити сходами; с- prefix before х
persona:
  voice: Encouraging Cultural Guide
  role: Historical Linguist
grammar:
- common roots (ход-, пис-, чит-, бач-)
- prefix + root combinations
- derivative formation
module_type: word-formation
immersion: 60-75% Ukrainian
prerequisites:
- adjective-suffixes-types
connects_to:
- root-families-ii
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

Research **Root Families I** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Root Families I

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
