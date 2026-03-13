# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-036
level: B2
sequence: 36
slug: politics-government-vocabulary
version: '2.0'
title: Політика та державне управління
subtitle: Мова влади і громадянства
focus: grammar
pedagogy: CLIL
phase: B2.4
word_target: 4000
objectives:
- Учень може розуміти новини про політичні події в Україні
- Учень може обговорювати політичні теми з використанням відповідної термінології
- Учень може розрізняти офіційний та публіцистичний стилі в політичному дискурсі
content_outline:
- section: 'Вступ: Політична система та історичне коріння (Introduction: Political System & Historical Roots)'
  words: 700
  points:
  - 'Україна як парламентсько-президентська республіка: розподіл влади на законодавчу, виконавчу та судову гілки (State Standard
    §3.7)'
  - 'Конституція Пилипа Орлика (1710) як історичний гачок: розгляд однієї з перших конституцій світу, що обмежила владу гетьмана
    та запровадила ''Генеральну Раду'''
  - 'Актуальність політичної грамотності: права та обов''язки громадянина в сучасній демократичній державі'
- section: Державні інституції та органи влади (State Institutions & Organs of Power)
  words: 900
  points:
  - 'Верховна Рада України: єдиний законодавчий орган, поняття депутатської недоторканності та архітектурний символ — амфітеатр
    сесійної зали як ознака підзвітності'
  - 'Кабінет Міністрів: структура уряду, повноваження прем''єр-міністра та функціонування міністерств у контексті державної
    політики'
  - 'Президент України: роль глави держави, право вето на закони та видання указів'
  - 'Місцеве самоврядування: реформа децентралізації, роль територіальних громад (ОТГ) та повноваження мера'
- section: Виборчий процес та демократичні механізми (Electoral Process & Democratic Mechanisms)
  words: 800
  points:
  - 'Типи виборів (президентські, парламентські, місцеві) та етапи виборчої кампанії: від реєстрації кандидата до підрахунку
    голосів'
  - 'Репрезентативна демократія: опозиція vs правляча коаліція, роль партійних фракцій та комітетів у парламенті'
  - 'Культурний контекст: референдум та плебісцит як інструменти прямої демократії в історії та сучасності України'
  - 'Нюанси лексики: відпрацювання розрізнення ''обирати'' (для виборів посадових осіб) та ''вибирати'' (загальний вибір)'
- section: Лексичні тонкощі та типові помилки (Lexical Nuances & Common Errors)
  words: 800
  points:
  - 'Корекція помилки: ''громадський'' (public/community) vs ''громадянський'' (civil/citizen-related). Приклади: громадський
    транспорт vs громадянське суспільство'
  - 'Поняття ''Політика'' (politics) vs ''Курс/Стратегія'' (policy): розрізнення загальної сфери боротьби за владу та конкретних
    планів дій уряду'
  - 'Термінологія демократії: введення словосполучень ''крихка демократія'', ''розбудова демократії'', ''верховенство закону'''
  - 'Законотворчий процес: шлях законопроекту від першого читання до ухвалення та підписання'
- section: 'Практика: Медіа та політичний дискурс (Practice: Media & Political Discourse)'
  words: 800
  points:
  - 'Аналіз політичних новин (State Standard §3.18): розрізнення нейтрального офіційно-ділового стилю та емоційного публіцистичного
    стилю'
  - 'Практичне завдання: написання коментаря або звернення до народного депутата/голови громади з використанням відповідного
    регістра'
  - 'Дискусія: обговорення суспільно-політичних подій, вираження власної позиції з використанням модальних конструкцій'
vocabulary_hints:
  required:
  - влада (power/authority) — законодавча, виконавча, судова; органи державної влади
  - закон (law) — ухвалити закон, порушити закон, згідно із законом, верховенство закону (high frequency)
  - громада (community/hromada) — територіальна громада, об’єднана територіальна громада (ОТГ); ключовий термін децентралізації
  - депутат (MP/deputy) — народний депутат, звернення депутата, депутатська недоторканність
  - громадянський (civil) — громадянські права, громадянське суспільство, громадянський обов’язок (contrast with громадський)
  - обирати (to elect) — обирати президента/депутата; термін для офіційного виборчого процесу
  recommended:
  - політика (politics/policy) — державна політика, проводити політику, внутрішня/зовнішня політика
  - громадський (public) — громадська думка, громадське місце, громадська організація
  - указ (decree) — президентський указ, видати указ
  - вето (veto) — накласти вето, право вето
  - коаліція (coalition) — правляча коаліція, утворити коаліцію
  - опозиція (opposition) — парламентська опозиція, перейти в опозицію
  - демократія (democracy) — крихка демократія, розбудова демократії
activity_hints:
- type: quiz
  focus: Identify political-terminology in sentences
  items: 12
- type: fill-in
  focus: Complete sentences using political-terminology
  items: 10
- type: match-up
  focus: Match Державні інституції та органи влади examples to categories
  items: 12
- type: error-correction
  focus: Find and fix errors in political-terminology
  items: 8
- type: group-sort
  focus: Classify examples by Виборчий процес та демократичні механізми
  items: 12
- type: essay-response
  focus: Write paragraph using political-terminology correctly
persona:
  voice: Professional Language Coach
  role: Civil Servant (Держслужбовець)
grammar:
- political-terminology
- official-register
- journalistic-register
prerequisites:
- checkpoint-register
connects_to:
- law-justice-vocabulary
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

Research **Політика та державне управління** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Політика та державне управління

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
