# Phase 4 Fix: Content Expansion for Word Count

> **You are Gemini, fixing content to pass audit.**
> **Task: Expand 4 thin sections to reach 4000+ words total.**

## Current State

The lesson is at **3364 core words** (target: 4000). Need **~700 more words**.

Read the current content:
```
curriculum/l2-uk-en/b1/sentence-structure.md
```

## Sections to Expand

| Section | Current | Target | Need |
|---------|---------|--------|------|
| Культурний код: Синтаксичний розбір | 293w | 500w | +207w |
| Діалоги: Граматика в контексті | 444w | 550w | +106w |
| Типи речень та сполучники | 351w | 450w | +99w |
| Підсумок: Ваша синтаксична карта | 248w | 350w | +102w |
| Вступ: Архітектура українського речення | 277w | 350w | +73w |
| Головні члени речення: Підмет і присудок | 487w | 550w | +63w |

## Expansion Instructions

Output the **FULL EXPANDED** version of each section below. I will replace each section entirely.

**Specific expansion needs:**

1. **Культурний код** (+207w): The crown jewel. Add a FULL worked example of синтаксичний розбір — take a real sentence like «Маленька дитина радісно грала в парку» and show step-by-step analysis: identify підмет, присудок, додаток, означення, обставина. Show the underlining conventions. Add a `[!culture]` callout about how every Ukrainian student does this exercise.

2. **Діалоги** (+106w): Add 1-2 more mini-dialogues. ALL dialogues MUST use blockquote format:
```markdown
> **Олена:** text
> **Тарас:** text
```

3. **Типи речень** (+99w): Add a comparison table for просте vs складне речення with 3-4 examples each. Add a `[!tip]` about recognizing clause boundaries.

4. **Підсумок** (+102w): Add 4-6 self-check questions in format:
```markdown
**Перевірте себе:**
1. question?
2. question?
...
```
Also add a visual table summarizing underlining symbols.

5. **Вступ** (+73w): Add connection to how this prepares students for b1-26 relative clauses and b1-35 concessive clauses.

6. **Головні члени** (+63w): Add one more example for each (підмет and присудок), showing more complex cases.

## Rules

- 85% Ukrainian immersion — English only in parenthetical equivalents on first use
- All dialogues in `> **Name:** text` format
- Use «...» for quotes
- No Russianisms
- Every H3 must have 80+ words

## Output Format

```
===EXPANSION_START===
## Вступ: Архітектура українського речення
{full section — 350+ words}

## Головні члени речення: Підмет і присудок
{full section — 550+ words}

## Типи речень та сполучники
{full section — 450+ words}

## Культурний код: Синтаксичний розбір
{full section — 500+ words}

## Діалоги: Граматика в контексті
{full section — 550+ words}

## Підсумок: Ваша синтаксична карта
{full section — 350+ words}
===EXPANSION_END===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase 4: Fix (Content Expansion)
**Step**: {what you were doing}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```
