---
name: show-me-your-work
description: Keep a reviewable decision log as a TSV the task owns. Use for /show-me-your-work.
---

# Show me your work

Keep a decision log when the task is long enough that a later reader cannot replay it from the diff alone. Do not run an upstream logger script. Append rows yourself.

Columns, tab-separated, header in [the template](references/decision-log-template.tsv):

`ts`, `phase`, `decision`, `why`, `evidence`, `result`

- `ts` comes from `date -u`.
- `evidence` is a commit SHA, a repo-relative path, or a command you ran. Never a secret, a host path, or a private transcript.
- `result` is a short outcome such as `tests green`, `reverted`, or `open`.

Store the file where the brief allows evidence, or under `batch_state/reports/` when that is the task's held-work location. Commit it only when the brief asks for an auditable record in git.

When you review a log, check each evidence cell against the artifact. A row with no evidence is a claim, not a record.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
