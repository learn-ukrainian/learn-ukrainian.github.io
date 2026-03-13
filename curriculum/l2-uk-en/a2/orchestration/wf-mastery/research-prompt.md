# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-048
level: A2
sequence: 48
slug: wf-mastery
version: '2.0'
title: 'Майстерня слів: Велика гра'
subtitle: Word Formation Mastery
focus: grammar
pedagogy: PPP
phase: A2.4 [Word Formation]
word_target: 2000
objectives:
- Learner can synthesize words from parts
- Learner can predict meaning relative to root
- Learner can analyze complex words
- Learner can create new words using patterns
content_outline:
- section: 'Вступ: Українська як LEGO (Introduction: Ukrainian as LEGO)'
  words: 325
  points:
  - 'From analysis to synthesis — cultural hook: Ukrainian as a ''LEGO'' language (synthetic vs analytic); contrast with English
    phrasal verbs (e.g., instead of ''get up'' or ''get out'', we modify the word itself: встати, вийти)'
  - 'Creating new words — introduction to high-yield ''blocks'': prefixes по- (start), з-/с- (complete), ви- (out), пере-
    (re-/cross), за- (into/behind)'
  - Pattern recognition — transition from memorizing isolated words to building them; alignment with State Standard §4.3.1-2
    (Aspectual Pairs & Comparisons)
- section: 'Презентація: Архітектор слова (Presentation: The Word Architect)'
  words: 500
  points:
  - The Word Architect and Derivative Chain — use 'Word Math' equations (e.g., за + пис + ати = записати; праців + ник = працівник)
  - 'The 8 Super-Roots Review — focus on high-frequency roots like -ход- (motion: вихід, захід, перехід), -пис- (write: писати,
    підпис, розпис), -роб- (work/do: робити, заробити, виробник)'
  - 'The Mastery Matrix — covering Aspectual Pairs (prefixation: робити -> зробити) and Comparisons (suffixation) per State
    Standard §4.3.1-2'
  - 'Anatomy of a Complex Word — demonstrate synthesis logic with examples like ''гідроелектростанція'' (19 letters: гідро
    + електро + станція); explain the ''LEGO'' efficiency of long words'
- section: 'Практика: Логіка синтезу (Practice: Logic Synthesis)'
  words: 550
  points:
  - Reverse Engineering — identifying roots in complex words to guess meaning; focus on root recognition despite vowel changes
    (e.g., кінець/кінця/закінчити)
  - 'Word Architect Challenge — applying the Euphony Rule (Cafe ''Ptakh'': с- before к, п, т, ф, х); learner error: correcting
    ''зфотографувати'' (wrong) to ''сфотографувати'' (correct)'
  - 'Logic Synthesis — distinguishing prefixes; learner error: correcting the use of ''ре-'' (re-) instead of the productive
    ''пере-'' for repetition (e.g., ''реписати'' -> ''переписати'')'
  - 'The Suffix Factory — practicing -ник (agent: працівник, керівник) and -ння (process: навчання, читання) to transform
    verbs into nouns'
- section: 'Діалоги: Емоційна інженерія (Dialogues: Emotional Engineering)'
  words: 400
  points:
  - At the Linguistic Club conversation — discussing 'Emotional Engineering'; the cultural capacity for diminutives (e.g.,
    мама -> матуся, кіт -> котик) to add nuance
  - Synthesis in Action — dialogue using high-frequency derivatives of -ход- and -пис- to describe daily routines and bureaucratic
    tasks (signing documents, entering/exiting)
- section: 'Підсумок: Матриця майстерності (Summary: Mastery Matrix)'
  words: 225
  points:
  - Confidence through Logic reflection — summarizing the 'Mastery Matrix' approach to vocabulary expansion
  - De-imperializing the dictionary — emphasizing Ukrainian's internal logic and creative potential as a distinct synthetic
    language
vocabulary_hints:
  required:
  - корінь (root) — the core meaning-bearer; e.g., -ход- (motion), -пис- (write), -роб- (work)
  - префікс (prefix) — e.g., по- (start/limit), пере- (re-/cross), з-/с- (together/complete)
  - суфікс (suffix) — e.g., -ник (agent/person), -ння (process/noun)
  - творення слів (word formation) — the process of 'creating' (творити) new lexemes
  - будувати (to build) — the metaphor of the 'Word Architect'
  - аналізувати (to analyze) — breaking complex words into morphemes
  - синтезувати (to synthesize) — the logic of combining 'blocks' into new words
  - значення (meaning) — how morphemes alter the semantic core
  - сфотографувати (to take a photo) — key example for the с- (Cafe Ptakh) rule
  - переписати (to rewrite) — key example for 're-' repetition (using пере- not ре-)
  required_roots:
  - -ход- (go/motion) — вихід (exit), захід (west/entry), перехід (crossing)
  - -пис- (write) — записати (to record), підпис (signature), розпис (mural/schedule)
  - -роб- (work/do) — робота, зробити (complete), виробник (producer)
  recommended:
  - похідний (derivative) — a word formed from another word or root
  - первісний (original) — the primary form before derivation
  - продуктивний (productive) — a pattern or morpheme that is frequently used
  - закінчення (ending) — the inflectional part of the word
  - гідроелектростанція (hydroelectric station) — 19-letter example of synthesis
  - матуся (mommy) — example of emotional diminutive suffixation
activity_hints:
- type: fill-in
  focus: Create words from parts
  items: 12
- type: group-sort
  focus: Break down and categorize word parts
  items: 15
- type: match-up
  focus: Match roots to meanings
  items: 12
- type: quiz
  focus: Word formation patterns
  items: 12
- type: unjumble
  focus: Build sentences with derived words
  items: 8
- type: cloze
  focus: Word formation in context
  items: 12
- type: error-correction
  focus: Fix word formation errors
  items: 8
connects_to:
- 'a2-49 (Checkpoint: Word Formation)'
prerequisites:
- a2-47 (Adjective Suffixes — Qualities)
persona:
  voice: Encouraging Cultural Guide
  role: Scrabble Champion
grammar:
- Word formation synthesis
- Prefix-root-suffix analysis
- Productive patterns
register: розмовний
immersion: 60-75% Ukrainian

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

Research **Майстерня слів: Велика гра** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Майстерня слів: Велика гра

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
