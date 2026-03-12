# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-024
level: A2
sequence: 24
slug: preferences-and-choices
version: '2.0'
title: Preferences and Choices
subtitle: Expressing Likes and Dislikes
focus: grammar
pedagogy: PPP
phase: A2.2
word_target: 2000
objectives:
- Learner can express preferences and choices
- Learner can compare options using comparative forms
- Learner can use 'would' structures for hypothetical choices
- Learner can politely decline or accept offers
sources:
- name: Ukrainian State Standard 2024 - Preferences
  url: https://mon.gov.ua/
  type: reference
  notes: Communicative requirements for making choices
- name: Ukrainian Language - Communicative Competence
  url: https://uk.wikipedia.org/wiki/Комунікативна_компетентність
  type: reference
  notes: Expressions for polite refusal and preference
content_outline:
- section: Вступ (Introduction)
  words: 275
  points:
  - 'Cultural Hook: Lviv Coffee Culture. Discuss the ritual of choosing coffee in Lviv, introducing terms like «філіжанка
    кави» and choices between «кава з молоком», «кава з піском» (brewed in sand), and «львівська кава».'
  - 'The ''Would Like'' Lexical Bridge: Introduce «я хотів би / я хотіла би» as a high-frequency polite chunk for making requests
    and choices. Explain it as a functional item for A2 without deep conditional theory, preparing for M22.'
- section: Презентація (Presentation)
  words: 600
  points:
  - 'Dative Experiencer Logic: Present «Мені подобається» aligned with State Standard §4.2.2.3. Address ''Nominative Overload''
    (preventing «Я подобається») and ''Object Case Error'' (ensuring the liked item stays in Nominative, e.g., «Мені подобається
    книжка», not «книжку»).'
  - 'Intensity Mismatch Analysis: Distinguish between «любити» (deep/stable affection, e.g., «Я люблю свою сім''ю») and «подобатися»
    (immediate/aesthetic liking, e.g., «Мені подобається це пальто»). Drill correct usage in shopping contexts.'
  - 'Comparison Mechanics: Introduce comparative structures «краще ніж» per State Standard §4.3.1. Highlight that «краще»
    functions as both an adjective (better item) and an adverb (better action, e.g., «так краще зробити»).'
  - 'Formal Preference: Introduce «віддавати перевагу» for more formal or deliberate choices, contrasting it with the spontaneous
    feel of «подобатися».'
- section: Практика (Practice)
  words: 475
  points:
  - 'Transformation Drills: Practice switching between «Я люблю» and «Мені подобається» while maintaining correct grammatical
    subject/object roles (Nominative vs. Dative logic).'
  - 'Decision-Making Scenarios: Enforce Dative experiencer logic through simulated choices in a Restaurant or Store. Focus
    on the State Standard''s requirement for expressing communicative intentions regarding likes/dislikes.'
  - 'Comparative Scale Drills: Weighing options using «краще ніж», «більш солодкий», and «менш дорогий» to build competence
    in qualitative comparison per §4.3.1.'
- section: Діалоги (Dialogues)
  words: 375
  points:
  - 'Situational Dialogue: Choosing a gift or activity with a friend. Integrate the proverb «На колір і смак товариш не всяк»
    (To each their own) to handle differing opinions politely.'
  - 'Immersion Shift: Transition to 60% Ukrainian for situational choices, using polite refusal and preference markers like
    «Дякую, але я б вибрав...» or «Мені це не дуже подобається».'
- section: Підсумок (Summary)
  words: 275
  points:
  - 'Review of Dative Subjectivity: Recalibrating the ''I like'' logic to ''To me is pleasing'' logic to eliminate persistent
    English-to-Ukrainian transfer errors.'
  - 'Prerequisite Check: Verify mastery of Dative pronouns (мені, тобі) and simple comparison forms before moving to M22 (Unreal
    Conditionals) and M24 (Smart Shopping).'
vocabulary_hints:
  required:
  - подобатися (to like) — мені подобається, дуже подобається; High frequency Core, requires Dative experiencer
  - вибирати (to choose) — вибирати книжку, вибирати професію, вибирати між...; Medium-High frequency Core
  - краще (better) — краще ніж, краще зробити, так краще; High frequency Core, functions as adjective and adverb
  - хотів би (would like) — я хотів би замовити, я хотіла би вибрати; High frequency phraseological chunk for polite requests
  recommended:
  - перевага (preference/advantage) — віддавати перевагу (to prefer), мати перевагу; Medium frequency Academic-Core
  - філіжанка (cup/demitasse) — філіжанка кави; Lviv cultural register, high-frequency in coffee contexts
  - смак (taste) — на колір і смак товариш не всяк; used in the key preference proverb
persona:
  voice: Encouraging Cultural Guide
  role: Sommelier
module_type: grammar
immersion: 50-60% Ukrainian
prerequisites:
- the-best-the-worst
connects_to:
- numerals-and-nouns
grammar:
- Вступ
- Презентація
- Практика
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

Research **Preferences and Choices** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Preferences and Choices

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
