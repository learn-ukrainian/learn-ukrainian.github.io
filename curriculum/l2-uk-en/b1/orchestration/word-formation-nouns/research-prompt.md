# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-056
level: B1
sequence: 56
slug: word-formation-nouns
version: '2.0'
title: Словотвір іменників
subtitle: 'Noun Word Formation: Suffixes, Prefixes, and Composition'
focus: grammar
pedagogy: PPP
phase: B1.7 [Word Formation and Lexicology]
word_target: 4000
objectives:
- Learner can form nouns using productive Ukrainian suffixes
- Learner can use common noun prefixes (без-, не-, під-, пере-)
- Learner can form and analyze compound nouns
- Learner can build word formation chains from a root
content_outline:
- section: 'Вступ: Як народжуються нові слова (Introduction: How New Words Are Born)'
  words: 500
  points:
  - 'State Standard §4.3.3: word formation as B1 requirement'
  - 'Overview of word formation types: суфіксальний, префіксальний, префіксально-суфіксальний, основоскладання'
  - 'Morpheme review: корінь (root), суфікс (suffix), префікс (prefix), закінчення (ending)'
- section: Суфіксальний словотвір (Suffixation)
  words: 900
  points:
  - 'Agent nouns: -ник (працівник), -ець (борець), -ач (читач), -тель (учитель)'
  - 'Abstract nouns: -ість (радість), -ння (читання), -ство (мистецтво), -ота (доброта)'
  - 'Place nouns: -ня (читальня, пекарня), -ище (летовище, стрільбище) — note: diminutive suffixes covered in dedicated module
    b1-52 (diminutives-master-class)'
  - 'Feminine counterparts: -ка (студентка), -иня (майстриня), -еса (поетеса)'
  - 'Learner drill: verb stem + suffix → noun (читати→читання→читач→читальня)'
- section: Префіксальний словотвір (Prefixation)
  words: 700
  points:
  - 'Common noun prefixes: без- (безробіття), не- (нещастя), під- (підзаголовок), пере- (перебудова)'
  - 'Negative: не- (невдача, нелюдь) vs без- (безнадія, безхатько)'
  - 'Spatial/temporal: перед- (передмова), після- (післямова), над- (надзвичайність)'
  - 'Learner error: confusing не- prefix with не particle'
- section: Основоскладання (Compound Nouns)
  words: 700
  points:
  - 'With connecting vowels: о/е (пароплав, землетрус, водоспад)'
  - 'Without connecting vowels: кіносеанс, авіаквиток'
  - 'Hyphenated compounds: генерал-лейтенант, прем''єр-міністр'
  - 'Cultural compounds: хлібосольство (hospitality), землеробство (agriculture)'
  - 'Modern compounds: кіберзахист, євроінтеграція'
- section: Словотвірні ланцюжки (Word Formation Chains)
  words: 700
  points:
  - 'Building word families: земля→земляний→землянин→заземлення→підземний'
  - 'Productivity patterns: which suffixes attach to which stems'
  - 'Word families from single roots: писати→письмо→письменник→письменність→записка'
  - 'Practice: given a root, build the maximum chain'
- section: 'Практика: Розпізнавання та творення (Practice: Recognition and Creation)'
  words: 500
  points:
  - Decompose complex nouns into morphemes
  - Create nouns from given verbs/adjectives using correct suffixes
  - 'Reading comprehension: identify word formation patterns in text'
  - Guess meaning of unknown nouns from known roots + suffixes
vocabulary_hints:
  required:
  - словотвір (word formation) — словотвір іменників; core linguistic term §4.3.3
  - суфікс (suffix) — словотвірний суфікс; morphological term
  - префікс (prefix) — словотвірний префікс; morphological term
  - корінь (root) — корінь слова, спільнокореневі слова
  - основа (stem) — основа слова, твірна основа
  - закінчення (ending) — нульове закінчення, відмінкове закінчення
  recommended:
  - основоскладання (compounding) — specialized term for compound formation
  - ланцюжок (chain) — словотвірний ланцюжок
  - продуктивний (productive) — продуктивний суфікс; linguistic productivity
  - морфема (morpheme) — значуща частина слова
  - гніздо (nest) — словотвірне гніздо; word family
activity_hints:
- type: fill-in
  focus: Form nouns from verbs/adjectives using correct suffix
  items: 20
- type: match-up
  focus: Match suffix to its meaning category (agent, abstract, diminutive)
  items: 15
- type: quiz
  focus: Identify word formation type (suffix, prefix, compound)
  items: 12
- type: error-correction
  focus: Fix incorrect suffix/prefix usage
  items: 10
connects_to:
- 'b1-57 (Word Formation: Modifiers)'
prerequisites:
- 'b1-55 (Checkpoint: Advanced Grammar)'
persona:
  voice: Senior Language & Culture Specialist
  role: Linguistic Researcher
grammar:
- Noun suffixation (-ник, -ець, -ість, -ння, -ство)
- Noun prefixation (без-, не-, під-, пере-, перед-)
- Compound nouns (основоскладання)
- Word formation chains (словотвірні ланцюжки)
register: нейтральний
immersion: 75-100% Ukrainian

```

**Level constraints quick-ref:**

```
# B1 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. Grammar explained IN Ukrainian. English only for disambiguation of false friends. Sentences max 30 words.`, etc.

## Grammar Scope

**Allowed:** All grammar constructions. Participles. Complex subordinate clauses.
Max 30 words per Ukrainian sentence. Max 4 clauses.

## Immersion Strategy (B1)

| Phase | Modules | Immersion | Notes |
|-------|---------|-----------|-------|
| B1.0 (Bridge) | M01-05 | Mixed | Teach grammar metalanguage; English scaffolding for abstract concepts |
| B1.1+ (Core) | M06-92 | **100%** | Full Ukrainian. English ONLY in vocabulary table translations |

**B1.0 Bridge modules:** English grammar term explanations allowed as transition from A2.

**B1.1+ Hard rule:** No English in prose, titles, callouts, or explanations.
No English in parentheses to clarify Ukrainian concepts:
- Wrong: **поки** — дія на тлі іншої дії (While she was cooking...)
- Right: **поки** — дія на тлі іншої дії, тобто одночасні процеси

## B1-Specific Writing Notes

- Content quality: equal treatment for all items in a category (same depth, same format)
- Example variety: mix standalone, table, inline, dialogue — no 5+ consecutive examples in same format
- Tables must have narrative context (2+ sentences before and after)
- Parallel sections use identical internal structure

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `B1` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Словотвір іменників** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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
- **Word count**: minimum **4000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Словотвір іменників

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
