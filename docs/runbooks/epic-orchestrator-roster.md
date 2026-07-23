# Epic-orchestrator routing — which model drives which epic

**Audience:** operator (you) + any agent launched as an epic/track driver.
**Companion skill:** [`drive-epic`](../../agents_extensions/shared/skills/drive-epic/SKILL.md)
— the model-agnostic playbook every driver runs.
**Per-model launch detail:** [`gemini-orchestrator.md`](gemini-orchestrator.md),
[`grok-session-canary.md`](grok-session-canary.md), [`epic-stream-handoff.md`](epic-stream-handoff.md).

There is no standing orchestrator "loop" process. **An orchestrator = a driver session
you launch.** You pick the model from the routing table below, then run
`./start-<model>-drive.sh <epic>`. The launcher claims the stream lease, mints a canary,
and cold-starts the driver, which runs the `drive-epic` skill to orchestrate its lane.

---

## Routing reminder — pick the seat, pass the epic

| Epic | Recommended seat | Run |
| --- | --- | --- |
| **harness / infra / devops** | Gemini (AGY) | `./start-gemini-drive.sh devops` |
| **harness / infra / devops** (named alternate) | Codex / gpt-5.6-terra | `./start-codex-drive.sh devops` |
| **corpus** (acquisition & ingestion) | Gemini (AGY) | `./start-gemini-drive.sh corpus` |
| **atlas** (Word Atlas + Practice Hub product) | Grok 4.5 | `./start-grok-drive.sh atlas` |
| **hramatka** (teacher lesson service) | Grok 4.5 · Sonnet-5 if judgment-heavy | `./start-grok-drive.sh hramatka` |
| **folk** (curriculum track) | Grok 4.5 † | `./start-grok-drive.sh folk` |
| **bio** (curriculum track) | Grok 4.5 | `./start-grok-drive.sh bio` |
| **any epic** — incident · architecture cutover · contested review | Sonnet-5 (Opus for the hardest) | `./start-sonnet-drive.sh <epic>` |

**Per-model launcher convention:** `./start-<model>-drive.sh <epic>` where `<model>` ∈
`codex · grok · gemini · sonnet`. Epic is the first arg; extra flags forward
(e.g. `--agent curriculum-track-orchestrator`). Each **launches the lane**; the driver
then loads `$drive-epic` — automatically once the cold-prompt wiring lands (follow-up PR),
and by manual `$drive-epic` invocation until then. The Codex DevOps alternate is the
first zero-touch path: its generated board is injected into SessionStart and explicitly
directs the task to load `$drive-epic`; the other wrappers do not yet auto-load the skill.

**Sonnet-5 is the sole Anthropic driver seat** — there is deliberately no Opus "drive"
wrapper (Opus is reserved; see below). For the rare hardest-session Opus-in-seat, use the
raw `./start-claude.sh --epic <x>`. The legacy `scripts/start-bio-driver.sh` runs Claude +
the `curriculum-track-orchestrator` agent-def if you specifically want that agent.

† **folk carve-out:** the *driver* may be Grok, but folk content **review** stays
cross-family **GPT ↔ Claude** (no DeepSeek, and Grok is never a judge seat) — the
`drive-epic` skill enforces this.

**Recommended against as a driver seat (least-bite — the live `model_catalog.orchestrator_seats` policy is authoritative):**
- **Opus 4.8** — hardest judgment + the cross-family review of record. Don't burn it on a polling loop.
- **Kimi K2.7** 256K — under the ~500K window we want for a driver. **Codex (GPT-5.6)** was
  dropped on 2026-07-22 for its 272K window, then **re-added on 2026-07-23** as the named
  harness / infra / devops alternate: HydrationCapsuleV1's score-from-memory and small capsule
  hydrate change the rollover-cost calculus. Codex remains a formal-CF **review** seat + coding lane;
  the shared lease prevents concurrent co-ownership.
- **Kimi K3** — frontier coder/reviewer + cross-family escalation authority (`max-effort-only` makes a continuous loop costly).

### Machine-authority projection (lint #5642)

Exact tables below must match `scripts/config/model_catalog.yaml` → `orchestrator_seats` and
`scripts/config/fleet_communications.yaml` → `endpoints[*].formal_review_eligible`. Enforced by
`.venv/bin/python scripts/lint/lint_fleet_roster.py` (never rewrites prose).

<!-- fleet-roster-projection:begin orchestrator_seats -->
| seat | model_id | effort | escalate_model_id | escalate_effort |
| --- | --- | --- | --- | --- |
| agy | gemini-3.6-flash-high | high | gemini-3.1-pro-high | high |
| claude | claude-sonnet-5 | high | claude-fable-5 | xhigh |
| codex | gpt-5.6-terra | high | gpt-5.6-sol | xhigh |
| grok | grok-4.5 | high | grok-4.5 | high |
<!-- fleet-roster-projection:end orchestrator_seats -->

