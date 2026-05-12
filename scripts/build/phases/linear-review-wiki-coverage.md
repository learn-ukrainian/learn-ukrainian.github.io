{NORTH_STAR}

{LESSON_CONTRACT}

# Phase 4 Linear Wiki-Coverage Reviewer Prompt

Review only wiki-obligation coverage. This pass is parallel to the five
standard QG dimensions; it is not a `QG_DIMS` dimension.

The deterministic gate has already checked objective presence. Your job is to
verify semantic adequacy: each obligation must be implemented in the claimed
artifact location with evidence consistent with its treatment type.

## Required Method

For every obligation in the Wiki Obligations Manifest:

1. Read the manifest obligation id, obligation type, required treatment, and
   source-line metadata.
2. Read the writer's implementation_map claim for that same obligation id.
3. Inspect the cited artifact and location in Generated Content.
4. Emit one verdict:
   - PASS: cited evidence implements the obligation.
   - PARTIAL: evidence exists but is thin, vague, or in a weaker location.
   - FAIL: missing, contradicted, or not in the claimed location.

Treatment-specific checks:

- `contrast_pair`: both the incorrect and correct forms appear in the activity
  body, and the learner has to distinguish them.
- `prose_explanation`: module.md prose discusses the wiki claim's substance,
  not merely a related vocabulary item.
- `explicit_explanation`: learner-facing pronunciation guidance is present; a
  vague "smooth speech" reminder is not enough.
- `sequence_step`: the module prose teaches the step's canonical pedagogical
  claim in an appropriate order.
- decolonization bans: the generated content avoids the banned framing and, if
  relevant, gives a Ukrainian-centered replacement.

Return only JSON:

```json
{
  "verdicts": [
    {
      "obligation_id": "err-1",
      "verdict": "PASS",
      "evidence": "verbatim excerpt from the cited artifact location",
      "rationale": "why this evidence satisfies or misses the treatment"
    }
  ],
  "overall_verdict": "PASS",
  "summary": "short aggregate rationale"
}
```

`overall_verdict` must be `FAIL` if any obligation verdict is `FAIL`.
`PARTIAL` is a soft signal unless the pattern shows systematic under-teaching.

## Module Context

- Level: {LEVEL}
- Module: {MODULE_NUM}
- Slug: {MODULE_SLUG}
- Word target: {WORD_TARGET}

## Wiki Obligations Manifest

{WIKI_MANIFEST}

## Deterministic Wiki Coverage Gate

{WIKI_COVERAGE_GATE}

## Plan

```yaml
{PLAN_CONTENT}
```

## Generated Content

{GENERATED_CONTENT}

