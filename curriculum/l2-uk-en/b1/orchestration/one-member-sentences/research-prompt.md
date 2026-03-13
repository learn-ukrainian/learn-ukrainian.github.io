# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-049
level: B1
sequence: 49
slug: one-member-sentences
version: '2.0'
title: Односкладні речення
subtitle: One-Member Sentences in Ukrainian
focus: grammar
pedagogy: TTT
phase: B1.6 [Participles and Advanced Grammar]
word_target: 4000
objectives:
- Learner can identify all 4 types of one-member sentences
- Learner can construct означено-особові and неозначено-особові sentences
- Learner can use безособові constructions for states, weather, and modals
- Learner can recognize називні речення in headlines and literature
content_outline:
- section: 'Вступ: Навіщо речення без підмета? (Introduction: Why Sentences Without a Subject?)'
  words: 500
  points:
  - 'State Standard §4.3.2: односкладні речення as required B1 grammar'
  - 'Cultural hook: Ukrainian preference for impersonal expression vs English "I" centering'
  - 'Overview: 4 types — означено-особові, неозначено-особові, безособові, називні'
- section: Означено-особові речення (Definite-Personal Sentences)
  words: 700
  points:
  - 'Definition: subject omitted but recoverable from verb ending (1st/2nd person)'
  - 'Examples: "Іду додому" (= я іду), "Знаєш цю пісню?" (= ти знаєш)'
  - 'Common in informal speech, imperatives: "Читай!", "Ходімо!"'
  - 'Drill: convert two-member → one-member by dropping pronoun'
- section: Неозначено-особові речення (Indefinite-Personal Sentences)
  words: 700
  points:
  - 'Definition: 3rd person plural verb, agent unknown or irrelevant'
  - 'Examples: "Кажуть, що..." (they say), "Тут не палять" (one doesn''t smoke here)'
  - 'Usage: news style, general truths, avoiding naming the agent'
  - 'Contrast with English passive: "It is said..." = "Кажуть..."'
- section: Безособові речення (Impersonal Sentences)
  words: 800
  points:
  - Most productive type in Ukrainian
  - 'State/weather: "Холодно", "Темніє", "Мені сумно"'
  - 'Modals: "Треба працювати", "Можна увійти?"'
  - 'Predicate forms: -но/-то ("Написано"), infinitive ("Не курити!")'
  - 'Learner error: adding "воно" (it is cold → *Воно холодно → Холодно)'
- section: Називні речення (Nominal Sentences)
  words: 600
  points:
  - 'Definition: noun/noun phrase in nominative, no verb'
  - 'Usage: headlines ("Перемога!"), scene setting ("Ніч. Тиша. Місяць.")'
  - Stage directions, poetry, emotional expression
  - 'News headlines: "Нові санкції проти Росії", "Рекордний урожай"'
- section: 'Практика: Від двоскладних до односкладних (Practice: From Two-Member to One-Member)'
  words: 700
  points:
  - 'Transformation exercises: identify type, convert between formats'
  - 'Reading comprehension: identify one-member sentences in authentic text'
  - 'Register awareness: which types dominate in which registers'
  - 'Writing: compose a weather report, news bulletin, informal message using one-member sentences'
vocabulary_hints:
  required:
  - односкладний (one-member) — односкладне речення; grammatical term
  - двоскладний (two-member) — двоскладне речення; contrast term
  - підмет (subject) — немає підмета, підмет опущений
  - присудок (predicate) — головний член речення
  - безособовий (impersonal) — безособове речення, безособовий зворот
  - називний (nominal/nominative) — називне речення, називний відмінок
  recommended:
  - означено-особовий (definite-personal) — grammatical classification
  - неозначено-особовий (indefinite-personal) — grammatical classification
  - заголовок (headline) — газетний заголовок; context for називні речення
  - модальність (modality) — модальні слова; connection to безособові
activity_hints:
- type: quiz
  focus: Identify one-member sentence type
  items: 15
- type: fill-in
  focus: Transform two-member to one-member sentences
  items: 15
- type: error-correction
  focus: Fix unnecessary subject insertion
  items: 10
- type: match-up
  focus: Match sentence to its type classification
  items: 12
connects_to:
- b1-50 (Adverbial Participles — Imperfective)
prerequisites:
- b1-48 (Passive Constructions)
persona:
  voice: Senior Language & Culture Specialist
  role: Linguistic Researcher
grammar:
- Означено-особові речення (definite-personal)
- Неозначено-особові речення (indefinite-personal)
- Безособові речення (impersonal)
- Називні речення (nominal)
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

Research **Односкладні речення** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Односкладні речення

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
