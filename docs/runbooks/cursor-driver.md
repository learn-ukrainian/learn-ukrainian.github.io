# Cursor Driver Seat Runbook & Identity Charter

Parent epic: [#6952](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6952) · Scope: [#6955](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6955) · Stream: `infra-harness` ([#6943](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6943)).

## Overview

Cursor is a first-class worker and orchestrator seat in the fleet roster. Promoting Cursor to an orchestrator seat is a roster change (leases, launcher, comms, identity) using the **existing** fleet-comms plane and the common `drive-epic` playbook. It is **not** a second control program, nor a separate bus.

## Driver vs GUI Supervision

- **Canonical Driver = TUI Launcher:** The canonical Cursor driver runs as a launched TUI driver session (`start-cursor-driver.sh`, child #6956) sharing `scripts/lib/launcher_core.sh` with other driver seats. It claims the stream lease, respects lease lifecycles, and executes the standard `drive-epic` loop.
- **GUI Cursor IDE = Human Supervision Only:** GUI Cursor chat is interactive human supervision and inspection. It is **not** a second driver protocol, does not claim autonomous stream leases, and does not run an unmonitored alternate orchestration loop.

## Identity Contract & Attestation

`cursor:auto` is a dynamic harness selector, never a concrete model identity. The identity contract enforces:

1. **Attested `resolved_model` Required for Driver-of-Record:** Driver-of-record requires an attested concrete `resolved_model` extracted from the run (via headless telemetry extraction in `scripts/delegate.py` and `scripts/agent_runtime/adapters/cursor.py`). An unattested run or unknown-Auto can **never** be driver-of-record.
2. **Unknown-Auto Resolves to Allowlist-Union Family {xAI, Moonshot}:** When `cursor:auto` reports `resolved_model=unknown`, resolve its identity to the **allowlist-union family {xAI, Moonshot}** (`grok-4.6` [xAI] | `composer-2.5` [Moonshot]) instead of unattested-harness-with-quorum:
   - **Cursor-Authored PR:** Single cross-family reviewer from outside {xAI, Moonshot} (e.g. Claude, Codex/GPT, Gemini/AGY, or GLM under local-only egress). This supersedes the #6489 dual-family quorum as the default for unknown-Auto PRs (dual-family quorum text remains as fallback history).
   - **Cursor-as-Reviewer:** Eligible only against author models outside {xAI, Moonshot}.
   - **Validity Condition:** The union bound holds strictly while the Auto allowlist contract holds (~30-day catalog refresh; lint enforces the pair). Allowlist rotation invalidates the bound (refresh first).

## Auto Allowlist & ~30-Day Refresh Contract

- **Explicit Allowlist:** Auto is permitted only when it resolves within the catalog allowlist:
  - `grok-4.6`
  - `composer-2.5`
- **Catalog Refresh Contract:** The allowlist is refreshed under the catalog's ~30-day freshness contract (`scripts/config/model_catalog.yaml`, enforced by `scripts/lint/lint_model_catalog.py`). The operator does not freeze a single SKU; when Cursor's pair changes, the allowlist rotates in the catalog.

## Family Attribution for Cross-Family (CF) Checks

Cross-family independence checks evaluate either the **attested concrete model family** or the **allowlist-union family**:

- **Attested Cursor `composer-2.5`:** Belongs to the **Moonshot** family (Composer 2.5 derives from Kimi 2.5; native Kimi K3 diverged, recorded for future reassessment. Composer 2.5 conservatively shares Moonshot independence lineage with Kimi; not native Kimi).
- **Attested Cursor `grok-4.6`:** Belongs to the **xAI** family (xAI via Cursor; distinct transport from the native Grok seat).
- **Unknown `cursor:auto`:** Belongs to the **union family {xAI, Moonshot}**. Reviewers must be strictly outside both families.
- **Same-Family / Union-Family Refusal:** A review of a Cursor-authored head must refuse if the reviewer belongs to the same attested family (e.g. Kimi reviewing Composer 2.5, or Grok reviewing Cursor `grok-4.6`) or if an unknown-Auto head is reviewed by any member of {xAI, Moonshot}.

## Operating Constraints & Concurrency

- **Concurrency 1:** A Cursor driver session **is** the Cursor lane. Do not dispatch `delegate.py dispatch --agent cursor` from inside a Cursor driver session (causes deadlock on the single-concurrency lease).
- **What serializes today (investigate receipt for #6956):**
  - Epic **stream leases** fail closed on a second live driver:
    `stream {id} already has live session …` in
    `agents_extensions/shared/session_streams/store.py` (`LifecycleError`).
  - `scripts/delegate.py` `_check_capacity_hint` is **non-blocking** (docstring:
    "Non-blocking hint when dispatching to a busy lane…"); busy Cursor workers
    only emit a stderr note — they do not refuse because a Cursor driver holds
    a stream lease.
  - `scripts/config/fleet_communications.yaml` `cursor.concurrency_limit: 1` is
    endpoint metadata (surfaced by the fleet API), not a dispatch mutex.
- **Layout A Worktrees:** Implementation runs only from isolated dispatch worktrees under `.worktrees/dispatch/{agent}/{task}/`.
- **Driver Never Merges:** Drivers neither merge PRs nor arm auto-merge. The human operator retains sole merge authority.
- **Single Playbook:** No second router or alternate state machine; drivers run the standard `drive-epic` skill.

## Do-Not-Vendor List (Non-Goals)

The following tools and frameworks are explicitly rejected and must not be vendored or integrated:

- **No pstack / `/poteto-mode`:** No third-party stack-management plugins.
- **No Graphite:** No external CLI stack wrappers.
- **No Benny:** No external automated workflow bots.
- **No N-Implementation Arenas (`/arena`):** Contest is handled via `ab discuss`, followed by a single dispatched owner.
- **No Second Comms Bus:** No `cursor-discuss` or custom socket daemon; comms uses the existing C0 fleet-comms plane.

## Fleet-comms (C0)

Cursor TUI drivers talk to the **existing** message plane only. Entry point is
the primary interpreter + bridge module (same bus as every other seat — not a
second discuss API):

```bash
/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python \
  scripts/ai_agent_bridge/__main__.py discuss <channel> "<topic>" \
  --with <a>,<b> [--max-rounds N]
```

| Verb | How |
| --- | --- |
| **inbox** | `… __main__.py inbox show\|ack …` (fleet-comms dual-write) |
| **dispatch** | `scripts/delegate.py dispatch --agent <non-cursor> …` (Cursor driver holds concurrency 1 — do not self-dispatch) |
| **discuss** | `ab discuss` via the venv bridge above → ACPX controller (`LU_ACPX_TRANSPORT=active`) on the same plane |
| **receipts** | `batch_state/tasks/<task-id>.json` + channel/thread ids; Cursor receipts must carry `resolved_model` / `resolved_model_known` / `resolved_model_source` |

### ACPX / Node jail (#6953)

`node_modules/.bin/acpx` is a `#!/usr/bin/env node` shim. A jail PATH of
`/usr/bin:/bin` (no Homebrew) fails as `env: node: No such file or directory`
in ~8s / 0 tokens. The ACPX adapter now:

1. Resolves an absolute host `node` (PATH, then `/opt/homebrew/bin`,
   `/usr/local/bin`, `~/.hermes/node/bin`).
2. Spawns `[node, <acpx-entry>, …]` so the shebang is never consulted.
3. Prepends Node's directory onto the child `PATH` for nested agent shebangs.

No deploy step outside the worktree is required for this repair — it is code
on the adapter path. If `node` is absent on the host entirely, discuss fails
closed with an actionable refusal (install Node; do not invent a second bus).

### Attestation on receipts

- Attested: concrete `resolved_model` (e.g. `composer-2.5`) +
  `resolved_model_known: true` + source (`cursor-stream-json` / transcript /
  stderr-json).
- Unattested Auto: `resolved_model: "unattested-harness"`,
  `resolved_model_known: false`, `resolved_model_source: "unattested-harness"`.
  That session is **not** driver-of-record. CF for unknown-Auto worker PRs
  still follows the allowlist-union / #6489 rules in `model-assignment.md`.
