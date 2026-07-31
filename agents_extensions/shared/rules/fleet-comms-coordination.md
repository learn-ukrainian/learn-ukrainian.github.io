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
| **Seat onboarding contract** | Task-oriented ownership matrix (discuss / delegate / fleet-comms / ACPX / Buzz deferred), Kimi routes, smoke | `docs/runbooks/agent-seat-onboarding.md` |
| **`drive-epic` skill** | Method playbook (orient → topology → route → dispatch → settle → CF → merge → handoff) | `agents_extensions/shared/skills/drive-epic/SKILL.md` |
| **Epic roster runbook** | Operator seat routing (which model drives which epic) | `docs/runbooks/epic-orchestrator-roster.md` |
| **Live routing data** | Caps, ladders, formal CF pins, **live plane mode** | `/api/rules` model-assignment + `scripts/config/model_catalog.yaml` + `scripts/config/fleet_communications.yaml` + `plane-status` |
| **Launchers** | Lease claim + dual-aware pointer (not a second design) | interactive `start-*.sh`, provider `start-*-driver.sh` |

**Golden rule (from drive-epic):** rules + skill teach **method**; roster/caps/modes are
**live data** — always re-read; never hard-code from memory. Fresh supported seats start
at the **onboarding contract** for ownership and experimental ACPX scope; this rule does
**not** duplicate mutable model pins, effort ladders, or a hard-coded live plane mode.

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
7. Provider drivers inject the **`drive-epic`** binding after their lease and
   provider canary. Interactive launchers never claim a driver lease.

## Operator launch surface (#5632)

- Driver entrypoints: `./start-grok-driver.sh --epic <epic>`,
  `./start-gemini-driver.sh --epic <epic>`,
  `./start-claude-driver.sh --epic <epic> [--model claude-fable-5|claude-sonnet-5]`,
  and `./start-codex-driver.sh --epic <epic>`. Interactive launchers reject `--epic`.
- Seat routing reminder: `docs/runbooks/epic-orchestrator-roster.md` (Gemini→harness/corpus,
  Grok→atlas/tracks, Sonnet-5→judgment-dense, Opus→hardest-judgment exception only — it
  spends the cross-family review-of-record seat). **Live policy** is still
  `model_catalog.orchestrator_seats` + `/api/rules`.
- **Codex is the named alternate for the harness / infra and DevOps streams** (re-added
  2026-07-23 after HydrationCapsuleV1 changed the rollover-cost calculus). Its launcher
  fails closed before lease acquisition on ambiguous, already-resumed, or native-app
  rollover packets; a fresh CLI packet is bound to the exact SessionStart task ID and
  the generated cold-start board is injected automatically. Infra uses `epic:4707`;
  DevOps independently uses `epic:5703`. Codex never concurrently co-owns a same-stream
  lease and remains a formal-CF **review** + coding lane.

## Ownership pointer (do not invent a second design)

Supported fleet seats cold-start through:

1. This rule (binding fleet-comms musts).
2. **`docs/runbooks/agent-seat-onboarding.md`** — ownership matrix for `discuss`,
   `delegate.py dispatch`, fleet-comms + authoritative file handoffs, experimental
   ACPX (default-off/shadow, one read-only/stateless Codex participant), and
   **Buzz deferred**. Also covers Kimi native (default; K3 max-only) vs explicit
   KimiCC (K3 defaults `high`), rollback, and no-auth fresh-agent smoke.

Discussion is never formal CF. Formal CF remains `review-pr` /
`publish-review-verdict` only. ACPX is structured invocation transport, not a
coordination authority. File dual-write stays authoritative in every plane mode.

## Bounded ACP panel (approved selection)

Every supported fleet orchestrator may explicitly invoke the fixed Codex↔Grok
ACP panel for **one consequential, read-only design or risk comparison** when
that direct cross-provider critique is materially useful. Its sole surface is
`.venv/bin/python -m scripts.fleet_comms acp-discuss`; do not add automatic launcher or
`delegate.py` use. The default is two rounds and the hard maximum is three.

Admission is one conversation repository-wide: return `busy` when occupied,
with zero queue and zero automatic retry. On busy or when ACPX is unready, use
the bounded bridge `discuss` path instead. ACP output is deliberation evidence:
a typed partial outcome is valid evidence but never a successful discussion,
formal review, or coordination authority. The exact command, primary-install
and body-free `acp-verify` E2E/replay procedure are in the onboarding contract.

## Offline fallback path

`agents_extensions/shared/rules/fleet-comms-coordination.md` (this file).
Served in `GET /api/rules` (`scripts/api/rules_router.py` `RULE_SOURCES`).
Onboarding contract (not served as a rules blob; linked from this rule):
`docs/runbooks/agent-seat-onboarding.md`.

</critical>
