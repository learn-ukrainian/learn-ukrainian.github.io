# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-079
level: B2
sequence: 79
slug: mystetstvo-i-literatura
version: '2.0'
title: Мистецтво і література
subtitle: Art & Literature
focus: domain
pedagogy: CBI
phase: B2.8
word_target: 4000
objectives:
- Використовувати термінологію мистецтва та літератури
- Обговорювати літературні жанри та художні стилі
- Орієнтуватися в українському культурному просторі
content_outline:
- section: 'Розминка та вступ: Культурний ландшафт України (Warm-up & Introduction: Cultural Landscape of Ukraine)'
  words: 500
  points:
  - 'Україна як перехрестя культур: Вплив Візантії, Західної Європи та Великого Степу на формування ідентичності.'
  - 'Державний стандарт (§3.4): Огляд культурного дозвілля — відвідування музеїв, картинних галерей та філармоній як шлях
    до розуміння коду нації.'
  - 'Роль сучасного мистецтва в умовах війни: Мистецтво як засіб рефлексії, спротиву та збереження колективної пам''яті.'
- section: 'Мистецька спадщина та авангард: Від Малевича до Бойчука (Artistic Heritage & Avant-Garde: From Malevich to Boichuk)'
  words: 800
  points:
  - 'Казимир Малевич: Київське походження митця та зв''язок супрематизму з українським народним мистецтвом (розпис печей,
    орнаменти вишивки).'
  - 'Михайло Бойчук та школа бойчукістів: Концепція неовізантизму як спроба відродження монументального стилю Київської Русі.'
  - 'Трагедія Розстріляного відродження: Втрачені шедеври та вплив ідеологічного тиску на розвиток українського модернізму.'
- section: 'Народне мистецтво: Символіка та традиції (Folk Art: Symbolism & Traditions)'
  words: 700
  points:
  - 'Петриківський розпис (ЮНЕСКО): Техніка роботи пензлем з котячої шерсті («котячка») та семантика символів (калина — дівоча
    краса, дуб — сила).'
  - 'Народний іконопис: Поєднання канонічної традиції з народною естетикою та колористикою.'
  - 'Термінологічна чистота: Розрізнення понять «живопис» та «картина», використання слова «митець» замість загального «художник».'
- section: 'Літературні обрії: Від класики до сучасності (Literary Horizons: From Classics to Modernity)'
  words: 800
  points:
  - 'Золотий фонд класики: Глибинні образи у творчості Тараса Шевченка, Івана Франка та Лесі Українки.'
  - 'Еволюція жанрів: Від шістдесятників-дисидентів до постмодернізму та сучасної інтелектуальної прози (Забужко, Андрухович,
    Жадан).'
  - 'Взаємозв''язок слова та образу: Як література впливає на візуальне мистецтво та кінематограф.'
- section: 'Мистецька критика: Лексика та стилістика (Art Criticism: Vocabulary & Stylistics)'
  words: 700
  points:
  - 'Стилістичні засоби (§4.4.1.2): Практика використання епітетів та метафор (глибокий зміст, теплий колорит, сюжетна лінія)
    для аналізу творів.'
  - 'Типові помилки: Усунення кальки «присутні кольори» (вживаємо «переважають/використано») та правильний вибір дієслів для
    настрою («навіювати», «створювати» замість «викликати»).'
  - 'Уникнення тавтології: Як не писати «художник зобразив зображення», використовуючи синоніми «відтворив», «змалював», «показав».'
- section: 'Практика та підсумок: Рецензія як жанр (Practice & Summary: Review as a Genre)'
  words: 500
  points:
  - 'Аналіз форми та змісту: Складання плану мистецького розбору літературного уривку або полотна.'
  - 'Написання міні-рецензії: Використання оціночної лексики (новаторський, майстерний, цілісний) для висловлення власної
    інтерпретації.'
  - 'Кураторський підсумок: Обговорення майбутнього української культури в глобальному контексті.'
vocabulary_hints:
  required:
  - аналіз (analysis) — глибокий аналіз, критичний аналіз; ключовий термін для мистецтвознавства.
  - композиція (composition) — центр композиції, цілісна композиція; основа аналізу структури твору.
  - сюжет (plot) — розвиток сюжету, захопливий сюжет; стосується як літератури, так і наративного живопису.
  - образ (image/character) — художній образ, створити образ; центральне поняття естетики.
  - зміст (content) — ідейний зміст, розкрити зміст; часто вживається в опозиції до форми.
  - вплив (influence) — значний вплив, під впливом митця; для опису генези стилів.
  recommended:
  - митець (artist/creator) — стилістично вищий синонім до слова «художник».
  - живопис (fine art/painting) — вид образотворчого мистецтва; уникати плутанини з «малюванням».
  - колорит (coloring/color scheme) — теплий/холодний колорит; важливий епітет для опису полотен.
  - майстерність (mastery/craftsmanship) — для позитивної оцінки техніки виконання.
  - новаторство (innovation) — для опису авангардних течій та експериментів.
  - рецензія (review) — критичний розгляд твору як окремий літературний жанр.
activity_hints:
- type: quiz
  focus: Identify Literary register in sentences
  items: 12
- type: fill-in
  focus: Complete sentences using Literary register
  items: 10
- type: match-up
  focus: Match Від Малевича до Бойчука examples to categories
  items: 12
- type: error-correction
  focus: Find and fix errors in Literary register
  items: 8
- type: group-sort
  focus: Classify examples by Символіка та традиції
  items: 12
- type: essay-response
  focus: Write paragraph using Literary register correctly
persona:
  voice: Professional Language Coach
  role: Gallery Curator (Куратор галереї)
grammar:
- Literary register
- Art criticism vocabulary
prerequisites:
- nauka-i-doslidzhennia
connects_to:
- modern-diaspora
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

Research **Мистецтво і література** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Мистецтво і література

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
