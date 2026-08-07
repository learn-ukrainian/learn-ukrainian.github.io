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
   - No self-authored partial-done bars; no "when you want" for in-scope residual;
     residual unfinished work is queue, not ceremony.
2. **Best practices.** Research the established best practice BEFORE implementing or deciding —
   `docs/best-practices/`, prior art, authoritative sources, current standards. Never ship the
   first thing that works. Fix root causes, not symptoms.
3. **Git & GitHub hygiene (layout A — Fable 2026-07-21).** One sentence: **root is the human's
   and the services'; agents live under `.worktrees/`.** Primary
   `~/projects/learn-ukrainian` is a **normal non-bare** checkout, pinned to `main`, where
   `git status` works; agents implement only in `.worktrees/dispatch/<agent>/<task>/`.
   **The primary checkout is strictly read-only.** Do not drop scratch files, test scripts,
   or command outputs into its root directory under any circumstances. If you need a
   temporary file for discovery or testing, put it in your assigned worktree or an ignored
   scratch directory (like `batch_state/`).
   `core.bare=true` on primary is a **bug** to heal (`git config core.bare false` +
   `extensions.worktreeConfig=true`), never an intentional mode. PRs for everything — no
   direct commits to main. **After merge, cleanup is mandatory before the next formal
   review or large dispatch** (operator 2026-08-07; ENOSPC is the known failure): (1)
   confirm MERGED, (2) `git worktree remove --force` for that PR's dispatch worktree
   **before** deleting the local branch, (3) delete local + remote branch +
   `git fetch --prune` + `git worktree prune`, (4) reap finished CF residue for that PR
   when no process holds it — `.worktrees/dispatch/acp/runtime-review-<PR>*`,
   `/tmp/lu-cf-clean/`, `/tmp/lu-review-*`, `/tmp/lu-pr*` (read-only sealed snaps need
   `chmod -R u+w` then `rm -rf`), task runtime tmp, stray worktree `.venv`, (5) prove
   with `df -h /` and `git worktree list` (no zombie path for that PR). A squash-merge
   alone is not done. Full checklist: `drive-epic` skill §7a. Close issues when
   acceptance criteria are met, with tool-backed evidence. `X-Agent` trailer on every
   commit. Session start/end: sweep worktrees, branches, open PRs — a dangling ref
   reads as unfinished work to the rest of the fleet.
4. **Utilize the whole fleet — together you are stronger.** Substantive design/decisions get
   ≥1 other agent BEFORE committing; solo only for trivial work. Two distinct duties, don't
   conflate them: (a) *discussion/panel input* improves the work but does NOT satisfy the
   independent-review gate; (b) the **review gate requires an independent reviewer from
   OUTSIDE your own model family** — never self-review, never same-family swarms. Keep lanes
   busy — an idle paid lane wastes the operator's money (operator policy: max out paid
   limits; cost is never a reason to hold back — passivity is the failure mode, not spend).
   **Driver routing is enforced** (operator GO 2026-08-06): every dispatch needs a
   `ROUTING_CARD_V1` (tier · model×harness · advisor packet · alternatives); default bounded
   work is **authority brief (Fable or Sol) → heap/practical implement**, not a mid-brain
   solo marathon. Session breadth floor + handoff report:
   `fleet-driver-routing.md` + `python -m scripts.fleet.driver_breadth_report`.
5. **Know each model's strengths and weaknesses; route by fit.** The canonical per-task routing
   table is `model-assignment.md` (served at `/api/rules`). Model names are examples, not
   constants — confirm current capability before relying on a specific string. Distinguish the
   MODEL from the HARNESS it rides in (see "Harness vs model" in `model-assignment.md`):
   hermes and opencode each host many models and add their own capabilities.
   **Tiers:** authority (Fable/Sol) · practical (Terra/Sonnet/Flash-high) · heap (Luna and
   weaker with a complete advisor packet). Fable remains the Anthropic authority seat even
   under a small Claude sub — reach via native Claude pin or **Cursor → Fable**.
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
   **Outcome validity precedes execution.** Before any paid provider/model run or consequential
   external action, research the exact model/artifact/runtime compatibility and define a
   falsifiable, user-visible success condition plus a stop condition. A canary must inspect the
   actual semantic output needed by the goal; hashes, schemas, throughput, cost, CI, and a
   provider `COMPLETED` state prove transport or structure only. A semantic tripwire is a
   terminal failure, never input to normalize away. Changing the artifact, tokenizer, prompt
   template, parser, or runtime invalidates prior canary proof. Completion reports must name the
   exact user-visible outcome that was verified, its real-world or source denominator, the
   independent held-out proof, and any residual gap. A seed, prototype, schema, transport check,
   or self-authored canary can establish engine/mechanism readiness only; it cannot close a
   product phase. For language claims, a source occurrence is not normative evidence until its
   pedagogical or evidential role is established.
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
    `model-assignment.md` when unsure). Fable is a summoned design advisor, not a standing
    reviewer or routing default. Discussion/panels improve quality but do **not**
    replace advisor approval for design. Routine implementation of already-queued work does
    not need a new advisor turn. Violations: shipping helpers/layouts/process "for now",
    redefining primary-checkout semantics, or flipping gates without an advisor record.
13. **Adversarial quality & constructive criticism (No happy-path nonsense).** Every in-flight
    architecture review and code audit MUST lead with potential failure modes, missing edge cases,
    race conditions, and un-tested codepaths. Never output superficial praise or "happy path"
    cheerleading. Default to rigorous constructive critique: identify structural fragility, demand
    empirical proof, and surface hidden risks. Terminal completion reports follow item 7: lead with
    the exact verified user-visible outcome, then the residual gap and risks.
14. **Pre-dispatch outcome adequacy.** Before presenting to the operator or dispatching a
    substantive phase or epic kickoff, freeze a prompt that names the user-visible outcome,
    real-world or source denominator,
    non-goals, role map, independent held-out evaluation, stop/residual policy, and completion
    vocabulary. A high-stakes domain prompt needs a domain-fit reviewer and a distinct adversarial
    scope/circularity critic; smaller consequential work needs at least one fast critic; a
    genuinely trivial bounded prompt is explicitly exempt. The prompt author counts as neither
    reviewer. Route those roles from the live
    `model-assignment.md` rules, never by permanent reviewer identity. Bind each review to the
    prompt SHA-256 and its explicit checklist verdict, findings, and author reconciliation;
    re-review after a material change to the outcome, scope, denominator, role map, acceptance
    criteria, or independent evaluation. A non-goal that shrinks the actual mission needs
    operator/advisor approval. Prompt review improves dispatch quality only: it never replaces
    exact-head implementation review or the independent cross-family PR gate.

## Precedence

Non-negotiable gates (blocking CI, VESUM, audit gates, secrets hygiene) outrank speed. The
contract above outranks convenience. When two contract items tension each other (e.g. fleet
utilization vs quality), quality wins and the tension gets surfaced in one sentence, not a menu.

</critical>
