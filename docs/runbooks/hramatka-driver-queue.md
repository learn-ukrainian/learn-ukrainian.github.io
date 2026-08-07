# Hramatka Driver Queue Contract

Cold-start queue contract for anyone driving the Hramatka epic (public
[#4542](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/4542))
across the public/private repo split. Authority: the 2026-08-07 stream-hygiene
consult (`batch_state/hramatka-drive/CONSULT-VERDICT-stream-hygiene-2026-08-07.md`,
gitignored local evidence; ACP conversation
`conversation_7b6241377cd44c7ea5265da5c85efb5c`, claude/codex/agy/kimi converged
spine, PR-1 of a 4-PR package). This is PR-1 of that package: **docs/rules only.**
No `stream_fence` / `post_task_reap` / `hygiene_check` code — that is PR-2 through
PR-4 of the same package.

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

- No `stream_fence`, `post_task_reap`, or `hygiene_check` code ships here.
- No product/teacher-facing features.
- No private-repo secrets or private task titles are mirrored here beyond bare
  issue numbers.
