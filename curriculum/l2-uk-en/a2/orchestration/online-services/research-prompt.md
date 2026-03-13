# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-072
level: A2
sequence: 72
slug: online-services
version: '2.0'
title: Online Services
subtitle: Apps and Delivery
focus: practical
pedagogy: PPP
phase: A2.6 [Practical]
word_target: 2000
objectives:
- Learner can use Ukrainian delivery apps
- Learner can handle online banking basics
- Learner can communicate with support
- Learner can understand app notifications
content_outline:
- section: Вступ (Introduction)
  words: 275
  points:
  - 'Online services in Ukraine — cultural hook: ''State in a Smartphone'' (Держава у смартфоні) and the Diia (Дія) app; explain
    that Ukraine is the first country to grant digital passports full legal status (State Standard §3.11, §3.4)'
  - 'Cashless economy context: the ubiquity of Apple Pay/Google Pay even at street kiosks; introduce the cultural phrase ''skinuty
    na kartu'' (скинути на картку) as a standard social and commercial interaction'
- section: Презентація (Presentation)
  words: 450
  points:
  - 'Core UI vocabulary: focus on ''замовлення'' (order), ''кошик'' (cart), and ''додаток'' (app); note ''додаток'' is the
    standard term for a mobile application (State Standard §3.9)'
  - 'Grammar focus: Imperative mood for app commands (Натисніть, Оберіть, Оплатити, Підтвердіть); provide a list of common
    button labels and their functions'
  - 'Learner error alert: ''Замовлення'' is neuter gender (моє замовлення); drill agreement to prevent feminine-ending confusion
    (-я suffix pattern)'
- section: Практика (Practice)
  words: 475
  points:
  - 'Navigation and Cart logic: drill the distinction between ''додати в кошик'' (motion, Accusative) and ''у кошику'' (static
    location, Locative); use 5 minimal pairs to reinforce the case change'
  - 'Ordering logistics: distinguish between ''номер'' (ID/phone number) and ''кількість'' (quantity); example: ''номер замовлення''
    vs ''кількість товарів'''
  - 'Delivery specifics: collocations for ''доставка'' (безкоштовна доставка, час доставки, служба доставки); simulate tracking
    an order using ''номер для відстеження'''
- section: Діалоги (Dialogues)
  words: 400
  points:
  - 'Taxi and Transport: functional dialogue using apps like Uklon or Bolt; use terms ''замовити таксі'', ''місце посадки''
    (pickup), and ''місце призначення'' (destination)'
  - 'Banking and Support: customer support chat context; handling a ''скарга'' (complaint) or ''повернення'' (refund/return);
    common phrases like ''перевірити баланс'' and ''поповнити рахунок'''
  - 'Peer-to-peer transfers: a dialogue about splitting a bill using ''скинути на картку''; mention Monobank and Privat24
    as the primary platforms'
- section: Розповідь (Narrative)
  words: 275
  points:
  - 'Cultural narrative: The ''Monobank cat'' mascot and the social phenomenon of the ''banka'' (банка/jar) for collective
    fundraising and digital philanthropy'
  - 'Story of a digital day: using Diia for ID, ordering delivery via Glovo/Bolt, and donating to a ''banka'', emphasizing
    Ukraine''s status as a digital leader'
- section: Підсумок (Summary)
  words: 125
  points:
  - Review of key collocations (оформити замовлення, оплата карткою); final check on neuter gender agreement for 'замовлення'
  - Preparation for a2-70 (Introduction to Participles) and the A2 Final Exam (a2-71)
vocabulary_hints:
  required:
  - замовлення (order) — оформити замовлення, номер замовлення, скасувати замовлення; high frequency; note neuter gender (моє)
  - кошик (cart/basket) — додати в кошик (motion/Acc), ваш кошик порожній (Loc); standard UI term
  - доставка (delivery) — служба доставки, безкоштовна доставка, час доставки; essential for e-commerce
  - додаток (app/application) — мобільний додаток, завантажити додаток, через додаток; refers specifically to mobile software
  - картка (card) — банківська картка, оплата карткою, номер картки; central to 'skinuty na kartu' culture
  - переказ (transfer) — грошовий переказ, переказ на картку; common in banking apps
  - баланс (balance) — перевірити баланс, поповнити баланс; used for phones and banks
  - оплата (payment) — термінал для оплати, підтвердити оплату; standard checkout term
  recommended:
  - підтвердження (confirmation) — код підтвердження, чекати на підтвердження
  - відстеження (tracking) — номер для відстеження, відстежити замовлення
  - підтримка (support) — служба підтримки, написати в підтримку
  - скарга (complaint) — подати скаргу, розгляд скарги
  - повернення (return/refund) — оформити повернення коштів, повернення товару
  - банка (jar/fundraising tool) — скинути в банку, відкрити банку; specific Monobank cultural term
  - промокод (promo code) — ввести промокод, знижка за промокодом
activity_hints:
- type: match-up
  focus: Online services vocabulary
  items: 25
- type: quiz
  focus: Understand app interfaces (reading comprehension)
  items: 15
- type: fill-in
  focus: Complete service requests
  items: 15
connects_to:
- a2-75 (Introduction to Gerunds)
- a2-58 (Shopping and Services)
prerequisites:
- a2-71 (Texting and Messaging)
persona:
  voice: Encouraging Cultural Guide
  role: IT Support Specialist
grammar:
- App interface vocabulary (кошик, замовити)
- Banking terms (картка, переказ, баланс)
- Customer support phrases
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

Research **Online Services** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Online Services

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
