# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c2-084
level: C2
sequence: 84
slug: corpus-linguistics
version: '2.0'
title: Корпусна лінгвістика та цифрові інструменти
subtitle: Corpus Linguistics and Digital Tools
focus: grammar
pedagogy: TTT
phase: C2.5 [Meta-Skills & Capstone]
word_target: 5000
objectives:
- Learner can navigate and query Ukrainian language corpora (ГРАК, Корпус текстів НАН) to extract authentic usage data
- Застосовувати corpus-based methods (concordancing, collocation analysis, frequency profiling) to resolve grammatical
  and lexical doubts
- Learner can critically compare textbook Ukrainian with corpus-attested natural usage and identify discrepancies
- Використовувати NLP tools for Ukrainian (морфологічний аналізатор, синтаксичний парсер) to support складні self-editing
  and language analysis
sources:
- name: ГРАК — Генеральний регіонально анотований корпус української мови
  url: https://grak.org.ua/
  type: primary
  notes: The largest annotated corpus of Ukrainian; primary tool for hands-on exercises
- name: Корпус текстів Національної академії наук України
  url: https://lcorp.ulif.org.ua/
  type: primary
  notes: Academic corpus maintained by the Ukrainian Lingua-Information Fund
- name: 'McEnery T., Hardie A. Corpus Linguistics: Method, Theory and Practice'
  url: https://www.cambridge.org/
  type: reference
  notes: Standard methodological reference for corpus linguistics adapted to Ukrainian context
content_outline:
- section: 'Вступ: Що таке мовний корпус (Introduction: What Is a Linguistic Corpus)'
  words: 700
  points:
  - 'Definition and purpose: what constitutes a linguistic corpus; the distinction between a corpus and a text archive; why
    corpus data matters for achieving C2 mastery.'
  - 'Types of corpora: annotated (морфологічно розмічений), parallel (паралельний), historical (діахронний), and learner corpora
    (корпус учнівських текстів); how each type serves different research and learning goals.'
  - 'Corpus-based vs corpus-driven approaches: using corpora to verify hypotheses (top-down) vs discovering patterns inductively
    from data (bottom-up).'
- section: Українські мовні корпуси (Ukrainian Language Corpora)
  words: 900
  points:
  - 'ГРАК (Генеральний регіонально анотований корпус): structure, size, regional and genre annotation; practical navigation
    of the search interface; interpreting results and metadata.'
  - 'Корпус текстів НАН України: academic and scientific text collections; how this corpus complements ГРАК for specialized
    registers and terminology.'
  - 'Historical and specialized corpora: diachronic corpora for tracking language change; learner corpora for error analysis;
    the role of corpora in standardization and dictionary compilation.'
- section: Корпусні інструменти та методи (Corpus Tools and Methods)
  words: 900
  points:
  - 'Concordancers and KWIC (Key Word In Context): how concordance lines reveal collocational patterns, syntactic behavior,
    and semantic prosody of Ukrainian words.'
  - 'Frequency lists and their applications: understanding frequency rankings; comparing active vocabulary with corpus frequency
    data; implications for vocabulary prioritization at C2 level.'
  - 'Collocation analysis and statistical measures: MI score (mutual information), t-score, and log-likelihood as tools for
    identifying strong vs weak collocations; practical interpretation of collocation tables.'
- section: Частотність і автентичність (Frequency and Authenticity)
  words: 800
  points:
  - 'Frequency dictionaries of Ukrainian: overview of existing resources; how corpus frequency validates or challenges traditional
    vocabulary selection in textbooks.'
  - 'Textbook Ukrainian vs corpus-attested usage: identifying gaps between pedagogical language and natural language; examples
    of overrepresented and underrepresented constructions in Ukrainian L2 materials.'
  - 'Register variation through frequency: how word frequency profiles differ across registers (academic, journalistic, literary,
    conversational) and what this reveals about authentic register mastery.'
- section: Обчислювальні підходи (Computational Approaches)
  words: 800
  points:
  - 'NLP tools for Ukrainian: морфологічний аналізатор (morphological analyzer), синтаксичний парсер (syntactic parser); overview
    of pymorphy2-uk, Stanza Ukrainian model, and LanguageTool-UA.'
  - 'The Ukrainian language technology landscape: current state, key research groups (ІМФ НАНУ, Грамматично), and challenges
    specific to Ukrainian NLP (rich morphology, free word order, limited training data).'
  - 'Machine translation evaluation: using corpus methods to assess MT output quality; identifying systematic errors in Ukrainian
    machine translation and their linguistic sources.'
