# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-020
level: B1
sequence: 20
slug: motion-passing-crossing
version: '2.0'
title: 'Рух: перехід і обхід'
subtitle: Motion - Passing & Crossing
focus: grammar
pedagogy: TTT
phase: B1.2 Motion
word_target: 4000
objectives:
- Learner can use пере- for crossing
- Learner can use про- for passing through/by
- Learner can use об- for going around
sources:
- name: Ukrainian State Standard 2024 - Motion Prefixes
  url: https://mon.gov.ua/
  type: reference
  notes: Official prefix meanings for crossing/passing
- name: Ukrainian Verbal Prefixes
  url: https://uk.wikipedia.org/wiki/Дієслівні_префікси
  type: reference
  notes: пере-, про-, об- semantics
content_outline:
- section: Вступ (Introduction)
  words: 400
  points:
  - 'Contextualize motion in an urban environment: the challenge of navigating barriers, bridges, and complex routes.'
  - 'Introduce the ''Kyiv Traffic Controller'' persona: an expert who values precision in prefix usage for safety and efficiency.'
  - Explicitly reference Ukrainian State Standard §4.3.8 regarding the formation of prefixed verbs for B1 proficiency.
- section: Тест (Diagnostic)
  words: 600
  points:
  - 'Diagnostic prefix selection: distinguish direct crossing (пере-) from avoiding (об-) using visual scenarios of obstacles.'
  - 'Calque detection: address the learner error of using motion verbs for academic ''passing'' (скласти іспит ≠ пройти).'
  - 'Intuition check: describe the trajectory across a major bridge like Міст Патона vs. going around a traffic jam (затор).'
- section: Пояснення (Explanation)
  words: 1000
  points:
  - 'Visual logic of trajectories: provide Mermaid diagrams for пере- (A → B across), про- (A → B through/past), and об- (A
    ↺ B around).'
  - 'Grammar focus: mastering the direct Accusative for crossing (перейти вулицю) as per standard §4.2.2.4 to avoid redundant
    prepositions.'
  - 'Contrastive semantics: explain why обійти implies a longer or more cautious path compared to the direct transversal of
    перейти.'
- section: Поглиблення (Expansion)
  words: 1000
  points:
  - 'Cultural deep dive: usage of переїжджати vs проїжджати in the context of the bascule Інгульський міст (lifting for ships).'
  - 'Aesthetic landmarks: describing a train crossing the valley via the picturesque Віадук у Плебанівці using precise motion
    verbs.'
  - 'Figurative nuances: distinguish physical bypassing from figurative meanings like ''overlooking'' (обійти увагою) or ''crossing
    the line'' (перейти межу).'
- section: Практика (Practice)
  words: 600
  points:
  - 'Route planning simulation: drafting a GPS navigation sequence to navigate Kyiv traffic, avoiding obstacles like яма and
    затор.'
  - 'Error correction drill: identifying and fixing redundant usage of ''через'' with crossing verbs (correction: перейти
    міст, not перейти через міст).'
  - 'Situational drills: choosing between про- and об- when encountering a crowd (пройти крізь натовп) vs. a physical barrier
    (обійти перешкоду).'
- section: Підсумок (Production)
  words: 400
  points:
  - 'Roleplay: acting as a navigator giving instructions to cross the Dnipro river, emphasizing the structural importance
    of Міст Патона.'
  - 'Linguistic reflection: summarizing the ''Theory-First'' logic of prefixation as a tool for decolonizing and professionalizing
    communication.'
  - 'Final synthesis: mapping specific verbs to the core B1 requirements of describing complex city routes.'
vocabulary_hints:
  required:
  - перейти/переходити (to cross on foot) — перейти вулицю (direct Accusative), перейти на інший бік; High frequency
  - 'переїхати/переїжджати (to cross by vehicle) — переїжджати міст (cultural hook: Міст Патона), переїхати кордон'
  - 'пройти/проходити (to pass on foot) — пройти повз будинок, пройти крізь натовп; Note: do not use for ''passing a test'''
  - проїхати/проїжджати (to pass by vehicle) — проїхати по мосту, проїхати повз зупинку; High frequency
  - обійти/обходити (to go around on foot) — обійти перешкоду (to bypass), обійти стороною (to avoid); Medium frequency
  - об'їхати/об'їжджати (to drive around) — об'їхати яму, об'їхати затор (to avoid traffic)
  - маршрут (route) — планувати маршрут, слідувати за маршрутом; Medium frequency
  - перешкода (obstacle) — долати перешкоду (overcome), обійти перешкоду (bypass)
  recommended:
  - перебігти/перебігати (to run across) — перебігти дорогу (often implies danger)
  - пробігти/пробігати (to run past) — пробігти повз крамницю
  - оббігти/оббігати (to run around) — оббігти навколо будинку
  - затор (traffic jam) — потрапити в затор, об'їхати затор
  - яма (hole/pothole) — об'їхати яму на дорозі
  - 'скласти іспит (to pass an exam) — Lexical distinction note: use instead of motion verbs'
activity_hints:
- type: quiz
  focus: пере- vs про- vs об- selection
  items: 15+
- type: fill-in
  focus: Route descriptions with correct prefixes
  items: 12+
- type: fill-in
  focus: Change movement type (cross → pass → around)
  items: 10+
- type: fill-in
  focus: Narrative describing a journey
  items: 12+
- type: match-up
  focus: Situation → prefixed verb
  items: 12+
connects_to:
- b1-19 (Motion - starting & returning)
- b1-22 (Motion full prefix integration)
prerequisites:
- 'b1-19 (Рух: Прибуття та вихід)'
persona:
  voice: Senior Language & Culture Specialist
  role: Kyiv Traffic Controller
grammar:
- Prefixes пере-, про-, об-
- Crossing, passing, going around patterns
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

Research **Рух: перехід і обхід** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Рух: перехід і обхід

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
