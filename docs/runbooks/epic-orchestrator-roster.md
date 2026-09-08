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
| **harness / infra** | Gemini (AGY) | `./start-gemini-driver.sh --epic infra` |
| **harness / infra** (named alternate) | Codex / gpt-6-astra @ high | `./start-codex-driver.sh --epic infra` |
| **devops** | Gemini (AGY) | `./start-gemini-driver.sh --epic devops` |
| **devops** (named alternate) | Codex / gpt-6-astra @ high | `./start-codex-driver.sh --epic devops` |
| **monitor** | Gemini (AGY) | `./start-gemini-driver.sh --epic monitor` |
| **monitor** (named alternate) | Codex / gpt-6-astra @ high | `./start-codex-driver.sh --epic monitor` |
| **corpus** (acquisition & ingestion) | Gemini (AGY) | `./start-gemini-driver.sh --epic corpus` |
| **atlas** (Word Atlas + Practice Hub product) | Grok 4.6 | `./start-grok-driver.sh --epic atlas` |
| **hramatka** (teacher lesson service) | Grok 4.6 · Fable if judgment-heavy | `./start-grok-driver.sh --epic hramatka` |
| **folk** (curriculum track) | Grok 4.6 † | `./start-grok-driver.sh --epic folk` |
| **bio** (curriculum track) | Grok 4.6 | `./start-grok-driver.sh --epic bio` |
| **any epic** — incident · architecture cutover · contested review | Opus 5 @ xhigh (default Anthropic) | `./start-claude-driver.sh --epic <epic>` |
| **any epic** — Fable alternate | Fable 5 | `./start-claude-driver.sh --epic <epic> --model claude-fable-5` |
| **any epic** — routine Anthropic alternate | Sonnet-5 | `./start-claude-driver.sh --epic <epic> --model claude-sonnet-5` |
| **any epic** — Cursor TUI driver (Auto; attested after run) | Cursor Auto | `./start-cursor-driver.sh --epic <epic>` |

**Driver launcher convention:** `./start-<provider>-driver.sh --epic <epic>` where `<provider>` ∈
`codex · grok · gemini · claude · cursor`. The core owns all launcher flags; provider
CLI flags follow `--`. Each driver validates the lane, claims the lease, runs
the provider canary, and injects the `drive-epic` binding before the provider
process starts. Codex additionally performs its transport-health probe during
adapter preflight, before it claims the lease; a degraded probe refuses the
launch without acquiring a lane.

### Remote lease and handoff authority

Driver leases are claimed on the API host through `/api/epics/v1`; remote mode is
the default. `--local` is an explicit operator-offline fallback and prints a
warning; it is not a fleet-visible lease. Drivers must not use `--local` as
recovery when the remote endpoint is unavailable. A handoff is an API mutation at
`POST /api/epics/v1/epic:<N>/handoff`, not a second local ownership record.

A driver on any machine resumes a lane by launching with `--epic <epic>`; the
successor launcher claims the corresponding remote stream. Live drivers do not
claim again. Before driving, the driver reads the remote
lease and digest surfaced at SessionStart; at the end of a batch it appends the
typed handoff through the API. The successor folds that digest into its own
handoff. Remote recovery uses Monitor TTL/CAS or an attributed operator release;
local PID death is not remote liveness proof.

Every host must export `LU_MONITOR_HOST_ID=<opaque id>` before a driver claims a
lease. Use the opaque IDs from the canonical `MONITOR_OCCUPANCY_HOST_IDS`
mapping (for example, `host-teacher` or `mac-operator`), so the
holder is not reported as `local`. Do not substitute a hostname, alias, or IP
address for the opaque ID.