- section: Практичне застосування (Practical Applications)
  words: 600
  points:
  - 'Self-editing with corpora: using corpus evidence to verify collocations, check preposition governance, and resolve grammatical
    doubts (e.g., case selection after specific verbs).'
  - 'Academic writing improvement: using frequency and collocation data to move from acceptable to natural Ukrainian in research
    papers, essays, and професійні documents.'
  - 'Resolving prescriptive disputes: cases where corpus data supports or challenges normative recommendations; the role of
    empirical evidence in contemporary Ukrainian language standardization.'
- section: 'Практикум: Корпусний запит (Workshop: Corpus Query Exercise)'
  words: 300
  points:
  - 'Hands-on exercise: formulating and executing corpus queries to find authentic examples for a chosen grammatical or lexical
    topic; interpreting concordance output and frequency data.'
  - 'Comparative task: contrasting corpus-attested patterns with learner intuitions and textbook prescriptions; writing a
    brief analytical report on findings.'
vocabulary_hints:
  required:
  - корпус (corpus) — мовний корпус, анотований корпус, паралельний корпус; foundational term for the entire module.
  - конкорданс (concordance) — конкордансні рядки, аналіз конкордансу; primary tool for corpus-based analysis.
  - колокація (collocation) — сильна колокація, аналіз колокацій, колокаційна таблиця; essential for understanding word combinations.
  - частотність (frequency) — частотний словник, частотний профіль, лексична частотність; core concept for corpus-based vocabulary
    work.
  - морфологічний аналізатор (morphological analyzer) — автоматичний морфологічний аналіз, розмічування тексту; NLP tool for
    Ukrainian.
  - синтаксичний парсер (syntactic parser) — автоматичний синтаксичний розбір, дерево залежностей; computational tool for
    sentence structure.
  - розмітка (annotation) — морфологічна розмітка, синтаксична розмітка, ручна розмітка; metadata layer that makes corpora
    searchable.
  - діахронний (diachronic) — діахронний аналіз, діахронний корпус; essential for historical language study.
  recommended:
  - конкорданцер (concordancer) — інструмент для пошуку та відображення контекстних рядків.
  - MI-показник (MI score / mutual information) — статистична міра сили колокації; значення MI вище 3 вказує на сильну колокацію.
  - KWIC (Key Word In Context) — формат відображення пошукових результатів у корпусі.
  - семантична просодія (semantic prosody) — позитивна/негативна семантична просодія; прихована оцінність слова, що виявляється
    через корпусний аналіз.
  - ревіталізація (revitalization) — корпусні дані як інструмент ревіталізації мовних норм.
activity_hints:
- type: quiz
  focus: Визначення корпусних термінів та інтерпретація статистичних показників
  items: 12
- type: fill-in
  focus: Формулювання корпусних запитів та інтерпретація конкордансів
  items: 10
- type: essay-response
  focus: Аналітичний звіт на основі корпусних даних
- type: critical-analysis
  focus: Порівняння підручникової мови з корпусними даними
  items: 6
connects_to:
- c2-85 (Error Analysis — corpus methods applied to error identification)
- c2-79 (Complete Grammar Review — corpus evidence for grammar mastery)
- c2-83 (Language Policy and Decolonization — empirical data informing policy analysis)
prerequisites:
- c2-083 (Language Policy and Decolonization)
persona:
  voice: Senior Specialist
  role: Digital Linguist
grammar:
- Що таке мовний корпус
- Українські мовні корпуси
- Корпусні інструменти та методи
- Частотність і автентичність
register: академічний

```

**Level constraints quick-ref:**

```
# C2 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `5000`, `Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words.`, etc.

## Grammar Scope

No grammar restrictions. Full literary Ukrainian. Near-native mastery expected.

## Immersion (100% Ukrainian)

Everything in Ukrainian — learner operates as near-native.
English ONLY in vocabulary table translations (YAML).
Latin/Greek scholarly terms (e.g., "damnatio memoriae", "genius loci") acceptable in academic contexts.

## Module Types

| Type | Modules | Focus |
|------|---------|-------|
| Stylistics | M01-25 | Stylistic perfection (7 styles) |
| Literary | M26-40 | Literary mastery |
| Professional | M41-75 | Professional meta-skills & specialization |
| Capstone | M76-100 | Meta-skills & final capstone |
| Checkpoint | M20,25,40,55,75,100 | Review + assessment |

## C2 Activity Design

C2 uses **analytical** activity types, not drill exercises:
- **reading** — extended authentic text analysis
- **essay-response** — long-form written production
- **critical-analysis** — literary/linguistic critique
- **comparative-study** — cross-text or cross-register comparison
- **quiz** — fewer but native-level complexity
- **true-false** — nuanced claim evaluation

**Not used at C2:** fill-in, cloze, unjumble, anagram, match-up, error-correction, mark-the-words, group-sort

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `C2` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Корпусна лінгвістика та цифрові інструменти** for the **C2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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
- **Word count**: minimum **5000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Корпусна лінгвістика та цифрові інструменти

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
