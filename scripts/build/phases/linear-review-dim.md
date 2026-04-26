{NORTH_STAR}

{LESSON_CONTRACT}

# Phase 4 Linear Per-Dimension Reviewer Prompt

Review only the assigned dimension. Cite concrete evidence from the generated
content. Return a machine-readable mapping with `score`, `evidence`, and
`verdict` for this one dimension.

Assigned dimension: {DIM}

Return only JSON:

```json
{"score": 0.0, "evidence": "\"quoted excerpt from the content\"", "verdict": "REVISE"}
```

## Module Context

- Level: {LEVEL}
- Module: {MODULE_NUM}
- Slug: {MODULE_SLUG}
- Word target: {WORD_TARGET}

## Immersion Rule

{IMMERSION_RULE}

## Contract YAML

```yaml
{CONTRACT_YAML}
```

## Plan

```yaml
{PLAN_CONTENT}
```

## Generated Content

{GENERATED_CONTENT}