**Cursor concurrency (documented serialization, #6956):** A Cursor driver session
**is** the Cursor lane (`fleet_communications.yaml` `concurrency_limit: 1`). Do not
also `delegate.py dispatch --agent cursor` from that session. What the runtime
already enforces today:

- **Stream lease (drivers only):** `SessionStreamStore.open_session` refuses a second
  live driver on the same epic stream with
  `stream {id} already has live session …` (`agents_extensions/shared/session_streams/store.py`).
- **Worker dispatch:** `scripts/delegate.py` `_check_capacity_hint` keeps the
  ordinary busy-lane note, but reads the session-stream store before a Cursor
  dispatch. A live Cursor process-driver lease refuses `dispatch --agent cursor`
  before spawn; `--force-agent` overrides that refusal with an explicit NOTE.
- **Fleet endpoint metadata:** `concurrency_limit: 1` on the `cursor` endpoint is
  declarative / API-surfaced and is not used as a general worker cap. The
  session-stream lease is the dispatch admission signal for the Cursor driver.

This lease↔dispatch coupling is fail-closed by default. Full charter:
`docs/runbooks/cursor-driver.md`.

**Opus 5 @ xhigh is the DEFAULT Anthropic driver seat** (operator decision 2026-08-03).
`./start-claude-driver.sh --epic <epic>` pins Opus 5 with `--effort xhigh` by default;
pass `--model claude-fable-5` or `--model claude-sonnet-5` for supported alternates
(and `--effort …` after `--epic` to override effort). Keep the SUMMONED cadence —
1-2 short scheduled sessions/day, dispatch-heavy, never a resident polling loop
(see model-assignment.md § Orchestration operating pattern). Both Anthropic wrappers
resolve to the same `claude-<lane>` handoff slot, so the stream lease still allows only one
Anthropic driver per lane. The legacy `scripts/start-bio-driver.sh` runs Claude + the
`curriculum-track-orchestrator` agent-def if you specifically want that agent.

† **folk carve-out:** the *driver* may be Grok, but folk content **review** stays
cross-family **GPT ↔ Claude** (no DeepSeek, and Grok is never a judge seat) — the
`drive-epic` skill enforces this.

**Recommended against as a driver seat (least-bite — the live `model_catalog.orchestrator_seats` policy is authoritative):**
- **Fable 5** (Anthropic top tier) — default Anthropic driver plus hardest judgment and
  top Anthropic advisor (with Sol). **Opus 5 is neither an advisor
  nor an orchestrator seat** (operator 2026-07-26) — it remains a complex-coding/deep-review
  dispatch seat only.
- **Kimi K2.7** 256K — under the ~500K window we want for a driver. **Codex (GPT-5.6)** was
  dropped on 2026-07-22 for its 272K window, then **re-added on 2026-07-23** as the named
  harness / infra / devops alternate: HydrationCapsuleV1's score-from-memory and small capsule
  hydrate change the rollover-cost calculus. Codex remains a formal-CF **review** seat + coding lane;
  each stream's lease prevents concurrent co-ownership.
- **Kimi K3** — frontier coder/reviewer + cross-family escalation authority (`max-effort-only` makes a continuous loop costly).

### Machine-authority projection (lint #5642)

Exact tables below must match `scripts/config/model_catalog.yaml` → `orchestrator_seats` and
`scripts/config/fleet_communications.yaml` → `endpoints[*].formal_review_eligible`. Enforced by
`.venv/bin/python scripts/lint/lint_fleet_roster.py` (never rewrites prose).

<!-- fleet-roster-projection:begin orchestrator_seats -->
| seat | model_id | effort | escalate_model_id | escalate_effort |
| --- | --- | --- | --- | --- |
| agy | gemini-3.8-flash-high | high | gemini-3.1-pro-high | high |
| claude | claude-fable-5-1 | high | gpt-6-astra | high |
| codex | gpt-6-astra | high | gpt-6-astra | high |
| cursor | auto | high | gpt-6-astra | high |
| grok | grok-4.6 | high | grok-4.6 | high |
<!-- fleet-roster-projection:end orchestrator_seats -->

<!-- fleet-roster-projection:begin formal_review_eligible -->
| endpoint | formal_review_eligible |
| --- | --- |
| agy | false |
| claude | true |
| codex | true |
| cursor | false |
| gemini | false |
| glm-local | true |
| grok | true |
| kimi | false |
<!-- fleet-roster-projection:end formal_review_eligible -->

These tables project catalog fields, not proof of current reviewer health or
qualification. Resolve review through the canonical `local-code-review` workflow:
a qualified native toolful outside-author-family reviewer inspects the exact head
SHA and posts findings/verdict on the PR; required CI must pass before merge.
Retired sealed ACP/MCP canaries do not establish current review eligibility.

**Model-by-harness intent:** operator-authorized Astra/Grok orchestration from Hermes
separates model family, model ID, harness, and functional role. Resolve supported
models and launcher routes from live catalog data and launcher help. This does not
change model pins, dispatch/review quality gates, or existing stream ownership:
one driver per stream still binds. The retired individual DeepSeek ACP transport
is not a blanket ban on the Hermes harness. Required catalog changes need advisor
review; this routing intent does not authorize speculative pins.

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
- **HydrationCapsuleV1** supplies the score-and-hydrate path for the authorized Codex alternate.
  Use the selected runtime's validated context profile; a historical model's window is not
  a current capability or permission grant. The alternate never co-owns Gemini's stream lease.
  Infra (`epic:6943`) and DevOps (`epic:5703`) are independent streams: one live driver does
  not block the other, while a second driver on either same stream still fails closed.

---

## What each driver does on cold-start

1. Launcher pins `SESSION_EPIC`, claims the stream lease, and — for grok/gemini/kimi —
   mints the session canary; Claude/Sonnet use the SessionStart hook chain (no canary lane).
   The Codex DevOps alternate preflights its dedicated `codex-devops` rollover namespace
   before acquiring `epic:5703`, independently of Infra's `codex-infra` / `epic:6943`
   ownership. It then selects at most one applicable rollover: zero packets starts fresh,
   one fresh unbound CLI packet exports exact IDs, and
   ambiguity, an already-resumed packet, or a native-app packet fails closed. After the
   lease and canary are ready, SessionStart binds the official new task ID and injects
   `CODEX-COLD-START.md`.
2. Driver runs **`drive-epic`** (invoke `$drive-epic`, or the launcher cold-prompt does it
   once wiring lands — see "Rollout" below).
3. Driver reads live routing from `/api/rules` + `model_catalog.yaml` (never hard-codes the
   roster), then runs the loop: topology → route → dispatch → Monitor settle → cross-family
   exact-head CF → CI Gate green on that head → merge queue (`drive-epic` §6/§7; never
   `gh pr merge --auto` first) → dual-write handoff.
4. Driver ends on its seat's handoff signal (canary **FAIL-HANDOFF** < 8/10 for
   grok/gemini/kimi; the thread-handoff for Claude/Sonnet), not on a compact count.

