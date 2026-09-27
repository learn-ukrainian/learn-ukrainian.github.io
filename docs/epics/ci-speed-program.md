# CI speed and reliability program

> Epic **#8875** (parent: infra stream epic #6943). This document (#8885) is the
> versioned plan; the measurement history lives in issue **#8750** (comments) and
> the area-lanes design in **#8872**. Written by the infra driver (Claude), 2026-09-27.
> Status: program in progress — Team plan and pre-commit guards already landed;
> most child tickets are `ready` (dispatched but not yet merged); two children are
> blocked; the merge-queue timeout change needs the operator's repo-admin action.

## 1. Purpose and user-visible outcome

Agents (and the operator) file dozens of PRs a day. CI feedback speed and
trustworthiness are load-bearing for that workflow, not a nicety: a slow or
flaky gate either gets ignored or costs a full ~15-minute re-run cycle per
mistake. The outcome this program commits to (epic #8875 AC-01/AC-02):

- A typical full-tier PR run's pytest phase gets **well under** the baseline
  ~10–12 minutes-per-shard wall time, measured p95 over 20 consecutive full
  runs, at least 40% below baseline.
- **Zero** green PRs dropped from the merge queue with reason
  `checks_timed_out` over 7 days after the timeout fix ships.
- Main stays green except for real regressions — red runs caused by
  main-wide episodes (time bombs, stale pinned assertions, timing races) are
  the ones this program targets, not test coverage.

Non-goals (epic #8875): the V7 curriculum build pipeline, separate
repositories, paid larger runners, weakening the merge queue or nightly full
runs.

## 2. Baseline measurements, with sources

All numbers below are quoted from tool-backed comments on **#8750**
(dated 2026-09-24 through 2026-09-27) unless a different source is named.
Anything not traceable to a run id, comment, or report path is marked
**unverified** rather than stated as fact, per the issue's stop policy.

### 2a. Run-level baseline (459-run window, 2026-09-22T20:24Z–2026-09-24T23:07Z)

Source: #8750 comment, "Step 1 baseline" (459 completed `ci.yml` runs, GitHub
job/step timings; 40 failed PR runs sampled via JUnit).

| Metric | p50 | p95 |
| --- | --- | --- |
| PR full-tier run wall (218 of 246 PR runs = 89% went full) | 16.4 min | 37.6 min |
| PR one-shard run wall (28 runs) | 7.8 min | 21.7 min |
| `merge_group` full wall (179 runs) | 15.7 min | 29.9 min |
| Time to first failed job, failing PR full runs (83) | 13.0 min | 29.2 min |
| pytest job queue (created→started) | 1.2 min | 12.7 min |
| pytest job execution / `Run pytest` step | 10.4 / 8.3 min | 13.3 / 11.1 min |

Same comment: runner cost ≈ 50 runner-minutes per full run; shard setup ≈ 2
min (checkout 0.7, containers 0.4); shards already balanced at 7.8–9.1 min
each; 114 of 116 failing PR jobs in the sample were pytest shards;
`repo_wide` (from #8707) = 468 tests, ~278 s serial; `tests/projects/open_model_data`
≈ 1,855 s serial, about a quarter of the suite.

### 2b. Runner-queue root cause (measured 2026-09-25)

Source: #8750 comment. All `ci.yml` jobs run on GitHub-hosted runners
(4,929 of 4,929 job records checked); **concurrent running `ci.yml` jobs
peaked at exactly 20** — the account's concurrent-job cap on the Free plan —
with long stretches at 15–20. A CI run uses 11 jobs (p50, max 12), so
roughly two runs execute at once and the rest queue. This is the direct
cause of the pytest queue p95 of 12.7 min, a preflight job's measured 5-min
wait (Phase A held-out probe, PR #8759), and a merge-queue timeout drop
(PR #8752, removed from the queue 30 min after being added while its
`merge_group` run 36076354122 was still `in_progress`).

Implication recorded on the issue: **job count per run was the main lever,
not test time**, at the time of that measurement.

### 2c. 120-PR sample, language/area split (measured 2026-09-26)

Source: #8750 comment, "CI measurement, 2026-09-26" (last 120 merged PRs,
merged 2026-09-23T21:49Z–2026-09-26T01:08Z, plus the JUnit of PR #8834's
full run, run 36205634726).

- pytest = 4,751 of 5,742 job-minutes (83%); Frontend = 169 min.
- 100 of 120 PRs ran the full four-shard pytest tier. Shard wall time: p50
  11.7 min, p95 14.2 min, max 17.2 min (420 shard jobs).
- 7 of 120 PRs changed no `.py` file yet still ran pytest (201 job-minutes);
  115 of 120 changed no site/JS/TS file yet 20 ran Frontend (150
  job-minutes) — both triggered by paths the tests/build genuinely read
  (skills, `.pre-commit-config.yaml`, curriculum assets, declared site
  inputs), so most of this is correct coverage, not waste (~6% of
  job-minutes at most).
- `scripts/ci/pytest-file-durations.json` was last refreshed 2026-09-23
  (#8531): 1,480 entries for ~1,571 test files, summing to 96.9 measured
  minutes against 119.2 actual — stale durations mis-balance shards.
- In PR #8834's full run, the four shards carried 34.4 / 23.6 / 40.4 / 20.7
  minutes of test time — the slowest shard sets the wall time.
- Of 32,905 tests (119.2 serial minutes): the 1,059 tests over 1s take 71.7
  min (60%); the slowest 200 take 41.3 min (35%).
  `tests/projects/open_model_data/` alone accounts for 26.9 min (22.6%).

### 2d. Red-run causes (150 failed runs since 2026-09-23)

Source: #8750 comment, "What actually holds work back in CI".

| Failure | Runs | Branches | Kind |
| --- | --- | --- | --- |
| `test_lint_test_assertions::test_repo_test_suite_is_clean` | 25 | 12 | main red ~2.5h on 09-24 (#8692) + genuine per-PR catches |
| `test_subprocess_timeout_guard` | 16 | 16 | genuine per-PR catches, each found only after a full ~15-min run |
| `test_acp_text_agent` (ACP timeout) | 20 | mostly merge queue | ~8h queue-kick episode on 09-23 |
| `test_decisions_record` | 14 | 5 | main red ~2h on 09-24 |
| `test_opsec_route_sweep` | 8 | 7 | time bomb: skip-expiry window, every branch red at once on 09-23 |
| `test_check_static_practice_assets` | — | — | import-time `sys.path` mutation; fixed by PR #8861 |

Conclusion recorded on the issue: red runs are mostly main-wide episodes and
late catches of cheap, file-local guards — not random flakes. This directly
motivated moving the two most frequent late-catch guards (the subprocess
timeout guard and the stale-epic lint) to pre-commit (see §4).

### 2e. Merge-queue starvation (2026-09-26T21:32Z)

Source: #8750 comment. PR #8852 was removed from the merge queue with
`reason=checks_timed_out`: its `merge_group` run 36271581935 was created
21:02:49Z, every job passed, but the final `CI Gate` job sat `queued` from
21:31:53Z waiting for a hosted runner, and the queue's
`check_response_timeout_minutes: 30` fired at 21:32:51Z — the run itself
then completed `success` seconds later. Ruleset `main-merge-queue` (id
20977023) at that time: `max_entries_to_build: 4`, `grouping_strategy:
ALLGREEN`, `check_response_timeout_minutes: 30`. Four concurrent
`merge_group` builds × ~10 jobs ≈ 40 runner requests against the (then) 20
concurrent-job cap — the queue was starving itself. PR #8858 was dropped
the same way shortly after (22:03Z, per the epic issue text). Two green PRs
lost to this cause is the AC-02 denominator this program tracks going
forward (zero drops over 7 days after the fix).

### 2f. Coupling map (test-file dependency graph)

Source: `batch_state/tasks/analysis-ci-coupling-map.result` (read-only
`git grep`/`find`/`git log` analysis, 2026-09-27; some sub-findings gathered
by parallel read-only research agents and summarized by the driver).

- Total test files: 1,572.
- Central-loader coupling (`scripts/agent_runtime/runner.py`,
  `scripts/delegate.py`) at module level reaches **90 of 1,572 files
  (~6%)** today. A much larger figure (~1,075 files, ~70% of the suite) was
  real for about 22.5 hours between commit `bf18b39e` (PR #8654/#8747,
  merged 2026-09-25T00:57) and its revert, commit `2f7f1894` (PR
  #8794/#8830, merged 2026-09-25T23:33) — a same-day regression, not the
  steady state on `main` today (2026-09-27).
- `tests/test_mcp_sources_v4_invocation_recording.py` borrows
  `open_model_data`'s test fixtures via `sys.path.insert` +
  `pytest_plugins` — the one hard, collection-blocking cross-area edge
  found.
- 17 test files are misrouted by name (11 infra/fleet-named files actually
  import `scripts.api.*`; 5 build-named + 1 curriculum-named files actually
  import `scripts.lexicon.*`).
- Of six candidate areas, only **atlas/lexicon/practice** (zero cross-area
  source or test edges) and **open_model_data** (a handful of edges, ~245
  of 1,572 files, ~16% of the suite together) are genuinely isolable by
  import graph. The other four areas (infra/fleet, site+API,
  curriculum-build, sources-MCP) are multi-directionally coupled — see §4.

### 2g. Slow-test root-cause analysis (30 slowest files)

Source: `batch_state/tasks/analysis-8750-slow-tests.result` (11 read-only
investigation passes over the worktree, 2026-09-27; every claim in the
underlying report cites file:line). Total addressable savings identified
across the 30 files: **roughly 730–865s (~12–14 min) of the ~2,569s these
files currently cost**, split into six ordered "briefs" (see §5, Briefs 1–6,
now filed as issues #8877–#8882). Briefs 1–4 (~475–590s) were assessed as
immediately actionable at low risk; Brief 5 higher-value but needing its
own review; Brief 6 blocked on #8809 (the `open_model_data` data-path
split).

## 3. What the industry does, and what fits this repo

Source: design-panel summary on #8872 (Codex + Grok, cross-family review,
both verdict ADOPT WITH CHANGES).

Common practice at scale: one pipeline with affected-set test selection
from a dependency graph (Bazel, Buck, Pants, Nx, Turborepo; Google's TAP);
predictive test selection as an optimization layer on top (Develocity,
Launchable); shards balanced by measured duration; build/dependency
caching; merge-queue batching; flaky-test quarantine; and cheap checks
before push (pre-commit / pre-push hooks). Per-folder CI (GitHub Actions
`paths:` filters, one workflow per directory) is the simple variant industry
also uses, with a known pitfall: a skipped workflow can leave a required
check pending, and cross-area breakage escapes if the filters are wrong.

**What fits this repo, per the panel and the coupling-map evidence:**

- Affected-set selection by import graph was tried (issue #8750, "Phase
  B0a") and found not to pay off here: ~1,075 of 1,571 test files reach the
  central registry loaders once those loaders' dynamic imports are treated
  correctly, so an honest selector saves at best ~30%, and only with new,
  hand-declared bounds per loader. The driver's recorded read: park the
  import-graph selector; the runner-capacity ceiling (§2b) was the
  dominant cost, not test selection.
- Per-folder CI (as a required-check-per-folder design) is rejected for the
  four multi-directionally-coupled areas — see §4/§6 — but the *lane*
  variant (selecting tests inside the existing shards, one required check)
  is adopted for the two areas the evidence shows are actually isolable.
- Cheap checks before push: adopted directly (pre-commit guards, §4,
  already landed as #8864).
- Shard balancing by measured duration: adopted (#8876), refreshed
  automatically rather than committed-and-stale.

## 4. Decisions, with evidence

| Decision | Evidence | Status |
| --- | --- | --- |
| **GitHub Team plan** (20 → 60 concurrent hosted jobs) | Runner-queue root cause, §2b; epic #8875: "Org moved to the Team plan (60 runners) on 2026-09-27." | **Done** (2026-09-27) |
| **More, better-balanced shards on the Team plan** | Shard imbalance data, §2c (34.4/23.6/40.4/20.7 min in one run; stale duration file); now safe to add shard count with 60 runners available | Tracked as **#8876**, open |
| **Pre-commit guards for the two most frequent late-catch failures** (`subprocess_timeout_guard`, stale-epic `lint_test_assertions`) | Red-run causes, §2d (16 and 25 of 150 failed runs respectively); repo tests kept as the CI backstop | **Landed**, PR #8864 (merged) |
| **Slow-test batches 1–6** (reclassify genuinely full-scope tests to nightly; remove incidental fsync/subprocess overhead; cache deterministic recomputation; stub non-under-test boundaries; shrink oversized fixtures; `open_model_data` fixture work) | Slow-test analysis, §2g | Tracked as **#8877–#8882**; #8882 blocked on #8809 P3 |
| **Merge-queue `check_response_timeout_minutes` 30 → 60** | Starvation incident, §2e (two green PRs dropped: #8852, #8858) | Proposed on #8750; needs a human with repo-admin rights (agent's own attempt was refused by the permission layer); tracked as **#8884**, waiting on the operator |
| **Area lanes for exactly two areas — atlas/lexicon/practice and open_model_data — after two prerequisite refactors, not four** | Coupling map, §2f/§6; design panel ADOPT WITH CHANGES | Tracked as **#8872**, being rewritten to DoR; refactors (fix the `pytest_plugins` borrowing, `git mv` the 17 misrouted files) are its own prerequisite scope |
| **Merge queue must run every lane for code changes before any PR-side lane selection ships** | Panel finding on #8872: `classify_changes.classify_tier` today applies the same path classes to `merge_group` as to `pull_request` (operator decision #8437, 2026-09-21) — lane selection on PRs is only safe if the queue is a full backstop | Operator decision needed; recorded as a dependency of #8872, not yet made |
| **DoR/DoD enforcement for every agent-filed issue** | Motivated by this program's own experience rewriting #8872/#8874 to meet the task-quality bar mid-flight | Tracked as **#8886**, open |
| **Root-cause the stale `.git/index.lock`** | Blocked the primary checkout's fast-forward for ~10h (issue title, #8874) | Tracked as **#8874**, being rewritten to DoR |

## 5. What was considered and rejected, and why

- **Per-folder CI (a required check per area) for the four coupled
  areas** (infra/fleet runtime, site+API, curriculum/content build,
  sources MCP) — rejected. The coupling map (§2f) shows site+API imports
  into 3 other areas in 26% of its own files; curriculum-build's dependency
  on infra/fleet (writer/reviewer dispatch) is architectural, not
  accidental; sources-MCP's real backing code (wiki/rag/verification, 104
  files, dwarfing the 1-file MCP server) has edges into all four other
  areas plus a 57-file out-of-tree shared package. A path-based gate over
  these four areas would either also have to watch the ~490-file de facto
  shared cluster — in which case most PRs still trigger most lanes, with
  little parallelism gained over today's generic sharding — or not watch
  it, in which case it would silently skip a lane whose code actually
  depends on what changed: a correctness regression, not just an
  efficiency loss. The existing shard-balancing approach gets wall-clock
  reduction with none of that correctness risk, because it doesn't claim
  semantic isolation.
- **Separate repositories per area** — rejected; explicit non-goal on
  epic #8875. Would trade a coupling problem this repo's tooling can
  measure and fix for a cross-repo coordination problem with worse
  visibility, for a project run mostly by AI agents that need one
  checkout to reason about.
- **Self-hosted runners** (to escape the 20/60 concurrent-job ceiling
  without a paid plan tier) — rejected for this repo. This is a public
  repository (confirmed: `gh repo view` reports `PUBLIC` visibility), and
  GitHub's own guidance is that self-hosted runners should not be used on
  public repositories: anyone who can open a pull request can get their
  workflow code to execute on the runner, which is a direct risk to any
  secrets or network access the runner has. GitHub-hosted runners on a
  paid plan (the Team-plan move, §4) get the same capacity increase without
  that exposure. (This option was not found explicitly discussed on #8750
  or #8872; the rejection reasoning above is the driver's, applying
  documented GitHub guidance to this repo's known-public status — flagged
  here as reasoning, not a measured number.)
- **Server-side summarizing instead of paging** for the Wikipedia-extract
  tool in the sources MCP (a #8875 child, #8883) — rejected. PR #8873
  (closing #8524) records the operator's 2026-09-27 decision: "research
  text must not be silently truncated." A summary is lossy by
  construction; paging (`offset`/`max_chars`, pages concatenating
  byte-for-byte to the full article) preserves the complete text and lets
  the consuming agent decide how much it needs. This item is grouped under
  the CI-program epic because it shares the epic's "agents get complete,
  trustworthy signal instead of a truncated one" theme, not because it
  changes CI runtime.

## 6. Area-lanes scope: why two areas, not six

The original operator question (2026-09-27, quoted on #8872) asked about
separate CI for infra, site backend, `open_model_data`, atlas, and
curriculum. The coupling map (§2f) answered with import-graph evidence, and
the design panel (Codex + Grok) reviewed the resulting plan twice
(ADOPT WITH CHANGES both times). The scope that survived:

- **In scope for #8872**: two prerequisite refactors (stop
  `tests/test_mcp_sources_v4_invocation_recording.py` borrowing
  `open_model_data` fixtures; `git mv` the 17 misrouted test files to their
  real area), then `scripts/ci/classify_changes.py` lane selection for
  **atlas/lexicon/practice and open_model_data only**, inside the existing
  shards (no new jobs — 5 lanes × 4 shards would be 20 jobs for one PR),
  plus `merge_group` running every lane for code changes.
- **Explicitly not in scope**: lanes for infra/fleet, site+API,
  curriculum-build, or sources MCP (they stay on the shared, balanced
  shards, #8876); separate workflows or required checks; the four
  "hygiene" refactors the coupling map also identifies (redefining shared
  core to include the ~490-file de facto cluster, bounding the adapter-glob
  dynamic import, declaring the curriculum-build → infra/fleet edge,
  de-duplicating the `sys.path` fallback imports) — those are real but
  separate hygiene tickets if pursued, not blockers for the two-area lane.
- **Proof required before the lane change ships**: replay of historically
  failed runs plus fault-injected changes for the two areas, zero escapes.
  Green merged PRs are explicitly not treated as proof (the panel's
  wording: "green merged PRs prove nothing").

## 7. Child tickets

| # | Child | Author → reviewer | Status (as of 2026-09-27) |
| --- | --- | --- | --- |
| #8872 | Area lanes: atlas/lexicon/practice + `open_model_data` only, after two refactors; other four areas stay on shards | Codex → Claude | being rewritten to DoR |
| #8874 | Stale `.git/index.lock` root cause | Codex → Claude | being rewritten to DoR |
| #8876 | More balanced shards on the Team plan | Codex → Claude | open, ready |
| #8877 | Slow tests batch 1: nightly tier for four full-scope tests | Cursor → Claude | open, ready |
| #8878 | Slow tests batch 2: fsync / git bootstrap / guard memoization | Codex → Claude | open, ready |
| #8879 | Slow tests batch 3: cache deterministic recomputation | Cursor → Claude | open, ready |
| #8880 | Slow tests batch 4: stub non-under-test boundaries; batch slot lookups | Codex → Claude | open, ready |
| #8881 | Slow tests batch 5: smaller fixtures, one shared browser | Codex → Claude | open, ready |
| #8882 | Slow tests batch 6: `open_model_data` fixtures | Codex → Claude | open, **blocked by #8809 P3** |
| #8883 | Wiki prompts describe paging | Cursor → Claude | open, **blocked by #8873 merge** |
| #8884 | Merge queue must not drop green PRs (timeout 30→60 min) | operator setting; driver verifies | open, **waiting on operator** |
| #8885 | This plan document | Claude → Codex | this document |
| #8886 | DoR/DoD enforcement for every agent-filed issue | Codex → Claude | open, ready |

Already landed, not tracked as an open child: pre-commit guards for the
timeout and stale-epic checks (PR #8864, merged) and the Team-plan capacity
move (2026-09-27, per epic #8875 text).

## 8. Risks and stop rules

- **Under-selection risk in area lanes.** Epic #8875's stop policy: a child
  that would lose or skip tests (collected count below baseline, or a
  known-failing change passing in replay) stops that child; the epic
  continues with the others. #8872's own stop policy is the same, scoped
  to the two lanes: any replayed failed run or fault injection that lane
  selection would have let pass stops the lane change, while the two
  prerequisite refactors still land on their own.
- **Merge-queue self-starvation recurring.** If `max_entries_to_build`
  interacts with the runner cap the way it did at 20 concurrent jobs
  (§2e), the same failure mode could reappear even at 60 concurrent jobs
  under higher load. The plan (per #8872's original description) is to
  keep `max_entries_to_build: 4` and measure drop rate, time-to-land, and
  runner occupancy for a week after the timeout change, rather than
  assuming the Team plan alone fixes it.
- **Coupling drift.** The 90-file (~6%) coupling figure in §2f was ~1,075
  files 22.5 hours earlier this same week, from one PR. Any area-lane
  design that assumes today's coupling is permanent needs the
  re-measure-before-2a-style discipline already used once on #8750 (re-
  check the actual reachable fraction before changing anything that
  depends on it).
- **Operator-gated items don't silently stall.** #8884 (timeout) and the
  merge-queue-full-backstop decision that #8872 depends on both require an
  operator or repo-admin action the agent fleet cannot take itself
  (permission layer refusal, confirmed on #8750). These are called out
  explicitly here so they are visibly "waiting", not silently dropped.
- **Residual policy** (epic #8875): each child owns its own residual; the
  epic closes only when every child is closed or re-homed with the
  operator's agreement.

## 9. How progress is measured

- **Baseline vs. after, run as the unit** (not per-shard): the method fixed
  on #8750 before any after-window was collected — before = the 459-run
  baseline window (§2a); after = the first ≥100 completed runs following
  each change's merge; stratify by `pull_request` vs. `merge_group` and by
  UTC hour; report account concurrency (peak and share of time at the cap)
  for both windows so a quieter after-period is not mistaken for an effect.
- **Tools kept with the infra lane** so the after-window uses identical
  code to the baseline: `ci_baseline.py`, `ci_analyze.py` (named on #8750).
- **Metrics tracked**: pytest shard queue wait (median, share of runs with
  any shard waiting >10 min); time to CI Gate completion; jobs per run;
  merge-queue ejections without a test failure; and, for the area-lanes
  change specifically, the replay-based escape count (§6) rather than a
  count of green merged PRs.
- **Epic-level acceptance** (#8875 AC-01–AC-04, verbatim): pytest-phase p95
  wall time over 20 consecutive full runs at least 40% below baseline;
  zero green-PR drops with reason `checks_timed_out` over 7 days after the
  merge-queue change; every child ticket passing
  `scripts/ci/check_issue_task_quality.py --strict` and closed with its
  DoD evidence; this plan document existing and matching what shipped.
- **This document** is the one place all of the above numbers are meant to
  be traceable from — every number above cites a run id, an issue comment,
  or a report path. If a future update to this program can't trace a new
  number the same way, the update should mark it unverified rather than
  restate it as fact, per the stop policy that has applied to every
  measurement on #8750 so far.
