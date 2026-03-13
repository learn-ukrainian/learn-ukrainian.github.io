# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-040
level: A2
sequence: 40
slug: checkpoint
version: '2.0'
title: Checkpoint
subtitle: Complex Sentences & Health
focus: checkpoint
pedagogy: TTT
phase: A2.2
word_target: 2000
objectives:
- Learner can build complex arguments using logical connectors
- Learner can use relative clauses to define and describe
- Learner can navigate medical situations confidently
- Learner can correct common errors in complex sentences
sources:
- name: Ukrainian State Standard 2024 - A2.2 Assessment
  url: https://mon.gov.ua/
  type: reference
  notes: Proficiency benchmarks for complex sentences and health communication at
    A2.2
- name: Review of Ukrainian Syntax for A2
  url: https://uk.wikipedia.org/wiki/Синтаксис_української_мови
  type: reference
  notes: Synthesized logic for coordinating multiple subordinate clauses
content_outline:
- section: Вступ та цілі (Introduction and Objectives)
  words: 267
  points:
  - 'Mapping Level A2.2 proficiency: transitioning from simple reports to complex
    logical structures aligned with State Standard §4.4.2'
  - Defining competencies for health communication, pharmacy interactions, and describing
    physical states per State Standard §3.12
- section: 'Синтаксис логіки: Причина та Мета (Syntax of Logic: Cause and Purpose)'
  words: 500
  points:
  - 'Conjunction Masterclass: Cause & Effect (Тому що, бо, через). Focus on register:
    correcting the overuse of ''тому що'' in casual speech where ''бо'' is more natural'
  - 'The Logic of Intent: Purpose & Desire (Щоб + Inf vs Щоб + Past). Critical drill
    for the ''щоб'' (in order to) vs ''що б'' (what would) learner error'
  - 'Scaffolding causal and final clauses with specific medical contexts: explaining
    why one goes to the doctor or takes specific medicine'
- section: Опис та послідовність дій (Description and Sequence of Actions)
  words: 500
  points:
  - 'The Relative Chameleon: Using ''який'' to define nouns. Targeted correction of
    ''який agreement'' errors (matching gender/case with the antecedent noun)'
  - 'Time Coordination: Integrating ''коли'', ''поки'', and ''після того як'' to sequence
    health-related events (e.g., ''Take medicine after you eat'')'
  - 'Preparing for B1 syntax: how complex A2 structures pave the way for conditional
    ''якби'' sentences'
- section: Медицина, тіло та народні методи (Medicine, Body and Folk Methods)
  words: 467
  points:
  - Integrating body parts (голова, живіт, горло, рука/нога) with pain expression
    using Accusative and Genitive cases
  - 'Pharmacy interactions: Correcting the literal translation of ''take medicine''
    from ''брати'' to ''приймати ліки'' (formal) or ''пити ліки'' (colloquial)'
  - 'Cultural Hook: Traditional Ukrainian treatments for colds—hot tea with raspberry
    (малина), viburnum (калина), and honey (мед) as natural antipyretics'
- section: Практичне застосування та підсумок (Practical Application and Summary)
  words: 266
  points:
  - 'Integration Challenge: navigating a medical consultation by combining cause,
    purpose, and description skills'
  - 'Cultural Hook: Usage of the toast ''Будьмо!'' (Let us be!) in social health rituals,
    emphasizing its literal meaning of being healthy and alive'
vocabulary_hints:
  required:
  - голова (head) — болить голова (headache), мити голову (wash hair); high-frequency
    body part
  - горло (throat) — червоне горло (red/sore throat), болить горло (sore throat);
    high frequency for illness
  - температура (temperature/fever) — висока температура (high fever), міряти температуру
    (take temperature)
  - ліки (medicine) — приймати ліки (formal/correct), пити ліки (colloquial); avoid
    literal 'take' translations
  - лікар (doctor) — йти до лікаря (go to the doctor), записатися до лікаря (make
    an appointment)
  - живіт (stomach/belly) — болить живіт (stomach ache); essential for pain description
  - застуда (cold) — мати застуду (have a cold), лікувати застуду (treat a cold)
  recommended:
  - рука/нога (arm/hand / leg/foot) — зламати руку (break an arm), права нога (right
    leg)
  - малина (raspberry) — малина з чаєм; used in traditional cold treatments
  - калина (viburnum) — чай з калиною; traditional natural medicine
  - мед (honey) — додавати мед у чай; natural antipyretic
  - 'щоб (in order to) — conjunction of purpose; learner error: distinguish from ''що
    б'''
  - бо (because) — natural/casual register; contrast with formal 'тому що'
persona:
  voice: Encouraging Cultural Guide
  role: Border Control Officer
grammar:
- logical connectors review
- relative clauses review
- health vocabulary review
- complex sentence structure
module_type: checkpoint
immersion: 60-75% Ukrainian
prerequisites:
- health-and-body
connects_to:
- basic-motion-prefixes
register: розмовний
activity_hints:
- type: quiz
  focus: Review all covered topics
  items: 15
- type: fill-in
  focus: Apply learned structures
  items: 10
- type: match-up
  focus: Match concepts from modules
  items: 10
- type: error-correction
  focus: Find errors across topics
  items: 8
- type: essay-response
  focus: Integrative writing task

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

Research **Checkpoint** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Checkpoint

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
