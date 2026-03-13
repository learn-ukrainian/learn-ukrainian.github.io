# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-012
level: C1
sequence: 12
slug: research-article
version: '2.0'
title: Жанр — Наукова стаття
subtitle: Introduction
content_outline:
- section: Вступ (Introduction)
  words: 600
  points:
  - Визначення жанру наукової статті згідно зі стандартом (§4.4.1.1) та його фундаментальна
    відмінність від суб'єктивного есе (essay vs research article)
  - Вимоги МОН України до фахових видань (Категорії А та Б) та роль НБУВ ім. Вернадського
    як головного центру наукової інформації
  - 'Культурний контекст: Іван Пулюй як приклад вченого світового рівня, чиї статті
    та листи заклали фундамент сучасної рентгенології'
- section: Структура IMRaD (IMRaD Structure)
  words: 1000
  points:
  - 'Логіка побудови статті за принципом «пісочного годинника»: від широкого контексту
    актуальності до вузьких методів і назад до глобальних імплікацій'
  - 'Розділ Introduction: обґрунтування актуальності теми, визначення об’єкта, предмета
    дослідження та формулювання наукового апарату'
  - 'Розділи Methods та Results: точність опису емпіричного дослідження, методологія
    та візуалізація виявлених закономірностей без вживання Я-конструкцій'
  - 'Розділ Discussion: інтерпретація результатів у контексті традицій українських
    наукових шкіл та університетських «Вісників»'
- section: Анотація та ключові слова (Abstract and Keywords)
  words: 800
  points:
  - 'Типова помилка: розмежування понять «анотація» та хибного друга перекладача «абстракт»
    (Correct: анотація — короткий виклад змісту)'
  - 'Структура розширеної анотації згідно з вимогами: мета, методологія, основні результати
    та висновки'
  - Формулювання інформативної назви та стратегічний вибір ключових слів для оптимізації
    статті у міжнародних наукометричних базах
- section: Мова та стиль наукового тексту (Academic Style and Language)
  words: 800
  points:
  - 'Безособовий стиль викладу (§4.4.5): заміна «Я вважаю» на академічні звороти «У
    статті проаналізовано», «Встановлено», «Доведено»'
  - 'Уникнення термінологічних кальок: правильне вживання термінів (напр. вживання
    «стаття/робота» замість калькованого «папір» для англ. paper)'
  - Типові фрази-маркери та мовні кліше для кожного розділу IMRaD, що забезпечують
    логічну зв'язність наукового тексту
- section: Висновки та оформлення джерел (Conclusions and References)
  words: 800
  points:
  - 'Формулювання основних висновків: узагальнення результатів, їхні практичні імплікації
    та окреслення перспектив подальших розробок'
  - Оформлення списку літератури згідно з ДСТУ 8302:2015 та дотримання академічної
    доброчесності при цитуванні (Building on c1-11)
  - 'Практика критичного аналізу: ідентифікація структурних елементів у зразках статей
    з провідних українських фахових видань'
vocabulary_hints:
  required:
  - стаття (article) — наукова стаття, фахове видання, опублікувати статтю; висока
    частотність
  - анотація (abstract) — написати анотацію, структура анотації, розширена анотація;
    уникнення помилки «абстракт»
  - дослідження (research) — емпіричне дослідження, методи дослідження, об’єкт і предмет
    дослідження
  - висновки (conclusions) — зробити висновки, дійти висновку, основні висновки
  - актуальність (relevance) — актуальність теми, обґрунтування актуальності; ключовий
    елемент вступу
  - методологія (methodology) — методологія дослідження, науковий апарат
  - результати (results) — отримані результати, виявлені закономірності
  - обговорення (discussion) — інтерпретація результатів, наукова дискусія
  - ключові слова (keywords) — вибір ключових слів, оптимізація для пошуку
  - література (references) — список використаних джерел, цитування, ДСТУ 8302:2015
  recommended:
  - публікація (publication) — підготувати публікацію, фахова публікація
  - рецензування (peer review) — рецензування статті, відгук рецензента
  - редакція (editorial board) — редакційна колегія, рішення редакції
  - фахове видання (professional journal) — видання категорії А або Б
  - імпакт-фактор (impact factor) — показник впливовості видання
  - науковий стиль (academic style) — дотримання норм наукового стилю (§4.4.1.1)
  - калька (calque) — уникнення термінологічних кальок з англійської мови
activity_hints:
- type: group-sort
  focus: Arrange article sections in order
  items: 12+
- type: match-up
  focus: Section to content type
  items: 15+
- type: cloze
  focus: Article section phrases
  items: 12+
- type: quiz
  focus: Identify IMRaD elements in excerpts
  items: 12+
- type: essay-response
  focus: Write abstract for given research
- type: fill-in
  focus: Match typical phrases to sections
  items: 12+
focus: grammar
pedagogy: TTT
prerequisites:
- c1-08 to c1-11 (Essay and Citation skills)
- Academic style markers
connects_to:
- c1-13 (Abstract Writing)
- c1-14 (Literature Review)
- c1-19 (Article Critique)
module_type: grammar
sources:
- name: Вимоги до наукових публікацій
  url: https://mon.gov.ua/
  type: reference
  notes: Official requirements for Ukrainian academic articles
- name: IMRaD Structure Guidelines
  url: https://mova.info/
  type: secondary
  notes: International research article structure
immersion: 100% Ukrainian
phase: C1.1 [Academic Writing & Research]
objectives:
- Learner can identify and produce correct Структура IMRaD forms
- Learner can analyze Анотація та ключові слова in authentic texts
- Learner can produce written text demonstrating mastery of Вступ
persona:
  voice: Senior Specialist
  role: Головний науковий співробітник
word_target: 4000
grammar:
- Вступ
- Структура IMRaD
- Анотація та ключові слова
- Мова та стиль наукового тексту
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

Research **Жанр — Наукова стаття** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Жанр — Наукова стаття

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
