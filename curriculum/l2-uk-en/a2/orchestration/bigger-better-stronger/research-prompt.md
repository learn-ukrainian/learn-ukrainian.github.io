# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-022
level: A2
sequence: 22
slug: bigger-better-stronger
version: '2.0'
title: Bigger, Better, Stronger
subtitle: The Comparative Degree
focus: grammar
pedagogy: PPP
phase: A2.2
word_target: 2000
objectives:
- Learner can form comparative adjectives
- Learner can compare two objects using 'ніж' and 'за'
- Learner can identify and use irregular comparative forms
- Learner can describe differences in quality and quantity
sources:
- name: Ukrainian State Standard 2024 - Comparison
  url: https://mon.gov.ua/
  type: reference
  notes: Comparative adjective requirements for A2
- name: Ukrainian Adjective Reference
  url: https://uk.wikipedia.org/wiki/Прикметник
  type: reference
  notes: Complete comparison paradigms
content_outline:
- section: 'Вступ (Introduction: The Arena of Comparison)'
  words: 325
  points:
  - 'Introduction of the ''Sports Commentator'' persona: setting the stage for comparing athletes, landmarks, and daily items
    using Ukrainian comparatives.'
  - 'Philosophical and cultural concept of comparison through proverbs: «Добре слово краще, ніж готові гроші» (quality comparison)
    and «Краще один раз побачити, ніж сто разів почути» (classic structure).'
  - 'English vs Ukrainian comparative logic: explicitly addressing the common learner error of double comparatives like «більш
    кращий» (more better) and teaching the correct synthetic («кращий») or analytic («більш хороший») forms.'
- section: 'Презентація: Творення ступенів (Presentation: Forming the Comparative)'
  words: 525
  points:
  - 'Regular formation using suffixes -іший and -ший: guided discovery of when to use each, aligned with State Standard §4.3.1
    requirements for A2.'
  - 'Deep dive into mandatory stem alternations (г→ж, к→ч, х→ш): specific focus on ''дорогий→дорожчий'', ''близький→ближчий'',
    and ''тихий→тихіший'' to preempt the ''alternation neglect'' error.'
  - 'Irregular (suppletive) comparatives: ''The Big 10'' master list, prioritizing high-frequency pairs like ''великий–більший'',
    ''малий–менший'', ''гарний–кращий'', and ''поганий–гірший''.'
  - 'Phonetic focus: training the ''Sports Commentator'' voice to emphasize the doubled consonants or shifts in stressed syllables
    during rapid comparison.'
- section: 'Структури порівняння: ніж vs за (Comparison Structures)'
  words: 475
  points:
  - 'Contrastive analysis of ''ніж'' (than) vs ''за'' (than): explaining that ''ніж'' is followed by the Nominative case while
    ''за'' requires the Accusative case.'
  - 'Error Correction Lab: focusing on the ''Case Confusion after за'' error (e.g., correcting *за він* to ''за нього'' and
    *за я* to ''за мене'').'
  - 'Using intensifiers for nuanced commentary: ''набагато'' (much), ''трохи'' (a little), and ''значно'' (significantly)
    to modify comparisons (e.g., ''набагато дорожчий'', ''трохи дешевший'').'
  - The dual comparative structure through the proverb «Чим старіший, тим мудріший» (The older, the wiser).
- section: 'Практика: Рекорди України (Practice: Ukrainian Records)'
  words: 400
  points:
  - 'Situational drills comparing Ukrainian landmarks: ''Київська телевежа'' (380m) is 55m taller (''вища'') than the Eiffel
    Tower; ''Батьківщина-Мати'' (102m) vs other European monuments.'
  - 'Retail and quality comparison drills: using frequency-based collocations like ''більший розмір'' (larger size), ''краща
    якість'' (better quality), and ''дорожчий товар'' (more expensive item).'
  - 'Transformation drills: converting positive adjectives into comparative forms with a focus on stem-shifting words found
    in sports (e.g., ''швидкий→швидший'', ''дужий→дужчий'').'
- section: Діалоги та Висновки (Dialogues and Summary)
  words: 275
  points:
  - 'Market commentary dialogue: comparing prices, quality, and quantity between different stalls using ''кращий спосіб''
    and ''менша кількість''.'
  - 'Family and age context: using ''старший за віком'' (older by age) and ''молодший брат'' in natural conversation.'
  - Final review of the 'Consonant Shift' checklist and a summary of 'ніж/за' case requirements to ensure A2 competency.
vocabulary_hints:
  required:
  - більший (bigger) — більший розмір (larger size), більша частина (greater part); high frequency
  - менший (smaller) — менша кількість (smaller quantity), менший розмір (smaller size)
  - кращий (better) — кращий результат (better result), краща якість (better quality), кращий спосіб (better way)
  - гірший (worse) — focus on quality and outcomes
  - вищий (taller/higher) — вищий на зріст (taller), вищий за мене (taller than me); use for buildings/people
  - нижчий (lower/shorter) — physical height or level
  - дорожчий (more expensive) — дорожчий товар (more expensive item), набагато дорожчий (much more expensive); note stem shift
    г→ж
  - дешевший (cheaper) — дешевший варіант (cheaper option), трохи дешевший (a little cheaper)
  - старший (older) — старший брат (older brother), старший за віком (older by age)
  - молодший (younger) — family and social context
  - довший (longer) — duration or physical length
  - коротший (shorter) — duration or physical length
  - ширший (wider) — physical dimensions
  - вужчий (narrower) — physical dimensions; note stem shift зк→жч
  - ніж (than) — comparison particle followed by Nominative case
  recommended:
  - за (than) — preposition requiring Accusative case (за мене, за нього); critical learner error point
  - набагато (much/far) — intensifier for comparative adjectives
  - трохи (a little) — intensifier for comparative adjectives
  - значно (significantly) — formal/analytical intensifier
  - швидший (faster) — high relevance for sports persona; formed by adding -ший to швидк- (dropping -кий)
activity_hints:
- type: fill-in
  focus: Transform positive to comparative
  items: 15+
- type: fill-in
  focus: Comparison sentences with ніж/за
  items: 12+
- type: quiz
  focus: Which is bigger/better/etc.?
  items: 12+
- type: match-up
  focus: Adjective + comparative form
  items: 12+
- type: fill-in
  focus: Irregular comparative forms
  items: 10+
connects_to:
- a2-23 (The Best, The Worst)
- a2-24 (Preferences and Choices)
- a2-29 (Smart Shopping)
prerequisites:
- A1 adjective agreement
- a2-19 (Possessive Sviy)
- Basic sentence structure
persona:
  voice: Encouraging Cultural Guide
  role: Sports Commentator
grammar:
- comparative adjectives formation
- regular comparatives (-іший)
- irregular comparatives (кращий, більший)
- comparison structures (ніж, за)
module_type: grammar
immersion: 50-60% Ukrainian
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

Research **Bigger, Better, Stronger** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Bigger, Better, Stronger

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
