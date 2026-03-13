# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-040
level: B1
sequence: 40
slug: temporal-clauses
version: '2.0'
title: Часові підрядні речення
subtitle: Temporal Clauses Deep Dive
focus: grammar
pedagogy: TTT
phase: B1.3b [Complex Sentences]
word_target: 4000
objectives:
- Learner can express часові відношення using various temporal connectors
- Learner can sequence events using appropriate temporal markers
- Learner can distinguish simultaneous vs sequential actions
- Learner can build complex temporal narratives
content_outline:
- section: Вступ та Діагностика (Introduction & Diagnostics)
  words: 600
  points:
  - 'Diagnostic quiz on temporal clauses per State Standard §4.4.3 — focus on the critical learner error: confusing ''коли''
    (point in time) vs ''поки'' (duration/simultaneity).'
  - 'Self-assessment on the ''Until'' negation trap: test the counter-intuitive use of ''поки не'' + perfective verb versus
    English positive logic.'
  - Orientation to simultaneous (одночасність) vs sequential (різночасовість) actions, identifying high-frequency connectors
    found in research.
- section: 'Пояснення: Одночасність та Тривалість (Explanation: Simultaneity & Duration)'
  words: 1000
  points:
  - 'Deep dive into ''коли'' (high frequency) vs ''поки/доки'' (duration) — corrective drill: ''Я читав, поки вона спала''
    (Correct) vs ''Я читав, коли вона спала'' (Incorrect nuance).'
  - 'Grammar of Simultaneous Actions: The requirement for Imperfective aspect (Impf + Impf) to show background continuity
    and parallel events.'
  - Usage of 'тим часом як' and 'під час того як' for complex narrative layers, expanding beyond basic A2 'коли' constructions.
- section: 'Пояснення: Послідовність та пастка «поки не» (Explanation: Sequence & the «Until» Trap)'
  words: 1000
  points:
  - 'Sequence Connectors: ''перш ніж'', ''після того як'', ''як тільки'' — visualize with a timeline to clarify event order
    (Action A finishes before Action B starts).'
  - 'Aspectual logic for sequencing: Emphasize the necessity of Perfective aspect (Perf + Perf) to signal completed sequence
    (e.g., ''Після того як я прочитав...'').'
  - 'The ''Until'' Negation Trap: Detailed explanation of ''поки не'' + negative perfective verb (e.g., ''Я буду чекати, поки
    ти не прийдеш'') to correct the most common B1 transfer error from English.'
- section: 'Культурна перспектива: Час і Доля (Cultural Perspective: Time & Destiny)'
  words: 700
  points:
  - 'Cultural Hook 1: ''Усьому свій час'' (Everything has its time) — Philosophical reading on patience and destiny in Ukrainian
    culture using general truth temporal clauses.'
  - 'Cultural Hook 2: ''Чекати з моря погоди'' — Idiom analysis focusing on passive vs active time management, contrasting
    ''поки'' (while waiting) with ''як тільки'' (actionable change).'
  - 'Linguistic elegance: How Ukrainian uses temporal markers to create ''narrative depth'' in storytelling, moving from simple
    lists to layered experiences.'
- section: Практика та Синтез (Practice & Synthesis)
  words: 700
  points:
  - 'Sentence building: Ordering historical or daily events using ''перш ніж'' vs ''після того як'' with strict aspectual
    checks.'
  - 'Error correction marathon: Fixing aspectual mismatches and the ''Until'' negation trap in 15+ student-simulated sentences.'
  - 'Narrative Production: Learners write a short story about a journey or event, incorporating at least 5 different temporal
    connectors and the idiom ''Чекати з моря погоди''.'
vocabulary_hints:
  required:
  - 'коли (when) — High frequency; collocations: ''коли я був...'', ''коли ми прийшли...''; used for specific points in time.'
  - 'поки (while/until) — High frequency; collocations: ''поки не'' (until + negative verb), ''поки я чекав...''; signals
    duration.'
  - 'перш ніж (before) — Medium frequency (literary/formal); collocations: ''перш ніж почати'', ''перш ніж сказати''; requires
    Perfective.'
  - 'після того як (after) — Medium frequency; collocations: ''після того як ми зробили...'', ''одразу після того як''.'
  - 'як тільки (as soon as) — Medium frequency; collocations: ''як тільки зможу'', ''як тільки прийдеш''; emphasis on immediacy.'
  - доки (while/as long as) — Synonym for 'поки'; focus on duration of a state.
  - під час (during) — Used with nouns to focus on simultaneous action phrases.
  - одночасно (simultaneously) — Crucial adverb for clarifying parallel sequences.
  recommended:
  - 'щойно (just as) — Emphasis on immediacy; collocation: ''щойно я побачив''.'
  - відтоді як (since) — Temporal starting point for a continuous duration.
  - до того як (before) — Common alternative to 'перш ніж' for sequential events.
  - 'тим часом (meanwhile) — Collocations: ''тим часом як'', ''а тим часом''; used for parallel plot lines.'
activity_hints:
- type: fill-in
  focus: Complete temporal sentences
  items: 25
- type: error-correction
  focus: Sequence events
  items: 20
- type: error-correction
  focus: Fix temporal clause errors
  items: 15
- type: fill-in
  focus: Write temporal narratives
  items: 10
connects_to:
- b1-41 (Інтеграція складних речень)
prerequisites:
- b1-39 (Причинові та наслідкові речення)
persona:
  voice: Senior Language & Culture Specialist
  role: Biographer
grammar:
- Temporal clauses with коли, після того як, поки
- 'Sequence markers: перш ніж, як тільки'
- Simultaneous vs sequential action
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

Research **Часові підрядні речення** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Часові підрядні речення

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
