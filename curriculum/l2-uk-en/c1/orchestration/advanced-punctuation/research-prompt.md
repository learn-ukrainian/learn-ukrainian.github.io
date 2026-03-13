# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-016
level: C1
sequence: 16
slug: advanced-punctuation
version: '2.0'
title: Поглиблена пунктуація
subtitle: Introduction — Punctuation as a Tool
content_outline:
- section: Вступ — Пунктуація як інструмент (Introduction — Punctuation as a Tool)
  words: 400
  points:
  - 'Роль пунктуації в науковому та публіцистичному текстах: відмінність між граматичною та інтонаційною функціями'
  - Пунктуаційна норма як засіб усунення двозначності в академічному письмі
  - 'Аналіз тексту: як розділові знаки структурують логіку викладу (builds on c1-05 Logical Connectors)'
- section: Складні речення та відокремлення (Complex Sentences and Separation)
  words: 900
  points:
  - 'Кома в складнопідрядних реченнях (§4.3.4.1): вживання перед сполучниками (і, а, але, що, який) та обставинними сполучними
    словами'
  - Пунктуація у складносурядних реченнях з протиставними відношеннями
  - 'Відокремлені члени речення (означення, обставини, додатки): правила та умови обов''язкового відокремлення'
  - 'Типова помилка: ''Кома-зрощення'' (Comma Splice) — аналіз вживання коми між граматичними основами без сполучника та методи
    виправлення через крапку з комою'
- section: 'Тире та двокрапка: смислова глибина (Dash and Colon: Semantic Depth)'
  words: 950
  points:
  - 'Тире між підметом і присудком (§4.3.4.2): випадки обов''язкового вживання (іменник-іменник, інфінітив-інфінітив)'
  - 'Двокрапка та тире у безсполучникових реченнях: вираження причиново-наслідкових та пояснювальних зв''язків (prepares for
    c1-107)'
  - Тире для підкреслення та авторське (інтонаційне) тире у публіцистиці
  - 'Learner error: графічна плутанина тире (пунктограма) та дефіса (орфограма) — правила розрізнення та написання'
  - Усунення зайвої коми через інтонаційну паузу між підметом і присудком (напр., 'Моя родина — це...')
- section: Цитування та допоміжні знаки (Citations and Auxiliary Marks)
  words: 650
  points:
  - 'Типи лапок в українській мові: традиційні «лапки-ялинки» для основного тексту та „лапки-лапки“ для внутрішніх цитат'
  - 'Пунктуація при цитуванні: оформлення прямої мови, квадратні дужки для кон''єктур та три крапки (еліпсис) для пропусків'
  - 'Круглі дужки для пояснень та ремарок: стилістичне використання в науковому апараті'
  - 'Вживання лапок для іронії та умовності: межа між стилістичним прийомом та надмірністю'
- section: Історичний контекст та стандартизація (Historical Context and Standardization)
  words: 500
  points:
  - 'Культурний гачок: еволюція знаків у давньоруських рукописах (XI–XIII ст.) — від довільних хрестиків і змійок до системності
    Альда Мануція'
  - Значення 'Харківського правопису' (1928 р.) у стандартизації української пунктуації та її відмежуванні від зовнішніх кальок
  - 'Реформи пунктуації у правописі 2019 року: актуалізація правил для сучасних медіа-текстів'
- section: Практика редагування (Editing Practice)
  words: 600
  points:
  - 'Алгоритм самоперевірки: розрізнення факультативних (авторських) та обов''язкових розділових знаків'
  - 'Трансформація речень: заміна безсполучникових конструкцій на сполучникові зі зміною пунктуації'
  - 'Редагування академічного есе: виправлення пунктуаційних огріхів у складних синтаксичних конструкціях (prepares for c1-18)'
