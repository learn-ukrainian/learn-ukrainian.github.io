# CI program — plan v2.3

> Epic **#8875** (parent: infra stream epic #6943). Written by the infra driver (Claude), 2026-09-28, from the read-only
> audit `audit-ci-program-v2` (186 `ci.yml` runs, 2026-09-27T11:02Z–2026-09-28T09:01Z; scratch data and scripts in
> `/var/tmp/lu/learn-ukrainian/audit-ci-v2/`). v2.1 folds in the three-seat panel review of v2 (Fable as advisor, Codex,
> Grok: every decision ADOPT or ADOPT WITH CHANGES, no REJECT; their results are `batch_state/tasks/panel-ci-v2-*.result`).
> v1 (2026-09-27) is in git history; its 459-run baseline (2026-09-22→24) stays the "before" reference.
> **The live task list is epic #8875's sub-issues**; this document is the plan and the decisions, not a status board.

## 1. Outcome

Agents and the operator get CI feedback that is **fast, trustworthy, and paid for once**:

- a code PR's CI answer arrives in minutes, not tens of minutes;
- a green PR is never ejected from the merge queue by a flaky test or an infrastructure hiccup;
- a red run says *what* failed without downloading artifacts;
- each change is tested on GitHub's runners at two required stages: the PR runs its classified tier (full, or a
  narrower path-selected tier once #9066/#8872 ship), and the merge queue runs the full required Python tier on the
  merged tree for every code change (D4). Workers and reviewers do not re-run suites on the VPS (operator,
  2026-09-28: "running the same test in parallel is so stupid").

Non-goals: the V7/fresh-build curriculum pipeline, separate repositories, self-hosted runners (public repo — GitHub
advises against them), paid larger runners, weakening the merge queue, the nightly run, or CI Gate as the single
required check.

## 2. Where we are (measured) and targets

