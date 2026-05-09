# Codex dispatch brief — #1779 bridge inbox TTL + auto-drain + orient surfacing

**Background:** Bridge inbox is purely pull-based. Deliveries sit `pending` indefinitely if nobody runs `ab inbox run <agent>`. Real-world consequence (2026-05-07): 4 deliveries pending across 3 agents, oldest 2.3 days old. Including a substantive PR re-review request that became meaningless because the PR had ALREADY merged.

Read full issue body via `gh issue view 1779`. The issue lays out P0/P1 priorities clearly.

## Worktree

You start in `.worktrees/dispatch/codex/1779-bridge-inbox-ttl/` on branch `codex/1779-bridge-inbox-ttl`. Do NOT `cd` out.

## Scope (P0 only — defer P1+ to follow-up)

### P0a — TTL / auto-expire

- Add a configurable `max_age_hours` per channel in `channels` table (default `24`).
- A janitor function `expire_stale_deliveries()` in `_channels.py` marks `pending` deliveries older than the channel's TTL as `expired` with `error="auto-expired (>${max_age_hours}h pending, channel=${channel})"`.
- Run the janitor at the top of `inbox show` and `inbox run` so visible state is fresh.
- Add `ab channel set-ttl <channel> <hours>` CLI for manual configuration.

### P0b — Surface in `/api/orient`

- Add `bridge_pending` field to `/api/orient` response showing per-agent pending counts + oldest-age-hours. Match the issue's example shape:
  ```json
  "bridge_pending": {
    "claude": {"count": 1, "oldest_hours": 6.5},
    ...
  }
  ```
- Update orient.html (or whichever consumer renders this) to display the field. Optional — JSON shape change is the load-bearing part.

## Files

- `scripts/ai_agent_bridge/_db.py` — schema migration (add `max_age_hours` column to `channels` if missing).
- `scripts/ai_agent_bridge/_channels.py` — `expire_stale_deliveries()` janitor + integration into existing inbox-show/run paths + `set_channel_ttl()` helper.
- `scripts/ai_agent_bridge/_channels_cli.py` — new `channel set-ttl` subcommand.
- `scripts/api/state_router.py` (or wherever `/api/orient` lives — search via grep) — add `bridge_pending` field.
- Tests in `tests/test_bridge_*.py`.

## Numbered steps

1. Verify worktree.
2. Read `_db.py` (schema + migration pattern), `_channels.py` (deliveries handling), `_channels_cli.py` (subcommand pattern), `/api/orient` route.
3. Schema: add `max_age_hours INTEGER DEFAULT 24` to `channels` table. Migration in `_db.py`.
4. Implement `expire_stale_deliveries()` — single-pass UPDATE marking pending → expired.
5. Wire janitor into `inbox show` + `inbox run` paths (call before reading state).
6. Add `channel set-ttl` CLI with arg validation (positive int hours).
7. Add `bridge_pending` to `/api/orient` JSON.
8. Tests:
   - `test_expire_stale_deliveries_marks_aged_pending_as_expired`
   - `test_expire_stale_deliveries_respects_channel_ttl`
   - `test_expire_stale_deliveries_skips_already_delivered`
   - `test_channel_set_ttl_persists`
   - `test_orient_includes_bridge_pending_field`
9. Run: `.venv/bin/pytest tests/test_bridge*.py tests/test_state_*.py tests/test_api_*.py -v`. None must regress.
10. Ruff.
11. Commit:
   ```
   feat(bridge): channel TTL + auto-expire + orient surfacing (#1779 P0)

   - channels.max_age_hours column (default 24h); per-channel override
     via `ab channel set-ttl <channel> <hours>`.
   - expire_stale_deliveries() janitor runs at top of inbox show/run,
     marking pending → expired with informative error note.
   - /api/orient now includes bridge_pending field with per-agent
     counts + oldest-age-hours, so the orchestrator sees stale
     deliveries during routine state checks rather than only via
     `channel list`.

   Closes #1779 (P0 scope; P1+ deferred to follow-up issue if needed)
   ```
12. Push + PR. Do NOT auto-merge.

## What NOT to do

- Do NOT delete expired deliveries — keep them in the table with `status='expired'` so audits can see what got dropped.
- Do NOT change the default TTL across existing channels mid-deploy — they all start at 24h, and explicit overrides via `set-ttl` from there.
- Do NOT enable auto-merge.

## Acceptance criteria

- [ ] Schema migration adds `max_age_hours` to `channels`.
- [ ] `expire_stale_deliveries()` correctly transitions stale pending → expired.
- [ ] `inbox show` + `inbox run` invoke the janitor before reading state.
- [ ] `ab channel set-ttl <channel> <hours>` works.
- [ ] `/api/orient` includes `bridge_pending` field per-agent with count + oldest_hours.
- [ ] 5+ new tests covering all the above.
- [ ] All existing tests still pass.
