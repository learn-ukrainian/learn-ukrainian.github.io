# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-007
level: B1
sequence: 7
slug: phonetics-alternation-simplification
version: '2.0'
title: 'Фонетика: спрощення та чергування'
subtitle: 'Phonetics: Cluster Simplification & Alternations'
focus: grammar
pedagogy: PPP
phase: B1.1 [Meta-Language and Phonetics]
word_target: 4000
objectives:
- Learner can identify and apply consonant cluster simplification rules
- Learner can predict vowel alternations (o/i, e/i) from syllable structure
- Learner can apply consonant alternations (g/zh/z, k/ch/ts, kh/sh/s)
- Learner can use euphony rules (u/v, i/y, z/iz/zi) naturally
content_outline:
- section: 'Вступ: Звукові зміни на стику (Introduction: Sound Changes at Boundaries)'
  words: 500
  points:
  - 'Align with State Standard §4.1.1: cluster simplification and alternation as structural phonetic principles of Ukrainian
    — the complement to assimilation covered in the previous module.'
  - Connect to the previous module on assimilation — extending the euphony toolkit from neighbouring-sound effects to syllable-structure-driven
    changes.
  - 'Preview the two-part agenda: how simplification affects spelling (письмо vs вимова), and how alternations drive morphology
    (case endings, word formation).'
- section: Спрощення в групах приголосних (Consonant Cluster Simplification)
  words: 800
  points:
  - 'Detail the three core simplification patterns: стн → сн (честь → чесний), здн → зн (їздити → пізно), стл → сл (щастя
    → щасливий) — provide clear before/after equations so visual learners can map the transformation.'
  - 'Mandatory simplification words: серце, сонце, проїзний, виїзний — drill these high-frequency items with example sentences
    so students internalise the ''silent letter'' conventions automatically.'
  - 'Learner error spotlight — ''Cluster Literalism'': pronouncing the silent consonant (reading чесний as [чесТний]) due
    to spelling transparency. Correct with minimal-pair audio contrasts and a rule-of-thumb mnemonic.'
- section: Чергування голосних (Vowel Alternations)
  words: 800
  points:
  - 'Present the о/і alternation in closed vs open syllables: стіл — столи, ніч — ночі, кіт — кота — frame the rule as ''о
    appears when the syllable stays open, і appears when it closes''.'
  - 'Present the е/і alternation: піч — печі, шість — шести — contrast with о/і to prevent overgeneralisation.'
  - Provide the historical basis briefly — vowel alternation preserves phonetic balance across inflection, making case paradigms
    easier to pronounce at speed.
  - 'Drilling pattern: given a nominative singular, predict the genitive or plural form by applying the open/closed syllable
    test — turn this into an active pattern-recognition habit.'
- section: Чергування приголосних (Consonant Alternations)
  words: 800
  points:
  - 'г/ж/з alternation: нога → ніжка, друг → дружба, дорога → доріжка — show how the same root consonant shifts depending
    on the following suffix, and why this is not irregular but rule-governed.'
  - 'к/ч/ц alternation: рука → ручка, козак → козацький, юнак → юначе (vocative) — highlight the vocative as a live context
    where this alternation surfaces daily.'
  - 'х/ш/с alternation: вухо → вушко, пастух → пастуше — fewer common words but important for recognising diminutives and
    vocative forms.'
  - 'Connect to morphology: these alternations drive case endings and diminutive suffixes, making word formation predictable
    once the pattern is internalised. Frame them as ''harmony tools'' inherited from Proto-Slavic.'
- section: Милозвучність на стику слів (Euphony at Word Boundaries)
  words: 600
  points:
  - 'у/в alternation: у місті (after consonant or pause) vs в місті (after vowel) — give a clear phonetic rule and abundant
    example sentences covering preposition, prefix, and conjunction uses.'
  - 'і/й alternation: і він vs й він — show that the same vowel-avoidance principle drives the choice, with a practical chart
    of surrounding-sound contexts.'
  - 'з/із/зі: з мамою (after vowel or single consonant), із серця (before a consonant cluster), зі мною (before /мн/) — frame
    the three-way choice as a graduated response to increasing consonant difficulty.'
  - 'Practical rule: avoid consonant clusters at word boundaries — Ukrainian chooses the allomorph that keeps the speech stream
    maximally open and flowing.'
- section: 'Практика: Вимова і правопис (Practice: Pronunciation vs Spelling)'
  words: 500
  points:
  - 'Dictation strategy — ''Write explicitly, pronounce smoothly'': learners write the full spelling (чесний with silent т)
    while pronouncing [чесний] — mismatch awareness is the core skill.'
  - Скоромовки (tongue twisters) targeting cluster simplification — celebrate the ''music'' of Ukrainian speech while drilling
    automaticity in simplified clusters.
  - 'Spelling drills with minimal pairs: чесний vs честь, щасливий vs щастя — force learners to toggle between the root form
    and its derived simplification to consolidate both spelling and pronunciation.'
vocabulary_hints:
  required:
  - спрощення (simplification) — спрощення приголосних, спрощення в групах; State Standard term
  - чергування (alternation) — чергування звуків, історичне чергування; specialized linguistic term
  - голосний (vowel) — чергування голосних, голосний звук; essential for phonetic discussion
  - приголосний (consonant) — група приголосних, чергування приголосних
  - склад (syllable) — відкритий/закритий склад; drives alternation rules
  - правопис (spelling) — правила правопису, правопис і вимова
  recommended:
  - милозвучність (euphony) — принцип милозвучності; cultural concept
  - скоромовка (tongue twister) — тренувати скоромовки
  - наголос (stress/accent) — ставити наголос; affects alternation
  - чергувати (to alternate) — голосні чергуються; verb form of чергування
  - стик (boundary/junction) — на стику слів, на стику морфем
activity_hints:
- type: quiz
  focus: Predict vowel alternation from syllable type
  items: 15
- type: fill-in
  focus: Apply consonant alternation in word forms
  items: 15
- type: match-up
  focus: Match simplified pronunciation to correct spelling
  items: 12
- type: error-correction
  focus: Fix euphony errors at word boundaries
  items: 10
connects_to:
- 'b1-08 (Aspect: Complete System)'
prerequisites:
- 'b1-06 (Phonetics: Assimilation)'
persona:
  voice: Senior Language & Culture Specialist
  role: Voice Coach
grammar:
- Consonant cluster simplification (стн→сн, здн→зн, стл→сл)
- Vowel alternations (о/і, е/і in closed/open syllables)
- Consonant alternations (г/ж/з, к/ч/ц, х/ш/с)
- Euphony at word boundaries (у/в, і/й, з/із/зі)
register: нейтральний
immersion: 75-100% Ukrainian

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

Research **Фонетика: спрощення та чергування** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Фонетика: спрощення та чергування

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
