# Fleet board API v1

Read-only JSON API mounted at `/api/fleet/v1`. Responses share one envelope.
The index and schema describe every registered route. Operations, snapshot
routes and the pull-request pipeline read optional locations and degrade
inside the envelope. Existing unversioned fleet routes, including
`/api/state/routing-budget`, are unchanged.

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
| `ok` | The index saw a set variable, or a data route completed a read. `age_s` is null when the route did not read the location. |
| `stale` | A read is older than its freshness window, or a refresh failed or timed out and a cached payload is being served. `age_s` is the age of that result. |
| `unavailable` | The read failed with nothing cached, or the status check failed. `error` is the token `unavailable`. |
| `not_configured` | The variable is unset or blank. `age_s` and `error` are null. |

The schema rejects a row whose status disagrees with `age_s` or `error`.
`not_configured` requires both to be null. `unavailable` requires a null age
and the error token `unavailable`. `ok` and `stale` require a null error.
A failed source changes that row's status. The HTTP status stays 200.
Exception text is not copied into the response. Each external read stops at
an overall deadline of two seconds and uses a short cache. The index reports
whether each variable is set; it does not read the location, so its `age_s`
stays null. Data routes report the source they actually read.

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

### `GET /api/fleet/v1/alerts`

`FLEET_ALERTMANAGER_URL`. Server-side read of Alertmanager v2 alerts.
Each item publishes `name`, `severity`, `summary`, `starts_at`, and `state`.
A name is kept only when it is a plain identifier, and a summary is kept as
plain text. Other fields are dropped. Unset or blank is `not_configured`.

### `GET /api/fleet/v1/stats`

`FLEET_PROMETHEUS_URL`. Four fixed instant queries: disk percent, memory
percent, live drivers, and API probe status. Names are `disk_pct`,
`memory_pct`, `drivers_live`, and `probe_status`. A query parameter on
this route is ignored. One failed query marks that stat `unavailable` and
leaves the others in place. When every query fails, a cached payload is
served as `stale`; with nothing cached the source is `unavailable`. Series
labels are not returned.

### `GET /api/fleet/v1/links`

`FLEET_GRAFANA_URL`. Fixed dashboard links for `overview` and `fleet`,
built from that base. Userinfo and query strings on the base are not
copied into the link.

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

### `GET /api/fleet/v1/backups`

`FLEET_BACKUP_STATE_DIR`, reading `last-success.json`, `freshness.json`,
and `receipt.json`. `data` is the age in hours, whether that age is over
36 hours, the last result, and the restore-test result. A missing file is
`unavailable` and still HTTP 200. Fields that were not read are null.

### `GET /api/fleet/v1/downloads`

`FLEET_DOWNLOAD_STATUS`. One row per source: state, done, total, percent,
last progress time, and `stalled`. `stalled` is true when there has been
no progress for more than `FLEET_DOWNLOAD_STALL_MIN` minutes (15 when
unset). A missing progress time leaves `stalled` null. An unreadable file
sets `data.state` to `unknown` and the source to `unavailable`.

### `GET /api/fleet/v1/harness`

`FLEET_HARNESS_SNAPSHOT`. One row per driver: context percent, compactions,
stop count, ask count, idle minutes, and `measured_at`. A missing
measurement is null. `GET /api/fleet/v1/harness/{agent_id}` returns that
driver, or null when the id is absent. The id is not copied into the body
when it is absent.
