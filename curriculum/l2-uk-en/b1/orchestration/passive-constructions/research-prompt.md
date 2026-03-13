# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-048
level: B1
sequence: 48
slug: passive-constructions
version: '2.0'
title: 'Пасивні конструкції: повна система'
subtitle: Passive Constructions - Complete System
focus: grammar
pedagogy: TTT
phase: B1.4a [Participles]
word_target: 4000
objectives:
- Learner can distinguish three types of passive constructions
- Learner can transform active sentences to passive
- Learner can explain stylistic nuances of each passive type
- Learner can choose appropriate passive for context
content_outline:
- section: Вступ та діагностичний тест (Introduction and Diagnostic Test)
  words: 600
  points:
  - 'Overview of the three passive types as defined by State Standard §4.2.3.1 and §4.4.2: Adjectival (participle), Impersonal
    (fact/result), and Reflexive (process/habitual action).'
  - Diagnostic exercise to identify existing learner patterns, specifically targeting the common error of adding an agent
    in the instrumental case to impersonal -но/-то constructions (e.g., diagnosing if learners say 'Мною було зроблено').
- section: 'Граматична система: три типи пасиву (Grammar System: Three Passive Types)'
  words: 1000
  points:
  - 'The Adjectival Passive: Using passive participles to describe states or features (e.g., ''зачинений магазин''); practical
    exercises based on Standard §4.4.2 regarding participle clauses.'
  - 'The Impersonal Passive (-но/-то): Deep dive into this unique Ukrainian feature used for констатація факту (stating fact/result);
    explanation of its fatalistic or official tone (e.g., ''Вхід заборонено'').'
  - 'The Reflexive Passive (-ся): Defining process or regular actions (e.g., ''магазин зачиняється о 18:00''); contrastive
    analysis to prevent confusion between process and result (''відчиняється'' vs ''відчинено'').'
- section: 'Культурний контекст: боротьба з «канцеляритом» (Cultural Context: Fighting ''Bureaucratese'')'
  words: 800
  points:
  - Defining 'Kanceliaryt' (bureaucratese) as a remnant of Soviet/Russian-style passive overuse; highlighting the linguistic
    preference for active voice ('Ми вирішили' vs 'Нами було вирішено').
  - 'Analyzing the ''Agent Error'': Explicitly teaching that forms on -но/-то must NOT have an agent in the instrumental case
    (''Мною зроблено'' - WRONG vs ''Я зробив'' or ''Зроблено'' - RIGHT).'
- section: Практика та корекція помилок (Practice and Error Correction)
  words: 900
  points:
  - 'Transformation triad: Converting active sentences into all three passive types while maintaining natural Ukrainian style;
    fixing English calques like ''It was decided by him'' -> ''Він вирішив''.'
  - 'Minimal pairs drill: Distinguishing between state (''Двері зачинені''), process (''Двері зачиняються''), and the result
    of a completed action (''Двері зачинено'').'
- section: Діалоги та застосування в мовленні (Dialogues and Speech Application)
  words: 700
  points:
  - 'Situational dialogues: Contrasting official announcements (high passive usage) with everyday conversation (high active
    usage) to demonstrate register shifts.'
  - 'Final summary: Decision-making matrix for choosing the correct passive vs. active voice based on emphasis (result vs.
    actor) and situational context (Standard §4.4.2 syntax integration).'
vocabulary_hints:
  required:
  - пасивний стан (passive voice) — вживати пасивний стан, речення в пасивному стані; High frequency in grammar context
  - активний стан (active voice) — перетворити на активний стан, перевага активного стану; High frequency, stylistic priority
  - дієприкметник (participle) — пасивний дієприкметник, дієприкметниковий зворот; High frequency (Education/Standard)
  - -но/-то (impersonal ending) — зроблено, написано, відкрито, заборонено; High frequency (Official/Announcements)
  - зворотний (reflexive) — зворотне дієслово, пасив на -ся
  - трансформація (transformation) — трансформація активу в пасив
  - конструкція (construction) — граматична конструкція, пасивна конструкція
  - стиль (style) — офіційно-діловий стиль, розмовний стиль
  - бути (to be) — допоміжне дієслово в пасиві
  - -ся (reflexive suffix) — додавання -ся до дієслова
  recommended:
  - наголос (emphasis) — робити наголос на результаті
  - агент дії (agent of action) — виконавець дії, уникати агента в орудному відмінку
  - регістр (register) — офіційний регістр, зміна регістру
  - уникати (to avoid) — уникати канцеляриту, уникати пасивних конструкцій
  - будуватися (to be built) — будинок будується, плани будуються; Medium frequency, common process example
  - канцелярит (bureaucratese) — ознака канцеляриту, вплив російської мови
  - констатація (statement) — констатація факту, констатація результату
activity_hints:
- type: fill-in
  focus: Active to three passive types
  items: 25
- type: quiz
  focus: Choose best passive type
  items: 20
- type: fill-in
  focus: Complete passive sentences
  items: 15
- type: fill-in
  focus: Write using varied passives
  items: 10
connects_to:
- 'b1-52 (Демінутиви: майстер-клас)'
prerequisites:
- b1-46 (Past Passive Participles 2)
persona:
  voice: Senior Language & Culture Specialist
  role: Government Spokesperson
grammar:
- Три типи пасивних конструкцій
- Пасив з дієприкметником (participle passive)
- Пасив з короткою формою (short form passive)
- Зворотний пасив (-ся reflexive passive)
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

Research **Пасивні конструкції: повна система** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Пасивні конструкції: повна система

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
