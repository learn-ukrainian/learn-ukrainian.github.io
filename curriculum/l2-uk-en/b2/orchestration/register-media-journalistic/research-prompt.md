# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-031
level: B2
sequence: 31
slug: register-media-journalistic
version: '2.0'
title: Медійний та журналістський регістр
subtitle: Мова новин і преси
focus: grammar
pedagogy: TTT
phase: B2.3
word_target: 4000
objectives:
- Учень може розпізнавати та аналізувати стиль новинних заголовків
- Учень може структурувати лід-абзац за принципом 5W
- Учень може правильно вживати конструкції цитування та атрибуції
- Учень може виявляти маркери упередженості в медійних текстах
content_outline:
- section: 'Вступ: Публіцистичний стиль та свобода слова (Introduction: Publicistic Style and Freedom of Speech)'
  words: 600
  points:
  - Де зустрічається публіцистичний стиль (газети, ТБ, онлайн-медіа) та його головна мета — інформування та вплив (§3.18)
  - 'Культурний контекст: Георгій Гонгадзе та ''Українська правда'' як символи боротьби за свободу слова та медіа-етику'
  - 'Баланс об''єктивності та переконування в журналістському тексті: розпізнавання інформаційного спротиву на прикладі телемарафону
    ''Єдині новини'''
- section: 'Структура новинного тексту: принцип перевернутої піраміди (Structure of News Text: Inverted Pyramid Principle)'
  words: 900
  points:
  - 'Принцип ''перевернутої піраміди'' (Inverted Pyramid) як структурна метафора: від найважливішого до деталей'
  - 'Лід (Lead) — перший абзац, що відповідає на 5W: хто (who), що (what), де (where), коли (when), чому (why)'
  - Практика написання ліду для визначної події з дотриманням лаконічності та інформативності
- section: Мова заголовків та стилістичні засоби (Language of Headlines and Stylistic Devices)
  words: 800
  points:
  - 'Синтаксис заголовків: телеграфний стиль, еліпсис (пропуск дієслів) та використання теперішнього часу для драматизації
    минулих подій (''Президент підписує закон'')'
  - Використання метафор та експресивної лексики в заголовках згідно з §4.4.1.2 для привернення уваги
  - 'Пунктуація в заголовках: двокрапка для атрибуції (''Експерт: криза триватиме'') та знак питання для непідтвердженої інформації'
- section: Цитати, атрибуція та подолання типових помилок (Quotes, Attribution and Overcoming Common Errors)
  words: 900
  points:
  - 'Пряма та непряма мова (§4.3.5): правила трансформації та використання сполучників ''що'', ''щоб'', частки ''чи'''
  - 'Корекція типової помилки пунктуації: заміна англійських лапок "" та коми на українські ''ялинки'' «» та двокрапку (Він
    сказав: «...»)'
  - 'Подолання калькування та NewsSpeak: вживання правильних форм ''вживати заходів'' (замість ''приймати міри'') та ''згідно
    із законом'' (замість ''згідно закону'')'
  - 'Вибір дієслів цитування: розрізнення ''вважати/думати'' та помилкового вживання ''рахувати'' в контексті суджень'
- section: 'Медіа-етика: джерела, факти та маркери упередженості (Media Ethics: Sources, Facts and Bias Markers)'
  words: 800
  points:
  - 'Робота з джерелами інформації: використання сталого виразу ''достовірне джерело'' та конструкцій ''згідно з джерелами'',
    ''посилаючись на...'''
  - 'Розмежування ''факту'' та ''судження'': маркери суб''єктивності (''на думку'', ''ймовірно'', ''очевидно'') та розпізнавання
    забарвленої лексики'
  - 'Процедура спростування: контексти вживання слів ''вимагати спростування'' та ''опублікувати офіційне спростування'' при
    виявленні дезінформації'
vocabulary_hints:
  required:
  - джерело (source) — достовірне джерело, посилатися на джерело; надзвичайно висока частотність у медіа-регістрі
  - офіційний (official) — офіційне повідомлення, офіційна заява, офіційний представник
  - спростування (refutation/disclaimer) — вимагати спростування, опублікувати спростування
  - наживо (live) — в ефірі наживо, транслювати наживо, включення наживо
  - подія (event) — визначна подія, перебіг подій, висвітлювати подію
  recommended:
  - аналіз (analysis) — системний підхід до вивчення медіа-тексту
  - синтез (synthesis) — поєднання інформації з різних джерел
  - дослідження (research) — журналістське розслідування
  - упередженість (bias) — маркер суб'єктивного висвітлення подій
  - атрибуція (attribution) — вказівка на автора висловлювання або джерело цитати
activity_hints:
- type: quiz
  focus: Identify News headline syntax (telegram style) in sentences
  items: 12
- type: fill-in
  focus: Complete sentences using News headline syntax (telegram style)
  items: 10
- type: match-up
  focus: Match принцип перевернутої піраміди examples to categories
  items: 12
- type: error-correction
  focus: Find and fix errors in News headline syntax (telegram style)
  items: 8
- type: group-sort
  focus: Classify examples by Мова заголовків та стилістичні засоби
  items: 12
- type: essay-response
  focus: Write paragraph using News headline syntax (telegram style) correctly
persona:
  voice: Professional Language Coach
  role: Editor-in-Chief (Головний редактор)
grammar:
- News headline syntax (telegram style)
- Lead paragraph structure (5W)
- Attribution and quoting conventions
- Bias markers and objectivity
prerequisites:
- register-literary-ukrainian
connects_to:
- register-colloquial-style
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

Research **Медійний та журналістський регістр** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Медійний та журналістський регістр

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
