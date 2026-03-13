# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c1-011
level: C1
sequence: 11
slug: summary-paraphrase
version: '2.0'
title: Резюме та парафраз
subtitle: 'Introduction: The Art of Retelling'
content_outline:
- section: 'Вступ: Мистецтво переказу (Introduction: The Art of Retelling)'
  words: 500
  points:
  - 'Linguistic distinction: Differentiating ''резюме'' (summary/abstract) from the
    common false friend ''резюме'' (CV/Resume) used in business contexts.'
  - 'Cultural hook: The Ukrainian school tradition of ''переказ'' (retelling) as a
    standardized exam format; differentiating between ''детальний'' (detailed) and
    ''стислий'' (concise) types.'
  - 'Role in academic writing: Following the State Standard §1.3.1.1 for using tools
    of indirect speech (іномовлення) to create secondary texts.'
- section: Техніки резюмування та анотування (Summarizing and Abstracting Techniques)
  words: 800
  points:
  - 'Selection of ''головні ідеї'' (main ideas): Criteria for distinguishing essential
    information from secondary details and examples.'
  - 'The process of ''реферування'' (abstracting): Structuring summarized information
    into a cohesive, structured text with points and subpoints.'
  - 'Capturing the ''суть'' (essence): How to maintain the original meaning while
    drastically reducing word count for an ''анотація'' (abstract).'
- section: Парафраз та техніка іномовлення (Paraphrase and Indirect Speech Technique)
  words: 1000
  points:
  - 'Fixing ''Patchwriting'': Moving beyond simple synonym swaps to deep structural
    transformation, including active to passive voice and verbal to nominal constructions.'
  - 'Learner error correction: Avoiding English calques like ''У інших словах'' and
    replacing them with standard markers: ''Інакше кажучи'', ''Іншими словами'', ''Тобто''.'
  - 'Demonstrating comprehension: Paraphrasing as a tool to show the reader that the
    source material has been fully internalized, not just copied.'
- section: Академічна доброчесність та уникнення плагіату (Academic Integrity and
    Avoiding Plagiarism)
  words: 700
  points:
  - 'Defining ''академічний плагіат'': Understanding the boundaries between proper
    paraphrase, direct ''цитування'' (citation), and intellectual theft.'
  - 'Rules of citation: When to use direct quotes (пряме цитування) versus indirect
    synthesis to support an academic argument.'
  - 'Tools and criteria: Self-check methods for verifying that a paraphrase is sufficiently
    different from the original source structure.'
- section: Науковий стиль та синтез інформації (Scientific Style and Information Synthesis)
  words: 500
  points:
  - 'Characteristics of ''науковий стиль'': Maintaining impersonality, precision,
    and logical flow when re-stating another author''s ideas.'
  - 'Synthesis techniques: Combining information from multiple sources into a single
    coherent paragraph for a ''Literature Review'' (prepares for c1-14).'
- section: Практика створення вторинних текстів (Practice of Creating Secondary Texts)
  words: 500
  points:
  - 'Applied task: Writing a professional ''анотація'' to a scientific article or
    cultural text, following State Standard §1.3.1.1 guidelines.'
  - 'Integration check: Evaluating the balance between summary and paraphrase within
    a 100-word paragraph.'
vocabulary_hints:
  required:
  - резюме (summary/abstract) — High frequency; distinguish from CV (Resume) in business
    contexts.
  - парафраз (paraphrase) — Medium frequency; technical technique of rewording.
  - переказ (retelling) — High frequency; familiar school exam format (детальний/стислий).
  - анотація (annotation/abstract) — Medium frequency; summary of a scientific or
    literary work.
  - плагіат (plagiarism) — Academic context; focus on 'уникнення плагіату' (avoiding
    plagiarism).
  - 'цитування (citation/quoting) — Collocations: ''пряме цитування'', ''правила цитування''.'
  - 'суть (essence/core) — Collocations: ''передати суть'', ''збагнути суть'', ''суть
    питання''.'
  - іномовлення (indirect speech/paraphrasing) — State Standard term for re-stating
    information.
  - реферування (abstracting) — Formal process of summarizing academic texts.
  - стислий (concise/brief) — Essential for 'стислий переказ' or 'стисле резюме'.
  recommended:
  - конспектування (note-taking) — Structured recording of information from a source.
  - адаптація (adaptation) — Modifying a text for a specific audience or purpose.
  - трансформація (transformation) — Changing grammatical structure (e.g., active
    to passive).
  - інтерпретація (interpretation) — Explaining the meaning of a source in one's own
    words.
  - науковий стиль (scientific style) — The formal register required for academic
    paraphrasing.
  - 'вдалий (successful/apt) — Collocation: ''вдалий парафраз''.'
activity_hints:
- type: fill-in
  focus: Summarize a paragraph in 2-3 sentences
  items: 10+
- type: fill-in
  focus: Paraphrase sentences without changing meaning
  items: 12+
- type: quiz
  focus: Identify plagiarism vs proper paraphrase
  items: 15+
- type: match-up
  focus: Original to acceptable paraphrase
  items: 12+
- type: cloze
  focus: Paraphrase markers in context
  items: 10+
- type: essay-response
  focus: Summarize article in 100 words
focus: grammar
pedagogy: TTT
prerequisites:
- c1-07 (Citation & Reference)
- c1-10 (Counterarguments)
connects_to:
- c1-12 (Research Article)
- c1-14 (Literature Review)
- c1-19 (Article Critique)
module_type: grammar
sources:
- name: Academic Writing Skills in Ukrainian
  url: https://mon.gov.ua/
  type: reference
  notes: Paraphrasing and summarizing guidelines
- name: Academic Integrity Resources
  url: https://mova.info/
  type: secondary
  notes: Avoiding plagiarism through proper paraphrasing
immersion: 100% Ukrainian
phase: C1.1 [Academic Writing & Research]
objectives:
- Learner can identify and produce correct Техніки резюмування та анотування forms
- Learner can analyze Парафраз та техніка іномовлення in authentic texts
- Learner can produce written text demonstrating mastery of Мистецтво переказу
persona:
  voice: Senior Specialist
  role: Референт
word_target: 4000
grammar:
- Мистецтво переказу
- Техніки резюмування та анотування
- Парафраз та техніка іномовлення
- Академічна доброчесність та уникнення плагіату
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

Research **Резюме та парафраз** for the **C1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Резюме та парафраз

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
