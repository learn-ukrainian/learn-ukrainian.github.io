# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-078
level: B2
sequence: 78
slug: nauka-i-doslidzhennia
version: '2.0'
title: Наука і дослідження
subtitle: Science & Research
focus: domain
pedagogy: CBI
phase: B2.8
word_target: 4000
objectives:
- Використовувати наукову термінологію українською
- Описувати дослідницький процес
- Орієнтуватися в українській науковій спільноті
content_outline:
- section: 'Вступ: Українська наука та видатні вчені (Introduction: Ukrainian Science and Distinguished Scientists)'
  words: 600
  points:
  - Introduction to the National Academy of Sciences (NAS) of Ukraine and universities as central hubs for research and innovation.
  - 'Cultural Hook: Volodymyr Vernadsky (1863–1945) — his refusal of Russian citizenship, the concept of the Noosphere, and
    his legacy as the founder of the Ukrainian Academy of Sciences.'
  - 'Cultural Hook: Borys Paton — pioneering electric welding in space and the development of bloodless surgery through soft
    tissue welding.'
  - 'Cultural Hook: Ihor Sikorsky — his early Kyiv-based inventions, including the first helicopter (1910) and the ''Ilya
    Muromets'' aircraft.'
- section: Структура наукового дослідження та академічна етика (Structure of Scientific Research and Academic Ethics)
  words: 700
  points:
  - 'Stages of research: from formulating a hypothesis (висунути гіпотезу) and choosing methodology to conducting experiments
    and reaching conclusions (дійти висновку).'
  - Defining the standard IMRAD structure (Introduction, Methods, Results, and Discussion) for organizing academic content
    and reading efficiency.
  - 'Scientific ethics: understanding academic integrity (доброчесність) and the peer review process (рецензування), including
    blind review (сліпе рецензування).'
  - 'Terminology nuance: distinguishing between the generic ''вчений'' (scientist) and the more active/professional ''науковець''
    (researcher/scholar).'
- section: Наукова термінологія та академічний регістр (Scientific Terminology and Academic Register)
  words: 700
  points:
  - 'Bridging the stylistics gap: differentiating between the Academic Register (Академічний стиль) and Conversational Register
    (Розмовний стиль).'
  - 'General scientific vocabulary across disciplines: analysis, synthesis, correlation, and conducting research (проводити
    ґрунтовне дослідження).'
  - 'Learner Error: Correcting the common Russianism ''В якості науковця...'' to the idiomatic Ukrainian ''Як науковець...''.'
  - 'Grammar in Science: Prioritizing the active voice (''Ми проаналізували'') over the clunky passive calques (''Нами було
    проведено аналіз'') common in learner output.'
- section: Критичне читання наукових текстів (Critical Reading of Scientific Texts)
  words: 700
  points:
  - 'Analysis of abstracts and introductions: identifying the object, subject, and goals of a study within the text.'
  - 'Decoding visual information: understanding graphs and tables and describing data trends using academic vocabulary.'
  - 'Naturalness Check: Avoiding the collocation error ''Зустрічаються помилки'' (meeting people) in favor of the correct
    ''Трапляються помилки'' (occurring errors).'
  - 'Stylistic precision: identifying and removing pleonasms like ''дисертаційне дослідження'' in favor of the concise ''дисертація''.'
- section: Обговорення наукових тем та представлення результатів (Discussing Scientific Topics and Presenting Results)
  words: 700
  points:
  - Formulating research questions and expressing degrees of certainty or hedging (можливо, ймовірно, за нашими даними) during
    academic discussion.
  - 'State Standard §3.17: Discussing scientific discoveries and inventions that changed the world (комп’ютеризація, телекомунікація).'
  - 'Science under pressure: a thematic discussion on the challenges and adaptation of Ukrainian science during the war.'
- section: Підсумок та практика (Summary and Practice)
  words: 600
  points:
  - 'Practical task: Analyzing a popular science article vs. an academic abstract to identify register shifts.'
  - 'Production: Delivering a short oral presentation on a scientific topic or a planned research project (§3.10: academic
    titles and degrees).'
  - Final review of key scientific collocations and preparatory notes for the B2 Capstone project.
vocabulary_hints:
  required:
  - дослідження (research) — проводити ґрунтовне дослідження, результати дослідження, об'єкт дослідження; high frequency academic
    term
  - аналіз (analysis) — глибокий аналіз, піддавати аналізу, на основі аналізу; high frequency in data description
  - синтез (synthesis) — синтез результатів, теоретичний синтез; often contrasted with analysis in research methodology
  - висновок (conclusion) — дійти висновку, зробити висновки, попередні висновки; crucial for summary sections
  - експеримент (experiment) — ставити експеримент, у ході експерименту; used in empirical and natural sciences
  - гіпотеза (hypothesis) — висунути гіпотезу, підтвердити/спростувати гіпотезу; core component of the scientific method
  recommended:
  - аналіз (analysis) — глибокий аналіз, піддавати аналізу, на основі аналізу; high frequency in data description
  - синтез (synthesis) — синтез результатів, теоретичний синтез; often contrasted with analysis in research methodology
  - висновок (conclusion) — дійти висновку, зробити висновки, попередні висновки; crucial for summary sections
  - експеримент (experiment) — ставити експеримент, у ході експерименту; used in empirical and natural sciences
  - рецензування (peer review) — процес рецензування, сліпе рецензування; specific to academic publishing and quality control
  - науковець (scientist/researcher) — молодий науковець, відомий науковець; modern preferred term over 'вчений'
activity_hints:
- type: quiz
  focus: Identify Academic register in sentences
  items: 12
- type: fill-in
  focus: Complete sentences using Academic register
  items: 10
- type: match-up
  focus: Match Структура наукового дослідження та академічна етика examples to categories
  items: 12
- type: error-correction
  focus: Find and fix errors in Academic register
  items: 8
- type: group-sort
  focus: Classify examples by Наукова термінологія та академічний регістр
  items: 12
- type: essay-response
  focus: Write paragraph using Academic register correctly
persona:
  voice: Professional Language Coach
  role: Lab Researcher (Лаборант-дослідник)
grammar:
- Academic register
- Scientific terminology
prerequisites:
- tekhnolohii-ta-shi
connects_to:
- mystetstvo-i-literatura
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

Research **Наука і дослідження** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Наука і дослідження

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
