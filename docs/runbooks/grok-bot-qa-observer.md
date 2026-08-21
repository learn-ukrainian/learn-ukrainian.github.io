# Grok Bot — external QA observer (#6742)

**Audience:** infra/track drivers, operators configuring the Grok Bot app, anyone
tempted to add `--agent grok-bot`.
**Status:** operator GO 2026-08-14 — observer contract only; not a fleet seat.
**Related:** native Grok CLI seat = [`grok-formal-cf-isolation.md`](grok-formal-cf-isolation.md);
roster = [`docs/best-practices/agent-activity-matrix.md`](../best-practices/agent-activity-matrix.md) §2.

## Role

Grok Bot (Cursor/xAI **cloud teammate**, `app/cursor`) is an **external QA
observer**. It reads GitHub Actions / site signals and **files GitHub issues or
comments**. It must **never**:

- merge PRs
- run `scripts/delegate.py` (no dispatch seat)
- act as CF of record
- write the primary checkout (local-computer: **Never** / **Ask** only)

It is **not** a second Grok orchestrator, not a substitute for cross-family PR
review, and not Entire-cloud.

## Not the native `grok` CLI seat

Do **not** confuse Grok Bot with the native Grok CLI / Grok Build lane already
on the roster (`delegate.py --agent grok`, alias `grok-build`).

- No `delegate.py` / registry adapter for Grok Bot
- Do **not** add `--agent grok-bot`
- Do **not** add `ask-grok-bot`
- Auth is the Cursor account, not `XAI_API_KEY`
- No webhook, no plane change, no fleet-comms seat

## How findings enter the fleet

1. Grok Bot files a **labeled** GitHub issue (`infra` / `ci` / `bug` as
   appropriate) — optionally a draft comment first.
2. Infra or track drivers consume those issues through the normal loop.
3. If Grok Bot ever authors a PR, **same-family Grok must not CF it**; route
   CF to an outside-family sealed reviewer.

## Approvals and privacy

| Action | Allowed? |
| --- | --- |
| Draft comment or draft issue | Yes |
| File a labeled issue (observer finding) | Yes (default delivery path) |
| Mutate GitHub beyond filing a labeled issue (extra labels, edits, reviews, merges, force-pushes) | **Human / driver approval required** |
| Secrets, private names, raw IPs in public issues/comments | **Never** |

## Routines (operator configures in the Grok Bot app — not in this PR)

Configure in the Grok Bot product UI; this repo does not encode schedules.

- **Weekday Actions watch** — scan CI/Actions failures and file labeled issues.
- **Optional** `./services.sh status` (or similar live probes) — only with
  explicit local-computer / operator approval; never silent primary-checkout
  writes.

## Presence heartbeat (#7063)

Occupancy cannot infer Grok Bot from a RAM lease. From a loopback Monitor client
(the notebook tunnel to `127.0.0.1`), heartbeat the current issue/PR:

```bash
curl -s -X POST http://127.0.0.1:8765/api/observer/presence \
  -H 'Content-Type: application/json' \
  -d '{"agent":"grok-bot","kind":"observer","task_id":"7061","status":"working","summary":"tunneled Monitor observer sweep"}'
```

`qa-engineer` is also allowed. Repeat at least every 15 minutes while working.
`GET /api/occupancy` then shows the row under `cloud-observer`. Do not POST a
`pid` or `reserved_ram_mb`. Do not treat this as a dispatch seat.

## Evidence (works today)

- Sweep 403 → [#6717](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6717)
- 2026-08-13 review batch: public LU [#6760](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6760)–[#6768](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6768) (`app/cursor`); private hramatka #451–#458 after code review

Parent: #6742.
