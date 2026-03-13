# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-070
level: B2
sequence: 70
slug: text-analysis
version: '2.0'
title: Аналіз тексту
subtitle: Text Analysis
focus: skills
pedagogy: TTT
phase: B2.7
word_target: 4000
objectives:
- Учень вміє розрізняти факти та судження у тексті
- Учень може виявити маніпулятивні прийоми та прихований підтекст
- Учень володіє інструментами аналізу риторичних пристроїв у промовах
content_outline:
- section: 'Вступ: Навіщо аналізувати тексти (Introduction: Why Analyze Texts)'
  words: 500
  points:
  - Поняття «інформаційної гігієни» та медіаграмотності в сучасному українському дискурсі; роль проєктів «StopFake» та «Детектор
    медіа» як культурних орієнтирів.
  - Критичне мислення як інструмент захисту від інформаційного шуму та розуміння прихованого змісту, іронії й натяків (§1.2.1.1
    Стандарту).
- section: Факт проти думки (Fact vs Opinion)
  words: 700
  points:
  - Ознаки фактичних тверджень (перевіряльність, джерела) vs оціночні судження (суб'єктивність, емоційність); маркери об'єктивного
    викладу («відбулося», «за даними»).
  - 'Learner Error: калькування «опінія» (неправильно) — заміна на питомі «на мою думку» або «на мій погляд» (правильно);
    практика розрізнення в медіа-текстах.'
  - 'Аналіз причинно-наслідкових зв''язків: чому речення зі сполучником «тому що» часто є авторською інтерпретацією (судженням),
    а не голим фактом.'
- section: Виявлення упередженості та маніпуляцій (Detecting Bias and Manipulation)
  words: 800
  points:
  - 'Типи упередженості (політична, комерційна) та мовні маркери: забарвлена лексика, гіперболи та емоційні епітети (§4.4.1.2
    Стандарту).'
  - 'Маніпулятивні техніки в медіа: перекручування фактів, вибіркове використання даних та прийом «вирвати з контексту» для
    зміни змісту.'
  - 'Аналіз джерела інформації: оцінка авторитетності автора, виявлення прихованих інтересів та перевірка репутації медіа-майданчика.'
- section: Риторичні прийоми та стилістичні засоби (Rhetorical Devices and Stylistic Tools)
  words: 800
  points:
  - Етос, пафос, логос як види переконання; розрізнення терміна «пафос» як урочистої піднесеності від хибного друга перекладача
    «pathetic» (жалюгідний — неправильно).
  - 'Стилістичні засоби синтаксису (§4.4.1.3): риторичні запитання, звертання, повтори (анафора) та порівняння для посилення
    емоційного впливу.'
  - 'Культурний гачок: аналіз риторики воєнного часу на прикладі сучасних лідерів (зокрема В. Зеленського) — використання
    анафори та антитези («Ми тут. Ми захищаємо»).'
- section: Структура та логіка аргументації (Text Structure and Argumentation Logic)
  words: 700
  points:
  - Виділення головної думки та підтримуючих деталей; вживання терміна «аргумент» як доказу (правильно), а не суперечки «dispute»
    (неправильно).
  - Логічна послідовність тверджень та використання евфемізмів або уточнень для маскування чи акцентування авторської позиції.
  - Методи синтезу інформації та виявлення прихованих висновків автора через контекстуальні підказки та «читання між рядків».
- section: 'Підсумок: Практика критичного аналізу (Summary: Practice of Critical Analysis)'
  words: 500
  points:
  - 'Комплексний аналіз публіцистичного тексту: від фактчекінгу до деконструкції риторичних фігур та виявлення прихованої
    маніпуляції.'
  - Написання критичного відгуку з дотриманням об'єктивного тону (використання Passive Voice — зв'язок з M01-10) та академічної
    етики.
  - 'Зв''язок з майбутніми модулями: підготовка до фінального іспиту (M94) та поглибленого вивчення стилістики й медіа-дискурсу
    на рівні C1.'
vocabulary_hints:
  required:
  - аналіз (analysis) — глибокий аналіз, провести аналіз; висока частотність в академічному реєстрі
  - факт (fact) — історичний факт, незаперечний факт, перекручування фактів; базовий термін медіаграмотності
  - судження (judgment) — оціночне судження, висловити судження; ключове поняття для розрізнення думок від фактів
  - упередженість (bias) — політична упередженість, явна упередженість, позбутися упередженості; середня частотність
  - маніпуляція (manipulation) — маніпуляція свідомістю, прихована маніпуляція, піддаватися маніпуляції; висока частотність
    у ЗМІ
  recommended:
  - контекст (context) — вирвати з контексту, історичний контекст, культурний контекст; критично для розуміння підтексту
  - риторичне запитання (rhetorical question) — стилістичний засіб синтаксису згідно з §4.4.1.3 Стандарту
  - медіаграмотність (media literacy) — ключова навичка сучасної «інформаційної гігієни» в Україні
  - інфопростір (information space) — актуальний термін для опису середовища поширення інформації
  - епітет (epithet) — художнє означення, стилістичний засіб лексики (§4.4.1.2) для вираження авторської оцінки
activity_hints:
- type: fill-in
  focus: Complete Факт проти думки with appropriate language
  items: 10
- type: quiz
  focus: Choose the best response for each scenario
  items: 12
- type: match-up
  focus: Match situations to appropriate language
  items: 12
- type: error-correction
  focus: Fix inappropriate register in Виявлення упередженості та маніпуляцій
  items: 8
- type: fill-in
  focus: Complete professional text with correct forms
  items: 8
- type: essay-response
  focus: Produce Факт проти думки for given scenario
persona:
  voice: Professional Language Coach
  role: Literary Critic (Літературний критик)
grammar:
- Аналіз підтексту та авторської позиції
- Риторичні фігури та засоби виразності
prerequisites:
- academic-writing
connects_to:
- news-analysis-basics
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

Research **Аналіз тексту** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Аналіз тексту

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
