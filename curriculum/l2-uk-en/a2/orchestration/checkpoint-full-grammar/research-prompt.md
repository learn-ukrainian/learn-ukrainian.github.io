# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-060
level: A2
sequence: 60
slug: checkpoint-full-grammar
version: '2.0'
title: Checkpoint — Full Grammar
subtitle: A2 Mastery Review
focus: checkpoint
pedagogy: TTT
phase: A2.5 [Vocabulary Expansion]
word_target: 2000
objectives:
- Learner can integrate A2 vocabulary in conversation
- Learner can use all grammatical cases correctly
- Learner can navigate common daily situations
- Learner can demonstrate A2 proficiency
content_outline:
- section: Вступ та огляд (Introduction and Overview)
  words: 267
  points:
  - Summative assessment for the A2 morphological curriculum (Standard §4.2.2), verifying
    ability to form all 7 cases and use aspectual pairs.
  - Self-assessment focus with emphasis on self-correction ('виправити помилку') and
    'Euphony as Logic' to explain linguistic irregularities.
- section: 'Милозвучність: Секрет мелодійності (Euphony: The Secret of Melodiousness)'
  words: 333
  points:
  - Scientific recognition of Ukrainian as a melodic language (similar to Italian)
    and the concept of 'Милозвучність' (Euphony).
  - Drilling the rules of u/v and i/y alternation as logical choices to avoid harsh
    consonant clusters and maintain musical flow.
- section: Система відмінків та Кличний (The Case System and the Vocative)
  words: 400
  points:
  - Review of the 7-case system, highlighting the 'Soul' of the Vocative (Кличний)
    as a sign of respect and personification of nature (lisi, zori).
  - 'Addressing common error: Case Confusion (Genitive vs. Accusative) in negation/quantity
    — ''Я не маю часу'' (Gen) vs ''Я маю час'' (Acc).'
- section: 'Дієслово: Вид та Рух (The Verb: Aspect and Motion)'
  words: 400
  points:
  - 'Aspectual pairs review: ''вибирати'' (process) vs ''вибрати'' (result) and ''перевіряти''
    (process) vs ''перевірити'' (result).'
  - 'Correcting Aspect Mismatch: using Perfective for completed actions (''написав
    лист'') vs Imperfective for background process (''писав лист'').'
  - 'Motion Verb Transport: correcting the confusion between ''іти'' (walking) and
    ''їхати'' (vehicle) — e.g., ''їду поїздом'', not ''йду''.'
- section: Сфери життя та Метамова (Spheres of Life and Metalanguage)
  words: 333
  points:
  - Integration of Daily Life, Work, and Health vocabulary while introducing Ukrainian
    meta-language terms like 'іменник' (noun) and 'дієслово' (verb).
  - 'B1 Bridge strategy: preparing learners for deeper grammatical analysis by using
    target language terminology for core concepts.'
- section: Підсумок та інтеграція (Summary and Integration)
  words: 267
  points:
  - 'Comprehensive assessment: selecting correct case and aspect in complex sentences
    (''речення'') to demonstrate A2 mastery.'
  - Consolidation of A2 core (A2-01 to A2-55) and preparation for A2-57 and the transition
    to the B1 level.
vocabulary_hints:
  required:
  - помилка (mistake) — робити помилку, виправити помилку, груба помилка; high-frequency
    meta-language for self-correction focus
  - правило (rule) — запам'ятати правило, за правилом, виняток з правила; high-frequency
    meta-language
  - відмінок (case) — Називний, Родовий, Давальний, Знахідний, Орудний, Місцевий,
    Кличний; summative morphological focus
  - дієслово (verb) — meta-language introduction for B1 Bridge strategy
  - іменник (noun) — meta-language introduction for B1 Bridge strategy
  - речення (sentence) — focus on complex structures and integrative assessment
  - правильно (correctly) — focus on self-correction and accuracy ('вибирати правильну
    відповідь')
  - повторення (review) — key concept for the A2 level summative checkpoint
  recommended:
  - милозвучність (euphony) — melodic quality of Ukrainian driving u/v and i/y alternation
    rules
  - вибирати (to choose) — вибирати правильну відповідь, вибирати подарунок; high-frequency
    A2 general vocabulary
  - перевіряти (to check) — перевіряти себе, перевіряти вправу, перевіряти знання;
    central to self-assessment
  - вид (aspect) — distinction between доконаний (perfective/result) and недоконаний
    (imperfective/process)
  - кличний відмінок (vocative case) — personification of nature and sign of respect
    in address
  - граматика (grammar) — the framework of rules and exceptions ('виняток з правила')
    mastered in A2
activity_hints:
- type: quiz
  focus: A2 grammar comprehensive test
  items: 30
- type: fill-in
  focus: Case and aspect selection
  items: 25
- type: error-correction
  focus: Fix common mistakes
  items: 15
- type: quiz
  focus: Demonstrate A2 proficiency
  items: 10
connects_to:
- a2-61 (Practical Intro)
prerequisites:
- a2-59 (Sports and Fitness)
- a2-55 (Health & Wellness)
persona:
  voice: Encouraging Cultural Guide
  role: Literary Editor
grammar:
- A2 vocabulary review (all thematic areas)
- Case system review (all 7 cases)
- Verb aspect review (perfective/imperfective)
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

Research **Checkpoint — Full Grammar** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Checkpoint — Full Grammar

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
