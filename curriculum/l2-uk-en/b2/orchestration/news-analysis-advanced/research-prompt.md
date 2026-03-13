# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-072
level: B2
sequence: 72
slug: news-analysis-advanced
version: '2.0'
title: 'Аналіз новин: Поглиблено'
subtitle: Advanced media literacy and critical news analysis
pedagogy: CBI
phase: B2.7
word_target: 4000
objectives:
- Learner can identify editorial bias and political perspectives in news coverage
- Learner can compare how different sources cover the same event
- Learner can recognize propaganda techniques and rhetorical manipulation
- Learner can evaluate source credibility and verify information
- Learner can analyze framing, tone, and linguistic choices in journalism
content_outline:
- section: Розминка та критичний вступ (Warm-up and Critical Introduction)
  words: 600
  points:
  - Перехід від вивчення структури новин (М89) до глибокого деконструктивного аналізу змісту в умовах інформаційної війни
  - 'Українські медіа в глобальному контексті: Реформа Суспільного (НСТУ) 2017 року як крок до незалежної журналістики та
    роль наглядової ради'
  - 'Обговорення новин та відгуків про них згідно зі стандартом B2 (§3.18, §1.1.2.2.2): фокус на інтенції аргументованої дискусії'
- section: Упередженість та редакційна політика (Bias and Editorial Policy)
  words: 800
  points:
  - 'Аналіз типів упередженості: вибіркове висвітлення (selection bias), фреймінг (framing) та замовчування фактів (omission)'
  - 'Український медіа-феномен «джинса»: розпізнавання прихованої реклами та політичного замовлення під виглядом новин'
  - 'Порівняльний аналіз редакційної політики: як власники медіа-холдингів впливають на інтерпретацію подій'
  - Розмежування понять «факт» та «судження» (fact vs opinion) у новинному тексті
- section: Пропаганда та емоційні маніпуляції (Propaganda and Emotional Manipulation)
  words: 900
  points:
  - 'Техніки пропаганди: демонізація опонента, whataboutism як спосіб відвернення уваги та гіперболізація загроз'
  - 'Емоційна лексика як маркер маніпуляції: апеляція до страху, гніву та штучного патріотизму для зниження критичного порогу'
  - 'Механіка дезінформації: аналіз методів створення фейків на прикладі російської пропаганди про Україну (без ретрансляції
    самих фейків)'
- section: Верифікація та фактчекінг (Verification and Fact-checking)
  words: 900
  points:
  - 'Методологія верифікації: застосування CRAAP-тесту (Currency, Relevance, Authority, Accuracy, Purpose) для оцінки надійності
    медіа'
  - 'Феномен StopFake (2014): історія проєкту Могилянської школи журналістики та його світове значення у боротьбі з дезінформацією'
  - 'Практичні інструменти: ресурси VoxCheck, зворотний пошук зображень та правило перехресної перевірки (мінімум три незалежні
    джерела)'
- section: Мовний аналіз та типові помилки (Linguistic Analysis and Common Errors)
  words: 800
  points:
  - 'Фреймінг через граматику: активний vs пасивний стан для приховування або підкреслення відповідальності суб''єкта дії'
  - 'Корекція типових лексичних помилок: калькування «гарячі новини» (вживати: свіжі/останні новини) та «зробити інтерв''ю»
    (вживати: взяти/дати інтерв''ю)'
  - 'Стилістичні нюанси: розмежування понять «опублікувати» (для преси) та «оприлюднити» (для документів/даних); різниця між
    «трансляцією» та «передачею»'
  - 'Робота з прийменниками у медіа-контексті: правильне вживання «в ефірі» (не «на ефірі») та «дивитися по телевізору»'
vocabulary_hints:
  required:
  - упередженість (bias) — редакційна/політична упередженість; упереджене ставлення до подій
  - маніпуляція (manipulation) — емоційна маніпуляція свідомістю; технічні засоби маніпуляції
  - пропаганда (propaganda) — ворожа/російська пропаганда; стати жертвою пропаганди
  - джерело (source) — надійне/перевірене джерело; посилатися на першоджерело
  recommended:
  - верифікація (verification) — верифікація даних; двоетапна верифікація інформації
  - джинса (hidden advertising) — прихована реклама в медіа; специфічний український термін для замовних матеріалів
  - шпальта (newspaper column/page) — з'явитися на перших шпальтах; газетна шпальта
  - оприлюднити (to make public/disclose) — оприлюднити офіційні результати або документи (на відміну від 'опублікувати' статтю)
  - свіжі новини (fresh/breaking news) — заміна кальці 'гарячі новини'; актуальна інформація
activity_hints:
- type: quiz
  focus: Identify Риторичні прийоми у ЗМІ in sentences
  items: 12
- type: fill-in
  focus: Complete sentences using Риторичні прийоми у ЗМІ
  items: 10
- type: match-up
  focus: Match Упередженість та редакційна політика examples to categories
  items: 12
- type: error-correction
  focus: Find and fix errors in Риторичні прийоми у ЗМІ
  items: 8
- type: group-sort
  focus: Classify examples by Пропаганда та емоційні маніпуляції
  items: 12
- type: essay-response
  focus: Write paragraph using Риторичні прийоми у ЗМІ correctly
persona:
  voice: Professional Language Coach
  role: Investigative Journalist (Журналіст-розслідувач)
grammar:
- Риторичні прийоми у ЗМІ
- Мовні маркери упередженості
- Конструкції хеджування та модальності
register: публіцистичний
immersion: 100
prerequisites:
- news-analysis-basics
connects_to:
- presentation-skills-basics

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

Research **Аналіз новин: Поглиблено** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Аналіз новин: Поглиблено

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
