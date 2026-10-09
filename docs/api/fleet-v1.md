# Fleet board API v1

Read-only JSON API mounted at `/api/fleet/v1`. The index and schema routes
publish the contract. Operations routes and the pull-request pipeline read
optional locations and degrade inside the envelope. Existing unversioned
fleet routes are unchanged.

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
| `ok` | The index saw a set variable, or a data route completed a read. `age_s` is the age of a completed read, and null when that route did not read the location. |
| `stale` | A completed read is older than its freshness window, or a refresh failed and a cached payload is being served. |
| `unavailable` | The read failed and there is nothing cached, or the location check failed. `error` is the token `unavailable`. |
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
