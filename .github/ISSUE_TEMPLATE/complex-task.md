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

## Acceptance Criteria / Definition of Done
- [ ] Outcome verified against denominator (evidence on this issue)
- [ ] Verify commands green (or N/A with reason)
- [ ] Docs/templates updated if touched
- [ ] If code/docs change: PR + independent cross-family exact-head APPROVE + CI green on that head + landed per merge policy
- [ ] Merge closeout when PR: remote branch gone, local branch gone, dispatch worktree reaped
- [ ] Close comment: verified outcome · denominator · residual · owner

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
