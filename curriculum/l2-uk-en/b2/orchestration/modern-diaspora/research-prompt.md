# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-080
level: B2
sequence: 80
slug: modern-diaspora
version: '2.0'
title: Сучасна діаспора
subtitle: Modern Diaspora
focus: culture
pedagogy: CBI
phase: B2.8
word_target: 4000
objectives:
- Учень розуміє роль та структуру сучасного глобального українства
- Учень може пояснити поняття м’якої сили та культурної дипломатії
- 'Учень ознайомлений з основними напрямками діяльності діаспори: лобізмом та гуманітарною допомогою'
content_outline:
- section: 'Вступ: Глобальне українство (Introduction: Global Ukrainedom)'
  words: 500
  points:
  - Визначення поняття «діаспора» та розрізнення термінів «біженці» (refugees) та «емігранти» (emigrants) у контексті подій
    після 2022 року
  - 'Огляд географії глобального українства: від традиційних центрів (Канада, США, Бразилія) до нових європейських осередків
    інтеграції'
- section: Історія та чотири хвилі еміграції (History and Four Waves of Emigration)
  words: 900
  points:
  - 'Аналіз чотирьох хвиль: трудова (кінець XIX ст.), політична (УНР), «Ді-Пі» (після 1945) та заробітчанська (1990-ті) —
    зв''язок із темами B1.4 (дієслова руху)'
  - 'Характеристика нової хвилі після повномасштабного вторгнення: соціологічний портрет та вплив на динаміку існуючих громад
    за кордоном'
- section: Організації та інституційна мережа (Organizations and Institutional Network)
  words: 800
  points:
  - Діяльність Світового Конґресу Українців (СКУ) як парасолькової організації, що об'єднує громади у понад 60 країнах світу
  - 'Роль освітніх та наукових інституцій: Український Вільний Університет у Мюнхені та мережа суботніх шкіл українознавства
    для молоді'
- section: М’яка сила та культурна дипломатія (Soft Power and Cultural Diplomacy)
  words: 700
  points:
  - 'Поняття «м''якої сили» (soft power) та лобіювання національних інтересів: приклад визнання Голодомору геноцидом у парламентах
    світу'
  - Використання безособових конструкцій на -но/-то у публіцистичних текстах про волонтерство (напр., «допомогу зібрано»,
    «рішення ухвалено», «петицію подано»)
- section: Мова діаспори та типові помилки (Language of Diaspora and Common Errors)
  words: 700
  points:
  - 'Порівняння діаспорної та материкової української: архаїзми «старої» еміграції vs неологізми сучасної інтегрованої молоді'
  - 'Корекція типових помилок: кальки з англійської у пасивному стані (напр., вживання орудного відмінка дійової особи «Книга
    написана автором» замість активного «Автор написав книгу»)'
- section: 'Практика: Аналіз та рефлексія (Practice: Analysis and Reflection)'
  words: 400
  points:
  - Критичний аналіз статті про сучасну діаспорну ініціативу з використанням публіцистичного та офіційно-ділового стилів
  - Підсумкова дискусія про роль діаспори як амбасадорів України та написання офіційного звернення до міжнародної організації
vocabulary_hints:
  required:
  - аналіз (analysis) — глибокий аналіз, проводити аналіз; ключове слово для критичного огляду діяльності організацій
  - дослідження (research) — результати дослідження, соціологічне дослідження; вказує на науковий підхід до вивчення хвиль еміграції
  - діаспора (diaspora) — українська діаспора, представники діаспори; центральне доменне слово модуля
  - синтез (synthesis) — синтез ідей, синтез культури; вживається в контексті поєднання українських та закордонних традицій
  recommended:
  - аналіз (analysis) — глибокий аналіз, проводити аналіз; ключове слово для критичного огляду діяльності організацій
  - дослідження (research) — результати дослідження, соціологічне дослідження; вказує на науковий підхід до вивчення хвиль еміграції
  - діаспора (diaspora) — українська діаспора, представники діаспори; центральне доменне слово модуля
  - синтез (synthesis) — синтез ідей, синтез культури; вживається в контексті поєднання українських та закордонних традицій
activity_hints:
- type: quiz
  focus: Identify Пасивні конструкції (-но/-то, -ний/-тий, -ся) у публіцистичному контексті in sentences
  items: 12
- type: fill-in
  focus: Complete sentences using Пасивні конструкції (-но/-то, -ний/-тий, -ся) у публіцистичному контексті
  items: 10
- type: match-up
  focus: Match Історія та чотири хвилі еміграції examples to categories
  items: 12
- type: error-correction
  focus: Find and fix errors in Пасивні конструкції (-но/-то, -ний/-тий, -ся) у публіцистичному контексті
  items: 8
- type: group-sort
  focus: Classify examples by Організації та інституційна мережа
  items: 12
- type: essay-response
  focus: Write paragraph using Пасивні конструкції (-но/-то, -ний/-тий, -ся) у публіцистичному контексті correctly
persona:
  voice: Professional Language Coach
  role: Diplomat (Дипломат)
grammar:
- Пасивні конструкції (-но/-то, -ний/-тий, -ся) у публіцистичному контексті
- Функціональні стилі (публіцистичний vs офіційно-діловий)
prerequisites:
- mystetstvo-i-literatura
connects_to:
- religion-in-ukraine
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

Research **Сучасна діаспора** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Сучасна діаспора

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
