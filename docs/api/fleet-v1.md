# Fleet board API v1

Read-only JSON API mounted at `/api/fleet/v1`. The index and schema
describe every registered route. The pull-request pipeline, the attention
list, and the throughput summary are the data routes. Existing unversioned
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
| `ok` | The read succeeded, or the index confirmed the location variable is set. `age_s` is the age of a completed read, and null when that route did not read the location. |
| `stale` | A completed read is older than that source's freshness interval. |
| `unavailable` | The read failed, or the location check failed. `error` is the token `unavailable`. |
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
| `stale_prs` | `FLEET_STALE_PR_STATE` | JSON file |

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

Each row has `number`, `repo`, `title`, `draft`, `head_sha`, `epics`, `ci` (`green`, `red`, or `pending`), `cf` (`verdict`, `at_head`), `gate` (the CI Gate check), `mq` (`queued`, `not_queued`, or `dropped`), `keeper` (`hold`, `reason`), `flake_grant` (`decision` `grant` or `deny`, `used`, `at`), `ready_since`, `stale_green`, `minutes`, `stacked_base`, `hours_idle`, `blocker`, `owner_lane`, `idle_24h`, and `idle_48h`.

`at_head` is true only when the cross-family verdict was recorded for the current head. An approval recorded for an older head does not count.

`stale_green` is true when the pull request is approved at the current head, CI is green, there is no merge conflict, the hold is known to be absent, its base is `main`, and it has stayed out of the queue for at least `FLEET_PR_STALE_MIN` minutes (default 60). `minutes` is that age. A hold, including a requeue hold, or an unknown hold, keeps `stale_green` false and `minutes` null. Without a recorded ready time, `minutes` is null. A pull request whose base is not `main` is never ready: `stale_green` is false and `minutes` is null.

`hours_idle` is the hours since the latest of the head commit, a cross-family verdict, or a merge event, truncated to a tenth of an hour. `idle_24h` is true at 24 hours and `idle_48h` at 48. When none of those times is known, `hours_idle` is null and both flags are false.

`blocker` is one object. `stacked_base` applies when the base branch is not `main`, including when the base pull request is still open, closed, or otherwise unmerged. It carries `number` and `state` (`open`, `closed`, `unmerged`, or `merged`). `conflict` is a merge conflict. `failing_check` lists the `checks` that finished without succeeding. `cf_changes` is a changes-requested verdict on the current head. `none` is everything else. When more than one applies, the order is `stacked_base`, then `conflict`, then `failing_check`, then `cf_changes`.

`owner_lane` is the lane named by the first segment of the head branch. A recorded lane on the optional state record replaces it. It is null when neither names a lane.

`stacked_base` is the open pull request whose head branch is this pull request's base (`number`, `ref`, `state`, `mq`). It is null when the base is the default branch.

Sources on this route are `github`, `mq_state`, and `stale_prs`.

`github` uses REST through the shared GitHub client. Queue membership is the one field read with a query, because REST does not provide it. Successful reads are reused for a short time (`FLEET_GITHUB_READ_TTL` seconds, default 15, at most 120). The repository is `FLEET_GITHUB_REPO`, or `GH_REPO` / `GITHUB_REPOSITORY` when that is unset, and must be `owner/name`. Unset is `not_configured`. A failed list read is `unavailable` with an empty `prs` array. HTTP status stays 200.

`mq_state` is the directory in `FLEET_MQ_STATE_DIR`. It holds `requeue.json` (the requeue gate), `keeper.json` (or `merge_queue_keeper.json`, the keeper's state), and `stale-approved.json` (`version` 1, `approved` keyed by `<number>:<head>` with `since`). Unset is `not_configured`. A directory with no keeper file, or unreadable or malformed keeper or alert state, is `unavailable`. While that source is unavailable, `keeper.hold` stays null unless a label hold is already known. A keeper or gate file older than two minutes is `stale`. The directory value is not returned.

`stale_prs` is the JSON file named by `FLEET_STALE_PR_STATE`. Unset is `not_configured`. The value is not returned. A missing or malformed file is `unavailable`, and the route still returns what GitHub and the queue state provide. `version` is 1. `activity` is keyed by pull-request number and may include `commit_at`, `cf_at`, `merge_event_at`, `owner_lane`, and `base` (`number`, `state`). `throughput` is a list of `date`, `repo`, `owner_lane`, `opened`, and `merged`. A file older than fifteen minutes is `stale`; its contents are still used.

### `GET /api/fleet/v1/now`

`schema` is `fleet.v1.now`. `data.attention` lists open pull requests with `idle_24h`, most idle first. Each item has `number`, `repo`, `title`, `owner_lane`, `hours_idle`, `idle_24h`, `idle_48h`, and `blocker`. Sources match the pull-request list.

### `GET /api/fleet/v1/stats`

`schema` is `fleet.v1.stats`. `data.window_days` is 14. `by_repo` and `by_lane` each carry `backlog` (open pull requests now) and `days` (one row per UTC day in the window, oldest first, with `date`, `opened`, and `merged`). A day outside the window is ignored. With no state record, opened and merged are zero and the backlog still comes from the open list. Sources match the pull-request list.

### `GET /api/fleet/v1/prs/{number}`

`schema` is `fleet.v1.pr`. `data.pr` is the same object as one list row, or null when that pull request is not open.
