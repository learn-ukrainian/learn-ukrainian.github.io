# Unattended dictionary staging (#10003, epic #6321)

Use `scripts.ingest.dictionary_acquisition` for one explicitly selected dictionary
and one frozen target. The existing `scripts.lexicon.build_slovnyk_mirror` remains
the supported bulk cache builder. This companion writes isolated staging only;
importing, publishing and live acquisition runs belong to the accountable driver.
It installs no service and does not change existing caches or live databases.

The companion keeps its observable, one-request transport local:
`_fetch_slovnyk_entry` returns `None` for both 404 and a 200 with no parsed entry,
and retries access failures as transient; `fetch_sum20_wordid` hides the numeric
HTTP status and can classify an article lacking `.ENTRY` as not found. Those
interfaces cannot supply the required first-access-failure stop or proven-404
distinction. The companion calls their existing article parsers directly and
preserves their source identities without patching global transports.

## Targets and storage

For slovnyk.me, select exactly one canonical slug from
`scripts.wiki.slovnyk_me.SLOVNYK_ME_DICTS` (catalogue aliases also resolve there).
Supply a JSON manifest with `entries[].lemma`; the denominator is the ordered
set of unique, nonempty lemma strings. Lookup normalization and article parsing
reuse `scripts.lexicon.enrich_manifest`. For `sum20_official`, supply both
inclusive integer bounds, at least 1. The denominator is every integer in that
finite range. Neither denominator measures the full upstream dictionary.

Choose an operator-owned **local filesystem** staging root, outside live stores.
All companion jobs on the same machine and upstream host must use this **same
root**. Do not place SQLite on network storage. Source/archive placement follows
[storage topology](storage-topology.md); staging is separate from canonical data.
Do not run other acquisition tools against a companion's staging files.

Each canonical dictionary owns `<root>/<dictionary>/`:

| File | Role |
| --- | --- |
| `staging.sqlite3` | Durable frozen specification, ordered results and attempt/outcome events |
| `status.json` | Atomically replaced projection reconciled from SQLite |
| `job.log` | Path-free structured state/count/retry log; no articles or exception bodies |
| `writer.lock`, `supervisor.lock` | OS advisory exclusive writer and supervisor admission |

The shared root also holds `slovnyk.lock/json`, `sum20ua.lock/json` for host-wide
request admission, and `admission.lock`, `refusal.json`, `refusals.log` for invalid
input/conflicting-writer receipts. A refusal never overwrites another writer's
job status. If refusal storage is unavailable, the JSON printed to the console
includes `evidence_error: refusal_storage_unavailable`. Malformed CLI arguments
exit 2 with a path-free error; no job can be bound in that case.

Locks are released by the OS when a process dies. Leave the lock files in place:
unlinking a lock can admit two writers on different inodes. One job per dictionary
per root is supported; a different target for the same dictionary needs a
separately scheduled new run after the existing job has stopped.

## Detached, bounded supervisor

Set `ACQ_CHECKOUT` to the reviewed checkout, `PRIMARY_CHECKOUT` to the checkout
holding the project interpreter, `ACQ_ROOT` to the agreed local staging root,
and `ACQ_MANIFEST` to the reviewed frozen manifest. These values stay private.
Preserve the `.venv/bin/python` path; do not resolve its executable symlink or
create a worktree virtual environment.

```bash
ACQ_PY="${PRIMARY_CHECKOUT:?}/.venv/bin/python"
cd "${ACQ_CHECKOUT:?}"
"$ACQ_PY" -m scripts.ingest.dictionary_acquisition --help

tmux new-session -d -s acquisition-vts -c "$ACQ_CHECKOUT" \
  "$ACQ_PY" -m scripts.ingest.dictionary_acquisition supervise \
  --root "${ACQ_ROOT:?}" --dictionary vts --manifest "${ACQ_MANIFEST:?}" \
  --delay 4 --timeout 30 --backoff 4 --max-attempts 4 --max-restarts 3

tmux new-session -d -s acquisition-official -c "$ACQ_CHECKOUT" \
  "$ACQ_PY" -m scripts.ingest.dictionary_acquisition supervise \
  --root "$ACQ_ROOT" --dictionary sum20_official --start-wordid 5 --end-wordid 12 \
  --delay 4 --timeout 30 --backoff 4 --max-attempts 4 --max-restarts 3

"$ACQ_PY" -m scripts.ingest.dictionary_acquisition status \
  --root "$ACQ_ROOT" --dictionary vts
```

