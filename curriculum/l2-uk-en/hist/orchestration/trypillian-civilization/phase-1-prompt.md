# Phase 1: Meta Rebuild

> **You are Gemini, executing Phase 1 of an orchestrated rebuild.**
> **Your ONLY task: Rebuild the content_outline from the plan + research.**

**Why this phase exists:** Existing meta files may be the product of a weak or outdated prompt. The plan is the source of truth. You rebuild the meta's content_outline fresh using the plan's structure + the research notes' depth.

## Your Input

Read the research notes from Phase 0:

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/research/trypillian-civilization-research.md
```

Read the **plan file** (SOURCE OF TRUTH for structure, objectives, vocabulary):

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/hist/trypillian-civilization.yaml
```

Read the **old meta file** (for reference only — you are REPLACING the content_outline):

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/meta/trypillian-civilization.yaml
```

## Your Task

**Rebuild** the `content_outline` in the meta file from scratch, using the plan's section structure as the skeleton and the research notes to inform depth and word allocation.

1. Every section has a `words` allocation
2. Word allocations sum to approximately **5000** (the level's word target, provided by the build system)
3. Sections are informed by research notes (sections with richer research get more words)
4. Section names are natural Ukrainian H2 headings
5. Each section's `points` list is specific and actionable — not vague ("cover grammar" → bad; "Each POS gets its own H3 with definition, question, 2+ examples, usage note" → good)

### Rules

- **Do NOT copy the old meta's outline** — rebuild from the plan's section structure
- Allocations should sum to approximately 5000 words (±10% is acceptable)
- Minimum section allocation: 200 words (smaller sections should be merged)
- Each section must have `section`, `words`, and `points` fields
- Section names must be Ukrainian (this is the lesson content heading)
- **Bridge modules (immersion < 90%):** Note the plan's `immersion` field in the outline. The intro section should explicitly list English scaffolding requirements.
- Check the subject's vital status: living person → "Значення" / "Вплив"; deceased → "Спадщина" / "Наслідки"
- If the research found mnemonics, cultural anchors, or notable quotes: ensure the outline allocates space for them in the appropriate section's `points`

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
  # Total: 5000 words
===META_OUTLINE_END===
```

### Validation

Before returning, verify:
- [ ] All section names are Ukrainian
- [ ] **Section names match plan exactly** — If the plan has a `content_outline` with section names, your output MUST use those EXACT names (or very close Ukrainian equivalents). Do NOT invent new section names that diverge from the plan. The audit will fail if meta section names don't match the content's H2 headings, which must match the plan.
- [ ] Each section has `words` and `points`
- [ ] Sum of all `words` = 5000
- [ ] No section has fewer than 200 words
- [ ] Points reflect research findings
- [ ] Section order follows logical narrative flow

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
- Do NOT add fields not listed above (no `id`, `type`, etc.)
- Do NOT request skills or delegate to Claude
