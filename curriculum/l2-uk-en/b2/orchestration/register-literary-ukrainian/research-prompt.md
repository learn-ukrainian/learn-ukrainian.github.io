# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-030
level: B2
sequence: 30
slug: register-literary-ukrainian
version: '2.0'
title: Регістр — Літературна українська
subtitle: Мова художньої літератури
focus: grammar
pedagogy: TTT
phase: B2.3
word_target: 4000
objectives:
- Учень може розпізнавати характерні ознаки літературного стилю
- Учень може аналізувати стилістичні засоби в художніх текстах
- Учень може трансформувати нейтральний текст у літературний стиль
content_outline:
- section: 'Вступ: Поняття художнього стилю (Introduction: Concept of Literary Style)'
  words: 600
  points:
  - 'Де зустрічається (проза, поезія, драматургія, есеїстика) та головна мета — естетичний вплив та емоційна образність через
    використання метамови: аналіз, синтез, процес'
  - 'Авторська індивідуальність vs стандартизація інших регістрів: як стиль письменника формує унікальне сприйняття художнього
    світу'
  - Визначення літературознавчих термінів та понять як інструментарію для дослідження та інтерпретації тексту
- section: Історичні витоки та зачинателі (Historical Origins and Pioneers)
  words: 800
  points:
  - 'Іван Котляревський та ''Енеїда'' (1798): революційне поєднання високого класичного сюжету з живою народною мовою (бурлеск)
    як фундамент сучасної літературної мови'
  - 'Тарас Шевченко та ''Кобзар'': остаточне утвердження літературного стандарту через синтез книжної традиції, фольклору
    та живої говірки'
  - Майстерність Шевченка у використанні кличного відмінка для персоніфікації абстрактних понять та явищ («Думи мої!», «Україно!»)
- section: Лексичні засоби та конотації (Lexical Means and Connotations)
  words: 900
  points:
  - Архаїзми та історизми для створення історичного колориту та піднесеності (отож, воістину, мовив, чоло, десниця)
  - Поетична лексика та поетизми (гай, криниця, обрій, зоря) та їх функція у створенні ліричного настрою
  - 'Аналіз та запобігання помилці стилістичного дисонансу: чому канцеляризм ''сонце здійснило захід'' руйнує художність на
    відміну від ''сонце сіло за обрій'''
  - Діалектизми як засіб мовної характеристики персонажів та надання тексту автентичності
- section: Тропи, фігури та персоніфікація (Tropes, Figures, and Personification)
  words: 900
  points:
  - Метафора, метонімія та епітети як ключові засоби створення образу (серце каменіє, срібний місяць, перо Шевченка)
  - 'Персоніфікація та роль кличного відмінка: виправлення типової помилки ігнорування вокатива (правильно: ''О, ноче!'',
    а не ''О, ніч!'')'
  - 'Гіпербола та літота: емоційне масштабування як метод посилення художньої виразності тексту'
- section: Синтаксис та запобігання помилкам (Syntax and Error Prevention)
  words: 800
  points:
  - Стилістична інверсія — зміна порядку слів для логічного акценту та створення особливого ритму ('прийшла весна красна')
  - Риторичні фігури (запитання, оклики) та синтаксичні повтори (анафори) для динамізації розповіді
  - 'Корекція калькованих конструкцій під впливом іноземних мов: вживання ''брати участь у виставі'' замість помилкового ''приймати
    участь'''
  - 'Практичне застосування: трансформація нейтрального повідомлення про подію у художній опис із використанням фігур та тропів'
vocabulary_hints:
  required:
  - аналіз (analysis) — стилістичний аналіз, глибокий аналіз твору; дія по розбору художніх засобів
  - синтез (synthesis) — гармонійний синтез, синтез мистецтв; поєднання елементів у цілісний образ
  - дослідження (research) — літературне дослідження, результати дослідження; науковий підхід до тексту
  recommended:
  - аналіз (analysis) — стилістичний аналіз, глибокий аналіз твору; дія по розбору художніх засобів
  - синтез (synthesis) — гармонійний синтез, синтез мистецтв; поєднання елементів у цілісний образ
  - дослідження (research) — літературне дослідження, результати дослідження; науковий підхід до тексту
activity_hints:
- type: quiz
  focus: Identify literary-register in sentences
  items: 12
- type: fill-in
  focus: Complete sentences using literary-register
  items: 10
- type: match-up
  focus: Match Історичні витоки та зачинателі examples to categories
  items: 12
- type: error-correction
  focus: Find and fix errors in literary-register
  items: 8
- type: group-sort
  focus: Classify examples by Лексичні засоби та конотації
  items: 12
- type: essay-response
  focus: Write paragraph using literary-register correctly
persona:
  voice: Professional Language Coach
  role: Novelist (Письменник-романіст)
grammar:
- literary-register
- figurative-language
- archaic-vocabulary
- inverted-word-order
prerequisites:
- register-official-legal
connects_to:
- register-media-journalistic
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

Research **Регістр — Літературна українська** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Регістр — Літературна українська

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
