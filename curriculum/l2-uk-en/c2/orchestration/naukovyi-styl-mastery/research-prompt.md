# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c2-003
level: C2
sequence: 3
slug: naukovyi-styl-mastery
version: '2.0'
title: Науковий стиль — Публікаційний рівень
subtitle: 'Introduction: Academic Tradition and Standards'
focus: stylistics
pedagogy: TTT
phase: C2.1 [Stylistics & Rhetoric]
word_target: 5000
objectives:
- Аналізувати стилістичні засоби в текстах різних функціональних стилів
- Продукувати тексти із свідомим використанням стилістичних фігур
- Розрізняти авторські стилістичні прийоми та оцінювати їхню ефективність
- Застосовувати знання з теми «Вторинні тексти та анотування» у власній мовній практиці
sources:
- name: ДСТУ 8302:2015 Бібліографічне посилання
  url: https://dstu.org.ua/
  type: reference
  notes: Ukrainian citation standard for academic publications
- name: Наукова комунікація в Україні — НАН
  url: https://nbuv.gov.ua/
  type: primary
  notes: Standards for academic writing in Ukraine
- name: Ukrainian State Standard 2024 — Academic writing
  url: https://mon.gov.ua/
  type: reference
  notes: C2 requirements for scientific style
content_outline:
- section: 'Вступ: Академічна традиція та стандарти (Introduction: Academic Tradition and Standards)'
  words: 600
  points:
  - 'Державний стандарт §4.3.1.1: Вимоги до наукового стилю на рівні С2 та роль професійної комунікації'
  - 'Історичний контекст: Заснування НАН України у 1918 році П. Скоропадським та внесок В. Вернадського як фундамент традиції'
  - 'Сучасний контекст: Тиск концепції ''публікуйся або зникни'' (publish or perish) та вимоги фахових видань категорії ''А'''
- section: Мовні особливості та подолання інтерференції (Language Features and Overcoming Interference)
  words: 1000
  points:
  - 'Типова помилка: Калькування англійського ''paper'' як ''папір'' (матеріал) замість ''стаття'' або ''дослідження'''
  - 'Синтаксична норма: Обмеження пасивного стану (''було зроблено'') на користь безособових форм на -но/-то (''досліджено'',
    ''розглянуто'')'
  - 'Авторське ''ми'' vs об''єктивність: Коли доречно вживати особові форми у власних дослідженнях'
  - Термінологічна точність та уникнення суржику в академічному дискурсі
- section: Структура наукової публікації IMRAD (Structure of a Research Publication IMRAD)
  words: 900
  points:
  - Постановка проблеми та обґрунтування актуальності теми у вступній частині
  - 'Методологія дослідження: Формулювання гіпотези та опис новітніх методів верифікації даних'
  - 'Результати та обговорення: Мовні кліше для представлення емпіричних даних та порівняльного аналізу'
  - Адаптація міжнародного стандарту IMRAD до специфіки українських гуманітарних наук
- section: Вторинні тексти та анотування (Secondary Texts and Abstracting)
  words: 900
  points:
  - 'Державний стандарт §4.3.8: Створення вторинних текстів (рефератів, повідомлень, анотацій)'
  - 'Розмежування понять: ''Реферат'' як стислий огляд змісту vs ''Анотація'' як інструмент пошуку в базах даних'
  - 'Структура розширеної анотації: Мета, методи, основні результати та наукова новизна'
  - Добір ключових слів для оптимізації індексації у Scopus та Web of Science
- section: Бібліографія та етика цитування (Bibliography and Citation Ethics)
  words: 900
  points:
  - 'Війна стандартів: Традиційний ДСТУ 8302:2015 (квадратні дужки, пунктуація //) проти міжнародних стилів (APA, MLA, Harvard)'
  - 'Типова помилка: Некоректна пунктуація в бібліографічному описі (крапки, тире, скісні риски)'
  - 'Академічна доброчесність: Визначення плагіату, самоцитування та етика посилань на джерела'
  - Інструменти керування бібліографією та оформлення списку використаних джерел
- section: Рецензування та редагування (Peer Review and Editing)
  words: 700
  points:
  - 'Процедура рецензування: Сліпе (blind review) та зовнішнє рецензування в українській практиці'
  - 'Жанр наукової рецензії: Структура, етикет критики та мовні формули оцінювання'
  - 'Робота з коментарями редактора: Стратегії аргументації та внесення правок у текст'
  - 'Саморедагування: Перевірка логічної послідовності та термінологічної уніфікації'
