# Phase 2 Fix: Content Expansion

> **You are Gemini, fixing undercount in Phase 2 content.**
> **Your ONLY task: Expand specific sections that are under their word floor.**

## Context

The content you wrote for **Мова про дієслова** (B1 M02) is under the 4000-word floor. The audit found:

```
TOTAL: 3074 / 4000 (❌ -926 words short)

Sections needing expansion:
  Час дієслова: Граматична подорож         429 / 616  ❌ (-187)
  Форми дієслова: Синтетична та складена   345 / 513  ❌ (-168)
  Читання граматичних пояснень             233 / 411  ❌ (-178)
  Міні-діалоги: Обговорення граматики      252 / 513  ❌ (-261)
```

## Files to Read

Read the current content file to understand what's already written:

```
curriculum/l2-uk-en/b1/language-about-verbs.md
```

Read the meta for section requirements:

```
curriculum/l2-uk-en/b1/meta/language-about-verbs.yaml
```

Read the research for additional material:

```
curriculum/l2-uk-en/b1/research/language-about-verbs-research.md
```

## Your Task

**Output a COMPLETE replacement version** of the content file, expanding the 4 sections listed above. Keep the existing content (don't rewrite what's already good), but ADD depth to the short sections.

### Specific Expansion Guidance

**Section 4 (Час дієслова) — needs +187 words:**
- Add a comparison table of 3 tenses with examples
- Expand the section on past tense rod (masculine/feminine/neuter) with examples
- Add a mini-dialogue asking about tense

**Section 7 (Форми дієслова) — needs +168 words:**
- Add comparison table: синтетична vs складена форма (at least 4 verb examples)
- Expand the наказова форма section with formation rules + examples
- Add a callout about парадигма and дієвідмінювання

**Section 8 (Читання граматичних пояснень) — needs +178 words:**
- Add a real grammar rule excerpt (e.g., from a textbook) and annotate it with terms learned
- Add a second practice text
- Include a step-by-step strategy for parsing grammar explanations

**Section 9 (Міні-діалоги) — needs +261 words:**
- Add at least 2 more dialogue pairs (currently probably only 1-2)
- Each dialogue should demonstrate 3+ verb terms in natural context
- Add a study-buddy scenario discussing homework questions about aspect

### Rules

- Keep ALL existing callouts, examples, dialogues that are in the current file
- Do NOT change section names (H2 headers must match exactly)
- Do NOT add vocabulary outside the plan's vocabulary_hints
- Use `> [!type]` format for all callouts (with blockquote prefix)
- Use «...» quotes, not "..."
- Every H3 block: 150-200 words minimum
- Target total: at least 4500 words (to have margin above 4000 floor)
- Immersion: 70% Ukrainian, English equivalents on first use only

## Output Format

Return the **COMPLETE** file content (all sections, not just the expanded ones):

```
===CONTENT_START===

{ENTIRE module content — all 10 sections, with expansions applied}

===CONTENT_END===
```

After the content block, report word counts:

```
===WORD_COUNTS===
Section "{name}": {count} words (floor: {allocation})
...
Total: {total} words (HARD FLOOR: 4000)
===WORD_COUNTS===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase 2: Content Fix
**Step**: {what you were doing}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT generate activities (Phase 3 handles these)
- Do NOT skip any section
- Do NOT remove existing callouts or examples
- Do NOT change H2 section names
