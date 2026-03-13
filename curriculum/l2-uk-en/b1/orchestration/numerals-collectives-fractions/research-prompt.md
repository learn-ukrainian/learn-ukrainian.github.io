# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-053
level: B1
sequence: 53
slug: numerals-collectives-fractions
version: '2.0'
title: 'Числівники: збірні та дроби'
subtitle: Numerals - Collectives and Fractions
focus: grammar
pedagogy: TTT
phase: B1.4b [Word Formation]
word_target: 4000
objectives:
- Learner can use collective numerals correctly
- Learner can explain when to use collectives vs cardinals
- Learner can express fractions and percentages
- Learner can combine numerals with various noun types
content_outline:
- section: Вступ та діагностика (Introduction and Diagnostics)
  words: 600
  points:
  - Diagnostic analysis of cardinal vs collective numeral usage — testing the distinction between 'два студенти' and 'нас
    двоє' in conversational contexts.
  - Alignment with State Standard §4.2.1.3 — bridging the gap between basic cardinal list and the functional necessity of
    collectives for natural Ukrainian speech.
- section: Збірні числівники та 'Пастки' (Collective Numerals and 'Traps')
  words: 1200
  points:
  - 'The ''Who/What counts?'' logic flowchart — defining triggers for collectives: living males (двоє хлопців), baby animals
    (четверо цуценят), and plurale tantum nouns (двоє саней, троє дверей).'
  - Deep dive into the 'Grandmother Trap' and 'Phone Trap' — explicit rules forbidding collectives with feminine nouns (use
    'три бабусі') and inanimate masculine nouns (use 'два телефони').
  - Addressing the Case Mismatch — enforcing the mandatory Genitive Plural case after collective numerals (двоє студентів,
    четверо коней) to ensure grammatical elegance.
- section: Дроби, відсотки та особливі форми (Fractions, Percentages, and Special Forms)
  words: 800
  points:
  - 'Fractional numerals in daily life — common forms: половина, третина, чверть; integration into time-telling expressions
    (чверть на третю, о пів на другу).'
  - Mastering 'півтора' (one and a half) — highlighting high-frequency usage and the unique requirement for the following
    noun to be in Genitive Singular (півтора місяця, півтора року).
  - Percentages and decimals — basic formation rules and agreement with the Genitive case (п'ять відсотків, нуль цілих п'ять
    десятих).
- section: 'Культурний контекст: Магія чисел (Cultural Context: Magic of Numbers)'
  words: 800
  points:
  - The Magical Number 3 in Ukrainian Folklore — exploration of the proverb 'Бог трійцю любить' and the recurrence of 'three
    brothers/tasks' in traditional folktales.
  - The Holy Number 12 and the '12 Dishes' — cultural anchoring of Christmas Eve (Sviat Vecher) traditions representing the
    apostles and the months of the year.
- section: Мовленнєва практика та підсумок (Speech Practice and Summary)
  words: 600
  points:
  - Real-world social scenarios — counting people at a table ('нас п'ятеро'), ordering portions in a restaurant, and discussing
    statistics using fractions.
  - Mathematical contexts and recipes — applying fractional numerals to measurements and simple arithmetic with a focus on
    conversational fluidity.
vocabulary_hints:
  required:
  - двоє (two - collective) — high frequency; used for male groups, mixed groups, or children (двоє друзів, двоє дітей, нас
    двоє)
  - 'троє (three - collective) — high frequency; used with babies and pluralia tantum (троє дверей, троє саней); cultural
    hook: ''Бог трійцю любить'''
  - четверо (four - collective) — medium frequency; used for groups of young animals (четверо цуценят, четверо кошенят)
  - півтора (one and a half) — high frequency; mandatory agreement with Genitive Singular nouns (півтора місяця, півтора року,
    півтора літра)
  - 'половина (half) — very high frequency; collocations: половина часу, о пів на другу (time)'
  - 'третина (third) — medium frequency; population/statistics: третина населення, одна третя'
  - 'чверть (quarter) — high frequency; time: чверть на третю; historical: чверть століття'
  - відсоток (percent) — formal/practical register; requires Genitive case agreement (п'ять відсотків)
  recommended:
  - утрьох (the three of us/them) — high frequency conversational adverbial form derived from collective root
  - 'ножиці (scissors) — plurale tantum noun requiring collective numeral: двоє ножиць'
  - 'окуляри (glasses) — plurale tantum noun requiring collective numeral: троє окулярів'
  - 'кількісний числівник (cardinal numeral) — grammar term: один, два, три'
  - 'дробовий числівник (fractional numeral) — grammar term: одна друга, півтора'
  - множина (plural) — required for collective numerals (specifically Genitive Plural)
activity_hints:
- type: fill-in
  focus: Choose cardinal or collective
  items: 25
- type: fill-in
  focus: Express as fractions
  items: 20
- type: quiz
  focus: Select correct numeral form
  items: 15
- type: fill-in
  focus: Express math in Ukrainian
  items: 10
connects_to:
- b1-50 (Checkpoint Participles Numerals)
prerequisites:
- 'b1-52 (Демінутиви: майстер-клас)'
persona:
  voice: Senior Language & Culture Specialist
  role: Accountant
grammar:
- Збірні числівники (двоє, троє, четверо)
- Дробові числівники (половина, третина, чверть)
- Вживання збірних з різними типами іменників
register: розмовний

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

Research **Числівники: збірні та дроби** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Числівники: збірні та дроби

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
