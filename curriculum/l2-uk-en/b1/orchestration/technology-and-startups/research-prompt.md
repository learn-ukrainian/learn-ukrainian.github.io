# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-086
level: B1
sequence: 86
slug: technology-and-startups
version: '2.0'
title: Технології та стартапи
subtitle: Ukraine's Tech Industry and Startup Ecosystem
focus: culture
pedagogy: CBI
phase: B1.7 [Contemporary Ukraine]
word_target: 4000
objectives:
- Learner can discuss Ukraine's IT sector in Ukrainian
- Learner can understand authentic texts about Ukrainian tech companies
- Learner can use technology-related vocabulary in context
- Learner can compare Ukrainian tech industry with global trends
content_outline:
- section: Вступ та історія українського IT (Introduction and History of Ukrainian IT)
  words: 600
  points:
  - 'Еволюція галузі: від радянських ЕОМ (Київський інститут кібернетики) до незалежності та статусу глобального хабу аутсорсингу.'
  - 'Термінологічна база та рід іменників: правильне вживання слова «комп''ютер» (чоловічий рід) та базові поняття індустрії.'
- section: Українські єдинороги та історії успіху (Ukrainian Unicorns and Success Stories)
  words: 1000
  points:
  - 'Кейс Grammarly: історія заснування Максимом Литвином та Олексієм Шевченком у 2009 році; шлях від стартапу до статусу
    «декакорна» ($13B+).'
  - 'GitLab та Дмитро Запорожець: історія першої версії коду, написаної в Харкові, та розвиток глобальної компанії з моделлю
    all-remote.'
  - 'Ajax Systems: український лідер у виробництві систем безпеки; поєднання локального R&D центру в Києві зі світовими амбіціями.'
- section: Дія — держава в смартфоні (Diia — State in a Smartphone)
  words: 800
  points:
  - 'Цифрова трансформація України: концепція «держава у смартфоні» та світове лідерство у прирівнюванні цифрових паспортів
    до паперових (2021).'
  - 'Лексичний фокус: вживання терміна «застосунок» (mobile app) як офіційної назви замість кальки «додаток» або англіцизму
    «аплікація».'
- section: Словотворення та назви професій (Word Formation and Profession Names)
  words: 800
  points:
  - 'Дотримання Державного стандарту (§4.3.3): утворення назв діячів за допомогою суфіксів -ник (розробник, тестувальник)
    та -іст (програміст).'
  - 'Дотримання Державного стандарту (§4.3.4): утворення віддієслівних іменників для опису процесів (програмування, кодування,
    тестування).'
- section: Практика та типові помилки (Practice and Common Errors)
  words: 400
  points:
  - 'Аналіз аспектів дієслова: розрізнення тривалого процесу («писав код цілий день») та завершеного результату («написав
    новий застосунок»).'
  - 'Відмінювання запозичень: правильне вживання слова «стартап» у відмінкових формах (наприклад, місцевий відмінок: «працювати
    в стартапі»).'
- section: 'Підсумок: Технології під час війни та майбутнє (Summary: Tech during War and the Future)'
  words: 400
  points:
  - 'IT-фронт: роль волонтерських технологічних проектів, кіберзахисту та підтримки економіки України в умовах повномасштабної
    війни.'
  - 'Перспективи: Україна як інтелектуальний центр Європи та розвиток напрямків штучного інтелекту та MilTech.'
vocabulary_hints:
  required:
  - стартап (startup) — заснувати стартап, інвестувати в стартап; висока частотність у медіа
  - програміст (programmer) — працювати програмістом; утворено за допомогою суфікса -іст
  - розробник (developer) — розробник програмного забезпечення; утворено за допомогою суфікса -ник
  - застосунок (app) — мобільний застосунок; рекомендований термін замість кальки «додаток»
  - інвестиція (investment) — залучати інвестиції (to raise investment); ключове слово для бізнес-контексту
  - технологія (technology) — інноваційна технологія; базова назва галузі
  - інновація (innovation) — впроваджувати інновації; частотне слово у сфері модернізації
  recommended:
  - єдиноріг (unicorn) — український стартап-єдиноріг (компанія вартістю понад $1 млрд)
  - програмування (programming) — займатися програмуванням; віддієслівний іменник на позначення процесу
  - завантажити (to download/install) — завантажити застосунок; основна дія в контексті ПЗ
  - штучний інтелект (artificial intelligence) — розвиток штучного інтелекту; сучасний тренд
  - кіберзахист (cybersecurity) — сфера кіберзахисту; актуально в контексті IT та війни
activity_hints:
- type: reading
  focus: Tech company profiles
  items: 15
- type: match-up
  focus: Match terms to definitions
  items: 20
- type: fill-in
  focus: Complete tech descriptions
  items: 15
- type: quiz
  focus: Discuss tech trends
  items: 10
connects_to:
- b1-87 (Спорт в Україні)
prerequisites:
- b1-85 (Українське кіно та серіали)
persona:
  voice: Senior Language & Culture Specialist
  role: Startup Founder
grammar:
- Technology vocabulary
- Business and startup terminology
- Discussing trends and innovations
register: розмовний

```

**Level constraints quick-ref:**

```
# B1 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. Grammar explained IN Ukrainian. English only for disambiguation of false friends. Sentences max 30 words.`, etc.

## Grammar Scope

**Allowed:** All grammar constructions. Participles. Complex subordinate clauses.
Max 30 words per Ukrainian sentence. Max 4 clauses.

## Immersion Strategy (B1)

| Phase | Modules | Immersion | Notes |
|-------|---------|-----------|-------|
| B1.0 (Bridge) | M01-05 | Mixed | Teach grammar metalanguage; English scaffolding for abstract concepts |
| B1.1+ (Core) | M06-92 | **100%** | Full Ukrainian. English ONLY in vocabulary table translations |

**B1.0 Bridge modules:** English grammar term explanations allowed as transition from A2.

**B1.1+ Hard rule:** No English in prose, titles, callouts, or explanations.
No English in parentheses to clarify Ukrainian concepts:
- Wrong: **поки** — дія на тлі іншої дії (While she was cooking...)
- Right: **поки** — дія на тлі іншої дії, тобто одночасні процеси

## B1-Specific Writing Notes

- Content quality: equal treatment for all items in a category (same depth, same format)
- Example variety: mix standalone, table, inline, dialogue — no 5+ consecutive examples in same format
- Tables must have narrative context (2+ sentences before and after)
- Parallel sections use identical internal structure

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `B1` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Технології та стартапи** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Технології та стартапи

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
