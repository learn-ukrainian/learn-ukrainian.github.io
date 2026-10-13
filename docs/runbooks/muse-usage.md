# Muse usage in the public telemetry producer

Issue #10564. This runbook is the public producer contract. The installed
private `lu-driver-status` consumer is owned by Infra and is not changed here.

## What the probe can see

The installed `muse` CLI help has no quota subcommand. CodexBar 0.69 is the
supported interface: `codexbar usage --provider muse --json --no-credits`.
Public CodexBar docs (`docs/muse.md`) map a Muse Code subscription onto the
usual usage windows when the provider includes `subs_usage`:

* primary: 5-hour window (`usedPercent`, `windowMinutes`, `resetsAt`)
* secondary: weekly window (`usedPercent`, `windowMinutes`, `resetsAt`)

A live CodexBar Muse probe on 2026-10-13 returned null primary and weekly
percentages. Null is unknown. It is not 0% used and it is not unlimited.
A reported `usedPercent` of 0 is a real empty window and stays 100% remaining.
Identity, account, and credit fields are dropped and are not part of this contract.

## Where Muse appears

`muse` is a member of `SUBSCRIPTION_PROVIDERS`. The existing subscription
scheduler (`codexbar-scheduler`) refreshes it with every other non-Cursor
lane. The default period is `DEFAULT_CODEXBAR_REFRESH_INTERVAL_S` (720
seconds), which is at most 15 minutes. There is no Muse-only poller.

`muse` is not a routing-budget lane. `GET /api/state/routing-budget` does
not grow an `agents.muse` entry from this change.

`python -m scripts.fleet.usage show` and `json` add `agents.muse` from
`get_provider_usage_data("muse")` in that process. `--fresh` blocks on the
existing provider refresh, then reads that cache. A cold process with no
cache renders unknown rather than guessing.

## Fields Infra should consume

Read `agents.muse` from `python -m scripts.fleet.usage json` after a refresh
in the same process (or the provider record from `get_provider_usage_data("muse")`).
Render null as the word `unknown`. Publish a number only when `freshness` is
`fresh` and no error or rate-limit is set.

| Field | Meaning |
| --- | --- |
| `remaining_pct` | Tightest reported window's remaining percent, or null |
| `headroom_pct` | Same binding remaining. Null when missing, unsupported, stale, in error, or rate-limited |
| `resets_at` | Reset timestamp of that window, or null |
| `freshness` | `fresh`, `stale_last_good`, or `unavailable` |
| `status` | `healthy` only for a fresh numeric window; otherwise `unknown` |
| `error_kind` / `error_code` | `unsupported` / `NO_QUOTA` when the probe returned no percentage; `rate_limit` / `429` when limited; `fetch_error` / `BAD_JSON` when the payload is malformed |

On the provider record, the same windows are `primary_remaining_pct`,
`weekly_remaining_pct`, `windows.primary`, `windows.secondary`, and
`weekly_resets_at`. A missing window is omitted from headroom. It is not
filled in as 100%.

Human output adds one quota line:

```text
muse | healthy | 70.0 | fresh | 0 | -
  quota: remaining=70.0% headroom=70.0% resets=2026-10-20T00:00:00Z
```

Unsupported, stale, malformed, and rate-limited rows keep remaining, headroom,
and reset as `unknown`.

## Dependency

Private status-consumer deployment remains with Infra. This repository change
does not edit installed private scripts, routing eligibility, credentials, or
a second telemetry service. Until Infra reads the fields above, the operator
status display will not show this producer on its own.
