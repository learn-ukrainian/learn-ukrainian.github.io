{NORTH_STAR}

{LESSON_CONTRACT}

# Phase 4 Linear Per-Dimension Reviewer Prompt

Review only the assigned dimension. Cite concrete evidence from the generated
content. Return a machine-readable mapping with `score`, `evidence`, and
`verdict` for this one dimension.

Assigned dimension: {DIM}

## Reasoning checklist (do this BEFORE scoring — #1673)

Before producing the JSON response, reason through this dimension explicitly.
If the model supports extended thinking (Claude, Gemini, GPT-5.5), use it
for these four steps. Skipping this is the "scoring without evidence" failure
mode that non-negotiable rule #6 forbids — every PASS or REVISE that doesn't
trace to verbatim quotes from the content is invalid by definition.

1. **List 3 specific evidence quotes from the Generated Content related to
   `{DIM}`.** Quote them verbatim — character-for-character strings that
   actually appear in `module.md`, `activities.yaml`, `vocabulary.yaml`, or
   `resources.yaml`. Do not invent. Do not paraphrase. Do not summarize.

2. **For each quote, state how it maps to the rubric for `{DIM}`.** Is this
   quote evidence FOR the dimension being satisfied, or evidence AGAINST?
   Which specific rubric criterion does it touch? A quote that is irrelevant
   to the rubric is not evidence — find a different one.

3. **Aggregate the score on the 1-10 scale.** Strongest evidence weighs more
   than weakest. What does the balance tell you? Round to 1 decimal place.

4. **Final verdict.** Score ≥8 → PASS. Score 6-7.99 → REVISE. Score <6 →
   REJECT.

The JSON `evidence` field below MUST be one of the verbatim quotes from
step 1, wrapped in escaped quotes. A summary or paraphrase in the evidence
field is a reviewer-protocol failure.

Return only JSON:

```json
{"score": 0.0, "evidence": "\"verbatim quote from the content\"", "verdict": "REVISE"}
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
