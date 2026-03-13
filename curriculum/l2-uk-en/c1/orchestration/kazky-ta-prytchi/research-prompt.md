# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-079
level: C1
sequence: 79
slug: kazky-ta-prytchi
version: '2.0'
title: Казки та притчі
subtitle: Ukrainian Folk Tales and Parables
content_outline:
- section: 'Вступ: Світ української казки та притчі (Introduction: The World of Ukrainian Fairy Tales and Parables)'
  words: 600
  points:
  - 'Визначення казки як універсального жанру та притчі як повчального тексту (§3.21 State Standard: традиції та звичаї)'
  - 'Архетип Котигорошка: аналіз ''українського супергероя'' як символу прихованої сили простого народу (Cultural Hook)'
  - Застосування стилю 'Казкар' (Storyteller) для занурення в атмосферу тексту при збереженні академічного рівня аналізу
- section: Класифікація та структура народної казки (Classification and Structure of Folk Tales)
  words: 900
  points:
  - 'Типологія казок: чарівні (Івасик-Телесик), про тварин (Лисичка-сестричка) та соціально-побутові (про бідного та багатого)'
  - 'Традиційна структура: зачин, розгортання дії, кінцівка. Використання інверсії ''Жив-був...'' (Learner Error: Word Order)'
  - 'Стилістичні засоби фольклору (§4.4.3): роль постійних епітетів та метафор у створенні магічного простору'
- section: Притчі, байки та літературні трансформації (Parables, Fables, and Literary Transformations)
  words: 900
  points:
  - 'Філософські притчі Григорія Сковороди: алегоризм та повчальність як основа української літературної традиції'
  - 'Байки Леоніда Глібова: жанрові особливості та роль моралі. Диференціація казки та байки (Learner Error: Fairy tale vs
    Fable)'
  - 'Сатира в казці ''Пан Коцький'': іронія над сліпою покорою авторитетам та ''страхом, що має великі очі'' (Cultural Hook)'
- section: Лінгвістичний аналіз та типові труднощі (Linguistic Analysis and Common Difficulties)
  words: 800
  points:
  - 'Аналіз переносного значення та алегорії в текстах притч: від буквального до філософського трактування'
  - 'Фразеологізми в казковому контексті: розуміння ідіом на кшталт ''піймати облизня'' (Learner Error: Literal Translation)'
  - 'Казкові формули та кліше: ''стали жити-поживати'', ''і я там був, мед-пиво пив'' як інструменти побудови наративу'
- section: Творча практика та дискусія (Creative Practice and Discussion)
  words: 800
  points:
  - 'Порівняльний аналіз: український Котигорошко vs європейські аналоги (аналіз схожих сюжетів та локальної специфіки)'
  - Написання сучасної притчі на задану тему з використанням алегоричних персонажів та моралі
  - Обговорення казки як інструменту сучасного виховання та деколонізації фольклорних наративів
focus: vocabulary
pedagogy: Immersion & Analysis
objectives:
- Learner can categorize Ukrainian folk tales into magic, animal, and social types
- Learner can analyze the moral and philosophical layers of Ukrainian parables
- Learner can use traditional storytelling formulas in their own narratives
grammar:
- Narrative structures
- Moral and allegorical registers
phase: C1.6 [Folk Culture & Traditions]
persona:
  voice: Senior Specialist
  role: Казкар
word_target: 4000
vocabulary_hints:
  required:
  - казка (fairy tale) — народна казка, чарівна казка, розказувати казку; high frequency
  - притча (parable) — біблійна притча, філософська притча, мова притч; medium frequency (literary)
  - байка (fable) — писати байки, мораль байки, персонажі байки; medium frequency (literary)
  - алегорія (allegory) — вдаватися до алегорії, прозора алегорія; academic register/medium frequency
  - мораль (moral) — мораль цієї історії, читати мораль, подвійна мораль; high frequency
  recommended:
  - зачин (opening/prologue) — традиційний зачин, казковий зачин; low frequency (literary/structural)
  - піймати облизня (to fail/be rebuffed) — ідіоматичний вираз; correction for literal translation errors
  - жив-був (once upon a time) — традиційна інверсія; usage marker for storytelling register
  - епітет (epithet) — постійний епітет, влучний епітет; academic register/stylistic analysis
prerequisites:
- kozatski-lehendy
connects_to:
- zymovi-obriady
register: літературний
activity_hints:
- type: quiz
  focus: Identify target structures in context
  items: 12
- type: fill-in
  focus: Complete sentences with correct forms
  items: 10
- type: match-up
  focus: Match Класифікація та структура народної казки examples to categories
  items: 12
- type: error-correction
  focus: Find and fix grammatical errors
  items: 8
- type: group-sort
  focus: Classify by Притчі, байки та літературні трансформації
  items: 12
- type: essay-response
  focus: Write using target structures correctly

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

Research **Казки та притчі** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Казки та притчі

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
