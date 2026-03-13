# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-080
level: B1
sequence: 80
slug: regions-west
version: '2.0'
title: 'Українські регіони: Захід'
subtitle: Western Ukraine - Regions and Heritage
focus: culture
pedagogy: CBI
phase: B1.7 [Contemporary Ukraine]
word_target: 4000
objectives:
- Learner can discuss Western Ukraine's regions and cultural heritage
- Learner can understand authentic texts about Lviv, Galicia, and Zakarpattia
- Learner can use regional vocabulary to describe Western Ukrainian culture
- Learner can compare Western Ukrainian traditions with other regions
content_outline:
- section: 'Вступ: Захід як вікно в Європу (Introduction: The West as a Window to Europe)'
  words: 600
  points:
  - Географічне розташування Західної України як 'вікна в Європу' та прикордонного мозаїчного регіону.
  - 'Державний стандарт §3.13: Опис ландшафту, інституцій та громадських місць, що формують особливу ідентичність Заходу.'
  - 'Розвінчування міфу про однорідність: короткий огляд відмінностей між Галичиною, Волинню, Буковиною та Закарпаттям.'
- section: Львів — місто кави та архітектури (Lviv — City of Coffee and Architecture)
  words: 1000
  points:
  - 'Історія львівської кави: Юрій Кульчицький, Віденська битва (1683) та перша кав''ярня ''Під синьою пляшкою''.'
  - 'Культурний гачок: Як Кульчицький винайшов рецепт кави з молоком та цукром, ставши символом європейської інтеграції Львова.'
  - 'Архітектурна спадщина: Львів як об''єкт Світової спадщини ЮНЕСКО (Державний стандарт §3.13).'
  - 'Робота над помилками: Жіночий рід слова ''кава'' в українській мові — вправи на узгодження прикметників (смачна кава,
    львівська кава).'
- section: 'Галичина: Традиції та мовний колорит (Galicia: Traditions and Linguistic Flavor)'
  words: 800
  points:
  - 'Навчальна помилка: Правильне вживання прийменників з історичними регіонами — ''на Галичині'' (територія) замість ''в
    Галичині''.'
  - 'Галицький діалект як маркер ідентичності: вживання слів ''філіжанка'', ''коліжанка'', ''файно'' в автентичному контексті.'
  - 'Державний стандарт §3.15: Роль Греко-католицької церкви та місцевих звичаїв у збереженні українських традицій.'
- section: Закарпаття — мозаїка культур та природи (Zakarpattia — A Mosaic of Cultures and Nature)
  words: 1000
  points:
  - 'Закарпаття як мультикультурне порубіжжя: суміш українських, угорських, румунських та словацьких впливів.'
  - 'Кулінарна дипломатія: традиції закарпатської кухні (бограч) та виноробства як частина туристичної привабливості.'
  - 'Карпатські гори: туризм, екологія та побут етнічних груп (гуцули, бойки, лемки) згідно зі стандартом §3.13.'
- section: 'Підсумок: Захід у серці України (Summary: The West in the Heart of Ukraine)'
  words: 600
  points:
  - Роль Західної України у національному відродженні та сучасній культурній дипломатії.
  - Порівняння регіональних особливостей (Галичина vs Закарпаття) для підготовки до модуля B1-73 (Схід України).
  - Повторення стратегій розуміння автентичних текстів про пам'ятки культури та туристичні принади.
vocabulary_hints:
  required:
  - регіон (region) — гірський регіон, прикордонний регіон; висока частотність
  - спадщина (heritage) — культурна спадщина, світова спадщина ЮНЕСКО; академічний реєстр
  - традиція (tradition) — за народною традицією, підтримувати традицію; загальновживане
  - архітектура (architecture) — пам'ятка архітектури, старовинна архітектура; тематичне
  - 'Галичина (Galicia) — вживання: НА Галичині (historical region preposition)'
  - 'Закарпаття (Zakarpattia) — вживання: НА Закарпатті; природа Закарпаття'
  - Львів (Lviv) — культурна столиця, львів'янин/львів'янка
  - культура (culture) — мозаїка культур, центр українського відродження
  recommended:
  - кав'ярня (coffee shop) — затишна львівська кав'ярня; осередок спілкування
  - гори (mountains) — відпочинок у горах, Карпати
  - етнічний (ethnic) — етнічні групи, етнічний склад населення
  - ідентичність (identity) — національна ідентичність, особлива ідентичність
  - філіжанка (cup) — галицький діалектизм; часто вживається з 'кава'
  - файно (fine/well) — діалектне прислівник, характерне для Заходу
  - колежанка (female colleague/friend) — специфічне західноукраїнське звертання
  - бограч (bograch) — закарпатська м'ясна страва; культурний маркер
activity_hints:
- type: reading
  focus: Authentic texts about Western Ukraine
  items: 15
- type: match-up
  focus: Match regions to features
  items: 20
- type: fill-in
  focus: Complete cultural descriptions
  items: 15
- type: quiz
  focus: Compare regional cultures
  items: 10
connects_to:
- 'b1-81 (Українські регіони: Схід)'
prerequisites:
- b1-79 (Емоційний інтелект та міжособистісні навички)
persona:
  voice: Senior Language & Culture Specialist
  role: Lviv Coffee Connoisseur
grammar:
- Reading comprehension strategies
- Cultural vocabulary in context
- Descriptive language patterns
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

Research **Українські регіони: Захід** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Українські регіони: Захід

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
