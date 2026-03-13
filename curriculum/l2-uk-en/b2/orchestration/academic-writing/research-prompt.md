# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b2-069
level: B2
sequence: 69
slug: academic-writing
version: '2.0'
title: Академічне письмо
subtitle: Academic Writing
focus: skills
pedagogy: TTT
phase: B2.7
word_target: 4000
objectives:
- Учень знає структуру академічного есе та правила цитування
- Учень може будувати логічну аргументацію з використанням тез та доказів
- Учень розуміє принципи академічної доброчесності
content_outline:
- section: 'Вступ: Основи та історія академічного письма (Introduction: Fundamentals and History of Academic Writing)'
  words: 600
  points:
  - 'Historical context: The Kyiv-Mohyla Academy tradition (1615) emphasizing rhetoric and philosophy vs. the Soviet-era legacy
    of ''dry'' scientific reporting.'
  - Defining the principles of objectivity, accuracy, and logic as the core of the Ukrainian academic register.
  - 'Distinguishing academic texts from publicism: tone, evidence-based claims, and target audience expectations.'
- section: Академічна доброчесність та етика у 2026 році (Academic Integrity and Ethics in 2026)
  words: 800
  points:
  - 'Review of the Law ''On Academic Integrity'' (Feb 1, 2026): New requirements for disclosing the use of AI tools in research
    and writing.'
  - The concept of 'доброчесність' (integrity) as a fundamental moral value in Ukrainian education, moving beyond simple rule-following.
  - 'Types of academic misconduct: identifying plagiarism, self-plagiarism, and the ethical implications of fabrication.'
  - 'Learner error correction: eliminating the pleonasm ''своя власна думка'' in favor of the correct ''власна думка'' when
    expressing a position.'
- section: Структура есе та побудова тези (Essay Structure and Thesis Development)
  words: 800
  points:
  - 'State Standard §1.3.1.1 alignment: Developing a complex thesis statement and organizing the text with clear logical hierarchies.'
  - 'The mechanics of the introduction: setting the problem context and formulating a ''вагома теза'' (strong thesis).'
  - 'Crafting logic between paragraphs: ensuring each sub-point supports the central thesis without thematic drift.'
  - 'Practical focus: Collocations for thesis work — ''сформулювати тезу'', ''обґрунтувати тезу'', ''головна теза''.'
- section: 'Аргументація: докази та контраргументація (Argumentation: Evidence and Counter-argumentation)'
  words: 1000
  points:
  - Developing 'за' (pro) and 'проти' (con) evidence for a balanced argumentative text as per the 2024 State Standard.
  - 'Types of academic evidence: logical reasoning, empirical data, and authoritative citations (авторитетні джерела).'
  - 'Strategic use of statistics and examples: ''наводити приклад'' (correct) vs. the common learner error ''приводити приклад''.'
  - 'Addressing counter-arguments: techniques for respectful refutation (''спростування'') and acknowledging the complexity
    of a problem.'
- section: Стилістика, цитування та покликання (Stylistics, Citations, and References)
  words: 800
  points:
  - 'Language organization: using ''вставні слова'' for listing (по-перше, по-друге), clarifying, and hedging (можливо, ймовірно).'
  - Correcting the calque 'при написанні' with the natural 'під час написання' or active constructions.
  - 'Shift from passive to active voice: replacing stiff constructions like ''нами було досліджено'' with ''ми дослідили''
    to show researcher agency.'
  - 'Terminology standardization: strictly using ''покликання'' (citation/reference) for bibliography items rather than the
    generic ''посилання'' (link).'
  - 'Academic integrity drills: paraphrasing vs. direct citation and formatting a ''список використаних джерел'' correctly.'
vocabulary_hints:
  required:
  - теза (thesis) — сформулювати тезу, обґрунтувати тезу; High frequency academic term
  - аргумент (argument) — вагомий аргумент, спростувати аргумент, навести аргумент; Core for persuasive writing
  - доброчесність (integrity) — академічна доброчесність, порушення доброчесності; Key legal and ethical term in 2026
  - покликання (citation/reference) — оформити покликання, список покликань; Use specifically for bibliography, not generic
    links
  - плагіат (plagiarism) — виявити плагіат, уникнути плагіату; Includes the concept of самоплагіат (self-plagiarism)
  - аналіз (analysis) — глибокий аналіз, провести аналіз, порівняльний аналіз; High frequency across all academic domains
  - цитування (citation) — правила цитування, пряме цитування; Distinction between direct and indirect quotes
  recommended:
  - термін (term) — вживати термін, науковий термін
  - поняття (concept) — ключове поняття, визначити поняття
  - процес (process) — динамічний процес, перебіг процесу
  - метод (method) — науковий метод, метод дослідження
  - синтез (synthesis) — результати синтезу, аналіз і синтез
  - дослідження (research) — ґрунтовне дослідження, об'єкт дослідження
  - брати участь (to participate) — Correct form; avoid the common error 'приймати участь'
activity_hints:
- type: fill-in
  focus: Complete Академічна доброчесність та етика у 2026 році with appropriate language
  items: 10
- type: quiz
  focus: Choose the best response for each scenario
  items: 12
- type: match-up
  focus: Match situations to appropriate language
  items: 12
- type: error-correction
  focus: Fix inappropriate register in Структура есе та побудова тези
  items: 8
- type: fill-in
  focus: Complete professional text with correct forms
  items: 8
- type: essay-response
  focus: Produce Академічна доброчесність та етика у 2026 році for given scenario
persona:
  voice: Professional Language Coach
  role: Thesis Advisor (Науковий керівник)
grammar:
- Структура аргументативного есе
- Використання вставних слів для зв’язку думок (отже, по-перше, з іншого боку)
prerequisites:
- professional-reports-advanced
connects_to:
- text-analysis
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

Research **Академічне письмо** for the **B2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Академічне письмо

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
