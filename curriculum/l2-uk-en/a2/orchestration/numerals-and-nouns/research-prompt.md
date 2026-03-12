# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-025
level: A2
sequence: 25
slug: numerals-and-nouns
version: '2.0'
title: Numerals and Nouns
subtitle: Counting Things Correctly
focus: grammar
pedagogy: PPP
phase: A2.2
word_target: 2000
objectives:
- Learner can use correct noun forms with numerals 1, 2-4, and 5+
- Learner can identify agreement zones for compound numbers
- Learner can use numerals in shopping contexts
- Learner can count years and age
- Learner can use numerals in accusative (animate vs inanimate)
- Learner can use numerals in dative case
sources:
- name: Ukrainian State Standard 2024 - Numerals
  url: https://mon.gov.ua/
  type: reference
  notes: Numeral-noun agreement requirements for A2
- name: Historical Ukrainian Grammar - Dual Number
  url: https://uk.wikipedia.org/wiki/Двоїна
  type: reference
  notes: Context for the 2-4 agreement pattern
content_outline:
- section: Вступ (Introduction)
  words: 300
  points:
  - 'The concept of ''Zones'' in Ukrainian counting — introduction of the mental model: Zone 1 (1), Zone 2 (2-4), and Zone
    3 (5-20) to replace the binary English singular/plural logic.'
  - 'State Standard §4.2.1.3 Alignment: Understanding the systemic requirements for designating quantity and measure in connection
    with cardinal numerals at the A2 level.'
  - 'Cultural Hook: Kyivan Rus Currency — The ''Gryvnia'' (гривня) as a IX-XIII century unit of weight and currency, grounding
    modern counting drills in a millennium of history.'
- section: 'Презентація: Зони 1 та 2 (Presentation: Zones 1 and 2)'
  words: 500
  points:
  - 'Zone 1: The ''One'' Rule — Focus on mandatory gender agreement (один долар, одна година, одне вікно); specific drill
    to prevent the error of using masculine for feminine nouns (e.g., ''один гривня'').'
  - 'Zone 2: Two, Three, Four (The Nominative Plural Zone) — Explanation of why Ukrainian differs from Russian; L1 Interference
    Alert: Russian speakers often use Genitive Singular (*два стола*), but Ukrainian requires Nominative Plural (два столи).'
  - 'Cultural Hook: The Dual Legacy (Двоїна) — Explaining why numbers 2-4 trigger unique patterns; mention the specific stress
    ''traces'' left in modern Ukrainian (e.g., дві кни́ги vs дві книжкИ) that reflect the ancient dual number.'
  - 'Gendered ''Two'': Distinguishing between ''два'' (masc/neut) and ''дві'' (fem); correcting the common learner error of
    ''два пляшки'' to ''дві пляшки''.'
- section: 'Презентація: Зона 3 та Складні Числівники (Presentation: Zone 3 and Compound Numerals)'
  words: 500
  points:
  - 'Zone 3: Five to Twenty (The Genitive Plural Zone) — Establishing the pattern for п''ять, десять, двадцять (п''ять гривень,
    десять євро); focus on the phonetics of soft endings.'
  - 'The ''11-14'' Trap: Reinforcing that numerals 11-14 belong strictly to Zone 3 (Genitive Plural) despite ending in digits
    1-4; preventing the over-application of the ''Last Digit Rule''.'
  - 'Compound Numerals and the ''Last Digit'' Rule: Demonstrating that in numbers like 21, 34, or 55, only the final word
    determines the agreement zone (e.g., 21 follows Zone 1 logic; 24 follows Zone 2).'
  - 'State Standard §4.2.2.2: Subject of Age — Using numerals to express age (Дідусеві вісімдесят років), focusing on the
    specific Genitive Plural forms required for ''years'' (років vs роки).'
- section: Практика на Ринку (Market Practice)
  words: 400
  points:
  - 'Market Context (Ринок): Immersion drills for natural repetition of counting currency and products (яблука, пляшки, кілограми)
    in a transactional setting.'
  - 'Currency Agreement: Drills comparing ''дві гривні'' (Zone 2) vs ''п''ять гривень'' (Zone 3) and ''один долар'' vs ''три
    долари''.'
  - 'The ''Euro'' Exception: Introducing ''євро'' as an indeclinable noun that remains constant regardless of the numeral
    (одне євро, десять євро), providing a cognitive break from complex agreement rules.'
- section: Діалоги та Одушевленість (Dialogues and Animacy)
  words: 300
  points:
  - 'Animacy Distinction in Accusative: Introducing the shift for animate objects with numerals; ''Бачу два столи'' (inanimate
    = Nominative form) vs ''Бачу двох друзів'' (animate = Genitive-like form).'
  - 'Shopping Dialogues: Roleplay involving specific quantities, prices, and ages of products (e.g., ''Цьому вину п''ять років''),
    integrating all three zones.'
  - 'Summary: Recapping the ''Zone'' model as a tool for self-correction when moving from A2 building blocks to B1 complexity.'
vocabulary_hints:
  required:
  - 'один / одна / одне (one) — Very High frequency; collocations: один долар, одна година, одне вікно'
  - 'два / дві (two) — High frequency; collocations: два квитки, дві гривні, дві пляшки; note gender agreement'
  - три (three) — High frequency; три дні, три гривні; Zone 2 agreement
  - чотири (four) — High frequency; чотири роки; Zone 2 agreement
  - п'ять (five) — High frequency; п'ять гривень, п'ять доларів; Zone 3 agreement
  - десять (ten) — High frequency; десять євро, десять хвилин; Zone 3 agreement
  - двадцять (twenty) — High frequency; двадцять хвилин; Zone 3 agreement
  - 'гривня (hryvnia) — High frequency (Market); Cultural note: unit of weight in Kyivan Rus'
  - долар (dollar) — High frequency (Travel/Finance); один долар, три долари, п'ять доларів
  - 'євро (euro) — High frequency (Finance); десять євро; Note: indeclinable'
  recommended:
  - ринок (market) — primary context for counting drills
  - кілограм (kilogram) — collocation for market counting
  - пляшка (bottle) — collocation for 'два/дві' gender drill
  - рік / роки / років (year/years) — for age expressions per State Standard
activity_hints:
- type: quiz
  focus: Accusative with numerals (animate vs inanimate)
  items: 8
- type: fill-in
  focus: Dative with numerals
  items: 8
- type: true-false
  focus: Numeral case rules
  items: 8
persona:
  voice: Encouraging Cultural Guide
  role: Inventory Manager
module_type: grammar
immersion: 60-75% Ukrainian
prerequisites:
- preferences-and-choices
connects_to:
- numeral-case-agreement
grammar:
- Вступ
- Зони 1 та 2
- Зона 3 та Складні Числівники
register: розмовний

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

Research **Numerals and Nouns** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Numerals and Nouns

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