| Metric | v1 baseline p50 / p95 | Now p50 / p95 | Target |
|---|---|---|---|
| PR full-tier time to CI Gate (min) | 16.4 / 37.6 | 9.2 / 11.2 | **p50 ≤ 7.5 / p95 ≤ 9.5**; stretch 6.5 / 8 only if #9065 removes the straggler gap |
| PR time to CI Gate, all tiers (min) | — | 9.2 / 11.6 | reported by #9058; falls as the full-tier share falls |
| Share of PR runs on the full tier | 89 % | 93 % | **≤ 40 %** after D1 + D4 |
| PR runs label-forced to full (`full-ci`) | — | 71 / 103 | **< 10 %** |
| Selected-tier PR wall and runner-minutes | — | n = 0 (never fired) | reported by #9058 once it fires |
| merge_group wall (min) | 15.7 / 29.9 | 9.0 / 9.8 | **p95 ≤ 9** |
| Enqueue → merge, first add (min) | — | 10.0 / 18.7 | **p95 ≤ 14** |
| pytest job queue wait (min) | 1.2 / 12.7 | 0.0 / 1.5 | keep ≤ 2 |
| Slowest ÷ mean shard `Run pytest` | — | 1.7 | **≤ 1.3** |
| Fixed setup per pytest shard (min) | ~2 | 2.1 | **≤ 1.7** (≤ 1.5 needs Postgres only in the shards that use it — in #9062's scope) |
| Runner-minutes per full run | ~50 | 75 | **≤ 60 for runs without Frontend**; ≤ 67 with Frontend |
| Merge-queue ejections by flakes | — | 4 / 80 runs (5 %) | **≤ 1 / 100** |
| Queue-only escapes (PR tier green, queue red on a test the PR tier did not run) | — | not measured | **≤ 1 / 100 queue runs** (the price of D1/D4, measured by #9058) |
| PR reruns that go green with no code change | — | 4 / 103 | **≤ 1 %** |
| `checks_timed_out` drops | 2 in a day | 0 | **0** |

#8876's own AC-05 is a ≥ 25 % cut of the 14.2-minute slowest-shard wall over 20 runs; the audit measured 32 % on the
job basis. The epic-level 40 % pytest-phase figure (#8875 AC-01) is measured as the slowest shard's `Run pytest` step,
currently −34 %; it is met only through #9065.

Most of the gain so far came from the Team plan (20 → 60 concurrent jobs) and 10 duration-balanced shards (#8876),
landed the same day, so the two effects are not separable. **What now dominates** (audit §A):

1. **The `full-ci` habit.** 57 of 85 PRs carry the label, added by agents following a drive-epic rule whose premise
   #8707 removed. It forces the full suite *and* the 7.8-minute Frontend job; the path-selected tier fired 0 times.
2. **Straggler shards.** Per-shard medians are flat (3.4 min), but in each run one shard takes 6.3 against a 3.7 mean —
   a tail inside shards (`--dist=loadfile`), not partition imbalance. Collection cost per shard is unmeasured.
3. **Fixed setup** of 2.1 min per shard: checkout 0.7 (`fetch-depth: 0`), Postgres service 0.4 and apt 0.2 in all ten
   shards, and a Python-env block copied three times.
4. **Flakes and infra hiccups.** Six merge-queue ejections in 22 h, four re-queued unchanged and merged; PyPI
   timeouts and 503s failed shards on 2026-09-28; a pydantic/pydantic-core skew turned one setup problem into 36 failing
   files across ten shards (`--no-deps` install, no integrity check).
5. **Duplicate test execution** on the VPS by workers and reviewers, on top of the two GitHub runs (fixed by D5).

## 3. Decisions (panel-reviewed)

- **D4 — The merge queue is the single full gate (#9073; first).** On `merge_group`, any change that touches code, tests,
  workflows, dependency files, or an unclassifiable path runs the full required Python tier on the merged tree;
  **frontend-only changes too** — Python tests read `site/` and `packages/activity-kit/` files the classifier treats as
  frontend-only (e.g. `tests/test_hramatka_teacher_dashboard_contract.py`), so skipping them in the queue would be a
  real coverage hole (panel split resolved in Codex's favour on that evidence). Docs-only and content-only changes
  keep their #8437 classes unless a Python test reads the path (then the path is treated as code). "Full" means
  everything except the `slow` and `atlas_release` markers, which run only nightly. This reverses the part of operator
  decision #8437 that gave `merge_group` the same path classes as PRs; it is the standard merge-queue pattern and what
  makes any PR-side selection safe. Cost: a genuine failure caught only by the queue costs one ejection cycle (~10 min),
  which the drive-epic skill already treats as same-hour work, and is measured as queue-only escapes (§2).
- **D1 — Retire the blanket `full-ci` habit (#9066; after #9073 and #9057).** Remove the drive-epic rule that labels
  every PR touching `tests/`; the label stays for the rare change the classifier cannot see. `full-ci` stops forcing
  the Frontend job unless site paths changed.
- **D2 — Flake control (#9067).** A quarantine registry (node id, fix issue, owner, expiry ≤ 30 days, one renewal).
  *Admission:* an open fix issue plus at least two observed flaky failures (run ids) — the registry lint rejects
  anything else. *Behaviour:* `pytest-rerunfailures` reruns **only** listed tests and **never** on the nightly
  `schedule` run, so a still-flaky test shows up red on the nightly; every rerun (first-attempt failure, rerun green)
  is written to the job summary and the nightly flake ledger. *Expiry:* on the expiry date the nightly opens or updates
  the fix issue; after a 7-day grace the entry's rerun is removed on every event, so an unfixed flake fails PR and queue
  runs again — a bounded, announced return, never a surprise repo-wide red (the 2026-09-23 time bomb). *Escalation:*
  a listed test that needs its rerun in more than 5 % of the week's queue runs escalates its issue to the driver's queue.
  Timing flakes that hit the pytest timeout (thread method) cannot be rerun and always need a real fix. The ledger first
  proves it can read rerun records under the repo's JUnit family, and it shares one JUnit parser with #9063.
- **D3 — Merge-queue build concurrency (#8884 AC-03).** Keep `max_entries_to_build: 4` (0.57 % of busy time at ≥ 60
  concurrent jobs, 0 timeouts). Re-decide when queue wait, runner saturation or first-enqueue p95 regress — not only
  after an ejection — and after #9066 and #9062 change the job mix. Other workflows on the same events share the
  60 slots, so the paper figure (4 × 17 = 68) understates the peak.
- **D5 — Test once per stage (#9057).** Dispatched workers run only the tests covering what they changed (including
  dependents of a changed shared helper), in the foreground. The PR's own CI run (its classified tier) is the proof for
  the PR; the merge queue's full run is the proof for `main`; a `workflow_dispatch` run only when a brief asks (branch
  with no PR, baseline capture, diagnosis). Reviewers review the diff and cite CI runs.

## 4. Task set — one ordered program (all are #8875 sub-issues)

Waves run top-down; items in one wave run in parallel only when they touch different files. Three serial chains:
`ci.yml` (#9061 → #9062 → #9063), the classifier (#9073 → #9066 → #8872 → #8506), and `drive-epic/SKILL.md`
(#9057 → #9066).

| Wave | Issue | What | Depends on |
|---|---|---|---|
| 0 (landing) | #8997 ✅, #8967 ✅, #8960 + #9020 + #8998, #8766 + #8795 + #8767, #9057, #8881 (part 1) | flakes, Gate race, CI setup breakages, test-once rule, slow-test batch 5 part 1 | — |
| 1 | **#9073** | D4: merge_group runs the full tier for every code change | — |
| 1 | #9058 | `ci_timings`: fail loudly; report every §2 metric, including all-tier PR time, full-tier share, queue-only escapes, and a Frontend job breakdown (install / Astro build / tests) | — |
| 1 | #9059 | workflow hygiene: timeouts, PR-only cancellation, least privilege, SHA-pinning policy, Dependabot | after #8767's PR (same `atlas-grow.yml`) |
| 1 | #9060 | remaining merge-queue flakes (delegate nonce env, task_scratch wrapper, `/tmp`-scan test) | — |
| 1 | #9065 (measure) | per-file variance from existing JUnit + `--collect-only` time per shard | — |
| 2 | #9061 → #9062 → #9063 | `ci.yml`, serialized: install integrity + network retries; setup cost (composite action, Postgres digest and only where used, lighter checkout — measured); failing tests in the job summary (shared JUnit parser) | #8967 ✅ |
| 2 | #9066 | D1 | #9073, #9057 |
| 2 | #9064 | pre-commit parity: same ruff version; one formatting-only commit, then `ruff format` enforced; cheap guards shifted left | #8795; off the speed-critical path |
| 2 | #8880 (rest) | slow-test batch 4 remainder | — |
| 3 | #9067 | D2 | #9058 |
| 3 | #9065 (A/B) | `worksteal` vs `loadfile` via workflow_dispatch | #8880, #8881 |
| 4 | #8879, #8882 | slow-test batches that touch #8809 P3a files (#8882 shares `test_v4_real_slot_mechanism.py` with the open-model-data lane's #8572 — one owner) | #8809 P3a merged |
| 4 | #8877 | move four full-scope tests to the nightly tier | P3a merged **and** the nightly shown reliable (see §5) |
| 5 | #8872 → #8506 | area lanes, then import-graph selection; one shared escape-replay proof (#8506's replay includes #8872's set) | #9073, #9066 |
| watch | #8876 AC-02/AC-05, #8884 AC-02 | tier equality on the nightly; 20-run sample; 7-day drop window to 2026-10-04 | — |

Out of this program: #8921 (Claude workers backgrounding pytest — harness), #8645 (OOM — host, waits on #8860),
#9023 (open-model-data suite, skipped in CI), #8572 remainder (re-homed to the open-model-data lane, 2026-09-28).

## 5. Risks and stop rules

- **Under-selection** (#9066, #8872, #8506): no PR-side narrowing ships before #9073. Before any selector ships, its
  proof is a **fault-injection oracle**: for each of a fixed set of injected faults (and every historically failed run
  in the replay set), the full suite is the oracle for which tests fail, and the selector must select **every** one of
  them — **zero misses**; merged-PR replays and importer checks alone are not proof. #8506's replay set includes
  #8872's. A selector change that misses, or that lowers a tier's collected-test count, stops. Queue-only escapes
  above 1 / 100 queue runs reopen D1.
- **Quarantine as a parking lot** (#9067): an entry without an open fix issue fails the registry lint; entries expire
  and the nightly shows it.
- **Nightly reliability:** the 2026-09-27 nightly started ~6 h late and the 2026-09-28 one had not started by 09:40Z.
  GitHub does not guarantee `schedule` timing. #8877 (moving tests to the nightly tier) waits until the nightly has run
  on 7 consecutive days; #8876 AC-02 uses whichever nightly completes.
- **Metric drift:** every §2 number must be reproducible by `scripts.ci.ci_timings` once #9058 lands; a number that
  cannot be traced to a run id is marked unverified.

## 6. Done when

Every #8875 sub-issue is closed with its evidence; the §2 targets hold over ≥ 100 first-attempt runs per event and tier,
measured by `ci_timings`; and this document matches what shipped.
