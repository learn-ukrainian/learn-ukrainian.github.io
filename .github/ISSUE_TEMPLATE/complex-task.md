---
name: Complex Task
about: Track planning, implementation, testing, and QA for multi-step work
title: ''
labels: task, working:unassigned
assignees: ''
---

## User-visible outcome
<!-- One sentence: what the user/fleet can see when this is done -->

## Why / evidence
<!-- Link, repro, metric, or failing command -->

## In scope
<!-- Concrete paths, surfaces, modules -->

## Non-goals
<!-- What this ticket will not do -->

## Denominator
<!-- What “all” means (files, modules, sample size, env) -->

## Verify
```bash
# Exact commands or held-out check
```

## Terminal goal
<!-- merge | deploy | certify | decision-only | audit-only -->

## Dependencies
<!-- Blockers named, or `none` -->

## Accountable driver
<!-- Lane/seat that owns merge + DoD closeout -->

## Stop policy
<!-- Failure condition · owner · disposition · unblock/transfer — not "none expected" alone -->

## Residual policy
<!-- Leftover owner / transfer, or explicit none -->

## Review plan
<!-- Anticipated author family · eligible outside-family reviewer · backup · independence revalidated after author+SHA known -->
<!-- Advisor discussion / prompt review does NOT satisfy exact-head CF -->

## Dispatch preflight (DoR B — before each worker wave and before CF)
- [ ] Monitor/API healthy for this task
- [ ] Named task infra works (sources/VESUM/CI/… as needed)
- [ ] Disk headroom proven (`df` + `.worktrees` via `git rev-parse --git-common-dir`)
- [ ] Capacity check run (`usage show` + `capacity_pick`)
- [ ] ≥2 non-orchestrator agents with headroom **when** terminal goal is merge/deploy/certify (roles named)
- [ ] Target epic/stream not lease-wedged; WIP OK
- [ ] Env/secrets present only if required (never print)
- [ ] Preflight evidence dated (command · timestamp · receipt · pass criterion; unknown ≠ green)

Canonical DoR: `docs/best-practices/task-quality.md` (card ∧ preflight).
Operator everyday “ready” = DoD delivered, not this checklist.

## Acceptance Criteria / Definition of Done
- [ ] AC-01: …
- [ ] AC-02: …
<!-- Stable IDs required; map each to Verify evidence + denominator -->
- [ ] Outcome verified on exact merged SHA / shipped artifact
- [ ] Verify commands green (or N/A with reason)
- [ ] Docs/templates updated if touched
- [ ] If code/docs change: PR + independent cross-family exact-head APPROVE (with quality-posture receipt) + CI green on that head + landed per merge policy
- [ ] Merge closeout when PR: remote branch gone, local branch gone, dispatch worktree reaped
- [ ] Close comment: verified outcome · denominator · merged SHA · residual · owner

Canonical pack: `docs/best-practices/task-quality.md`

## Phases

### Phase 1: Planning
- [ ] Research/explore codebase
- [ ] Document approach in comment
- [ ] Operator/advisor GO only if this is a *new* architecture/layout/process decision

### Phase 2: Implementation
- [ ] Implement in a **dispatch worktree** (never primary `main`)
- [ ] Commit with `X-Agent` trailer and `#issue` references
- [ ] Update progress in comments

### Phase 3: Testing
- [ ] Run audit/validation named in Verify
- [ ] Test edge cases
- [ ] Document results in comment

### Phase 4: QA/Review
- [ ] Independent cross-family exact-head review (not self-review)
- [ ] Update documentation if needed

## Blocked (only if blocked-with-receipt)
<!-- code · unblock condition · owner · next poll — else omit -->

## Residual
<!-- leftovers + owner, or “none” -->

## Notes
<!-- Progress updates, decisions -->
