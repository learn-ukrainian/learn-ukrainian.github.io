# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-078
level: B1
sequence: 78
slug: travel-geography
version: '2.0'
title: Подорожі та географія
subtitle: Travel & Geography
focus: vocabulary
pedagogy: PPP
phase: B1.6 [Vocabulary Expansion II]
word_target: 4000
objectives:
- Learner can use 30 travel and geography words in context
- Learner can distinguish between подорож/мандрівка/поїздка
- Learner can form natural collocations with travel vocabulary
- Learner can discuss travel plans and experiences
content_outline:
- section: Вступ (Introduction)
  words: 600
  points:
  - 'Ukrainian geography superlatives based on State Standard §3.14: Ukraine as the largest country entirely in Europe (603,628
    km²), Mount Hoverla (2061 m) as the highest peak, and the Dnipro river''s division into Right and Left Banks.'
  - 'Introduction to high-frequency travel collocations mandated by Standard §3.5: «вирушити в подорож», «незабутня мандрівка»,
    «далека подорож».'
  - 'Setting the narrative arc: from practical planning (booking) to physical geography (mountains/seas) to cultural sharing
    (natural wonders).'
- section: 'Лексичні нюанси: Поняття «подорож» (Lexical Nuances: The Concept of ''Travel'')'
  words: 800
  points:
  - 'Differentiating trip types to avoid common learner errors: «поїздка» (short/specific purpose, e.g., commute), «подорож»
    (general/long journey), and «мандрівка» (adventurous/literary context).'
  - 'Distinguishing vacation terminology: Adults taking «відпустка» (work leave) versus students having «канікули» (academic
    break); drill context-specific usage.'
  - 'Usage of register-specific terms: «регіон» (formal/news) vs «місцевість» (general description) in alignment with Standard
    §3.13.'
- section: Географія та природні дива (Geography & Natural Wonders)
  words: 1000
  points:
  - 'Cultural Hook: The Geometric Center of Europe near Dilove, Zakarpattia (historical marker from 1887) as a focal point
    for geographical discussion.'
  - 'The 7 Natural Wonders of Ukraine: Detailed exploration of Askania-Nova (virgin steppe), Dniester Canyon, Lake Synevyr
    (''Sea Eye''), Lake Svityaz (deepest), Podilski Tovtry, Granite-Steppe Lands of Buh, and Marble Cave.'
  - 'Describing diverse landscapes (Standard §3.14): From the ''Sea Eye'' of the Carpathians to the virgin steppes of the
    south, focusing on ''naturalness'' in landscape descriptions.'
- section: 'Граматичний практикум: Прийменники та локації (Grammar Workshop: Prepositions & Locations)'
  words: 800
  points:
  - 'Correcting prepositional errors with geographical locations: Drill «у горах» (Correct) vs «на горах» (Wrong); «на курорті»
    (Correct) vs «в курорті» (Wrong).'
  - 'Practical application of booking vocabulary (Standard §3.13): Using «бронювати» for hotels, tickets, and tables in a
    service-oriented dialogue context.'
  - 'Forming natural collocations with water bodies: «їхати на море», «відпочивати на морі» vs «купатися в озері».'
- section: Подорожні плани та враження (Travel Plans & Impressions)
  words: 800
  points:
  - 'Simulating travel planning dialogues: Integrating ''The Storyteller'' persona to describe Synevyr legends and Carpathian
    traditions with 100% Ukrainian immersion.'
  - 'Expressing impressions and sharing experiences: Differentiating ''unforgettable'' (незабутня) versus ''virtual'' (віртуальна)
    adventures.'
  - 'Summary of State Standard §3.5 competencies: Verifying the ability to describe transport, travel planning, and natural
    environments in a cohesive narrative.'
vocabulary_hints:
  required:
  - подорож (journey) — High frequency; далека подорож, вирушити в подорож, морська подорож, подорож мрії
  - мандрівка (adventure/trip) — Medium frequency (literary/adventurous); піша мандрівка, незабутня мандрівка, віртуальна
    мандрівка
  - поїздка (trip/short journey) — Focused on specific/short-term goals; ділова поїздка, поїздка на роботу
  - географія (geography) — Academic context; вивчати географію, фізична географія, географія України
  - регіон (region) — High frequency in formal/news contexts; гірський регіон, південний регіон, розвиток регіону
  - 'гори (mountains) — Plural; Карпатські гори, піднятися в гори, відпочинок у горах (Note: use ''у'' for location)'
  - 'море (sea) — Чорне море, тепле море, їхати на море, відпочивати на морі (Note: use ''на'' for location/direction)'
  - аеропорт (airport) — Travel hub; міжнародний аеропорт, їхати в аеропорт, чекати в аеропорту
  - бронювати (to book) — Service context; бронювати готель, бронювати квитки, бронювати столик
  recommended:
  - курорт (resort) — морський курорт, гірськолижний курорт, лікувальний курорт; use with preposition 'на'
  - відпустка (vacation/leave) — Specific to work; щорічна відпустка, йти у відпустку, бути у відпустці
  - канікули (school break) — Plural only; зимові канікули, бути на канікулах
  - екскурсія (excursion) — цікава екскурсія, замовляти екскурсію
  - центр Європи (center of Europe) — Cultural/geographical landmark near Dilove
  - диво природи (natural wonder) — refers to the '7 Natural Wonders' list
activity_hints:
- type: match-up
  focus: Travel noun phrases
  items: 25
- type: fill-in
  focus: Describe travel and geography
  items: 20
- type: match-up
  focus: Match geography terms
  items: 15
- type: quiz
  focus: Discuss travel experiences
  items: 10
connects_to:
- 'b1-58 (Синонімія I: Дієслова мислення)'
prerequisites:
- b1-77 (Основи бізнесу)
persona:
  voice: Senior Language & Culture Specialist
  role: Travel Agency Owner
grammar:
- Travel vocabulary collocations
- Geographical terminology
- Direction and location expressions
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

Research **Подорожі та географія** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Подорожі та географія

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
