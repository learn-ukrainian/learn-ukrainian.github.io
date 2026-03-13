# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-058
level: B1
sequence: 58
slug: synonymy-thinking-verbs
version: '2.0'
title: 'Синонімія I: Дієслова мислення'
subtitle: 'Synonymy I: Thinking Verbs'
focus: vocabulary
pedagogy: PPP
phase: B1.6 [Vocabulary Expansion II]
word_target: 4000
objectives:
- Learner can distinguish between думати/гадати/вважати/міркувати
- Learner can use 20 thinking verbs in appropriate contexts
- Learner can form natural collocations with thinking verbs
- Learner can express cognitive processes precisely
content_outline:
- section: 'Вступ: Я мислю, отже я існую (Introduction: Cogito Ergo Sum)'
  words: 600
  points:
  - 'Cultural hook: Introduction to the philosophy of thinking through René Descartes’ iconic quote «Я мислю, отже я існую»
    (Cognito, ergo sum) and its significance in Ukrainian intellectual tradition.'
  - 'The power of precision: Why choosing the right ''thinking'' verb matters for character traits and personal views, aligning
    with State Standard §3.1 ''Людина''.'
  - 'Conceptual categorization: Distinguishing between cognitive processes (міркувати), expressing opinions (вважати), and
    pure states of understanding (розуміти).'
- section: 'Словник думок: Від «думати» до «вважати» (Vocabulary: From Thinking to Opining)'
  words: 800
  points:
  - 'Semantic deep dive into ''Думати'': Neutral usage (''думати про'' for general thoughts) vs. problem-solving nuance (''думати
    над'' for puzzles and tasks).'
  - 'The ''Opinion'' Tier: Using ''Вважати'' for formal discussions and personal stances (e.g., ''я вважаю, що...''); mapping
    it to formal stylistic registers.'
  - 'The ''Supposition'' Tier: Exploring ''Гадати'' (to suppose/guess) and its idiomatic usage in ''не довго думаючи й гадаючи''.'
  - 'The ''Process'' Tier: ''Міркувати'' as a deliberate, logical activity (міркувати вголос, міркувати логічно).'
- section: 'Аналіз помилок: Рахувати чи вважати? (Error Analysis: To Count or to Opine?)'
  words: 800
  points:
  - 'Critical correction of the common calque: Learner error ''Я рахую, що...'' (from Russian) vs. correct Ukrainian ''Я вважаю,
    що...''. Rule: ''Рахувати'' is strictly for numbers/money.'
  - 'Disambiguating ''Гадати'' vs. ''Ворожити'': Correcting the error ''Циганка гадала мені'' to ''Циганка ворожила мені'',
    clarifying that ''гадати'' is a mental act, not fortune-telling.'
  - 'State Standard §4.5.1.1 compliance: Exercises on stylistic differentiation between neutral ''я думаю'' and formal ''я
    вважаю'' in various social contexts.'
- section: Літературні думи та народна мудрість (Literary Thoughts and Folk Wisdom)
  words: 900
  points:
  - 'Cultural hook: Taras Shevchenko’s ''Думи мої, думи мої...'' — analyzing the word ''думи'' as a symbol of sorrowful reflection
    on the nation''s fate.'
  - 'Folk wisdom integration: Analyzing ''На те й голова, щоб у ній розум був'' to discuss the cultural value of pragmatic
    intelligence and comprehension (розуміти з півслова).'
  - 'Deep cognition: Exploring ''усвідомлювати'' (to realize) and ''осягати'' (to grasp/comprehend) through short philosophical
    excerpts.'
- section: 'Практика та підсумок: Точність міркувань (Practice and Summary: Precision of Reasoning)'
  words: 900
  points:
  - 'Scenario-based production: Choosing appropriate verbs for collocations like ''вважати за потрібне'' or ''дати зрозуміти''
    in workplace vs. personal dialogues.'
  - 'Synthesis: Connecting thinking to speaking (preparing for b1-69); learners express their cognitive process for solving
    a travel problem (linked to b1-67).'
  - 'Final summary: Recap of the 10/12 rule (choosing the right synonym for the right register) and a check on the State Standard
    competencies for §4.5.1.1.'
vocabulary_hints:
  required:
  - 'думати (to think) — High frequency, neutral; collocations: думати про (general), думати над (problem-solving)'
  - 'вважати (to consider/opine) — High frequency, formal; collocations: вважати за потрібне, вважати когось другом. Correct
    alternative to ''рахувати''.'
  - 'гадати (to suppose/guess) — Medium frequency; context: я гадаю, що...; ''не довго думаючи й гадаючи''.'
  - 'міркувати (to ponder/reason) — Medium frequency, process-oriented; collocations: міркувати логічно, міркувати вголос.'
  - 'розуміти (to understand) — High frequency; collocations: розуміти з півслова (to understand perfectly), дати зрозуміти
    (to hint/make understood).'
  - пам'ятати (to remember) — Cognitive state of retention.
  - згадувати (to recall/mention) — Active process of bringing to mind.
  - усвідомлювати (to realize/be conscious of) — Deep cognitive realization.
  - 'рахувати (to count) — Note: Often misused for ''вважати''; only for numbers/money.'
  - 'ворожити (to tell fortunes) — Note: Often confused with ''гадати''.'
  recommended:
  - роздумувати (to reflect/meditate) — Profound, often literary thought process.
  - обмірковувати (to deliberate/weigh) — Analyzing options before a decision.
  - осягати (to grasp/comprehend) — Achieving full intellectual understanding.
  - впізнавати (to recognize) — Cognitive identification of something known.
  - мислити (to think/reason) — Abstract, philosophical act of thinking (as in Descartes).
activity_hints:
- type: match-up
  focus: Match verbs to meanings
  items: 25
- type: fill-in
  focus: Choose correct thinking verb
  items: 20
- type: fill-in
  focus: Replace with synonyms
  items: 15
- type: fill-in
  focus: Express thoughts precisely
  items: 10
connects_to:
- 'b1-59 (Синоніми II: дієслова мовлення)'
prerequisites:
- b1-78 (Подорожі та географія)
persona:
  voice: Senior Language & Culture Specialist
  role: Philosopher
grammar:
- Verb synonymy and semantic distinctions
- Thinking verb collocations
- Cognitive verb patterns
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

Research **Синонімія I: Дієслова мислення** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Синонімія I: Дієслова мислення

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
