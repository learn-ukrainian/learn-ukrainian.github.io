# Systemd unit templates (loopback services)

Templates only — do not commit machine-specific paths. Copy a unit into
`~/.config/systemd/user/` (linger enabled) or `/etc/systemd/system/`, replace
`@REPO_ROOT@` / `@PRIVATE_ROOT@`, `daemon-reload`, then enable/start.

Services bind `127.0.0.1` only. Reach them from another machine with an SSH
tunnel; set `MONITOR_INSTANCE_ID` in the environment so `/api/health`
distinguishes hosts. For `GET /api/occupancy`, set `MONITOR_OCCUPANCY_HOST_IDS`
to comma-separated `canonical=opaque-id` pairs (opaque values only, e.g.
`host-job`). Optional local seats: `ATLAS_JOB_SELF_HOST` or
`MONITOR_OCCUPANCY_DRIVER_HOST_ID` attaches session-stream driver leases;
`MONITOR_OCCUPANCY_MARKERS` publishes Foundry/compiler heartbeats. Do not put
addresses or SSH hostnames in the occupancy JSON.

Units are **Linux-native `Type=simple`** processes. Do not wrap
`./services.sh start` in `Type=oneshot RemainAfterExit=yes`: that is
launchd-shaped and does not supervise the listener on Linux. macOS still
uses `./services.sh supervise api` / launchd.

Public fixtures use opaque ids `host-job` and `host-teacher` only.
