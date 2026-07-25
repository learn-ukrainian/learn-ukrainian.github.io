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
it is the 360-minute platform default minus startup.

What that number does and does not prove, stated precisely — because the first draft of this
autopsy overstated it (caught in cross-family review of PR #5741, *after* it had already been
merged): a duration pinned to the platform ceiling proves the job was **killed by the cap rather
than finishing**, i.e. something blocked indefinitely. It does **not** identify which test hung,
and it does not by itself establish a blocked subprocess as the mechanism. Absent `pytest-timeout`
there was no per-test attribution at all; the subprocess mechanism was inferred from the 325
unbounded call sites and from a later stall at
`tests/wiki/test_ukrainian_wiki_corpus.py`, whose `_configure_search` helper does not stub the real
`dense_rerank.rerank_candidates`. Two observed stalls were at *different* tests, which argues the
hang was systemic rather than one bad test.

Two further defects kept the failure invisible:

**`main` cancelled its own verification.** `concurrency.cancel-in-progress: true` applied to
`push: main` as well as PR branches, so each merge killed the previous merge's run. Of the last
30 CI runs on `main`: **14 cancelled, 16 failed, 0 succeeded.** There was no working post-merge
signal, so "main is green" had been meaningless for some time.

**A red check that gated nothing.** `frontend-e2e` was absent from `ci-gate.needs`. A real
learner-facing regression (Practice setup dashboard rendering 940px of content in a 768px
viewport, pushing the primary start/resume CTAs below the fold) stayed red from ~11:53Z while
**32 commits merged over it**.

## The queue freeze had two more causes, established later

The sections above explain the **hang**. They do not explain why, once the hang was bounded, the
fleet still could not ship. Two further causes were established on 2026-07-25 and belong here,
because a reader who stops at "unbounded subprocesses" will mis-diagnose the next occurrence.

### A required gate went red via a governance bypass, not a CI defect

`Lesson Schema Drift` is a **required** job (`ci-gate.needs`). It regenerates
`docs/lesson-schema.yaml` from `site/src/components/**` and fails if the tracked copy differs. It
went red on `main` and stayed red — and because every branch is cut from `main`, **all open pull
requests inherited the failure and became unmergeable.** That, not runner starvation, is why nothing
could merge by morning.

Cause: commits `5f425a5fe1` and `9debd99699` reached `main` **with no pull request**
(`/commits/{sha}/pulls` returns `[]` for both; neither carries the `(#NNNN)` suffix a squash-merge
adds). Both touch `site/src/components/**` without regenerating the tracked artifact. A direct push
skips PR CI entirely, so the required job never evaluated them.

**The gate machinery was not at fault.** The `lesson_schema` paths filter explicitly covers
`site/src/components/**`, `tests/test_lesson_schema_filter_coverage.py` enforces that coverage, and a
`lesson-schema-drift` pre-commit hook is scoped to the same files. All three were bypassed, not
misconfigured. Fixed by regenerating in PR #5746; the durable fix is requiring pull requests on
`main`.

A structural aggravator, worth naming: because the tracked artifact embeds a **content hash of a
whole directory**, every component PR must regenerate it, and any two component PRs therefore
conflict on that one line. Two individually-green PRs can also combine into a hash matching neither —
a semantic merge conflict that nothing validates without a merge queue. Resolving PR #5739 produced a
*third* hash (`2ad46d68…`), belonging to neither side.

### The test environment did not fit the runner

