# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-060
level: B2
sequence: 60
slug: idioms-somatic
version: '2.0'
title: 'Соматичні фразеологізми: Голова, обличчя, руки, ноги, тіло'
subtitle: All Somatic Idioms (head, face, hands, legs, body — merged)
focus: phraseology
pedagogy: CBI
phase: B2.6 [Lexicology]
word_target: 4000
objectives:
- Learner can recognize and interpret 25+ somatic idioms across head, hands, legs, heart, and body
- Learner can distinguish literal vs figurative meanings of body-related idioms
- Learner can classify somatic idioms by semantic group (intellect, action, movement, emotion)
- Learner can use somatic idioms appropriately across formal and informal registers
content_outline:
- section: 'Вступ: Тіло як дзеркало мови (Introduction: The Body as a Mirror of Language)'
  words: 500
  points:
  - 'Соматична фразеологія як система: голова = інтелект, руки = дія, ноги = рух, серце = емоції, очі = сприйняття'
  - 'Вимоги Державного стандарту (§4.4.1.2): використання фразеологізмів як стилістичного засобу для збагачення мовлення рівня
    B2'
- section: Голова, обличчя, очі (Head, Face, Eyes)
  words: 800
  points:
  - 'Ідіоми з «голова»: світла голова (розум), гаряча голова (імпульсивність), вішати голову (відчай), як сніг на голову (раптовість),
    морочити голову (набридати)'
  - 'Ідіоми з «око»/«обличчя»: впадати в око (не «кидатися в очі» — калька!), замилювати очі (обманювати), втратити обличчя
    (зганьбитися), краєм ока (неуважно)'
  - 'Етимологія: «опростоволоситися» — сакральність покриття голови; «водити за ніс» — ведмеді на ярмарку'
- section: Руки та плечі (Hands and Shoulders)
  words: 800
  points:
  - 'Ідіоми з «рука»: мати золоті руки (вправність), руки не доходять (нестача часу), рука об руку (разом), махнути рукою
    (відмовитися), брати себе в руки (самоконтроль)'
  - 'Ідіоми з «плече»: плечем до плеча (солідарність), мати голову на плечах (розсудливість), з плечей упало (полегшення)'
  - 'Прийменникове керування: різниця між «взяти в руки» (Acc), «тримати в руках» (Loc), «з рук у руки» (Gen→Acc)'
- section: Ноги, серце, спина (Legs, Heart, Back)
  words: 900
  points:
  - 'Ідіоми з «нога»: стати на ноги (досягти успіху), плутатися під ногами (заважати), ноги в руки (швидко), зі зв''язаними
    ногами (безпорадність)'
  - 'Ідіоми з «серце»: від щирого серця (щирість), брати до серця (хвилюватися), камінь на серці (тягар), легко на серці (полегшення)'
  - 'Ідіоми з «спина»/«шия»: сісти на шию (використовувати), за спиною (таємно), нести на своїх плечах (відповідальність)'
  - 'Граматична корекція: «сміятися з когось» (не «над кимось»)'
- section: 'Практичний синтез: весь корпус соматизмів (Practice: Full Body Idioms)'
  words: 1000
  points:
  - 'Класифікаційна вправа: розподіл 25+ ідіом за семантичними групами (інтелект, дія, рух, емоції, стосунки)'
  - 'Регістрова диференціація: книжні (втратити обличчя) vs розмовні (водити за ніс) vs нейтральні (мати золоті руки)'
  - 'Творче завдання: створення лінгвістичного портрета з використанням мінімум 8 соматизмів із різних частин тіла'
vocabulary_hints:
  required:
  - світла голова (bright mind) — про розумну, розсудливу людину; висока частотність
  - впадати в око (to catch the eye) — правильно вживати замість кальки 'кидатися в очі'
  - водити за ніс (to lead by the nose) — обманювати; розмовний стиль
  - мати золоті руки (to have golden hands) — бути вправним майстром; висока частотність
  - брати себе в руки (to pull oneself together) — самоконтроль; нейтральний стиль
  - стати на ноги (to get on one's feet) — досягти незалежності/успіху; нейтральний стиль
  - від щирого серця (from the bottom of one's heart) — щирість; висока частотність
  - втратити обличчя (to lose face) — втратити авторитет; книжний/діловий стиль
  recommended:
  - опростоволоситися (to make a fool of oneself) — зганьбитися (культурний контекст)
  - морочити голову (to mess with someone's head) — набридати; не плутати з 'ламати голову'
  - руки не доходять (can't get around to it) — нестача часу; розмовний стиль
  - плечем до плеча (shoulder to shoulder) — солідарність; публіцистичний стиль
  - камінь на серці (a weight on one's heart) — тягар; нейтральний стиль
  - сміятися з когось (to laugh at someone) — правильне прийменникове керування (не 'над')
activity_hints:
- type: match-up
  focus: Match idioms to their meanings
  items: 15
- type: group-sort
  focus: Classify idioms by Голова, обличчя, очі
  items: 12
- type: fill-in
  focus: Complete sentences with the correct idiom
  items: 10
- type: quiz
  focus: Choose the correct meaning of each idiom
  items: 12
- type: error-correction
  focus: Fix incorrect idiom usage
  items: 8
- type: essay-response
  focus: Use 5+ idioms in a coherent paragraph
connects_to:
- b2-61 (Idioms Animals)
prerequisites:
- b2-59 (Set Expressions Combined)
persona:
  voice: Professional Language Coach
  role: Portrait Painter (Портретист)
grammar:
- Fixed expressions (фразеологічні одиниці)
- Idiom structure and variation
register: varies
immersion: 100

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

Research **Соматичні фразеологізми: Голова, обличчя, руки, ноги, тіло** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Соматичні фразеологізми: Голова, обличчя, руки, ноги, тіло

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
