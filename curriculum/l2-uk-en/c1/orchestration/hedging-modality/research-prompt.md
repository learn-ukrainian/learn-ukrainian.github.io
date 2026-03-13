# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-006
level: C1
sequence: 6
slug: hedging-modality
version: '2.0'
title: Хеджінг та модальність
subtitle: 'Introduction: Ethics and Academic Style'
content_outline:
- section: 'Вступ: Етика та науковий стиль (Introduction: Ethics and Academic Style)'
  words: 600
  points:
  - 'Роль хеджінгу в академічному дискурсі згідно з Державним стандартом (§4.4.1.1): баланс між упевненістю та науковою обережністю'
  - 'Професійна етика дослідника: чому пом''якшення тверджень є ознакою точності, а не слабкості позиції'
  - 'Дихотомія ''авторська суб''єктивність vs об''єктивність даних'': перехід від особистих переконань до аргументованих припущень'
- section: 'Граматика обережності: Вставні слова (Grammar of Caution: Parenthetical Words)'
  words: 800
  points:
  - 'Використання вставних слів для вираження ступеня впевненості (§4.3.2): ''мабуть'', ''очевидно'', ''ймовірно'', ''безперечно'''
  - 'Частотний аналіз прислівників: ''цілком ймовірно'', ''найбільш ймовірно'', ''стає очевидним'' як ключові маркери наукового
    стилю'
  - Функціональна різниця між 'безперечно' (для акцентування доведених фактів) та 'напевно' (для гіпотетичних зв'язків)
- section: Модальні дієслова та припущення (Modal Verbs and Assumptions)
  words: 800
  points:
  - 'Дієслівні конструкції хеджінгу: ''можна припустити'', ''є підстави вважати'', ''видається'', ''виявляється'''
  - 'Аналіз дієслова ''припускати'': типові академічні структури (''автори припускають'', ''це дає змогу припустити'')'
  - 'Ступені модальності: вибір між ''може'', ''міг би'' та ''мусить'' залежно від ваги наведених доказів'
- section: 'Культурні коди: Ми-авторське та епістолярій (Cultural Codes: We-author and Epistolary)'
  words: 700
  points:
  - 'Традиція Plurālis Auctōris в українській науці: використання ''Ми'' замість ''Я'' для досягнення об''єктивності (спадок
    НТШ)'
  - 'Дипломатичність української інтелігенції: аналіз хеджінгу в епістолярії Лесі Українки та Михайла Грушевського (''Чи не
    могли б Ви'', ''Дозволю собі зауважити'')'
  - Контраст між 'м'яким' стилем класичної еліти та імперативним, безапеляційним тоном радянського канцеляриту
- section: 'Аналіз помилок: Від кальки до норми (Error Analysis: From Calque to Norm)'
  words: 700
  points:
  - 'Помилка калькування суб''єктивності: заміна ''Я відчуваю, що...'' на нормативне ''Видається, що...'' або ''Дані свідчать
    на користь того, що...'''
  - 'Корекція структури ''Може бути'': відмова від кальки ''Maybe'' на користь вставних слів ''Можливо'' або ''Мабуть'''
  - 'Боротьба з надмірною категоричністю: трансформація тверджень ''Це точно так'' у гнучкі конструкції (''не виключено що'',
    ''цілком імовірно що'')'
- section: 'Підсумок: Стратегії наукової аргументації (Summary: Strategies for Academic Argumentation)'
  words: 400
  points:
  - 'Шкала впевненості: систематизація засобів хеджінгу від 25% (навряд чи) до 100% (безсумнівно)'
  - Практичні рекомендації щодо модуляції тону у висновках та рекомендаціях наукових робіт
  - 'Фінальна рефлексія: хеджінг як інструмент деколонізації наукового мислення через відмову від радянської авторитарності'
vocabulary_hints:
  required:
  - ймовірно (probably) — цілком ймовірно, найбільш ймовірно; висока частотність в академічних текстах
  - припускати (to assume) — є підстави припускати, автори припускають; ключове слово для гіпотез
  - очевидно (obviously) — стає очевидним; висока частотність, маркер логічного висновку
  - безперечно (undoubtedly) — безперечно важливий; використовується для емфази, але потребує обережності
  - навряд чи (hardly) — навряд чи можливо, навряд чи варто; маркер дистанціювання або скепсису
  - видається (it seems) — видається помилковим; стилістично правильний замінник суб'єктивного 'я думаю'
  - мабуть (perhaps) — вставне слово для вираження невпевненості або припущення
  - виключено (excluded) — не виключено що; конструкція для позначення високого ступеня ймовірності
  recommended:
  - певною мірою (to some extent) — для обмеження обсягу твердження
  - почасти (partly) — замінник 'частково' для урізноманітнення тексту
  - скоріш за все (most likely) — розмовна та публіцистична конструкція високої ймовірності
  - позаяк (since) — книжний сполучник для пояснення причини
  - на нашу думку (in our opinion) — вияв Plurālis Auctōris для скромності та об'єктивності
activity_hints:
- type: quiz
  focus: Certainty scale (0-100%) ranking
  items: 15+
- type: fill-in
  focus: Add hedging to categorical statements
  items: 12+
- type: match-up
  focus: Hedging device to certainty level
  items: 15+
- type: cloze
  focus: Academic text with hedging gaps
  items: 12+
- type: essay-response
  focus: Rewrite confident claims with appropriate hedging
- type: group-sort
  focus: Hedging expressions by strength
  items: 15+
focus: grammar
pedagogy: TTT
prerequisites:
- c1-05 (Logical Connectors)
- Academic style awareness
connects_to:
- c1-07 (Citation & Reference)
- c1-09 (Thesis Development)
- 'c1-57 (Ступені впевненості: Модальність та хеджування)'
module_type: grammar
sources:
- name: Academic Hedging in Ukrainian
  url: https://mova.info/
  type: reference
  notes: Research on hedging devices in Ukrainian academic writing
- name: Модальність у сучасній українській мові
  url: https://r2u.org.ua/
  type: secondary
  notes: Comprehensive modality analysis
immersion: 100% Ukrainian
phase: C1.1 [Academic Writing & Research]
objectives:
- Learner can identify and produce correct Вставні слова forms
- Learner can analyze Модальні дієслова та припущення in authentic texts
- Learner can produce written text demonstrating mastery of Етика та науковий стиль
persona:
  voice: Senior Specialist
  role: Дипломат
word_target: 4000
grammar:
- Етика та науковий стиль
- Вставні слова
- Модальні дієслова та припущення
- Ми-авторське та епістолярій
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

Research **Хеджінг та модальність** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Хеджінг та модальність

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
