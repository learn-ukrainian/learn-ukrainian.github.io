# VPS localhost services — Step 1 runbook

> **DRAFT — pending Fable/Sol + operator GO.** Do not execute migration, bind
> ports on a public interface, or treat this document as approved infrastructure
> policy until advisors and the operator sign off.

**Audience:** infra drivers, operators planning service topology, anyone
tempted to assume the Monitor API always runs on the operator laptop.
**Status:** draft planning only — **no implementation in this step.**
**Related:** [`grok-bot-qa-observer.md`](grok-bot-qa-observer.md) (Grok Bot
contract unchanged) · [`local-api-server.md`](../best-practices/local-api-server.md)
· [`docs/monitor-api/work.md`](../monitor-api/work.md) · [`MONITOR-API.md`](../MONITOR-API.md)
§ Service Boundaries.

---

## Goal

Keep project services running **without requiring the operator laptop to stay
awake**. A small Hetzner VPS is the preferred target: it costs less than buying
a new Mac solely to host always-on local services, and it separates long-running
dev infrastructure from interactive driver sessions.

This runbook covers **Step 1 only**: run the existing public and private
`services.sh` stacks on the VPS with **loopback binds** and **SSH tunnel**
access from laptops. It does not relocate fleet worktrees, agent harnesses, or
orchestration authority.

---

## Step 1 scope (this runbook)

| In scope | Out of scope (later + advisor-gated) |
| --- | --- |
| Migrate **public** repo `services.sh` to the VPS | Fleet dispatch worktrees on the VPS |
| Migrate **private** sibling repo `services.sh` to the VPS | Grok Bot as orchestrator (current GO: **observer only** — see [`grok-bot-qa-observer.md`](grok-bot-qa-observer.md)) |
| Every managed listener binds **`127.0.0.1` only** | Changing the Grok Bot contract |
| Operator/driver access via **SSH local port forwarding** only | Exposing services on `0.0.0.0` or a public hostname |
| Fix the public Monitor API bind bug (see below) | systemd/launchd parity decisions beyond loopback + tunnel |

---

## Service table (loopback on VPS)

All ports listen on **`127.0.0.1`** on the VPS unless noted. Drivers reach them
through SSH `-L` forwards; nothing in this step is internet-facing.

| Service | Port | Repo / script | Role |
| --- | --- | --- | --- |
| **api** (Monitor) | `8765` | public `./services.sh` | FastAPI Monitor — orient, state, comms, work projection seam, dashboards |
| **sources** (MCP) | `8766` | public `./services.sh` | SQLite FTS5 MCP server (textbooks, dicts, literary, Wikipedia) |
| **work** (private adapter) | `8769` | public `./services.sh` starts sibling private checkout | Read-only Work projection adapter (`../learn-ukrainian-infra-private` or `LEARN_UKRAINIAN_INFRA_PRIVATE_ROOT`) |
| **astro** (Course UI dev) | `4321` | public `./services.sh` | Astro dev server (`npm run dev -- --host 127.0.0.1`) |
| **hramatka** (private teacher HTTPS) | `8443`, `8788` | **private** `./services.sh` | Hramatka lesson support, linguistics verification, teacher dashboard (`/api/hramatka/*`) — **not** mounted on the public Monitor process |

Public `./services.sh start` already binds **astro** and **work** to loopback.
**sources** health checks target loopback. The **api** service is the outlier
today.

---

## Known bug — public api must move to loopback

Public `services.sh` currently starts the Monitor API with **`--host 0.0.0.0`**:

```64:70:services.sh
SVC_CMD[api]="$VENV/python -m uvicorn scripts.api.main:app --host 0.0.0.0 --port 8765 --log-config scripts/api/logging.json --timeout-graceful-shutdown 8"
SVC_PORT[api]=8765
SVC_LOG[api]="$LOGS_DIR/api.log"
SVC_DESC[api]="API Dashboard Server (FastAPI)"
SVC_HEALTH[api]="http://127.0.0.1:8765/api/health"
SVC_HEALTH_ALT[api]="http://localhost:8765/api/health"
SVC_MATCH[api]="scripts.api.main:app --host 0.0.0.0 --port 8765"
```

**Step 1 must change api to `--host 127.0.0.1`** (and update `SVC_HOST[api]`,
health probes, and `SVC_MATCH` accordingly) before or as part of VPS cutover.
Binding `0.0.0.0` on a remote host would expose the Monitor API on the VPS
network interface — incompatible with SSH-tunnel-only access.

