# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-038
level: A2
sequence: 38
slug: time-clauses
version: '2.0'
title: Time Clauses
subtitle: When, While, and After
focus: grammar
pedagogy: PPP
phase: A2.2
word_target: 2000
objectives:
- Learner can sequence events using time conjunctions
- Learner can describe simultaneous actions using 'поки' and 'коли'
- Learner can distinguish between 'перед тим як' and 'після того як'
- Learner can tell stories with clear chronological structure
sources:
- name: Ukrainian State Standard 2024 - Temporal Clauses
  url: https://mon.gov.ua/
  type: reference
  notes: Communicative requirements for sequencing events and temporal coordination at A2
- name: Grammar of Ukrainian Language - Time Conjunctions
  url: https://uk.wikipedia.org/wiki/Складнопідрядне_речення_часу
  type: reference
  notes: Detailed rules for 'коли', 'поки', and 'як тільки'
content_outline:
- section: Вступ (Introduction)
  words: 275
  points:
  - 'Life as a sequence of events: alignment with Ukrainian State Standard §1.4.1.1 regarding the creation of a narrative
    monologue as a simple sequence of events.'
  - 'The cultural concept of time and patience: Introduction of the proverb «Всьому свій час» (Everything has its time) to
    frame the importance of temporal logic.'
- section: 'Презентація: Граматичні основи (Presentation: Grammatical Foundations)'
  words: 525
  points:
  - 'Simultaneity and Points in Time: Contrast between «коли» (point/when) and «поки» (process/while) using a visual timeline
    for clarity.'
  - 'Sequencing events: Detailed rules for «перед тим як» (before) and «після того як» (after), focusing on the necessity
    of the linkers «тим/того».'
  - 'Common Error Correction: Addressing the ''If confusion'' where learners use «коли» for conditional «якщо» (e.g., «Якщо
    я матиму час...» vs «Коли я матиму час...»).'
  - 'Pedagogical Distinction: Explicitly contrast the structure of «перед» + Noun (prepositional phrase) vs «перед тим як»
    + Verb (time clause).'
- section: 'Презентація: Складні випадки та культура (Presentation: Complex Cases and Culture)'
  words: 475
  points:
  - 'The ''Until Trap'': Explaining the double negative requirement in «поки не» clauses (e.g., «Я чекаю, поки ти не прийдеш»).'
  - 'Cultural Hook: The Ukrainian Christmas Eve (Свята Вечеря) tradition of waiting to eat «поки не зійде перша зірка» (until
    the first star appears).'
  - 'Immediacy and Frequency: Usage of «щойно» (just/as soon as) and «як тільки» (as soon as) in spoken register, plus «кожного
    разу, коли...» for habits.'
- section: Практика та корекція помилок (Practice and Error Correction)
  words: 400
  points:
  - 'Drill: Identifying and fixing the missing linker error (e.g., correcting «Перед я пішов» to «Перед тим як я пішов»).'
  - 'Transformation exercises: Converting simple prepositional phrases into complex time clauses using the research-based
    contrast patterns.'
  - 'Negative logic drills: Practicing the «поки не» structure to internalize the Ukrainian negation of the limit-action.'
- section: Продукція та діалоги (Production and Dialogues)
  words: 325
  points:
  - 'Monologue production: Reporting a busy morning schedule or a trip itinerary, strictly following the State Standard requirement
    for sequencing.'
  - 'Dialogue: Planning a shared event where participants use «поки», «як тільки», and «після того як» to coordinate their
    actions.'
vocabulary_hints:
  required:
  - 'коли (when) — High frequency/Core. Collocations: Коли ти прийдеш? Коли я був маленьким...'
  - 'поки (while/until) — High frequency/Core. Collocations: Поки я чекаю... Поки що (meanwhile/so far).'
  - 'перед тим як (before [doing something]) — Medium frequency. Usage: Перед тим як вийти... Перед тим як лягти спати...'
  - 'після того як (after [doing something]) — Medium frequency. Usage: Після того як ми закінчили... Після того як він подзвонив...'
  - 'щойно (just/as soon as) — Medium frequency/Spoken register. Collocations: Щойно я зайшов...'
  - 'як тільки (as soon as) — Medium frequency/Spoken register. Collocations: Як тільки зможу...'
  recommended:
  - 'поки не (until) — Grammatical logic: requires a double negative in Ukrainian.'
  - якщо (if) — Essential contrast word to avoid the 'when/if' confusion at A2.
  - кожного разу, коли (every time when) — Frequency pattern for habit description.
persona:
  voice: Encouraging Cultural Guide
  role: Orchestra Conductor
grammar:
- time connectors (коли, поки, після того як)
- sequence of tenses
- aspect in time clauses
- simultaneous vs sequential actions
module_type: grammar
immersion: 60-75% Ukrainian
prerequisites:
- which-one
connects_to:
- health-and-body
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

Research **Time Clauses** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Time Clauses

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
