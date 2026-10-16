# Delegate API

`GET /api/delegate/active` observes hot task records and local worker identity.
It returns one inventory or HTTP 503 with `detail.status: unknown` and a reason.
An unavailable directory, failed read, invalid record, or detected concurrent
change cannot produce a successful empty inventory.

`tasks` contains hot records whose persisted status is `running` or `spawning`,
except `running` records whose worker is proven dead. `total` always equals
`len(tasks)`. There is no page limit. Archive records and `*.snapshots.json`
sidecars are outside this scope. Closeout state objects written by
`scripts/review/closeout_cli.py` are recognized by their complete field set and
field types, independently of filenames. They are counted separately in
`source.closeout_artifacts`. A task or malformed object is never excluded merely
because its filename ends in `.closeout.json` or `-resolve.json`. An identity-only
object without a status remains unclassified and refuses the inventory.
Terminal records are parsed to determine scope. An invalid record anywhere in
the hot denominator prevents a complete inventory.

Every qualifying attempt also appears in `observations`, including excluded
proven-dead running attempts. `source.records_in_scope` counts these observations;
`source.excluded_dead_running` explains the difference from `total`.
`source.records_scanned` counts hot task record files before status and internal
filtering, excluding the separately counted validated closeout artifacts. The internal Python loader accepts an authoritative exact-match
repository predicate before constructing observations and totals. HTTP remains
unscoped. `source.filtered` discloses that distinction without exposing a name.

Legacy task row keys remain available. `alive` is `true`, `false`, or `null`.
`null` means unknown, including a missing PID or incompatible identity visibility.
`spawning` remains a record status even when its process is alive or dead.
Neither record status nor a successful scan confirms that every task is running.

Each observation names `task_id`, the persisted `run_nonce`, `record_status`,
and `alive`. A null nonce means the record supplies no attempt nonce.
`liveness_basis` distinguishes identity records from legacy PID namespace evidence.
`worker_liveness` checks namespace and process start identity for identity-bearing
records. Its shared healer migration fallback still permits a positive signal-zero
result in a confirmed initial PID namespace. The active API qualifies that result
as `alive: null` with `liveness_reason: legacy_worker_identity_unattested` because
PID existence cannot bind the process to the recorded task attempt. Proven-dead
legacy results remain `false`; other unknown identity or visibility results retain
`worker_identity_or_visibility_unknown`. Expected PID range and conversion
errors also produce this explicit unknown. Both process samples use the same API
qualification. This changes no shared healing or terminalization policy, and
unknown legacy records remain in `tasks`, `total`, and `observations`.

`record_updated_at` is the file's actual modification time, not task start time.
`record_observed_at` is the read observation time. `record_age_s` measures the
modification age at scan completion and can be negative for a future file time.
`liveness_observed_at` and `liveness_age_s` describe the first process sample.
The task row's existing `age_s` still measures time since `started_at`.

`source.scan_started_at` and `source.observed_at` bound the scan interval.
`source.age_s: 0` describes the completed source observation. `cache_age_s: 0`
means no completed response cache was reused. These ages are measured at source
completion; consumers add elapsed time after that timestamp. An old record
modification time stays old even when its worker is sampled again.

The active path bypasses the history and SQLite summary caches. Its existing
context runtime retains at most 16,384 compact terminal or closeout facts keyed
by full device, inode, size, and nanosecond modification/change tokens. Terminal
status strings longer than 64 characters are not retained. No task payloads,
derived liveness, active summaries, or completed responses are retained there.
Records beyond the cache budget are still read and counted. Successful scans
replace the retained facts, evicting disappeared records. Contexts share no facts,
and a fresh process starts without them. Active records are always read again.

Concurrent HTTP requests share an in-flight scan; sequential requests rescan even
within the historical two-second route TTL. Scope, liveness, and ages are
recomputed. Before returning, the scanner rechecks file tokens and directory
identity after the final process sample. Directory metadata changes trigger
re-enumeration with the same candidate predicate and comparison of membership
and record tokens. Benign SQLite cache sidecars can appear without refusing an
unchanged inventory. Added, removed, replaced, or rewritten records and replaced
directories produce `task_authority_changed`. This is a bounded observation, not
a transaction with all writers and processes. Changes after the final check
remain possible.

HTTP 503 reason codes are `task_directory_unavailable`,
`task_record_unreadable_or_invalid`, and `task_authority_changed`.
Error responses have no successful `total` or `tasks`. Raw reader errors,
private paths, prompts, credentials, and worker identity payloads are not emitted.

`GET /api/delegate/tasks` retains its historical two-second route cache keyed
by directory generation, plus mtime-based in-memory and SQLite task caches.
Terminal queries also scan archive records. Its total precedes pagination.
It does not inherit the active route's observation guarantees.
`GET /api/delegate/tasks/{task_id}` remains an uncached detail read with the
existing optional nonce mismatch response.

Known consumers include Monitor orient, Work's admitted public projection,
routing-budget collection, fleet health, capacity selection, Fleet Comms inbox
triage, goal-driver stop checks, handoff readiness, thread handoff, delegate
admission, and worktree reaping. Additive top-level observations preserve their
legacy task row keys and active-count scope. A consumer that previously treated
missing authority as successful zero now receives an exception or HTTP error;
its own failure handling determines the resulting qualified state.
