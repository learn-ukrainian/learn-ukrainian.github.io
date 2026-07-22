# Fleet-comms coordination (binding mid-cutover)

<critical>

**Product epic:** #5512 · **Stream:** #4707 (infra-harness) · **Sol memo:** `SHIP-THIS-ARCHITECTURE`  
**Applies to:** every standalone TUI/UI and orchestrator seat (Claude, Codex, Grok, AGY/Gemini, Kimi, Cursor, wrappers) — not only agents that load a skill.

This is the **shared-context SSOT** for coordination during the fleet-comms cutover. Launchers may inject a short pointer; skills teach method (`drive-epic`); neither may invent a competing design or silently flip cutovers.

## Two halves (do not conflate)

| Half | Status | Surfaces |
| --- | --- | --- |
| **Session stream / lease** | Live | `claim_session_supervisor_env`, `SESSION_STREAM_*`, stream tail/digest, canary mint |
| **Message plane + CF-comms** | Mid-cutover | `scripts.fleet_comms`, `review-pr`, `publish-review-verdict` |

Launchers already claim leases. Drivers must **also** speak the message-plane + CF half — prefer plane when enabled; fall back to file dual-write while plane is off.

## Dual-aware cutover (operator/advisor gated)

1. **Check first (every cold-start / before coordination decisions):**
   ```bash
   .venv/bin/python -m scripts.fleet_comms plane-status
   ```
   Modes: `off` | `shadow` | `dual_write`. Default remains **`off`** until parity receipt + present-tense operator/advisor GO.

2. **While `mode=off` (current production):**
   - Prefer plane/CF **command surfaces** for topology, metrics, and formal review.
   - **File dual-write remains authoritative** for continuity diaries  
     (`.claude/<epic>-epic/*-DRIVER-HANDOFF.md`, stream dual-write, `docs/session-state/` pointers).
   - Do **not** treat streams as sole authority; do **not** retire file handoffs.
   - Do **not** set `FLEET_COMMS_MESSAGE_PLANE=dual_write` (or flip stream-authority / `formal_review_eligible`) without GO.

3. **When plane is `shadow` or `dual_write`:** prefer plane for coordination; keep diary dual-write until stream-authority cutover is explicitly approved. Drop file-handoff folklore as the primary coordination path after that cutover — a config/process flip, not a new design.

4. **Forbidden:** inventing a third message bus, encoding only file-handoff folklore in new cold-prompts, or “for now” plane flips.

## Required primitives (tool-backed)

```bash
# Topology / health / parity
.venv/bin/python -m scripts.fleet_comms plane-status
.venv/bin/python -m scripts.fleet_comms metrics
.venv/bin/python -m scripts.fleet_comms backlog
.venv/bin/python -m scripts.fleet_comms dead-letters

# Continuity (lease already claimed by launcher — do not re-open)
.venv/bin/python -m agents_extensions.shared.session_streams tail --stream epic:<N> --limit 20
.venv/bin/python -m agents_extensions.shared.session_streams dual-write-status

# Formal cross-family CF (never self-seal; agy|kimi|grok stay fail-closed until isolation proofs)
.venv/bin/python -m scripts.ai_agent_bridge review-pr <N> --reviewer codex|claude|glm
.venv/bin/python -m scripts.ai_agent_bridge publish-review-verdict ...
```

Live routing seats remain in `model-assignment.md` (this same `/api/rules` blob). Isolation fail-closed matrix: #5555–#5557.

## Standalone TUI/UI contract

Every epic driver session (any harness) MUST:

1. Obey this rule (via `/api/rules` or offline fallback of this file).
2. Run `plane-status` before assuming message-plane availability.
3. Use `review-pr` / `publish-review-verdict` for formal PR CF — not “ask the same family to rubber-stamp.”
4. Dual-write the lane diary while files are authoritative; stamp after each batch.
5. Treat launcher-claimed stream leases as held — do not open/resume the lease yourself.

Optional method playbook: skill `drive-epic` (when installed). Skills are **not** a substitute for this rule.

## Offline fallback path

`agents_extensions/shared/rules/fleet-comms-coordination.md` (this file).  
Served in `GET /api/rules` (`scripts/api/rules_router.py` `RULE_SOURCES`).

</critical>