Implementation of that fix is **not** part of this draft document; it is a
prerequisite called out for the approved migration step.

---

## SSH tunnel access (examples)

Replace `user@vps` with the operator's SSH alias or account configured in
`~/.ssh/config`. **Do not commit real IPs, hostnames, or infrastructure
identifiers** to the repository.

### Core public stack

Forward Monitor, Sources, Work adapter, and Astro:

```bash
ssh -L 8765:127.0.0.1:8765 \
    -L 8766:127.0.0.1:8766 \
    -L 8769:127.0.0.1:8769 \
    -L 4321:127.0.0.1:4321 \
    user@vps
```

With the tunnel up, local tools keep using familiar URLs:

- Monitor: `http://127.0.0.1:8765/`
- Sources MCP health: `http://127.0.0.1:8766/health`
- Work adapter: `http://127.0.0.1:8769/v1/health`
- Astro dev: `http://127.0.0.1:4321/`

Set `AB_MONITOR_URL=http://127.0.0.1:8765/api/state/summary` (or
`http://localhost:8765/...`) on the **laptop** when the tunnel is active —
same as today, but the processes run on the VPS.

### Private hramatka (separate checkout)

When the private repo's `./services.sh` runs on the VPS, forward its HTTPS
loopback ports separately (exact service names follow the private repo's
`services.sh`; public Monitor docs reference **`127.0.0.1:8443`** and
**`127.0.0.1:8788`**):

```bash
ssh -L 8443:127.0.0.1:8443 \
    -L 8788:127.0.0.1:8788 \
    user@vps
```

Combine forwards in one session when both public and private stacks are needed.

---

## Driver assumptions after Step 1

| Assumption | Correct after Step 1 |
| --- | --- |
| "Monitor always runs on the Mac primary checkout" | **No.** Monitor may run on the VPS; the laptop uses SSH tunnels. |
| "`curl localhost:8765` works without a tunnel" | Only when services run locally **or** the tunnel is up. |
| "Cold-start scripts can skip tunnel checks" | Drivers should verify reachability (`curl --max-time 2 http://127.0.0.1:8765/api/health`) and distinguish **tunnel down** from **service down**. |
| "Grok Bot can drive dispatches from the VPS" | **No.** Grok Bot remains an external QA observer per [`grok-bot-qa-observer.md`](grok-bot-qa-observer.md). |

---

## Migration checklist (planning — not executed in this draft)

Use this as the implementation outline **after** advisor + operator GO:

1. **Advisor GO** on loopback-only binds and SSH-tunnel-only access model.
2. **Fix api bind** to `127.0.0.1` in public `services.sh` (and dependent docs that still prescribe `0.0.0.0`).
3. **Provision VPS** checkout(s): public repo + private sibling with venvs and data prerequisites documented in existing runbooks ([`storage-topology.md`](storage-topology.md), [`recovery.md`](recovery.md)).
4. **Start services on VPS** via `./services.sh start` (public) and private `./services.sh` for hramatka — confirm `./services.sh status` shows loopback ports only.
5. **Validate from laptop** through SSH forwards: health endpoints, orient lean, Sources MCP, Work adapter CORS contract (`Origin: http://127.0.0.1:8765`).
6. **Document operator SSH alias** in private operator notes only — not in the public repo.
7. **Retire** always-on Mac launchd Monitor job only after parallel soak and explicit operator cutover (see [`launchd-inventory.md`](launchd-inventory.md)).

---

## Explicit non-goals (later steps)

- **Fleet worktrees on VPS** — dispatch worktrees stay under layout A on driver
  machines until a separate plan approves remote harness hosting.
- **Grok Bot as orchestrator** — contradicts current operator GO; see
  [`grok-bot-qa-observer.md`](grok-bot-qa-observer.md).
- **Public ingress / TLS termination** for Monitor or Sources — Step 1 is
  loopback + SSH only.
- **Changing Grok Bot contract** — this runbook does not modify observer
  boundaries, labels, or filing rules.

---

## Status

| Item | State |
| --- | --- |
| Runbook | **DRAFT** |
| Advisor review (Fable / Sol) | Pending |
| Operator GO to implement | Pending |
| Code / infra changes | **None** in this dispatch — documentation only |
