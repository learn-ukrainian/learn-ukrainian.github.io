# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-042
level: B1
sequence: 42
slug: reported-statements
version: '2.0'
title: 'Непряма мова: твердження'
subtitle: Reported Statements
focus: grammar
pedagogy: TTT
phase: B1.3b [Complex Sentences]
word_target: 4000
objectives:
- Learner can report what someone said using indirect speech
- Learner can apply tense backshift in reported statements
- Learner can use appropriate reporting verbs
- Learner can transform direct speech to indirect
content_outline:
- section: Вступ (Introduction)
  words: 400
  points:
  - Introduction to reporting speech in Ukrainian, aligning with State Standard §4.4.3 for complex sentences with declarative
    indirect speech.
  - 'Cultural hook: The concept of Oral History (Усна історія) and how «Люди кажуть...» (People say) served as a trusted unofficial
    truth in Ukrainian culture.'
- section: Діагностика (Diagnostic Test)
  words: 600
  points:
  - Diagnostic quiz identifying direct vs. indirect speech structures in simple narratives to establish baseline competency.
  - 'Identification task: Spotting the mandatory conjunction «що» in reported statements vs. English optional ''that'' patterns.'
  - Self-assessment exercises on basic pronoun shifts (e.g., changing speaker 'I' to reported 'he/she').
- section: Граматичне пояснення (Grammar Explanation)
  words: 1300
  points:
  - 'The ''Time Travel'' metaphor: Explaining why Ukrainian retains the original tense of the direct speech (frozen moment)
    while English requires a tense backshift.'
  - 'Mandatory Conjunction «що»: Contrastive analysis showing that unlike the English ''that'', «що» can never be omitted
    in reported statements.'
  - 'Pronoun and perspective shifts: Rule-based breakdown of moving from 1st person to 3rd person perspective in reporting.'
  - 'Reporting Verbs and Register: Distinguishing between neutral verbs (сказати, розповісти) and formal/assertive media-style
    verbs (стверджувати, заявити, повідомити).'
- section: Практика трансформації (Transformation Practice)
  words: 1000
  points:
  - 'Controlled transformation drill: Converting direct speech to reported statements with strict focus on avoiding the ''English
    Trap'' of tense backshifting.'
  - 'Error correction activity: Identifying and fixing sentences where the conjunction «що» is missing or pronouns haven''t
    been shifted.'
  - 'Vocabulary variety drill: Replacing repetitive uses of «сказати» with register-appropriate verbs like «відповісти», «пояснити»,
    or «зауважити».'
- section: Комунікація та культура (Communication and Culture)
  words: 700
  points:
  - 'Citation Culture: Practicing reporting structures used in daily life to reference folk wisdom or literature (e.g., «Як
    казав Шевченко...», «Як кажуть у народі...»).'
  - 'Storytelling scenario: Reporting a sequence of events from an interview or social interaction, emphasizing the nuance
    of the reporter''s perspective.'
  - 'Final production task: Summarizing a news report or official statement using a mix of neutral and formal reporting verbs
    to convey different levels of certainty.'
vocabulary_hints:
  required:
  - 'сказати (to say) — High frequency (Core A1); collocations: сказати правду, сказати «так», як то кажуть'
  - 'говорити (to speak/talk) — High frequency (Core A1); collocations: говорити про, говорити, що...'
  - 'розповісти (to tell) — High frequency (Core A2); collocations: розповісти історію, розповісти про себе'
  - 'стверджувати (to claim/assert) — Medium frequency (B1/Media); usage: стверджувати, що; вчені стверджують'
  - 'повідомити (to report/inform) — Medium frequency (B1/Official); collocations: повідомити новину, повідомити про зміни'
  - що (that) — MANDATORY conjunction in Ukrainian reported statements (unlike English 'that')
  - непряма мова (indirect speech) — technical term for reported speech
  - пряма мова (direct speech) — original speech being reported
  - твердження (statement) — the specific type of reported speech (declarative)
  recommended:
  - 'заявити (to declare) — Medium frequency (B1/Media); collocations: офіційно заявити, заявити про наміри'
  - 'додати (to add) — High frequency in dialogues; collocations: додати, що...'
  - пояснити (to explain) — reporting verb used for clarifying information
  - відповісти (to answer/reply) — essential for reporting dialogues
  - зазначити (to note/state) — formal reporting verb for specific details
  - підтвердити (to confirm) — used in formal reporting to verify information
activity_hints:
- type: fill-in
  focus: Direct to indirect conversion
  items: 25
- type: fill-in
  focus: Complete reported statements
  items: 20
- type: error-correction
  focus: Fix reported speech errors
  items: 15
- type: fill-in
  focus: Write reported paragraphs
  items: 10
connects_to:
- b1-43 (Непрямі питання та накази)
prerequisites:
- b1-41 (Інтеграція складних речень)
persona:
  voice: Senior Language & Culture Specialist
  role: Court Reporter
grammar:
- Converting direct speech to indirect speech
- Він сказав, що... constructions
- Tense and pronoun changes
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

Research **Непряма мова: твердження** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Непряма мова: твердження

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
