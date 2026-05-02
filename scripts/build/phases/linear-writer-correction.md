# ADR-008 Writer Correction

You are correcting one failed deterministic Python QG gate.

Hard constraint: modify in place via append/insert, never re-author or regenerate.

Forbidden phrases for this task:
- regenerate
- rewrite
- produce again
- start over

Do not use any forbidden phrase as an instruction or strategy. Do not discard
the previously-passing prose. Keep the current structure and patch only the
specific failed gate described below.

## Gate Feedback

```yaml
{CORRECTION_SECTION}
```

## Previously-Passing Prose

The following prose passed other gates before this correction. Preserve it
verbatim except for the smallest append/insert needed for the failed gate.

```markdown
{MODULE_CONTENT}
```
