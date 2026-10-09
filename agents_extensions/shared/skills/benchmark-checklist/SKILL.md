---
name: benchmark-checklist
description: Check performance claims against a comparable baseline and reproducible measurements. Use for /benchmark-checklist, measured speedups, regressions or benchmark methodology review.
---

# Benchmark checklist

Vet a performance claim with evidence. Preserve worker ownership: reviewers
remain read-only and send harness or implementation defects to the authoring
worker. Execute only measurements permitted by the task and seat; this skill
does not authorize production load, paid runs or unrelated tuning.

- **Claim and baseline:** define the acceptance criterion, metric, unit, workload
  denominator and threshold before running. Identify baseline and candidate
  revisions, dependencies, input fingerprint and measurement script. Without a
  comparable baseline, report the comparison as inconclusive.
- **Comparable conditions:** keep hardware class, runtime, build mode, input,
  concurrency, cache state and equivalent tuning comparable. Record relevant
  differences using sanitized metadata. Do not pick an implementation winner
  when one side is untuned; distinguish configuration comparisons explicitly.
- **Reproducible method:** provide exact commands, seed where relevant, setup,
  warmup, repetitions and aggregation. Repeat both sides and interleave their
  order to expose drift. Retain individual samples in an allowed evidence
  location and report median, spread and run count. A single exploratory run
  cannot establish a speedup or regression.
- **Correctness and work:** verify outputs against acceptance criteria, count
  failures, timeouts and retries, and demonstrate that the intended work
  completed inside the timed region. Fast failures, unused lazy results and
  no-ops are not improvements.
- **Limiter and relevance:** identify the limiting resource with separate
  diagnostic runs; exclude profiler overhead from reported measurements. Check
  physical and workload bounds. Measure the user-visible end-to-end path before
  generalizing a microbenchmark, and report its share of the whole.
- **Verdict:** report faster, slower, no measurable difference or inconclusive
  with baseline and candidate values, uncertainty and reproduction evidence.
  If variation masks the effect or correctness, comparability or limiter
  evidence is missing, name the gap rather than selecting a winner.

**Prove it works** means observable behaviour against acceptance criteria with
test evidence, alongside timing results. Passing a timing threshold alone is
insufficient. Name unverified criteria and residual owners; send material
measurement defects or scope changes to the accountable driver. Benchmark
evidence does not replace independent exact-head cross-family review or
current-head CI under `agents_extensions/shared/rules/workflow.md`.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
