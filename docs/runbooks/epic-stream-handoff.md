# Epic stream handoff (cross-agent)

**Issue:** #5530 · parent #5531 · long-term home: fleet-comms #5512 (Sol PR-I supervisor)

## Problem

Thread rollover packets transfer **one harness thread**. Epic session streams
transfer **driver authority for a product lane** (`epic:N`). When an interim
driver (e.g. Codex on hramatka) leaves, content dual-write alone is not enough:

- lease can stay `active` after TTL expires with a **dead PID**
- pins can still name the interim driver
- successor launched without `--epic` has no stream
- multi-packet rollover detect (#5398) can hide or mis-pick packets

## Contract (v0)

1. **Predecessor** clean-exits (`hook close`) **or** successor runs **proof-gated
   force-close** (holder PID dead **and** claimer is a distinct live instance;
   wall-clock TTL need not have expired — a dead process cannot renew).
2. **Successor opens a NEW session/lease** on the same `epic:N` — never reopens a
   closed session.
3. **Pin transfer:** append a binding order that names the new driver; do not leave
   “interim until return” as the only ownership signal.
4. **Dual-write:** predecessor `STATE AT HANDBACK`; successor folds into its own
   board (e.g. `CLAUDE-DRIVER-HANDOFF.md`).
5. **Rollover:** if packets exist, bind **exact** lineage/rollover IDs. With N>1
   pending for an agent, never silent single-select (#5398).
6. **Launcher:** `--epic <name>` must set stream id + handoff slot. Note the
   slot trap: a packet under `claude/` may not appear under `claude-hramatka`.

## Remote lease and handoff authority

Driver leases are claimed on the API host through `/api/epics/v1`; remote mode
is the default. `--local` is offline-only, prints a warning, and does not make
the lease visible to other machines. Handoffs are appended with
`POST /api/epics/v1/epic:<N>/handoff`.

A driver on any machine resumes by launching with `--epic <name>` and claiming
the same remote stream. It then reads the current holder, lease state, and
latest digest at SessionStart, and writes the next typed handoff through the
API. The remote API host is the lease authority; local files remain the
thread-rollover and lane handoff context, not a competing lease store.

Every host must export `LU_MONITOR_HOST_ID=<opaque id>` before claiming. The
value must be one of the opaque IDs in the canonical `MONITOR_OCCUPANCY_HOST_IDS`
mapping (for example, `host-teacher`, `host-job`, or `mac-operator`) so the
holder is not reported as `local`. Do not use a hostname, alias, or IP address
as the host ID.

### Codex DevOps zero-touch boundary

`./start-codex-driver.sh --epic devops` scans only its assigned `codex-devops` rollover
namespace before acquiring `epic:5703`. Infra keeps the separate `codex-infra`
namespace and `epic:6943` lease, so a live Infra driver does not block DevOps.
The launcher starts a fresh task when no packet
exists, or exports one exact fresh unbound `codex-cli` packet for SessionStart
to bind to the newly created task ID. Multiple packets, an already-resumed
packet, and a packet requiring the native Codex app adapter all stop the
launcher before lease acquisition. The launcher never invokes `codex resume`
or selects a packet by title, age, or filesystem order.

## CLI

```bash
# Remote claim (the API host owns the lease; set the opaque host identity first)
LU_MONITOR_HOST_ID="<opaque id>" \
  .venv/bin/python -m scripts.session_supervisor claim \
  --role driver --stream epic:4542 \
  --agent claude --harness claude-code \
  --instance-id example-driver --process-id 1234 \
  --lineage-id example-lineage

# Typed handoff: POST /api/epics/v1/epic:4542/handoff
```

The driver launcher normally performs the claim. `--local` is the explicit
offline fallback and prints its warning; it is not a remote handoff path.

## Manual checklist (until CLI is habitual)

1. Read `GET /api/epics/v1/epic:<N>` or the equivalent SessionStart remote state.
2. If the remote holder is expired/released, relaunch with `--epic <name>` and
   claim the stream; no local store promotion is needed.
3. If a live foreign holder remains, **stop** — ask that driver to close.
4. Read the remote digest surfaced at SessionStart and fold it into your handoff file.
5. Bind exact rollover IDs if any, then drive.
6. Append a typed `POST …/handoff` after each batch and cleanly release on end.

## Related

- `docs/runbooks/grok-session-canary.md` — end on measured rot, not compact count
- `docs/best-practices/codex-thread-handoff.md` — thread rollover (different layer)
- `.claude/<epic>-epic/TAKEOVER-PROTOCOL.md` — lane-specific interim rules (hramatka)
