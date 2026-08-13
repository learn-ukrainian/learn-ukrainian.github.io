# AGENTS.md - Compact Rules for AI Coding Agents

> This is the non-skippable static digest for Codex-family consumers. It is
> deliberately compact: full policy lives in the rules API and the listed local
> sources. Do not load `CLAUDE.md` or `GEMINI.md` during normal Codex startup.

## Read the current rule set

When the local Monitor API is available, read `GET /api/rules?format=markdown`
before consequential work; it is the canonical, complete ruleset. It is served
with the operator contract first and supports hash-based cache checks.

When that API is unavailable, read
`agents_extensions/shared/rules/_load-via-api.md`, then its ordered local
fallback list. Do not invent an alternative policy or treat an unavailable API
as permission to skip rules. The full sources include the operator contract,
critical and non-negotiable rules, workflow, fleet-comms coordination,
worktree, CLI, and model-assignment rules.

## Operator Contract (binding for ALL agents — read before acting)

The binding wording is in
`agents_extensions/shared/rules/operator-expectations.md` (served first by
`/api/rules`). Its items decide conflicts. This inline digest is intentionally
non-skippable:

1. Quality: no shortcuts, threshold-lowering, or “for now”.
2. Use established best practice and fix root causes.
3. Preserve Git/GitHub hygiene: layout A, dispatch worktrees, PRs, and
   `X-Agent` attribution.
4. Use the fleet; the review gate is an independent **cross-family** review,
   not discussion.
5. Route by model × harness fit.
6. Substitute a constrained lane and record that substitution.
7. Make tool-backed claims only; outcome validity precedes paid execution:
   define semantic success and stop criteria; transport, shape, and cost are
   not proof. Verify Ukrainian word, stress, and morphology claims with
   VESUM/`sources`.
8. Keep code and documentation current and clean.
9. Maximize Ukrainian immersion, **EXCEPT A1**.
10. Drive decided work within approved scope.
11. Repository hard gates bind.
12. Do not make architecture, layout, process, or policy decisions without
    present-tense operator or designated-advisor approval.
13. Apply adversarial quality: lead with failure modes and missing evidence.
14. **Pre-dispatch outcome adequacy:** before presenting or dispatching a
    substantive phase/epic, freeze the SHA-256, user outcome, denominator,
    non-goals, role map, independent held-out evaluation, stop/residual policy,
    and completion terms. Prompt review never replaces exact-head
    implementation or cross-family PR review.

## Non-skippable offline execution guardrails

- The primary checkout belongs to the human and services and is read-only for
  agents. Make every implementation edit, branch, commit, and PR only from a
  dispatch worktree at `.worktrees/dispatch/<agent>/<task>/`; never switch the
  primary checkout’s branch.
- For changed agent-rule deploy copies, edit `agents_extensions/` first and
  run the repository deployment check or command required by the full rules;
  never hand-edit deployed `.claude/`, `.codex/`, `.agent/`, or `.gemini/`
  copies.
- Use the project interpreter prescribed by the task/worktree contract for project, shell, and
  production commands; never use bare `python`, `python3`, or `sys.executable` there. Tests that
  spawn a Python subprocess MUST use `sys.executable` (it is the interpreter running under
  `.venv/bin/python -m pytest`).
- Never modify `.python-version`, `.yamllint`, or `.markdownlint.json` to make
  work pass. Fix source instead. Do not commit generated status, audit, review,
  or telemetry artifacts; keep one PR to one concern and under the file cap.
- Do not delete existing files without explicit authorization. Do not weaken, skip, stub, or comment out tests.
  Run the affected checks and report their actual output; distinguish sandbox or harness limits from product failures.
- Never print or commit secrets, credentials, infrastructure details, raw IP
  addresses, or private transcripts. Use only approved, privacy-safe evidence.
- Every commit has an `X-Agent: <agent>/<task-id>` trailer. Change tasks end in
  a pushed PR with CI; never push directly to `main`. Workers neither merge nor
  arm auto-merge. Before merge, required CI and an independent cross-family
  exact-head review must both pass; resolve material findings and re-review.
- Treat unavailable telemetry as unknown, not policy proof. Do not close
  partial work: state verified outcome, denominator, residual gap, and owner.

## Fleet, context, and delegation

- For standalone TUI/UI drivers, read
  `agents_extensions/shared/rules/fleet-comms-coordination.md`; file
  dual-write remains authoritative in every plane mode. Use `plane-status` and
  the `drive-epic` skill; Codex is a coding or review seat, not an epic-driver
  loop. Do not change plane, retention, or formal-review eligibility without
  operator/advisor GO.
- On non-trivial work, use the `entire-context` skill: run status and one
  bounded search before prioritization or dispatch. Treat results as body-free,
  supplemental locators; record use only when a verified locator informed work.
- Before delegation, classify role, task family, track, and owned paths for the
  Project Research Registry. Before every `delegate.py dispatch`, the accountable
  orchestrator records a scoped classification using `--research-role`,
  `--research-task-family`, `--research-track`, and `--research-owned-path`, or
  deliberately classifies it as genuinely generic or unknown and omits all
  `--research-*` flags. A surfaced pointer is not proof of consumption; verify
  attributed consumption before final disposition. Full contract:
  `agents_extensions/shared/rules/workflow.md` § Project Research Registry.
  Give helpers disjoint paths and bounded authority; same-family helpers do not
  satisfy the cross-family review gate.

## Completion

Before claiming completion, inspect the exact diff and status, run proportionate
verification, and report changed files, commands/results, final branch status,
the user-visible outcome, and any residual. Follow the full rules for issue
linkage, PR state, review routing, merge ownership, and cleanup.
