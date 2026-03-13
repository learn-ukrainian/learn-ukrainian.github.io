# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-067
slug: checkpoint-c1-5
level: C1
sequence: 67
phase: C1.5 [Stylistics & Rhetoric]
version: '1.0'
title: 'Контрольна точка: Стилістика і регістри'
subtitle: 'Checkpoint: Stylistics and Registers'
focus: checkpoint
pedagogy: Assessment
objectives:
- Assessment of ability to identify and use different language registers
- Assessment of politeness strategies application
- Assessment of slang and idiom comprehension
content_outline:
- section: 'Вступ: Стиль як генетичний код нації (Introduction: Style as a Nation''s Genetic Code)'
  words: 400
  points:
  - 'Вступне слово від імені Редактора стилю: концепція мови як генетичного коду нації за Ліною Костенко'
  - 'Роль стилістичної вправності на рівні C1: від простої комунікації до маркування ідентичності та професіоналізму'
- section: Палітра функціональних стилів за Державним стандартом (The Palette of Functional Styles per State Standard)
  words: 1000
  points:
  - 'Огляд семи стилів за §4.4.1.1: розмовний, офіційний, науковий, публіцистичний, художній, релігійний, епістолярний'
  - 'Практикум редактора: ідентифікація стилів у змішаних текстах та перевірка засвоєння стилістичних засобів (§4.4.3)'
  - Аналіз художніх тропів та лексичного багатства (епітети, метафори) як ознаки високого стилю
- section: 'Мистецтво редагування: Боротьба з канцеляритом та калькою (The Art of Editing: Fighting Chancery and Calques)'
  words: 1000
  points:
  - Виявлення та корекція 'сухого канцеляриту' в побутовому мовленні (заміна 'дане питання' на 'це питання')
  - Трансформація пасивних синтаксичних конструкцій в активні за українським зразком (напр., 'ми вирішили' замість 'було вирішено
    нами')
  - Викорінення суржику та калькованих англіцизмів у синтаксисі для відновлення природного звучання фрази
- section: Регістри та стратегії ввічливості (Registers and Politeness Strategies)
  words: 800
  points:
  - 'Перемикання між високим та низьким регістрами: ситуативні завдання на відповідність контексту'
  - 'Етикетні формули відмови: порівняння офіційного листа-відмови та дружнього ''ні'' без порушення стосунків'
  - 'Аналіз типових помилок: використання сленгу в офіційному листуванні та методи їх швидкої корекції'
- section: Синонімічне багатство та закон милозвучності (Synonym Richness and the Law of Euphony)
  words: 800
  points:
  - Вправа на розширення синонімічних рядів для дієслів руху (йти, крокувати, теліпатися, чалапати) для передачі тонких відтінків
  - 'Застосування закону милозвучності: чергування у/в, і/й/та як фінальний штрих стилістичного редагування'
  - 'Підсумок: стилістичний аналіз як підготовка до вивчення народної культури та літератури'
vocabulary:
  required: '[]'
  recommended: '[]'
  forbidden: '[]'
persona:
  voice: Senior Specialist
  role: Редактор стилю
word_target: 4000
vocabulary_hints:
  required:
  - стиль (style) — функціональний стиль, високий стиль, змішування стилів; базова категорія §4.4.1.1
  - реєстр (register) — високий/низький реєстр, перемикання регістрів; частотний термін для C1
  - канцеляризм (chancery/bureaucratic word) — уникати канцеляризмів, сухий канцеляризм; маркер мовного сміття
  - суржик (surzhyk) — викорінювати суржик, побутовий суржик; соціально-мовне явище
  recommended:
  - тропи (tropes) — художні тропи, багатство тропів; лексичні засоби за §4.4.3
  - милозвучність (euphony) — закон милозвучності, чергування у/в; фоно-стилістична норма
  - калькування (calquing) — калькування синтаксису, уникати кальок; типова помилка перекладу
  - синонімічний ряд (synonymic series) — розгалужений ряд, багатство синонімів; інструмент точності
prerequisites:
- review-c1-5
connects_to:
- kobzari-bandura
grammar:
- Стиль як генетичний код нації
- Палітра функціональних стилів за Державним стандартом
- Боротьба з канцеляритом та калькою
- Регістри та стратегії ввічливості
register: літературний
activity_hints:
- type: quiz
  focus: Comprehensive review
  items: 15
- type: fill-in
  focus: Apply learned structures
  items: 12
- type: match-up
  focus: Match Палітра функціональних стилів за Державним стандартом examples to categories
  items: 12
- type: group-sort
  focus: Classify by Боротьба з канцеляритом та калькою
  items: 10
- type: error-correction
  focus: Cross-module error detection
  items: 10
- type: essay-response
  focus: Integrative writing task

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

Research **Контрольна точка: Стилістика і регістри** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Контрольна точка: Стилістика і регістри

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
