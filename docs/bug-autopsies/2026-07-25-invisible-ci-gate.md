# The CI gate was invisible, and the suite rotted behind it

**Date:** 2026-07-25
**Symptom:** every PR reported a green CI Gate while the full test suite was broken — 111 failures on the first unconditional run, 6 of them red on `main` itself, plus two hangs that wedged any complete run.
**Severity:** systemic — the repository's only required check could pass while the build
pipeline, the quality gates, and 111 tests were broken.
**Surfaced by:** #5766 (CI Gate reboot), which made the full suite run unconditionally.

---

## Root cause

CI selected tests by changed files. A PR ran only the tests its diff "touched".

That is a reasonable-sounding optimization with one fatal property: **a test that nobody's
diff touches never runs again, forever.** There is no alarm, no decay signal, no report.
The gate stays green because it is not looking.

The suite silently accumulated:

- **111 failures** on the first unconditional full run
- **6 tests red on `main` itself**, in `tests/build/` — the regression cover for the
  pipeline that builds learner modules
- **2 hangs** that wedged any full-suite run
- **2 mutually contradictory invariants** living side by side, each with a passing test,
  because the two tests were never scheduled in the same run
- **4 test files** importing modules deleted in 2026-06 (`v6_build.py`) and 2026-07
  (`phases/v6-write.md`) — one of those deletions was titled *"delete retired v6_build.py
  **+ test suite**"*, and its sweep missed them

None of it was visible. Every PR was green.

## Why this is the worst class of gate bug

A red gate stops the line and gets fixed within the hour. A gate that reports green while
measuring nothing produces **false confidence that compounds**: every merge on top of it
inherits the assumption that the suite passed. The longer it runs, the more expensive the
truth becomes. 111 failures is not 111 mistakes — it is one mistake, undetected for a long
time.

## The contradiction, as the sharpest example

Two tests, both passing before the reboot, impossible to satisfy at once:

| Test | Asserts |
| --- | --- |
| `test_v7_build_resume.py` (3 tests) | a fresh `llm_qg.json` MAY substitute for a DB record — so a resumed build in a fresh worktree (no gitignored `llm_qg.db`) doesn't re-run paid LLM gate calls |
| `test_v7_build_reviewer_assert.py::test_llm_qg_phase_artifact_requires_current_db_record` | a fresh `llm_qg.json` must NOT count as a pass without a current DB record — so a stale or hand-written file can't make a build skip its LLM quality gate |

Both are defensible. Both cannot be true. They coexisted because changed-files selection
never put them in the same run, so **the codebase held two incompatible definitions of
"this quality gate passed" and nothing noticed.**

PR #5784 restored the fallback, satisfied the first three, and silently broke the fourth —
i.e. made a quality gate accept an unverified artifact. It had already passed an
independent cross-family review that approved it, because the reviewer could not run the
tests (its sparse worktree omits `curriculum/`, without which `tests/build/` cannot even
collect). **Only the rebooted CI caught it.**

Resolution: the production change was reverted (the DB stays authoritative); the three
resume tests are `xfail(strict=True)` naming the contradiction. `strict` matters — if
someone makes them pass, the file fails until the conflict is resolved deliberately rather
than drifting back. Which contract wins is a design decision, not a code fix, and is
handed to the advisor seat.

## Prevention

1. **A gate must measure the whole artifact, unconditionally.** Selecting tests by diff
   trades an invisible, unbounded correctness risk for minutes of CI. The replacement —
   four parallel shard jobs — runs the whole suite in ~9 minutes, *faster* than the thing
   it replaced.
2. **Sharding must be provably total.** `tests/test_ci_shard_partition.py` extracts the
   split expression from `ci.yml` and asserts a true partition: union == every test file,
   no overlap, none empty, no reference to git/diff/changed/base-ref. An injected
   off-by-one that drops 50 files fails the test and names them.
3. **The aggregate check must require every job.** `coverage-floor` was initially missing
   from `ci-gate.needs`, so the sole required check could pass while coverage enforcement
   failed — the same bug shape one level up.
4. **Coverage must refuse to pass on no data.** With four shards no single one sees the
   whole suite, so per-shard enforcement would measure a quarter and pass vacuously. The
   combining job exits non-zero on zero coverage files.
5. **Skips must be conditional, named, and proven both ways.** Every skip added here names
   the missing artifact and was verified to *run* its assertions where the artifact exists.
   A test that skips unconditionally is worse than one that fails: it looks green while
   asserting nothing — the gate's own failure, in miniature.
6. **Environment premises rot too.** The CI install stripped torch, justified in-comment by
   "no first-party module imports them" — true for *direct* imports, false in practice:
   `stress_annotator._get_stressifier()` → `ukrainian_word_stress` → `stanza` → `torch`.
   The premise survived because nothing ever ran those tests. A comment asserting a fact
   about the codebase should say how to re-verify it.
7. **Deleting a module must delete its tests, verifiably.** Two separate V6 removals left 4
   test files importing absent modules. Under changed-files selection they simply never ran.

## Diagnostic lessons worth keeping

- **A hang in a "parallel-only" test is not necessarily about parallelism.** A 4-way matrix
  (`serial` / `-n 1` / `loadfile` / `-n auto`) with a 60s heartbeat identified the hanging
  test directly: each log's last line is a *bare test name with no matching PASSED*. The
  `serial` variant — no xdist, no workers, no IPC — still hung, which falsified a
  well-argued 4-seat panel conclusion that the hang lived in the xdist/execnet plumbing.
  Root cause: `apply_worker_memory_limit()` applied in the **coordinator**, so under an
  in-process test the coordinator *is* pytest and pytest set an RLIMIT on itself.
- **When a hang appears to "move" after you quarantine one test, suspect two hangs.** It
  was never moving; the next one was surfacing.
- **`conclusion: failure` + `jobs: []` can be a GitHub transient, not a bad workflow file.**
  Push an empty commit and re-observe before bisecting. The tell: sibling workflows the
  branch never touched fail identically while passing on another branch.
- **Review and the gate catch different things; neither is optional.** The cross-family
  reviewer approved a change that broke an invariant, honestly noting it could not run the
  tests — the gate caught it. A separate review caught a defect the gate never could: a
  TOCTOU test that could delete a concurrent session's state.
