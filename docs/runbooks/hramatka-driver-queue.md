# Hramatka Driver Queue Contract

Cold-start queue contract for anyone driving the Hramatka epic (public
[#4542](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4542))
across the public/private repo split. Authority: the 2026-08-07 stream-hygiene
consult (`batch_state/hramatka-drive/CONSULT-VERDICT-stream-hygiene-2026-08-07.md`,
gitignored local evidence; ACP conversation
`conversation_7b6241377cd44c7ea5265da5c85efb5c`, claude/codex/agy/kimi converged
spine). Scope gate ships with PR-2; settle reaper with PR-3; closeout
`hygiene_check` with PR-4 (this document covers all three surfaces).

## Queue roles

| Queue | Role |
| --- | --- |
| Private BOARD [learn-ukrainian-infra-private#349](https://github.com/learn-ukrainian/learn-ukrainian-infra-private/issues/349) | **Planning/priority queue.** Ownership + ordering for active Hramatka work. |
| Public [#4542](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4542) | **Charter + bare pointer.** Narrative/authorization record, not a live operational checklist. Never auto-generate or mirror a public checklist from the private board — leak + dual-write, explicitly rejected by the consult. |
| GitHub issue/PR state (either repo) | Factual SSOT for what is actually open or closed. #349 is the priority queue, not a duplicate status feed — an item can be closed on GitHub while still ranked on #349, and the reverse. |

## Cold-start read order

1. Private #349 (priority/ownership)
2. Private open PRs
3. Public PRs linked from #4542 only

Do not treat #4542's own body text as a live queue snapshot — read it for
charter/authorization context only.

## New-scope gate

Before a Hramatka driver starts a **new dispatch**, **new scope**, or **new PR**,
run the mechanical gate with a repo-qualified issue target:

```bash
.venv/bin/python -m scripts.fleet.hramatka_scope_gate \
  --action new_dispatch \
  --issue-repo learn-ukrainian/learn-ukrainian.github.io \
  --issue 4542
```

It emits JSON with exactly one of `ALLOW`, `ROUTE`, `HOLD`, or `ESCALATE`; only
`ALLOW` exits zero. `ROUTE` always names its destination, such as
`infra-harness epic #4707`; `HOLD` means stop the new action; `ESCALATE` means
surface the item to the operator. The gate is deliberately not applied to
cleanup, review, escalation, or unblocking the driver's own already-open PR.

Public work must have exact stream membership through Hramatka epic #4542.
Private work must be tracked by private board #349, carry the exact `hramatka`
label, or use an explicit `stream:hramatka` body tag. Ordinary mentions of
Hramatka and any 50%/majority heuristic are not membership evidence. A private
API failure is `UNKNOWN` and therefore `HOLD` for every new-scope action; it
never becomes an implicit allow. The gate has no environment-variable bypass.

Host-mutation work without an explicit operator GO remains `ESCALATE` (see
private #212 residual; private #360 crypto redeploy was completed on-host).

## Closeout hygiene check

Before declaring a Hramatka drive **verified-clean** at handoff, run the
read-only closeout gate:

```bash
.venv/bin/python -m scripts.fleet.hramatka_hygiene_check
# exit 0 verified | exit 1 stale | exit 2 unknown
```

It emits a JSON receipt (`policy_version`, `status`, `epic_charter_ok`,
`queue_pointer_ok`, `zombie_worktrees`, `df`, plus supporting `reasons`) and
never mutates GitHub or the filesystem. Only exit 0 (`verified`) is a clean
handoff:

- **stale** (exit 1) — the public epic #4542 still carries a live (unchecked)
  checklist item, is missing its pointer to private board #349, a registered
  dispatch worktree is bound to an already-terminal task
  (`.worktrees/dispatch/` vs. `batch_state/tasks/`), or local disk use is at
  or above the configured high-water mark (default 95%, `--high-water-percent`).
- **unknown** (exit 2) — GitHub was unreachable for the public epic or the
  private board. This is never a pass.

The gate does not reap orphan worktrees or gate new scope itself — that is
`post_task_reap` (PR-3) and `hramatka_scope_gate` (PR-2) respectively. It only
reports.

## Operator-only items — track/escalate, never action solo

Host mutation without an explicit operator GO must **ESCALATE** — track and
surface, do not freestyle host changes outside the documented deploy path.
Drivers with SSH access still follow the private deploy runbook and record
evidence on the private issue.

## Same-session correction rule

If #349 and any other view of the queue (a cached handoff note, a stale reading
of #4542, an out-of-date driver's own memory) disagree, **#349 wins**. Correct
the other view in the same session — do not carry the disagreement forward or
defer the fix to a later PR.

## What this contract does not change

- No product/teacher-facing features in these process PRs.
- No private-repo secrets or private task titles are mirrored here beyond bare
  issue numbers.
