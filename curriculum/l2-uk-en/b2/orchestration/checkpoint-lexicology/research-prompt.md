# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-064
level: B2
sequence: 64
slug: checkpoint-lexicology
version: '2.0'
title: 'Контрольна точка: лексикологія'
subtitle: Checkpoint — Lexicology
focus: checkpoint
pedagogy: Assessment
phase: B2.6 [Lexicology]
word_target: 4000
objectives:
- Учень успішно демонструє знання відмінювання складних числівників
- Учень вільно оперує системою синонімів на позначення дій, станів та абстрактних понять
- Учень правильно вживає ідіоми та прислів'я у відповідному контексті
- Учень будує складні синтаксичні конструкції з використанням вдосконалених сполучників
content_outline:
- section: Вступ та організація (Introduction and Organization)
  words: 400
  points:
  - 'Огляд мети контрольної точки: перевірка засвоєння тем M41-M69 (фразеологія, синоніміка, складний синтаксис) згідно з
    Держстандартом (§4.4.3, §4.3.4)'
  - 'Структура оцінювання: аналіз тексту, лексико-граматичні вправи та творче завдання; критерії оцінювання та прохідний бал'
- section: Лексична точність та стилістика (Lexical Precision and Stylistics)
  words: 900
  points:
  - 'Робота з синонімічним багатством та стилістично забарвленою лексикою: розрізнення нейтральних та експресивних засобів
    (§4.4.3)'
  - 'Виправлення типових помилок: калькування фразеологізмів (відігравати роль vs мати значення) та помилки з дієсловами (брати
    участь vs приймати участь, відчиняти двері)'
  - 'Тестування паронімів: розрізнення ''ефектний'' (вражаючий зовнішньо) vs ''ефективний'' (дієвий) та ''громадський'' vs
    ''громадянський'' у професійному контексті'
- section: 'Наука та медицина: кейс Івана Пулюя (Science and Medicine: Ivan Puliui Case)'
  words: 1100
  points:
  - 'Аналіз тексту про Івана Пулюя: інтеграція наукової (гіпотеза, експеримент) та медичної (X-промені, діагноз, скелет) термінології'
  - 'Складний синтаксис у науковому мовленні: вживання сполучників з''ясувальних та обставинних відношень (завдяки тому, що;
    незважаючи на те, що)'
  - 'Іван Пулюй як постать деколонізаційного наративу: висвітлення його внеску в науку (лампи Пулюя) та культуру (переклад
    Біблії українською)'
- section: 'Суспільство та культура: Українська діаспора (Society and Culture: Ukrainian Diaspora)'
  words: 900
  points:
  - 'Тематичний блок про українську діаспору: аналіз лексики на позначення ідентичності, збереження традицій та громадської
    активності'
  - Перевірка вміння будувати складнопідрядні речення з різними типами підрядності для опису історичних та соціокультурних
    процесів
  - Вживання абстрактних понять та термінології гуманітарного спрямування (поняття, процес, метод) у контексті світового українства
- section: Підсумок та рефлексія (Summary and Reflection)
  words: 700
  points:
  - 'Самоаналіз результатів: виявлення сильних сторін та зон для розвитку (інтерпретація результатів тесту)'
  - Рекомендації для повторення матеріалу M41-M69 та підготовка до фази B2.3 (доменна лексика та академічне письмо)
  - 'Підсумковий огляд шляху B2.1 + B2.2: перехід до поглибленої комунікації та спеціалізованих професійних тем'
vocabulary_hints:
  required:
  - аналіз (analysis) — розклад об'єкта на складові для вивчення
  - синтез (synthesis) — об'єднання частин у ціле
  - дослідження (research) — фундаментальна наукова діяльність
  - симптом (symptom) — виявляти симптоми; тривожний симптом
  - діагноз (diagnosis) — ставити/встановити діагноз; висока частотність у медицині
  - гіпотеза (hypothesis) — висунути/підтвердити/спростувати гіпотезу
  - експеримент (experiment) — проводити експеримент; чистота експерименту
  recommended:
  - аналіз (analysis) — розклад об'єкта на складові для вивчення
  - синтез (synthesis) — об'єднання частин у ціле
  - дослідження (research) — фундаментальна наукова діяльність
  - симптом (symptom) — виявляти симптоми; тривожний симптом
  - жанр (genre) — літературний або мистецький жанр (фентезі, кіно)
  - оскільки (since/as) — стилістично правильна заміна кальки 'так як'
  - ефектний (spectacular) — паронім: той, що справляє сильне зовнішнє враження
  - ефективний (effective) — паронім: той, що приносить потрібний результат
activity_hints:
- type: quiz
  focus: "Review: Review of M31-M69 grammar topics"
  items: 15
- type: fill-in
  focus: "Comprehensive: apply learned structures"
  items: 12
- type: match-up
  focus: Match concepts from covered modules
  items: 12
- type: group-sort
  focus: Classify examples by module topic
  items: 10
- type: error-correction
  focus: Find errors across all covered topics
  items: 10
- type: essay-response
  focus: Integrative writing task combining all topics
connects_to:
- b2-65 (Professional Email Basics)
prerequisites:
- b2-63 (Neologisms Borrowings)
persona:
  voice: Professional Language Coach
  role: Invigilator (Екзаменатор)
grammar:
- Review of M31-M69 grammar topics
register: академічний
immersion: 100

```

**Level constraints quick-ref:**

```
# B2 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words.`, etc.

## Grammar Scope

**Allowed:** Full grammar including adverbial participles.
Max 35 words per Ukrainian sentence. Max 6 clauses.

## Immersion (100% Ukrainian)

All content in Ukrainian. English ONLY in vocabulary table translations (YAML).
B2 learners have internalized all grammar terminology from B1 — no English scaffolding needed.

## Module Types

| Type | Modules | Pedagogy | Structure |
|------|---------|----------|-----------|
| Grammar | M01-40 | TTT | Діагностика → Аналіз → Поглиблення → Практика → Підсумок |
| Phraseology | M41-70 | CBI | Вступ → Наратив → Аналіз → Граматика в контексті → Підсумок |
| Integration | M71-83 | CBI | Same as phraseology |
| Communication | M85-93 | CBI | Same as phraseology |
| Checkpoint | M10,30,40,70,84 | — | Review + assessment |

> History content is in separate **HIST** track.

## B2-Specific Writing Notes

- No language mixing — every sentence fully Ukrainian or fully English (English only in vocab YAML)
- Fill-in blanks use `___` format (no brackets)
- Error-correction items: the `error` field marks the wrong word, `answer` is the correct replacement

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `B2` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Контрольна точка: лексикологія** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Контрольна точка: лексикологія

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
