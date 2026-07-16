---
name: local-code-review
description: Canonical closeout-review workflow — freezes scope, resolves the exact review target (local/commit/branch/PR), runs a non-mutating review, resolves a cross-family reviewer, and requires separate behavior proof for user-visible changes. Use before declaring any change done.
argument-hint: "[local | commit <sha> | branch <branch> <base> | pr <number>]"
---

# Closeout Review: $ARGUMENTS

> **Scope**: this is the closeout gate for a change you (or another agent)
> already made — not a PR-comment bot. For posting inline PR comments, use
> the official `/code-review:code-review` plugin instead; this skill can
> still drive the target-selection and scope-freeze steps underneath it.

This skill defines **orchestration and policy** for closeout review. It does
not implement the strict finding verifier or reviewer process isolation —
those are separate, later slices (issue #5281 children 2 and 3). What it
does guarantee:

- the review target is explicit and deterministic — never inferred from
  whatever the working tree happens to look like;
- scope is frozen once, before the first review pass, and visibly
  re-checked as the review/fix loop runs;
- review preparation never mutates the source tree;
- the reviewer is a different model **family** from the author, resolved
  by a single canonical helper — not re-derived per skill invocation;
- every finding is adjudicated explicitly — nothing is silently dropped,
  and nothing is applied "as-is" without an adjudication;
- CLI/API/UI/generated-artifact changes require a separate, source-blind
  behavior proof — code review alone cannot close them out.

## Parse arguments

`$ARGUMENTS` selects the review target **mode**, explicitly — never inferred
from `git status`:

1. `local` — staged + unstaged + untracked changes in the working tree.
2. `commit <sha>` — one already-made commit, diffed against its parent.
3. `branch <branch> <base>` — a branch diffed against an explicit base ref.
4. `pr <number>` — a PR diffed against its **actual** base (not an assumed
   default branch).

If the user gives you a PR number, a commit SHA, or says "review my branch,"
that is the mode — do not fall back to `local` because the working tree
looks clean. A clean working tree is not evidence that a commit or PR was
reviewed (see Step 1 below).

## Execute

Read and follow [`local-code-review-checklist.md`](local-code-review-checklist.md)
in full. It drives `.venv/bin/python -m scripts.review.closeout_cli` for every
step that has a deterministic answer (target resolution, scope-baseline
freeze and breakers, reviewer resolution, findings adjudication) and tells
you exactly what to reason about yourself.

## Output

Print a structured report to the conversation (the checklist's Step 8 gives
the exact shape). Do NOT write a file unless specifically asked.
