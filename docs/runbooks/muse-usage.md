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
`get_provider_usage_data("muse")` in that process, and `agents.agy` from the
AGY `/usage` groups that same refresh already parsed. `--fresh` blocks on the
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

## AGY quota groups

`agents.agy` is the other row on that same `usage show` / `json` surface. It
is filled from the existing AGY CLI probe, `agy --prompt /usage`
(`source: agy_cli_usage`), which the Gemini routing lane already runs. There
is no second poller and no Google quota API.

The payload's `command.data.groups[]` are separate subscriptions. This row
keeps them separate:

* Gemini Models (`key: gemini_models`): `buckets[]` whose `window` is `5h` or `weekly`
* Claude and GPT models (`key: claude_gpt`): the same two windows

Each bucket maps `remaining_fraction` to used and remaining percent, and
`reset_time` to that window's reset. A finite fraction of `1` is a measured
full window (0% used, 100% remaining). A fraction of `0` is a measured empty
window. Neither one means unlimited. A missing, null, or non-finite fraction
stays unknown. The reset is still shown when that timestamp parsed and the
observation is fresh. A missing bucket is omitted. One group's window is never
copied into the other group, and a 5-hour reading is never copied into the
weekly window. Credit groups are not read.

The lane has no single `remaining_pct`. The groups are not one quota, so the
headline remaining stays unknown. `status` is `healthy` only when `freshness`
is `fresh` and at least one bucket has a finite fraction. Otherwise `status`
is `unknown`.

| Field | Meaning |
| --- | --- |
| `quota_groups[].key` / `label` | Which subscription group the windows belong to |
| `quota_groups[].windows[].used_pct` | Used percent from that bucket's `remaining_fraction`, or null |
| `quota_groups[].windows[].remaining_pct` | Remaining percent from that same fraction, or null |
| `quota_groups[].windows[].resets_at` | That bucket's `reset_time` when it parsed; null when the observation is stale, in error, or rate-limited |
| `freshness` | `fresh`, `stale_last_good`, or `unavailable` |
| `status` | `healthy` only for a fresh numeric bucket; otherwise `unknown` |
| `error_kind` / `error_code` | `unsupported` / `NO_QUOTA` when a fresh payload has no fraction; `rate_limit` / `429` when limited; `fetch_error` / `BAD_JSON` when the payload is malformed |

Stale, malformed, error, and rate-limited observations do not keep numeric
headroom or the previous reset. A cold process with no parsed payload renders
unknown.

```text
agy | healthy | unknown | fresh | 0 | -
  Gemini Models (5h): used=0.0% rem=100.0% resets=2026-09-30T12:33:22Z
  Gemini Models (weekly): used=0.2% rem=99.8% resets=2026-10-07T02:23:27Z
  Claude and GPT models (5h): used=0.0% rem=100.0% resets=2026-09-30T12:33:22Z
  Claude and GPT models (weekly): used=0.0% rem=100.0% resets=2026-10-07T07:33:22Z
```

## Dependency

Private status-consumer deployment remains with Infra. This repository change
does not edit installed private scripts, routing eligibility, credentials, or
a second telemetry service. Until Infra reads the fields above, the operator
status display will not show this producer on its own.
