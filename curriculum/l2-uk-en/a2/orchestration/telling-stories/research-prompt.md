# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-031
level: A2
sequence: 31
slug: telling-stories
version: '2.0'
title: Telling Stories
subtitle: Sequencing Events in Narrative
focus: vocabulary
pedagogy: PPP
phase: A2.2
word_target: 2000
objectives:
- Learner can sequence events using connectors
- Learner can tell a simple story with a beginning, middle, and end
- Learner can describe unexpected events
- Learner can use time markers to structure narrative
sources:
- name: Ukrainian State Standard 2024 - Narration
  url: https://mon.gov.ua/
  type: reference
  notes: Narrative and sequence requirements for A2
- name: Stylistics of Ukrainian Language - Narrative Flow
  url: https://uk.wikipedia.org/wiki/Оповідь
  type: reference
  notes: Logical connectors in Ukrainian prose
content_outline:
- section: Вступ (Introduction)
  words: 325
  points:
  - The transition from listing events to a cohesive narrative as mandated by State Standard §1.4.1.1.1 (simple sequences).
  - 'The ''Robot Style'' problem: why beginners overuse «і» (and) for every action and how sequencing words create natural
    flow.'
  - 'Cultural Hook: The Village Storyteller (Казкар) — an introduction to the communal art of oral tradition and the storyteller''s
    role as a cultural anchor.'
- section: 'Презентація: Дорожні знаки часу (Presentation: Road Signs of Time)'
  words: 475
  points:
  - 'Visual Metaphor: The «Timeline Road» using «спочатку», «потім», and «нарешті» as the cars of a train connecting the story.'
  - 'Learner Error: Confusing the adverb «спочатку» (at first) with the prepositional phrase «з початку» (from the start)
    — drill pattern: «Спочатку я поснідав» vs. «З початку книги».'
  - 'Word Order Rule: Time markers as ''Theme'' — placing markers at the start of sentences (e.g., «Потім я пішов...») to
    avoid the common error of trailing them like English ''afterwards''.'
- section: 'Презентація: Драма та несподіванки (Presentation: Drama and Surprises)'
  words: 400
  points:
  - 'The ''Plot Twist'' button: Using «раптом» and «несподівано» to break expectation and add drama to a narrative.'
  - 'Relative time markers for depth: «раніше», «недавно», «давно» and their roles in setting the backstory context.'
  - 'Narrative Registers: Fairytale opening formulas like «Жили-були...» (Once upon a time) and how they signal the start
    of a story.'
- section: 'Практика: Сміхова культура (Practice: Laughter Culture)'
  words: 400
  points:
  - 'Cultural Hook: Ukrainian Laughter (Сміхова культура) — drilling the timing of «потім» and «раптом» using the ''Anekdot''
    format to land punchlines.'
  - 'Drill: Replacing ''Robot Style'' chains of «і» with varied sequencing connectors in a chaotic morning routine scenario.'
  - Minimal pair drills for «спочатку» vs «з початку» in context-dependent sentences.
- section: Продукція та підсумок (Production and Summary)
  words: 400
  points:
  - 'Task: Telling a fishing story or travel adventure using at least five different sequencing markers with correct sentence-initial
    placement.'
  - 'Final review of the Village Storyteller persona: the importance of oral storytelling in maintaining moral and historical
    narratives.'
  - 'Checklist for learners: Did I avoid «і» chains? Are my time markers at the start? Did I use a ''Plot Twist'' marker?'
vocabulary_hints:
  required:
  - 'спочатку (at first) — спочатку я..., спочатку було...; High frequency; Note: avoid confusion with «з початку» (from the
    start)'
  - 'потім (then/afterwards) — а потім, потім ми...; High frequency; Note: typically starts the sentence in natural narration'
  - нарешті (finally) — нарешті прийшов, нарешті сталося; High frequency; signals the narrative conclusion
  - раптом (suddenly) — і раптом побачив, раптом почався; Medium frequency; the 'Plot Twist' or drama marker
  - одного разу (once/one day) — одного разу влітку, одного разу я...; Medium frequency; standard narrative opening
  - несподівано (unexpectedly) — несподівано з'явився, несподівано для всіх; used for adding narrative tension
  - 'казка (fairytale) — читати казку, народна казка; key opening formula: «Жили-були...»'
  - анекдот (joke/anecdote) — розповідати анекдот, смішний анекдот; requires precise timing of connectors
  recommended:
  - казкар (storyteller) — шанований казкар; refers to the traditional oral storyteller persona
  - несподіванка (a surprise) — приємна несподіванка; noun form related to «несподівано»
  - раніше (earlier/before) — раніше я не знав; used for relative time reference
  - давно (long ago) — дуже давно; indicates distant past in storytelling
persona:
  voice: Encouraging Cultural Guide
  role: Village Storyteller
grammar:
- sequencing words (спочатку, потім, нарешті)
- time markers (раптом, одного разу)
- narrative tenses
- structuring a story
module_type: vocabulary
immersion: 60-75% Ukrainian
prerequisites:
- checkpoint-aspect-comparison
connects_to:
- because-and-although
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

Research **Telling Stories** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Telling Stories

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
