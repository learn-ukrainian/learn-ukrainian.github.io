# Smoke build — A1/colors — FAILED at review (pipeline bug)

**Date**: 2026-04-23
**Branch**: `claude/claude-smoke-build-colors`
**Worktree**: `.worktrees/claude-smoke-colors`
**Base rebased onto**: `a6a1597b53` (tip of `origin/main` — includes #1421 per-dim reviewer + #1427 ukrainian_wiki embedding ingest fix).

## Verdict

**Smoke FAILED.** Terminal = `budget_exhausted` after 2 attempts. **Do not retry blindly.**

**Where it broke**: attempt 2 (full_rewrite strategy) — the writer produced a module
that violates the plan contract. Sidecar validator raised `RuntimeError` inside
the convergence loop; the exception handler broke out of the loop and emitted a
`budget_exhausted.yaml` terminal.

**Classification**: **pipeline bug**, not a reviewer-strictness issue and not a
content-grounding issue. Reviewer behaviour was correct, dim scores were plausible,
writer output on round 1 had real quality problems. But the ladder's `full_rewrite`
escalation cannot recover when the post-patch sidecar validator rejects the new
content — one validator exception collapses the whole budget.

## Build command and wall-clock

```
.venv/bin/python -u scripts/build/v6_build.py a1 10 \
    --force \
    --writer gemini-tools --reviewer codex-tools \
    2>&1 | tee /tmp/smoke-build-colors.log
```

Exit: non-zero (`module_failed` JSONL event emitted, pipeline aborted at review).
Wall-clock: 2026-04-23T00:02:36Z → 00:31:16Z = **28m 40s**.

## Preconditions — all PASS before running

| # | Precondition | Status |
|---|---|---|
| 1 | `#1421` per-dim reviewer merged | PASS — present on rebased branch |
| 1 | `#1427` ukrainian_wiki ingest→encode fix merged | PASS — present on rebased branch |
| 2 | `search_sources('кольори …', track='a1')` returns ≥ 3 ukrainian_wiki hits with `dense_score > 0` | PASS — 5 hits |
| 3 | 9 per-dim reviewer prompt files at `scripts/build/phases/v6-review/v6-review-{actionable,completeness,decolonization,dialogue,factual,honesty,language,naturalness,plan-adherence}.md` | PASS |

Note on worktree hygiene: this worktree's `data/` is checked out from git but the
git-ignored heavy files (`sources.db`, `sources.db-shm/-wal`, `embeddings/`) do not
live in git, so I symlinked them (plus `.venv`, `starlight/node_modules`,
`embed-venv`) from the main checkout. Matches the pattern in
`start-codex.sh:124`. Pre-existing issue — worth adding a helper script, but not in
scope for this smoke.

## Per-dim reviewer fanout — confirmed working

9 independent dispatches against `codex-tools` (`gpt-5.4`) fired in round 1. Log
evidence (`/tmp/smoke-build-colors.log:274-290`):

```
📋 Dispatch log → dispatch/99-review-naturalness-…json   (110s)
📋 Dispatch log → dispatch/99-review-decolonization-…json (110s)
📋 Dispatch log → dispatch/99-review-dialogue-…json       (125s)
📋 Dispatch log → dispatch/99-review-honesty-…json        (154s)
📋 Dispatch log → dispatch/99-review-factual-…json        (170s)
📋 Dispatch log → dispatch/99-review-plan_adherence-…json (215s)
📋 Dispatch log → dispatch/99-review-completeness-…json   (220s)
📋 Dispatch log → dispatch/99-review-language-…json       (235s)
📋 Dispatch log → dispatch/99-review-actionable-…json     (255s)
```

Matching per-dim YAML outputs landed at
`curriculum/l2-uk-en/a1/review/colors-review-{dim}-r1.yaml` plus an aggregate.

### Round 1 dim scores

| # | Dimension | Score | Verdict |
|---|---|---:|---|
| 1 | Naturalness | **4.8** | REJECT |
| 2 | Decolonization | 8.8 | REVISE |
| 3 | Dialogue | 5.8 | REVISE |
| 4 | Honesty | **4.8** | REVISE |
| 5 | Factual | 7.4 | REVISE |
| 6 | Plan Adherence | 6.8 | REVISE |
| 7 | Completeness | 8.3 | REVISE |
| 8 | Language | 5.8 | REVISE |
| 9 | Actionable | **4.9** | REJECT |

- **MIN gate**: 4.8/10 — FAIL (threshold ≥ 8).
- Weighted avg (info only): 6.4/10.

The low dims reflect real content problems in the gemini round-1 draft:
`INJECT_ACTIVITY` HTML comments were never expanded to actual exercises (→
Naturalness, Actionable), dialogue framing referenced a "poem about the sun"
not in the contract (→ Honesty), and several dialogue turns read as
stage-directed rather than natural (→ Naturalness, Dialogue). This is genuine
writer weakness, not reviewer nitpicking.

## Attempt 2 — where the pipeline actually broke

Convergence loop selected **tier 3 / full_rewrite** (cross-section findings
required a full module regeneration). Writer re-ran write → exercises → activities →
verify → vocab, finishing at 00:31:16Z. Immediately after, the loop invoked
`context.refresh_sidecars("full_rewrite")` (from
`scripts/build/convergence_loop.py:584`), which in turn runs
`_validate_regenerated_sidecars` at `scripts/build/v6_build.py:9659`.

That validator raised:

```
RuntimeError: plan-sidecar validation failed:
  Missing contract vocabulary targets: [
    'чорний (black)',
    'сірий (grey)',
    'колір (color, m)',
    'якого кольору? (what color?)'
  ];
  Activity order mismatch at position 3 (expected type 'quiz', found 'group-sort-hard-soft')
  and position 4 (expected type 'match-up', found 'quiz-blue-vs-lightblue')
  and position 5 (expected type 'group-sort', found 'match-up-appearance')
```

The exception bubbles to the `except Exception as exc:` at
`convergence_loop.py:623-646`, which:

1. records an exception round (`decision_reason: exception`)
2. **`break`s out of the convergence loop** with only 2 attempts recorded
3. drops out into the post-loop "terminal" selector, which writes
   `curriculum/l2-uk-en/a1/orchestration/colors/budget_exhausted.yaml`

Net effect: a writer that produced contract-noncompliant content on its *second*
swing terminates the whole module under the wrong label. The convergent spec
(`docs/architecture/convergent-pipeline-spec.md:34`) allows up to 5 escalations
before `budget_exhausted`; here we got 2 because the validator's contract complaint
was treated as an un-recoverable exception rather than a fresh finding that
the next iteration could address.

## Root cause

**`_validate_regenerated_sidecars` is brittle to writer drift during
`full_rewrite`.** The expected recovery path is:

- Sidecar mismatches (missing contract vocab, activity-order mismatch) should be
  *findings*, not exceptions. They should feed back into the next iteration as
  prioritised findings (probably tier 2 `section_rewrite` or tier 1 `patch` to
  restore the missing vocab / reorder activities).

Today's behaviour is the opposite: any `RuntimeError` in `refresh_sidecars`
collapses the whole budget into `budget_exhausted`, wasting the remaining 3
escalation slots.

Secondary: the terminal name is misleading. This was not a budget cap hit — it
was an unhandled exception. Emitting `budget_exhausted.yaml` here hides the fact
that the real problem is an exception path in the mutation loop.

## Acceptance criteria — status

| AC | Status |
|---|---|
| Build exits with rc=0 | ❌ |
| All phases complete through publish | ❌ (review failed; publish never ran) |
| `module_done` JSONL emitted | ❌ (`module_failed` emitted instead) |
| Per-dim reviewer fans out (9 calls) | ✅ |
| Every dim scores ≥ 8/10 | ❌ (MIN 4.8, 3 dims < 6) |
| After ≤ 2 fix rounds MIN ≥ 8 | ❌ (attempt 2 crashed) |
| `verdict_score = min(per_dim_scores) ≥ 8` + PASS | ❌ |
| Audit gate green (`status/colors.json` PASS) | ❌ (no status file produced) |
| Published MDX at `starlight/src/content/docs/a1/colors.mdx` | ❌ (never written) |
| Dialogue uses ≥ 1 ukrainian_wiki-grounded phrase provably from colors wiki article | Unverifiable — module never published. Research packet does include project wiki (`wiki/pedagogy/a1/colors.md`); `ukrainian_wiki` corpus retrieval is healthy (5 dense hits in precondition 2) but the `--research` phase completed in 0.03s, reusing an earlier cached research packet — so this build never exercised the freshly-indexed `ukrainian_wiki` corpus end-to-end. Re-running with `--reset-memory` or deleting the cached research packet would be needed to prove the wiring. |

## Surprises / warnings in the log

- `VESUM check skipped: VESUM database not found at …/data/vesum.db` — VESUM was
  not symlinked (only `sources.db`, `embeddings/`). Downstream phases continued
  degraded; this does **not** explain the review failure but should be symlinked
  on the next smoke attempt for completeness.
- `verify` phase reported `status: "degraded", ok: false` in 0.042s due to the
  VESUM skip. Review was still allowed to proceed — matches
  "Verification completed with skipped checks — downstream phases may continue"
  policy.
- The re-write pass *kept* the contract violation instead of fixing it. Writer
  prompt (`colors-review-r1.md`, 45 KB) was the full round-1 finding list —
  worth inspecting whether the prompt prioritises fix-quality over
  plan-adherence.

## Recommended next step — for the next session, not this one

1. **Fix the pipeline first.** Don't re-run the smoke until the
   `_validate_regenerated_sidecars` path is converted from raise → finding. A
   minimal patch would catch `RuntimeError` inside
   `convergence_loop.py:584-585` and inject the validator's messages as new
   prioritised findings for the next iteration, preserving budget. File
   pointers:
   - `scripts/build/convergence_loop.py:584-585` — raise site in the
     `full_rewrite` branch (and the symmetric `section_rewrite:579-580`,
     `writer_swap:619-620` branches).
   - `scripts/build/v6_build.py:9659` — where the RuntimeError originates.
2. Once fixed, the colors smoke should retry with at most `--resume`; round-1
   findings are already on disk and cheap to reuse.
3. Do **not** start parallel overnight A1/A2 rebuilds until a single vertical
   smoke reaches `module_done` — that's the whole point of this gate.
4. For diagnosis, the full attempt trail is at
   `curriculum/l2-uk-en/a1/orchestration/colors/budget_exhausted.yaml` (46 KB,
   all 32 findings normalised).

## Artifacts committed to this branch

- `curriculum/l2-uk-en/a1/review/colors-review-{dim}{,-r1}.yaml` — per-dim
  reviewer outputs (9 × 2 files)
- `curriculum/l2-uk-en/a1/review/colors-review-aggregate{,-r1}.yaml`
- `curriculum/l2-uk-en/a1/review/colors-review-r1.md` (prompt fed back to
  writer for attempt 2)
- `curriculum/l2-uk-en/a1/orchestration/colors/state.json` (terminal status)
- `curriculum/l2-uk-en/a1/orchestration/colors/budget_exhausted.yaml`
- `curriculum/l2-uk-en/a1/orchestration/colors/exercise-verification.json`
- `curriculum/l2-uk-en/a1/colors.md` (round-1 content; unpublished)
- `curriculum/l2-uk-en/a1/vocab/colors.yaml` (vocab from re-run)
- This summary
