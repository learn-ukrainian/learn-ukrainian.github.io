# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-098
level: C1
sequence: 98
slug: obrazotvorche-mystetstvo-2
version: '2.0'
title: Образотворче мистецтво II
subtitle: Visual Arts II — From Socialist Realism to Present
content_outline:
- section: 'Вступ: Мистецтво під тиском тоталітаризму (Introduction: Art Under Totalitarian Pressure)'
  words: 600
  points:
  - Аналіз канонів соцреалізму як «єдино правильного методу» та його впливу на знищення творчої індивідуальності.
  - Обговорення боротьби з «формалізмом» та репресій проти митців як засобів ідеологічного контролю.
  - Роль музеїв та виставкових залів у збереженні та реінтерпретації мистецтва під тиском (відповідно до Держстандарту §3.4).
- section: Бойчукізм та школа монументалізму (Boychuism and the School of Monumentalism)
  words: 800
  points:
  - 'Дослідження школи Михайла Бойчука: поєднання візантійських традицій, фрескового живопису та мозаїки.'
  - Чітке розмежування бойчукізму як професійної школи монументалізму та наївного мистецтва як народної традиції.
  - 'Трагедія «Розстріляного відродження»: фізичне знищення митців та їхніх монументальних робіт (фресок, панно).'
- section: Шістдесятництво та візуальний спротив Алли Горської (The Sixtiers and the Visual Resistance of Alla Horska)
  words: 900
  points:
  - 'Культурний гачок: історія знищеного вітража «Шевченко. Мати» (1964) у Київському університеті як символ безкомпромісного
    спротиву.'
  - 'Аналіз мозаїк та графіки Алли Горської: синтез народного стилю та сучасного модерну.'
  - 'Мовний фокус: використання стилістичних засобів (метафори, епітети) для опису емоційного навантаження творів спротиву
    (Держстандарт §4.4.3).'
  - 'Корекція типової помилки: вживання середнього роду — «Українське мистецтво» (не «українська»).'
- section: 'Наївне мистецтво: Марія Примаченко та Катерина Білокур (Naive Art: Maria Prymachenko and Kateryna Bilokur)'
  words: 1000
  points:
  - 'Феномен народної традиції: «чистота сприйняття» та «народний примітив» у роботах Марії Примаченко.'
  - 'Культурний гачок: порятунок картин Примаченко з палаючого музею в Іванкові (2022) як доказ живої цінності спадщини.'
  - 'Майстерність Катерини Білокур: аналіз шедеврів наївного малярства та цитата Пабло Пікассо про її світовий рівень.'
  - 'Корекція професійної лексики: диференціація «писати картину/олією» (професійний термін) проти загального «малювати».'
- section: Сучасна арт-сцена та практичне застосування (Contemporary Art Scene and Practice)
  words: 700
  points:
  - 'Сучасна українська арт-сцена: відродження інтересу до барокового Пінзеля та актуальні виставки часів війни.'
  - 'Практика: аналіз картини «Звір» Примаченко з використанням метафор та порівнянь; корекція помилки «цю картину кличуть»
    → «називають».'
  - 'Продуктивне завдання: написання критичного есе про «знищене покоління» митців та їхню роль у формуванні сучасної ідентичності.'
focus: fine-arts
pedagogy: CBI
objectives:
- Learner can evaluate the impact of Soviet repression on Ukrainian art.
- Learner can analyze the works of folk masters like Prymachenko and Bilokur.
- Learner explores the contemporary art scene in Ukraine.
grammar:
- Describing artistic style
- Narrative of resistance
phase: C1.7 [Fine Arts & High Culture]
persona:
  voice: Senior Specialist
  role: Арт-дилер
word_target: 4000
vocabulary_hints:
  required:
  - Соцреалізм (Socialist realism) — канони соцреалізму, єдино правильний метод; специфічний ідеологічний термін
  - Шістдесятники (The Sixtiers) — рух шістдесятників, київські шістдесятники; ключовий культурно-історичний контекст
  - Наївне мистецтво (Naive art) — шедеври наївного малярства, народний примітив; опис народної традиції
  - Монументалізм (Monumentalism) — школа монументалізму, бойчукісти; професійна термінологія (фрески, мозаїки)
  - Репресії (Repressions) — сталінські репресії, жертви терору; висока частотність у контексті історії мистецтва
  - Писати (to paint an art piece) — писати олією, писати з натури, майстерно написано; професійний живаписний термін
  recommended:
  - Формалізм (Formalism) — звинувачення у формалізмі; ідеологічне кліше радянської доби
  - Знищене покоління (The Executed Renaissance) — метафора для митців 1920-30-х років
  - Чистота сприйняття (Purity of perception) — часто вживається щодо наївного мистецтва
  - Меценатство (Patronage) — роль галерей та приватних колекцій у підтримці сучасного мистецтва
prerequisites:
- obrazotvorche-mystetstvo-1
connects_to:
- balet-i-tanets
register: літературний
activity_hints:
- type: quiz
  focus: Art terminology comprehension
  items: 12
- type: match-up
  focus: Match Бойчукізм та школа монументалізму examples to categories
  items: 12
- type: fill-in
  focus: Complete descriptions of artistic works
  items: 10
- type: group-sort
  focus: Classify by Шістдесятництво та візуальний спротив Алли Горської
  items: 10
- type: reading
  focus: Analyze arts-related text
  items: 4
- type: essay-response
  focus: Write critical analysis of artistic work

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

Research **Образотворче мистецтво II** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Образотворче мистецтво II

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
