# Resumable slovnyk mirror

Run the foreground shared-cache builder with exactly one writer. Keep other
enrichment writers stopped during an operational handover. The accountable driver
owns live measurement, reviewed-code restart and retained-work verification.

```bash
.venv/bin/python -m scripts.lexicon.build_slovnyk_mirror --manifest manifest.json --progress-every 25
```

Keep stdout attached to the pane. The builder also appends the same progress to
`batch_state/slovnyk-mirror/<target-digest>.log`; redirecting stdout hides pane
progress. `--log-file` overrides the log location, and `--checkpoint` overrides
the default `LEXICON_SLOVNYK_CACHE/.mirror-checkpoint.json` state file.

Startup announces validation before scanning caches and reports scan counts,
verified complete lemmas, attempted fetch lemmas, partial lemmas, lookup counts,
rate and ETA. Fetch progress follows the same format. The denominator comes from
distinct lemmas in the selected manifest and the currently configured dictionary slugs;
`--limit` caps the initial manifest selection but does not shrink that denominator.
`fetched`, `reused`, `misses`, `errors` and `pending` partition lookup accounting.
Errors are unresolved work even though they are counted separately from pending.
Only `verified_complete` proves fully resolved lemmas; attempted is never completion.

Every startup checks the actual cache schema, lemma, normalized lookup identity,
provenance timestamp and dictionary rows. Current valid positives are adopted
without a checkpoint. Legacy nulls have no transport evidence and remain retryable.
Newly observed 404s are stored with identity-bound `not_found` evidence. A lemma
is complete only when every configured slug has a valid positive or observed miss.
Missing slugs alone are fetched; transient failures are not published as misses.
Input/configuration changes trigger validation, and changed, missing or stale cache
rows cannot inherit checkpoint completion. Invalid checkpoint JSON or unsupported
checkpoint versions stop the run; preserve the state for diagnosis before retrying.

Cache results are written to unique sibling temporary files, flushed and fsynced,
then atomically replaced and the directory fsynced. Checkpoints use the same
ordering, after data publication, at progress boundaries and graceful termination.
If interrupted before checkpoint publication, restart adopts the durable data.
A failure before replacement preserves the previous cache bytes. Temporary files
left by an uncatchable process kill are never read as cache or checkpoint data.

Persistent advisory lock files refuse overlapping mirror runs sharing a cache
or checkpoint. Do not unlink lock files: the operating system releases admission
when the process exits, including a crash. Other enrichment writers must respect
the operational single-writer handover; atomic publication does not grant them
permission to run concurrently with the mirror.

Exit 0 means verified complete, including an empty manifest. Exit 1 covers limited,
partial, offline-pending, invalid-state and storage/access/parse failures; exit 2
is invalid usage; exit 130 and `status=interrupted` indicate SIGINT or SIGTERM.
An uncatchable kill cannot print a terminal summary, but restart remains safe.
Headers, pacing, retry and access-block handling are unchanged.

Offline author probes must set `LEXICON_SLOVNYK_CACHE` to synthetic storage before
importing either mirror or enrichment, use synthetic manifests, and keep checkpoint
and log destinations local to the dispatch worktree. Never probe live payloads.
