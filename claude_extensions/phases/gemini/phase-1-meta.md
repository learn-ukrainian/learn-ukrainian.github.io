# Phase 1: Meta Alignment

> **You are Gemini, executing Phase 1 of an orchestrated rebuild.**
> **Your ONLY task: Refine the content_outline with word allocations.**

## Your Input

Read the research notes from Phase 0:

```
{RESEARCH_PATH}
```

Read the current meta file:

```
{META_PATH}
```

Read the plan file (source of truth for word_target and objectives):

```
{PLAN_PATH}
```

## Your Task

Refine the `content_outline` in the meta file so that:

1. Every section has a `words` allocation
2. Word allocations sum to **exactly {WORD_TARGET}** (the plan's word_target)
3. Sections are informed by research notes (sections with richer research get more words)
4. Section names are natural Ukrainian H2 headings

### Rules

- **Do NOT change `word_target`** — it comes from the plan and is immutable
- Allocations must sum to `word_target` (not more, not less)
- Minimum section allocation: 200 words (smaller sections should be merged)
- Each section must have `section`, `words`, and `points` fields
- Section names must be Ukrainian (this is the lesson content heading)
- Check the subject's vital status: living person → "Значення" / "Вплив"; deceased → "Спадщина" / "Наслідки"

### Output Format

Return the refined content_outline as YAML:

```
===META_OUTLINE_START===
content_outline:
  - section: "{Section 1 name in Ukrainian}"
    words: {allocation}
    points:
      - "{key point 1}"
      - "{key point 2}"
  - section: "{Section 2 name}"
    words: {allocation}
    points:
      - "..."
  # ... all sections
  # Total: {WORD_TARGET} words
===META_OUTLINE_END===
```

### Validation

Before returning, verify:
- [ ] All section names are Ukrainian
- [ ] Each section has `words` and `points`
- [ ] Sum of all `words` = {WORD_TARGET}
- [ ] No section has fewer than 200 words
- [ ] Points reflect research findings
- [ ] Section order follows logical narrative flow

## Boundaries

- Do NOT write lesson content
- Do NOT change word_target
- Do NOT add fields not listed above (no `id`, `type`, etc.)
- Do NOT request skills or delegate to Claude
