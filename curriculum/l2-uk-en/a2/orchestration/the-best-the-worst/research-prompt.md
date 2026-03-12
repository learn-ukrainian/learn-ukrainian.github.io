# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-023
level: A2
sequence: 23
slug: the-best-the-worst
version: '2.0'
title: The Best, The Worst
subtitle: The Superlative Degree
focus: grammar
pedagogy: PPP
phase: A2.2
word_target: 2000
objectives:
- Learner can form superlative adjectives
- Learner can describe the highest degree of a quality
- Learner can use superlatives to talk about records and favorites
- Learner can distinguish between comparative and superlative forms
sources:
- name: Ukrainian State Standard 2024 - Superlatives
  url: https://mon.gov.ua/
  type: reference
  notes: Superlative requirements for A2
- name: Ukrainian Adjective Masterclass
  url: https://uk.wikipedia.org/wiki/Прикметник
  type: reference
  notes: Superlative formation and usage
content_outline:
- section: Вступ (Introduction)
  words: 275
  points:
  - Introduction to the concept of the superlative degree as the expression of an extreme quality, building directly on the
    comparative degree structures learned in module a2-18.
  - 'The logic of Ukrainian superlative formation: simply adding the prefix ''най-'' to the existing comparative form (e.g.,
    більший → найбільший).'
  - 'Hook: Mention that Ukraine holds several world-class records which will be explored through the lens of superlative adjectives.'
- section: Граматична презентація (Grammar Presentation)
  words: 575
  points:
  - 'Synthetic (Simple) form (§4.3.1): focus on the ''най-'' + comparative structure for regular adjectives (e.g., найсолодший,
    найважливіший).'
  - 'Suppletive (Irregular) forms (§4.3.1): High-frequency pairs including великий/найбільший, малий/найменший, добрий/найкращий,
    and поганий/найгірший.'
  - 'Analytic (Compound) form (§4.3.1): Using ''найбільш'' (the most) or ''найменш'' (the least) + the basic form of the adjective;
    explain when to prefer this form (longer or technical adjectives).'
  - 'Adjective agreement check: Reinforce that superlative forms are still adjectives and must agree in gender, number, and
    case with the noun (e.g., найкраща ідея, найкращий план, найкраще місто).'
- section: Типові помилки та підсилення (Common Errors and Intensifiers)
  words: 400
  points:
  - 'Learner error: Russian influence ''самий''. Explicitly debunk the use of ''самий великий'' in favor of ''найбільший''
    or ''найбільш великий''.'
  - 'Learner error: Double Superlatives. Correct the mistake of mixing forms like ''найбільш цікавіший'' (wrong) vs ''найбільш
    цікавий'' or ''найцікавіший'' (correct).'
  - 'Emphatic prefixes: Introduce ''якнай-'' and ''щонай-'' to express ''as ... as possible'' (e.g., якнайшвидше, якнайкраще)
    for added semantic depth.'
  - 'Distinguishing ''дуже'' (very) from ''най-'' (the most): clarifying that ''найкращий'' is a unique rank, while ''дуже
    добрий'' is just a high degree.'
- section: 'Культурний контекст: Рекорди України (Cultural Context: Ukrainian Records)'
  words: 425
  points:
  - 'World records quiz focusing on specific Ukrainian data: Станція «Арсенальна» у Києві — найглибша станція метро у світі
    (105,5 м).'
  - 'Geographical superlatives: Говерла — найвища гора України (2061 м); Печера «Оптимістична» — найдовша гіпсова печера у
    світі (понад 230 км).'
  - 'Technological superlatives: АН-225 «Мрія» — найбільший і найпотужніший транспортний літак у світі; emphasize its symbolic
    importance.'
- section: Діалоги та практика (Dialogues and Practice)
  words: 325
  points:
  - 'Roleplay as a Restaurant Critic: Comparing three restaurants to find the ''найкращий сервіс'', ''найсмачніша їжа'', and
    ''найцікавіше меню''.'
  - 'Award Ceremony Dialogue: Using collocations like ''найважливіший крок'' and ''найвищий рівень'' to praise achievements.'
  - 'Final summary: Reviewing the choice between synthetic and analytic forms based on register and frequency.'
vocabulary_hints:
  required:
  - 'найкращий (the best) — High frequency (Top 500); collocations: найкращий друг, найкращий час, найкраща ідея'
  - 'найгірший (the worst) — High frequency; collocations: найгірший сценарій, найгірша погода, найгірший день'
  - 'найбільший (the biggest/largest) — High frequency (Top 500); collocations: найбільша країна, найбільша помилка, найбільше
    місто'
  - 'найменший (the smallest) — High frequency; collocations: найменша дитина, найменша деталь, найменша ціна'
  - найбільш (the most... [analytic]) — Required for compound superlatives; most frequent in formal contexts
  - 'найважливіший (the most important) — Medium-high frequency; collocations: найважливіше питання, найважливіший крок'
  recommended:
  - 'найвищий (the highest) — Used for records and levels; collocations: найвища гора, найвищий бал, найвищий рівень'
  - якнайшвидше (as fast as possible) — Example of emphatic prefix usage for A2 enrichment
  - станція (station) — Required for 'найглибша станція метро' cultural context
  - гора (mountain) — Required for 'найвища гора' context
  - печера (cave) — Recommended for the 'найдовша печера' cultural hook
  - літак (airplane) — Recommended for the 'найбільший літак' cultural hook
persona:
  voice: Encouraging Cultural Guide
  role: Restaurant Critic
grammar:
- superlative adjectives formation (най-)
- irregular superlatives (найкращий)
- emphatic superlatives (якнай-, щонай-)
- world records context
module_type: grammar
immersion: 50-60% Ukrainian
prerequisites:
- bigger-better-stronger
connects_to:
- preferences-and-choices
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

Research **The Best, The Worst** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: The Best, The Worst

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
