# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-083
level: B2
sequence: 83
slug: capstone-prezentatsiya
version: '2.0'
title: 'Capstone: Презентація'
subtitle: 'Capstone: Presentation'
focus: project
pedagogy: CBI
phase: B2.9
word_target: 4000
objectives:
- Structure a compelling presentation
- Master public speaking techniques (voice, body language)
- Create effective visual aids
content_outline:
- section: Риторична спадщина та сучасність (Rhetorical Heritage and Modernity)
  words: 600
  points:
  - 'Історичний фундамент: аналіз ''Слова про закон і благодать'' (1049) як першого зразка українського ораторського мистецтва'
  - 'Традиції Києво-Могилянської академії: вивчення ''барокового красномовства'' та мистецтва переконування XVII-XVIII ст.'
  - 'Сучасний контекст: феномен TEDxKyiv як майданчик для новітньої української риторики (приклади Я. Грицака та М. Хромих)'
- section: Структура та логіка виступу (Presentation Structure and Logic)
  words: 800
  points:
  - 'Реалізація стандарту §1.1.2.1.3: вимоги до виголошення довгих презентацій та виступів на конференціях'
  - 'Впевнений старт: подолання помилки ''вибачення на початку'' — заміна фрази ''Я трохи хвилююся'' на гачок (факти чи запитання)'
  - 'Логічне структурування: тріада ''Вступ — Основна частина — Висновок'' та її функціональне наповнення'
  - 'Мовні маркери (§4.4.1.3): використання вставних слів для signposting (по-перше, по-друге, отже, на мою думку)'
- section: Візуалізація та дизайн слайдів (Visuals and Slide Design)
  words: 700
  points:
  - 'Принципи ефективних слайдів: мінімізація тексту та використання візуалізації як опори, а не сценарію'
  - 'Корекція помилки ''читання зі слайдів'': відпрацювання зорового контакту з аудиторією замість повертання спиною до залу'
  - 'Розмежування контенту: що відображається на слайді (графіки, тези) vs. що проговорюється усно (історії, деталізація)'
- section: Майстерність публічного виступу (Public Speaking Mastery)
  words: 800
  points:
  - 'Техніка голосу та мова тіла: робота з темпом, паузами та жестикуляцією для утримання уваги аудиторії'
  - 'Боротьба зі словами-паразитами: усвідомлена пауза як альтернатива звукам ''е-е-е'', ''ну'', ''якби'' (filler words)'
  - 'Психологічна стійкість: методи управління хвилюванням та перетворення стресу на енергію виступу'
- section: Взаємодія та Q&A сесія (Interaction and Q&A Session)
  words: 700
  points:
  - 'Стратегії відповідей на запитання: кліше ''Це чудове запитання'', ''Якщо я правильно зрозумів ваше питання'' для ввічливості'
  - 'Робота зі складною аудиторією: нейтралізація критики та визнання меж своєї компетенції без втрати авторитету'
  - 'Завершення виступу: сильний фінальний висновок та заклик до дії (call to action)'
- section: Репетиція та фінальний проєкт (Rehearsal and Final Project)
  words: 400
  points:
  - 'Peer review сесія: надання та отримання конструктивного зворотного зв''язку за критеріями оцінювання'
  - 'Контрольний список (checklist): технічна перевірка обладнання, таймінгу та фінальна репетиція виступу'
vocabulary_hints:
  required:
  - презентація (presentation) — проводити презентацію, готувати презентацію, слайди презентації; High frequency
  - виступ (speech/performance) — публічний виступ, виступ перед аудиторією, готуватися до виступу; Essential generic term
  - слайд (slide) — наступний слайд, перемикати слайди, візуалізація на слайді; High frequency (tech/edu)
  - аудиторія (audience) — тримати увагу аудиторії, взаємодія з аудиторією; Medium frequency (academic)
  - аргумент (argument) — вагомий аргумент, наводити аргументи, переконливий аргумент; Crucial for B2 argumentation
  - висновок (conclusion) — робити висновки, дійти висновку, підсумовуючи; High frequency in structured speech
  recommended:
  - маркери переходів (signposting) — по-перше, по-друге, отже, переходячи до наступного; §4.4.1.3 requirement
  - слова-паразити (filler words) — позбутися слів-паразитів; register awareness
  - красномовство (eloquence) — барокове красномовство, майстерність красномовства; Cultural/academic register
  - аналіз/синтез/дослідження (analysis/synthesis/research) — проводити глибокий аналіз; Standard academic B2 terms
activity_hints:
- type: quiz
  focus: Identify Rhetorical devices in speech in sentences
  items: 12
- type: fill-in
  focus: Complete sentences using Rhetorical devices in speech
  items: 10
- type: match-up
  focus: Match Структура та логіка виступу examples to categories
  items: 12
- type: error-correction
  focus: Find and fix errors in Rhetorical devices in speech
  items: 8
- type: group-sort
  focus: Classify examples by Візуалізація та дизайн слайдів
  items: 12
- type: essay-response
  focus: Write paragraph using Rhetorical devices in speech correctly
persona:
  voice: Professional Language Coach
  role: Conference Moderator (Модератор конференції)
grammar:
- Rhetorical devices in speech
- Visual presentation structure
prerequisites:
- capstone-research
connects_to:
- b2-pidsumkovyy-ohlyad
register: нейтральний

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

Research **Capstone: Презентація** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Capstone: Презентація

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
