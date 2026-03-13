# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-095
level: C1
sequence: 95
slug: operne-mystetstvo
version: '2.0'
title: Оперне мистецтво
subtitle: Opera Art
content_outline:
- section: 'Вступ: Історія та архітектура оперних центрів (Introduction: History and Architecture of Opera Centers)'
  words: 600
  points:
  - Історія заснування Львівської (1900) та Київської (1901) опер як символів європейської ідентичності України; порівняння
    архітектурних стилів із Віденською оперою.
  - 'Перша національна опера «Запорожець за Дунаєм»: синтез трагічного та комічного, що заклав фундамент українського оперного
    канону.'
- section: 'Золотий вік: Соломія Крушельницька та світове визнання (The Golden Age: Solomiya Krushelnytska and World Recognition)'
  words: 950
  points:
  - 'Культурний гачок: Як українська примадонна врятувала «Мадам Баттерфляй» Пуччіні після фіаско в Ла Скала, ставши ідеалом
    образу Чіо-Чіо-сан.'
  - 'Українська агентність: Крушельницька не просто брала участь у виставах, а формувала оперні стандарти свого часу на провідних
    сценах світу.'
  - 'Видатні голоси минулого: Борис Гмиря та Анатолій Солов''яненко — майстерність виконання та збереження національної традиції.'
- section: 'Сучасний ренесанс: Оксана Линів та диригентська майстерність (Modern Renaissance: Oksana Lyniv and Conducting
    Mastery)'
  words: 850
  points:
  - 'Оксана Линів як символ сучасної української музичної дипломатії: історичний виступ у Байройті (2021) — перша жінка за
    145 років.'
  - 'Професійна термінологія: обговорення ролі диригента, читання партитури та керування оркестром («під орудою диригента»).'
  - 'Світові баси сучасності: внесок Анатолія Кочерги в інтерпретацію класичного репертуару.'
- section: 'Культура мовлення: Музична точність та стилістика (Speech Culture: Musical Precision and Stylistics)'
  words: 700
  points:
  - 'Типові помилки: розмежування паронімів «музичний інструмент» (пов''язаний з музикою) та «музикальна людина» (талановита).'
  - 'Стилістична вправність за Держстандартом (§4.4.3): використання епітетів та метафор для опису вокальної майстерності
    (драматичне сопрано, глибокий бас).'
  - 'Уникнення кальок: заміна «грати на ролі» на «виконувати/грати роль» та перевага терміну «вистава» над «спектакль» у театральному
    контексті.'
- section: 'Мистецький дискурс: Рецензування та оперний аншлаг (Artistic Discourse: Reviewing and Opera Full House)'
  words: 900
  points:
  - 'Практика написання професійної рецензії на виставу за схемою: лібрето, постановка, вокальні арії та сценографія.'
  - Обговорення феномену «повного аншлагу» та важливості сучасної оперної режисури для залучення нової аудиторії.
  - 'Підсумкова дискусія: майбутнє української опери як частини світового культурного дозвілля (Держстандарт §3.4).'
focus: fine-arts
pedagogy: CBI
objectives:
- Learner knows the history of major Ukrainian opera houses.
- Learner can identify world-renowned Ukrainian opera singers.
- Learner uses professional terminology to evaluate operatic performances.
grammar:
- Narrative of institutional history
- Evaluative discourse on performance
phase: C1.7 [Fine Arts & High Culture]
persona:
  voice: Senior Specialist
  role: Лібретист
word_target: 4000
vocabulary_hints:
  required:
  - партитура (score) — читати партитуру, диригентська паличка; ключовий елемент роботи диригента
  - лібрето (libretto) — автор лібрето, писати лібрето; літературна основа оперної вистави
  - арія (aria) — виконувати славетну арію; сольний номер у опері
  - диригент (conductor) — головний диригент, під орудою диригента; висока частотність у мист. контексті
  - постановка (production) — прем'єрна постановка, сучасна постановка; режисерська інтерпретація
  - аншлаг (full house) — зібрати повний аншлаг; показник успіху вистави
  recommended:
  - сопрано/бас (soprano/bass) — драматичне сопрано, глибокий бас; типи голосів
  - вистава (performance/show) — оперна вистава; стилістично правильний термін замість 'спектакль'
  - музикальний (musical/talented) — музикальна дитина; про наявність хисту
  - музичний (musical/related to music) — музичний інструмент; про належність до галузі
prerequisites:
- klasychna-muzyka-3-modernizm-i-suchasnist
connects_to:
- vokalne-mystetstvo
register: літературний
activity_hints:
- type: quiz
  focus: Art terminology comprehension
  items: 12
- type: match-up
  focus: Match Соломія Крушельницька та світове визнання examples to categories
  items: 12
- type: fill-in
  focus: Complete descriptions of artistic works
  items: 10
- type: group-sort
  focus: Classify by Оксана Линів та диригентська майстерність
  items: 10
- type: reading
  focus: Analyze arts-related text
  items: 4
- type: essay-response
  focus: Write critical analysis of artistic work

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

Research **Оперне мистецтво** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Оперне мистецтво

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
