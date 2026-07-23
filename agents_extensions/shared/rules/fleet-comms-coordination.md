# Fleet-comms coordination (binding mid-cutover)

<critical>

**Product epic:** #5512 · **Stream:** #4707 (infra-harness) · **Sol memo:** `SHIP-THIS-ARCHITECTURE`  
**Applies to:** every standalone TUI/UI and epic-driver seat (Claude/Sonnet, Grok, AGY/Gemini, Kimi, Cursor, wrappers) — not only agents that load a skill.

This is the **shared-context SSOT** for coordination during the fleet-comms cutover. It is
served in `GET /api/rules`. Launchers inject a short pointer; the **`drive-epic` skill**
teaches the full method loop. Neither may invent a competing design or silently flip
cutovers.

Aligned with the post-#5632 surface (drive-epic + per-model drive wrappers + Sol CF on
that skill). Do not reintroduce claims Sol rejected (see §Plane modes).

## Layering (do not conflate)

| Layer | Role | Where |
| --- | --- | --- |
| **This rule** | Binding musts for every TUI/UI cold-start | `/api/rules` + offline path |
| **`drive-epic` skill** | Method playbook (orient → topology → route → dispatch → settle → CF → merge → handoff) | `agents_extensions/shared/skills/drive-epic/SKILL.md` |
| **Epic roster runbook** | Operator seat routing (which model drives which epic) | `docs/runbooks/epic-orchestrator-roster.md` |
| **Live routing data** | Caps, ladders, formal CF pins | `/api/rules` model-assignment + `scripts/config/model_catalog.yaml` + `scripts/config/fleet_communications.yaml` |
| **Launchers** | Lease claim + dual-aware pointer (not a second design) | `start-*.sh`, `start-*-drive.sh` |

**Golden rule (from drive-epic):** rules + skill teach **method**; roster/caps are **live
data** — always re-read; never hard-code from memory.

## Two halves (do not conflate)

| Half | Status | Surfaces |
| --- | --- | --- |
| **Session stream / lease** | Live | `claim_session_supervisor_env`, `SESSION_STREAM_*`, stream tail/digest, canary mint (hook-less seats) |
| **Message plane + CF-comms** | Mid-cutover | `scripts.fleet_comms`, `review-pr`, `publish-review-verdict` |

Launchers already claim leases. Drivers must **also** speak the message-plane + CF half.

## Plane modes (Sol-corrected — #5632 F003)

```bash
.venv/bin/python -m scripts.fleet_comms plane-status
```

Implemented modes are **only** `off` | `shadow` | `dual_write`. Production default is
**`shadow`** after Gate A parity + operator finish GO (2026-07-23); override with
`FLEET_COMMS_MESSAGE_PLANE=off|dual_write`.

| Fact | Binding |
| --- | --- |
| File dual-write / diary | **Stays authoritative in every plane mode** today |
| `dual_write` mode | Shadow/mirror of plane traffic — **not** stream-authority cutover |
| Post-cutover “plane-only authority” | **Not implemented** — do not claim a one-line yaml flip retires files |
| Who may flip plane / retention apply / eligibility | **Infra/harness lane** after parity + present-tense operator/advisor GO |

**Never drop the file handoff on your own.** Retiring file handoffs is a future infra step
gated on an authority signal the plane does not yet expose.

Forbidden: inventing a third message bus; encoding only file-handoff folklore in new
cold-prompts; silent plane flips; “for now” cutovers.

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

# Formal cross-family CF — PR number is REQUIRED and positional
.venv/bin/python -m scripts.ai_agent_bridge review-pr <PR_NUMBER> --reviewer codex|claude|glm
.venv/bin/python -m scripts.ai_agent_bridge publish-review-verdict ...
```

- **agy | kimi | grok** remain `formal_review_eligible: false` until isolation proofs
  (#5555–#5557). They **request** CF via `review-pr`; they do not self-seal.
- Escalate hard/non-routine CF with Sol / Fable (`--model gpt-5.6-sol` or `claude-fable-5`
  `--effort xhigh`) per model-assignment.

## Standalone TUI/UI contract

Every epic driver session (any harness) MUST:

1. Obey this rule (via `/api/rules` or offline fallback of this file).
2. Run `plane-status` before assuming message-plane availability.
3. Prefer plane/CF **command surfaces** for topology and formal review; **keep** the lane
   diary dual-write current (`.claude/<epic>-epic/*-DRIVER-HANDOFF.md` and stream notes)
   in **all** plane modes.
4. Use `review-pr <PR_NUMBER> …` / `publish-review-verdict` for formal PR CF — discussion
   and same-family chat are not the review gate.
5. Treat launcher-claimed stream leases as held — do not open/resume the lease yourself.
6. **Session health by seat:**
   - **grok / gemini / kimi:** canary mint/score
     (`.venv/bin/python -m scripts.session_canary.{grok,gemini,kimi}_lane …`); end on
     FAIL-HANDOFF (&lt;8/10), not compact count.
   - **Claude / Sonnet:** SessionStart / PostCompact + thread-handoff — **no** canary lane
     (do not invent `<model>_lane`).
7. When driving an epic end-to-end, load the **`drive-epic`** skill for the method loop
   (wrappers `start-*-drive.sh` do not auto-load it yet — invoke `$drive-epic` until
   cold-prompt wiring lands).

## Operator launch surface (#5632)

- Per-model driver: `./start-grok-drive.sh <epic>`, `./start-gemini-drive.sh <epic>`,
  `./start-sonnet-drive.sh <epic>` (thin wrappers over `start-*.sh --epic`).
- Seat routing reminder: `docs/runbooks/epic-orchestrator-roster.md` (Gemini→harness/corpus,
  Grok→atlas/tracks, Sonnet-5→judgment-dense). **Live policy** is still
  `model_catalog.orchestrator_seats` + `/api/rules`.
- **Codex is not a driver seat** (dropped 2026-07-22: 272K window vs rollover cost). Codex
  remains a formal-CF **review** + coding lane. Do not launch Codex as a continuous
  epic-driver loop.

## Offline fallback path

`agents_extensions/shared/rules/fleet-comms-coordination.md` (this file).  
Served in `GET /api/rules` (`scripts/api/rules_router.py` `RULE_SOURCES`).

</critical>
