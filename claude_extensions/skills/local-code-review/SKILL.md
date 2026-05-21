---
name: local-code-review
description: Working-tree (uncommitted diff) code review with cross-model adversarial pass — Gemini reviews, Codex challenges false positives, surviving findings get applied. Use BEFORE commit. For PR-level review, use the official `/code-review:code-review` plugin instead.
argument-hint: "[files|diff|all]"
---

# Local Code Review: $ARGUMENTS

> **Scope**: working-tree only — uncommitted edits in your active session. For pull-request review use the official `/code-review:code-review` plugin command (it fans out 5 parallel Sonnet agents + Haiku confidence-scoring and posts back via `gh pr comment`).

## Parse Arguments

The user provides one of:

1. **No args or "diff"**: Review only files changed since last commit (`git diff --name-only` + `git diff --cached --name-only`)
2. **"all"**: Review all staged + unstaged changes
3. **Specific files**: `scripts/build/v7_build.py scripts/build/linear_pipeline.py`

## Execute

Read and follow the full local code review checklist at [`local-code-review-checklist.md`](local-code-review-checklist.md).

## Output

Print a structured report to the conversation. Do NOT write a file unless specifically asked.