---

## Fleet-comms authority and review

The launchers claim **session-stream/lease** authority (#5512); `drive-epic`
teaches the message-plane and cross-family review loop.

- Production default is **`authority`** (#6159). Query live data with
  `.venv/bin/python -m scripts.fleet_comms plane-status`; the default is not a
  substitute for that observation.
- Implemented modes are `off` | `shadow` | `dual_write` | `authority`.
  Fleet-comms is the durable message-plane source of truth in `authority`;
  legacy stores are read-only migration/projection inputs. Session handoff
  files still carry continuity, not competing message or lease authority.
  `dual_write` is a compatibility soak/rollback mode, not normal operation.
- Sealed formal CF (`review-pr`, `publish-review-verdict`, `lu-review-*` trees)
  is **retired — do not use**. Use a qualified native toolful cross-family
  reviewer and post its verdict and findings on the PR at the exact head SHA,
  following the [local-code-review workflow](../../agents_extensions/shared/skills/local-code-review/SKILL.md).
- Plane, retention, and review-eligibility changes remain infra/harness actions
  requiring present-tense operator/advisor approval; drivers do not flip them.

---

## When a driver comes back to you (operator)

A driver escalates instead of deciding solo when it hits: (1) an architecture/layout/process
change, (2) a contested cross-family verdict, (3) a fragile fix whose right layer is unclear,
(4) a high-risk route that would trip the `model_catalog.yaml` risk floor, or (5) a repo-wide
safety interruption of another lane. Advisors for those calls: **Fable, Astra @ high**.

Everything else the driver runs to completion and reports past-tense — no "should I?" menus.

---

## Rollout (sequencing)

1. **This PR:** the `drive-epic` skill, this runbook, and the provider driver launchers
   (`start-grok-driver.sh` / `start-gemini-driver.sh` / `start-claude-driver.sh` /
   `start-codex-driver.sh` / `start-cursor-driver.sh`). Cross-family reviewed;
   advisor-looped on the skill contract.
2. **Follow-up PR:** rewire the `start-grok.sh` / `start-gemini.sh` / `start-kimi.sh`
   cold-prompt `case` blocks to invoke `$drive-epic` (replacing the hand-written per-epic
   prose), so the playbook loads automatically. Held separate so the skill is reviewed
   before the launchers depend on it.
3. **Cold-start smoke** (a #5512 done-when item): launch each driver, confirm it orients +
   runs the loop without manual folklore.
