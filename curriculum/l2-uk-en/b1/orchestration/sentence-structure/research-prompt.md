# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-004
level: B1
sequence: 4
slug: sentence-structure
version: '2.0'
title: Структура речення
subtitle: Sentence analysis terminology
focus: integration
pedagogy: PPP
phase: B1.0 Bridge
word_target: 4000
objectives:
- Learner can identify sentence parts using Ukrainian terminology
- Learner can distinguish main and subordinate clauses
- Learner can name sentence types and punctuation marks
sources:
- name: Ukrainian Syntax (Wikipedia)
  url: https://uk.wikipedia.org/wiki/Синтаксис_української_мови
  type: reference
  notes: Overview of Ukrainian sentence structure terminology
- name: Ukrainian State Standard 2024 - Syntax
  url: https://mon.gov.ua/
  type: reference
  notes: Official terminology for sentence analysis
content_outline:
- section: 'Вступ: Анатомія мови (Introduction: Anatomy of Language)'
  words: 500
  points:
  - Why sentence analysis terminology matters — introduction of the 'Anatomy of Language' concept as taught in Ukrainian schools
  - 'Metalanguage Bridge B1.0: Transitioning from English scaffolding to Ukrainian syntactic terms to prepare for State Standard
    §4.4 requirements'
  - 'The logic of ''Parsing'': Presenting syntactic analysis (синтаксичний розбір) not as a chore, but as a logical exercise
    akin to a mathematical proof'
- section: Головні та другорядні члени речення (Main and Secondary Sentence Parts)
  words: 1000
  points:
  - 'The Underlining Ritual: Introducing the universal Ukrainian visual code — Subject (підмет) as one line, Predicate (присудок)
    as two lines'
  - 'Visualizing secondary parts: Attribute (означення) with a wavy line (хвиляста лінія), Object (додаток) with dots (пунктир),
    and Adverbial (обставина) with dot-dash (штрих-пунктир)'
  - 'Identifying the Grammatical Basis: Defining ''граматична основа'' as the core of the sentence consisting of subject and
    predicate'
  - 'Focus on ''узгодження'' (agreement): How the predicate must agree with the subject in person, number, and gender'
- section: Класифікація речень за Державним стандартом (Sentence Classification per State Standard)
  words: 1000
  points:
  - Simple sentences (просте речення) vs. Complex sentences (складне речення) — establishing the B1 baseline for syntax (lines
    2367-2431)
  - 'State Standard §4.4.2: Overview of ''ускладнене речення'' (complicated simple sentences) including homogeneous parts
    and parenthetical words (вставні слова)'
  - 'State Standard §4.4.3: Structural analysis of ''складносурядне'' (coordinate) and ''складнопідрядне'' (subordinate) sentences'
  - 'Clause relationships: Distinguishing the main clause (головне речення) from the subordinate clause (підрядне речення)
    using subordinating conjunctions'
- section: Аналіз типових помилок та нюансів (Analysis of Common Errors and Nuances)
  words: 800
  points:
  - 'Error Pattern 1: Confusing ''Part of Speech'' (noun/іменник) with ''Sentence Part'' (subject/підмет) — explaining role
    vs. category'
  - 'Error Pattern 2: Pro-Drop Panic — addressing the learner''s fear of ''missing subjects'' in sentences like ''Люблю каву'',
    where the predicate implies the subject'
  - 'Error Pattern 3: Object vs. Adverbial confusion — differentiating questions ''кого? чого?'' (Object) from ''де? куди?''
    (Adverbial) in prepositional phrases'
  - 'Word order and Emphasis: Explaining the flexibility of Ukrainian syntax (SVO vs. OVS) and how inversion affects the focus
    of the ''синтаксичний центр'''
- section: 'Практика: Повний синтаксичний розбір (Practice: Full Syntactic Analysis)'
  words: 700
  points:
  - 'Step-by-step walkthrough of ''зробити розбір'': Applying the visual underlining ritual to complex authentic sentences'
  - 'Logic drill: Identifying sentence components in sequences where the subject is not the first word, using specific question-asking
    techniques'
  - 'Summary and self-assessment: Checklist for identifying all members of the grammatical basis and secondary parts in preparation
    for B1.3 complexity'
vocabulary_hints:
  required:
  - підмет (subject) — головний член речення; підкреслюємо однією рискою
  - присудок (predicate) — дієслівний присудок; узгоджується з підметом (підкреслюємо двома рисками)
  - додаток (object) — прямий додаток, непрямий додаток (підкреслюємо пунктиром)
  - означення (attribute) — узгоджене означення, поширене означення (підкреслюємо хвилястою лінією)
  - обставина (adverbial) — обставина часу, місця, способу дії (підкреслюємо штрих-пунктиром)
  - граматична основа (grammatical basis) — сукупність підмета і присудка
  - просте речення (simple sentence) — речення з однією граматичною основою (§4.4.2)
  - складне речення (complex sentence) — речення з двома або більше основами (§4.4.3)
  - підрядне речення (subordinate clause) — залежна частина складного речення
  recommended:
  - синтаксичний розбір (syntactic analysis) — зробити розбір речення; розібрати за членами речення
  - вставні слова (parenthetical words) — слова, що не є членами речення, але виражають ставлення (§4.4.2)
  - сполучник підрядності (subordinating conjunction) — з'єднує головне і підрядне речення
  - інверсія (inversion) — зміна звичного порядку слів для емоційного наголосу
  - пунктуація (punctuation) — система розділових знаків (кома, крапка, двокрапка)
  - ускладнене речення (complicated sentence) — просте речення з однорідними членами або зворотами
activity_hints:
- type: mark-the-words
  focus: Identify sentence parts in Ukrainian sentences
  items: 10+
- type: match-up
  focus: Term → example sentence part
  items: 12+
- type: quiz
  focus: Sentence type identification
  items: 10+
- type: fill-in
  focus: Label sentence components
  items: 8+
- type: true-false
  focus: Statements about sentence types and clause relationships
  items: 8+
connects_to:
- b1-05 (Metalanguage checkpoint)
- 'b1-30 (Підрядні означальні: де, куди, звідки)'
- 'b1-38 (Допустові речення: хоча, незважаючи на)'
prerequisites:
- b1-01 (Basic grammar terminology)
- b1-02 (Verb terminology)
- b1-03 (Reading grammar rules)
persona:
  voice: Senior Language & Culture Specialist
  role: Construction Architect
grammar:
- Sentence parts in Ukrainian
- Clause types
- Sentence types and punctuation
module_type: bridge
immersion: 70-85% Ukrainian
register: нейтральний

```

**Level constraints quick-ref:**

```
# B1 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Bridge modules: teach grammar metalanguage. English scaffolding for abstract concepts. Parenthetical equivalents for new terms. Sentences max 30 words.`, etc.

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

Research **Структура речення** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Структура речення

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
