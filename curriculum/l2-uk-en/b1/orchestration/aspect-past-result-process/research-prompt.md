# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-010
level: B1
sequence: 10
slug: aspect-past-result-process
version: '2.0'
title: 'Вид у минулому: результат і процес'
subtitle: 'Aspect in Past: Result vs Process'
focus: grammar
pedagogy: TTT
phase: B1.1 Aspect
word_target: 4000
objectives:
- Learner can distinguish result from process in past tense
- Learner can explain duration markers with imperfective
- Learner can select aspect based on speaker's focus (result vs activity)
- Learner recognizes completion markers with perfective
sources:
- name: Ukrainian State Standard 2024 - Aspect and Result
  url: https://mon.gov.ua/
  type: reference
  notes: Official guidance on result-oriented aspect usage
- name: Ukrainian Grammar - Aspect
  url: https://uk.wikipedia.org/wiki/Вид_дієслова
  type: reference
  notes: Process vs result distinction in Ukrainian
content_outline:
- section: Діагностичний тест (Diagnostic Test)
  words: 600
  points:
  - 'Diagnostic narrative: Distinguishing between ''Ми будували хату'' (process) and ''Ми збудували хату'' (result) within
    the context of the Ukrainian Toloka tradition.'
  - 'Visual metaphor introduction: Representing the Imperfective (Process) as a wavy line with no visible end and the Perfective
    (Result) as a checkmark or point on a timeline.'
  - 'Baseline check for common learner error: Identifying if students use Imperfective (''Я писав тест'') instead of Perfective
    achievement markers when reporting outcomes.'
- section: Презентація та теорія (Presentation and Theory)
  words: 1000
  points:
  - 'Perfective Aspect (Result): Introducing the cultural hook ''Зробив діло — гуляй сміло'' to explain that leisure is culturally
    justified only after the completion of an action.'
  - 'Imperfective Aspect (Process): Introducing the cultural hook ''Тихіше їдеш — далі будеш'' to highlight the emphasis on
    the manner, duration, and ongoing nature of an action.'
  - 'State Standard §4.2.3.1 implementation: Detailed formation of past tense verbs (хотів/хотіла/хотіли vs побачив/побачила/побачили)
    with strict focus on gender and number agreement.'
  - 'Linguistic Markers contrast: Categorizing duration markers (''весь день'', ''тривалий час'', ''довго'') vs result markers
    (''вже'', ''нарешті'', ''успішно'').'
- section: Порівняльний аналіз (Comparative Analysis)
  words: 800
  points:
  - 'The Toloka Paradigm: Analyzing how the same historical event shifts meaning — focusing on the social shared process (''будували
    весь день'') vs the physical result (''збудували до заходу сонця'').'
  - 'Communication Intent in context: Professional reporting (Boss asking for Perfective accomplishments) vs Social sharing
    (Friend asking for Imperfective descriptions of activities).'
  - 'Identifying subtle shifts: How adding markers like ''нарешті'' or ''до кінця'' necessitates a change from process to
    result focus in a sentence.'
- section: Практика та виправлення помилок (Practice and Error Correction)
  words: 900
  points:
  - 'Correction drill: ''Process for Result'' — fixing the transfer error where learners use Imperfective for completed achievements
    (e.g., replacing ''Я писав статтю'' with ''Я написав статтю'').'
  - 'Eliminating auxiliary ''був'': Direct correction of the error ''Я був ходив'' to reinforce the synthetic Ukrainian past
    tense structure without English-style auxiliaries.'
  - 'Gender Mismatch Clinic: Exercises specifically targeting the phonetic and grammatical oversight where students use the
    wrong gender form (e.g., ''Я зробив'' used by female speakers).'
  - 'Daily life simulation: Choosing the correct aspect for scenarios involving moving houses, completing studies, and reporting
    work tasks.'
- section: Діалоги та підсумок (Dialogues and Summary)
  words: 700
  points:
  - 'Work Report Dialogue: Roleplay between a result-oriented supervisor and an employee, emphasizing achievement-based questions
    and answers.'
  - 'Narrative Construction: Describing a ''Study Experience'' where the learner must describe the long process of learning
    leading to the successful result of passing an exam.'
  - 'Final Self-Check: Review of indicative mood past tense rules and alignment with the competencies defined in the State
    Standard.'
vocabulary_hints:
  required:
  - результат (result) — досягти результату, головний результат, результат роботи, чекати на результат; High frequency/General
    Corpus.
  - процес (process) — у процесі, навчальний процес, тривалий процес, контролювати процес; High frequency.
  - завершення (completion) — успішне завершення, після завершення, етап завершення; Medium frequency/Academic & Formal.
  - тривалість (duration) — середня тривалість, тривалість життя, тривалість дії; Medium frequency/Formal.
  - вже (already) — вже зробив, вже готово, я вже знаю; Very high frequency/Spoken & Written.
  - нарешті (finally) — нарешті прийшов, нарешті зробив, ну нарешті; High frequency/Spoken.
  - весь день (all day) — primary marker for Imperfective duration.
  - годину (for an hour) — marker used to emphasize the length of a process.
  - до кінця (to the end) — marker indicating the boundary of a completed action.
  - довго (for a long time) — common marker for ongoing imperfective states.
  recommended:
  - ще (still/yet) — used to indicate ongoing process or lack of result.
  - зараз (now) — to contrast past process with current state.
  - поступово (gradually) — indicates the manner of a process over time.
  - раптом (suddenly) — often signals the interruption of a process by a result/event.
  - миттєво (instantly) — emphasizes the speed of a result.
activity_hints:
- type: quiz
  focus: Result or process aspect?
  items: 15+
- type: fill-in
  focus: Duration markers with imperfective
  items: 12+
- type: fill-in
  focus: Add result marker → change to perfective
  items: 10+
- type: fill-in
  focus: Narrative with result/process focus
  items: 10+
connects_to:
- b1-09 (Aspect in future)
- b1-14 (Aspect integration practice)
prerequisites:
- 'b1-08 (Вид дієслова: повна система)'
- 'b1-09 (Вид у минулому: одного разу vs щодня)'
persona:
  voice: Senior Language & Culture Specialist
  role: Crime Scene Investigator
grammar:
- Result-oriented vs process-oriented aspect
- Duration markers and aspect
- Completed actions vs ongoing processes
module_type: grammar
immersion: 100% Ukrainian
register: нейтральний

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

Research **Вид у минулому: результат і процес** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Вид у минулому: результат і процес

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
