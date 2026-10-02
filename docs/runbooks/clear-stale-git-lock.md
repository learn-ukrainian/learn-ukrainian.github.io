# Clearing a stale Git lock

Issue #8874 tracks the primary checkout lock incident; #8887 adds the manual
removal tool. A Git lock can belong to a live process. Inspect it before any
removal:

```bash
.venv/bin/python -m scripts.ops.clear_stale_git_lock --repo . --dry-run
```

Run from the checkout whose lock failed, or pass that checkout to `--repo`.
The tool accepts `index.lock` by default; `--lock packed-refs.lock` selects
another `.lock` file directly inside that checkout's Git directory. It refuses
nonregular files, recently created or changed locks, and a Git process targeting
that checkout. The lock must have been unchanged for at least ten minutes.
An unreadable Git process is treated as active. The dry run reports eligibility
without removing anything.

Once the dry run reports an eligible lock, repeat with `--apply`. The tool
checks the lock and process list again before removal, then writes a receipt to
stdout (and therefore to the journal when run under systemd). Do not schedule
it automatically; the operator must inspect the failed Git operation first.
