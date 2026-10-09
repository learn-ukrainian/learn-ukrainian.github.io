# Fleet board API v1

Read-only JSON API mounted at `/api/fleet/v1`. Responses share one envelope.
The index and schema describe every registered route. Existing unversioned
fleet routes, including `/api/state/routing-budget`, are unchanged.

## Envelope

Every response is one object:

| Field | Meaning |
| --- | --- |
| `schema` | `fleet.v1.<name>` |
| `generated_at` | UTC timestamp, `YYYY-MM-DDTHH:MM:SSZ` |
| `sources` | One row per external location |
| `data` | The payload for that route |

Each source row is `{name, status, age_s, error}`.

| Status | Meaning |
| --- | --- |
| `ok` | The source was read, or a route that does not read it found the variable set. `age_s` is null until a route has read the source. |
| `stale` | A read source is older than twice its snapshot interval, or a budget refresh did not finish in time and an older result is being served. `age_s` is how old that result is. |
| `unavailable` | The read or status check failed. `error` is the token `unavailable`. |
| `not_configured` | The variable is unset or blank. `age_s` and `error` are null. |

The schema rejects a row whose status disagrees with `age_s` or `error`.
`not_configured` requires both to be null. `unavailable` requires a null age
and the error token `unavailable`. `ok` and `stale` require a null error.
A failed source changes that row's status. The HTTP status stays 200.
Exception text is not copied into the response.

## Configuration

Every location variable is optional. Unset or blank is `not_configured`.
There is no default value. The value itself is never returned.

| Source name | Variable | Setting |
| --- | --- | --- |
| `roster_snapshot` | `FLEET_ROSTER_SNAPSHOT` | JSON file |
| `harness_snapshot` | `FLEET_HARNESS_SNAPSHOT` | JSON file |
| `downloads` | `FLEET_DOWNLOAD_STATUS` | JSON file |
| `backups` | `FLEET_BACKUP_STATE_DIR` | directory |
| `mq_state` | `FLEET_MQ_STATE_DIR` | directory |
| `stats` | `FLEET_PROMETHEUS_URL` | URL |
| `alerts` | `FLEET_ALERTMANAGER_URL` | URL |
| `links` | `FLEET_GRAFANA_URL` | URL |

## Routes

### `GET /api/fleet/v1`

`schema` is `fleet.v1.index`. `data.endpoints` lists every registered v1
route as `{method, path, schema}`. `HEAD` and `OPTIONS` are omitted.

### `GET /api/fleet/v1/schema`

`schema` is `fleet.v1.schema`. `data.endpoints` maps each schema id to a
JSON Schema document. The `fleet.v1.index` document validates a response
from the index route.

### `GET /api/fleet/v1/roster`

`schema` is `fleet.v1.roster`. The body is read from the JSON snapshot
named by `FLEET_ROSTER_SNAPSHOT`. The location itself is not returned.
Unset or blank is `not_configured`. An unreadable or non-object document
is `unavailable`. Both still respond with HTTP 200 and the three layers,
with no epics.

`data.layers` is three groups, in order:

| `layer` | `kind` | Who is listed |
| --- | --- | --- |
| `0` | `foundations` | Snapshot epics on layer 0, foundations first (`codebase`, then `data`), then any other layer-0 epic |
| `1` | `consumers` | Snapshot epics on layer 1 |
| `null` | `postponed` | Snapshot epics marked postponed |

Each epic has `epic`, `depends_on`, `restart_condition`, `state`, and
`flags`. A postponed epic is always `state: "off"`. A flag `value` is
`true`, `false`, or `"unknown"`. Only a JSON boolean stays boolean; every
other value, including a missing one, is `"unknown"`. Each flag also has
`source` and `checked_at` (null when the snapshot did not give a usable
token or timestamp).

`data.foundation_status` is `{foundation, red, reasons}`. `red` is boolean
or null. A missing or non-boolean `red` is null. `data.active_alerts` is
`{name, summary}` from the snapshot's `alerts` list. Keys the snapshot
adds beyond this contract are dropped.

