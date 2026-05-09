# Codex dispatch brief — #1838 bridge ack-step + drop sender self-fanout

**Why this matters now:** Codex Desktop's Automations feature (per the new ADR addendum at `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` § "Codex Desktop Automations") is the canonical path for autonomous orchestrator → Desktop participation. **The Automation prompt requires a clean `ab inbox ack <delivery_id>` CLI** — without it, every automation run leaves the delivery `pending` forever and the inbox warning recurs. Until this lands, the Automation has to call internal `_channels.mark_delivery()` from inline Python, which is ugly and bypasses the bridge's CLI surface.

Separately, every `ab discuss` run today leaks 3-12 stale deliveries because synchronous discuss has no terminal ack step + channel posts fan out to the sender as well as recipients. This issue addresses both.

## Worktree (already prepared by dispatcher)

You start in `.worktrees/dispatch/codex/1838-bridge-ack-and-no-self-fanout/` on branch `codex/1838-bridge-ack-and-no-self-fanout`, branched from `origin/main`. Do NOT `cd` out, do NOT create a new branch in the main checkout.

## Goal

Ship three small changes that together close out the inbox-pending-forever pattern:

1. **`ab inbox ack <delivery_id>`** — new CLI subcommand for explicit per-delivery ack. Calls `_channels.mark_delivery(delivery_id, "delivered", error=...)`.
2. **Drop sender self-fanout** — when a channel post is created, do NOT generate a delivery row for `to_agent == from_agent`. Agents don't need to "process" their own replies.
3. **`ab discuss` acks the deliveries it creates on convergence** — one pass at end of `discuss` over the deliveries it produced, marking them `delivered` with `error="acked by ab discuss orchestrator (round N)"`.

Plus tests + docs.

## Files to touch

### 1. `scripts/ai_agent_bridge/__main__.py` — new `inbox ack` subcommand

The `inbox` subparser already has `run` and `show`. Add a third: `ack`.

Read the existing structure (search for `def _add_inbox_subparser` or similar), then add:

```python
ack_parser = inbox_subparsers.add_parser(
    "ack",
    help="Mark a delivery as delivered without spawning the agent (manual operator drain or post-handling ack from automations / external workers)",
)
ack_parser.add_argument(
    "delivery_id",
    help="Delivery ID to mark delivered (long form, from `ab inbox show <agent>`)",
)
ack_parser.add_argument(
    "--error",
    default=None,
    help="Optional ack note recorded in deliveries.error (e.g. 'processed by codex-desktop automation')",
)
ack_parser.set_defaults(handler=_handle_inbox_ack)
```

Implement the handler:

```python
def _handle_inbox_ack(args: argparse.Namespace) -> int:
    """Explicit ack of one delivery. Used by automations + manual operator drain."""
    from ai_agent_bridge import _channels as ch
    # Verify delivery exists + is in a state we can ack.
    # (Reading the DB directly is OK here — it's the bridge's own DB.)
    import sqlite3
    db_path = ch.default_db_path() if hasattr(ch, "default_db_path") else _resolve_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT delivery_id, status, to_agent, message_id "
            "FROM deliveries WHERE delivery_id=?",
            (args.delivery_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        print(f"❌ delivery_id {args.delivery_id!r} not found", file=sys.stderr)
        return 1
    if row["status"] == "delivered":
        print(f"⚠️  delivery {args.delivery_id} is already 'delivered' (no-op)")
        return 0
    note = args.error or "explicitly acked via `ab inbox ack`"
    ch.mark_delivery(args.delivery_id, "delivered", error=note)
    print(f"✅ delivery {args.delivery_id} → delivered  (to={row['to_agent']}, message={row['message_id']})")
    return 0
```

Match the project's argparse + handler style — read 50 lines around the existing `inbox run`/`inbox show` registration first.

### 2. Drop sender self-fanout — channel post path

Find the function in `scripts/ai_agent_bridge/_channels.py` that inserts `deliveries` rows after a `channel_messages` insert. Likely named `_create_deliveries_for_message`, `post_to_channel`, or similar. Search:

