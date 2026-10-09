# Fleet board API v1

Read-only JSON API mounted at `/api/fleet/v1`. This slice publishes the
contract only: an index of routes and a JSON Schema for each response.
Later slices add the data routes. Existing unversioned fleet routes are
unchanged.

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
