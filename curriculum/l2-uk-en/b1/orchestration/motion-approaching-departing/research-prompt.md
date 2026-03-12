# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-022
level: B1
sequence: 22
slug: motion-approaching-departing
version: '2.0'
title: 'Рух: наближення і віддалення'
subtitle: Motion - Approaching & Departing
focus: grammar
pedagogy: TTT
phase: B1.2 Motion
word_target: 4000
objectives:
- Learner can use під- for approaching
- Learner can use від- for departing
- Learner can use до- for reaching destination
sources:
- name: Ukrainian State Standard 2024 - Motion Prefixes
  url: https://mon.gov.ua/
  type: reference
  notes: Official prefix meanings for approach/depart
- name: Ukrainian Verbal Prefixes
  url: https://uk.wikipedia.org/wiki/Дієслівні_префікси
  type: reference
  notes: під-, від-, до- semantics
content_outline:
- section: 'Діагностика: Вступний тест (Diagnostic Test)'
  words: 600
  points:
  - 'Prefix diagnostic focusing on the common learner error: confusing під- (approach/come up to) with при- (arrive) — identifying
    the semantic mismatch in ''Я підійшов додому о 6-й'' versus the correct ''Я прийшов додому о 6-й''.'
  - Intuition check on reaching a limit (до-) vs general arrival (при-) — testing the learner's sense of 'дійти' as a process
    of walking all the way to a destination versus simply appearing there.
- section: 'Граматика: Простір та межі (Grammar: Space & Limits)'
  words: 1000
  points:
  - 'Strict preposition enforcement as a grammatical anchor: підійти ДО (genitive) and відійти ВІД (genitive) — mandatory
    drills for matching prefixes with their required prepositions.'
  - 'Semantic nuance breakdown based on State Standard §4.3.8: підійти implies proximity/getting close to an object, whereas
    дійти implies reaching the physical end or boundary of a path.'
  - 'Prefix selection drills to correct the від- vs ви- confusion: explaining why ''відійшов з кімнати'' is awkward and ''вийшов
    з кімнати'' (out of) is the correct motion for leaving an enclosed space.'
- section: 'Культурний контекст: Проводи та традиції (Cultural Context: Farewells & Traditions)'
  words: 800
  points:
  - 'Cultural hook: «Присісти на дорогу» (Sit for the road) — detailing the superstition of sitting in silence to trick house
    spirits (domovyk) before departure, now a practical moment for reflection.'
  - 'Railway station culture: «Проводи» (Farewells) — describing the tradition of waiting on the platform until the train
    physically moves (поїзд рушив/відійшов), emphasizing station-specific vocabulary.'
- section: Переносне значення та фразеологія (Figurative Meanings & Phraseology)
  words: 1000
  points:
  - 'Abstract usage of motion verbs: mastering ''дійти згоди'' (to reach an agreement), ''дійшли чутки'' (rumors reached/circulated),
    and ''відійти в минуле'' (to become history/fade away).'
  - 'Frequency-based collocations: using ''час підійти'' (time to approach), ''міра наближення'' (degree of approach), and
    ''поступове віддалення'' (gradual moving away) in formal or academic registers.'
- section: 'Практика: Роль начальника станції (Practice: Station Master Persona)'
  words: 600
  points:
  - 'Production task: Narrating a journey and departure schedule from the perspective of a Station Master, using ''поїзд відходить
    о...'' and describing passengers ''підходячи до каси''.'
  - 'Final summary and synthesis: Consolidating the approach-depart-reach sequence in a narrative about distance (відстань)
    and achieving a destination (досягнення).'
vocabulary_hints:
  required:
  - підійти/підходити (to approach on foot) — підійти до вікна, підійти ближче, час підійти; High frequency; implies proximity
  - під'їхати/під'їжджати (to approach by vehicle) — під'їхати до будинку, під'їхати на таксі
  - відійти/відходити (to move away on foot/depart) — відійти від краю, поїзд відійшов (departed), відійти в минуле (figurative);
    High frequency
  - від'їхати/від'їжджати (to drive away) — від'їхати від готелю, від'їжджати на літо
  - дійти/доходити (to reach on foot) — дійти додому, дійти згоди (figurative), дійшли чутки; High frequency; implies reaching
    the end of a path
  - доїхати/доїжджати (to reach by vehicle) — доїхати до міста, доїжджати до зупинки
  - наближення (approach) — наближення свята, міра наближення; Medium frequency (Academic/News)
  - віддалення (moving away) — ефект віддалення, поступове віддалення; Medium frequency (Formal)
  - досягнення (reaching/achievement) — досягнення мети, досягнення пункту призначення
  - відстань (distance) — велика відстань, на відстані кроку
  recommended:
  - підбігти/підбігати (to run up to) — підбігти до мами
  - відбігти/відбігати (to run away) — відбігти від небезпеки
  - добігти/добігати (to reach running) — добігти до фінішу
  - наблизитися (to approach - reflexive) — наблизитися до розв'язки
  - віддалитися (to move away - reflexive) — віддалитися від берега
  - Присісти на дорогу (to sit for the road) — traditional superstition before departure
  - Проводи (farewells) — railway station departure culture
activity_hints:
- type: quiz
  focus: під- vs від- vs до- selection
  items: 15+
- type: fill-in
  focus: Route descriptions with direction
  items: 12+
- type: fill-in
  focus: Approach → depart → reach sequence
  items: 10+
- type: fill-in
  focus: Narrative about a journey
  items: 12+
- type: match-up
  focus: Situation → prefixed verb
  items: 12+
connects_to:
- b1-21 (Motion - figurative uses)
- b1-24 (Motion full prefix integration)
prerequisites:
- b1-19 (Motion - starting & returning)
persona:
  voice: Senior Language & Culture Specialist
  role: Station Master
grammar:
- Prefixes під-, від-, до-
- Approaching, departing, reaching patterns
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

Research **Рух: наближення і віддалення** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Рух: наближення і віддалення

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
