# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-037
level: A2
sequence: 37
slug: which-one
version: '2.0'
title: Which One?
subtitle: Relative Clauses with Який
focus: grammar
pedagogy: PPP
phase: A2.2
word_target: 2000
objectives:
- Learner can use 'який' to connect sentences
- Learner can decline 'який' to match the gender and case of the noun
- Learner can describe people and objects using relative clauses
- Learner can punctuate complex sentences correctly
sources:
- name: Ukrainian State Standard 2024 - Relative Clauses
  url: https://mon.gov.ua/
  type: reference
  notes: Standards for complex sentence structures and relative pronouns at A2
- name: Grammar of Ukrainian Language - Relative Pronouns
  url: https://uk.wikipedia.org/wiki/Відносні_займенники
  type: reference
  notes: Declension rules for 'який' and its role in subordinate clauses
content_outline:
- section: 'Вступ: Опис за межами прикметників (Introduction: Description Beyond Adjectives)'
  words: 300
  points:
  - The power of complex sentences — moving from simple adjectives to describing people and things with full clauses; contextualizing
    the bridge between A2 and B1 syntax.
  - 'Folk wisdom hook: «Який пан, такий жупан» (Like master, like coat/jacket) — a linguistic illustration of how «який» matches
    the noun it describes, just as a garment reflects its owner''s status.'
  - 'Introduction to the ''Mirror'' analogy: Visualizing «який» as a mirror that reflects the gender and number of the noun
    it follows (the antecedent).'
- section: 'Презентація: Відмінювання та узгодження (Presentation: Agreement and Declension)'
  words: 475
  points:
  - 'Basic Agreement: «Який, Яка, Яке, Які» in the Nominative case — mastering the gender/number match with the antecedent;
    standard reference to adjective-like endings.'
  - 'The Case Detective: Introducing the rule that «який» ''dresses for the job'' inside the relative clause — the case is
    determined by the verb inside the clause (e.g., «знаю кого? -> якого»), not the main sentence.'
  - 'Introducing Accusative forms: Focusing on «якого» (masc/anim) and «яку» (fem) as the primary tools for building descriptive
    sentences about actions.'
  - 'Scaffolding strategy: Moving from Nominative subject clauses (e.g., «чоловік, який стоїть») to Accusative object clauses
    (e.g., «чоловік, якого я знаю»).'
- section: Культурний контекст та вибір (Cultural Context and Selection)
  words: 375
  points:
  - 'The ''Selection'' Culture: Navigating a Ukrainian market (ринок) where the question «Який?» is constant for precision;
    exploring the nuance of selecting specific items.'
  - 'Market interactions: Practical phrases like «Який вам зважити?» (Which one should I weigh?) and «Які помідори найсолодші?»
    (Which tomatoes are the sweetest?).'
  - 'The logic of naming: Discussing the idiom «Як ви човен назвете, так він і попливе» (As you name the boat, so it shall
    float) regarding the importance of defining characteristics.'
- section: Практика та типові помилки (Practice and Common Errors)
  words: 550
  points:
  - 'Differentiating «Хто» vs. «Який»: Correcting the common learner error of using «хто» for people (e.g., «Чоловік, хто
    живе тут» — incorrect) vs. the correct «Чоловік, який живе тут».'
  - 'The Mandatory Comma: Deep dive into punctuation rules; emphasizing that unlike English restrictive clauses, Ukrainian
    relative clauses almost always require a preceding comma.'
  - 'Case Agreement Drills: Transforming simple pairs into complex sentences (e.g., «Я бачу дівчину. Вона читає.» -> «Я бачу
    дівчину, яка читає.» vs «Дівчина читає. Я її бачу.» -> «Дівчина, яку я бачу, читає.»).'
  - 'Identifying the ''The Chameleon'' behavior: Drills to ensure learners don''t mismatch the case of the relative pronoun
    with the antecedent when the clause function differs.'
- section: Діалоги та підсумок (Dialogues and Summary)
  words: 300
  points:
  - 'Witness Interview scenario: Providing detailed descriptions of people or lost items to an official using varied forms
    of «який».'
  - 'Shopping scenario: A market dialogue focusing on specifying preferences («Мені подобається той, який...») and asking
    clarifying questions.'
  - 'Final synthesis: Reviewing the universal nature of «який» for both people and objects, reinforcing the ''reflects antecedent
    / dresses for internal job'' rule.'
vocabulary_hints:
  required:
  - який (which/that/who - masc) — який це?, той, який... (the one who/which); Top 20 frequency
  - яка (which/that/who - fem) — яка різниця? (what's the difference?), дівчина, яка...; Top 50 frequency
  - яке (which/that/who - neut) — яке сьогодні число? (what's the date?); Top 100 frequency
  - які (which/that/who - pl) — люди, які... (people who...), які плани?; Top 100 frequency
  - той (that one) — той, хто... (he who...), той самий (the same one); Top 200 frequency
  recommended:
  - 'чоловік (man/husband) — learner error: used for both ''man'' and ''husband'''
  - 'жінка (woman/wife) — learner error: used for both ''woman'' and ''wife'''
  - ринок (market) — central setting for 'Selection' culture activities
  - зважити (to weigh) — key verb in market selection collocations
  - різниця (difference) — used in the common collocation «яка різниця?»
persona:
  voice: Encouraging Cultural Guide
  role: Competition Judge
grammar:
- relative pronoun який (declension)
- defining relative clauses
- punctuation in complex sentences
- adjective agreement rules
module_type: grammar
immersion: 60-75% Ukrainian
prerequisites:
- in-order-to
connects_to:
- time-clauses
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

Research **Which One?** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Which One?

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
