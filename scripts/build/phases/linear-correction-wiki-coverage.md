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

You may emit ONLY these two fix shapes inside `<fixes>...</fixes>`
(XML or YAML, no other content):

- `<fix><find>...</find><replace>...</replace></fix>` - local textual
  find/replace.
- `<fix><insert_after>...</insert_after><text>...</text></fix>` - inserts
  AFTER an existing anchor.

You MUST NOT:

- Regenerate full activity blocks (`- id: act-N` with multiple keys).
- Add new top-level activity entries.
- Rewrite multi-line YAML structures.
- Output any Markdown, prose, or YAML outside `<fixes>`.

Allowed XML form:

```xml
<fixes>
  <fix obligation_id="err-1">
    <find>exact text currently present in the artifact</find>
    <replace>small corrected text</replace>
  </fix>
</fixes>
```

Allowed XML insert form:

```xml
<fixes>
  <fix obligation_id="err-1">
    <insert_after>exact existing anchor text</insert_after>
    <text>small inserted text</text>
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

Allowed YAML insert form:

```yaml
<fixes>
- obligation_id: err-1
  insert_after: exact existing anchor text
  text: small inserted text
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
- Each `replace` and each `text` body must satisfy both caps: at most 6 lines
  and at most 240 characters. Exceeding either cap is evidence of
  regeneration. If you need a larger patch, abort with `<fixes></fixes>` and
  let the next gate iteration handle it.
- Patch only this artifact. Do not mention or modify unrelated files.

## Anti-Pattern: m20 Build #1 Regeneration

WRONG (regeneration):

```yaml
- find: |
    - id: act-7
      ...existing block...
  replace: |
    - id: act-7
      ...rewritten block...
    - id: act-8           # FORBIDDEN: brand-new entry
      type: true-false
      ...
```

RIGHT (additive via `insert_after`):

```yaml
- insert_after: |
    # last item of an existing activity's `items:` list
  text: |
    - left: foo
      right: bar
```

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
