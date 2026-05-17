# Phase 4 Linear Wiki-Coverage Correction Prompt

This is Path 3 PR3 from
`docs/decisions/2026-05-17-path3-per-obligation-review-loop.md` lines 66-92.
PR1 seeded `implementation_map.json`; PR2 made `run_wiki_coverage_gate`
emit structured `fix_proposals`; this prompt closes the deterministic loop
for one batched failure group. PR4 is separate Goodhart-sentinel work and
must not be implemented here.

You are correcting one group of deterministic wiki coverage failures. Apply
the smallest local changes that satisfy the supplied proposals.

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
- Use `manifest_payload` values verbatim. For example, if the proposal says
  `incorrect: Я прокидаєшся.` and `correct: Я прокидаюся.`, the replacement
  must contain those strings exactly.
- No single `replace` value may exceed 600 characters.
- Patch only this artifact. Do not mention or modify unrelated files.

## Module Context

- Level: {LEVEL}
- Module: {MODULE_NUM}
- Slug: {MODULE_SLUG}
- Word target: {WORD_TARGET}
- Failure group: {FAILURE_GROUP_KEY}
- Coverage before this pass: {COVERAGE_PCT_BEFORE}
- Iteration: {ITERATION}

## Fix Proposals For This Group

```yaml
{FIX_PROPOSALS_YAML}
```

## Current Artifact Text

```text
{ARTIFACT_TEXT}
```
