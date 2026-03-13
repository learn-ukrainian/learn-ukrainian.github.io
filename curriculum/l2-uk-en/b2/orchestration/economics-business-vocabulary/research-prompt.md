# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-038
level: B2
sequence: 38
slug: economics-business-vocabulary
version: '2.0'
title: 'Економічна лексика: говоримо про бізнес'
subtitle: Economics & Business Vocabulary
focus: grammar
pedagogy: CLIL
phase: B2.4
word_target: 4000
objectives:
- Учень може читати та розуміти економічні новини українською мовою
- Учень може аналізувати економічні показники та їх значення
- Учень може обговорювати економічну ситуацію в Україні, використовуючи спеціалізовану лексику
content_outline:
- section: 'Вступ: Економічний ландшафт України (Introduction: Ukraine''s Economic Landscape)'
  words: 600
  points:
  - 'Аналіз сучасного стану економіки: IT-сектор як ''цифрова фортеця'' та його зростання під час війни'
  - 'Аграрна галузь: Україна як світовий лідер експорту зернових та особливості ''Зернового коридору'''
  - Основні галузі економіки (АПК, промисловість) та роль міжнародної допомоги й волонтерства у змінах
- section: Макроекономічні показники та державна політика (Macroeconomic Indicators and State Policy)
  words: 800
  points:
  - 'ВВП (валовий внутрішній продукт), інфляція та курс валют: динаміка та вплив на життя громадян'
  - Державний бюджет та борг; поняття споживчого кошика та сімейного бюджету (згідно зі стандартом §3.8)
  - Проблеми бідності, малозабезпечені групи населення та виклики безробіття в умовах воєнного стану
- section: Бізнес-структури та цифровізація (Business Structures and Digitalization)
  words: 900
  points:
  - 'Типи підприємств: різниця між ФОП (Sole Proprietor) та ТОВ (LLC); статус ''акули бізнесу'''
  - 'Цифрова трансформація: сервіс ''Дія.Бізнес'' як інструмент для швидкої реєстрації та ведення справ'
  - 'Фінансовий результат: дохід, витрати, чистий та валовий прибуток; отримання та розподіл прибутку'
- section: Фінансові операції та податкова система (Financial Operations and Tax System)
  words: 900
  points:
  - 'Банківська справа: відкриття поточних та депозитних рахунків; дії з рахунком (поповнити, заблокувати)'
  - 'Податки в Україні: ПДВ, податок на прибуток, ЄСВ; податкове навантаження на малий та середній бізнес'
  - Страхування, кредитні лінії, процентні ставки та розвиток фінтеху й криптовалют в українському контексті
- section: Ділова комунікація та корекція помилок (Business Communication and Error Correction)
  words: 800
  points:
  - 'Норми ділового мовлення: виправлення кальки ''згідно із законом'' (не ''по закону'') та ''брати участь'' (не ''приймати'')'
  - 'Укладання угод: вживання ''укласти контракт'' або ''підписати угоду'' замість ненормативного ''заключити'''
  - 'Практичне застосування: аналіз економічних новин, читання фінансових графіків та побудова прогнозів'
vocabulary_hints:
  required:
  - прибуток (profit) — чистий ~, валовий ~, податок на ~; висока частотність у бізнес-реєстрі
  - угода (agreement/deal) — укладати угоду (не 'заключити'), підписувати ~, вигідна ~; юридична сила
  - рахунок (account) — відкрити ~, поточний ~, депозитний ~, поповнити ~; банківська термінологія
  - економіка (economy) — ринкова ~, цифрова ~, національна ~; зростає або падає
  - бізнес (business) — малий та середній ~, вести ~, ~-план; загальновживаний термін
  - Дія.Бізнес (Diia.Business) — унікальний державний цифровий сервіс для підприємців
  - споживчий кошик (consumer basket) — набір товарів для оцінки рівня життя; стандарт §3.8
  - брати участь (take part) — єдина нормативна форма для ділового спілкування
  - згідно із законом (according to the law) — правильна конструкція; уникати 'по закону'
  recommended:
  - Дія.Бізнес (Diia.Business) — унікальний державний цифровий сервіс для підприємців
  - споживчий кошик (consumer basket) — набір товарів для оцінки рівня життя; стандарт §3.8
  - брати участь (take part) — єдина нормативна форма для ділового спілкування
  - згідно із законом (according to the law) — правильна конструкція; уникати 'по закону'
  - аналіз (analysis) — здійснювати ~, системний ~, фінансовий ~
  - синтез (synthesis) — метод синтезу, теоретичний ~
  - дослідження (research) — ринкове ~, проводити ~, результати ~
activity_hints:
- type: quiz
  focus: Identify Economic terminology and register in sentences
  items: 12
- type: fill-in
  focus: Complete sentences using Economic terminology and register
  items: 10
- type: match-up
  focus: Match Макроекономічні показники та державна політика examples to categories
  items: 12
- type: error-correction
  focus: Find and fix errors in Economic terminology and register
  items: 8
- type: group-sort
  focus: Classify examples by Бізнес-структури та цифровізація
  items: 12
- type: essay-response
  focus: Write paragraph using Economic terminology and register correctly
persona:
  voice: Professional Language Coach
  role: Economist (Економіст)
grammar:
- Economic terminology and register
- Business communication conventions
- Financial news reading strategies
register: науковий
prerequisites:
- law-justice-vocabulary
connects_to:
- checkpoint-domain

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

Research **Економічна лексика: говоримо про бізнес** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Економічна лексика: говоримо про бізнес

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
