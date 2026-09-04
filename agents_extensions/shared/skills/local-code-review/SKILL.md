---
name: local-code-review
description: Canonical code/infra closeout workflow — freezes scope, resolves the exact review target (local/commit/branch/PR), runs a non-mutating review, resolves a cross-family reviewer, and requires separate behavior proof for user-visible code or infrastructure changes. Never use as a learner-content semantic gate.
argument-hint: "[local | commit <sha> | branch <branch> <base> | pr <number>]"
---

# Closeout Review: $ARGUMENTS

This skill supports only `code` and `infra` review profiles. A normal BIO
learner-content request routes to `$curriculum-lifecycle` (or directly to
`$track-completion` for one module), which owns the single bounded
`$post-build-review` gate. `resolve-reviewer` fails before route selection for
any learner-content semantic profile or domain. Do not duplicate post-build
semantic review here.

Use the explicit target in `$ARGUMENTS`: `local`, `commit <sha>`,
`branch <branch> <base>`, or `pr <number>`. The checklist below owns target
semantics, scope freezing, non-mutating checks, cross-family reviewer
resolution, finding adjudication, and separate behavior proof. A clean
working tree never substitutes for reviewing a requested commit or PR.

For inline PR-comment posting, use `/code-review:code-review`.

## Execute

Read and follow [`local-code-review-checklist.md`](local-code-review-checklist.md)
in full. It drives `.venv/bin/python -m scripts.review.closeout_cli` for every
step that has a deterministic answer (target resolution, scope-baseline
freeze and breakers, reviewer resolution, findings adjudication) and tells
you exactly what to reason about yourself.

## Output

Print a structured report to the conversation (the checklist's Step 8 gives
the exact shape). Do NOT write a file unless specifically asked.
