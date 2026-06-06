# Current - Codex Orchestrator Handoff (2026-06-06)

Latest-Brief: docs/session-state/codex-orchestrator-handoff.md

## Role

Codex is the A1/A2 retrofit PR gate and orchestrator. Workers open draft PRs
and stop; the orchestrator checks the queue, reviews, assigns independent
review, merges only when clean, and cleans up branches/worktrees.

Do not use `docs/session-state/current.md` as scratch space. It is the shared
router. If it is dirty at startup, restore it from `origin/main` and stop to
report. Durable orchestrator state lives in this file. Thread rollover packets
live under `.agent/<agent>-thread-handoff.md`.

## Current State

- #2717 merged: neutral A1/A2 standards.
- #2728 merged: A1/A2 retrofit audit protocol and evidence packet template.
- #2734 merged: A1 M1-M7 retrofit audit/classification report.
- #2736 merged: A1 M1-M7 plan/wiki/prompt repair.
- #2736 merge commit: `7ebac72745a0a1dc12c97ee841e1e6c7869570d7`.
- #2747 cleanup work is complete and merged, including the related cleanup PRs
  #2767, #2765, #2770, #2771, #2772, and #2773.
- #2774 merged: worker inbox control plane for orchestrator/delegate results.

The A1 M1 pilot is still struggling. The current blocker is not "rebuild from
scratch"; it is that early A1 gates/prompts are asking for mature error
correction material too early, especially decolonization bad-form pairs. The
likely direction is pure Ukrainian learner-facing A1 content first, then
introduce Russianism/Anglicism contrast work later when students have enough
Ukrainian to benefit from it.

## Operating Rules

- One active A1/A2 PR maximum.
- Before dispatching or reviewing, check open PRs and active delegates.
- Do not start duplicate work if a worker is already running.
- Do not create a new branch/worktree unless fixing the PR under review.
- Do not touch generated status/audit/review artifacts unless explicitly in
  scope.
- Do not modify `.python-version`, `.yamllint`, or `.markdownlint.json`.
- Do not use third-party workbook/product/trademark names in repo files,
  branch names, PR titles/bodies, issue comments, or internal handles.
- Do not copy, quote, summarize, store, extract, embed, or derive from paid
  commercial materials.
- Use `.worktrees/dispatch/<agent>/<task>/` for implementation work.
- Every commit must carry an `X-Agent` trailer.
- Use `.venv/bin/python`, not `sys.executable` or system Python.

## Review Policy

Use deterministic checks first. Use Gemini for independent review when required
by the gate. Add DeepSeek, Claude, or Cursor review when there is meaningful
language/register/pedagogy/build risk. The orchestrator remains responsible for
rejecting false positives and fixing or routing valid findings.

## Startup Checks

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main --prune
git status --short -- docs/session-state/current.md
gh pr list --state open --json number,title,isDraft,mergeStateStatus,headRefName,url --limit 50
gh pr list --search 'A1 A2 in:title,body is:open repo:learn-ukrainian/learn-ukrainian.github.io' --json number,title,isDraft,mergeStateStatus,headRefName,url --limit 50
curl -sS http://127.0.0.1:8765/api/delegate/active
.venv/bin/python scripts/orchestration/orchestrator_control.py inbox --recent 20 --include-results
```

## Next Focus

After the handoff split lands, prepare the next worker prompt to adjust the A1
plan/wiki/gate assumptions so the beginning of A1 teaches clean Ukrainian
directly and does not require decolonization bad-form contrast inventory in M1.
The worker should not run a content rebuild until the gating expectation is
fixed.