The examples use the approved detached tmux pattern and the CLI's own supervisor;
do not wrap them in an unconditional shell restart loop. Start only the reviewed
explicit jobs. Initially allow at most two slovnyk dictionaries and one official
job, all sharing the root and using delay 4 or greater. The host lock serializes
GETs across dictionaries and reserves a minimum four-second quiet interval
**after** each completed request: aggregate companion starts are at most one per
four seconds per host, rather than that rate multiplied by the process count.
Other clients outside this root are not coordinated; the driver must account for
their traffic before launching. Multiple machines require coordinated operational
scheduling; this is a local coordination helper, not a distributed limiter.

Every attempt, including a retry, waits for the host reservation and its durable
backoff deadline. The CLI refuses delay below two seconds. The reservation is
written before HTTP, conservatively including timeout plus delay if the request
is interrupted. `Retry-After` delta seconds and HTTP dates are honored. Requests
use existing identifying User-Agent strings and an HTML Accept header; redirects,
environment proxies and implicit netrc credentials are disabled. There are no
challenge workarounds or impersonation headers.

## Frozen input, reuse and restart

The SQLite specification binds dictionary, manifest bytes or explicit range,
ordered target fingerprint, parser and companion code hashes, seed-directory
identity, timing and attempt/restart budgets. Repeating `run` or `supervise`
rejects drift **before HTTP**. Keep the original manifest bytes and CLI options,
and pin the checkout for the run. `status` needs no manifest and reconciles from
the durable store. A busy writer returns conflict instead of competing for data;
read the last atomic `status.json` until that writer exits.

`--seed-cache "$REVIEWED_CACHE"` is optional for slovnyk. It only reads positive
rows with the current cache schema, matching lemma/lookup/dictionary, valid direct
source URL and an aware acquisition timestamp. Reused rows preserve the article,
original timestamp, source locator and cache digest, with `http_status: null`
because legacy HTTP status was not recorded. Invalid rows and legacy nulls are
refetched; null is not proof of a 404. Seed files are never rewritten. The seed
snapshot is retained in staging after creation; changing a seed file later does
not alter an existing job.

`run` processes resolved targets until it encounters a transient failure or a
terminal stop. `supervise` launches `run` and retries transient/unexpected crash
exits with a quiet interval of at least two seconds. Per-target attempts and
supervisor launches are reserved **durably before execution**. A restart of either
process cannot reset the budget. Defaults allow four attempts per unresolved
target and four child launches **without durable target progress** (initial plus
three restarts). Each committed positive article or proven 404 starts a new
no-progress launch budget; transient results, in-flight attempts and process
startup do not. Launch reservations and resolved outcomes share the persisted
event sequence, so progress remains effective across a supervisor restart,
while subsequent crashes without progress still consume the same bounded cap.
Scattered recovered failures can therefore complete even when lifetime launches
exceed four. Reaching either current cap latches `exhausted`. A launch reservation
consumed by a crash still counts. Neither progress nor an explicit resume erases
lifetime launch or request-attempt history. Retryable network failures and
408/425/429/5xx never become misses.

| Exit | Outcome / unattended behavior |
| --- | --- |
| 0 | `complete`, or successful `status`/explicit `resume`; supervisor stops |
| 2 | Invalid arguments, dictionary, storage, frozen-input mismatch; stop |
| 3 | First 401/403 or other unsupported HTTP/redirect; `blocked`, stop immediately |
| 4 | HTTP 200 without a usable parsed article; `parse_error`, stop |
| 5 | Persistent attempt or supervisor budget exhausted; stop |
| 6 | Conflicting writer/supervisor; stop |
| 75 | One transient result from `run`; supervisor may retry within persisted caps |
| Unexpected child exit | Supervisor may restart within persisted caps, after checking durable terminal state |

