# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-032
level: C1
sequence: 32
slug: diaspora-ukrainian
version: '2.0'
title: Українська діаспора
subtitle: 'Introduction: History and Waves of Emigration'
content_outline:
- section: 'Вступ: Історія та хвилі еміграції (Introduction: History and Waves of Emigration)'
  words: 500
  points:
  - 'Аналіз чотирьох хвиль еміграції: від перших переселенців кінця XIX ст. до масового виїзду після 2022 року.'
  - 'Причини розсіювання: політичні репресії (дипісти), економічна скрута та сучасна втеча від збройної агресії.'
  - 'Географія діаспори: формування потужних громад у Канаді, США, Бразилії та Австралії, їхній внесок у збереження державності.'
- section: Культурні інституції та ідентичність (Cultural Institutions and Identity)
  words: 800
  points:
  - Роль 'Пласту' (Plast) як хребта національного виховання молоді в екзилі та збереження структури організації.
  - 'Феномен суботніх шкіл (Saturday schools) українознавства: методика викладання мови та історії в іншомовному середовищі.'
  - Церква (УГКЦ та УПЦ) як осередок гуртування та соціальної підтримки громади, роль релігійних свят у збереженні традицій.
  - 'Культурний міст Квітки Цісик: вплив її творчості на популяризацію української пісні у світі та її повернення в Україну.'
- section: 'Мовні особливості: архаїзми та збережений стандарт (Linguistic Features: Archaisms and Preserved Standard)'
  words: 900
  points:
  - Використання архаїзмів та правопису 1928 року (Харківський правопис) як ознака тяглості традиції (напр., 'фотоґрафія',
    'кляса').
  - 'Діалектна основа діаспорної мови: вплив західноукраїнських говірок (ровер, кобіта) на мовленнєвий етикет за кордоном.'
  - Методика делікатного розрізнення діаспорного варіанта та сучасної літературної норми без стигматизації 'неправильності'.
- section: Проблеми інтерференції та Heritage Speakers (Interference Issues and Heritage Speakers)
  words: 800
  points:
  - 'Аналіз явища ''Ukish'': лексичне калькування з англійської (кара/car, трак/truck, бізи/busy) та способи очищення мовлення.'
  - 'Типові граматичні помилки heritage speakers: нейтралізація відмінкових закінчень та труднощі з категорією роду іменників.'
  - 'Мовна асиміляція та мовний зсув: виклики для другого та третього поколінь емігрантів у збереженні активного словникового
    запасу.'
- section: Сучасна діаспора та стереотипи (Modern Diaspora and Stereotypes)
  words: 600
  points:
  - 'Українці за кордоном згідно з Держстандартом (§3.9): аналіз стереотипів, соціальних проблем та питань інтеграції.'
  - 'Діалог між ''старою'' (політичною) та ''новою'' (трудовою та воєнною) еміграцією: спільні цінності та розбіжності.'
  - 'Цифрова діаспора: використання діджитал-інструментів для підтримки України та координації волонтерських рухів.'
- section: 'Практикум: Аналіз діаспорних текстів (Workshop: Analysis of Diaspora Texts)'
  words: 400
  points:
  - 'Робота з першоджерелами: порівняння мови діаспорної періодики середини XX ст. із сучасними українськими медіа.'
  - 'Дискусія про збереження національної ідентичності: баланс між успішною інтеграцією в іноземне суспільство та недопущенням
    асиміляції.'