```bash
grep -n "INSERT INTO deliveries\|insert.*deliveries\|mk_delivery\|create_delivery" scripts/ai_agent_bridge/_channels.py
```

In that function, when iterating over recipient agents, **skip the row whose recipient agent equals the message sender** (`from_agent`). Keep a comment explaining why:

```python
# Skip sender self-fanout: an agent does not need to "process" its own
# reply. This eliminates the 3-12 stale deliveries that ab discuss leaves
# behind on every multi-round run, and matches the intent of channel
# posts (they are for OTHER subscribers).
if recipient == channel_message["from_agent"]:
    continue
```

This is a behavior change that may affect existing callers. Search for tests that assert on self-fanout deliveries:

```bash
grep -rn "to_agent.*from_agent\|self.*fanout\|own.*delivery" tests/test_channels*.py tests/test_bridge*.py
```

Update any test that asserts the old (buggy) behavior.

### 3. `ab discuss` acks its own deliveries on convergence

Find the `discuss` orchestrator function (likely `_handle_discuss` or `run_discussion` in `_channels_cli.py` or `_discuss.py`). After the orchestrator collects the round-N reply from agent X and inserts the resulting `channel_messages` row, ack the deliveries that were just created.

Two reasonable implementation shapes:

a. **Per-round ack:** after each round's posts settle, ack all deliveries whose `message_id` is in the just-inserted set. Cleaner — keeps the loop tight.
b. **End-of-discussion ack:** at the end of the `discuss` run, single pass over all deliveries created during the run.

Either works. Pick (a) if it doesn't add too much code; (b) is simpler.

The error note should be informative:

```python
ch.mark_delivery(
    delivery_id,
    "delivered",
    error=f"acked by ab discuss orchestrator (thread={thread_id[:8]}, round={round_index})",
)
```

### 4. Tests

Add to `tests/test_channels_inbox.py` (or wherever inbox tests live):

- `test_inbox_ack_marks_delivery_delivered` — create a pending delivery, run `ab inbox ack <id>`, assert status is `delivered` and error is recorded.
- `test_inbox_ack_unknown_delivery_id_errors` — run with garbage id, assert exit code 1 + error message.
- `test_inbox_ack_already_delivered_is_noop` — ack twice, second call exits 0 with "already delivered" message.

Add to `tests/test_channels_post.py` (or wherever post tests live):

- `test_channel_post_does_not_fanout_to_sender` — post from agent X to a channel that includes X as a subscriber, assert no `deliveries` row exists with `to_agent=X` for that message.
- `test_channel_post_still_fans_out_to_other_subscribers` — same setup, assert the OTHER subscribers get deliveries.

Add to `tests/test_channels_discuss*.py`:

- `test_discuss_acks_its_own_deliveries_on_convergence` — run a 2-round discussion, assert all deliveries created during the discuss run are `delivered` after it returns (`SELECT COUNT(*) FROM deliveries WHERE message_id IN (...) AND status='pending'` is 0).

Existing tests must still pass. If any existing test asserts on self-fanout (unlikely, but possible) or on post-discuss pending deliveries (also unlikely), update them.

### 5. Docs

Add a short entry to `docs/best-practices/agent-bridge.md` under the "Inbox management" or equivalent section:

```markdown
## Explicit ack: `ab inbox ack <delivery_id>`

When an external worker (Codex Desktop Automation, manual operator drain,
external service) processes a delivery without going through `ab inbox run`,
ack it explicitly:

    ab inbox ack <delivery_id> [--error "processed by <thing>"]

Without an explicit ack, deliveries stay `pending` forever and the inbox
warning recurs.

`ab discuss` now acks its own deliveries on round convergence
automatically — no manual intervention needed for that path.
```

## Acceptance criteria

- [ ] `ab inbox ack <delivery_id>` exists and ✅-marks an existing pending delivery as `delivered`.
- [ ] `ab inbox ack <unknown>` errors with exit 1 + clear message.
- [ ] `ab inbox ack <already-delivered>` exits 0 with no-op message.
- [ ] `ab inbox ack --error "..."` records the note in `deliveries.error`.
- [ ] Channel posts no longer fan out to the sender (verified by SQL: `SELECT COUNT(*) FROM deliveries d JOIN channel_messages m ON d.message_id=m.message_id WHERE d.to_agent=m.from_agent` is 0 for messages created post-this-PR).
- [ ] `ab discuss` run leaves zero pending deliveries from the message_ids it created (verified by `ab inbox show <agent>` for each participant).
- [ ] All new tests in §4 pass.
- [ ] All existing tests still pass.
- [ ] Docs entry added per §5.

