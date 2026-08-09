# Pull-request issue references

GitHub parses closing references lexically. Negating a closing action does not
make an issue reference safe.

When a pull request leaves an issue open, use one of these forms:

- `Refs #123`
- `This PR leaves #123 open.`

Use `Closes #123`, `Fixes #123`, or `Resolves #123` only when the pull request
owns the issue's complete closeout. Do not put a negative expression beside a
closing action and an issue reference.

The required CI job runs this deterministic check on PR creation, updates, and
body edits. To exercise it locally with a disposable body, run:

```bash
printf '%s' 'Refs #123' | .venv/bin/python scripts/audit/lint_pr_closing_references.py --stdin
```

Before auto-merge, the task lifecycle also compares GitHub's authoritative
closing-reference list with the lifecycle's declared remaining-scope status.
