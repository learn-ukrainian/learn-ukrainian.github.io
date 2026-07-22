# Epic-orchestrator roster — which model drives which lane, and how

**Audience:** operator (you) + any agent launched as an epic/track driver.
**Companion skill:** [`drive-epic`](../../agents_extensions/shared/skills/drive-epic/SKILL.md)
— the model-agnostic playbook every driver runs.
**Per-model launch detail:** [`gemini-orchestrator.md`](gemini-orchestrator.md),
[`grok-session-canary.md`](grok-session-canary.md), [`epic-stream-handoff.md`](epic-stream-handoff.md).

There is no standing orchestrator "loop" process. **An orchestrator = a driver session
you launch with `start-<model>.sh --epic <name>`.** The launcher claims the stream lease,
mints a canary, and (for hook-less CLIs) injects a cold-start prompt; the driver then runs
the `drive-epic` skill to orchestrate its lane.

---

## The roster (why these seats)

Every strong long-context model is load-bearing somewhere else, so every orchestrator
pick "bites a hand." This roster bites the **least**: it keeps the scarce authority +
language + review lanes free, and puts the loop on the most replaceable capacity.

| Lane / epic | Driver model | Launch | Why this seat |
| --- | --- | --- | --- |
| **Harness / infra** | Gemini 3.6 Flash (AGY) | `./start-gemini.sh --epic harness` | 1M window, MCP-leading tool use, token-efficient, cheap. Ideal infra driver. **Never claims content lanes.** Already the #5512 orchestrator seat. |
| **Curriculum / track** (atlas, hramatka, folk, bio, …) | Grok 4.5 | `./start-grok.sh --epic <track>` | Best-on-board agentic tool use, cheap, on its **own** subscription window → steals the least. Coordination-dense driving. |
| **Judgment-dense sessions** (incidents, architecture cutovers, contested reviews) | Sonnet-5 | `./start-sonnet-driver.sh --epic <epic> [--agent <type>]` | 1M window, near-Opus judgment at much lower cost. **Extra Anthropic capacity — does not consume the Opus review seat.** |
| **Reserved — NOT orchestrator loops** | Opus 4.8 · Codex (GPT-5.6) · Kimi K3 | — | Opus = hardest judgment + CF review of record. Codex (272K window) + Kimi K2.7 (256K) → coding/review pool. K3 = frontier coder/reviewer + cross-family escalation authority. |

**Do not** make Opus or Codex a daily orchestrator: Opus is the single most expensive hand
to bite (you'd lose your best cross-family reviewer to run a polling loop); Codex's 272K
window and doubled coder+reviewer role make it the worst capacity trade.

**Context-window floor for an orchestrator is ~500K+** (must thread long sessions + query
fleet state). That is why Codex (272K) and Kimi **K2.7** (256K) are ruled out as drivers
and Grok (500K), Sonnet-5/Opus/Gemini/K3 (1M) qualify.

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
  `\.venv/bin/python -m scripts.fleet_comms plane-status`.
- Until it flips, **file handoffs stay authoritative** and the skill dual-writes.
- After the infra lane flips it, the plane becomes authoritative — a **one-line config
  change** in `fleet_communications.yaml`, not a skill rewrite.

So drivers are strengthened onto the comms layer we are **keeping**, and the flip does not
race the skill.

---

## When a driver comes back to you (operator)

A driver escalates instead of deciding solo when it hits: (1) an architecture/layout/process
change, (2) a contested cross-family verdict, (3) a fragile fix whose right layer is unclear,
(4) a high-risk route that would trip the `model_catalog.yaml` risk floor, or (5) a repo-wide
safety interruption of another lane. Advisors for those calls: **Fable, Sol**.

Everything else the driver runs to completion and reports past-tense — no "should I?" menus.

---

## Rollout (sequencing)

1. **This PR:** the `drive-epic` skill + this runbook + `start-sonnet-driver.sh` wrapper.
   Cross-family reviewed; advisor-looped on the skill contract before merge.
2. **Follow-up PR:** rewire the `start-grok.sh` / `start-gemini.sh` / `start-kimi.sh`
   cold-prompt `case` blocks to invoke `$drive-epic` (replacing the hand-written per-epic
   prose), so the playbook loads automatically. Held as a separate PR so the skill is
   reviewed before the launchers depend on it.
3. **Cold-start smoke** (a #5512 done-when item): launch each driver, confirm it orients +
   runs the loop without manual folklore.
