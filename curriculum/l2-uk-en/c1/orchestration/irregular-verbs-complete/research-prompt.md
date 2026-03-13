# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-017
level: C1
sequence: 17
slug: irregular-verbs-complete
version: '2.0'
title: Неправильні дієслова — повний огляд
subtitle: 'Introduction: Etymology and Systematics'
content_outline:
- section: 'Вступ: Етимологія та системність (Introduction: Etymology and Systematics)'
  words: 500
  points:
  - 'Історичні причини нерегулярностей: від давньоруської мови до сучасної морфонології'
  - 'Культурний гачок: Філософська вага дієслова «бути» (Hamlet: «Бути чи не бути»)
    у перекладах Г. Кочура та М. Рильського'
  - 'Класифікація: розмежування передбачуваних чергувань та справжніх суплетивних
    основ'
- section: Унікальні парадигми та державний стандарт (Unique Paradigms and State Standard)
  words: 700
  points:
  - 'Дотримання стандарту §4.1.3.1: Повне відмінювання «дати» та «їсти» у майбутньому
    та теперішньому часі (дам, даси, дасть... їм, їси, їсть...)'
  - 'Типова помилка: надмірна регуляризація дієслів «дати» та «їсти» (заміна «дам/їм»
    на помилкові *даю*, *їю*)'
  - 'Продуктивність префіксальних похідних: аналіз дієслів «віддати», «подати», «продати»,
    що зберігають нерегулярність кореня'
- section: Чергування голосних та приголосних (Vowel and Consonant Alternations)
  words: 700
  points:
  - 'Морфологія §4.2: Аналіз чергувань у дієсловах «писати» (пишу), «мити» (мию) та
    «брати» (беру)'
  - 'Помилка учня: плутанина основ у дієслові «брати» (вживання *браю* замість «беру»)
    через ігнорування випадного голосного'
  - 'Консонантні мутації: акцент на переході «д» -> «дж» у дієслові «ходити» (ходжу)
    для запобігання типовим помилкам'
- section: Суплетивні основи та дієслово «бути» (Suppletive Stems and the Verb 'to
    be')
  words: 600
  points:
  - 'Функціонування дієслова «бути» як найчастотнішої одиниці (Top 10): форми «є»,
    «був», «буду»'
  - 'Суплетивізм у дієсловах руху: історичний зв''язок основ «іти» (теперішній час)
    та «ішов» (минулий час)'
  - 'Частотний аналіз: чому найбільш вживані дієслова («бути», «йти») залишаються
    нерегулярними в процесі розвитку мови'
- section: Дієслова руху та їх відмінювання (Motion Verbs and Their Conjugation)
  words: 600
  points:
  - Відмінності в парадигмах однонаправлених («йти», «нести», «їхати») та різноспрямованих
    («ходити», «носити», «їздити») дієслів
  - 'Помилка учня: плутанина між формами майбутнього часу (йтиму — рідше, піду — частіше
    vs ходитиму)'
  - 'Фразеологічні вислови: «йти на компроміс», «час біжить», «йти стрімголов» як
    приклади контекстного вживання'
- section: Культурний контекст та народна мудрість (Cultural Context and Folk Wisdom)
  words: 450
  points:
  - 'Ритуали гостинності: роль дієслів «їсти» та «дати» у традиції частування («дати
    хліб-сіль», «скуштувати»)'
  - 'Пареміологія як мнемотехніка: аналіз прислів''я «Дають — бери, б''ють — тікай»
    для засвоєння наказового способу та відмінювання'
  - 'Символізм їжі: розбір фразеологізмів «їсти очима», «з''їсти пуд солі» у художніх
    текстах'
- section: Практика та синтез (Practice and Synthesis)
  words: 450
  points:
  - 'Тренування мінімальних пар: корекція помилкових форм через порівняння з правильними
    парадигмами §4.1.3'
  - 'Контекстне використання в академічному письмі: вибір точних дієслів («брати до
    уваги», «брати гору»)'
  - 'Підсумковий аналіз: створення власної мапи чергувань для системного розуміння
    неправильних дієслів'
vocabulary_hints:
  required:
  - бути (to be) — бути чи не бути, як це може бути; Top 10 найчастотніших слів
  - йти (to go) — йде дощ, йти на компроміс, час йде; Top 50, суплетивна основа
  - дати (to give) — дати слово, дати спокій, дати знати; Top 100, архаїчне відмінювання
  - їсти (to eat) — їсти очима, просити їсти, з'їсти пуд солі; унікальна парадигма
  - брати (to take) — брати участь, брати до уваги, брати гору; чергування а/е
  - бігти (to run) — час біжить, бігти стрімголов; чергування г/ж
  - чергування (alternation) — фонологічна зміна звуків у корені
  - суплетивний (suppletive) — утворення форм від різних основ
  recommended:
  - морфонологія (morphonology) — розділ мовознавства на межі морфології та фонології
  - непродуктивний (unproductive) — тип відмінювання, що не поширюється на нові слова
  - парадигма (paradigm) — сукупність усіх граматичних форм слова
  - відмінювання (conjugation) — зміна дієслів за особами, числами та часами
activity_hints:
- type: fill-in
  focus: Conjugate irregular verbs
  items: 20+
- type: match-up
  focus: Infinitive to conjugated form
  items: 15+
- type: quiz
  focus: Identify correct form in context
  items: 15+
- type: group-sort
  focus: Classify verbs by alternation type
  items: 15+
- type: cloze
  focus: Complete text with verb forms
  items: 12+
- type: error-correction
  focus: Fix incorrect verb forms
  items: 10+
focus: grammar
pedagogy: TTT
prerequisites:
- B2 verb conjugation basics
- Aspect pairs understanding
connects_to:
- c1-18 (Essay Writing Practice)
- c1-47 (Archaic Verb Forms)
- c1-20 (C1.1 Checkpoint)
module_type: grammar
sources:
- name: Морфологія української мови
  url: https://r2u.org.ua/
  type: reference
  notes: Complete verb morphology reference
- name: Ukrainian Verb Conjugation Patterns
  url: https://mova.info/
  type: secondary
  notes: Irregular verb patterns and alternations
immersion: 100% Ukrainian
phase: C1.1 [Academic Writing & Research]
objectives:
- Learner can identify and produce correct Унікальні парадигми та державний стандарт forms
- Learner can analyze Чергування голосних та приголосних in authentic texts
- Learner can produce written text demonstrating mastery of Етимологія та системність
persona:
  voice: Senior Specialist
  role: Лінгвіст-архіваріус
word_target: 4000
grammar:
- Етимологія та системність
- Унікальні парадигми та державний стандарт
- Чергування голосних та приголосних
- Суплетивні основи та дієслово «бути»
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

Research **Неправильні дієслова — повний огляд** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Неправильні дієслова — повний огляд

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
