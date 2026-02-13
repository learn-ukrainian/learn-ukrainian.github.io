# Phase 1: Meta Rebuild

> **You are Gemini, executing Phase 1 of an orchestrated rebuild.**
> **Your ONLY task: Rebuild the content_outline from the plan + research.**

**Why this phase exists:** Existing meta files may be the product of a weak or outdated prompt. The plan is the source of truth. You rebuild the meta's content_outline fresh using the plan's structure + the research notes' depth.

## Your Input

Read the research notes from Phase 0:

```
curriculum/l2-uk-en/b1/orchestration/how-to-talk-about-grammar/phase-0-research.md
```

Read the **plan file** (SOURCE OF TRUTH for structure, word_target, objectives, vocabulary):

```
curriculum/l2-uk-en/plans/b1/how-to-talk-about-grammar.yaml
```

Read the **archive diff report** (what good content was lost in the previous rebuild — must be preserved):

```
curriculum/l2-uk-en/b1/orchestration/how-to-talk-about-grammar/archive-diff.md
```

Read the **old meta file** (for reference only — you are REPLACING the content_outline):

```
curriculum/l2-uk-en/b1/meta/how-to-talk-about-grammar.yaml
```

## Your Task

**Rebuild** the `content_outline` in the meta file from scratch, using the plan's section structure as the skeleton and the research notes to inform depth and word allocation.

1. Every section has a `words` allocation
2. Word allocations sum to **exactly 4000** (the plan's word_target)
3. Sections are informed by research notes (sections with richer research get more words)
4. Section names are natural Ukrainian H2 headings
5. Each section's `points` list is specific and actionable — not vague ("cover grammar" → bad; "Each POS gets its own H3 with definition, question, 2+ examples, usage note" → good)

### Rules

- **Do NOT change `word_target`** — it comes from the plan and is immutable
- **Do NOT copy the old meta's outline** — rebuild from the plan's section structure
- Allocations must sum to `word_target` (not more, not less)
- Minimum section allocation: 200 words (smaller sections should be merged)
- Each section must have `section`, `words`, and `points` fields
- Section names must be Ukrainian (this is the lesson content heading)
- **Bridge module (immersion 65%):** The intro section should explicitly list English scaffolding requirements — Ukrainian term first, English in parentheses on first introduction only.
- **CRITICAL: The archive diff report lists high-value content that was lost in the previous rebuild. Your outline MUST allocate space for these elements:**
  - Case mnemonic (На Різдво Дід Загубив Орішки Між Ковбасками)
  - Deverbal instruction keywords (Означає, Вказує на, etc.) in the Practice section
  - Introduction sub-structure (psychological advantage + linguistic tradition)
  - Section 5 MUST have 3 separate H3 subsections (морфеміка, граматичні категорії, синтаксичні ролі)
  - Myth-buster and metacognitive callouts

### Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

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
  # Total: 4000 words
===META_OUTLINE_END===
```

### Validation

Before returning, verify:
- [ ] All section names are Ukrainian
- [ ] Each section has `words` and `points`
- [ ] Sum of all `words` = 4000
- [ ] No section has fewer than 200 words
- [ ] Points reflect research findings AND archive diff requirements
- [ ] Section order follows logical narrative flow
- [ ] Section 5 explicitly requires 3 H3 subsections
- [ ] Case section includes mnemonic requirement
- [ ] Practice section includes deverbal instruction keywords

## Friction Report (MANDATORY)

After your meta outline output, include:

```
===FRICTION_START===
**Phase**: Phase 1: Meta Outline
**Step**: {what you were doing when friction occurred, or "Full outline"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT write lesson content
- Do NOT change word_target
- Do NOT add fields not listed above (no `id`, `type`, etc.)
- Do NOT request skills or delegate to Claude
