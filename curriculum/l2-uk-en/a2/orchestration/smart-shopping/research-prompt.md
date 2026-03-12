# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-029
level: A2
sequence: 29
slug: smart-shopping
version: '2.0'
title: Smart Shopping
subtitle: Comparisons and Choices
focus: vocabulary
pedagogy: PPP
phase: A2.2
word_target: 2000
objectives:
- Learner can compare products using comparative adjectives
- Learner can ask for recommendations and advice
- Learner can negotiate prices and ask for discounts
- Learner can express purchase decisions politely
sources:
- name: Ukrainian State Standard 2024 - Shopping
  url: https://mon.gov.ua/
  type: reference
  notes: Communicative requirements for shopping and negotiation
- name: Cultural Guide to Ukrainian Markets
  url: https://uk.wikipedia.org/wiki/Ринок
  type: reference
  notes: Social etiquette of bargaining in Ukraine
content_outline:
- section: Вступ (Introduction)
  words: 275
  points:
  - 'The philosophy of a ''Bazar'' vs a ''Supermarket'' — cultural hook: bargaining in Ukrainian markets is less about aggressive
    haggling and more about building rapport with a ''regular'' vendor (свій продавець) to secure ''friendly'' prices.'
  - 'The ''Freshness Hierarchy'' — cultural hook: products from ''grannies'' (бабусі) selling from their own gardens are perceived
    as superior to supermarket organic brands; introduction of traditional units like ''стакан'' (glass) for berries and ''пучок''
    (bunch) for herbs.'
- section: Презентація (Presentation)
  words: 500
  points:
  - 'Core transaction vocabulary based on §3.9 of the State Standard: ''Ціна'' (вигідна, зі знижкою), ''Знижка'' (надати знижку,
    акційна ціна), ''Решта'' (дати решту, правильна решта), and ''Чек'' (касовий чек, видати чек, зберігати чек).'
  - 'Grammar of comparison (§4.3.1): introduction of simple forms (солодший, важливіший) and compound forms (більш солодкий,
    менш кислий) for the comparative degree.'
  - 'Grammar of superlatives (§4.3.1): introduction of simple forms (найсолодший, найважливіший) and compound forms (найбільш
    солодкий, найменш кислий) for the superlative degree.'
  - 'Digital Shopping Essentials: high-frequency modern terms including ''кошик'' (cart), ''оформити замовлення'' (checkout),
    and ''доставка'' (delivery).'
- section: Практика (Practice)
  words: 475
  points:
  - 'Grammar Drill: focus on phonetic stem changes (г+ш -> жч) to avoid common learner errors like *дорожший* (correct: дорожчий)
    and *ближший* (correct: ближчий).'
  - 'Correction Exercise: targeting ''Double Comparison'' contamination, ensuring learners use either ''більш дешевий'' or
    ''дешевий'', but never *більш дешевший*.'
  - 'Comparative Particles Drill: practicing the correct use of ''ніж'' (than) and the preposition ''за'' + Accusative (дешевший
    за...) while explicitly avoiding the incorrect use of ''як'' for direct comparisons.'
- section: Продукція (Production)
  words: 475
  points:
  - 'Role-play scenario: Market negotiation vs. Supermarket checkout. Contrast the dynamic negotiation of ''ринок'' (Чи можна
    дешевше?) with the standard fixed prices of ''магазин''.'
  - 'Refusal and decision-making etiquette: practicing polite phrases like ''Я ще подумаю'' and using comparative forms for
    quality decisions (кращий варіант, найкраща якість).'
- section: Підсумок (Summary)
  words: 275
  points:
  - 'Review of communicative requirements for shopping as per State Standard §3.9: handling currency, units of volume, and
    consumer goods.'
  - Final summary of adjective degrees (§4.3.1) and a checklist for polite shopping interactions in both physical and digital
    Ukrainian contexts.
vocabulary_hints:
  required:
  - ціна (price) — вигідна ціна, ціна зі знижкою, фіксована ціна; high-frequency thematic term
  - знижка (discount) — сезонна знижка, акційна ціна, надати знижку; high-frequency thematic term
  - решта (change) — дати решту, правильна решта, дрібна решта; essential for practical transactions
  - чек (receipt) — касовий чек, видати чек, зберігати чек; high-frequency practical term
  - кращий (better) — набагато кращий, кращий варіант, найкраща якість; high-frequency irregular form
  - дешевий (cheap) — дешевший за..., найбільш дешевий товар; primary grammar anchor for comparisons
  recommended:
  - ринок (market) — базар, свій продавець; cultural marker for dynamic negotiation
  - кошик (basket/cart) — додати в кошик; essential for digital shopping register
  - оформити (to process/checkout) — оформити замовлення; essential for digital shopping register
  - доставка (delivery) — high-frequency term in modern Ukrainian infrastructure
  - стакан (glass) — traditional unit for measuring berries/seeds at markets
  - пучок (bunch) — traditional unit for measuring herbs/greens at markets
persona:
  voice: Encouraging Cultural Guide
  role: Personal Shopper
grammar:
- comparison in context
- asking for advice
- negotiation phrases
- decision making
module_type: vocabulary
immersion: 60-75% Ukrainian
prerequisites:
- complete-imperative
connects_to:
- checkpoint-aspect-comparison
register: розмовний
activity_hints:
- type: match-up
  focus: Match words to definitions
  items: 12
- type: fill-in
  focus: Complete sentences with vocabulary
  items: 8
- type: group-sort
  focus: Sort by category
  items: 10
- type: quiz
  focus: Choose correct word for context
  items: 10
- type: fill-in
  focus: Use words in sentences
  items: 6
- type: essay-response
  focus: Write using domain vocabulary

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

Research **Smart Shopping** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Smart Shopping

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