vocabulary_hints:
  required:
  - анотація (abstract) — написати анотацію, розширена анотація; висока частотність в академічному контексті
  - методологія (methodology) — методологія дослідження, обґрунтування методології; ключовий термін для розділу методів
  - доброчесність (integrity) — академічна доброчесність, кодекс доброчесності; актуальний термін щодо етики
  - бібліографія (bibliography) — оформлення бібліографії, список літератури; стосується ДСТУ 8302:2015
  - цитування (citation) — індекс цитування, правила цитування, некоректне цитування; базовий термін публікаційного рівня
  - рецензія (review/peer review) — написати рецензію, сліпе рецензування; стосується оцінки якості статті
  - посилання (reference) — бібліографічне посилання, посилання у тексті; розрізняти з веб-посиланням
  - плагіат (plagiarism) — виявлення плагіату, боротьба з плагіатом; термін для розділу етики
  - дисертація (dissertation) — захист дисертації, автореферат дисертації; вищий рівень наукової роботи
  - гіпотеза (hypothesis) — висунути гіпотезу, підтвердити гіпотезу; основа наукового пошуку
  recommended:
  - емпіричний (empirical) — емпіричні дані, емпіричне дослідження; частотний у природничих та соціальних науках
  - верифікація (verification) — процедура верифікації, верифікація результатів; перевірка істинності
  - апробація (approbation) — апробація результатів, пройти апробацію; представлення роботи на конференціях
  - публікаційний (publication-ready) — публікаційна активність, публікаційний рівень; готовність до друку
  - імпакт-фактор (impact factor) — високий імпакт-фактор, журнал з імпакт-фактором; показник впливовості видання
  - стаття (article) — наукова стаття, фахова стаття; уникати помилкового 'папір' (paper)
vocabulary:
  required:
  - анотація (abstract)
  - гіпотеза (hypothesis)
  - методологія (methodology)
  - бібліографія (bibliography)
  - цитування (citation)
  - рецензія (review/peer review)
  - посилання (reference)
  - доброчесність (integrity)
  - плагіат (plagiarism)
  - дисертація (dissertation)
  recommended:
  - емпіричний (empirical)
  - верифікація (verification)
  - апробація (approbation)
  - публікаційний (publication-ready)
  - імпакт-фактор (impact factor)
  forbidden: []
activity_hints:
- type: quiz
  focus: Identify target structures in context
  items: 15
- type: fill-in
  focus: Complete sentences with correct forms
  items: 12
- type: match-up
  focus: Match Мовні особливості та подолання інтерференції examples to categories
  items: 12
- type: error-correction
  focus: Find and fix errors in authentic texts
  items: 10
- type: group-sort
  focus: Classify by Структура наукової публікації IMRAD
  items: 12
- type: essay-response
  focus: Produce text using target structures
activities:
  types_required:
  - quiz
  - fill-in
  - error-correction
  - critical-analysis
  - essay-response
  min_items_per_type: 6
  total_min_items: 30
  no_mirroring: true
connects_to:
- c2-10 (Transforming academic to popular)
- c2-32 (Writing literary essays uses academic conventions)
- c2-52 (Professional documents build on formal structures)
persona:
  voice: Senior Specialist
  role: Academic Publisher
prerequisites:
- milozvuchnist-complete
grammar:
- Академічна традиція та стандарти
- Мовні особливості та подолання інтерференції
- Структура наукової публікації IMRAD
- Вторинні тексти та анотування
register: академічний

```

**Level constraints quick-ref:**

```
# C2 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `5000`, `Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words.`, etc.

## Grammar Scope

No grammar restrictions. Full literary Ukrainian. Near-native mastery expected.

## Immersion (100% Ukrainian)

Everything in Ukrainian — learner operates as near-native.
English ONLY in vocabulary table translations (YAML).
Latin/Greek scholarly terms (e.g., "damnatio memoriae", "genius loci") acceptable in academic contexts.

## Module Types

| Type | Modules | Focus |
|------|---------|-------|
| Stylistics | M01-25 | Stylistic perfection (7 styles) |
| Literary | M26-40 | Literary mastery |
| Professional | M41-75 | Professional meta-skills & specialization |
| Capstone | M76-100 | Meta-skills & final capstone |
| Checkpoint | M20,25,40,55,75,100 | Review + assessment |

## C2 Activity Design

C2 uses **analytical** activity types, not drill exercises:
- **reading** — extended authentic text analysis
- **essay-response** — long-form written production
- **critical-analysis** — literary/linguistic critique
- **comparative-study** — cross-text or cross-register comparison
- **quiz** — fewer but native-level complexity
- **true-false** — nuanced claim evaluation

**Not used at C2:** fill-in, cloze, unjumble, anagram, match-up, error-correction, mark-the-words, group-sort

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `C2` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Науковий стиль — Публікаційний рівень** for the **C2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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
- **Word count**: minimum **5000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Науковий стиль — Публікаційний рівень

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
