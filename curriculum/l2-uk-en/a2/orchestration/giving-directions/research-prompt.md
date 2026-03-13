# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-068
level: A2
sequence: 68
slug: giving-directions
version: '2.0'
title: Giving Directions
subtitle: Navigating the City
focus: practical
pedagogy: PPP
phase: A2.6 [Practical]
word_target: 2000
objectives:
- Learner can ask for directions in a city
- Learner can give simple directions to others
- Learner can understand location descriptions
- Learner can use landmarks for navigation
content_outline:
- section: Вступ (Introduction)
  words: 325
  points:
  - City layout basics — focusing on standard urban vocabulary (street, square, intersection) as mandated by State Standard
    §3.5 for the A2 thematic catalogue.
  - 'Cultural hook: Arsenalna Metro Station — meeting at the deepest station in the world (105.5m), emphasizing the idiom
    «зустрінемось на Арсенальній» and describing the 5-minute escalator ride as a navigation milestone.'
  - 'Cultural hook: Lviv Rynok Square Fountains — navigating via the four mythological fountains (Neptune, Diana, Amphitrite,
    Adonis) at the corners of the square («біля Нептуна», «біля Діани»).'
- section: Презентація (Presentation)
  words: 525
  points:
  - Polite inquiries — teaching «Вибачте, як пройти до...?» with a focus on the high-frequency verb «пройти» (to pass/go through)
    as the standard for navigation requests.
  - Directional adverbs — presenting «прямо», «направо/праворуч», and «наліво/ліворуч»; explicitly addressing the common learner
    error of using the adjective «лівий/правий» instead of the adverb.
  - Motion verb distinction — presenting the strict contrast between «іти» (on foot) and «їхати» (by vehicle) as per Standard
    requirements, highlighting that English 'go' is split into two distinct concepts.
  - Imperative grammar — introducing the imperative mood for instructions («ідіть», «поверніть», «пройдіть») as specified
    in Standard §4.4.1.3 for giving directions/advice.
- section: Практика (Practice)
  words: 475
  points:
  - 'Error Correction Drill 1: Adjective vs. Adverb — practicing the distinction between «лівий» and «наліво/ліворуч»; correcting
    the error «Ідіть лівий» to «Ідіть наліво».'
  - 'Error Correction Drill 2: Motion Verbs — drilling the choice between foot vs. vehicle travel; correcting «Я йду на метро»
    to «Я їду на метро» using 5 situational prompts.'
  - Step-by-step navigation — practicing sequences like «пройдіть два квартали», «поверніть за ріг», and «перейдіть вулицю».
- section: Діалоги (Dialogues)
  words: 400
  points:
  - Destination Case Control — modeling the usage of prepositions «в/на» + Accusative for movement (Standard §4.2.2.4) vs.
    «біля/навпроти» + Genitive for static location.
  - Prepositional Government — explicitly drilling the Genitive case after «до»; addressing the learner error of using Nominative
    (e.g., «до парку» vs. wrong «до парк»).
  - Iconic Route Dialogues — simulating a route from a metro station to a museum using real landmarks (Arsenalna, Maidan)
    and sequencing markers (спочатку, потім, після цього).
- section: Розповідь (Narrative)
  words: 275
  points:
  - Navigation story — a narrative arc involving a character navigating from a train station to a specific landmark in Lviv
    or Kyiv, integrating «через міст», «на світлофорі», and «наступна зупинка».
  - Summary — reinforcing the distinction between «куди?» (motion + Accusative) and «де?» (static location + Locative/Genitive)
    to wrap up the module's grammar goals.
vocabulary_hints:
  required:
  - йти / їхати (to go on foot / by vehicle) — high frequency core; strictly separate based on transport mode
  - 'пройти (to go through/to get to) — collocation: «як пройти до...?»; high frequency A2 verb'
  - напрямок (direction) — general term for navigation and movement
  - 'прямо (straight) — collocation: «йти прямо», «пройдіть прямо два квартали»'
  - 'направо / праворуч (to the right) — frequency: high; use adverbs for movement instructions'
  - 'наліво / ліворуч (to the left) — frequency: high; distinguish from adjective «лівий»'
  - 'повернути (to turn) — collocation: «повернути за ріг», «поверніть на світлофорі»'
  - 'вулиця (street) — collocations: «на вулиці», «через вулицю», «по вулиці»'
  - 'площа (square) — cultural context: Площа Ринок (Lviv), Майдан Незалежності (Kyiv)'
  - 'перехрестя (intersection) — collocations: «на перехресті», «до перехрестя»'
  recommended:
  - 'квартал (block) — collocation: «пройти два квартали»'
  - 'міст (bridge) — collocation: «через міст» (across the bridge)'
  - 'світлофор (traffic light) — collocation: «на світлофорі»'
  - 'зупинка (stop) — collocations: «автобусна зупинка», «наступна зупинка»'
  - орієнтир (landmark) — used for navigation relative to visible objects
  - 'навпроти (opposite) — usage: «навпроти банку» (+ Genitive)'
  - 'поруч (nearby) — synonym for близько; usage: «тут поруч»'
activity_hints:
- type: match-up
  focus: Directions vocabulary
  items: 25
- type: match-up
  focus: Ask for directions
  items: 15
- type: quiz
  focus: Give directions to places
  items: 10
connects_to:
- a2-69 (Asking for Directions)
prerequisites:
- a2-67 (Scheduling Interviews)
persona:
  voice: Encouraging Cultural Guide
  role: Kyiv Metro Navigator
grammar:
- Asking for directions (як пройти?)
- Giving instructions (йдіть прямо, поверніть)
- Prepositions of place and movement
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

Research **Giving Directions** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Giving Directions

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