<!-- fleet-roster-projection:begin formal_review_eligible -->
| endpoint | formal_review_eligible |
| --- | --- |
| agy | false |
| claude | true |
| codex | true |
| cursor | false |
| gemini | false |
| glm-local | false |
| grok | false |
| kimi | false |
<!-- fleet-roster-projection:end formal_review_eligible -->

---

## Why these seats (the "least-bite" logic)

Every strong long-context model is load-bearing somewhere, so every orchestrator pick
"bites a hand." This routing bites the **least** — it keeps the scarce authority +
language + review lanes free and puts the loop on the most replaceable capacity:

- **Gemini** → infra: 1M window, MCP-leading tool use, cheap; never claims content lanes.
- **Grok** → product/track coordination: best-on-board agentic tool use, on its **own**
  subscription window, so driving it doesn't steal review or writing capacity.
- **Sonnet-5** → judgment-dense: near-Opus judgment at much lower cost, and it's *extra*
  Anthropic capacity that does **not** consume the Opus review-of-record seat.
- **HydrationCapsuleV1** gives Codex (272K) a measured, low-overhead score-and-hydrate path, so it
  can serve as the harness / infra / devops alternate without co-owning Gemini's stream lease.

---

## What each driver does on cold-start

1. Launcher pins `SESSION_EPIC`, claims the stream lease, and — for grok/gemini/kimi —
   mints the session canary; Claude/Sonnet use the SessionStart hook chain (no canary lane).
   The Codex DevOps alternate preflights its lane-scoped rollover namespace before the
   lease: zero packets starts fresh, one fresh unbound CLI packet exports exact IDs, and
   ambiguity, an already-resumed packet, or a native-app packet fails closed. After the
   lease and canary are ready, SessionStart binds the official new task ID and injects
   `CODEX-COLD-START.md`.
2. Driver runs **`drive-epic`** (invoke `$drive-epic`, or the launcher cold-prompt does it
   once wiring lands — see "Rollout" below).
3. Driver reads live routing from `/api/rules` + `model_catalog.yaml` (never hard-codes the
   roster), then runs the loop: topology → route → dispatch → Monitor settle → cross-family
   `review-pr` → arm auto-merge after gate + green CI → dual-write handoff.
4. Driver ends on its seat's handoff signal (canary **FAIL-HANDOFF** < 8/10 for
   grok/gemini/kimi; the thread-handoff for Claude/Sonnet), not on a compact count.

---

## Fleet-comms dependency (why the old start scripts felt "off the new plane")

The launchers already speak the **session-stream/lease** half of fleet-comms (#5512). The
**message-plane + cross-family-comms** half (`fleet_comms plane-status`, `review-pr`,
`publish-review-verdict`) is wired into the `drive-epic` skill but is **mid-cutover**:

- `dual_write` is an operator/advisor-gated flip **owned by the infra/harness lane**
  (parity receipt → approved enable). Check state:
  `.venv/bin/python -m scripts.fleet_comms plane-status` (currently `mode: off`).
- Plane modes are only `off → shadow → dual_write`; in **all** of them **file handoffs
  stay authoritative** and the skill dual-writes. `dual_write` is shadow/mirror, **not**
  cutover — there is **no implemented post-cutover authority state** yet.
- Retiring file handoffs is a future infra step gated on an implemented authority signal
  (not a `fleet_communications.yaml` edit a driver makes). Because the drivers work today
  on the file path, you do **not** need to wait for the rollout to start using them.

---

## When a driver comes back to you (operator)

A driver escalates instead of deciding solo when it hits: (1) an architecture/layout/process
change, (2) a contested cross-family verdict, (3) a fragile fix whose right layer is unclear,
(4) a high-risk route that would trip the `model_catalog.yaml` risk floor, or (5) a repo-wide
safety interruption of another lane. Advisors for those calls: **Fable, Sol**.

Everything else the driver runs to completion and reports past-tense — no "should I?" menus.

---

## Rollout (sequencing)

1. **This PR:** the `drive-epic` skill, this runbook, and the per-model driver launchers
   (`start-grok-drive.sh` / `start-gemini-drive.sh` / `start-sonnet-drive.sh` /
   `start-claude-drive.sh`). Cross-family reviewed; advisor-looped on the skill contract.
2. **Follow-up PR:** rewire the `start-grok.sh` / `start-gemini.sh` / `start-kimi.sh`
   cold-prompt `case` blocks to invoke `$drive-epic` (replacing the hand-written per-epic
   prose), so the playbook loads automatically. Held separate so the skill is reviewed
   before the launchers depend on it.
3. **Cold-start smoke** (a #5512 done-when item): launch each driver, confirm it orients +
   runs the loop without manual folklore.
