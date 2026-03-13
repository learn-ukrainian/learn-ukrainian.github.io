# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c2-046
level: C2
sequence: 46
slug: terminology-acquisition-ii
version: '2.0'
title: Опанування термінології II — Побудова глосаріїв
subtitle: 'Introduction: Personal Glossary as a C2 Tool'
focus: vocabulary
pedagogy: TTT
phase: C2.3 [Professional Language]
word_target: 5000
objectives:
- Аналізувати та класифікувати явища Структура та наповнення термінологічної картки у автентичних текстах
- Продукувати тексти з коректним застосуванням Джерела та методи екстракції термінів
- Оцінювати стилістичну доречність мовних засобів у контексті Опанування термінології II — Побудова глосаріїв
- Застосовувати знання з теми «Джерела та методи екстракції термінів» у власній мовній практиці
sources:
- name: ISO 1087:2019 — Термінологія та терміни
  url: https://www.iso.org/
  type: reference
  notes: International standards for terminology and glossary creation
- name: Українське термінознавство — підручник
  url: https://ium.org.ua/
  type: reference
  notes: Academic textbook on Ukrainian terminology methodology
- name: СУМ-20 — Словник української мови
  url: https://sum20ua.com/
  type: reference
  notes: Authoritative Ukrainian dictionary for term verification
content_outline:
- section: 'Вступ: Персональний глосарій як інструмент C2 (Introduction: Personal Glossary as a C2 Tool)'
  words: 750
  points:
  - Роль персонального глосарію у професійній діяльності відповідно до §4.3.8 Держстандарту щодо вміння створювати довідково-інформаційні
    тексти
  - 'Аналіз поширеної помилки: плутанина між загальним словником та фаховим глосарієм (вузькоспеціалізованість та контекстуальність
    дефініцій)'
- section: Структура та наповнення термінологічної картки (Structure and Content of the Terminology Card)
  words: 1000
  points:
  - Обов'язкові та факультативні елементи картки (дефініція, контекст, синоніми); аналіз помилки 'циклічних дефініцій' (визначення
    терміна через однокореневі слова)
  - Практика створення чітких дефініцій та важливість фіксації джерела для подальшої верифікації та валідації терміна
- section: Джерела та методи екстракції термінів (Sources and Methods of Term Extraction)
  words: 1250
  points:
  - Екстракція професіоналізмів з фахових текстів згідно з §4.3.3 Держстандарту; робота з паралельними текстами для пошуку
    адекватних відповідників
  - Методи автоматизованої та ручної вибірки термінів; роль консультацій з фахівцями галузі для уникнення 'мертвих глосаріїв',
    що не мають практичного застосування
- section: Верифікація та деколонізація термінології (Verification and Decolonization of Terminology)
  words: 1250
  points:
  - 'Історичний контекст: діяльність Інституту української наукової мови (1921-1930) під керівництвом Агатангела Кримського
    та ''золотий вік'' термінотворення'
  - 'Аналіз радянського терміноциду 1930-х років: виявлення штучних кальок з російської та повернення до питомої української
    наукової лексики'
- section: Організація та цифрові інструменти (Organization and Digital Tools)
  words: 750
  points:
  - 'Сучасні інструменти побудови баз знань: порівняння Excel з нелінійними системами (Obsidian, Notion); класифікація за
    тематичними полями'
  - Регулярний перегляд та інтеграція глосарію в активне професійне вживання; презентація індивідуального проєкту та самооцінка
vocabulary_hints:
  required:
  - глосарій (glossary) — укладати глосарій, персональний глосарій, структура глосарія; середня частотність (академічний/IT-контекст)
  - дефініція (definition) — чітка дефініція, надати дефініцію, розширена дефініція; висока частотність у науковому дискурсі
  - верифікація (verification) — верифікація даних, процес верифікації, верифікувати термін; висока частотність
  - кодифікований (codified) — кодифікована норма, кодифікована мова, кодифікація терміна; середня частотність (лінгвістичний
    реєстр)
  - термінологічна картка (terminology card) — заповнити картку, структура картки, поля картки; низька частотність (спеціалізована
    лексика)
  recommended:
  - терміноцид (terminocide) — радянський терміноцид 1930-х років, мовна політика репресій
  - питомий (indigenous/native) — питомий український термін (на противагу калькуванню), повернення до питомих форм
  - екстракція (extraction) — екстракція термінів з тексту, автоматизована екстракція
  - валідація (validation) — валідація терміна, процес валідації, валідувати дані
  - лематизація (lemmatization) — процес лематизації, початкова форма слова
vocabulary:
  required:
  - глосарій (glossary)
  - термінологічна картка (terminology card)
  - дефініція (definition)
  - контекст (context)
  - джерело (source)
  - верифікація (verification)
  - валідація (validation)
  - колокація (collocation)
  - семантичне поле (semantic field)
  - екстракція (extraction)
  recommended:
  - лематизація (lemmatization)
  - частотність (frequency)
  - конкордансний (concordance)
  - кодифікований (codified)
  - нормативний (normative)
  forbidden: []
activity_hints:
- type: quiz
  focus: Identify target structures in context
  items: 15
- type: fill-in
  focus: Complete sentences with correct forms
  items: 12
- type: match-up
  focus: Match Структура та наповнення термінологічної картки examples to categories
  items: 12
- type: error-correction
  focus: Find and fix errors in authentic texts
  items: 10
- type: group-sort
  focus: Classify by Джерела та методи екстракції термінів
  items: 12
- type: essay-response
  focus: Produce text using target structures
activities:
  types_required:
  - match-up
  - essay-response
  - quiz
  - critical-analysis
  min_items_per_type: 6
  total_min_items: 30
  no_mirroring: true
connects_to:
- c2-49 (Reading Professional Texts I)
- c2-58 (Побудова галузевої експертизи)
- c2-60 (Професійне портфоліо I — Демонстрація компетентності)
persona:
  voice: Senior Specialist
  role: Terminologist
prerequisites:
- terminology-acquisition-i
grammar:
- Персональний глосарій як інструмент C2
- Структура та наповнення термінологічної картки
- Джерела та методи екстракції термінів
- Верифікація та деколонізація термінології
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

Research **Опанування термінології II — Побудова глосаріїв** for the **C2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Опанування термінології II — Побудова глосаріїв

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
