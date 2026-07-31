# Codex rollout state reconciliation

`scripts/hygiene/codex_rollout_reconcile.py` is a project-owned, dry-run-first
health tool for stale `threads.rollout_path` rows. It never changes the
installed Codex CLI and never deletes a rollout file.

The tool only considers a missing path eligible when it is an absolute
`rollout-*.jsonl` path below the selected Codex home's `sessions/` or
`archived_sessions/` directory, the row is unpinned, and `updated_at` is at
least 24 hours old. Outside, malformed, recent, pinned, present, and unknown
schema rows are protected. The age window can be lowered for temporary tests,
but the production default is 24 hours.

## Scan

The default operation is a read-only scan. `--db` is optional; without it the
tool selects the newest compatible exact `state_*.sqlite` under `--codex-home`.
Rows and counts are emitted as stable, sorted JSON.

```bash
.venv/bin/python scripts/hygiene/codex_rollout_reconcile.py scan \
  --codex-home "$HOME/.codex" \
  --db "$HOME/.codex/state_5.sqlite"
```

For a read-only health check suitable for automation, fail when eligible stale
rows remain:

```bash
.venv/bin/python scripts/hygiene/codex_rollout_reconcile.py scan \
  --codex-home "$HOME/.codex" --fail-on-stale
```

Review the `eligible_stale_ids` list and the per-row classification. The list
is the confirmation input for the next step; do not infer an apply count from
another scan or from the database directly.

## Apply

Close Codex and stop any process that can write the selected state database.
Then pass the exact `eligible_stale` count from the reviewed scan and the
explicit acknowledgement flag. The tool creates a uniquely named SQLite
backup with restrictive permissions before opening one `BEGIN IMMEDIATE`
transaction. Every candidate is re-read and its ID, path, update time, pin
state, and filesystem absence are checked again inside that transaction.

```bash
.venv/bin/python scripts/hygiene/codex_rollout_reconcile.py apply \
  --codex-home "$HOME/.codex" \
  --db "$HOME/.codex/state_5.sqlite" \
  --expected-eligible-stale 3 \
  --confirm-stale
```

A count mismatch refuses before backup creation or any write. Changed or newly
present candidates are skipped safely. Matching `thread_spawn_edges` are
removed for deleted thread IDs; declared foreign keys handle dependent dynamic
tools. The receipt printed to stdout includes the backup path, deleted and
skipped counts, remaining classifications, SQLite `integrity_check`, and
post-apply parity. Keep that receipt with the backup path for operator review;
the repository does not write receipts or local state files.

## Verify

After apply, run the project check and Codex's own diagnostic while Codex is
closed, then reopen Codex and repeat the scan:

```bash
codex doctor --json
.venv/bin/python scripts/hygiene/codex_rollout_reconcile.py scan \
  --codex-home "$HOME/.codex" --fail-on-stale
```

The scan should report zero unexplained `eligible_stale` rows. Existing
rollouts, pinned/recent rows, suspicious paths, and unrelated thread rows must
remain present.

## Rollback

Rollback is operator-only. First close Codex completely and stop every Codex
process that could open the database. Confirm the backup is the receipt's
backup and has restrictive permissions. Do not restore while Codex is running.

Use SQLite's restore command rather than copying a live database file:

```bash
DB="$HOME/.codex/state_5.sqlite"
BACKUP="/absolute/path/from-the-receipt/state_5-before-reconcile-<id>.sqlite"
sqlite3 "$DB" ".restore '$BACKUP'"
sqlite3 "$DB" "PRAGMA integrity_check;"
codex doctor --json
```

If the restore or integrity check fails, leave Codex closed and escalate with
the receipt and error output. Never delete rollout JSONL files as part of
reconciliation or rollback.