vocabulary_hints:
  required:
  - пунктуація (punctuation) — правила пунктуації, пунктуаційна помилка; висока частотність у науковому стилі
  - кома (comma) — кома-зрощення (comma splice), ставити кому; базовий знак відокремлення
  - тире (dash) — інтонаційне тире, авторське тире, тире між підметом і присудком
  - двокрапка (colon) — після узагальнювального слова, перед переліком
  - лапки (quotation marks) — брати в лапки, іронічні лапки; розрізнення «ялинок» та „лапок“
  - відокремлення (separation) — відокремлені члени речення (appositives/modifiers); граматичний термін С1
  - підрядне речення (subordinate clause) — пунктуація на межі частин складного речення
  - еліпсис (ellipsis) — три крапки на місці пропущеного слова або частини цитати
  recommended:
  - пунктограма (punctuation rule/unit) — одиниця пунктуаційного правила
  - орфограма (spelling rule/unit) — для контрасту при вивченні тире/дефіса
  - факультативний (optional) — про авторські знаки, що не є обов'язковими за правописом
  - інтонаційний (intonational) — опис паузи, що зумовлює вибір знака
  - калька (calque) — у контексті уникнення чужорідних пунктуаційних моделей
activity_hints:
- type: error-correction
  focus: Fix punctuation errors in academic text
  items: 15+
- type: fill-in
  focus: Insert appropriate punctuation
  items: 15+
- type: quiz
  focus: Choose correct punctuation option
  items: 15+
- type: match-up
  focus: Punctuation mark to rule
  items: 12+
- type: cloze
  focus: Punctuate academic passages
  items: 10+
- type: group-sort
  focus: Classify punctuation functions
  items: 12+
focus: grammar
pedagogy: TTT
prerequisites:
- c1-05 (Logical Connectors)
- Complex sentence structures
connects_to:
- c1-17 (Irregular Verbs Complete)
- c1-18 (Essay Writing Practice)
- c1-48 (Literary Syntax)
- 'c1-44 (Безсполучникове речення: логіка тире і двокрапки)'
module_type: grammar
sources:
- name: Український правопис 2019
  url: https://mon.gov.ua/
  type: reference
  notes: Official punctuation rules
- name: Пунктуація сучасної української мови
  url: https://r2u.org.ua/
  type: secondary
  notes: Comprehensive punctuation guide
immersion: 100% Ukrainian
phase: C1.1 [Academic Writing & Research]
objectives:
- Learner can identify and produce correct Складні речення та відокремлення forms
- Learner can analyze смислова глибина in authentic texts
- Learner can produce written text demonstrating mastery of Вступ — Пунктуація як інструмент
persona:
  voice: Senior Specialist
  role: Коректор
word_target: 4000
grammar:
- Вступ — Пунктуація як інструмент
- Складні речення та відокремлення
- смислова глибина
- Цитування та допоміжні знаки
register: літературний

```

**Level constraints quick-ref:**

```
# C1 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words.`, etc.

## Grammar Scope

No grammar restrictions. Full literary Ukrainian. No sentence length limit.

## Immersion (100% Ukrainian)

Full Ukrainian immersion. All content — grammar explanations, narratives, dialogues,
cultural content, analyses, literary critiques, activity instructions, tips — in Ukrainian.

English ONLY in vocabulary table translations (YAML).

No Language Link boxes at C1 — students learned all grammar terminology by B1.

## Module Types

| Type | Modules | Focus |
|------|---------|-------|
| Academic | M01-19 | Academic foundation |
| Professional | M21-34 | Professional communication |
| Stylistics | M36-55 | Stylistics & sociolinguistics |
| Folk Culture | M56-85 | Folk culture & arts |
| Literature | M86-105 | Literary analysis |
| Checkpoint | M20,35,55,85,105,106 | Review + assessment |

> Biography content is in separate **BIO** track.

## Content-Heavy Modules (Folk/Literature M56+)

**Golden Rule:** "Can the learner answer without reading the Ukrainian text?"
- If YES → rewrite (tests content recall, not language)
- If NO → keep (tests Ukrainian comprehension)

Forbidden activity patterns: "У якому році...", "Хто був...", "Що символізує..." (without text reference)
Required patterns: "Згідно з текстом...", "У тексті модуля автор...", "Яку стилістичну функцію..."

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `C1` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Поглиблена пунктуація** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Поглиблена пунктуація

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
