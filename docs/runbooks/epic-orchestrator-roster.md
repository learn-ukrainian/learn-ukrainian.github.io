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
| **harness / infra** | Gemini (AGY) | `./start-gemini-drive.sh harness` |
| **corpus** (acquisition & ingestion) | Gemini (AGY) | `./start-gemini-drive.sh corpus` |
| **atlas** (Word Atlas + Practice Hub product) | Grok 4.5 | `./start-grok-drive.sh atlas` |
| **hramatka** (teacher lesson service) | Grok 4.5 · Sonnet-5 if judgment-heavy | `./start-grok-drive.sh hramatka` |
| **folk** (curriculum track) | Grok 4.5 † | `./start-grok-drive.sh folk` |
| **bio** (curriculum track) | Claude | `./start-claude-drive.sh bio` |
| **any epic** — incident · architecture cutover · contested review | Sonnet-5 (Opus for the hardest) | `./start-sonnet-drive.sh <epic>` |

**Per-model launcher convention:** `./start-<model>-drive.sh <epic>` where `<model>` ∈
`grok · gemini · sonnet · claude`. Epic is the first arg; extra flags forward
(e.g. `--agent curriculum-track-orchestrator`). Every one runs the `drive-epic` skill.

† **folk carve-out:** the *driver* may be Grok, but folk content **review** stays
cross-family **GPT ↔ Claude** (no DeepSeek, and Grok is never a judge seat) — the
`drive-epic` skill enforces this.

**Reserved — do NOT use as a driver seat:**
- **Opus 4.8** — hardest judgment + the cross-family review of record. Don't burn it on a polling loop.
- **Codex (GPT-5.6)** 272K window + **Kimi K2.7** 256K — under the ~500K orchestrator floor → coding/review pool.
- **Kimi K3** — frontier coder/reviewer + cross-family escalation authority (`max-effort-only` makes a continuous loop costly).

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
- **Context-window floor ~500K+** (thread long sessions + query fleet state) is why Codex
  (272K) and Kimi K2.7 (256K) can't drive; Grok (500K) and the 1M-window models can.

---

## What each driver does on cold-start

1. Launcher pins `SESSION_EPIC`, claims the stream lease, mints the session canary.
2. Driver runs **`drive-epic`** (invoke `$drive-epic`, or the launcher cold-prompt does it
   once wiring lands — see "Rollout" below).
3. Driver reads live routing from `/api/rules` + `model_catalog.yaml` (never hard-codes the
   roster), then runs the loop: topology → route → dispatch → Monitor settle → cross-family
   `review-pr` → arm auto-merge after gate + green CI → dual-write handoff.
4. Driver ends on canary **FAIL-HANDOFF** (< 8/10), not on a compact count.

---

## Fleet-comms dependency (why the old start scripts felt "off the new plane")

The launchers already speak the **session-stream/lease** half of fleet-comms (#5512). The
**message-plane + cross-family-comms** half (`fleet_comms plane-status`, `review-pr`,
`publish-review-verdict`) is wired into the `drive-epic` skill but is **mid-cutover**:

- `dual_write` is an operator/advisor-gated flip **owned by the infra/harness lane**
  (parity receipt → approved enable). Check state:
  `.venv/bin/python -m scripts.fleet_comms plane-status` (currently `mode: off`).
- Until it flips, **file handoffs stay authoritative** and the skill dual-writes.
- After the infra lane flips it, the plane becomes authoritative — a **one-line config
  change** in `fleet_communications.yaml`, not a skill rewrite. So you do **not** need to
  wait for the rollout to start using these drivers.

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
