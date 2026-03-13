# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-073
level: B2
sequence: 73
slug: presentation-skills-basics
version: '2.0'
title: 'Презентації: Основи'
subtitle: Структура та подання професійних презентацій
focus: skills
pedagogy: CBI
phase: B2.7
word_target: 4000
objectives:
- Learner can structure a professional presentation with clear opening, body, and conclusion
- Learner can use signposting language to guide the audience through presentation sections
- Learner can apply basic delivery techniques including eye contact, pacing, and volume control
- Learner can create effective visual aids for Ukrainian-language presentations
content_outline:
- section: Вступ та психологія (Introduction & Psychology)
  words: 600
  points:
  - 'Психологічна підготовка до виступу: методи подолання страху публічності через дихальні вправи та візуалізацію успішного
    результату.'
  - Визначення цільової аудиторії (target audience) та адаптація змісту презентації під професійні потреби слухачів згідно
    зі стандартом B2.
- section: Риторична спадщина та структура (Rhetorical Heritage & Structure)
  words: 800
  points:
  - 'Культурний гачок: риторична традиція Києво-Могилянської академії (Феофан Прокопович) як коріння українського публічного
    слова проти радянського бюрократичного стилю.'
  - 'Класична трискладова побудова презентації: привернення уваги у вступі, доказова основна частина та запам’ятовуваний висновок.'
  - 'Формулювання та захист основної тези презентації: перехід від загальних описів до конкретних професійних аргументів.'
- section: 'Мовна навігація: Signposting (Linguistic Navigation: Signposting)'
  words: 1000
  points:
  - 'Систематизація вступних маркерів та фраз для оголошення структури: «Сьогодні я розповім про...», «Метою мого виступу
    є...».'
  - 'Оволодіння фразами для логічних переходів між слайдами: «Це підводить нас до...», «Зупинимося детальніше на...», «Наступний
    важливий момент...».'
  - 'Використання активного стану (Agency Pass) для підкреслення авторської відповідальності: заміна «Було розглянуто» на
    «Ми розглянули / Я пропоную».'
  - 'Маркери підбиття підсумків та заклику до дії: «Отже», «Підсумовуючи сказане», «Тож я запрошую вас до...».'
- section: Візуальна культура та ідентичність (Visual Culture & Identity)
  words: 800
  points:
  - 'Принципи ефективного дизайну слайдів: правило 6x6, робота з графіками та діаграмами для візуалізації даних.'
  - 'Культурний елемент: використання сучасних українських шрифтів (наприклад, Mariupol або AlfaBravo) як засіб професійної
    самоідентифікації.'
  - 'Аналіз візуальних помилок: перевантаження слайда текстом, дрібний шрифт та невідповідність зображень змісту виступу.'
- section: Техніка виступу та робота над помилками (Delivery Technique & Error Correction)
  words: 800
  points:
  - 'Управління паралінгвістичними засобами: гучність, чіткість дикції, темп мовлення та важливість стратегічних пауз.'
  - 'Корекція типових лексичних помилок: розрізнення «власне / насправді» (замість калькованого «актуально») та «отже / тож»
    (замість «так» у значенні ''so'').'
  - Боротьба зі словами-паразитами («ну», «е-е-е», «як би») та підвищення професіоналізму мовлення через впевнену артикуляцію.
vocabulary_hints:
  required:
  - 'презентація (presentation) — High frequency; collocations: ефективна презентація, робити презентацію, слайди презентації'
  - 'виступ (speech/performance) — High frequency; collocations: публічний виступ, готувати виступ, впевнений виступ'
  - 'аудиторія (audience) — Medium frequency; collocations: увага аудиторії, контакт з аудиторією, цільова аудиторія'
  - 'теза (thesis/point) — Medium frequency; collocations: основна теза, аргументувати тезу, формулювати тези'
  - 'висновок (conclusion) — High frequency; collocations: зробити висновок, у висновку, підсумовуючи'
  recommended:
  - 'слайд (slide) — High frequency; collocations: наступний слайд, текст на слайді, перемикати слайди'
  - власне (actually/specifically) — Used to correct English-influenced errors where learners say 'actually' as 'akytualno'
  - отже (so/therefore) — Essential signposting marker to avoid English-style 'so' calques
  - підсумовуючи (summarizing) — Formal participle for transition to the conclusion phase
  - аргументувати (to argue/provide evidence) — Professional verb for the body section of a presentation
activity_hints:
- type: fill-in
  focus: Complete Риторична спадщина та структура with appropriate language
  items: 10
- type: quiz
  focus: Choose the best response for each scenario
  items: 12
- type: match-up
  focus: Match situations to appropriate language
  items: 12
- type: error-correction
  focus: Fix inappropriate register in Signposting
  items: 8
- type: fill-in
  focus: Complete professional text with correct forms
  items: 8
- type: essay-response
  focus: Produce Риторична спадщина та структура for given scenario
persona:
  voice: Professional Language Coach
  role: Sales Representative (Торговий представник)
grammar:
- Imperative mood for instructions
- Modal constructions for recommendations
register: публіцистичний
immersion: 100
prerequisites:
- news-analysis-advanced
connects_to:
- presentation-skills-advanced

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

Research **Презентації: Основи** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Презентації: Основи

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
