# Operator Expectations — the working contract

<critical>

The operator's standing expectations, consolidated 2026-07-05 (user-confirmed list + standing
orders). Every agent in the fleet boots with this contract. When any other instruction seems to
conflict, these are the tie-breakers.

## The contract

1. **Quality work.** No heuristics when a proper algorithm exists, no threshold-lowering, no
   "for now". One excellent module beats ten mediocre ones — this is education for real
   learners; bad pedagogy creates durable learner errors.
2. **Best practices.** Research the established best practice BEFORE implementing or deciding —
   `docs/best-practices/`, prior art, authoritative sources, current standards. Never ship the
   first thing that works. Fix root causes, not symptoms.
3. **Git & GitHub hygiene.** Worktrees for all branch work (main checkout stays on `main`,
   clean). PRs for everything — no direct commits to main. After merge: delete branch local +
   remote, remove worktree. Close issues when acceptance criteria are met, with tool-backed
   evidence. `X-Agent` trailer on every commit. Session start/end: sweep worktrees, branches,
   open PRs — a dangling ref reads as unfinished work to the rest of the fleet.
4. **Utilize the whole fleet — together you are stronger.** Substantive design/decisions get
   ≥1 other agent (discuss or independent cross-verify) BEFORE committing; solo only for
   trivial work. Route the bulk of reviews to non-Claude lanes; never self-review. Keep lanes
   busy — an idle paid lane wastes the operator's money (#M-14: max out paid limits; cost is
   never a reason to hold back, and passivity is the failure mode, not spend).
5. **Know each model's strengths and weaknesses; route by fit.** The canonical per-task routing
   table is `model-assignment.md` (served at `/api/rules`). Model names are examples, not
   constants — confirm current capability before relying on a specific string. Distinguish the
   MODEL from the HARNESS it rides in (see "Harness vs model" in `model-assignment.md`):
   hermes and opencode each host many models and add their own capabilities.
6. **Limits happen — handle them.** Providers rate-limit and quota out; that is normal
   operations, not an outage. On limit: check `/api/orient` runtime headroom, fall back per
   `scripts/config/agent_fallback_substitutions.yaml`, reroute to an equivalent lane, and note
   the substitution in the artifact. Never silently drop work because a lane was full; never
   burn a window past its cap either — use it fully, don't trip it.
7. **No claims without proof (#M-4/#M-4a).** Every verifiable claim is tool-backed: test
   results, audit gates, word validity, SHAs, counts, "done". Quote the command + cwd + raw
   output. "Done" means the USER-visible artifact was verified end-to-end, not "my diff
   applied". Never rationalize a defect as by-design.
8. **Clean code and clean documentation.** Dead code removed, functions tested, docs current.
   Stale docs are context-pollution that misroutes every agent that reads them — expired
   dates, retired lanes, and superseded defaults get pruned when touched (this file's own
   companion sweep: keep rules short, current, non-contradictory).
9. **Maximum Ukrainian immersion — with the A1 exception.** Learners learn Ukrainian IN
   Ukrainian. **A1 is the deliberate exception**: absolute beginners need English scaffolding,
   so A1 obeys its immersion CAP in `scripts/config.py` — do not push A1 to full immersion.
   From A2 the gradient is 85–100% graduated full-immersion (easy UA teaching voice, EN as
   vocab glosses only), B1+ effectively full. NEVER propose raising English / lowering
   immersion at A2+; equally, never strip A1's designed English support.
10. **Drive, don't defer.** When the next action is determinable — from the queue, an order, or
    your own recommendation — EXECUTE and report past-tense. Options-menus and "should I?"
    are disobedience, not caution. Stop only for: the operator's accounts/credentials, a
    deploy only they trigger, system-config changes without a present-tense go, or a direct
    conflict you cannot resolve.

## Precedence

Non-negotiable gates (blocking CI, VESUM, audit gates, secrets hygiene) outrank speed. The
contract above outranks convenience. When two contract items tension each other (e.g. fleet
utilization vs quality), quality wins and the tension gets surfaced in one sentence, not a menu.

</critical>
