# Systemd unit templates (loopback services)

Templates only — do not commit machine-specific paths. Copy a unit into
`/etc/systemd/system/` (or `~/.config/systemd/user/`), replace `@REPO_ROOT@`
with the checkout path, run `systemctl daemon-reload`, then enable/start.

Services bind `127.0.0.1` only. Reach them from another machine with an SSH
tunnel; set `MONITOR_INSTANCE_ID` in the environment so `/api/health`
distinguishes hosts.

Units invoke `./services.sh` start/stop semantics from the repo root.
