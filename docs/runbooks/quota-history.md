# Quota history

An hourly, privacy-safe record of the weekly allowance for the five quota slots, and a reader that reports
where the observed used-percentage dropped or the reported reset timestamp moved, with the weekday.

Tracking: #11144 (stream #10844).

## What is recorded

One JSON line per slot per run, always five lines per run:

| Field | Meaning |
| --- | --- |
| `provider` | `codex`, `claude`, `grok` or `antigravity` |
| `slot` | `codex`, `claude:a`, `claude:b`, `grok` or `antigravity` (configured slot label, not an identity) |
| `window` | always `weekly` |
| `observed_at` | UTC time the collector ran |
| `source_observed_at` | UTC time the provider data was fetched, or null |
| `used_percent` | 0–100 when `status` is `known`, otherwise null |
| `resets_at` | UTC reported reset timestamp, or null |
| `status` | `known`, `stale` or `unknown` |
| `reason` | fixed code when not `known`: `source_unavailable`, `row_missing`, `value_invalid`, `source_stale`, `not_fresh`, `source_time_invalid` |

Only these fields are written. Account identifiers, email addresses, tokens, credit balances and any other
nested field of the Monitor projection are dropped before writing and are never printed.

`claude:a` and `claude:b` store `used_percent` as `100 - left_pct`. A value is only `known` when all of
these hold; otherwise the row is an explicit `unknown` or `stale` and nothing is inferred or carried forward:

- The Monitor labels it fresh and reports `stale: false`. A missing or non-boolean flag is `not_fresh`.
- Its source time (`fetched_at` for agent rows, `updated` for Claude account rows) is a valid
  timezone-aware timestamp that is not after the collector's observation (`source_time_invalid`), and no
  older than the snapshot's `diagnostics.stale_threshold_s` (`stale`, `source_stale`). When that
  threshold is missing or unusable, the Monitor's own 900-second bound applies, as it does in the Monitor.
- For agent rows (`codex`, `grok`, `antigravity`), the snapshot's own `diagnostics.data_age_s` is not past
  the threshold; past it the Monitor withdraws the snapshot's lane authority, and these rows are `stale`.
  Claude account rows are re-read live by the Monitor on every request, so they keep their own evidence.
  Because `data_age_s` is the oldest agent sample, one long-stale agent lane marks every agent row stale
  until that lane refreshes.
- The value is a finite number between 0 and 100. Booleans and numbers too large for a float are
  `value_invalid`.

A timestamp whose UTC value falls outside the years 1 to 9999 is invalid, never a crash. One hostile value
affects only its own slot; an unparseable Monitor document gives five `source_unavailable` rows.

## Where it is stored

`$LU_QUOTA_HISTORY_FILE` if set, otherwise `$XDG_STATE_HOME/learn-ukrainian/quota-history/samples.jsonl`
(default `~/.local/state/...`). Missing directories are created with mode 0700 and the file with mode 0600.
Writes are append-only, under an exclusive lock, in one write per run. Nothing truncates, rewrites or
prunes the file. Retention is an operator decision, not something the collector does.

Before writing, the collector walks from the home directory (or `/` for a path outside it) to the history
directory one component at a time and refuses any symlink. The history directory must be owned by the
user with no group or other permission bits; the file must be the user's own regular file with no group or
other bits. A symlink, FIFO, directory or other entry at the file name, or an existing path with wider
permissions, is refused (`collect` exits 1 with `unsafe history path refused; no rows written`) and
nothing is written or re-permissioned. Fix such a path by hand; the collector never runs `chmod`.

The collector reads the Monitor at `DELEGATE_MONITOR_API` (default: the loopback Monitor). It performs
one bounded HTTP GET of the existing `/api/state/routing-budget` projection (10-second timeout). It makes
no provider call, refreshes no quota and starts no service.

## Commands

```bash
.venv/bin/python -m scripts.fleet.quota_history collect        # append one run (what the timer does)
.venv/bin/python -m scripts.fleet.quota_history resets          # text report
.venv/bin/python -m scripts.fleet.quota_history resets --json   # same report as JSON
```

Both commands accept `--file PATH`. `collect` prints only counts and fixed reason codes.

## Reading the report

`resets` reports two kinds of observed change between consecutive `known` samples of one slot:

- `used_drop`: the used percentage went down. The reset happened at some point between the two
  observations; its exact time is not known.
- `reset_timestamp_jump`: the reported reset timestamp changed. This is a change in what the provider
  reported, not a confirmed reset.

Each event carries the weekday of the observation (and, for jumps, of both reset timestamps). Duplicate
samples (same slot, source time and values) count once. Out-of-order lines are sorted into place. Malformed
lines are counted and skipped. Unknown and stale samples are never compared.

The report does not state a reset schedule. A history with no `known` samples says so explicitly and
certifies nothing. Do not read a weekday in the report as a guaranteed reset day; it is the weekday of an
observation that a change was seen.

## Install (after merge; idempotent)

The units are templates. Render `@REPO_ROOT@` to the deployed checkout path, install, reload and enable the
timer. Re-running these commands is safe.

Install the companion data-volume drop-in (`packaging/systemd/dropins/learn-ukrainian-quota-history.service.d/data-volume.conf`)
before enabling the timer. It wraps the collector's `ExecStart` with the data-volume guard, so a failed guard exits 78 and
prevents restart. The approved installer renders it with every other timer service's drop-in. Run the preview from the
primary checkout first, then `--apply` from the primary checkout (it refuses dispatch worktrees). It does not reload or
start units:

```bash
.venv/bin/python scripts/storage/install_data_volume_dropins.py          # preview; no writes
.venv/bin/python scripts/storage/install_data_volume_dropins.py --apply  # primary checkout only; writes drop-ins
```

```bash
mkdir -p ~/.config/systemd/user
sed "s#@REPO_ROOT@#<deployed-checkout>#g" packaging/systemd/learn-ukrainian-quota-history.service > ~/.config/systemd/user/learn-ukrainian-quota-history.service
sed "s#@REPO_ROOT@#<deployed-checkout>#g" packaging/systemd/learn-ukrainian-quota-history.timer > ~/.config/systemd/user/learn-ukrainian-quota-history.timer
systemctl --user daemon-reload
systemctl --user enable --now learn-ukrainian-quota-history.timer
systemctl --user start learn-ukrainian-quota-history.service   # one immediate sample, optional
systemctl --user list-timers learn-ukrainian-quota-history.timer
```

Verify the rendered units without installing: `systemd-analyze verify <rendered-unit-paths>`.

## Limits

- A run during a Monitor outage writes five explicit `unknown` rows with `source_unavailable`. This is
  intentional: an outage is visible history, not a gap to fill.
- The first `known` sample of a slot is only a baseline. It never produces an event.
- The history is only as long as the timer has run. An empty or all-unknown history cannot establish
  calendar behaviour.
- Provider timestamps come from the Monitor. The collector checks that they are valid, not in the future
  and within the published threshold, but cannot prove the Monitor's clock is right.
- The reader counts a stored `known` record as malformed unless its value is valid and its source time is
  present and not after its observation.