The snapshot may include `generated_at` and `interval_s`. When both are
present and the document is older than twice `interval_s`, the
`roster_snapshot` source is `stale` and `age_s` is set. The roster data
is still returned.

### `GET /api/fleet/v1/budget`

`schema` is `fleet.v1.budget`. `data.subscriptions` has one row per
subscription lane from the existing routing-budget compute:

| Field | Meaning |
| --- | --- |
| `subscription` | Lane name |
| `used_pct` | Weekly used percent. Null when the compute has no weekly figure. A measured zero stays zero. |
| `elapsed_pct` | Percent of the weekly window that has elapsed. Null when it cannot be computed. |
| `pace` | Pace stage from the existing weekly pace function, or null when used percent is unknown. |
| `reset_at` | Weekly reset instant in UTC with whole seconds, or null |
| `recommendation` | The lane status already computed for that subscription, or null |

The route keeps a result for 15 seconds and waits at most 2 seconds for a
refresh. When a refresh exceeds that wait and an older result exists, the
response is that older result, the `routing_budget` source is `stale`, and
`age_s` is the age of the cached result. A failure with nothing cached is
`unavailable`, with null measurements, and HTTP 200. This route does not
change the response of `/api/state/routing-budget`.

### `GET /api/fleet/v1/prs`

Open pull requests. `schema` is `fleet.v1.prs`.

| Query | Effect |
| --- | --- |
| `epic` | Keep rows whose epic token matches. A token is an `epic:` label or marker, or a closing reference. `12` and `epic:12` match the same token. |
| `state` | `open`, `stale`, `held`, `red`, `green`, `pending`, `queued`, `not_queued`, or `dropped`. An unknown value matches nothing. |

Each row has `number`, `repo`, `title`, `draft`, `head_sha`, `epics`, `ci` (`green`, `red`, or `pending`), `cf` (`verdict`, `at_head`), `gate` (the CI Gate check), `mq` (`queued`, `not_queued`, or `dropped`), `keeper` (`hold`, `reason`), `flake_grant` (`decision` `grant` or `deny`, `used`, `at`), `ready_since`, `stale_green`, `minutes`, and `stacked_base`.

`at_head` is true only when the cross-family verdict was recorded for the current head. An approval recorded for an older head does not count.

`stale_green` is true when the pull request is approved at the current head, CI is green, there is no merge conflict, the hold is known to be absent, and it has stayed out of the queue for at least `FLEET_PR_STALE_MIN` minutes (default 60). `minutes` is that age. A hold, including a requeue hold, or an unknown hold, keeps `stale_green` false and `minutes` null. Without a recorded ready time, `minutes` is null.

`stacked_base` is the open pull request whose head branch is this pull request's base (`number`, `ref`, `state`, `mq`). It is null when the base is the default branch.

Sources on this route are `github` and `mq_state`.

`github` uses REST through the shared GitHub client. Queue membership is the one field read with a query, because REST does not provide it. Successful reads are reused for a short time (`FLEET_GITHUB_READ_TTL` seconds, default 15, at most 120). The repository is `FLEET_GITHUB_REPO`, or `GH_REPO` / `GITHUB_REPOSITORY` when that is unset, and must be `owner/name`. Unset is `not_configured`. A failed list read is `unavailable` with an empty `prs` array. HTTP status stays 200.

`mq_state` is the directory in `FLEET_MQ_STATE_DIR`. It holds `requeue.json` (the requeue gate), `keeper.json` (or `merge_queue_keeper.json`, the keeper's state), and `stale-approved.json` (`version` 1, `approved` keyed by `<number>:<head>` with `since`). Unset is `not_configured`. A directory with no keeper file, or unreadable or malformed keeper or alert state, is `unavailable`. While that source is unavailable, `keeper.hold` stays null unless a label hold is already known. A keeper or gate file older than two minutes is `stale`. The directory value is not returned.

### `GET /api/fleet/v1/prs/{number}`

`schema` is `fleet.v1.pr`. `data.pr` is the same object as one list row, or null when that pull request is not open.
