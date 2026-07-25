# CI hang — unbounded jobs, unbounded subprocesses

**Date:** 2026-07-24/25 · **Issues:** #5740, PR #5735 · **Category:** ci-availability

## What broke

The whole fleet could not ship for a day. GitHub Actions runs queued at 16:40Z were still
`in_progress` more than six hours later, with everything else stacked behind them.

The visible symptom was queue starvation, and the visible cause was job fan-out: `ci.yml`
dispatched 21 jobs per push at ~47 merges/day. That reading was wrong, or rather it was the
amplifier and not the cause.

## Why

Three independent bounds were all missing at once, so a single blocked syscall became a
six-hour outage.

**1. No `timeout=` on subprocess calls in tests.** 325 `subprocess.run` / `Popen` /
`check_output` / `call` invocations across 87 test files passed no timeout. A subprocess that
blocks hangs its test forever.

**2. No `timeout-minutes` on any CI job.** GitHub's default of **360 minutes** therefore
applied. The hung test did not fail — it held a runner slot for six hours.

**3. No `pytest-timeout`.** So there was no per-test bound either, and no way to learn *which*
test hung. The job simply stopped producing output.

The measurement that settled it, from run `30109965086`:

```
Test (pytest) [3/4]:  357 min -> cancelled   <- hung
Test (pytest) [4/4]:    9 min -> failure
Test (pytest) [2/4]:    8 min -> failure
Test (pytest) [1/4]:   10 min -> failure
```

One shard ran 357 minutes while its siblings finished in 8–10. 357 minutes is not a slow test;
it is the 360-minute platform default minus startup. The number itself was the diagnosis.

Two further defects kept the failure invisible:

**`main` cancelled its own verification.** `concurrency.cancel-in-progress: true` applied to
`push: main` as well as PR branches, so each merge killed the previous merge's run. Of the last
30 CI runs on `main`: **14 cancelled, 16 failed, 0 succeeded.** There was no working post-merge
signal, so "main is green" had been meaningless for some time.

**A red check that gated nothing.** `frontend-e2e` was absent from `ci-gate.needs`. A real
learner-facing regression (Practice setup dashboard rendering 940px of content in a 768px
viewport, pushing the primary start/resume CTAs below the fold) stayed red from ~11:53Z while
**32 commits merged over it**.

## Prevention

- **Bound every layer, not the convenient one.** Job timeout is a tourniquet — it stops the
  bleeding but names no culprit. Per-test timeout is the diagnostic. `timeout=` at the call site
  is the cure. Shipping only the tourniquet converts a 6-hour outage into a 40-minute one; it does
  not stop hangs.
- **A platform default is not a decision.** Nobody chose 360 minutes. Any resource with an
  implicit ceiling should have an explicit one, chosen against what the job actually does.
- **Read the number, not the label.** A rerun loop reported "transient" four times. Four identical
  failures of the same shard is a signal to read the log, not to retry.
- **`cancel-in-progress` is not uniformly safe.** It is right for PR branches, where a newer push
  supersedes an older one. It is wrong for `main`, where each run verifies a *different* commit
  and cancelling destroys the only post-merge signal. Split the concurrency policy by ref.
- **A check outside the gate's `needs` will eventually be ignored.** Either it gates or it is
  advisory-by-design and labelled as such. `frontend-e2e` was neither, so a genuine regression
  shipped 32 times. When a gate must be added while red, prefer `xfail(strict=True)` — it
  self-destructs when the bug is fixed — over `continue-on-error`, which never does.
- **Distrust green built on a silent success path.** The lane-capability probe printed on every
  failure branch and nothing on success, which made a *working* lane read as broken. Silence is
  not a status.

## Related

- #5740 — sweep the 325 call sites, add `pytest-timeout`, add a guard test against reintroduction
- PR #5735 — job timeouts, 21→8 jobs, restored paths-filter incident comments
- #3873 / #4888 / #4936 / #5351 / #5354 — the data-coupling filter-gap family; the paths-filter
  comments deleted-and-restored in #5735 are the institutional memory of those five
