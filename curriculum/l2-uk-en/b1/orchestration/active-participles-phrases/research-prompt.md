# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-045
level: B1
sequence: 45
slug: active-participles-phrases
version: '2.0'
title: Активні дієприкметники та їхній стиль
subtitle: Active Participles & Phrases
focus: grammar
pedagogy: TTT
phase: B1.4a [Participles]
word_target: 4000
objectives:
- Learner can recognize active present participles (-учий/-ючий)
- Learner can recognize active past participles (-лий)
- Learner can explain stylistic markedness of participles
- Learner can avoid bureaucratic forms and russicisms
content_outline:
- section: 'Вступ: Природа дієприкметника (Introduction: The Nature of the Participle)'
  words: 600
  points:
  - 'Introduction to State Standard §4.2.3.1: The concept of the participle (дієприкметник) as a verbal adjective that agrees
    in gender, number, and case'
  - 'The ''Stylistic Hard Line'': Establishing the normative status of active past participles (-лий) versus the restricted/avoided
    active present participles (-учий/-ючий)'
  - 'Persona alignment: The Poet''s view on language purity — rejecting artificial bureaucratic structures in favor of natural,
    living flow'
- section: Морфологія та мовна норма (Morphology and Language Norms)
  words: 900
  points:
  - 'Active past participles with suffix -лий: normative usage for resultative states (посивілий, зів''ялий, зжовклий)'
  - 'The folklore hook: Analyzing the proverb «Не бійся гостя сидячого, а бійся стоячого» to explain lexicalized (adjectivized)
    participles'
  - 'The ''Safe List'': Identifying fully normative adjectivized forms (співучий, квітучий, родючий) that function as regular
    adjectives'
  - 'Common learner error: failing to match gender/number/case agreement with the modified noun (e.g., *палаючий очі* instead
    of *палаючі очі*)'
- section: Боротьба з канцеляритом (The Struggle Against Bureaucratese)
  words: 1100
  points:
  - 'Cultural Hook: The ''Anti-Cancelyarit'' movement as a decolonization effort to purge Soviet-era bureaucratic language
    and Russian syntax calques'
  - 'Error Correction: Replacing artificial present participles with normative Ukrainian alternatives (бажаючі → охочі, оточуюче
    середовище → довкілля)'
  - 'Professional Titles: Correcting the agent noun vs. participle confusion (Командуючий армією → Командувач армії, завідуючий
    кафедрою → завідувач кафедри)'
  - 'The case of «працюючий»: distinguishing between ''працюючий телефон'' (incorrect → справний) and ''працюючий пенсіонер''
    (better → пенсіонер, який працює)'
- section: Синтаксис та трансформації (Syntax and Transformations)
  words: 900
  points:
  - 'State Standard §4.4.2: Mastering the syntax of participial phrases (дієприкметниковий зворот) in complex simple sentences'
  - 'The ''Replacement Strategy'': Step-by-step transformation of active participles into relative clauses (відносні речення)
    using «який...» or «той, хто...»'
  - 'Correction of Russian calques: transformation drill (e.g., «Я бачу йдучого чоловіка» → «Я бачу чоловіка, який йде»)'
  - 'Stylistic nuance: when to prefer a specific noun (довкілля) over a participle construction (навколишнє середовище)'
- section: Практика та стилістичний підсумок (Practice and Stylistic Summary)
  words: 500
  points:
  - 'Contrastive analysis: identifying the difference between poetic/literary ''палаючий'' and artificial ''працюючий'''
  - 'Summary of lexicalized exceptions: a reference guide to the adjectivized forms that learners should continue to use'
  - Final review of agreement rules and stylistic markedness for the B1 level
vocabulary_hints:
  required:
  - дієприкметник (participle) — verbal adjective; requires agreement (узгодження)
  - канцелярит (bureaucratese) — meta-topic; specifically Soviet-style artificial language
  - 'працюючий (working - participle) — low frequency as participle, high as error; better: «пенсіонер, який працює»'
  - родючий (fertile) — high frequency, adjectivized; normative (e.g., «родюча земля», «родючий ґрунт»)
  - завідуючий (head of...) — deprecated/incorrect; correct form is «завідувач» (agent noun)
  - активний (active) — used to describe voice in participles
  - теперішній час (present tense) — restricted usage for active participles
  - минулий час (past tense) — normative usage for participles ending in -лий
  recommended:
  - стилістика (stylistics) — focus on naturalness (природність)
  - русизм (russicism) — specifically active present participles used as calques
  - відносне речення (relative clause) — the primary replacement for active participles
  - палаючий (burning) — medium frequency, poetic/literary; e.g., «палаючі очі»
  - охочий (willing/desirous) — the normative replacement for «бажаючий»
  - довкілля (environment) — the preferred natural alternative to «оточуюче середовище»
  - навколишнє (surrounding) — acceptable adjectival alternative to participles
activity_hints:
- type: quiz
  focus: Identify participle types
  items: 25
- type: fill-in
  focus: Participle to relative clause
  items: 20
- type: error-correction
  focus: Fix stylistic errors
  items: 15
- type: fill-in
  focus: Choose participle or clause
  items: 10
connects_to:
- b1-46 (Past Passive Participles 1)
prerequisites:
- b1-51 (Дієприслівники доконаного виду)
persona:
  voice: Senior Language & Culture Specialist
  role: Poet
grammar:
- Активні дієприкметники теперішнього часу (-учий/-ючий)
- Активні дієприкметники минулого часу (-лий)
- Стилістична маркованість та канцелярит
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

Research **Активні дієприкметники та їхній стиль** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Активні дієприкметники та їхній стиль

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
