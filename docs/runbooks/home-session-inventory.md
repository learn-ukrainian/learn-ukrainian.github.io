# Home session inventory

Use the inventory to inspect the local agent-session stores covered by #4956.
It reports each provider-home root's size and age, then lists only stale files
inside the session allowlist. It never treats a provider root or configuration
file as a deletion candidate.

```bash
.venv/bin/python scripts/hygiene/inventory_home_sessions.py --json
```

The fixed provider allowlist is intentionally small:

- `~/.codex/sessions` and `~/.codex/archived_sessions`;
- `~/.claude/projects`;
- `~/.cursor/chats`;
- `~/.grok/sessions` (the documented peer in lane-retention policy).

The default retention boundary is 14 days. Missing roots are reported; they are
not created. Symlinked homes, session roots, and files are skipped.

## Scheduled policy check

The existing local Git-hygiene LaunchAgent runs every four hours and now invokes
the inventory in read-only mode. Its receipt reports, for each provider lane,
the total allowlisted session-file count and provider-root bytes plus stale
file count and stale bytes. The #4956 policy threshold is **14 days** and the
allowed stale budget is **0 files / 0 bytes**: any stale allowlisted session
file prints a `HARD WARNING`. An existing but unmeasurable provider root also
prints a hard warning rather than being treated as compliant.

Run the same observation manually:

```bash
.venv/bin/python scripts/hygiene/home_session_retention_check.py --json
```

This check has no apply option, does not read `LU_HOME_SESSION_APPLY`, and never
archives or deletes anything. Applying archive or deletion remains exclusively
behind the inventory command's `--apply` plus `LU_HOME_SESSION_APPLY=1` gate.

## Apply

Apply is deliberately double-gated. It requires both `--apply` and the exact
environment variable `LU_HOME_SESSION_APPLY=1`. Without that variable the
command exits before scanning or mutating.

Archive is the default apply action and moves only freshly revalidated stale
session files to the supplied archive root. Deletion is explicit:

```bash
LU_HOME_SESSION_APPLY=1 .venv/bin/python scripts/hygiene/inventory_home_sessions.py \
  --apply --archive-root "$HOME/Library/Application Support/learn-ukrainian/home-session-archives"

LU_HOME_SESSION_APPLY=1 .venv/bin/python scripts/hygiene/inventory_home_sessions.py \
  --apply --action delete --retention-days 30
```

Before every mutation, the command revalidates that the path is a regular file
under one of the allowlisted session subtrees and still older than the selected
retention boundary. It does not remove directories, provider configuration,
symlinks, or any file outside the listed paths.
