# Operator Expectations — the working contract

<critical>

The operator's standing expectations, consolidated 2026-07-05 (user-confirmed list + standing
orders; fleet-reviewed by codex · agy · cursor · pool · deepseek, 1 round). Served first in
`/api/rules` and listed in the offline fallback, so every agent that follows the cold-start
sequence loads this contract. When any other instruction seems to conflict, these are the
tie-breakers.

## The contract

1. **Quality work.** No heuristics when a proper algorithm exists, no threshold-lowering, no
   "for now". One excellent module beats ten mediocre ones — this is education for real
   learners; bad pedagogy creates durable learner errors.
2. **Best practices.** Research the established best practice BEFORE implementing or deciding —
   `docs/best-practices/`, prior art, authoritative sources, current standards. Never ship the
   first thing that works. Fix root causes, not symptoms.
3. **Git & GitHub hygiene (layout A — Fable 2026-07-21).** One sentence: **root is the human's
   and the services'; agents live under `.worktrees/`.** Primary
   `~/projects/learn-ukrainian` is a **normal non-bare** checkout, pinned to `main`, where
   `git status` works; agents implement only in `.worktrees/dispatch/<agent>/<task>/`.
   `core.bare=true` on primary is a **bug** to heal (`git config core.bare false` +
   `extensions.worktreeConfig=true`), never an intentional mode. PRs for everything — no
   direct commits to main. After merge: delete branch local + remote, remove worktree. Close
   issues when acceptance criteria are met, with tool-backed evidence. `X-Agent` trailer on
   every commit. Session start/end: sweep worktrees, branches, open PRs — a dangling ref
   reads as unfinished work to the rest of the fleet.
4. **Utilize the whole fleet — together you are stronger.** Substantive design/decisions get
   ≥1 other agent BEFORE committing; solo only for trivial work. Two distinct duties, don't
   conflate them: (a) *discussion/panel input* improves the work but does NOT satisfy the
   independent-review gate; (b) the **review gate requires an independent reviewer from
   OUTSIDE your own model family** — never self-review, never same-family swarms. Keep lanes
   busy — an idle paid lane wastes the operator's money (operator policy: max out paid
   limits; cost is never a reason to hold back — passivity is the failure mode, not spend).
5. **Know each model's strengths and weaknesses; route by fit.** The canonical per-task routing
   table is `model-assignment.md` (served at `/api/rules`). Model names are examples, not
   constants — confirm current capability before relying on a specific string. Distinguish the
   MODEL from the HARNESS it rides in (see "Harness vs model" in `model-assignment.md`):
   hermes and opencode each host many models and add their own capabilities.
6. **Limits happen — handle them.** Providers rate-limit and quota out; that is normal
   operations, not an outage. On limit: check `/api/orient` runtime headroom; for
   Claude/Codex budget buckets at `near_cap`, substitute per
   `scripts/config/agent_fallback_substitutions.yaml`; for other lanes, reach the SAME model
   through a different harness or an equivalent lane per the harness-vs-model table. Always
   NOTE the substitution in the artifact — silent rerouting hides review-independence, cost,
   and data-egress changes. Never silently drop work because a lane was full; never burn a
   window past its cap either — use it fully, don't trip it.
7. **No claims without proof (#M-4/#M-4a).** Every verifiable claim is tool-backed: test
   results, audit gates, SHAs, counts, "done". Quote the command + cwd + raw output.
   **Ukrainian language facts doubly so**: word validity, stress, morphology, and derived
   forms are verified against VESUM / the `sources` MCP — never guessed from morphological
   intuition (pre-training is Russian-contaminated). "Done" means the USER-visible artifact
   was verified end-to-end, not "my diff applied". Never rationalize a defect as by-design.
8. **Clean code and clean documentation.** Dead code removed, functions tested, docs current.
   Stale docs are context-pollution that misroutes every agent that reads them — expired
   dates, retired lanes, and superseded defaults get pruned when touched.
9. **Maximum Ukrainian immersion — with the A1 exception.** Learners learn Ukrainian IN
   Ukrainian. **A1 is the deliberate exception**: absolute beginners need English
   scaffolding, so A1 has intentionally LOW immersion bands — authoritative values live in
   `IMMERSION_POLICIES` / `compute_immersion_band()` in `scripts/config.py` (banded, e.g.
   ULP S1 ~40–55%, later A1 bands lower/higher per design) — scaffolding is a design
   feature there, not a defect to fix. From A2 immersion is graduated UP:
   `a2-bridge` 75–100% → `a2-ramp`+ 85–100% (easy-UA teaching voice; English shrinks to
   vocab glosses and bounded metalanguage clarifications per the band's policy) → B1+
   effectively full. NEVER propose raising English / lowering immersion at A2+; equally,
   never strip A1's designed English support. The per-band `forbid` rules in
   `IMMERSION_POLICIES` are binding.
10. **Drive, don't defer — within approved scope.** When the next action is determinable from
    the queue, an order, or an already-approved design — EXECUTE and report past-tense.
    Options-menus and "should I?" on *implementation* of decided work are disobedience.
    **Stop and get approval** for: the operator's accounts/credentials; deploys only they
    trigger; system-config changes without a present-tense go; **and any architecture,
    process, or working-model decision** (see item 12).
11. **Repo mechanics are part of the contract.** The hard gates codified in `AGENTS.md` and
    `/api/rules` bind as if written here — notably: dispatch worktree subtree layout
    (`.worktrees/dispatch/<agent>/<task>/`); `.venv/bin/python` only (never bare
    `python`/`sys.executable`); no generated `status/`, `audit/`, `review/`, or telemetry
    artifacts in code PRs; no `.python-version`/linter-config drive-bys; builds only in
    worktrees; `Monitor` for event streams (never polling loops); never print secrets.
    This contract references them instead of duplicating them; violating them violates the
    contract.
12. **Advisor / operator approval gate (binding).** Agents must **not** invent or unilaterally
    adopt architecture, local layout, process, or policy without **present-tense approval**
    from the **operator** or a designated **advisor**. Current advisors: **Fable** and **Sol**
    (roster may change — do not hard-code forever; confirm via `/api/rules` /
    `model-assignment.md` when unsure). Discussion/panels improve quality but do **not**
    replace advisor approval for design. Routine implementation of already-queued work does
    not need a new advisor turn. Violations: shipping helpers/layouts/process "for now",
    redefining primary-checkout semantics, or flipping gates without an advisor record.

## Precedence

Non-negotiable gates (blocking CI, VESUM, audit gates, secrets hygiene) outrank speed. The
contract above outranks convenience. When two contract items tension each other (e.g. fleet
utilization vs quality), quality wins and the tension gets surfaced in one sentence, not a menu.

</critical>
