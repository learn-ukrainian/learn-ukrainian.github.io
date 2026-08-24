# Project-state reporter timers (#7188)

Per-host checkout and serving-SHA drift reaches the Monitor API through a
loopback-only push reporter on each machine. The API host evaluates itself
in-process on every `GET /api/fleet/projects/v1` read; remote hosts POST
sanitized documents to `POST /api/fleet/projects/v1/report` through the
existing loopback tunnel.

## Reporter CLI

```bash
LU_MONITOR_HOST_ID=host-job \
  .venv/bin/python scripts/api/project_state_local.py report
```

Dry-run collection only:

```bash
.venv/bin/python scripts/api/project_state_local.py collect --dry-run
```

The reporter identity is the opaque host id from `LU_MONITOR_HOST_ID`,
`MONITOR_OCCUPANCY_DRIVER_HOST_ID`, or the single self-mapped entry in
`MONITOR_OCCUPANCY_HOST_IDS`. `mac-operator` is also allowlisted without a
mapping entry.

## Linux (systemd timer)

Templates live in `packaging/systemd/`:

- `learn-ukrainian-project-state-reporter.service` (oneshot)
- `learn-ukrainian-project-state-reporter.timer` (5-minute cadence)

Install is operator-owned: copy units into the user or system unit path, set
`WorkingDirectory` and `ExecStart` to the primary checkout, enable the timer,
and verify loopback POST succeeds. The wrapper script is
`scripts/orchestration/run_project_state_reporter.sh`.

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