vocabulary_hints:
  required:
  - діаспора (diaspora) — світова/українська діаспора; висока частотність у контексті зовнішньої політики
  - громада (community) — церковна/активна громада; ключовий термін для соціальної організації за кордоном
  - еміграція (emigration) — хвилі еміграції (політична, трудова, воєнна); історичний процес виїзду
  - асиміляція (assimilation) — мовна/культурна асиміляція; загроза розчинення в іншому етносі
  - ідентичність (identity) — національна ідентичність; збереження самобутності в іншомовному середовищі
  - heritage speaker (носій спадкової мови) — особа, що вивчила мову вдома, але живе в іншому мовному оточенні
  - архаїзм (archaism) — застарілі слова або граматичні конструкції, збережені діаспорою
  - збереження мови (language maintenance) — комплекс заходів для запобігання мовному зсуву
  recommended:
  - Пласт (Plast) — національна скаутська організація; символ тяглості виховання
  - суботня школа (Saturday school) — освітній заклад для вивчення українознавчих дисциплін за кордоном
  - інтерференція (interference) — мовне втручання, що призводить до появи Ukish-кальків
  - мовний зсув (language shift) — поступова заміна рідної мови мовою більшості
  - репатріація (repatriation) — процес повернення на батьківщину
  - двомовність (bilingualism) — здатність спілкуватися двома мовами; характерна риса діаспори
activity_hints:
- type: quiz
  focus: Diaspora communities and history
  items: 15+
- type: match-up
  focus: Region → language features
  items: 12+
- type: fill-in
  focus: Diaspora vocabulary
  items: 12+
- type: cloze
  focus: Heritage language characteristics
  items: 10+
- type: group-sort
  focus: Waves of emigration
  items: 12+
- type: essay-response
  focus: Heritage language maintenance
focus: linguistics
pedagogy: TTT
prerequisites:
- c1-28 (Dialects)
- 'c1-30 (Суржик: Феномен змішування)'
- 'c1-31 (Історія мови: Від Русі до сьогодення)'
connects_to:
- c1-36 (Професійні сценарії)
- c1-20 (Контрольна точка — Академічна база)
- c1-49 (Church Slavonicisms)
module_type: cultural
sources:
- name: Українська діаспора
  url: https://diasporaua.org/
  type: reference
  notes: Diaspora community information
- name: Heritage Language Studies
  url: https://mova.info/
  type: secondary
  notes: Research on diaspora language
immersion: 100% Ukrainian
phase: C1.3 [Movoznavstvo & Sociolinguistics]
objectives:
- Learner can identify and produce correct Культурні інституції та ідентичність forms
- Learner can analyze архаїзми та збережений стандарт in authentic texts
- Learner can produce written text demonstrating mastery of Історія та хвилі еміграції
persona:
  voice: Senior Specialist
  role: Представник діаспори
word_target: 4000
grammar:
- Історія та хвилі еміграції
- Культурні інституції та ідентичність
- архаїзми та збережений стандарт
- Проблеми інтерференції та Heritage Speakers
register: літературний

```

**Level constraints quick-ref:**

```
# C1 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words.`, etc.

## Grammar Scope

No grammar restrictions. Full literary Ukrainian. No sentence length limit.

## Immersion (100% Ukrainian)

Full Ukrainian immersion. All content — grammar explanations, narratives, dialogues,
cultural content, analyses, literary critiques, activity instructions, tips — in Ukrainian.

English ONLY in vocabulary table translations (YAML).

No Language Link boxes at C1 — students learned all grammar terminology by B1.

## Module Types

| Type | Modules | Focus |
|------|---------|-------|
| Academic | M01-19 | Academic foundation |
| Professional | M21-34 | Professional communication |
| Stylistics | M36-55 | Stylistics & sociolinguistics |
| Folk Culture | M56-85 | Folk culture & arts |
| Literature | M86-105 | Literary analysis |
| Checkpoint | M20,35,55,85,105,106 | Review + assessment |

> Biography content is in separate **BIO** track.

## Content-Heavy Modules (Folk/Literature M56+)

**Golden Rule:** "Can the learner answer without reading the Ukrainian text?"
- If YES → rewrite (tests content recall, not language)
- If NO → keep (tests Ukrainian comprehension)

Forbidden activity patterns: "У якому році...", "Хто був...", "Що символізує..." (without text reference)
Required patterns: "Згідно з текстом...", "У тексті модуля автор...", "Яку стилістичну функцію..."

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `C1` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Українська діаспора** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Українська діаспора

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
