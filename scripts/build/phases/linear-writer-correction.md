# ADR-008 Writer Correction

You are correcting one failed deterministic Python QG gate. Apply the smallest
patch that clears the gate.

## Output contract — non-negotiable

Return **exactly one** fenced markdown block, formatted as:

```` markdown
```markdown file=module.md
... full patched module.md content ...
```
````

That is the entire response. Do **not** include any of the following:
- progress notes ("Done.", "Word count went from X → Y")
- summaries of changes
- explanatory prose before, between, or after the fenced block
- the `activities.yaml`, `vocabulary.yaml`, or `resources.yaml` artifacts
  (they are not being patched in this correction pass — leave them untouched
  on disk)

Any response that is not exactly one `markdown file=module.md` fenced block
will be rejected as `writer_correction_unparseable` and the module will fail.

## Hard constraint — patch-bounded

Modify in place via append/insert. Never re-author or regenerate.

Forbidden phrases as instructions or strategy: "regenerate", "rewrite",
"produce again", "start over". Do not discard the previously-passing prose.
Keep the current structure and patch only the specific failed gate described
below.

## Gate Feedback

```yaml
{CORRECTION_SECTION}
```

## Previously-Passing Prose

The following prose passed other gates before this correction. Preserve it
verbatim except for the smallest append/insert needed for the failed gate.
Return the FULL patched module.md (the unchanged prose plus your minimal
patch) inside the single fenced block above.

```markdown
{MODULE_CONTENT}
```
