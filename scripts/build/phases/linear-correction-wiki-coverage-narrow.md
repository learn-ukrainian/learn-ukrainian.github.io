# Phase 4 Linear Wiki-Coverage Narrow Correction Prompt

This is Path 3 PR3 from
`docs/decisions/2026-05-17-path3-per-obligation-review-loop.md` lines 66-92.
PR1 seeded `implementation_map.json`; PR2 made `run_wiki_coverage_gate`
emit structured `fix_proposals`; this prompt is the per-obligation fallback
after batched correction attempts. PR4 is separate Goodhart-sentinel work and
must not be implemented here.

You are correcting one deterministic wiki coverage failure. Apply the
smallest local change that satisfies the supplied obligation.

## Output Contract

Return exactly one `<fixes>` block and nothing else.

Allowed XML form:

```xml
<fixes>
  <fix obligation_id="err-1">
    <find>exact text currently present in the artifact</find>
    <replace>small corrected text</replace>
  </fix>
</fixes>
```

Allowed YAML-list form:

```yaml
<fixes>
- obligation_id: err-1
  find: exact text currently present in the artifact
  replace: small corrected text
</fixes>
```

No commentary before or after `<fixes>`. No fenced code blocks. No regenerated
artifact. No section rewrite. Strictly follow ADR-007:
`docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md`.

## Patch Rules

- Every `find` value must be a unique exact substring of the current artifact
  text below.
- Every `replace` value must be the corrected text for that same local span.
- Each fix must identify the `obligation_id` it satisfies, preferably as the
  XML `obligation_id` attribute shown above.
- Use `manifest_payload` values verbatim. If it contains `incorrect`,
  `correct`, `written`, `spoken`, `heading`, `required_claim`, `why`, or
  `rule`, reproduce the relevant value exactly.
- No single `replace` value may exceed 600 characters.
- Patch only this artifact. Do not mention or modify unrelated files.

## Module Context

- Level: {LEVEL}
- Module: {MODULE_NUM}
- Slug: {MODULE_SLUG}
- Previous batched attempts: {PREVIOUS_BATCHED_ATTEMPTS}

## Obligation

- Obligation id: {OBLIGATION_ID}
- Obligation type: {OBLIGATION_TYPE}
- Failure reason: {FAILURE_REASON}

## Expected Treatment

```yaml
{EXPECTED_TREATMENT}
```

## Manifest Payload

```yaml
{MANIFEST_PAYLOAD}
```

## Surgical Diff Hint

```text
{SURGICAL_DIFF_HINT}
```

## Current Artifact State From Gate

```text
{CURRENT_ARTIFACT_STATE}
```

## Full Artifact Text

```text
{FULL_ARTIFACT_TEXT}
```
