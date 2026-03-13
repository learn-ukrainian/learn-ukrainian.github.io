# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-071
level: B1
sequence: 71
slug: society-politics
version: '2.0'
title: Суспільство та політика
subtitle: Society & Politics
focus: vocabulary
pedagogy: PPP
phase: B1.5 [Vocabulary Expansion I]
word_target: 4000
objectives:
- Learner can use 30 civic and political vocabulary words in context
- Learner can discuss democratic processes and institutions
- Learner can form natural collocations with political vocabulary
- Learner can understand Ukrainian political discourse
content_outline:
- section: Вступ (Introduction)
  words: 500
  points:
  - 'Thematic alignment with State Standard §3.6 (Social Relations & State Structure): Why civic literacy and state structure
    vocabulary are essential for B1 learners.'
  - 'Historical Hook: Constitution of Pylyp Orlyk (1710) as one of the world''s first democratic documents, establishing the
    separation of powers before Montesquieu as evidence of early Ukrainian democratic traditions.'
  - 'Overview of the three branches of power in modern Ukraine: legislative, executive, and judicial.'
- section: Політичні інституції та влада (Political Institutions & Power)
  words: 800
  points:
  - 'Official register focus: Analyzing news headlines using passive constructions and verbal nouns (e.g., ''формування уряду'',
    ''прийняття закону'').'
  - 'Learner error: Confusing ''Політика'' (the sphere/policy) with ''Політик'' (the person/politician) – drill stress patterns
    and usage context.'
  - 'High-frequency collocations for power dynamics: ''прийти до влади'', ''органи державної влади'', ''поділ влади'', and
    ''голова уряду''.'
- section: Громадянське суспільство та історія (Civil Society & History)
  words: 900
  points:
  - 'Engagement Hook: The Human Chain (1990) ''Українська хвиля'' – a narrative of civic unity and ''соборність'' involving
    millions of citizens from Kyiv to Lviv.'
  - 'Learner error: Distinguishing between ''Громадський'' (public transport/space) and ''Громадянський'' (civil society/rights)
    to avoid root-similarity confusion (Громадський транспорт vs Громадянське суспільство).'
  - 'Vocabulary expansion: ''Громадянин'' (citizen), their rights (''права''), and duties (''обов''язки'') in a democratic
    state.'
- section: Демократичний процес та дискурс (Democratic Process & Discourse)
  words: 900
  points:
  - 'The vocabulary of elections: ''брати участь у виборах'', ''виборча дільниця'', ''день голосування'', and ''право голосу''.'
  - 'Syntactic focus: Constructing complex causal sentences using ''тому що'' and ''через те що'' for political argumentation
    and justification of views.'
  - 'Register contrast: Distinguishing between the formal language of news broadcasts and ''kitchen table'' political discussions
    among citizens.'
- section: Право, закон та громадянські права (Law, Legislation & Civil Rights)
  words: 700
  points:
  - 'Legal terminology in context: ''ухвалити закон'', ''порушувати закон'', ''згідно із законом'', and ''гарант конституції''.'
  - 'Learner error: Correcting the calque ''громадянський шлюб'' to the proper ''цивільний шлюб/кодекс'' (distinguishing civil
    law from civic/social status).'
  - 'Discussion of fundamental freedoms: ''свобода слова'', ''захищати права'', and ''принципи демократії''.'
- section: Підсумок (Summary)
  words: 200
  points:
  - Synthesis of high-frequency civic collocations and summary of register distinctions (formal vs. informal political talk).
  - 'Practice recommendations: Encouraging learners to follow Ukrainian news to observe institutional vocabulary in real-time.'
vocabulary_hints:
  required:
  - уряд (government) — формування уряду, відставка уряду, голова уряду; medium frequency political term
  - держава (state) — державна влада, органи державної влади, громадянин України; high frequency
  - влада (power/authority) — виконавча влада, прийти до влади, поділ влади, органи влади; high frequency
  - вибори (elections) — брати участь у виборах, йти на вибори, виборча дільниця, право голосу; medium frequency
  - голосування (voting) — право голосу, день голосування; essential for democratic process
  - закон (law) — ухвалити закон, порушувати закон, згідно із законом, поза законом; high frequency
  - громадянин (citizen) — права громадянина, обов'язок громадянина, громадянин України; high frequency social term
  - права (rights) — захищати права, порушення прав, права людини; high frequency
  recommended:
  - парламент (parliament) — розпуск парламенту, сесія парламенту; institutional vocabulary
  - конституція (constitution) — згідно з конституцією, гарант конституції, Конституція Пилипа Орлика
  - демократія (democracy) — розвиток демократії, принципи демократії; core concept
  - свобода (freedom) — свобода слова, боротьба за свободу; essential value
  - громадянський (civic/civil) — громадянське суспільство, громадянські права; distinguish from громадський
  - громадський (public) — громадський транспорт, громадське місце; distinguish from громадянський
  - цивільний (civil) — цивільний шлюб, цивільний кодекс; distinguish from громадянський
  - політик (politician) — відомий політик; distinguish from політика (sphere)
activity_hints:
- type: match-up
  focus: Political noun phrases
  items: 25
- type: fill-in
  focus: Complete civic sentences
  items: 20
- type: match-up
  focus: Match institutions and functions
  items: 15
- type: quiz
  focus: Discuss civic topics
  items: 10
connects_to:
- b1-72 (Професійна комунікація)
prerequisites:
- b1-70 (Медіа та новини)
persona:
  voice: Senior Language & Culture Specialist
  role: Political Analyst
grammar:
- Noun collocations with civic vocabulary
- Political discourse patterns
- Formal register expressions
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

Research **Суспільство та політика** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Суспільство та політика

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
