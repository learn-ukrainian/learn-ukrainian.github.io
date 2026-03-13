# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-009
level: B1
sequence: 9
slug: aspect-past-single-repeated
version: '2.0'
title: 'Вид у минулому: одного разу vs щодня'
subtitle: 'Aspect in Past: Single vs Repeated Actions'
focus: grammar
pedagogy: TTT
phase: B1.1 Aspect
word_target: 4000
objectives:
- Learner can distinguish single from repeated past actions
- Learner can select correct aspect based on time markers
- Learner can explain how frequency affects aspect choice
- Learner can transform between single and habitual narratives
sources:
- name: Ukrainian State Standard 2024 - Past Tense Aspect
  url: https://mon.gov.ua/
  type: reference
  notes: Official rules for aspect in past tense contexts
- name: Ukrainian Aspectual Pairs
  url: https://uk.wikipedia.org/wiki/Видові_пари_дієслів
  type: reference
  notes: Comprehensive list of aspectual pairs
content_outline:
- section: 'Тест: Два спогади (Test: Two Memories)'
  words: 600
  points:
  - 'Memoirist persona: Contrast a recurring childhood habit (repeated action) with a single, life-altering event (single
    action).'
  - 'Visual timeline deduction: Introduce the ''Dots on a line'' (habits) vs ''One big X'' (events) visualization to help
    learners identify frequency markers.'
  - 'Initial identification of time markers found in research: «щодня» vs «того разу» as triggers for aspect selection.'
- section: 'Презентація: Теорія та культурний контекст (Presentation: Theory and Cultural Context)'
  words: 1000
  points:
  - 'Alignment with State Standard §4.2.3.1: Systematic review of past tense formation for imperfective (хотів) and perfective
    (побачив) verbs.'
  - 'The Folk Tale Hook: Deep dive into «Одного разу...» (Once upon a time) as the canonical folk-tale opener that shifts
    language into narrative storytelling mode.'
  - 'Habitual Hospitality Hook: Cultural associations with «щонеділі» (every Sunday) and «на свята» (on holidays) as triggers
    for imperfective verb rituals (gathering, cooking, visiting).'
  - 'Semantic contrast table: Explicitly compare «читав» (process or habit) vs «прочитав» (achievement or result) using high-frequency
    collocations.'
  - 'Deconstructing ''Used to'' confusion: Explain how the Ukrainian past imperfective fully encompasses the English ''used
    to'' concept without requiring extra structures.'
- section: Грамматичні нюанси та типові помилки (Grammatical Nuances and Common Errors)
  words: 800
  points:
  - 'Learner Error Correction: Addressing the ''Perfective for Habituals'' trap (Він прочитав книгу щодня -> Він читав...)
    by focusing on the frequency marker over completion.'
  - 'Process vs Achievement: Distinguishing between ''Я складав іспит'' (the act of taking) and ''Я склав іспит'' (the success
    of passing) as a marker of single achievement.'
  - 'Selection algorithm: A step-by-step guide for choosing aspect based on frequency adverbs (часто, іноді, зазвичай) vs
    specific sequence markers (вперше, востаннє).'
- section: 'Практика: Минуле в деталях (Practice: Past in Detail)'
  words: 1000
  points:
  - 'School memories narrative: Practice contrasting teachers'' routines (habitual) with a specific memory of a graduation
    ceremony (single event).'
  - 'The ''One Summer'' Transformation: Drill transforming a habitual description (''Кожного літа ми їздили...'') into a specific
    narrative (''Того літа ми поїхали...'').'
  - 'Professional Memoir Dialogue: Scenario-based practice discussing repeated daily work tasks versus a single major career
    milestone.'
- section: 'Підсумок: Резюме маркерів (Summary: Marker Recap)'
  words: 600
  points:
  - 'Master table of frequency markers: Grouping ''always/often/usually'' (Imp) vs ''once/that day/that time'' (Perf) for
    quick reference.'
  - 'Persona reflection: A final narrative summary by the Memoirist, weaving together habits and specific events to showcase
    the beauty of Ukrainian aspectual flow.'
  - 'Self-check assessment: 10-item diagnostic identifying the ''Storytelling Mode'' triggered by narrative markers.'
vocabulary_hints:
  required:
  - 'одного разу (once) — High frequency; collocations: одного разу вранці/вночі; canonical folk-tale opener'
  - 'щодня (every day) — High frequency; synonym: кожного дня; collocations: робити щодня, бачити щодня'
  - 'часто (often) — Very High frequency; collocations: досить часто, дуже часто, як часто'
  - 'іноді (sometimes) — High frequency; collocations: тільки іноді, іноді навіть, іноді буває'
  - 'зазвичай (usually) — High frequency; usage: зазвичай ми, він зазвичай, як зазвичай'
  - 'того разу (that time) — Medium frequency; specific event marker; collocations: пам''ятаю того разу, саме того разу'
  - того дня (that day) — Specific perfective trigger for narrative events
  - 'завжди (always) — Very High frequency; collocations: назавжди (forever), завжди був, завжди казав'
  - ніколи (never) — Negative frequency marker; usually requires past imperfective for habits
  - рідко (rarely) — Frequency marker for repeated actions
  recommended:
  - регулярно (regularly) — Formal register frequency marker
  - постійно (constantly) — High intensity habitual marker
  - вперше (for the first time) — Achievement/single event marker
  - востаннє (for the last time) — Final occurrence marker
  - неодноразово (repeatedly) — Formal register for multiple occurrences
  - щонеділі (every Sunday) — Cultural hook associated with family rituals and imperfective aspect
  - на свята (on holidays) — Context for habitual hospitality and recurring actions
activity_hints:
- type: fill-in
  focus: Time marker → aspect selection
  items: 15+
- type: fill-in
  focus: Single event → habitual (and vice versa)
  items: 10+
- type: quiz
  focus: Which aspect for which context?
  items: 12+
- type: fill-in
  focus: Narrative with aspect choices
  items: 10+
- type: match-up
  focus: Time marker → aspect
  items: 12+
connects_to:
- b1-08 (Aspect in past - result vs process)
- b1-14 (Aspect integration practice)
prerequisites:
- 'b1-08 (Вид дієслова: повна система)'
persona:
  voice: Senior Language & Culture Specialist
  role: Memoirist
grammar:
- Aspect selection with time markers
- Single events vs habitual actions
- Frequency adverbs and aspect
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

Research **Вид у минулому: одного разу vs щодня** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Вид у минулому: одного разу vs щодня

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
