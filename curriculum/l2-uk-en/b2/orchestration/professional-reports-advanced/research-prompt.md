# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-068
level: B2
sequence: 68
slug: professional-reports-advanced
version: '2.0'
title: 'Професійні звіти: Поглиблення'
subtitle: Advanced analytical reports and presentation
focus: skills
pedagogy: CBI
phase: B2.7
word_target: 4000
objectives:
- Learner can write complex analytical reports with multiple data sources
- Learner can create advanced data visualizations and interpret trends
- Learner can use hedging and tentative language appropriately
- Learner can present report findings to stakeholders orally
- Learner can critically evaluate existing reports for quality
content_outline:
- section: Вступ (Introduction)
  words: 500
  points:
  - Перехід від базової звітності (М87) до аналітичної роботи з акцентом на реалізацію Держстандарту §1.3.2 щодо створення
    складних професійних текстів.
  - 'Культурний контекст: Федір Щербина як засновник української бюджетної статистики та приклад глибокої аналітичної традиції
    вивчення господарств.'
  - Роль аналітичних звітів у стратегічному плануванні компанії та розвиток критичного мислення в інтерпретації великих масивів
    даних.
- section: 'Імерсивна розповідь: Сучасна аналітика (Immersive Narrative: Modern Analytics)'
  words: 1200
  points:
  - Інтеграція даних з різних джерел (фінансові, маркетингові) та вагування надійності первинних і вторинних джерел через
    тріангуляцію даних.
  - 'Технологічний контекст: Проєкт StatGPT від Держстату України як приклад використання ШІ та відкритих даних у сучасній
    звітній діяльності, що руйнує стереотипи про бюрократію.'
  - 'Складна візуалізація та опис графіків: термінологія для опису осей абсцис/ординат, кривих зростання та діаграм розсіювання
    (scatter plots).'
  - 'Усна презентація звіту: адаптація складності до аудиторії та професійний етикет привітання (нормативний називний відмінок
    «Добрий день»).'
- section: Критичний аналіз та етика (Critical Analysis and Ethics)
  words: 900
  points:
  - Виявлення логічних помилок (хибна кореляція, селективні дані) та оцінка надійності методології (розмір вибірки, репрезентативність).
  - 'Етика звітності: чесність у презентації несприятливих даних та прозорість щодо обмежень дослідження для запобігання маніпуляціям.'
  - 'Професійна термінологія високого рівня: екстраполяція, сценарний аналіз, регресія та бізнес-аналітика (KPI, benchmark,
    SWOT).'
- section: Граматика та офіційно-діловий стиль (Grammar and Official Business Style)
  words: 900
  points:
  - 'Номіналізація: активне використання віддієслівних іменників на -ння, -ення (Стандарт §4.2.6) для досягнення лаконічності
    та точності в офіційному стилі.'
  - 'Модальні конструкції для професійного хеджування (hedging): використання «може свідчити», «ймовірно вказує», «за наявних
    даних» як ознаки наукової обережності.'
  - 'Корекція типових помилок: вживання «брати участь» замість кальки «приймати участь» та «протягом року» замість помилкового
    «на протязі».'
  - 'Усунення тавтологій та зайвих слів: редагування конструкцій типу «вільна вакансія» (тільки «вакансія») для підвищення
    якості тексту.'
- section: Підсумок (Summary)
  words: 500
  points:
  - 'Синтез навичок: від описової звітності до аналітичної майстерності та підготовка до новинного аналізу в наступних модулях
    (М89-90).'
  - 'Робота над граматичною коректністю: прийменникові конструкції «звіт за результатами» або «про результати» (замість помилкового
    «по результатам»).'
vocabulary_hints:
  required:
  - Звіт (report) — подати/скласти звіт, річний звіт, звіт за результатами; висока частота в діловому стилі
  - Дані (data) — обробляти дані, візуалізація даних, достовірність даних; ключовий термін аналітики
  - Аналіз (analysis) — глибокий аналіз, порівняльний аналіз, критичний аналіз; академічний та професійний регістр
  - Висновки (conclusions) — робити висновки, обґрунтовані висновки, дійти висновку; обов'язковий елемент структури
  - Тенденція (trend) — тенденція до зростання, виявити тенденцію, позитивна/негативна тенденція
  recommended:
  - Брати участь (to take part) — нормативна конструкція, критично важлива для уникнення кальки
  - Протягом (during/throughout) — часовий прийменник для звітів (напр. протягом звітного періоду)
  - Ймовірно (probably/likely) — модальне слово для хеджування та обережних висновків
  - Дослідження (research) — обмеження дослідження, результати дослідження, польове дослідження
  - Показник (indicator) — ключовий показник ефективності (KPI), динаміка показників
activity_hints:
- type: fill-in
  focus: Complete Сучасна аналітика with appropriate language
  items: 10
- type: quiz
  focus: Choose the best response for each scenario
  items: 12
- type: match-up
  focus: Match situations to appropriate language
  items: 12
- type: error-correction
  focus: Fix inappropriate register in Критичний аналіз та етика
  items: 8
- type: fill-in
  focus: Complete professional text with correct forms
  items: 8
- type: essay-response
  focus: Produce Сучасна аналітика for given scenario
persona:
  voice: Professional Language Coach
  role: Data Scientist (Дата-сайєнтист)
prerequisites:
- professional-reports-basics
connects_to:
- academic-writing
grammar:
- Report writing conventions
- Analytical language patterns
- Data presentation structures
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

Research **Професійні звіти: Поглиблення** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Професійні звіти: Поглиблення

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
