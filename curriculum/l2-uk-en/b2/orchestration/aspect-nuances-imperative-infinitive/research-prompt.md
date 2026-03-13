# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-041
level: B2
sequence: 41
slug: aspect-nuances-imperative-infinitive
version: '2.0'
title: 'Відтінки виду II: наказовий спосіб та інфінітив'
subtitle: Вид дієслова в командах та інфінітивних конструкціях
focus: grammar
pedagogy: TTT
phase: B2.5
word_target: 4000
objectives:
- Learner can distinguish polite invitations from urgent commands by aspect
- Learner can form prohibitions using the correct aspect
- Learner can interpret не можна + infinitive based on aspect
- Learner can choose appropriate aspect in imperative for different situations
content_outline:
- section: 'Вступ: Культура спонукання та етикет (Introduction: The Culture of Prompting & Etiquette)'
  words: 600
  points:
  - 'The ''Polite Ukrainian Host'' concept: why Imperfective aspect (Сідайте, заходьте, беріть) is essential for hospitality,
    contrasting with the distance created by the Perfective.'
  - 'Learner error ''The Rude Guest'': analyzing why ''Сядь!'' (Perf) sounds like a military order or a command to a pet,
    whereas ''Сідай'' (Impf) sounds welcoming.'
  - 'State Standard §4.3.1.3 integration: expressing requests and advice through softened forms of the imperative mood.'
- section: Граматика та морфологія наказу (Grammar & Morphology of Commands)
  words: 1000
  points:
  - 'Morphological formation according to §4.1.3.2: regular patterns for ''хотіти'', ''літати'', and ''робити'' across different
    persons (ходи, ходімо, ходіть).'
  - 'The spectrum of ''наказ'' vs ''прохання'': using Perfective for categorical, urgent, or single-result actions (Зроби
    це зараз!) vs Imperfective for processes or recurring actions.'
  - 'Military register nuances (Persona): the use of Perfective aspect in formal ''накази'' (orders) to ensure clarity of
    the required outcome.'
- section: Заборони, застереження та забобони (Prohibitions, Warnings, & Superstitions)
  words: 800
  points:
  - 'The ''Accident Warning'' rule: using Perfective aspect to warn against unintentional results (''Не впади!'', ''Не забудь!'')
    vs Imperfective for general prohibitions (''Не бігай!'').'
  - 'Cultural ''Забобони'' (superstitions) as a linguistic anchor: teaching ''Не можна'' + Imperfective through taboos like
    ''Не можна передавати речі через поріг''.'
  - Distinguishing 'Не' + Imperfective (Forbidden action) from 'Не' + Perfective (Warning against a negative result/accidental
    completion).
- section: 'Модальність інфінітива: Правила vs Можливість (Infinitive Modality: Rules vs Possibility)'
  words: 900
  points:
  - 'The Semantic Divide: ''Не можна'' + Imperfective (It is forbidden/against the law/taboo) vs ''Не можна'' + Perfective
    (It is physically impossible/the result cannot be achieved).'
  - 'Case study: ''Не можна відчиняти вікно'' (Prohibited by the ''процес'') vs ''Не можна відчинити вікно'' (It is stuck/physically
    impossible to complete the ''аналіз'').'
  - Integrating academic vocabulary (метод, поняття, дослідження) into modal constructions to discuss scientific constraints
    and methodologies.
- section: 'Професійне застосування: Накази та інструкції (Professional Application: Orders & Instructions)'
  words: 700
  points:
  - 'Drafting formal instructions: selecting aspect based on the ''термін виконання'' (deadline) and nature of the ''процес''
    (ongoing vs finite).'
  - 'Synthesis of grammar: writing a ''наказ'' (order) for a military scenario or a ''правила гри'' (game rules) using correct
    aspectual nuances for prohibitions and invitations.'
  - 'Review of ''Common Learner Errors'' in official-business style: avoiding inappropriate imperatives in formal ''прохання''
    (requests).'
vocabulary_hints:
  required:
  - аналіз (analysis) — глибокий аналіз (deep analysis), проводити аналіз (to conduct an analysis), критичний аналіз (critical analysis).
  - синтез (synthesis) — логічний синтез (logical synthesis), результати синтезу (results of synthesis).
  - дослідження (research) — наукове дослідження (scientific research), результати дослідження (research results), проводити дослідження (to conduct research).
  - наказ (order) — віддати наказ (to issue an order), виконувати наказ (to follow an order), згідно з наказом (according to the order); High frequency in military/official contexts.
  recommended:
  - аналіз (analysis) — глибокий аналіз (deep analysis), проводити аналіз (to conduct an analysis), критичний аналіз (critical analysis).
  - синтез (synthesis) — логічний синтез (logical synthesis), результати синтезу (results of synthesis).
  - дослідження (research) — наукове дослідження (scientific research), результати дослідження (research results), проводити дослідження (to conduct research).
  - наказ (order) — віддати наказ (to issue an order), виконувати наказ (to follow an order), згідно з наказом (according to the order); High frequency in military/official contexts.
  - прохання (request) — велике прохання (big request), на прохання (at the request of), звертатися з проханням (to address with a request).
  - заборона (prohibition) — сувора заборона (strict prohibition), накласти заборону (to impose a ban), порушити заборону (to violate a prohibition).
activity_hints:
- type: quiz
  focus: Identify Aspect in imperative mood in sentences
  items: 12
- type: fill-in
  focus: Complete sentences using Aspect in imperative mood
  items: 10
- type: match-up
  focus: Match Граматика та морфологія наказу examples to categories
  items: 12
- type: error-correction
  focus: Find and fix errors in Aspect in imperative mood
  items: 8
- type: group-sort
  focus: Classify examples by Заборони, застереження та забобони
  items: 12
- type: essay-response
  focus: Write paragraph using Aspect in imperative mood correctly
persona:
  voice: Professional Language Coach
  role: Military Instructor (Військовий інструктор)
grammar:
- Aspect in imperative mood
- Imperfective vs perfective commands
- Prohibition with imperfective
- Aspect in infinitive constructions
- не можна + aspect distinction
prerequisites:
- aspect-nuances-secondary-imperfectivization
connects_to:
- pluperfect-tense
register: нейтральний

```

**Level constraints quick-ref:**

```
# B2 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words.`, etc.

## Grammar Scope

**Allowed:** Full grammar including adverbial participles.
Max 35 words per Ukrainian sentence. Max 6 clauses.

## Immersion (100% Ukrainian)

All content in Ukrainian. English ONLY in vocabulary table translations (YAML).
B2 learners have internalized all grammar terminology from B1 — no English scaffolding needed.

## Module Types

| Type | Modules | Pedagogy | Structure |
|------|---------|----------|-----------|
| Grammar | M01-40 | TTT | Діагностика → Аналіз → Поглиблення → Практика → Підсумок |
| Phraseology | M41-70 | CBI | Вступ → Наратив → Аналіз → Граматика в контексті → Підсумок |
| Integration | M71-83 | CBI | Same as phraseology |
| Communication | M85-93 | CBI | Same as phraseology |
| Checkpoint | M10,30,40,70,84 | — | Review + assessment |

> History content is in separate **HIST** track.

## B2-Specific Writing Notes

- No language mixing — every sentence fully Ukrainian or fully English (English only in vocab YAML)
- Fill-in blanks use `___` format (no brackets)
- Error-correction items: the `error` field marks the wrong word, `answer` is the correct replacement

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `B2` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Відтінки виду II: наказовий спосіб та інфінітив** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Відтінки виду II: наказовий спосіб та інфінітив

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
