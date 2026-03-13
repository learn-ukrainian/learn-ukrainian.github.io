# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-022
level: C1
sequence: 22
slug: job-interview
version: '2.0'
title: 'Співбесіда: стратегії успіху'
subtitle: Introduction — Market Analysis & Preparation
content_outline:
- section: Вступ — Аналіз ринку та підготовка (Introduction — Market Analysis & Preparation)
  words: 500
  points:
  - Аналіз ринку праці (Державний стандарт §3.13) та вимог роботодавця до кваліфікації кандидата.
  - 'Дослідження компанії та підготовка портфоліо документів: правильне використання терміна «релевантний досвід».'
  - 'Психологічне налаштування на офіційно-діловий стиль спілкування: перехід від теорії до практики працевлаштування.'
- section: Етикет та культурні особливості комунікації (Etiquette & Cultural Communication)
  words: 850
  points:
  - 'Культурний гачок: Суворе дотримання звертання «Ви» в українській бізнес-культурі та етикет переходу на «ти».'
  - Дипломатичне реагування на питання про особисте життя (сімейний стан) — стратегії ввічливого окреслення професійних кордонів.
  - 'Невербальна комунікація: зоровий контакт та діловий дрес-код як складники першого враження (persona: Рекрутер).'
  - Використання безособових конструкцій («вимагається», «цінується», «очікується») для опису робочих процесів.
- section: Ефективні відповіді та метод STAR (Effective Answers & STAR Method)
  words: 1100
  points:
  - 'Презентація сильних сторін та професійних компетенцій: розрізнення «м''яких» (soft skills) та «твердих» (hard skills)
    навичок.'
  - 'Метод STAR (Ситуація, Завдання, Дія, Результат) через призму українських реалій: волонтерство та проєктна робота.'
  - 'Обґрунтування мотивації: відповідь на питання «Чому ви хочете працювати в нашій компанії?» з використанням офіційного
    стилю.'
  - Аналіз складних запитань про причини звільнення та конфліктні ситуації на попередніх місцях роботи.
- section: Мовна коректність та подолання кальок (Linguistic Correctness & Anti-Calque)
  words: 700
  points:
  - 'Learner error: Виправлення кальки «подавати на роботу» — тренінг вживання «претендувати на посаду» та «відгукнутися на
    вакансію».'
  - 'Граматичний фокус: Керування дієслів «дякувати вам» (Давальний відмінок) та «вибачте мені» замість «вибачаюсь».'
  - 'Лексичний нюанс: Розрізнення «ринок праці» vs «ринок роботи» та контекстуальне вживання слів «робота» і «праця».'
  - 'Вживання термінології: «офіційне працевлаштування», «робота за контрактом», «випробувальний термін».'
- section: Переговори про умови та укладання угод (Negotiations & Agreement)
  words: 850
  points:
  - 'Мистецтво ведення переговорів про зарплату: використання фрази «претендувати на винагороду» та обговорення очікувань.'
  - Обговорення додаткових пільг, робочого графіка та умов контракту згідно з діловими стандартами.
  - 'Завершення співбесіди та follow-up: професійна подяка за приділений час та уточнення термінів зворотного зв''язку.'
  - 'Підсумок: Симуляція співбесіди (Практичне завдання) з оцінкою за критеріями офіційно-ділового стилю.'
vocabulary_hints:
  required:
  - співбесіда (job interview) — проходити співбесіду, запросити на співбесіду, етапи співбесіди
  - роботодавець (employer) — вимоги роботодавця, потенційний роботодавець
  - претендувати (to apply/claim) — претендувати на посаду/вакансію; correction for «подавати на роботу»
  - досвід (experience) — релевантний досвід, професійний досвід, досвід роботи
  - відгукнутися (to respond/apply) — відгукнутися на вакансію (to apply for an opening)
  - випробувальний термін (probation period) — призначити випробувальний термін, успішно пройти термін
  - зарплата (salary) — очікування щодо зарплати, переговори про зарплату, гідна оплата праці
  - посада (position) — вакантна посада, претендувати на керівну посаду
  - навичка (skill) — м'які навички (soft skills), тверді навички (hard skills), ключові навички
  - дякувати (to thank) — дякувати вам/тобі (requires Dative case); usage in closing
  recommended:
  - ринок праці (labor market) — тенденції на ринку праці, сучасний ринок праці
  - переговори (negotiations) — вести переговори, успішні переговори, ділові переговори
  - компетенція (competence) — професійні компетенції, сфера компетенцій
  - працевлаштування (employment) — офіційне працевлаштування, умови працевлаштування
  - стресостійкість (stress resistance) — виявляти стресостійкість, вимога щодо стресостійкості
  - самовдосконалення (self-improvement) — прагнення до самовдосконалення
activity_hints:
- type: quiz
  focus: Interview questions and appropriate answers
  items: 15+
- type: match-up
  focus: Question → appropriate response strategy
  items: 12+
- type: fill-in
  focus: STAR method responses
  items: 12+
- type: cloze
  focus: Interview dialogue completion
  items: 10+
- type: error-correction
  focus: Fix inappropriate interview responses
  items: 10+
- type: essay-response
  focus: Self-presentation paragraph
focus: communication
pedagogy: PPP
prerequisites:
- c1-21 (CV & Resume Writing)
- Formal dialogue skills
connects_to:
- c1-23 (Business Etiquette)
- c1-24 (Digital Communication)
- c1-36 (Професійні сценарії)
module_type: skills
sources:
- name: Ukrainian HR Standards
  url: https://mon.gov.ua/
  type: reference
  notes: Professional interview practices in Ukraine
- name: STAR Method Guidelines
  url: https://careers.gov.ua/
  type: secondary
  notes: Behavioral interview techniques
immersion: 100% Ukrainian
phase: C1.2 [Professional Communication]
objectives:
- Learner can use appropriate language for Етикет та культурні особливості комунікації
- Learner can produce professional texts in the domain of Співбесіда: стратегії успіху
- Learner can evaluate and correct register in Вступ — Аналіз ринку та підготовка contexts
persona:
  voice: Senior Specialist
  role: Рекрутер
word_target: 4000
grammar:
- Вступ — Аналіз ринку та підготовка
- Етикет та культурні особливості комунікації
- Ефективні відповіді та метод STAR
- Мовна коректність та подолання кальок
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

Research **Співбесіда: стратегії успіху** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Співбесіда: стратегії успіху

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
