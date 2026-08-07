# Hramatka Driver Queue Contract

Cold-start queue contract for anyone driving the Hramatka epic (public
[#4542](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4542))
across the public/private repo split. Authority: the 2026-08-07 stream-hygiene
consult (`batch_state/hramatka-drive/CONSULT-VERDICT-stream-hygiene-2026-08-07.md`,
gitignored local evidence; ACP conversation
`conversation_7b6241377cd44c7ea5265da5c85efb5c`, claude/codex/agy/kimi converged
spine, PR-1 of a 4-PR package). PR-2 adds the Hramatka-only scope gate below;
`post_task_reap` and `hygiene_check` remain separate PR-3/PR-4 work.

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

Private #360 and #212 remain `ESCALATE` because they are operator-only host
mutation work. This PR intentionally does not add a self-asserted GO/override
flag: a verified operator authorization belongs in its own audited workflow.

## Operator-only items — track/escalate, never action solo

Private [#360](https://github.com/learn-ukrainian/learn-ukrainian-infra-private/issues/360)
and [#212](https://github.com/learn-ukrainian/learn-ukrainian-infra-private/issues/212)
require host mutation. A driver without an explicit operator GO for the specific
mutation must **ESCALATE** — track the item and surface it, do not action it.
This is not a bare refuse: the item stays visible and owned, it does not drop
out of the queue.

## Same-session correction rule

If #349 and any other view of the queue (a cached handoff note, a stale reading
of #4542, an out-of-date driver's own memory) disagree, **#349 wins**. Correct
the other view in the same session — do not carry the disagreement forward or
defer the fix to a later PR.

## What this contract does not change

- No `post_task_reap` or `hygiene_check` code ships here.
- No product/teacher-facing features.
- No private-repo secrets or private task titles are mirrored here beyond bare
  issue numbers.