Shard `[3/4]` failed **identically across unrelated PRs** (#5745, #5742, #5738, #5747) with
`RuntimeError: can't start new thread` and `MemoryError` (run `30136964516`). When one shard fails on
diffs with nothing in common, the shard's environment is the defect.

CI installed the full lockfile and then force-reinstalled `torch==2.13.0` + `torchvision==0.28.0`
CPU wheels **on all four shards** — roughly 2.5 GB per shard — on a standard GitHub-hosted runner already
running `pytest-xdist` with `-n auto`. Nothing the suite loads needs any of it: a repo-wide search
for `import torch`, `from torch`, `sentence_transformers`, `SentenceTransformer` and `open_clip`
returns **zero hits under `scripts/` or `tests/`**. 

> **Correction (2026-07-25):** earlier revisions of this autopsy, and the commit messages of
> #5749, described the runner as "2 vCPU / ~7 GB". That figure was **wrong** — GitHub's standard
> hosted runners for **public** repositories are documented at **4 vCPU / 16 GB with unlimited free
> minutes**, which an independent capacity review surfaced. The measured failures
> (`MemoryError`, `RuntimeError: can't start new thread`) and the fix are unaffected: removing the
> unused ML stack turned all four shards green (29 checks pass, 0 fail). But the *stated cause*
> carried a wrong number, so the lesson is narrower than first written — four xdist workers each
> importing torch can exhaust even a 16 GB runner. Do not cite the old figure; and note the real
> free-tier constraints are **20 concurrent jobs** and RAM *usage*, not minutes and not machine size — every hit is inside `embed-venv/`, the embedding
worker's separate virtualenv, and its vendored `huggingface_hub`. Addressed in PR #5749.

### The gate and the concurrency policy were jointly self-defeating

`CI Gate` fails when a required pytest shard is `cancelled` — correctly, since a cancelled shard
proves nothing ran (`RESULTS: success,skipped,cancelled,…` → *"A required pytest shard failed, was
cancelled, or was unexpectedly skipped"*). But `cancel-in-progress` **produces** cancellations
whenever anything pushes. Under load the policy manufactures exactly the state the gate refuses, so
no PR can hold a green gate long enough to merge. Neither half is wrong alone; together they
deadlock.

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
- **A protection that can be walked around is not a protection.** Three correct layers — paths
  filter, its coverage test, a scoped pre-commit hook — were all skipped by one direct push to
  `main`. Enforcement has to live where it cannot be bypassed by choosing a different command.
- **Never gate on a whole-directory content hash without a merge queue.** It serialises every PR
  touching that directory, and it lets two green PRs combine into a state neither validated. Either
  validate the combined result (merge queue), or compute the hash in CI instead of tracking it.
- **A gate and a cancellation policy must be designed together.** Failing on `cancelled` is right.
  Manufacturing cancellations is also defensible. Doing both deadlocks the queue. Check every
  "correct" rule against the states the *rest* of the system generates.
- **Install only what the tested code imports.** 2.5 GB of ML wheels per shard bought nothing and
  cost the runner its headroom. Heavy optional dependencies belong behind an extra or in the worker's
  own environment, not in the test install.
- **A dispatch that produced no commit must not report success.** Four dispatches this incident
  settled as `done` having pushed nothing: two (`timeouts-B3`, `timeouts-B6`) left finished work
  *uncommitted* in their worktrees, one (`timeouts-B4`) produced nothing after inventorying 56 call
  sites, and one (`ci-replacement-build`) replied with a clarifying question instead of building.
  Three real failures read as three successes. Orchestrators must verify a pushed PR, never a status
  field — and briefs must state that a pushed PR *is* the definition of done and that a worker must
  assume-and-proceed rather than ask.
- **Do not merge ahead of the review verdict, even under pressure.** This document is the example:
  it was armed while green and merged before its cross-family review returned, and that review then
  found the omission and the overstatement corrected above. Green is not reviewed.

## Related

- #5740 — sweep the 325 call sites, add `pytest-timeout`, add a guard test against reintroduction
- PR #5735 — job timeouts, 21→8 jobs, restored paths-filter incident comments
- PR #5746 — regenerated `docs/lesson-schema.yaml`; unblocked the required gate and with it every
  open PR. First successful `main` run against the 0-of-30 baseline (`30136861313`)
- PR #5749 — stop installing torch/torchvision for the pytest suite (the shard OOM cause)
- PR #5739 — the below-the-fold Practice CTA regression that `frontend-e2e` failed to gate; its
  conflict resolution is the worked example of the generated-hash serialisation problem
- #5744 — restore duration-balanced sharding + completeness verification inside `CI Gate`
- #3873 / #4888 / #4936 / #5351 / #5354 — the data-coupling filter-gap family; the paths-filter
  comments deleted-and-restored in #5735 are the institutional memory of those five
- `codex-dispatch-stall.md` (#2985, 2026-06-12) — **prior art for the false-`done` failures above.**
  Then: dispatches completed the work, hung before committing, and showed as `running`. Now: they
  settle as `done` having pushed nothing. Same underlying gap — completion is inferred from a status
  field rather than from a pushed artifact — which is why the fix belongs in the harness, not in
  another round of orchestrator vigilance
