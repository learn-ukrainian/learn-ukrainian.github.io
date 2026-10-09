# Fleet board API v1

Read-only JSON API mounted at `/api/fleet/v1`. The index and schema
describe every registered route. The pull-request pipeline is the first
data route. Existing unversioned fleet routes are unchanged.

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
| `ok` | The location variable is set. This slice does not read it, so `age_s` is null. |
| `stale` | Reserved for a later slice that has read a location older than its interval. |
| `unavailable` | The status check failed. `error` is the token `unavailable`. |
| `not_configured` | The variable is unset or blank. `age_s` and `error` are null. |

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

### `GET /api/fleet/v1/prs`

Open pull requests. `schema` is `fleet.v1.prs`.

| Query | Effect |
| --- | --- |
| `epic` | Keep rows whose epic token matches. A token is an `epic:` label or marker, or a closing reference. `12` and `epic:12` match the same token. |
| `state` | `open`, `stale`, `held`, `red`, `green`, `pending`, `queued`, `not_queued`, or `dropped`. An unknown value matches nothing. |

Each row has `number`, `repo`, `title`, `draft`, `head_sha`, `epics`, `ci` (`green`, `red`, or `pending`), `cf` (`verdict`, `at_head`), `gate` (the CI Gate check), `mq` (`queued`, `not_queued`, or `dropped`), `keeper` (`hold`, `reason`), `flake_grant` (`decision` `grant` or `deny`, `used`, `at`), `ready_since`, `stale_green`, `minutes`, and `stacked_base`.

`at_head` is true only when the cross-family verdict was recorded for the current head. An approval recorded for an older head does not count.

`stale_green` is true when the pull request is approved at the current head, CI is green, there is no merge conflict, it is not held, and it has stayed out of the queue for at least `FLEET_PR_STALE_MIN` minutes (default 60). `minutes` is that age. A hold, including a requeue hold, keeps `stale_green` false and `minutes` null. Without a recorded ready time, `minutes` is null.

`stacked_base` is the open pull request whose head branch is this pull request's base (`number`, `ref`, `state`, `mq`). It is null when the base is the default branch.

Sources on this route are `github` and `mq_state`.

`github` uses REST through the shared GitHub client. Queue membership is the one field read with a query, because REST does not provide it. Successful reads are reused for a short time (`FLEET_GITHUB_READ_TTL` seconds, default 15, at most 120). The repository is `FLEET_GITHUB_REPO`, or `GH_REPO` / `GITHUB_REPOSITORY` when that is unset, and must be `owner/name`. Unset is `not_configured`. A failed list read is `unavailable` with an empty `prs` array. HTTP status stays 200.

`mq_state` is the directory in `FLEET_MQ_STATE_DIR`. It holds `requeue.json` (the requeue gate), `keeper.json` (or `merge_queue_keeper.json`, the keeper's state), and `stale-approved.json` (`version` 1, `approved` keyed by `<number>:<head>` with `since`). Unset is `not_configured`. Unreadable or malformed keeper or alert state is `unavailable`. A keeper or gate file older than two minutes is `stale`. The directory value is not returned.

### `GET /api/fleet/v1/prs/{number}`

`schema` is `fleet.v1.pr`. `data.pr` is the same object as one list row, or null when that pull request is not open.
