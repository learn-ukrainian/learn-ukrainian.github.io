# Home session inventory

Use the inventory to inspect allowlisted local agent-session stores. It
reports sizes and ages and identifies stale session files. Provider roots and
configuration files are never deletion candidates. Keep provider-home paths,
account mappings and raw inventory output in private operational evidence.

Run from the project checkout with its configured project interpreter:

```bash
.venv/bin/python scripts/hygiene/inventory_home_sessions.py --json
```

Missing roots are reported rather than created. Symlinked homes, session
roots and files are skipped. The tracked command defines the allowlist; do
not expand it to include credentials, configuration or unrelated files.

## Scheduled policy check

The read-only retention check compares allowlisted session files with the
approved local retention policy. Use the private runbook for the schedule,
retention boundary and stale-file budget. Unmeasurable stores are unknown,
never evidence of compliance.

```bash
.venv/bin/python scripts/hygiene/home_session_retention_check.py --json
```

The check never archives or deletes files. Review its sanitized result before
requesting any mutation; keep paths and raw receipts private.

## Apply

Mutations require explicit authorization and both of the inventory command's
apply gates. Read the command's help before preparing an authorized archive
operation:

```bash
.venv/bin/python scripts/hygiene/inventory_home_sessions.py --help
```

Choose an approved archive destination and retention boundary through the
private procedure. Archive is the default action; deletion requires a
separate explicit choice. Before each mutation, the command revalidates that
the candidate is a regular file inside an allowlisted subtree and still
older than the selected boundary. It does not remove directories, provider
configuration, symlinks or files outside the allowlist. Verify the receipt
before treating an archive as recoverable.

Operational details are in the private infra repository's `runbooks/home-session-inventory.md`.
