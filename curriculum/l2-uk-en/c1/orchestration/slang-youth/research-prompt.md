# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-061
level: C1
sequence: 61
slug: slang-youth
version: '1.0'
title: Сленг та молодіжна мова
subtitle: Slang & Youth Language
focus: style
pedagogy: TTT
phase: C1.5 [Stylistics & Rhetoric]
word_target: 4000
objectives:
- Learner can understand and appropriate use common Ukrainian youth slang
- Learner can distinguish between slang and standard language
- Learner can analyze the influence of English on modern Ukrainian slang
content_outline:
- section: 'Вступ: Сленг як соціальний інструмент (Introduction: Slang as a Social Tool)'
  words: 500
  points:
  - 'Визначення сленгу згідно з Держстандартом (§4.4.1.1): роль розмовного стилю як маркера соціальної ідентифікації молоді.'
  - 'Сленг vs Суржик: розмежування свідомого використання соціолекту та мовної інтерференції (напр. ''оф корс'' vs ''канєшно'').'
  - 'Поняття мовної моди та динамічності лексики: чому сленг 90-х (''шнурки в стакані'') поступився місцем сучасним запозиченням.'
- section: 'Аналіз англізації: ''Укр-інгліш'' (The Phenomenon of Anglicization: ''Ukr-English'')'
  words: 1000
  points:
  - 'Вплив глобалізації на сучасне мовлення: перехід від русизмів до активного запозичення з англійської (чілити, стрімити,
    донатити).'
  - 'Морфологічна адаптація англіцизмів: розбір помилки невідмінювання (напр. правильне ''ловити вайб'' vs помилкове ''без
    настрій'' замість ''настрою'').'
  - 'Лексичні пласти: геймерський сленг, сленг соцмереж (TikTok/YouTube) та офісний сленг.'
- section: Стилістичні засоби та літературний контекст (Stylistic Means and Literary Context)
  words: 900
  points:
  - 'Використання сленгу в сучасній літературі: аналіз творчості С. Жадана, І. Карпи та Л. Дереша як засобу передачі живого
    мовлення.'
  - 'Стилістичні прийоми за Держстандартом (§4.4.3): використання скорочень, абревіатур та згрубілих форм для створення образу
    героя.'
  - 'Експресивність та конотація: як слова ''крінж'', ''зашквар'' та ''рофл'' передають емоційний стан краще за стандартну
    лексику.'
- section: 'Практика: Регістри та комунікативні ситуації (Practice: Registers and Communicative Situations)'
  words: 1000
  points:
  - 'Типова помилка: змішування регістрів (використання ''Ок'' чи ''Супер'' в офіційному листуванні з викладачами) та шляхи
    її виправлення.'
  - 'Трансформація: переклад речень зі сленгу на літературну мову і навпаки для відчуття межі офіційності.'
  - 'Соціальна дистанція: розбір ситуацій, де використання сленгу є доречним (peer-to-peer), а де — ризикованим (зашкварним).'
- section: 'Підсумок: Мовний портрет покоління (Conclusion: Linguistic Portrait of a Generation)'
  words: 600
  points:
  - 'Рефлексія на тему ''душності'' мовного пуризму: чи збіднює сленг українську мову, чи робить її життєздатною (жиза).'
  - 'Створення власного ''словника актуального вайбу'': закріплення вивчених колокцій (кидати пруфи, повний крінж).'
  - 'Прогноз розвитку: як англіцизми стають частиною стандартного розмовного стилю С1.'
vocabulary_hints:
  required:
  - крінж (cringe) — ловити крінж, повний крінж; висока частота (Gen Z), маркер сорому
  - вайб (vibe) — класний вайб, вайбовий, перевірка вайбу; висока частота, атмосфера
  - рофлити (to rofl) — рофлити з когось, це просто рофл; середня частота, глузувати/жартувати
  - жиза (life/relatable) — ну це жиза, життєво; висока частота, вказує на спільний життєвий досвід
  - зашквар (disgrace/shame) — повний зашквар, зашкварна історія; висока частота, ганьба
  - душнити (to be boring/toxic) — не душни, який ти душний; висока частота, занудствувати
  recommended:
  - топчик (top/great) — це просто топчик, виглядати топ; позитивна оцінка
  - пруф (proof) — кинути пруфи, де пруфи?; вимога доказів у дискусії
  - чілити (to chill) — відпочивати, розслаблятися
  - донатити (to donate) — переказувати кошти (особливо на ЗСУ)
  - стрімити (to stream) — вести пряму трансляцію
vocabulary:
  required: '[]'
  recommended: '[]'
  forbidden: '[]'
persona:
  voice: Senior Specialist
  role: Молодіжний блогер
prerequisites:
- intimate-register
connects_to:
- persuasive-speech
grammar:
- Сленг як соціальний інструмент
- '''Укр-інгліш'''
- Стилістичні засоби та літературний контекст
- Регістри та комунікативні ситуації
register: літературний
activity_hints:
- type: match-up
  focus: Match 'Укр-інгліш' examples to categories
  items: 12
- type: group-sort
  focus: Classify by Стилістичні засоби та літературний контекст
  items: 12
- type: fill-in
  focus: Rewrite in target register
  items: 10
- type: quiz
  focus: Identify stylistic devices in context
  items: 12
- type: error-correction
  focus: Fix register-inappropriate language
  items: 8
- type: essay-response
  focus: Produce text in specified style

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

Research **Сленг та молодіжна мова** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Сленг та молодіжна мова

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
