# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-061
level: B2
sequence: 61
slug: idioms-animals
version: '2.0'
title: 'Фразеологізми: Тварини (Вовк, Собака, Кінь, Кіт, Миша та інші)'
subtitle: 'Animal Idioms in Ukrainian'
focus: phraseology
pedagogy: CBI
phase: B2.6 [Lexicology]
word_target: 4000
objectives:
- Вивчити 8 ключових фразеологізмів про вовків, собак та коней
- Розуміти культурний контекст тваринних образів в українській мові
- Вміти вживати ці вирази у відповідних регістрах (від розмовного до книжного)
content_outline:
- section: 'Вступ: Тваринний код української культури (Introduction: Animal Code of Ukrainian Culture)'
  words: 600
  points:
  - Введення поняття «тваринного коду» як ключа до розуміння народного світогляду згідно зі стандартом §4.4.1.2 (стилістичні
    засоби лексики)
  - 'Обговорення ролі тварин у фольклорі через призму етнографа: тварини як провідники між світами та символи людських рис'
  - Аналіз подвійної природи образу (вовк як небезпека і сакральна сила, собака як відданість і приниження)
- section: 'Вовк — між демоном та захисником (The Wolf: Between Demon and Protector)'
  words: 900
  points:
  - 'Культурний гачок: дуалізм вовка в Поліському фольклорі (створений дияволом, але на службі у Бога) та роль вовка як тотема
    для козаків-характерників'
  - Детальний розбір фразеологізмів «Вовка ноги годують» та «Скільки вовка не годуй, він у ліс дивиться» як описів незмінної
    природи та потреби в активній дії
  - Аналіз виразу «Дивитися вовком» (вороже налаштованим) замість нетипового «Морити вовка голодом» для вираження емоційного
    стану
  - Вивчення образу «Вовк в овечій шкурі» як біблійної метафори лицемірства, поширеної в українській книжній традиції
- section: 'Собака: відданість, майстерність та щоденний побут (The Dog: Loyalty, Mastery, and Daily Life)'
  words: 800
  points:
  - 'Розвінчання помилкового тлумачення виразу «Собаку з''їсти»: перехід від буквального розуміння до значення «бути великим
    знавцем/майстром справи»'
  - 'Аналіз соціальних контекстів: «Як собака на сіні» (егоїзм) та «Собака гавкає — вітер несе» (ігнорування пустих слів)'
  - 'Робота з частотними колоквіалізмами: «собаче життя» та «потрібний як собаці п''ята нога» з акцентом на емоційне забарвлення
    та розмовний регістр'
- section: 'Кінь — вірний побратим та символ долі (The Horse: Faithful Brother-in-arms and Symbol of Destiny)'
  words: 900
  points:
  - 'Культурний контекст: кінь у козацькій традиції та картинах «Козак Мамай» як символ свободи та «побратим»'
  - Опрацювання виразу «Кінь ще не валявся» з попередженням про його суто розмовний регістр та недоречність у формальному
    стилі
  - Аналіз метафори долі через вираз «Долі й конем не об'їдеш» та етикетного правила «Дарованому коневі в зуби не заглядають»
  - 'Вивчення частотних образів: «бути на коні» (успіх) та «робоча конячка» (невтомна праця)'
- section: 'Практикум: Труднощі перекладу та тваринні метафори (Practicum: Translation Difficulties and Animal Metaphors)'
  words: 800
  points:
  - 'Аналіз та виправлення помилок дослівного перекладу: чому англійське «raining cats and dogs» стає українським «ллє як
    з відра» (порівняльна фразеологія)'
  - 'Вправи на вибір правильного регістра: диференціація книжних метафор (вовк в овечій шкурі) та грубо-розмовних виразів
    (собаче життя)'
  - 'Творче завдання: написання байки в ролі Етнографа («Як кажуть старі люди...»), інтегруючи вивчені фразеологізми про вовка,
    собаку та коня'
vocabulary_hints:
  required:
  - фразеологізм (idiom) — стійке сполучення слів; high frequency in literature
  - переносне значення (figurative meaning) — основа тваринної метафори
  - стилістичне забарвлення (stylistic coloring) — маркування регістра (розмовне/книжне)
  - вовчий апетит (wolfish appetite) — висока частотність; вказує на сильний голод
  - дивитися вовком (to look hostile) — частотна колоквіальна одиниця для опису ворожості
  recommended:
  - побратим (brother-in-arms) — ключовий концепт для образу коня
  - лицемірство (hypocrisy) — значення ідіоми про вовка в шкурі
  - вірний як собака (loyal as a dog) — стійке порівняння
  - робоча конячка (workhorse) — частотне метафоричне найменування людини-трудівника
activity_hints:
- type: reading
  focus: Контекстне використання
  items: 4
- type: fill-in-the-blank
  focus: Практичне застосування
  items: 10
- type: true-false
  focus: Розуміння значень
  items: 8
connects_to:
- b2-62 (Idioms Nature)
prerequisites:
- b2-60 (Idioms Somatic)
persona:
  voice: Professional Language Coach
  role: Folklore Ethnographer (Етнограф)
grammar:
- Fixed expressions
- Idiom structure and variation
register: varies

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

Research **Фразеологізми: Тварини (Вовк, Собака, Кінь, Кіт, Миша та інші)** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Фразеологізми: Тварини (Вовк, Собака, Кінь, Кіт, Миша та інші)

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
