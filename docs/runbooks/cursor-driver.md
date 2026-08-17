# Cursor Driver Seat Runbook & Identity Charter

Parent epic: [#6952](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6952) · Scope: [#6955](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6955) · Stream: `infra-harness` ([#6943](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6943)).

## Overview

Cursor is a first-class worker and orchestrator seat in the fleet roster. Promoting Cursor to an orchestrator seat is a roster change (leases, launcher, comms, identity) using the **existing** fleet-comms plane and the common `drive-epic` playbook. It is **not** a second control program, nor a separate bus.

## Driver vs GUI Supervision

- **Canonical Driver = TUI Launcher:** The canonical Cursor driver runs as a launched TUI driver session (`start-cursor-driver.sh`, child #6956) sharing `scripts/lib/launcher_core.sh` with other driver seats. It claims the stream lease, respects lease lifecycles, and executes the standard `drive-epic` loop.
- **GUI Cursor IDE = Human Supervision Only:** GUI Cursor chat is interactive human supervision and inspection. It is **not** a second driver protocol, does not claim autonomous stream leases, and does not run an unmonitored alternate orchestration loop.

## Identity Contract & Attestation

`cursor:auto` is a dynamic harness selector, never a concrete model identity. The identity contract enforces:

1. **Attested `resolved_model` Required:** Driver-of-record and single-reviewer cross-family (CF) review require an attested concrete `resolved_model` extracted from the run (via headless telemetry extraction in `scripts/delegate.py` and `scripts/agent_runtime/adapters/cursor.py`).
2. **Unattested Auto Fails Closed:** `cursor:auto` with `resolved_model=null` (or an unrecognized selector) is classified as `unattested-harness`. An unattested harness can **never** be driver-of-record and can **never** serve as a formal cross-family review identity.
3. **Dual-Family Quorum for Worker PRs (#6489):** The dual-family quorum rule remains unchanged as the fallback for already-authored Auto **worker** PRs. A driver-of-record cannot use the quorum fallback; driver identity must be attested.

## Auto Allowlist & ~30-Day Refresh Contract

- **Explicit Allowlist:** Auto is permitted only when it resolves within the catalog allowlist:
  - `grok-4.6`
  - `composer-2.5`
- **Catalog Refresh Contract:** The allowlist is refreshed under the catalog's ~30-day freshness contract (`scripts/config/model_catalog.yaml`, enforced by `scripts/lint/lint_model_catalog.py`). The operator does not freeze a single SKU; when Cursor's pair changes, the allowlist rotates in the catalog.

## Family Attribution for Cross-Family (CF) Checks

Cross-family independence checks evaluate the **attested concrete model family**, never the harness name (`cursor`):

- **Cursor `composer-2.5`:** Belongs to the **Moonshot** family (conservatively shares Moonshot independence lineage with Kimi; not native Kimi).
- **Cursor `grok-4.6`:** Belongs to the **xAI** family (xAI via Cursor; distinct transport from the native Grok seat).
- **Same-Family Refusal:** A review of a Cursor-authored head must refuse if the reviewer belongs to the same attested family (e.g. Kimi reviewing Composer 2.5, or Grok reviewing Cursor `grok-4.6`).

## Operating Constraints & Concurrency

- **Concurrency 1:** A Cursor driver session **is** the Cursor lane. Do not dispatch `delegate.py dispatch --agent cursor` from inside a Cursor driver session (causes deadlock on the single-concurrency lease).
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
