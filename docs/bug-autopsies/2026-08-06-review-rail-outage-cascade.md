# Autopsy: review-rail cascade + GitHub outage merge freeze (2026-08-06)

## Symptom
- Zero PRs merged for a full working day despite ~10 review rounds executed; operator escalated
  to near-cancellation.
- The formal sealed review rail failed 7× against 1 legitimate catch: a stale authority lease
  locked the queue-unblocking PR out of re-review (~2h); a running review was killed by a
  tmp-dir wipe leaving a PR with zero verdicts while believed in-flight; its retry was refused
  (substitution authorization envelope drift); a COMPLETED review was discarded for a missing
  routing authority receipt; a docs PR could not be routed at all (no_policy_approved_route);
  one request crashed raw (authority_key_semantic_conflict); one docs report consumed FOUR full
  review rounds (round 3 was a 6-byte arithmetic nit).
- GitHub Actions entered major outage (~17:08Z–~00:30Z). Agents kept firing reviews and reruns
  into the dead platform; nothing in the system knew the platform was down.
- The one required CI status context froze every merge, including two-file docs PRs, because
  branch protection enforced admins and no outage mode existed.
- One expired provider API key (401) silently disabled an entire seat (dispatch AND review);
  discovered only when a dispatch failed after 7 minutes of retries.
- Delegate finalizer reported false `no_deliverable` for pushed work 3× (#6426), burning a
  verification round-trip each time.

## Root cause
1. **Exact-head formality without delta awareness.** Any new SHA — even a 6-byte docs fix —
   invalidated the review and forced a complete fresh read. Cost scaled with ceremony, not risk.
2. **No platform-health input.** Reviews, reruns, and merge automation had no notion of
   "GitHub is down"; they burned provider tokens and rerun quota into a dead queue.
3. **Bookkeeping as a hard gate.** Reservations/leases/envelopes/receipts sat BETWEEN a
   completed review and its verdict; every bookkeeping defect destroyed real, paid work.
4. **Unmonitored single points of failure.** One required status context; one API key per seat;
   one $TMPDIR shared with an unaware wiper.
5. **Agents obey process over purpose under pressure.** The orchestrator ground against its own
   guards for ~1h of operator escalation before treating "process defeats purpose" as the
   emergency it was. No rule licensed early escalation.

## What held (keep these)
- Cross-family review substance: caught a real P1 in the rail fix itself.
- The sealed evidence validator: mechanically rejected 3 fabricated findings (2 hallucinated
  paths, 1 out-of-scope anchor) — the reason the grok judge ban could stay lifted.
- Local-test-evidence + explicit manual merge: 100/40/150/29-test local runs allowed safe
  merging through the outage without shipping untested code.
- Deterministic-over-hallucination: executing a branch's tests refuted a plausible-but-wrong
  review finding (40/40 pass vs predicted failure).

## Fixes shipped same-night
- #6423: direct one-round cross-family review by default; sealed path opt-in for high-risk
  code; docs PRs fold trivial findings at merge; `ask-* --review` unlocked.
- #6421: reservation supersede fix (the head-poisoning treadmill).
- #6426 filed: finalizer false no_deliverable on --cwd reuse worktrees.
- Operator allowlisted orchestration commands past the auto-mode classifier.

## Prevention

### Prevention candidates (fleet discussion 2026-08-07 — decide, then implement)
P1. **Delta re-reviews**: a re-review after fixes receives the prior verdict + the incremental
    diff (prev-head..new-head) only; full re-read only when the delta is architectural.
P2. **Platform-health gate**: one cached probe (githubstatus API) consulted by review/rerun/
    merge automation; on major_outage, queue instead of burn, arm a recovery watch.
P3. **Outage mode for merges**: documented evidence path (local test runs + CF verdict +
    admin merge + protection restore) instead of ad-hoc heroics.
P4. **Credential canaries**: per-seat cheap liveness probe (or dispatch-time fast-fail) with a
    loud operator ping on 401/expiry — a dead key must not be discovered by a 7-minute retry.
P5. **Verdicts outlive bookkeeping**: a completed review's verdict is always recoverable and
    publishable even if its reservation/lease/receipt state is corrupt.
P6. **"Process defeats purpose" escalation rule**: when guards block ALL progress on the
    operator's stated goal, agents stop grinding and escalate with a concrete override
    proposal after ONE failed cycle, not four.
P7. **Guard scoping audit**: guards accreted broader than their incident. The primary-checkout
    write guard (born from a worker patch landing in primary) now blocks the orchestrator
    writing its own docs/autopsies; the merge guard blocks operator-intended outage merges with
    no override; variable-expanded paths false-positive as primary writes. Each guard gets an
    explicit scope statement + an operator-visible override path, or it shrinks.

## Fleet discussion outcome (2026-08-07, codex + agy + glm, 2 rounds + synthesis)

Verdicts on the candidates (full transcript: fleet conversation
`conversation_bceaa18330d24c61acdea399d75f46e6`):
- **P5 is the strongest fix and a dependency of P1**: persist the completed exact-head verdict
  through the existing result/artifact path BEFORE any reservation/bookkeeping cleanup; later
  publication replays that result. Bookkeeping failure must never erase a completed verdict.
- **P1 endorsed, narrowed**: incremental re-review only when a durable prior verdict exists for
  the actual base/head with unchanged review scope; otherwise normal review. NO blanket
  docs-only fast-track (one over-reviewed report is not evidence all docs are harmless), and
  NO semantic-diff engine (ceremony creep).
- **P2 + P6 merge into one fail-stop**: a capability-aware check at the GitHub side-effect
  boundary; ONE failed rail/infrastructure recovery cycle → terminal `needs_operator`, suppress
  further automatic cycles for that PR/head (single-flight), emit one actionable notice.
  Substantive findings (real test/lint failures) are NOT escalation grounds — classify first.
- **P3**: a short human-run outage-merge runbook (distinguish platform outage from failing
  tests; exact-head local evidence + any valid independent verdict; named admin action;
  restoration + reconciliation afterward). A runbook, not a subsystem.
- **P4 reframed to transport-level**: 401/403/expiry immediately quarantines the seat from
  dispatch, stops retries, alerts once. No background heartbeat cron.
- **P7 as an audit**: per guard record scope, purpose/owner, failure class, next operator
  action, override-allowed?. "Operator-visible" ≠ every guard bypassable.
- **Failure taxonomy** (the shared contract): platform · credential · guard-control ·
  bookkeeping · substantive-finding · unknown. The first four and unknown → `needs_operator`
  fail-stop; only substantive findings continue the normal fix loop.

**Explicitly NOT built** (anti-ceremony guardrails): no review-history database, no new
ledgers/reconciliation daemons, no AST diff engine, no verdict registry, no docs-only skip
rule, no platform-health required CI check, no automated admin merges, no credential heartbeat
cron, no per-guard override UI, no new retry counters/dashboards/SLOs. The 7:1 failure ratio
justifies fail-stop design and this autopsy — not deletion of independent review itself.

## Links

- Issue #4811 (CI runner-queue starvation / related outage lessons)
- Related formal-review rail incidents referenced in body; outage day 2026-08-06
- Sample commit: `402120edac` (queue starvation recovery PR branch tip lineage)
