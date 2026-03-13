# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-031
level: C1
sequence: 31
slug: history-of-language
version: '2.0'
title: 'Історія мови: Від Русі до сьогодення'
subtitle: Origins and Old East Slavic Period
content_outline:
- section: Витоки та давньоруський період (Origins and Old East Slavic Period)
  words: 600
  points:
  - 'Праслов''янська спадщина: розгляд спільних коренів та незалежного розвитку української мови від протослов''янської бази.'
  - 'Культурний гачок: Графіті Софії Київської (XI-XII ст.) як доказ живої мови — аналіз давального відмінка на -ові/-еві
    (Петрові, Павлові).'
  - 'Типова помилка: розмежування історичного терміна «руський» (Kyivan Rus'') та «російський» (Muscovite) — вправа на корекцію
    «давньоросійська мова».'
- section: Середньоукраїнська доба та Козаччина (Ruthenian Era and Cossack Period)
  words: 700
  points:
  - Формування староукраїнської (середньоукраїнської) мови в XIV-XVIII ст. та її функціонування в офіційних документах.
  - 'Культурний гачок: Пересопницьке Євангеліє (1556-1561) як символ «простої мови» та фундамент державної ідентичності.'
  - 'Взаємодія з церковнослов''янською: аналіз лексичного та граматичного впливу на високий стиль літератури.'
- section: Епоха заборон та лінгвоциду (Era of Bans and Linguicide)
  words: 800
  points:
  - Аналіз Валуєвського циркуляра (1863) та Емського указу (1876) як інструментів імперського лінгвоциду.
  - 'Мова як опір: розгляд того, як заборони стали каталізатором для інтелектуалів щодо збереження та розвитку культури.'
  - 'Термінологія репресій: опрацювання концептів «лінгвоцид», «глотоцид» та «зросійщення» через призму історичних документів.'
- section: Відродження та кодифікація (Revival and Codification)
  words: 700
  points:
  - 'Іван Котляревський та «Енеїда»: легітимізація живої народної мови як літературного стандарту.'
  - Роль Тараса Шевченка у створенні сучасної мови — аналіз фонологічних та морфологічних стандартів у його творах.
  - 'Процеси кодифікації: розвиток правописних норм та наукової термінології на зламі XIX-XX століть.'
- section: 'Радянський період: Українізація та репресії (Soviet Period: Ukrainization and Repressions)'
  words: 700
  points:
  - 'Політика коренізації 1920-х років: короткий розквіт «червоної українізації» та культурний вибух.'
  - 'Трагедія 1930-х: репресії проти мовознавців (Розстріляне відродження) та штучне наближення української до російської.'
  - 'Механізми русифікації у повоєнний час: витіснення мови з освіти, науки та офіційного вжитку.'
- section: Сучасна мовна політика (Modern Language Policy)
  words: 500
  points:
  - 'Мова як чинник нацбезпеки: аналіз Мовного закону 2019 року та його впливу на публічну сферу.'
  - 'Державний стандарт (§3.8, §4.4.1.1): розвиток функціональних стилів (науковий, публіцистичний) у сучасній державі.'
  - 'Практикум: аналіз соціолінгвістичного феномену «лагідної українізації» та зміцнення мовної ідентичності сьогодні.'
vocabulary_hints:
  required:
  - давньоруський (Old East Slavic) — давньоруська мова, спадщина; academic register, distinguish from modern Russian.
  - праслов'янський (Proto-Slavic) — праслов'янські корені, єдність; used in scientific diachronic analysis.
  - церковнослов'янський (Church Slavonic) — вплив на богослужіння, книжна мова; indicates religious/historical register.
  - лінгвоцид (linguicide) — політика лінгвоциду, жертви лінгвоциду; high frequency in historical/political texts.
  - русифікація (Russification) — тотальна русифікація, зросійщення, опір; core term for Soviet/Imperial periods.
  - українізація (Ukrainization) — політика українізації, коренізація, лагідна українізація; historical and modern context.
  - кодифікація (codification) — кодифікація норм, правописна кодифікація; linguistic register for standard setting.
  - староукраїнська мова (Ruthenian/Middle Ukrainian) — terminology for XIV-XVIII centuries development.
  recommended:
  - глотоцид (glottocide) — formal synonym for linguicide, used in academic discussions.
  - літературна мова (literary language) — modern standard language since Kotlyarevsky.
  - діахронія (diachrony) — linguistic term for historical development over time.
  - етимологія (etymology) — study of word origins, crucial for Proto-Slavic links.
  - коренізація (indigenization) — specific Soviet policy of the 1920s favoring local languages.
activity_hints:
- type: quiz
  focus: Language history timeline
  items: 15+
- type: match-up
  focus: Historical event → consequence
  items: 12+
- type: fill-in
  focus: Historical narrative completion
  items: 12+
- type: cloze
  focus: Language policy vocabulary
  items: 10+
- type: group-sort
  focus: Events by historical period
  items: 12+
- type: true-false
  focus: Ukrainian language history facts
  items: 12+
focus: history
pedagogy: CBI
prerequisites:
- c1-28 (Dialects)
- 'c1-30 (Суржик: Феномен змішування)'
connects_to:
- c1-32 (Українська діаспора)
- c1-47 (Archaic Verb Forms)
- c1-20 (Контрольна точка — Академічна база)
module_type: cultural
sources:
- name: Історія української мови
  url: https://r2u.org.ua/
  type: primary
  notes: Comprehensive language history
- name: Шевельов - Історична фонологія
  url: https://mova.info/
  type: reference
  notes: Academic linguistic history
immersion: 100% Ukrainian
phase: C1.3 [Movoznavstvo & Sociolinguistics]
objectives:
- 'Analyze the causes and consequences of історія мови: від русі до сьогодення'
- Evaluate the historical significance of давньоруський період
- Trace the development of практичне завдання
persona:
  voice: Senior Specialist
  role: Історичний лінгвіст
word_target: 4000
grammar:
- Витоки та давньоруський період
- Середньоукраїнська доба та Козаччина
- Епоха заборон та лінгвоциду
- Відродження та кодифікація
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

Research **Історія мови: Від Русі до сьогодення** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Історія мови: Від Русі до сьогодення

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
