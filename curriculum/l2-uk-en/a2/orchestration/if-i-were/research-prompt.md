# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-027
level: A2
sequence: 27
slug: if-i-were
version: '1.0'
title: If I Were...
subtitle: 'Умовний спосіб: якби та б'
focus: grammar
pedagogy: PPP
phase: A2.2
word_target: 2000
objectives:
- Learner can form the conditional mood using past tense + б/би
- Learner can express hypothetical conditions with якщо б / якби
- Learner can distinguish real conditions (якщо + future) from unreal conditions (якщо б + conditional)
- Learner can use conditional mood in polite requests and wishes
sources:
- name: Ukrainian State Standard 2024 - Conditional Mood
  url: https://mon.gov.ua/
  type: reference
  notes: Conditional mood formation and usage at A2 level
- name: Grammar of Ukrainian Language - Conditional Mood
  url: https://uk.wikipedia.org/wiki/Умовний_спосіб
  type: reference
  notes: Formation rules for the conditional mood
content_outline:
- section: 'Вступ: Світ мрій та припущень (Introduction: The World of Dreams and Hypotheticals)'
  words: 275
  points:
  - 'Why Ukrainian needs a separate mood for "what if" — contrasting the indicative (facts) with the conditional (hypotheticals)'
  - 'Cultural hook: Ukrainian proverb «Якби та кабí, то в роті росли́ б гриби́» (If ifs and buts were candy and nuts) — showing
    how the conditional is woven into folk wisdom'
  - 'Preview of the formation pattern: past tense + б/би — simpler than English conditional'
- section: 'Утворення умовного способу (Forming the Conditional Mood)'
  words: 400
  points:
  - 'Core rule: past tense form + particle б (after vowels) or би (after consonants) — я читáв би, вонá читáла б'
  - 'Gender and number agreement follows past tense: він ходи́в би, вонá ходи́ла б, вонó ходи́ло б, вони́ ходи́ли б'
  - 'Position of б/би: typically after the verb, but can follow other sentence elements for emphasis — я б хотíв, він би знав'
  - 'State Standard requirement (§4.2.3.3): learner must form conditional from both imperfective and perfective verbs — читáв
    би (would be reading) vs прочитáв би (would read/would have read)'
- section: 'Реальна vs нереальна умова (Real vs Unreal Conditions)'
  words: 400
  points:
  - 'Real conditions with якщо + future/present: Якщо пíде дощ, я вíзьму парасóльку (If it rains, I will take an umbrella)'
  - 'Unreal conditions with якщо б / якби + conditional: Якби я мав грóші, я б купи́в маши́ну (If I had money, I would buy a
    car)'
  - 'The fused form якби as a stylistic variant of якщо б — both are correct, якби is more common in speech'
  - 'Learner error: mixing real and unreal patterns — *Якщо б я буду мати* (contamination of conditional with future tense)'
- section: 'Ввічливі прохання та побажання (Polite Requests and Wishes)'
  words: 350
  points:
  - 'Conditional for politeness: Я хотíв би... / Я хотíла б... (I would like...) — the most common real-world use of conditional'
  - 'Чи не мóгли б ви...? (Could you...?) — polite request pattern with conditional mood'
  - 'Wishes: Я б хотíв жи́ти в Украї́ні (I would like to live in Ukraine), Було́ б дóбре... (It would be good...)'
  - 'Connection to imperative: conditional requests are softer than imperative commands — register awareness'
- section: 'Практичне застосування (Practical Application)'
  words: 350
  points:
  - 'Dream scenarios: describing what you would do if you won the lottery, visited Kyiv, spoke perfect Ukrainian'
  - 'Advice giving: Я б на твоéму мíсці... (If I were in your place...) — a high-frequency conditional pattern'
  - 'Comparing two worlds: what is (real) vs what would be (hypothetical) — integrating indicative and conditional in one context'
  - 'Summary: the conditional mood as a tool for dreams, politeness, and nuance in A2-level communication'
vocabulary_hints:
  required:
  - 'б / би (conditional particle) — Very high frequency; б after vowels, би after consonants; IPA: [b] / [bɪ]'
  - 'якщо (if — real) — Very high frequency; introduces real conditions; IPA: [jɐkˈʃtʃo]'
  - 'якби / якщо б (if — unreal) — High frequency; introduces hypothetical conditions; IPA: [jɐkˈbɪ]'
  - 'хотíв би / хотíла б (would like) — Very high frequency polite form; most common conditional in daily speech'
  - 'міг би / моглá б (could) — High frequency; polite requests and hypothetical ability'
  - 'було́ б (it would be) — High frequency; було б добре (it would be good), було б чудово (it would be wonderful)'
  recommended:
  - 'кабí (regional: if only) — appears in proverbs; stylistic/dialectal variant'
  - 'на мíсці (in place of) — High frequency; я б на твоєму місці (if I were you)'
  - 'мрíяти (to dream) — Mid frequency; мріяв би (would dream); connects to cultural hook'
persona:
  voice: Encouraging Cultural Guide
  role: Dream Architect
module_type: grammar
immersion: 60-75% Ukrainian
prerequisites:
- numeral-case-agreement
- yesterday-past-tense
connects_to:
- complete-imperative
- smart-shopping
grammar:
- conditional mood formation (past tense + б/би)
- real vs unreal conditions (якщо vs якщо б/якби)
- polite conditional requests
register: розмовний
activity_hints:
- type: quiz
  focus: Identify real vs unreal conditions
  items: 12
- type: fill-in
  focus: Complete sentences with correct conditional forms
  items: 10
- type: error-correction
  focus: Fix common conditional mood errors
  items: 8
- type: match-up
  focus: Match conditions to consequences
  items: 10
- type: essay-response
  focus: Write about hypothetical scenarios using conditional

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

Research **If I Were...** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: If I Were...

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
