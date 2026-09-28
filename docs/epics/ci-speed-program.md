# CI program — plan v2

> Epic **#8875** (parent: infra stream epic #6943). v2 written by the infra driver (Claude), 2026-09-28, from the
> read-only audit `audit-ci-program-v2` (186 `ci.yml` runs, 2026-09-27T11:02Z–2026-09-28T09:01Z; scratch data and
> scripts in `/var/tmp/lu/learn-ukrainian/audit-ci-v2/`). v1 (2026-09-27) is in git history; its baseline (459 runs,
> 2026-09-22→24) is still the "before" reference. **The live task list is epic #8875's sub-issues**; this document is
> the plan and the decisions, not a status board.

## 1. Outcome

Agents and the operator get CI feedback that is **fast, trustworthy, and paid for once**:

- a code PR's CI answer arrives in minutes, not tens of minutes;
- a green PR is never ejected from the merge queue by a flaky test or an infrastructure hiccup;
- a red run says *what* failed without downloading artifacts;
- each change's full suite runs once on GitHub's runners — not repeatedly on the VPS by workers and reviewers
  (operator, 2026-09-28: "running the same test in parallel is so stupid").

Non-goals: the V7/fresh-build curriculum pipeline, separate repositories, self-hosted runners (public repo — GitHub
advises against them), paid larger runners, weakening the merge queue, the nightly run, or CI Gate as the single
required check.

## 2. Where we are (measured)

| Metric | v1 baseline p50 / p95 | Now p50 / p95 | Target |
|---|---|---|---|
| PR full-tier time to CI Gate (min) | 16.4 / 37.6 | 9.2 / 11.2 | **p50 ≤ 6.5 / p95 ≤ 8** |
| merge_group wall (min) | 15.7 / 29.9 | 9.0 / 9.8 | **p95 ≤ 8** |
| Enqueue → merge, first add (min) | — | 10.0 / 18.7 | **p95 ≤ 12** |
| pytest job queue wait (min) | 1.2 / 12.7 | 0.0 / 1.5 | keep ≤ 2 |
| Slowest ÷ mean shard `Run pytest` | — | 1.7 | **≤ 1.3** |
| Fixed setup per pytest shard (min) | ~2 | 2.1 | **≤ 1.5** |
| Runner-minutes per full run | ~50 | 75 | **≤ 60** |
| Merge-queue ejections by flakes | — | 4 / 80 runs (5 %) | **≤ 1 / 100** |
| PR reruns that go green with no code change | — | 4 / 103 | **≤ 1 %** |
| `checks_timed_out` drops | 2 in a day | 0 | **0** |
| PR runs forced to full by the `full-ci` label | — | 71 / 103 | **< 10 %** |

