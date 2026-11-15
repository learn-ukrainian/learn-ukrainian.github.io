# Grok QA bot (eggbot) — tasked fleet seat (#6742)

**Audience:** drivers who need UI QA, design review, UX review or a retest.
**Status:** operator order EGGBOT-FLEET-1112 (C-5336, 2026-11-12). Eggbot is a fleet member. It is not a `dispatch.py` agent and not a review of record.
**Related:** Grok coding and review = [`model-assignment.md`](../../agents_extensions/shared/rules/model-assignment.md); roster = [`docs/best-practices/agent-activity-matrix.md`](../best-practices/agent-activity-matrix.md) §2. The send procedure is the infra-private runbook `docs/runbooks/bot-gateway.md` (name only; this public page has no host, tunnel or credential detail).

## Role

Eggbot (the Grok QA bot) does UI QA, design review, UX review and retesting (C-5336).

Task it with `bot_gateway.py send`, the CTO's local send helper in the bot-gateway role. It wakes by webhook, works through a read-only UI tunnel, and replies on Fleet Comms to `claude-cto`:

```text
EGGBOT-RESULT id=<task> status=<done|partial|blocked>
```

It keeps a daily safety check. Every UI change that lands locally gets an eggbot retest before anything goes public (C-5346).

It must never:

- merge PRs
- run `scripts/dispatch.py`
- act as a review of record
- write the primary checkout

It is not a second Grok orchestrator and not a substitute for cross-family PR review.

## Not a dispatch agent

Grok 4.7 coding and code/infra review go through the Cursor seat:

```bash
.venv/bin/python scripts/dispatch.py dispatch --agent cursor --model grok-4.7-high
```

`dispatch.py` rejects `--agent grok`. grok-4.6 and grok-4.5 stay retired. Grok holds no driver, Ukrainian, advisory, or high/critical final-signoff seat (C-5307).

Eggbot stays a separate tasked seat:

- Do **not** add `--agent grok-bot`
- Do **not** add `ask-grok-bot`
- Do **not** give it a registry adapter

## How a result enters the fleet

1. A driver tasks eggbot with `bot_gateway.py send`. Follow `docs/runbooks/bot-gateway.md` in the infra-private tree.
2. Eggbot replies `EGGBOT-RESULT` to `claude-cto` over Fleet Comms, with `status` of `done`, `partial` or `blocked`.
3. If eggbot ever authors a PR, same-family Grok must not review it. Route that review to an outside family.

## Approvals and privacy

| Action | Allowed? |
| --- | --- |
| UI QA, design review, UX review, retest, through `bot_gateway.py send` | Yes (default path) |
| Reply `EGGBOT-RESULT` to `claude-cto` | Yes |
| Merge, dispatch, or review of record | **No** |
| Secrets, private names, or raw addresses in public issues or comments | **Never** |

## History

Before C-5336, eggbot was an external observer that filed labeled GitHub issues for drivers to consume (operator GO 2026-08-14). That path is not the current tasking path. Public examples from that period: [#6717](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6717) and the 2026-08-13 review batch [#6760](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6760)–[#6768](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6768).

Parent: #6742.
