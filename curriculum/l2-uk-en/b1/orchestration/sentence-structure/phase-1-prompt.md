# Phase 1: Meta Rebuild

> **You are Gemini, executing Phase 1 of an orchestrated rebuild.**
> **Your ONLY task: Rebuild the content_outline from the plan + research.**

**Why this phase exists:** The plan is the source of truth. You rebuild the meta's content_outline fresh using the plan's structure + the research notes' depth.

## Your Input

Read the research notes from Phase 0:

```
curriculum/l2-uk-en/b1/research/sentence-structure-research.md
```

Read the **plan file** (SOURCE OF TRUTH for structure, word_target, objectives, vocabulary):

```
curriculum/l2-uk-en/plans/b1/sentence-structure.yaml
```

There is no existing meta file — this is a fresh build. You are creating the content_outline from scratch.

## Your Task

**Build** the `content_outline` from scratch, using the plan's section structure as the skeleton and the research notes to inform depth and word allocation.

1. Every section has a `words` allocation
2. Word allocations sum to **exactly 4000** (the plan's word_target)
3. Sections are informed by research notes (sections with richer research get more words)
4. Section names are natural Ukrainian H2 headings
5. Each section's `points` list is specific and actionable — not vague ("cover grammar" → bad; "Each sentence part gets its own H3 with definition, question pattern, 2+ examples, standard underlining convention" → good)

### Special Considerations

- This is a **bridge module** (B1.0 phase, 85% immersion). The intro should note English scaffolding: Ukrainian terms first, English in parentheses on FIRST introduction only. After that, Ukrainian only.
- The plan has thin sections: "Conjunctions" (151w) and "Additional Syntax Terms" (151w) — both below the 200w minimum. **Merge or redistribute** these into other sections.
- The research found the "синтаксичний розбір" (syntactic analysis) cultural hook — allocate space in a Practice section.
- The standard underlining conventions (підмет = one line, присудок = two lines, etc.) should be prominently featured.

### Rules

- **Do NOT change `word_target`** — it is 4000 and immutable
- Allocations must sum to exactly 4000
- Minimum section allocation: 200 words (smaller sections should be merged)
- Each section must have `section`, `words`, and `points` fields
- Section names must be Ukrainian (this is the lesson content heading)
- **Section names must match plan where possible** — use the plan's section names or close Ukrainian equivalents
- If the research found mnemonics, cultural anchors, or notable quotes: ensure the outline allocates space

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
- Do NOT change word_target
- Do NOT add fields not listed above (no `id`, `type`, etc.)
- Do NOT request skills or delegate to Claude
