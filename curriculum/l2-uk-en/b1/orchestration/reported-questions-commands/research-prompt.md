# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-043
level: B1
sequence: 43
slug: reported-questions-commands
version: '2.0'
title: Непрямі питання та накази
subtitle: Reported Questions & Commands
focus: grammar
pedagogy: TTT
phase: B1.3b [Complex Sentences]
word_target: 4000
objectives:
- Learner can report questions using indirect speech
- Learner can report commands and requests using щоб
- Learner can choose appropriate structures for different speech acts
- Learner can transform all speech types
content_outline:
- section: Діагностичний тест (Diagnostic Test)
  words: 500
  points:
  - Diagnostic quiz identifying the common 'що' vs 'чи' confusion in Yes/No indirect questions (e.g., *Він запитав, що я хочу
    кави* vs correct *чи я хочу*)
  - Check for 'ask to action' mistranslations where learners incorrectly use *питати* instead of *просити* for requests
  - 'Visual recognition task: identifying the incorrect retention of question marks in reported questions (e.g., *Вона спитала,
    де я живу?*)'
  - Self-assessment against Ukrainian State Standard §4.4.3 competencies regarding reported speech transformations
- section: Граматичне пояснення (Grammatical Explanation)
  words: 1300
  points:
  - 'State Standard §4.4.3: Syntax of complex sentences with indirect speech; mapping direct speech acts to subordinating
    conjunctions (*що*, *чи*, *щоб*)'
  - 'Indirect Yes/No Questions: Mandatory use of *чи*; explicit drill to eliminate the common learner error of using *що*
    as a universal conjunction'
  - 'Wh-Questions (що, де, коли...): Focus on the shift from rising interrogative intonation to falling narrative intonation
    and the mandatory removal of the question mark'
  - 'Reported Commands and Requests: Detailed analysis of the *щоб* + Past Tense structure (e.g., *сказав, щоб я зробив*);
    explaining why past form is used despite present/future meaning'
  - 'Lexical Register Hierarchy: Contrasting *наказати* (strong/official/military authority) vs *просити* (standard polite)
    vs *вимагати* (demanding/urgent)'
  - 'Pronoun and Person Shifts: Rules for transforming *I/Me* to *He/She/Him/Her* to maintain narrative logic and avoid subject
    confusion'
- section: Практичні вправи (Practical Exercises)
  words: 1000
  points:
  - 'Transformation drills: Converting direct imperatives into polite indirect requests using the *просити, щоб* pattern'
  - 'Mixed transformation practice: Shifting a variety of direct questions (Yes/No and Wh-types) into reportable narrative
    statements'
  - 'Error correction focus: Identifying and fixing specific learner pitfalls documented in research, such as question mark
    retention and incorrect conjunction choice'
  - 'Sentence completion: Building complex sentences from prompts focusing on the ''щоб'' + past tense morphology'
- section: Культурний контекст та діалоги (Cultural Context & Dialogues)
  words: 700
  points:
  - 'Politeness Hierarchy: Exploring why Ukrainians prefer indirect structures like *Чи не могли б ви...?* over direct commands
    in formal settings'
  - 'The ''Ty'' vs ''Vy'' dynamic: How reporting a request changes based on the social hierarchy (e.g., reporting a teacher''s
    request vs a friend''s request)'
  - 'Scenario-based dialogues: Applying reported commands in workplace (formal/demanding) vs household (casual/polite) contexts'
  - 'Intonation drill: Practice reading reported questions with narrative falling tones to distinguish them from direct queries'
- section: Підсумок та самоперевірка (Summary & Self-check)
  words: 500
  points:
  - Summary table of conjunction selection based on speech act type (Question -> чи/wh-word; Command -> щоб)
  - 'Final review of the ''Ask'' distinction: *запитати* (information) vs *просити* (action)'
  - Checklist for B1-41 Checkpoint readiness, ensuring all complex sentence structures from B1.3b are internalized
  - 'Reflective task: Describing a recent request or command using all three main conjunctions (*що, чи, щоб*)'
vocabulary_hints:
  required:
  - питання (question) — поставити питання, вирішити питання, спірне питання, риторичне питання; high frequency general use
  - наказ (command) — віддати наказ, виконати наказ, видати наказ; implies official or military register
  - прохання (request) — звернутися з проханням, ввічливе прохання, настійливе прохання; high frequency
  - чи (whether) — mandatory for Yes/No indirect questions; must be distinguished from 'що' in reporting
  - запитати (to ask) — запитати дозволу, запитати дорогу, запитати пораду; focus on information seeking
  - наказати (to order) — наказати зробити, суворо наказати; implies authority (parental, military, or state)
  - просити (to request) — просити допомоги, просити пробачення, просити слова; key for reporting actions (not questions)
  - щоб (that - subjunctive) — mandatory for reported commands/requests; used with past tense verbs (*сказав, щоб я зробив*)
  recommended:
  - поцікавитися (to wonder) — polite, higher-register alternative to 'запитати' in indirect speech
  - вимагати (to demand) — stronger than 'просити', implies urgency, authority, or strict necessity
  - умовляти (to persuade) — describing the act of trying to convince someone to comply with a request
  - заборонити (to forbid) — used for negative reported commands (e.g., *Він заборонив, щоб ми йшли*)
activity_hints:
- type: fill-in
  focus: Questions and commands to indirect
  items: 25
- type: fill-in
  focus: Complete reported questions/commands
  items: 20
- type: error-correction
  focus: Fix indirect speech errors
  items: 15
- type: fill-in
  focus: Report conversations
  items: 10
connects_to:
- b1-41 (Checkpoint Complex Sentences 2)
prerequisites:
- 'b1-42 (Непряма мова: твердження)'
persona:
  voice: Senior Language & Culture Specialist
  role: Executive Assistant
grammar:
- Reported questions with чи, що, хто, де, коли
- Reported commands with щоб + past form
- Reported requests with просити, щоб
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

Research **Непрямі питання та накази** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Непрямі питання та накази

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
