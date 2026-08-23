# macOS LaunchAgent templates (loopback observer heartbeat)

Templates and installers for macOS LaunchAgents.

## `com.learn-ukrainian.mac-observer-heartbeat`

Supervises background observer presence heartbeats for live Mac GUI sessions (Cursor IDE and Codex UI).
When Cursor or Codex GUI apps are active, sends periodic heartbeats to `POST /api/observer/presence`
over the loopback monitor tunnel (`http://127.0.0.1:8765`), keeping their presence alive under `cloud-observer`
in `/api/occupancy` with `status=idle` and TTL ≤15m.

To install or manage:
```bash
.venv/bin/python scripts/orchestration/install_mac_observer_launchd.py install
.venv/bin/python scripts/orchestration/install_mac_observer_launchd.py status
.venv/bin/python scripts/orchestration/install_mac_observer_launchd.py uninstall
```