Most of the gain so far came from the Team plan (20 → 60 concurrent jobs) and 10 duration-balanced shards (#8876),
landed the same day, so the two effects are not separable. **What now dominates** (audit §A):

1. **The `full-ci` habit.** 57 of 85 PRs carry the label (added by agents following a drive-epic rule whose premise
   #8707 removed). It forces the full suite *and* the 7.8-minute Frontend job; the path-selected tier fired 0 times.
2. **Straggler shards.** Per-shard medians are flat (3.4 min), but in each run one shard takes 6.3 against a 3.7 mean —
   a tail effect inside shards (`--dist=loadfile`), not partition imbalance.
3. **Fixed setup** of 2.1 min per shard: `fetch-depth: 0` checkout, a Postgres service plus apt install in all ten
   shards, and a Python-env block copied three times.
4. **Flakes and infra hiccups.** Six merge-queue ejections in 22 h, four of them re-queued unchanged and merged;
   PyPI timeouts/503s failed two shards this morning; a pydantic/pydantic-core skew turned one setup problem into
   36 failing files across all ten shards (`--no-deps` install, no integrity check).
5. **Duplicate test execution.** The same change is tested by the worker on the VPS, the reviewer on the VPS, PR CI,
   and the merge queue — the full suite on GitHub twice, plus overlapping local suites that drove the VPS to load 32.

## 3. Decisions for the panel

Each needs operator or advisor approval before its task is dispatched (operator contract item 12). Recommendation first.

- **D1 — Retire the blanket `full-ci` habit (#9066).** Remove the drive-epic rule that tells drivers to label every
  PR touching `tests/`; the label stays for the rare change the classifier cannot see. `full-ci` no longer forces the
  Frontend job unless site paths changed. *Why safe:* the selected tier already runs the `repo_wide` tests (ci.yml
  :508-522, since #8707), and the merge queue remains the full backstop (D4).
- **D2 — Flake control (#9067).** A quarantine registry (node id, issue, owner, expiry); `pytest-rerunfailures`
  `@flaky(reruns=1)` applies **only** to listed tests; a nightly JUnit flake ledger; an expired entry opens or updates
  its issue at night — it never turns every branch red at once (the opsec skip-expiry time bomb, 2026-09-23). Every
  entry points at an open fix issue; the registry is not a parking lot.
- **D3 — Merge queue build concurrency (#8884 AC-03).** Keep `max_entries_to_build: 4` for now: 4 × 17 jobs = 68 is
  above the 60 cap on paper, but runs spent only 0.57 % of busy time at ≥ 60 concurrent jobs and 0 timeouts occurred.
  Re-decide after D1 and #9062 cut jobs and minutes; drop to 3 if a `checks_timed_out` ejection recurs.
- **D4 — PR tier vs merge-queue tier (#8872 prerequisite).** The merge queue runs the full suite for every code
  change; PRs get the path-selected tier (and, after #8872, area lanes). This reverses part of operator decision
  #8437 (merge_group used the same path classes as PRs) — the queue becomes the single full gate, which is the
  standard merge-queue pattern and what makes PR-side selection safe.
- **D5 — Test once, on GitHub (#9057).** Dispatched workers run only the tests covering the files they changed and
  prove full-suite claims with `gh workflow run ci.yml --ref <branch>`; reviewers review the diff and cite CI runs
  instead of re-running suites. (Implemented in #9057; listed here so the panel sees the whole policy.)

## 4. Task set — one ordered program (all are #8875 sub-issues)

Waves run top-down; items in one wave run in parallel only when they touch different files. `ci.yml` changes are
serialized in the order given.

| Wave | Issue | What | Depends on |
|---|---|---|---|
| 0 (landing) | #8997 ✅, #8967, #8960 + #9020 + #8998, #8766 + #8795 + #8767, #9057, #8881 | flakes, Gate race, CI setup breakages, test-once rule, slow-test batch 5 | — |
| 1 (now) | #9058 | `ci_timings` fails loudly on empty pages; reports every metric in §2 | — |
| 1 | #9059 | workflow hygiene: `timeout-minutes`, `concurrency`, least privilege, SHA-pinning policy, grouped Dependabot bumps | — |
| 1 | #9060 | the two untracked merge-queue flakes | — |
| 2 | #9061 → #9062 → #9063 | `ci.yml`, serialized: install integrity + network retries; setup cost (composite action, postgres digest, lighter checkout); failing tests in the job summary | #8967 merged |
| 2 | #9064 | pre-commit parity: same ruff version, one formatting-only commit then `ruff format` enforced, cheap guards moved to pre-commit | #8795 merged |
| 2 | #8880 (rest) | slow-test batch 4 remainder | — |
| 3 (decided) | #9066 (D1), #9067 (D2) | `full-ci` habit; flake quarantine + ledger | panel; #9067 after #9058 |
| 4 | #8877, #8879, #8882 | slow-test batches touching P3a files | #8809 P3a merged |
| 4 | #9065 | straggler root cause; `worksteal` vs `loadfile` A/B | #9058; #8880 + #8881 |
| 5 | #8872 → #8506 | area lanes, then import-graph selection | D1, D4 |
| watch | #8876 AC-02/AC-05, #8884 AC-02 | tier equality on the nightly; 20-run p95; 7-day drop window to 2026-10-04 | — |

Out of this program: #8921 (Claude workers backgrounding pytest — harness), #8645 (OOM — host, waits on #8860),
#9023 (open-model-data suite, skipped in CI), #8572 remainder (open-model-data lane).

## 5. Risks and stop rules

- **Under-selection** (D1, D4, #8872, #8506): any change that lets a known-failing replay pass, or lowers the
  collected-test count of a tier, stops that change; the merge queue stays full.
- **Quarantine as a parking lot** (D2): an entry without an open fix issue fails the registry lint; entries expire.
- **Metric drift:** every number in §2 must be reproducible by `scripts.ci.ci_timings` once #9058 lands; until then
  the audit's scripts are the reference. A number that cannot be traced to a run id is marked unverified.
- **Nightly schedule reliability:** the 2026-09-27 nightly started ~6 h late and the 2026-09-28 one had not started by
  09:40Z. GitHub does not guarantee `schedule` timing; #8876 AC-02 uses whichever nightly completes.

## 6. Done when

Every #8875 sub-issue is closed with its evidence; the §2 targets hold over ≥ 100 runs per event measured by
`ci_timings`; and this document matches what shipped.
