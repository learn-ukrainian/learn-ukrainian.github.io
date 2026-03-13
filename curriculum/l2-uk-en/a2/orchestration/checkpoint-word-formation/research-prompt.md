# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-049
level: A2
sequence: 49
slug: checkpoint-word-formation
version: '2.0'
title: 'Checkpoint: Word Formation'
subtitle: Review and Mastery Assessment
focus: checkpoint
pedagogy: TTT
phase: A2.4 [Word Formation]
word_target: 2000
objectives:
- Demonstrate confidence in identifying root families
- Deduce meaning using morphological clues
- Form words using correct prefixes and suffixes
- Correct common word formation errors
content_outline:
- section: Огляд та місток до B1 (Overview and Bridge to B1)
  words: 267
  points:
  - Skills assessment focusing on A2 standards (§4.3.1 degrees of comparison and §4.3.2
    aspect pairs) as a foundation for mastery
  - 'Transitioning to B1 requirements: introducing linguistic terminology (префікс,
    суфікс, корінь) in Ukrainian to prepare for advanced grammar'
  - 'Word formation as the engine of the language: how morphological awareness accelerates
    vocabulary acquisition and autonomy'
- section: Словотворчі префікси та дієслівний вид (Word-forming Prefixes and Verb
    Aspect)
  words: 433
  points:
  - 'Directional and aspectual prefixes: consolidating aspect pairs (робити – зробити,
    ділити – поділити) per Standard §4.3.2'
  - 'Learner error: avoiding Surzhyk and Russian calques (e.g., using correct спів-
    as in співробітник, but correcting wrong співпадати to збігатися)'
  - 'Cultural hook: ''Вороженьки'' (Ukrainian anthem) and the diminutive suffix -еньк
    — how word formation ''softens'' even the concept of enemies'
  - 'Prefix substitution practice: identifying how changing a prefix alters the lexical
    meaning of common A2 verbs'
- section: 'Суфіксальне багатство: -ння, -ість, -ач (Suffixal Richness: -ння, -ість,
    -ач)'
  words: 433
  points:
  - 'Standard §4.3.4: High productivity of -ння for verbal nouns (читання, навчання,
    життя); drill as the default ''action-to-noun'' converter'
  - 'Learner error: identifying the misuse of -к suffixes (розробка) where literary
    Ukrainian requires -ння (розроблення) for active processes'
  - 'Abstract and Agent nouns: using -ість (радість, незалежність) for concepts and
    -ач (слухач, викладач) for active roles'
  - 'Productive patterns: creating new nouns from known A2 verbs and adjectives using
    specified suffix sets'
- section: Ад’єктивні суфікси та родини коренів (Adjective Suffixes and Root Families)
  words: 433
  points:
  - 'Standard §4.3.6: Review of -ний and -ський suffixes for relational and national
    adjectives'
  - 'Learner error: confusion between -ний (general relation) and -овий (material/type)
    — stylistic and semantic distinctions'
  - 'Visualizing morphology: ''Word Families'' trees and ''Root Flowers'' (a core
    root in the center with derived petals) for visual learners'
  - 'Cultural hook: The creation of «мрія» (dream) by Mykhailo Starytsky — an example
    of conscious word formation shaping national identity'
- section: 'Підсумковий практикум: «Паляниця» та помилки (Final Workshop: «Palianytsia»
    and Errors)'
  words: 434
  points:
  - 'Comprehensive word analysis: breaking down complex words into morphemes to deduce
    meaning without a dictionary'
  - 'The ''Паляниця'' shibboleth: analysis of the -иця suffix and how word formation
    creates unique cultural identifiers'
  - 'Common mistake clinic: fixing wrong suffix calques and Surzhyk forms in a text-based
    context'
  - 'Final summary table: a visual guide to the most productive A2/B1 prefixes and
    suffixes as a reference for future modules'
vocabulary_hints:
  required:
  - корінь (root) — спільний корінь, корінь слова, пустити коріння (High frequency;
    foundation of the word)
  - префікс (prefix) — додати префікс, префікс з- (Mid frequency; changes direction/aspect)
  - суфікс (suffix) — словотворчий суфікс, суфікс -ння (Mid frequency; defines word
    class/nuance)
  - значення (meaning) — лексичне значення, змінити значення, має значення (Very High
    frequency)
  - утворення (formation) — словотворення, утворення слів, рік утворення (High frequency)
  - помилка (error) — груба помилка, виправити помилку, зробити помилку (High frequency;
    focus on 'growth points')
  - слово (word) — корінь слова, утворення слів
  - правильний (correct) — правильна форма, правильний суфікс
  recommended:
  - -ння (verbal noun suffix) — читання, навчання, життя (Extremely high productivity
    for processes)
  - -ість (abstract noun suffix) — радість, незалежність (High productivity for qualities)
  - -ач (agent noun suffix) — слухач, глядач, викладач (High productivity for people)
  - '-иця (suffix) — паляниця, крамниця (Context: cultural shibboleth)'
  - морфема (morpheme) — аналіз морфем
  - аналіз (analysis) — морфемний аналіз
  - синтез (synthesis) — словотворчий синтез
  - похідний (derivative) — похідне слово, похідне значення
activity_hints:
- type: quiz
  focus: Word formation comprehensive
  items: 12
- type: fill-in
  focus: Create correct forms
  items: 12
- type: error-correction
  focus: Fix formation errors
  items: 8
- type: match-up
  focus: Root families and meanings
  items: 12
- type: group-sort
  focus: Sort by suffix types
  items: 12
- type: cloze
  focus: Word formation in context
  items: 12
- type: unjumble
  focus: Word formation sentences
  items: 8
- type: translate
  focus: Form equivalents
  items: 8
connects_to:
- a2-50 (Food and Cooking)
prerequisites:
- 'a2-48 (Майстерня слів: Велика гра)'
persona:
  voice: Encouraging Cultural Guide
  role: Linguistics Professor
grammar:
- Word formation comprehensive review
- Root families review
- Prefix/suffix application
register: розмовний
immersion: 60-75% Ukrainian

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

Research **Checkpoint: Word Formation** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Checkpoint: Word Formation

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
