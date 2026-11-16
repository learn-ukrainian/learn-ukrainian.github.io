# macOS LaunchAgent templates (loopback observer heartbeat)

> **Roots for `lu_machinery` commands.** Commands on this page that run `lu_machinery.*` modules use the installed lu-machinery release. It reads the product checkout from `LU_PRODUCT_ROOT` and the shared-state anchor from `LEARN_UKRAINIAN_PRIMARY_REPO_ROOT`; launcher sessions and dispatched workers set both. In any other shell, run them from the product checkout after:
>
> ```bash
> export LU_PRODUCT_ROOT="$PWD" LEARN_UKRAINIAN_PRIMARY_REPO_ROOT="${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:-$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")}"
> ```

Templates and installers for macOS LaunchAgents.

## `com.learn-ukrainian.mac-observer-heartbeat`

Supervises background observer presence heartbeats for live Mac GUI sessions (Cursor IDE and Codex UI).
When Cursor or Codex GUI apps are active, sends periodic heartbeats to `POST /api/observer/presence`
over the loopback monitor tunnel (`http://127.0.0.1:8765`), keeping their presence alive under `cloud-observer`
in `/api/occupancy` with `status=idle` and TTL ≤15m.

To install or manage:
```bash
.venv/bin/python -m lu_machinery.orchestration.install_mac_observer_launchd install
.venv/bin/python -m lu_machinery.orchestration.install_mac_observer_launchd status
.venv/bin/python -m lu_machinery.orchestration.install_mac_observer_launchd uninstall
```
