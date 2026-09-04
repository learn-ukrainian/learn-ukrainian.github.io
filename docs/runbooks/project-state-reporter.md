# Project-state reporter timers (#7188 / #7177)

Per-host checkout and serving-SHA drift reaches the Monitor API through a
loopback-only push reporter on each machine. The API host evaluates itself
in-process on every `GET /api/fleet/projects/v1` read (empty-map Linux fills
the production glance row `host-teacher`); remote hosts POST sanitized
documents to `POST /api/fleet/projects/v1/report` through the existing
loopback tunnel. Do **not** report as `host-job` — that opaque id is not a
default glance row and returns `400 unknown host_id` unless mapped.

## Reporter CLI

On the production Linux API host, in-process collect is enough; an optional
loopback POST may use the production opaque id:

```bash
LU_MONITOR_HOST_ID=host-teacher \
  .venv/bin/python scripts/api/project_state_local.py report
```

Or omit `LU_MONITOR_HOST_ID` when `MONITOR_OCCUPANCY_HOST_IDS` is unset — the
launcher resolves to `host-teacher` on Linux / `mac-operator` on Darwin.

Dry-run collection only:

```bash
.venv/bin/python scripts/api/project_state_local.py collect --dry-run
```

The reporter identity is the opaque host id from `LU_MONITOR_HOST_ID`,
`MONITOR_OCCUPANCY_DRIVER_HOST_ID`, or the single self-mapped entry in
`MONITOR_OCCUPANCY_HOST_IDS`. With an empty map, Linux resolves to
`host-teacher` and Darwin to `mac-operator`. `mac-operator` is also
allowlisted without a mapping entry.

## Linux (systemd timer)

Templates live in `packaging/systemd/`:

- `learn-ukrainian-project-state-reporter.service` (oneshot)
- `learn-ukrainian-project-state-reporter.timer` (5-minute cadence)

### One-line operator install

```bash
install -Dm644 packaging/systemd/learn-ukrainian-project-state-reporter.{service,timer} \
  ~/.config/systemd/user/ && systemctl --user daemon-reload && \
  systemctl --user enable --now learn-ukrainian-project-state-reporter.timer
```

Set `WorkingDirectory` / the wrapper path to the primary checkout if the
template `%h/projects/learn-ukrainian` placeholder differs. Prefer leaving
`LU_MONITOR_HOST_ID` unset on the API host (in-process fill), or set
`LU_MONITOR_HOST_ID=host-teacher` — never `host-job`.

The wrapper script is `scripts/orchestration/run_project_state_reporter.sh`.

## macOS (LaunchAgent)

```bash
.venv/bin/python scripts/orchestration/install_mac_project_state_launchd.py
```

Uses the same bash wrapper as systemd. Default interval is 5 minutes. Logs land
under `~/.codex/project-state-reporter/logs/`.

## Freshness and drift semantics

- Remote reports expire after **15 minutes** without a heartbeat (`freshness:
  unknown`).
- `origin_main_age_s` comes from local `refs/remotes/origin/main` plus
  `FETCH_HEAD` mtime; values above **3600** seconds degrade every drift verdict
  to `unknown` and add a `stale_upstream` attention item.
- Per service: `state != running` ⇒ drift `unknown`; sibling `work` repo ⇒
  `not_applicable`; release mode compares `serving_sha` to `origin_main_sha`;
  checkout mode compares `checkout_sha` and is badged `checkout` in
  `fleet.html`.

Deploying timers on live hosts is an operator step; this repository only ships
templates and the CLI.