Blocked, parse-error, exhausted and complete jobs do not automatically resume,
including when a child commits a terminal state and dies before returning its
exit code. The failed wordid/lemma stays unresolved; checkpoint does not advance.
A 404 is the only observed HTTP miss. Parser/schema ambiguity stops rather than
guessing or changing parser semantics. Raw response bodies and request secrets
are never emitted to logs/status; successful articles live only in local staging.

After the driver has investigated a stop and the operator authorizes another
attempt, use an **explicit** resume action with the original frozen options:

```bash
"$ACQ_PY" -m scripts.ingest.dictionary_acquisition resume \
  --root "$ACQ_ROOT" --dictionary vts --manifest "$ACQ_MANIFEST" \
  --delay 4 --timeout 30 --backoff 4 --max-attempts 4 --max-restarts 3
```

`resume` makes no requests. It resets unresolved attempt/no-progress launch budgets, records
an `operator_resume` event and preserves resolved articles/misses and historical
events. It refuses an active writer or supervisor. Then deliberately launch the
same reviewed `supervise` command again. The supervisor never passes `resume` to
a child. A new root requires separate driver scheduling so the shared-host budget
is preserved; do not use a new root to circumvent a stop or reset a budget.

## Coverage and evidence

`counts.positive`, `miss`, `pending`, `error`, `reused` partition the frozen
denominator and are recomputed from durable result rows. `checkpoint` is the
length of the contiguous resolved prefix; official status also names `next_wordid`.
Positive official rows are unique by requested wordid. `complete` means every
target in this manifest/range has a positive/reused article or proven 404, including
the possible all-miss case; it never claims all upstream articles were acquired.

`request_attempts` counts historical durable attempt reservations, including
interrupted requests; it cannot prove that every reserved request reached upstream.
`current_attempt_budget_used` sums current per-target attempt counters, and
`retry` reports the next unresolved target's attempts/deadline.
`retry.supervisor_launches` and `supervisor_restarts` are lifetime counters;
`retry.no_progress_launches` is the current launch budget used, bounded by
`retry.max_no_progress_launches` (`max_restarts + 1`). A resolved target resets
only that current launch budget, never per-target attempts or historical counts.
The structured log includes the same retry and attempt counters as status.
Elapsed time includes interruptions. ETA is `null` until at least two
network targets resolve, and remains unknown for terminal errors. A supported ETA
is an estimate from elapsed progress, not evidence of dictionary completeness.

The database commit is authoritative if interruption leaves stale JSON. Restart
or `status` repairs the projection from rows/events without losing or double
counting resolved targets. Admission refusals are separate receipts, so check both
job status and the invocation exit code/refusal when diagnosing a failed launch.

Offline validation uses fake HTTP and disposable local storage:

```bash
COVERAGE_FILE="${TMPDIR:?}/dictionary-acquisition.coverage" "$ACQ_PY" -m pytest \
  tests/test_dictionary_acquisition.py tests/test_sum20_official.py \
  tests/test_build_slovnyk_mirror.py \
  --cov=scripts.ingest.dictionary_acquisition --cov-branch \
  --cov-report=term-missing --cov-fail-under=80
"$ACQ_PY" -m ruff check scripts/ingest/dictionary_acquisition.py \
  scripts/wiki/sum20_official.py tests/test_dictionary_acquisition.py \
  tests/test_sum20_official.py
"$ACQ_PY" -m ruff format --check scripts/ingest/dictionary_acquisition.py \
  scripts/wiki/sum20_official.py tests/test_dictionary_acquisition.py \
  tests/test_sum20_official.py
```

These author tests establish implementation evidence. The driver owns independent
held-out subprocess interruption/concurrency/reconciliation cases, native Opus
exact-head review, CI, landing, cleanup and operational source-access checks.
No live acquisition or canonical-store write is part of offline validation.
