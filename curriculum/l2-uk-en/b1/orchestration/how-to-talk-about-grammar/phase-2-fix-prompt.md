# Phase 2 Fix: Content Expansion

> **You are Gemini, fixing Phase 2 output that failed validation.**
> **Your ONLY task: Expand the existing content to meet word count and callout targets.**

## Current Content (READ FROM DISK)

```
curriculum/l2-uk-en/b1/orchestration/how-to-talk-about-grammar/phase-2-content.md
```

## Validation Failures

The content was validated by the orchestrator and **FAILED** on these metrics:

| Metric | Required | Actual | Gap |
|--------|----------|--------|-----|
| Total words | 4000 minimum (6000 target) | **2437** | **-1563 below minimum** |
| Engagement callouts | 14+ | 10 | -4 |

**NOTE**: Your previous word count report said 5350 words. The ACTUAL count (verified by `wc -w`) is **2437**. Your word counting was off by 2x. Do NOT trust your internal word counter — the real target is to double the current content length.

## Specific Fixes Required

### 1. MNEMONIC ERROR (Critical)
The case mnemonic is WRONG. You wrote "**Г**орішки" but the correct mnemonic is:
**На Різдво Дід Загубив Орішки Між Ковбасками**
- **Н**а → **Н**азивний
- **Р**іздво → **Р**одовий
- **Д**ід → **Д**авальний
- **З**агубив → **З**нахідний
- **О**рішки → **О**рудний
- **М**іж → **М**ісцевий
- **К**овбасками → **К**личний

Each first letter maps to a case. Fix this with the correct letter-by-letter mapping.

### 2. WORD COUNT EXPANSION (Critical — +1563 words minimum)
Every section is too thin. Apply these expansions:

**Section 1 (Вступ)** — Current ~300w, need ~550w:
- Expand Смотрицький paragraph with specific historical details (1619 grammar, Church Slavonic tradition)
- Add 1-2 more etymological comparisons (e.g., "adjective" < Latin *adiectivum* vs "прикметник" < прикмета)

**Section 2 (Самостійні частини мови)** — Current ~500w, need ~750w:
- Each H3 needs ~80-100 words minimum. Expand definitions to 2+ sentences
- Add usage notes (напр., "Прикметники в українській мові завжди узгоджуються з іменником — у роді, числі та відмінку")
- Add [!observe] callout to one POS asking the student to identify examples

**Section 3 (Службові слова)** — Current ~350w, need ~600w:
- Expand each H3 with a real-context example from a grammar rule
- Add [!culture] or [!history-bite] callout about Ukrainian particle system

**Section 4 (Відмінки)** — Current ~500w, need ~800w:
- Each case H3 needs ~80-100 words. Currently ~60 each.
- Expand "Додаткова інформація" sections (currently one sentence each)
- Add connection to etymology (Давальний ← давати, Знахідний ← знаходити, Орудний ← орудувати)
- Fix mnemonic as specified above

**Section 5 (Будова слова)** — Current ~400w, need ~650w:
- Морфеміка: Add a concrete word decomposition example (e.g., пере-чит-ува-ти)
- Граматичні категорії: Add 1 example for each category
- Синтаксичні ролі: Add a sentence parsed into all roles

**Section 6 (Практика)** — Current ~300w, need ~400w:
- Add a textbook excerpt analysis (show a real-looking passage, then identify the metalanguage)
- Expand cultural anchoring with specific quote analysis

**Section 7 (Підсумок)** — Current ~150w, need ~250w:
- Add a key terms review table (term → question → example)
- Expand the roadmap section

### 3. ADD 4 MORE CALLOUTS (to reach 14+)
Suggested placements:
- [!history-bite] in Section 4 about Smotrytskyj and Vocative case
- [!decolonization] about Ukrainian grammatical tradition being distinct from Russian
- [!observe] in Section 2 asking students to classify words
- [!culture] in Section 6 about Ukrainian literary tradition

### 4. DO NOT CHANGE
- The H2/H3 structure (it's correct)
- The mermaid diagrams (they're correct)
- The dialogues (they're correct)
- The example sentence format

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

Return the COMPLETE expanded content (not just the changes):

```
===CONTENT_START===
{full expanded content with ALL fixes applied}
===CONTENT_END===
```

Then report HONEST word counts (remember: `wc -w` is the real validator, not your internal counter):

```
===WORD_COUNTS===
Section "{name}": {count} words (target: {allocation})
...
Total: {total} words (target: 4000, overshoot ratio: {total/4000}x)
===WORD_COUNTS===
```

## Friction Report

```
===FRICTION_START===
**Phase**: Phase 2: Content Fix
**Step**: {what}
**Friction Type**: NONE | ...
**Raw Error**: {or "None"}
**Self-Correction**: {or "N/A"}
**Proposed Tooling Fix**: {or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT change the document structure
- Do NOT add new sections
- Do NOT generate activities or vocabulary tables
- Do NOT remove existing content — only EXPAND
- Fix the mnemonic error
- Add 4+ new callouts
- Target 4000+ words total (verify by counting every word)
