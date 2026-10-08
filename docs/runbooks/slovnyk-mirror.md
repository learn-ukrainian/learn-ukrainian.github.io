# Resumable slovnyk mirror

Run the foreground shared-cache builder with exactly one writer. Keep other
enrichment writers stopped during an operational handover. The accountable driver
owns live measurement, reviewed-code restart and retained-work verification.

```bash
.venv/bin/python -m scripts.lexicon.build_slovnyk_mirror --manifest manifest.json --progress-every 25
```

Keep stdout attached to the pane. The builder also appends the same progress to
`batch_state/slovnyk-mirror/<target-digest>.log` under the repository root,
independent of the launch directory; redirecting stdout hides pane
progress. `--log-file` overrides the log location, and `--checkpoint` overrides
the default `LEXICON_SLOVNYK_CACHE/.mirror-checkpoint` JSON state file. Its name
and lock suffix stay outside cache consumers' `*.json` glob. Explicit checkpoint
paths remain supported; keep JSON-named state outside the cache directory.

Startup announces validation before scanning caches and reports scan counts,
verified complete lemmas, attempted fetch lemmas, partial lemmas, lookup counts,
rate and ETA. Fetch progress follows the same format. The denominator comes from
distinct lemmas in the selected manifest and the currently configured dictionary slugs;
`--limit` caps the initial manifest selection but does not shrink that denominator.
`fetched`, `reused`, `misses`, `errors` and `pending` partition lookup accounting.
Errors are unresolved work even though they are counted separately from pending.
If another alias durably resolves an earlier failed lookup during the run, final
accounting moves that alias lookup from `errors` to `reused`. It does not count
the shared publication as another fetch or miss.
Only `verified_complete` proves fully resolved lemmas; attempted is never completion.

Every startup checks the actual cache schema, normalized lookup identity, filename,
provenance timestamp and dictionary rows. Current valid positives are adopted
without a checkpoint. Legacy nulls have no transport evidence and remain retryable.
Newly observed 404s are stored with identity-bound `not_found` evidence. A lemma
is complete only when every configured slug has a valid positive or observed miss.
Missing slugs alone are fetched; transient failures are not published as misses.
Input/configuration changes trigger validation, and changed, missing or stale cache
rows cannot inherit checkpoint completion. Invalid checkpoint JSON or unsupported
checkpoint versions stop the run; preserve the state for diagnosis before retrying.
Same-lookup lemma aliases share validated rows without replacing completed cache
bytes or repeating requests. Distinct lookup identities sharing a filename fail
closed before overwrite. Final completion and checkpoint digests are revalidated
against the current durable cache; earlier scan results cannot prove completion.
Collision failures report `reason=cache-filename-collision` and
`action=resolve-distinct-lookup-identities-before-retry`, without emitting raw
lookup identities or filenames. Check the manifest and retained cache locally
for distinct identities mapped to the same sanitized filename; resolve the
conflict before retrying. The diagnostic does not authorize cache deletion.

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