## Numbered execution steps

1. **Verify worktree** — `git rev-parse --abbrev-ref HEAD` must print `codex/1838-bridge-ack-and-no-self-fanout`. If not, STOP.

2. **Read context** — `scripts/ai_agent_bridge/_channels.py` (post path + `mark_delivery`); `scripts/ai_agent_bridge/__main__.py` (existing `inbox` subparser); `scripts/ai_agent_bridge/_channels_cli.py` or `_discuss.py` (the discuss orchestrator); existing channel + inbox tests.

3. **Implement §1** (new CLI). Add the subparser registration + handler. Test manually:
   ```
   .venv/bin/python scripts/ai_agent_bridge/__main__.py inbox ack --help
   ```

4. **Implement §2** (no self-fanout). Find the post path, add the skip, comment why. Search for any test that asserted on the old behavior.

5. **Implement §3** (discuss ack). Pick per-round or end-of-discussion. Add the ack call.

6. **Implement §4** (tests). Five new tests minimum. Run them:
   ```
   .venv/bin/pytest tests/test_channels_inbox.py tests/test_channels_post.py tests/test_channels_discuss_resume.py -v
   ```

7. **Implement §5** (docs).

8. **Run full bridge test suite** to catch regressions:
   ```
   .venv/bin/pytest tests/test_channels*.py tests/test_bridge*.py tests/test_ai_agent_bridge*.py -v
   ```

9. **Lint** — `.venv/bin/ruff check scripts/ai_agent_bridge/ tests/`.

10. **Commit** — single conventional commit:
    ```
    feat(bridge): ab inbox ack CLI + drop sender self-fanout + ab discuss acks own deliveries (#1838)

    Three small changes that together close out the inbox-pending-forever
    pattern that nags every ab discuss + every Codex Desktop Automation run.

    - `ab inbox ack <delivery_id>` — new CLI subcommand for explicit
      per-delivery ack. Used by external workers (Codex Desktop
      Automations, manual drain) that process a delivery without going
      through `ab inbox run`.
    - Channel post path no longer fans out to the sender. Agents do not
      need a "process your own reply" delivery — that was 3-12 stale
      deliveries per ab discuss run, all noise.
    - ab discuss acks the deliveries it creates on round convergence,
      with an informative error note. Matches the synchronous-discuss
      contract (work is done in-process, no external worker needs to
      pick the deliveries up later).

    Closes #1838
    Refs Multi-UI ADR (Codex Desktop Automations strand)
    ```

11. **Push** — `git push -u origin codex/1838-bridge-ack-and-no-self-fanout`.

12. **Create PR** — `gh pr create --title "feat(bridge): ab inbox ack CLI + drop sender self-fanout + ab discuss acks own deliveries (#1838)" --body "..."`. Reference this brief. Do NOT enable auto-merge.

## What NOT to do

- Do NOT add a `seen_at`/`read_at` column to deliveries. That was floated as a future refinement in the design discussion but is out of scope here.
- Do NOT touch the legacy `messages` table or `mcp__message-broker__*` tools. This issue is about `deliveries` + `channel_messages` only.
- Do NOT change `mark_delivery()` itself. The API is fine; we're adding a CLI surface on top.
- Do NOT enable auto-merge.
- Do NOT add a `--ack-delivery <id>` flag to `ab post`. That was discussed as a future bonus; not in scope here. Single-purpose `ab inbox ack` is enough.

## Output expected

A single PR on branch `codex/1838-bridge-ack-and-no-self-fanout` ready for review. PR body must include:
- The 3 ACs verified (CLI works, no self-fanout, discuss-acks).
- Output of the `ab inbox show <agent>` for `claude` / `codex` / `gemini` after running a fresh `ab discuss` test, showing 0 pending.
