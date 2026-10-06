# Agent-friendly rearchitecture — counted gaps against the approved delivery design

Status: landing on operator direction (2026-10-06); supersedes PR #9803; the review of record belongs on the landing pull request; census figures remain frozen at `3e4bdb3dd9`. This document does not implement anything. It extends the approved design in [docs/plans/agent-friendly-delivery.md](agent-friendly-delivery.md) and the baseline in [docs/design/agent-friendly-delivery-baseline.md](../design/agent-friendly-delivery-baseline.md).

Frozen git head for every count below: `3e4bdb3dd9ecc57d1b519050bf64fa7a0ed9b737`. Machine-readable snapshot: [agent-friendly-rearchitecture-evidence.json](agent-friendly-rearchitecture-evidence.json). Refresh the git half with:

```bash
.venv/bin/python scripts/evidence/agent_pitfall_census.py --pretty
```

The census pins full UTC calendar days with explicit UTC-midnight bounds and git running with `TZ=UTC`; monthly trailer figures use each commit's own committer offset, so the counts reproduce on any host and at any time of day. The first snapshot of this plan used date-only bounds, which git resolves with the current time of day in the host timezone, so its figures could not be reproduced; this snapshot replaces them.

## Relationship

* **Adds.** A full count of fix commits, path buckets, reverts, and X-Agent trailers for 2026-07-01 through 2026-10-05, plus a complete failed-workflow census for that quarter and a complete failed-job census for the CI workflow in the approved plan's own window (2026-09-30 through 2026-10-05). Three gaps the approved plan's sample of 200 recent non-merge commits (249 in the window at its head `c21043daa5`; 281 counted at the frozen head) did not rank: review-machinery repairs inside that same window, the quarter-long practice/atlas/lexicon repair mass, and hook-guard repairs that continued after a shared parser landed. A sequencing rule so those gaps do not collide with #9721, #9718, or the Atlas word-card work.
* **Supersedes.** Two sentences in the approved plan's evidence section, and nothing in its architecture choice. See [What the counts force](#what-the-counts-force). The owner-interface recommendation, the rejection of a central advance-task facade, the seven stages, Phase 1's issue assignment, the baseline specification, the CI Gate, cross-family review, and the merge queue all stand.
* **Leaves to #9737's driver.** Every implementation packet already under that epic, including the open pull requests at census time and their branches. This plan does not edit those branches, does not open a second removal or review path, and does not take the infra-harness lease.

#9721 stays the six-component separation (open-model data and evaluation, Atlas data, Atlas frontend, practice frontend, curriculum generation, curriculum display). Its first deliverable is still the source-backed dependency map and migration plan. This document does not publish a competing boundary. #9718 stays the frontend build-reuse packet. Atlas word cards stay #8977, on the ULIF tables landed in #9268, under the #8400 source rules.

## 1. Date range, sources, and method

| Source | What was counted | Range |
| --- | --- | --- |
| Non-merge git commits | 3,739 commits, of which 1,489 start with `fix` | 2026-07-01 inclusive through 2026-10-05 (git `--until=2026-10-06T00:00:00+00:00`) |
| Same, approved-plan window | 281 commits, of which 151 start with `fix` | 2026-09-30 through 2026-10-05 |
| X-Agent trailer by calendar month | All 9,204 non-merge commits on this head | 2025-11 through 2026-10 |
| GitHub Actions runs with `conclusion=failure` | 4,132 runs, by workflow name and event | 2026-07-01 inclusive to 2026-10-06 exclusive; weekly slices summed; snapshot `measured_on` 2026-10-05 |
| Failed jobs on failed `CI` workflow runs | 147 runs, every failed job | 2026-09-30 through 2026-10-05 |
| Pull-request text search for `VERDICT:` | Search `total_count` | `updated:2026-07-01..2026-10-06` |
| Issue comments | 13,924 comments scanned for the verdict marker | `since=2026-07-01` |
| This checkout | Definitions and production calls of the worktree removers | head above |

The July start is measured, not chosen for convenience. Missing `X-Agent` trailers are 725/967 in May, 424/1,445 in June, 138/1,485 in July, 73/978 in August, 54/1,070 in September, and 6/211 in October. July is the first month the trailer is the normal case. Counts before that mix the period before the trailer rule. The primary window still has 271/3,739 commits without the trailer.

