# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-008
level: B1
sequence: 8
slug: stress-mobility-euphony
version: '1.0'
title: 'Рухомий наголос та милозвучність'
subtitle: 'Mobile Stress & Advanced Euphony'
focus: grammar
pedagogy: PPP
phase: B1.1 [Meta-Language and Phonetics]
word_target: 4000
objectives:
- Learner can predict stress shifts in noun declension paradigms (рукá→рýки)
- Learner can apply stress mobility rules in verb conjugation
- Learner can use advanced euphony alternations (все/усе, вже/уже, зі/із) beyond basic і/й and у/в
- Learner can recognize stress-driven vowel quality changes and their effect on meaning
content_outline:
- section: 'Вступ: Наголос як рухома сила (Introduction: Stress as a Moving Force)'
  words: 500
  points:
  - 'State Standard §4.1.2: mobile stress as a structural feature of Ukrainian — contrast with fixed-stress languages'
  - 'Why stress matters: stress shifts distinguish grammatical forms (зáмок "castle" vs замóк "lock") and drive morphological patterns'
  - 'Preview: stress mobility in declension, conjugation, and its interaction with euphony'
- section: Рухомий наголос у відмінюванні іменників (Mobile Stress in Noun Declension)
  words: 900
  points:
  - 'End-stress → root-stress shifts: рукá → рýки, водá → вóди, землé → зéмлі — mapping the pattern across declension classes'
  - 'Root-stress → end-stress: слóво → словá (plural), óзеро → озéра — systematic patterns in neuter nouns'
  - 'Stress in the four declension classes: which declensions have mobile stress and which are stable'
  - 'Fleeting vowels under stress shift: сон → сну, день → дня — vowel disappearance when stress moves away'
  - 'Practical drill: given nominative with stress marked, predict genitive singular stress position'
- section: Рухомий наголос у дієвідмінюванні (Mobile Stress in Verb Conjugation)
  words: 800
  points:
  - 'First conjugation stress patterns: писáти → пишý, пúшеш — stress shift from infinitive to present tense stem'
  - 'Second conjugation patterns: ходúти → хóджу, хóдиш — root stress in present but end stress in infinitive'
  - 'Stress in past tense: бýти → булá (feminine stress shift), нестú → нíс, неслá'
  - 'Common learner errors: misplacing stress in high-frequency verbs (робúти → *рóблю instead of роблю́)'
  - 'Mnemonic strategies for irregular stress patterns in the 50 most common verbs'
- section: 'Поглиблена милозвучність (Advanced Euphony: Beyond Basics)'
  words: 900
  points:
  - 'Recap of basic euphony (у/в, і/й) from B1.7 — then extend to advanced cases'
  - 'все/усе alternation: все знають vs усе було добре — phonetic environment and stylistic register differences'
  - 'вже/уже alternation: вже прийшов vs уже вечір — positional and rhythmic factors'
  - 'зі/із beyond basic з: зі мною, із задоволенням — full three-way system with complex consonant clusters'
  - 'увійти/ввійти, увесь/ввесь — prefix euphony in word-internal position'
  - 'Register sensitivity: literary norm vs conversational shortcuts in euphony application'
- section: 'Наголос і милозвучність у взаємодії (Stress and Euphony Interaction)'
  words: 500
  points:
  - 'How stress position affects euphony choices: stressed vs unstressed prepositions (нá воду vs на водý)'
  - 'Enclitics and proclitics: stress shifts in prepositional phrases (пíд руку, зá ніч)'
  - 'Rhythmic euphony: how Ukrainian avoids stress clashes through particle and preposition choices'
- section: 'Практика: Наголос у контексті (Practice: Stress in Context)'
  words: 400
  points:
  - 'Reading aloud with stress marks: authentic text passage with all stress positions marked'
  - 'Dictation exercise: write words with correct stress placement after hearing them in context'
  - 'Euphony editing: correct texts with euphony violations to develop native-like intuition'
vocabulary_hints:
  required:
  - наголос (stress/accent) — рухомий наголос, нерухомий наголос; State Standard term
  - рухомий (mobile/movable) — рухомий наголос; describes stress that shifts between forms
  - милозвучність (euphony) — закони милозвучності; core phonetic principle
  - відмінювання (declension) — наголос у відмінюванні; stress patterns across cases
  - дієвідмінювання (conjugation) — наголос у дієвідмінюванні; stress patterns across persons
  recommended:
  - ненаголошений (unstressed) — ненаголошений склад; unstressed syllable
  - наголошений (stressed) — наголошений голосний; stressed vowel
  - проклітика (proclitic) — прийменник-проклітика; unstressed preposition before noun
  - енклітика (enclitic) — частка-енклітика; unstressed word leaning on previous
  - чергування (alternation) — чергування у/в, і/й; euphony alternation
activity_hints:
- type: quiz
  focus: Predict stress position in declined/conjugated forms
  items: 15
- type: fill-in
  focus: Choose correct euphony variant (все/усе, вже/уже, зі/із)
  items: 12
- type: error-correction
  focus: Fix stress placement and euphony errors in sentences
  items: 10
- type: match-up
  focus: Match nominative form to correct genitive with stress shift
  items: 12
prerequisites:
- 'b1-07 (Phonetics: Alternation & Simplification)'
connects_to:
- 'b1-09 (Aspect: Complete System)'
persona:
  voice: Senior Language & Culture Specialist
  role: Voice Coach
grammar:
- Mobile stress in noun declension (рукá→рýки, водá→вóди)
- Mobile stress in verb conjugation (писáти→пишý)
- Advanced euphony (все/усе, вже/уже, зі/із)
- Stress in prepositional phrases (enclitics/proclitics)
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

Research **Рухомий наголос та милозвучність** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Рухомий наголос та милозвучність

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
