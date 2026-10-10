# Seat reliability for drivers and cloud agents

Binding for every epic driver, lane worker and Cursor Cloud agent. These rules add to
`/api/rules`; they do not replace the routing, review or landing rules served there.

## Before you start: Definition of Ready

Do not implement an issue until it carries a complete DoR block: goal, scope,
acceptance criteria, dependencies, data and access, allowed model, verify plan. If it is
missing or incomplete, write the DoR first and stop there; that is the task. Use pstack
for it (`/architect`, or the Multi-phase plan playbook for multi-step work).

## Finish line: Definition of Done plus the done-check

"Closed" is not done. An issue counts as finished only when every DoD item is ticked with
evidence and it passes the done-check:

- a linked PR is merged through the normal landing path;
- CI and the matching verify-* skill or QA run passed on the merged head, with the
  evidence in an issue comment;
- docs are updated, or the issue says "no docs needed";
- cleanup is complete: head branch deleted, worktrees and temp dirs reaped, no stale open
  PRs or branches left for the issue.

Use pstack for the evidence (prove-it-works, verify-* skills). An autopilot or `/loop`
finish condition is "all children pass the done-check", never "all children closed".

## pstack before custom code

If a pstack playbook, skill or principle covers the need, use it. Build custom code only
for a gap, and say in the PR body which gap it fills.

## Escalation

When blocked, try up to 2 different fixes. Then escalate once, in one line, saying exactly
what you need, and move on to other work. Never idle-wait and never re-ask.

## Priority order

Pick the next item in this order: security and OPSEC, then `operator-task` issues, then
broken main or CI, then epic work, then cleanup.

## Ownership

The private ownership map (`docs/ownership-map.md` in the private infra repo) is the
source of truth for which lane owns which area. Every handoff names an owner from it and
confirms receipt. An unowned item goes to the coordinator in the same turn.

## Long jobs

Downloads, evals, backups and builds run detached under `systemd-run` or `tmux` so they
survive a session restart. Never run them inside an interactive session.

## Model budget

Top models stay the default. Model choice per job type follows the measured cost/quality
Pareto line (tracked in the private routing work). Grok and Gemini also take every job
where they sit on or near that line, so their subscriptions get used; they are not a
leftovers tier, and work that needs a top model is never downgraded to them. No Chinese
models on Ukrainian-language work. Haiku stays the default for routine mechanical coding
until the Pareto data says otherwise. Subscriptions before API keys. When a quota runs
out, say so once and switch to the next allowed lane; never stop silently and never
quietly downgrade a protected job (review, architecture, Ukrainian language, security).