Method follows pstack `/correct` and `/architect` as a way of reading history: group repeated repairs, prefer a structural owner over a new checklist, and screen a second shape (a central facade) against the design red flags. `/architect`'s multi-model arena was not run. The operator forbade a blank-slate redesign and forbade vendoring an arena, and [model-assignment.md](../../agents_extensions/shared/rules/model-assignment.md) plus [cursor-driver.md](../runbooks/cursor-driver.md) already forbid committing one. The approved design is the candidate. The facade is the alternative already rejected in that design; the counts below support that rejection. `/recall` used the assignment's state capsule (the approved plan, #9737, #9721) as the shared record. Monitor's rules API was unreachable in this session; the rules were read from `agents_extensions/shared/rules/`, including operator item 12 (no new architecture without approval) and the CLI help standard.

**Counted** means a git token, a path prefix, a workflow name, a job name, or a search total. **Inferred** means a cause read off those counts. Inferences are marked.

The approved plan sampled 200 recent non-merge commits (249 in the window at its head `c21043daa5`; 281 counted at the frozen head) and inspected eight diffs. This census counts that window as full UTC calendar days and finds 281 commits. That sample is a mechanism study. It is not a ranking of the window, and it is not a ranking of the quarter. This document supplies those rankings. It does not replace the eight-diff mechanism study.

A failed Actions run is not, by itself, an agent mistake. The CI Gate is supposed to go red when the head is not eligible. Advisory workflows are labeled advisory in their names.

## 2. Pitfall classes

### Ranked by `fix(<scope>)` subject token

These scopes are disjoint: a subject has one scope token. 1,489 fix commits in the primary window.

| Rank | Scope | Count | Bucket |
| --- | --- | --- | --- |
| 1 | practice | 96 | learner content |
| 2 | atlas | 69 | learner content |
| 3 | ci | 65 | harness |
| 4 | review | 64 | delivery machinery |
| 5 | delegate | 53 | delivery machinery |
| 6 | tests | 48 | harness |
| 6 | lexicon | 48 | learner content |
| 8 | bridge | 44 | delivery machinery |
| 8 | bio | 44 | learner content |
| 10 | hooks | 38 | delivery machinery |
| 11 | runtime | 37 | delivery machinery |
| 12 | api | 35 | delivery machinery |
| 13 | build | 33 | harness |
| 14 | audit | 24 | harness |
| 15 | site | 23 | learner content |
| 15 | orchestration | 23 | delivery machinery |
| 15 | routing | 23 | delivery machinery |
| 15 | folk | 23 | learner content |
| 19 | security | 21 | harness |
| 19 | dispatch | 21 | delivery machinery |

The bucket column labels rows in this table. It is not a partition of all 1,489 commits: the census found 179 scopes. Learner-content rows in the table (practice, atlas, lexicon, bio, site, folk) sum to 303. Delivery-machinery rows (review, delegate, bridge, hooks, runtime, api, orchestration, routing, dispatch) sum to 338. Harness rows (ci, tests, build, audit, security) sum to 191. The next scopes, outside the table, are fleet, harness, and monitor at 20 each, cycle007 at 19, and opsec and acp at 17 each.

Same token, approved-plan window only (151 fix commits inside the 281):

| Scope | Count |
| --- | --- |
| review | 18 |
| dispatch | 10 |
| fresh | 9 |
| runtime, tests | 8 each |
| opsec, build, delegate | 7 each |
| routing | 6 |
| agent-runtime, evidence, deps | 5 each |
| sources | 4 |
| ulif | 3 |
| lifecycle, site, launchers, agy, acp, session-streams, reaper, ci, fresh-build, hooks, stress, fleet, agents, standard | 2 each |
| workflow, path-safety, orchestration, eval, security, atlas, jsonl, rollover, session-start, agent_runtime, docs, hygiene, mcp, infra, rag, wiki, cursor, mdx, pre-commit, backup, fresh-writer | 1 each |

`fix(fresh)` in that window is the curriculum-validator class the approved plan already described (learner-only page text, arc, English channel, activity coverage). Example: [#9574](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/9574). `fix(routing)` is 6; the two commits that plan cites, [84c9f897da](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/84c9f897da9bc272c6ac9e1a2ab6bc2f553d097b) and [8e4496f135](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/8e4496f135ead2a1d23f608177917dea1e3d6ff2), both 2026-10-03, are among them.

### Path buckets on the 1,489 fix commits

A commit is counted once per bucket it touches. Test paths are classified first; the site buckets count the remaining `site/` paths.

| Bucket | Fix commits |
| --- | --- |
| tests or site tests | 1,309 |
| delivery trees (`scripts/delegate.py`, `scripts/review/`, `scripts/orchestration/`, `scripts/fleet/`, `scripts/agent_runtime/`, `scripts/runtime/`, hook paths) | 424 |
| other site paths | 242 |
| `scripts/lexicon/` or `data/lexicon/` | 120 |
| site paths whose names mention practice | 107 |
| `curriculum/` | 88 |
| site paths whose names mention atlas or word-card | 46 |
| `.github/workflows/ci.yml` | 46 |
| other workflow files | 30 |

In the approved-plan window the delivery bucket is 78 of 151 fix commits. Lexicon is 7. Site-atlas is 2. `ci.yml` is 1.

### Subject-regex hits (not a second ranking)

The census script also counts fix subjects against fixed regexes. A subject can match several. Use these as supporting hits, not as the rank order. Primary window: source-evidence words 65, review-machinery words 48, timeout or cache words 36, removal or reap words 29, hook-guard words 26, opsec-path words 20, test-isolation words 18, CI-selection words 17, routing-credit words 6. The routing-credit regex is narrower than the `routing` scope (23). The scope token is the ranking.

### Reverts

Two commits in the primary window start with `revert`: [#8384](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/96fac6e1c7456f2739f53daa59d0be54a8f6a193) and [#8356](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/f4c979f709edeacac7adf88679f9cdc4ec160f50), both A1 curriculum rollbacks on 2026-09-21 and 2026-09-20. One further subject mentions a revert: the autopsy of a connector commit that silently reverted merged hunks, [#7190](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/0afded20103043ae36bc56b4ccd288da8ec0cfa5). Reverts are rare next to the 1,489 fix commits. **Inferred:** agents repair in place far more often than the project reverts a merge.

### CI failures, separate from the fix commits

4,132 failed workflow runs from 2026-07-01 through 2026-10-05. By event: `pull_request` 2,131, `merge_group` 1,074, `push` 407, `schedule` 163, others under 130. By workflow, the top of a complete tally: CI 2,737, Hygiene (advisory) 765, Issue task quality (advisory) 123, Auto-arm merge queue 100, Integration sweep 89. The weekly series peaks at 836 in 2026-09-23..2026-09-29 and is 389 in 2026-09-30..2026-10-06.

Failed jobs on the 147 failed CI-workflow runs in 2026-09-30..2026-10-06, complete for that window:

| Failed job or run diagnostic | Count |
| --- | --- |
| CI Gate | 146 |
| pytest shards, summed across shard names | 290 |
| Dependency audit | 21 |
| Checks | 10 |
| Frontend | 3 |
| Secret scan | 2 |
| Fast checks | 1 |
| pytest report | 1 |
| Failed run with no job conclusion of failure | 1 |

One run can fail several jobs, so the job counts exceed 147. The last row counts a failed run with no failed job, separately from the 474 failed jobs. Examples: [CI Gate run 37388894492](https://github.com/learn-ukrainian/learn-ukrainian.github.io/actions/runs/37388894492), [pytest shard run 37358321354](https://github.com/learn-ukrainian/learn-ukrainian.github.io/actions/runs/37358321354), [Frontend run 37271335317](https://github.com/learn-ukrainian/learn-ukrainian.github.io/actions/runs/37271335317). #9718 records a Frontend job of 772 seconds on run 37220316307. That is a duration fact owned by #9718. It is a different measurement from these failure counts. This census does not re-time that job and does not claim a speed winner. The baseline document already forbids treating a missing span as zero and forbids a fleet speed claim outside Phase 3.

### Cross-family verdict text

GitHub search `total_count` for pull requests updated in the primary window whose searchable text contains the string: `VERDICT: CHANGES_REQUESTED` 101, `VERDICT: APPROVED` 603, `VERDICT: BLOCKED` 37, `cf-verdict v1` 85. These are pull requests, not review rounds, and the string can sit in a landing summary.

A scan of 13,924 issue comments since 2026-07-01 found 111 comments matching the strict marker order in `scripts/review/record_cf_verdict.py`: 110 `APPROVED`, 1 `CHANGES_REQUESTED`. Another 679 comments contained a `VERDICT:` line that marker did not parse. Those 679 were not split by verdict word. **Inferred:** the strict marker under-counts changes rounds relative to the 101 search hits. Neither figure is a round count. Both are large enough to show that review text is a normal part of the quarter, which matches `fix(review)` at 64.

### What the counts force

The approved plan says two repeated classes have independent diff evidence (routing/credit consumers, and curriculum requirements that stay expectations until production), and that launcher forwarding, dispatch-bus validation, and structured review-receipt acceptance are single sampled events.

The full count of that same window forces two corrections to that evidence section:

1. The fleet ranking for 2026-09-30..2026-10-05 is not "two classes." Of 151 fix commits, `review` leads at 18, followed by `dispatch` at 10 and `fresh` (the curriculum-validator class) at 9; runtime and tests are tied at 8 each, opsec, build, and delegate at 7 each, and routing is at 6.
2. Review-machinery repair is recurrent in that window (18 fix commits), so the "single sampled event" label does not survive a complete subject count. The approved response is already review-feasibility ownership (#9739). The label changes. The response stays.

Across the quarter, practice (96), atlas (69), and lexicon (48) outrank routing (23). That is a gap the six-day sample could not see. It does not force a different architecture. See move 4.

The architecture choice stands. Delivery repairs are spread across the delivery-machinery rows in the table (338 commits) and across 424 fix commits that touch the delivery trees. A central facade would put one interface in front of that spread without giving any of those trees a single owner. That is the shallow-module and temporal-decomposition shape the approved plan already rejected. These counts agree.

**Inferred mechanisms**, tied to the subjects the census listed:

* Delivery repairs keep restating a fact another module owns: which family may review, whether a credit covers a lane, whether a guard sees a redirect, whether a worktree may disappear. Agents copy the nearest caller.
* Harness repairs keep adjusting path filters, shard bounds, and tests that touch live checkout state, then a later commit puts the merge queue back as the full gate. Example of that restoration: [a68b38c50f](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/a68b38c50f) (#9090).
* Content repairs keep landing after the page exists: cloze items without a unique answer, classify keys without VESUM evidence for the displayed sense ([#9135](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/9135)), A1 modules published and then reverted. **Inferred:** the lesson-page validators the approved plan names do not see practice cards or Atlas lexicon rows.

### Removal ownership on this head

The structure scan found one `git_worktree_remove` definition, in `scripts/orchestration/worktree_claims.py`, with two production callers: that module and `scripts/orchestration/reap_worktrees.py`. It found two `remove_unclaimed_worktree` definitions. The one in `scripts/orchestration/task_family/git_safety.py` delegates to the worktree-claims owner. That is the shape the approved plan asked for, and #9645 has since merged through [#9755](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/9755). This plan does not draw a third remover.

## 3. Architecture moves, in order

Each move says what it removes, then the collision line. The collision table in the next section is the checklist.

### Move 1 — Finish the approved owner repairs

Removes the repeated reconstruction of routing, review-admission, and removal facts (routing scope 23 on the quarter; review scope 18 in the sample window and 64 on the quarter; the removal scan above).

At census time, the work was the open #9737 packets, on their existing branches. This plan adds the ranking that says review-feasibility is the largest fix scope inside the approved plan's own window, which is why that packet stays first among delivery repairs. It does not add a facade, a new bus, or a second Work API.

Collision: Atlas data no, Atlas frontend no, #9721 boundaries no, #9718 CI path no. Sequence: alongside the driver's open pull requests at census time. Those pull requests yield to nothing in this document; this document yields to them.

### Move 2 — Keep one hook parser, and stop growing sibling parsers

Removes the hook-guard series. Scope count: `hooks` 38. Subject regex: 26. After [4287a9920f](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/4287a9920f) ("one shared quote-aware pre-processing pipeline") the series continues: [b66bd9c405](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/b66bd9c405) and [b7fafd482c](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/b7fafd482c) teach the guard about redirects. **Inferred:** callers still interpret shell themselves, so the shared pipeline is not yet the only interpreter an agent can reach.

The structural move is the one the October commits already point at: one quote-aware parser, internals not importable, a check that fails when a second parser appears. Documentation of the bypass does not close it. `/correct` stops at a new rule only when architecture, types, and a failing check cannot express the constraint. A second parser is expressible as a failing check. The infra-harness driver can schedule that check inside #9737. This plan does not write it.

Collision: Atlas data no, Atlas frontend no, #9721 boundaries no, #9718 CI path no. Sequence: alongside #9737, after move 1's packets open at census time if they touch the same hook files. No yield against Atlas or #9718.

### Move 3 — Leave `ci.yml` alone until #9721's graph and #9718's reuse exist

Removes the temptation to add another hand-maintained path filter. Evidence: 46 fix commits touch `ci.yml`; 65 commits use scope `ci`; the sample-window job census shows the CI Gate red on 146 of 147 failed CI runs and the Frontend job red on 3. Cheap-exit followed by restoring the full merge-queue gate is already in history ([a68b38c50f](https://github.com/learn-ukrainian/learn-ukrainian.github.io/commit/a68b38c50f)). The approved plan already says to qualify affected-check coverage before changing selection, and to keep integration and security checks.

The structural move, when it happens, is to derive selection from #9721's dependency graph. Until that graph is the source of truth, a new filter list is another hand-synced list. #9718 already owns `.github/workflows/ci.yml` for frontend build reuse, and it has an open test-race (A4) in `atlas-runtime-shards.test.ts` on branch `cursor/ci-frontend-speed-9718` (pushed, no pull request). Editing that file here would collide with both.

Collision: Atlas data no, Atlas frontend only if the Frontend job changes (do not change it), #9721 boundaries yes as a future consumer of their graph, #9718 CI path yes if `ci.yml` changes. Sequence: after #9718 lands and after #9721's map exists. Both of those land first.

### Move 4 — Leave learner-content evidence inside the components that already own it

Removes the quarter's largest content repair mass from the "we need a new platform" reading. Practice 96, atlas 69, lexicon 48, bio 44. Paths: lexicon 120, site practice 107, site atlas 46, curriculum 88. The approved plan's lesson-page validators show up as `fix(fresh)` 9 inside its own window. They do not account for the quarter's practice and atlas scopes. That is the gap.

#8977 already states the structural fix: one cited card per word, and Atlas, practice, and the open dataset generated from those cards, on the ULIF tables from merged [#9268](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/9268), under #8400's one-crawler one-store rules. A second card schema, a second lexicon store, or a seventh component would recreate the split the 120 lexicon fix commits are already paying for. **Inferred from the issue text plus the path counts:** the repair mass is a consumer-copy problem #8977 names, not a missing delivery facade.

This plan does not design that card, does not retune ULIF, and does not move practice validators into Atlas data. Practice-frontend checks belong on #9721's practice-frontend boundary and read cards when #8977 produces them. Curriculum-generation checks stay on that component. Atlas data stays #8400 and #8977.

Collision: Atlas data yes if anyone edits `sources.db` or ULIF tables (forbidden here), Atlas frontend yes if anyone edits word-card rendering (forbidden here), #9721 boundaries yes only as alignment with the six components, #9718 CI path no. Sequence: after the in-flight word-card and ULIF work for anything that reads cards. Those streams land first.

### Move 5 — Keep public-path refusal on the existing publisher

Removes repeated absolute-path scrubs. `opsec` is 17 fix commits on the quarter and 7 in the sample window, including scrubs of generated curriculum and audit text ([#8045](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/8045), [#8087](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/8087)). **Inferred:** generators can still emit a host path, and a later sweep deletes it. The higher level is a writer that cannot emit one, which the existing publication scanner is already becoming. This plan does not add a second scanner and does not point that scanner at ULIF rows or word-card schema.

Collision: Atlas data only if a scrub rewrites lexicon or `sources.db` (do not), Atlas frontend no, #9721 boundaries only where open-model-data artifacts are already that component's outputs, #9718 CI path no. Sequence: alongside, and stop if the file is in an Atlas or #9721 branch.

## 4. Collisions and sequencing

**State at landing (2026-10-06).** #9784 merged (`aed3a320fd`) as the #9721 plan. The #9737 PRs listed under "Branches this work did not touch" (#9781, #9779, #9800, #9798, #9802) have merged. Move 2 is in progress as #9807 slice 2a.

Fixed inputs, not redesigned here:

* #9721 — six components; moved into #9737 on 2026-10-06, with the infra driver as owner (recorded on #9737). First deliverable is the dependency and ownership map plus the migration plan. Pull request [#9784](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/9784), open at census time on `codex/publish-9721-approved-plan`, merged as `aed3a320fd`. This plan does not edit that branch.
* #9718 — frontend build reuse. Owns `.github/workflows/ci.yml`, the site build-artifact tests, `tests/test_frontend_ci_build_reuse.py`, and `docs/runbooks/ci-gate.md`. Branch `cursor/ci-frontend-speed-9718` is pushed and has no pull request. Open A4 race in `atlas-runtime-shards.test.ts`. Packet coordination is codex-atlas; landing stays with the infrastructure owner.
* #8400 / #8977 — ULIF source rules and one cited word card, on the tables from merged #9268. Owner codex-atlas, stream #4387. #8977's non-goal is re-harvesting ULIF. #8400's rule is one crawler and one store.

| Move | Atlas data | Atlas frontend | #9721 boundaries | #9718 CI path | When | Order |
| --- | --- | --- | --- | --- | --- | --- |
| 1. Finish approved owner repairs | no | no | no | no | alongside the #9737 pull requests open at census time | those pull requests land first; this plan waits |
| 2. One hook parser | no | no | no | no | alongside #9737, after move 1 if hook files overlap | no Atlas or CI ordering |
| 3. Selection from #9721's graph | no | no, leave the Frontend job | yes, as a consumer of their map | yes, so do not edit `ci.yml` now | after #9718 and after the #9721 map | #9718 and #9721 land first |
| 4. Content evidence via existing cards | yes if schema or ULIF changes, so do not | yes if card rendering changes, so do not | align with the six; do not add a seventh | no | after #8400 / #8977 for card readers | Atlas word-card work lands first |
| 5. Public-path refusal on the current publisher | no lexicon or `sources.db` edits | no | open-model-data outputs only, inside that component | no | alongside, stop on an overlapping branch | the branch that already has the file lands first |

Prefer #9721's six names over any new component list. Move 4 would force Atlas rework if it added a card schema or a second lexicon store. The path evidence for refusing that rework is the 120 lexicon fix commits and the 46 site-atlas fix commits already spent on the current store, plus #8977's statement that independent copies are the defect. Move 3 would force #9718 rework if it edited `ci.yml` or `atlas-runtime-shards.test.ts` while A4 is open. The job evidence for refusing a frontend-CI redesign is 3 Frontend failures against 146 CI Gate failures in the approved plan's window.

## 5. What was prototyped

| Probe | Command or read | Result | What it changed |
| --- | --- | --- | --- |
| Git census | `.venv/bin/python scripts/evidence/agent_pitfall_census.py` at `3e4bdb3dd9` | 3,739 non-merge / 1,489 fix; scopes and path buckets in section 2 | Replaced the 200-commit ranking with a full count. Forced the two evidence-section corrections. Did not force a new architecture. |
| Removal scan | same script, `structure_on_head` | One raw remover; production callers are the owner and the reaper; `git_safety.remove_unclaimed_worktree` is a second name that delegates | Move 1 does not invent a remover. #9755 already landed the chokepoint the approved plan described. |
| CI job census | Actions API, every failed job on 147 failed CI runs, 2026-09-30..2026-10-06 | CI Gate 146, pytest shards 290, Frontend 3 | Move 3 does not retune the Frontend job. Duration stays with #9718. |
| Path buckets | same git census | Lexicon 120, site practice 107, site atlas 46, `ci.yml` 46 | Move 4 yields to #8977 / #8400. Move 3 yields to #9718 and #9721. |

No throwaway branch was pushed. The census script and the JSON snapshot are the evidence that stays on this branch.

## 6. Decisions only the operator can make

Stream ownership is the one question an experiment cannot assign.

Should the quarter's practice and atlas repair mass become a #9737 child at all? The recommendation here is no. #8977 and #9721 already own the structural fix (one card, six components). A #9737 child that cannot edit ULIF, the card schema, or `ci.yml` would still be a second driver on the same outcome. Leave the content residual with codex-atlas and the infra separation driver. #9737's driver keeps delivery ownership, the hook parser if they accept move 2, and the later consumption of #9721's graph in move 3.

No other operator decision came out of the counts. The facade stays rejected. The gates stay. This file does not edit the approved plan, so that plan's own version-2 notes (wording of status and of the accountable driver) remain its notes.

## Branches this work did not touch

Open #9737 pull requests at the time of the census: [#9781](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/9781) `claude/impl-9739`, [#9779](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/9779) `codex/impl-9742`, [#9800](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/9800) `grok/impl-9741-c`, [#9798](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/9798) `codex/impl-9785`, [#9802](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/9802) `codex/impl-9797`. Also left alone: #9721's [#9784](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/9784) `codex/publish-9721-approved-plan`, and #9718's `cursor/ci-frontend-speed-9718`.
