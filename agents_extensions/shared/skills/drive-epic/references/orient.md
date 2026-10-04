# Orient, inbox watcher, topology (drive-epic §0, §0b, §1)

Read at cold start and whenever you lose track of fleet state. The §0a inbox drain
itself is stated once in the core `SKILL.md` loop.

## §0. Orient

```bash
.venv/bin/python -m scripts.fleet_comms cold-start-board   # cold-start first action
curl -sS --max-time 2 "http://127.0.0.1:8765/api/orient?lean=true" || true
curl -sS --max-time 2 "http://127.0.0.1:8765/api/work/v1/projection" || true  # best-effort: local server, degraded/absent sources are normal
curl -sS --max-time 2 "http://127.0.0.1:8765/api/work/v1/next?stream=<your-stream>" || true  # stream-scoped pick list (#6880)
.venv/bin/python -m scripts.fleet_comms plane-status        # message-plane mode/parity
.venv/bin/python -m agents_extensions.shared.session_streams dual-write-status
```

`cold-start-board` probes fleet, plane, and stream state so you orient from live data,
never memory. Implemented plane modes are `off | shadow | dual_write | authority` — do not
hard-code a mode in prose; always query it fresh.

Know your `SESSION_EPIC`, your stream, and your handoff slot (the launcher already
claimed the stream lease — do **not** open or resume it yourself). Session health is
**seat-specific** and is not an ordinary cold-start mint: only the Codex launcher mints
its own startup canary; **grok / kimi** run
`.venv/bin/python -m scripts.session_canary.{grok,kimi}_lane` mint/score only
within the `thread-rollover` procedure; **gemini** fails closed — do not run
`gemini_lane` mint or score until an independently reviewed lease-safe runtime repair
lands (its score path closes the session after a failed score or blocked hydration);
halt the affected continuation, preserve handoff and session state, and leave
disposition to the supervisor; **Claude / Sonnet** have **no** canary lane and
use the native SessionStart / PostCompact hook chain + thread-handoff instead (do not
call a non-existent `<model>_lane`).

**Work-board orientation surface:** `GET http://127.0.0.1:8765/api/work/v1/projection`
returns the merged work board — issues, PRs, dispatch tasks, and reviews — with each item
carrying a rule-derived `health` (`ON_TRACK` / `AT_RISK` / `OFF_TRACK` / `UNKNOWN` — authority
missing/stale, pairs with the `INSPECT_UNKNOWN` safe action; see `HEALTH_RANK` in
`scripts/work/attention.py`), an `attention_rank`, and a `safe_next_action`. Query it at orient
and again when picking the next unblocked action (§2); it is a queue INPUT alongside your
stream/GH/issue sources, never a replacement for them.

**Stream next-queue:** `GET http://127.0.0.1:8765/api/work/v1/next?stream=<your-stream>`
returns a compact, stream-scoped actionable pick list (default `limit` 7). Consult it at orient
and next-action time alongside the projection — also a queue INPUT, never a replacement. Cold
(absent) cache → `503` `building` + `retry_after_s` (does not trigger a build); unknown
`stream` → `400` with `valid_streams`.

**Entire cold-start companion (not a substitute for the file handoff):** after orienting,
run `.venv/bin/python -m scripts.entire_context status` and
`search --query "<path-or-sha-needle>"` (and optional `handoff --query`) so promoted SHAs
surface before dispatch. Ranking is **one substring** (prefer path tokens like `practice`
or a full SHA — not multi-word sentences). Empty search = nothing indexed for that needle;
`handoff --query` with zero hits may return `seed_invalid` — use `--locator-id` from
bootstrap/search instead. Fall through to GH issues + file handoff.

## §0b. Optional Monitor inbox-watcher wakeup — cold start only

At cold-start, **if your harness has a Monitor-equivalent**, invoke it once with that
harness's `persistent`/timeout option, pointed at this one shell command:

```bash
scripts/ai_agent_bridge/inbox_watch.sh "$SESSION_HANDOFF_AGENT"
```

This is a **wakeup signal only**: each stdout line says that an unconsumed legacy
message exists, with its id, sender, request id, and a bounded preview. It never reads
the full body into your context and never marks a message consumed. You still must run
the required §0a / §4a / §5a / §8a inbox drains in the core loop to read, apply, and
explicitly live-consume everything the signal points at; those drains remain the
universal fallback for every seat, watcher or not.

Direct confirmation exists only for **Claude Code, Gemini/AGY, and Grok CLI**. For any
other harness, ask the running agent directly whether it has an equivalent before using
one; do not infer it from documentation or `--help`. Stop a running watcher cleanly
with `scripts/ai_agent_bridge/inbox_watch.sh --stop "$SESSION_HANDOFF_AGENT"`; if a
crashed process leaves a stale pidfile, the operating system releases its advisory lock
and the next watcher replaces the recorded pid safely.

## §1. Read topology + metrics (don't hold state — query it)

```bash
.venv/bin/python -m scripts.fleet_comms metrics        # efficiency metrics (no content)
.venv/bin/python -m scripts.fleet_comms backlog        # pending/dispatched delivery
.venv/bin/python -m scripts.fleet_comms dead-letters   # stuck deliveries
```

Fleet-comms externalizes topology + usage so you decide against fresh state, not a
stale in-context snapshot. Per-lane budget health and the pace check before dispatch are
in `routing-and-dispatch.md` § Live capacity.
