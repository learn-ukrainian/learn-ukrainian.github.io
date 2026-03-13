# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-058
level: A2
sequence: 58
slug: shopping-services
version: '2.0'
title: Shopping and Services
subtitle: Buying and Paying
focus: vocabulary
pedagogy: PPP
phase: A2.5 [Vocabulary Expansion]
word_target: 2000
objectives:
- Learner can buy items in a shop
- Learner can ask for price and pay
- Learner can use service vocabulary (checkout, receipt)
- Learner can describe payment methods
content_outline:
- section: Вступ (Introduction)
  words: 275
  points:
  - 'Introduction to the shopping theme aligned with State Standard §3.9. Distinguish between different store types: магазин
    (general shop), супермаркет (supermarket), and ринок (traditional market).'
  - 'Cultural landmark spotlight: Bessarabka Market (Бессарабський ринок) in Kyiv. Explain its history (built 1912 by Lazar
    Brodsky) and its Art Nouveau architecture as an urban monument.'
  - Introduce the famous Kyiv idiom 'Expensive as in Bessarabka' (Дорого, як на Бессарабці) to discuss price perception and
    the market's premium reputation.
- section: Лексика та культура (Vocabulary and Culture)
  words: 475
  points:
  - 'Essential commodities from State Standard §3.9: groceries (овочі, фрукти, м’ясо, хліб, молочні продукти) and hygiene
    products (мило, шампунь, зубна паста).'
  - 'Traditional market etiquette: Explain why ''Чи є у вас свіже...?'' (Is there at you fresh...?) is the standard polite
    opener, contrasted with the unnatural direct translation ''Ти маєш...?'' (Do you have?).'
  - 'Units of weight and volume (одиниці ваги й об’єму): kilo, liter, and pieces (штуки) as required by the Standard for transactional
    competency.'
- section: Граматика (Grammar)
  words: 500
  points:
  - 'Direction vs. Location: Correcting the common learner error of using the Locative (''Я йду в магазині'') instead of the
    Accusative (''Я йду в магазин'') for motion toward a shop.'
  - 'The Instrumental case for payment methods: Explicit drill on ''платити карткою'' (pay with card) to fix the frequent
    error ''платити картою''. Contrast with ''платити готівкою'' (pay with cash).'
  - 'Verbal patterns for shopping: Conjugation and usage of купувати (to buy), продавати (to sell), and платити (to pay) in
    the context of prices (Скільки коштує?).'
- section: Діалоги та практика (Dialogues and Practice)
  words: 475
  points:
  - 'Simulated market dialogue: Practice asking about freshness, weight, and price using natural immersion patterns. Roleplay
    as a Bessarabka vendor and an encouraging guide.'
  - 'Supermarket checkout flow: Dialogues involving asking for a bag (пакет), a receipt (потрібен чек/фіскальний чек), and
    clarifying payment method (карткою чи готівкою?).'
  - 'Correction drill for ''Do you have?'': Replace the learner''s direct translation ''Ти маєш хліб?'' with the natural ''Чи
    є у вас хліб?'' in various shopping contexts.'
- section: Послуги та підсумок (Services and Summary)
  words: 275
  points:
  - 'Introduction to basic services per State Standard §3.11: перукарня (hairdresser), хімчистка (dry cleaning), and ремонт
    (repair). Focus on simple service requests.'
  - Final summary of high-frequency vocabulary and collocations. Review of the distinction between buying (what - Accusative)
    and paying (how - Instrumental).
vocabulary_hints:
  required:
  - магазин (store) — йти в магазин, продуктовий магазин; High Frequency (Standard §3.9)
  - ціна (price) — висока ціна, яка ціна?, ціна за кілограм; High Frequency
  - купувати (to buy) — купувати продукти, купувати одяг; High Frequency
  - платити (to pay) — платити карткою, платити готівкою; Instrumental case requirement; High Frequency
  - гроші (money) — паперові гроші, мати гроші; High Frequency (Standard §3.9)
  - картка (card) — банківська картка, платити карткою; High Frequency
  - готівка (cash) — платити готівкою, мати готівку; Medium Frequency
  - чек (receipt) — потрібен чек, фіскальний чек; Medium Frequency
  recommended:
  - знижка (discount) — знижка 50%, сезонні знижки; Medium Frequency
  - каса (checkout) — де каса?, на касі
  - здача (change) — ваша здача, без здачі
  - пакет (bag) — чи потрібен вам пакет?
  - примірка (fitting room) — де примірка?
  - розмір (size) — який розмір?, мій розмір
  - перукарня (hairdresser) — йти в перукарню; (Standard §3.11)
  - хімчистка (dry cleaning) — віддати в хімчистку; (Standard §3.11)
  - ремонт (repair) — ремонт взуття, ремонт одягу; (Standard §3.11)
activity_hints:
- type: match-up
  focus: Shopping vocabulary
  items: 30
- type: cloze
  focus: Store conversation
  items: 12
- type: fill-in
  focus: Complete shopping sentences
  items: 15
- type: cloze
  focus: Buy items at a store
  items: 8
connects_to:
- a2-59 (Sports and Fitness)
- a2-63 (At the Bank)
prerequisites:
- a2-57 (Education and Learning)
persona:
  voice: Encouraging Cultural Guide
  role: Bessarabka Market Vendor
grammar:
- Payment verbs (платити, купувати, продавати)
- Accusative for prices and objects
- Instrumental for means (карткою, готівкою)
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

Research **Shopping and Services** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Shopping and Services

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
