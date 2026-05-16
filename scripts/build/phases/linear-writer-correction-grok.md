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

## When `gate = tool_theatre`

Your previous turn cited tool names in `<plan_thinking><verification_trace>` that
you did not actually call. The unmatched citations are listed under
`diagnostic.violations` in the gate feedback above.

Pick exactly one path. Single fenced ```` ```markdown file=module.md ```` block
as your entire response, no prose around it.

1. **Call them now.** Make the tool calls you cited (each one), then re-emit
   `module.md` with the actual tool results in the verification block. The
   verification text should reference the result, not the tool name in isolation.
2. **Remove the false citations.** Delete the unmatched tool names from the
   verification blocks; replace each removed citation with the verbatim text
   "verification not performed" so it's auditable.

No third option. Citing the same tools again without calling them = same
failure, same gate, exhausted retry. Removing backticks while keeping the
uncalled tool name in prose is still a citation and still fails.

Verbatim citation rule: every tool name you cite in
`<plan_thinking><verification_trace>` must correspond to a tool call you
actually made in this turn's trace.

## Previously-Passing Prose

The following prose passed other gates before this correction. Preserve it
verbatim except for the smallest append/insert needed for the failed gate.
Return the FULL patched module.md (the unchanged prose plus your minimal
patch) inside the single fenced block above.

```markdown
{MODULE_CONTENT}
```
