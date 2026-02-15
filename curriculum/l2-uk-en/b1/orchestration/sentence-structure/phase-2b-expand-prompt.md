# Phase 2b: Content Expansion

> **You are Gemini, continuing Phase 2 of an orchestrated rebuild.**
> **Your task: Expand specific thin sections to hit the 4000-word minimum.**

## Context

The lesson content for **Структура речення** is at 2938 words — needs 1100+ more to hit the 4000 minimum. Several sections are below their budgets.

Read the current content file:
```
curriculum/l2-uk-en/b1/orchestration/sentence-structure/phase-2-content.md
```

Read the meta for section budgets:
```
curriculum/l2-uk-en/b1/meta/sentence-structure.yaml
```

## Sections to Expand

| Section | Current | Target | Deficit |
|---------|---------|--------|---------|
| Структура складного речення | 194w | 350w | +156w |
| Підсумок: Ваша синтаксична карта | 186w | 350w | +164w |
| Пунктуація та порядок слів | 212w | 350w | +138w |
| Культурний код: Синтаксичний розбір | 221w | 500w | +279w |
| Другорядні члени речення | 464w | 550w | +86w |
| Діалоги: Граматика в контексті | 393w | 550w | +157w |

## Expansion Instructions

For each section, output the **FULL EXPANDED SECTION** (not just additions). This lets the orchestrator do a clean replacement.

**How to expand each section:**

1. **Структура складного речення** (need +156w): Add a comparison table for складносурядне vs складнопідрядне. Add a `[!tip]` callout about recognizing clause boundaries.

2. **Підсумок** (need +164w): Add 4-6 self-check questions (Перевірте себе). Add a visual cheat sheet table of underlining symbols.

3. **Пунктуація та порядок слів** (need +138w): Add examples showing how comma placement changes meaning. Add a `[!warning]` about common punctuation mistakes.

4. **Культурний код: Синтаксичний розбір** (need +279w): This is the crown jewel — the cultural hook. Add a full worked example of синтаксичний розбір step by step. Show the underlining notation for a multi-part sentence.

5. **Другорядні члени речення** (need +86w): Add one more contrasting example for each member type.

6. **Діалоги** (need +157w): Add 1-2 more mini-dialogues. Ensure all dialogues use blockquote format: `> **Name:** text`.

## Rules

- Keep 85% Ukrainian immersion
- Use «...» for quotes, never "..."
- All dialogues in blockquote format
- No Russianisms
- No English inside Ukrainian sentences

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

Output each expanded section between delimiters. The orchestrator will replace sections in the original file.

```
===EXPANSION_START===
## Структура складного речення
{full expanded section content — 350+ words}

## Пунктуація та порядок слів
{full expanded section content — 350+ words}

## Культурний код: Синтаксичний розбір
{full expanded section content — 500+ words}

## Другорядні члени речення
{full expanded section content — 550+ words}

## Діалоги: Граматика в контексті
{full expanded section content — 550+ words}

## Підсумок: Ваша синтаксична карта
{full expanded section content — 350+ words}
===EXPANSION_END===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase 2b: Content Expansion
**Step**: {what you were doing}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```
