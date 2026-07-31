# Codex rollout state reconciliation

`scripts/hygiene/codex_rollout_reconcile.py` is a project-owned, dry-run-first
health tool for stale `threads.rollout_path` rows. It never changes the
installed Codex CLI or deletes a rollout file.

Eligibility requires an absolute `rollout-*.jsonl` path under the row's
selected `sessions/` or `archived_sessions/` root, a filename ending in its
canonical UUID, an unpinned row, and `updated_at` at least 24 hours old. UUID,
archived, path, symlink, foreign-key, trigger, and unknown-schema mismatches are
protected. A missing rollout root is also suspicious; harmless INSERT/UPDATE
maintenance triggers are accepted, while DELETE or unrecognized triggers are
not. Tests may lower the 24-hour age window.

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

Review `eligible_stale_ids`, each classification, and `eligible_digest`. This
canonical SHA-256 covers sorted eligible fingerprints (`id`, `rollout_path`,
`updated_at`, `pinned`, `archived`) and must be copied exactly with the count;
do not infer either value from another scan or the database.

## Apply

Close Codex and stop every process that can write the selected database. Pass
both reviewed values and acknowledgement. Apply opens the writable database,
enables foreign keys/busy timeout, acquires `BEGIN IMMEDIATE`, then uses a
separate read connection under that lock to create and integrity-check the
backup. It revalidates digest-bound identity and filesystem absence, deletes
matching spawn edges before thread rows, and commits only after those deletes.

```bash
.venv/bin/python scripts/hygiene/codex_rollout_reconcile.py apply \
  --codex-home "$HOME/.codex" \
  --db "$HOME/.codex/state_5.sqlite" \
  --expected-eligible-stale 3 \
  --expected-eligible-digest "64-hex-digest-from-reviewed-scan" \
  --confirm-stale
```

A count or digest mismatch refuses before backup creation or any write, so a
same-count substitution cannot be applied. Changed or newly present candidates
are skipped safely, but a skipped row must still exist for post-apply parity to
pass. The receipt printed to stdout includes the backup path, actual deleted
IDs/count, skipped counts, remaining classifications, SQLite
`integrity_check`, and post-apply parity. If verification fails after commit,
the receipt says `post_commit_verification_failed` and
`mutation_committed: true`; it never reports a successful mutation as a
rollback or as zero deletion.

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
sqlite3 "/absolute/path/to/codex-home/state_5.sqlite" \
  ".restore '/absolute/path/from-the-receipt/state_5-before-reconcile-<id>.sqlite'"
sqlite3 "/absolute/path/to/codex-home/state_5.sqlite" "PRAGMA integrity_check;"
codex doctor --json
```

If the restore or integrity check fails, leave Codex closed and escalate with
the receipt and error output. Never delete rollout JSONL files as part of
reconciliation or rollback.
