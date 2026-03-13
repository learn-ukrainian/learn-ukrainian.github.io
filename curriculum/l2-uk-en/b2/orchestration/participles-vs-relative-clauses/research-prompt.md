# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-009
level: B2
sequence: 9
slug: participles-vs-relative-clauses
version: '2.0'
title: Дієприкметники проти підрядних речень
subtitle: 'When to Use Який Instead'
focus: grammar
pedagogy: TTT
phase: B2.1
word_target: 4000
objectives:
- Learner can identify and apply дієприкметники проти підрядних речень
- Learner can form and use два способи вираження ознаки за дією
sources:
- name: Ukrainian State Standard 2024 - Syntax
  url: https://mon.gov.ua/
  type: reference
  notes: Relative clause formation and usage
- name: Сучасна українська літературна мова - Синтаксис
  url: https://uk.wikipedia.org/wiki/Синтаксис
  type: secondary
  notes: Syntactic structures and stylistic choices
- name: CEFR B2 Grammar Complexity
  url: https://www.coe.int/en/web/common-european-framework-reference-languages
  type: reference
  notes: B2 complex sentence requirements
content_outline:
- section: 'Вступ: Два способи вираження ознаки за дією (Introduction: Two Ways of Expressing Attribute by Action)'
  words: 500
  points:
  - Пояснення концепції дієприкметника як компактної форми проти підрядного речення як розгорнутої форми згідно зі Стандартом
    §4.1.3.1 та §4.3.4.2
  - 'Огляд стилістичного вибору: чому жива мова уникає нагромадження дієприкметників, вважаючи це ознакою бюрократичного «канцеляриту»'
- section: Морфологічний та синтаксичний еквівалент (Morphological and Syntactic Equivalent)
  words: 800
  points:
  - 'Систематичне порівняння активних форм: чому «працюючий студент» є помилкою калькування, а «студент, який працює» — нормою'
  - 'Аналіз пасивних форм: «прочитана книга» (компактність) проти «книга, яку прочитали» (нейтральність)'
  - Використання сполучних слів «який», «що», «котрий» (висока частотність «який» та «що» згідно з даними дослідження)
- section: Стилістичний вибір та культура мовлення (Stylistic Choice and Speech Culture)
  words: 900
  points:
  - 'Культурний гук: Боротьба з канцеляритом за порадами Максима Рильського та Бориса Антоненка-Давидовича щодо «оживлення»
    мови через підрядні речення'
  - 'Пріоритет агентності (Agency): Чому український синтаксис тяжіє до активних конструкцій («Ми зробили») замість пасивних
    дієприкметників («Було зроблено»)'
  - 'Сфери вживання: Академічне письмо та фіксовані терміни («чинний закон», «діючий вулкан») проти розмовної природності'
- section: Аналіз та виправлення типових помилок (Analysis and Correction of Common Errors)
  words: 900
  points:
  - 'Критична помилка: виявлення та усунення калькування активних дієприкметників на -уч/-юч (*читаючий*, *пишучий*) як маркера
    суржику'
  - 'Пастка повторення «який»: стратегії уникнення монотонності через чергування зі сполучником «що» або доречним вживанням
    дієприкметникових зворотів'
  - 'Корекція неузгодження відмінків: відпрацювання правильних форм сполучних слів (наприклад, «дівчина, яку я люблю»)'
- section: Трансформаційна практика та редагування (Transformational Practice and Editing)
  words: 900
  points:
  - 'Практикум «Літературний редактор»: перетворення сухого академічного тексту на зрозумілу публіцистику через синтаксичну
    трансформацію'
  - Вправи на збереження значення та зміну стилістичного забарвлення при переході від дієприкметника до підрядного речення
  - 'Підсумковий чек-лист: критерії вибору форми залежно від жанру тексту та вимог до природності мовлення'
vocabulary_hints:
  required:
  - який / яка / яке (which/that) — сполучне слово; дуже висока частотність; вимагає узгодження у відмінку
  - що (that) — сполучний засіб для підрядних означальних речень; часто взаємозамінний з «який» у Н. та З. відмінках
  - котрий (which/who) — книжний варіант; середня частотність; використовується при виборі або в часових конструкціях («о
    котрій годині»)
  - чинний закон (effective law) — стійке словосполучення; протиставляється помилковому «діючий закон»
  - діючий вулкан (active volcano) — приклад прийнятної термінологічної форми активного дієприкметника
  - охочий (willing/eager) — частотний прикметниковий замінник дієприкметника («охочі вчитися»)
  recommended:
  - канцелярит (officialese/bureaucratese) — термін для опису «мертвої» бюрократичної мови, перенасиченої дієприкметниками
  - агентність (agency) — мовна категорія, що підкреслює суб'єктність дії в українському синтаксисі
  - природність (naturalness) — головний критерій вибору підрядного речення в розмовному стилі
  - стилістична норма (stylistic norm) — правила вибору синтаксичних конструкцій залежно від регістра
  - еквівалентний (equivalent) — такий, що має те саме значення при зміні форми
  - суржик (surzhyk) — змішана мова; калькування дієприкметників на -уч/-юч часто є його ознакою
activity_hints:
- type: error-correction
  focus: Participles → relative clauses (and vice versa)
  items: 14+
- type: quiz
  focus: Which style is more appropriate for context?
  items: 15+
- type: error-correction
  focus: Remove unnecessary participles from text
  items: 3 texts
- type: match-up
  focus: Participle form → equivalent clause
  items: 12+
- type: group-sort
  focus: Same sentence in both forms — analyze style
  items: 10+
- type: fill-in
  focus: Complete with appropriate form (participle or clause)
  items: 12+
- type: essay-response
  focus: Rewrite academic text for general audience
  output: Model answer provided
connects_to:
- b2-10 (B2.1a Checkpoint)
- b2-18 (Multi-clause Sentences)
- 'b2-30 (Register: Literary Ukrainian)'
prerequisites:
- b2-07 (Active Participles Present)
- b2-08 (Active Participles Past)
- b2-02 (Past Passive Participles)
- Relative clause formation
persona:
  voice: Professional Language Coach
  role: Literary Editor (Літературний редактор)
module_type: grammar
immersion: 100% Ukrainian
grammar:
- Participle vs relative clause choice
- Standard Ukrainian preference for який-clauses
- Decolonization of participial calques
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

Research **Дієприкметники проти підрядних речень** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Дієприкметники проти підрядних речень

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
