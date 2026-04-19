# Wiki Rebuild Plan — Phased Build with `--dim-review` Shadow Canary

> **Status:** Active plan as of 2026-04-18. Applies to the net-new wiki rebuild on top of Phase 2 dimensional-review system (commit `15db4323a` + follow-ups).
> **Related:** [`docs/design/dimensional-review.md`](design/dimensional-review.md), [`docs/session-state/current.md`](session-state/current.md).

## Prerequisites

All shipped and verified:

- ✅ Phase 2 dim-review orchestrator (`scripts/wiki/review.py`)
- ✅ Deterministic fix-merger with AMBIGUOUS/MISSING/SPAN_OVERLAP/DIFFERENT_REPLACE conflict detection (`scripts/wiki/review_merger.py`)
- ✅ Four dim reviewer prompts (`scripts/wiki/prompts/review_*.md`) — linguistic review pass applied
- ✅ Code gates for citation-registry + `## Джерела` section (`scripts/wiki/quality_gate.py`, #1326)
- ✅ Sibling-YAML source migration (#1323)
- ✅ External corpus re-chunk + MCP expose + per-track ranking (`scripts/wiki/migrate_external_chunks.py`, #1324)
- ✅ Fetch-sources extensions: channel registry + rate limit + resume (#1151)
- 🟡 Diasporiana PDF ingest — Doroshenko «Нарис історії України» (#1188 in flight; blocks HIST/ISTORIO optimality, not startability)

Corpus inventory already in `data/sources.db`:

| Source | Records |
|---|---|
| `ulp_youtube` | 1,732 |
| `imtgsh` | 1,597 |
| `realna_istoria` | 1,401 |
| `komik_istoryk` | 852 |
| `istoria_movy` | 505 |
| `ulp_blogs` | 164 |
| `other_blogs` | 225 |

## Phased rebuild

### Phase 0 · Smoke test (5 min, 1 article)

**Purpose:** prove the full stack (compile → sibling-YAML → code gates → 4-dim review → merge → report) works end-to-end before scaling.

```bash
.venv/bin/python scripts/wiki/compile.py --track a1 --slug sounds-letters-and-hello --dim-review
```

**Expected artifacts:**

```
wiki/pedagogy/a1/sounds-letters-and-hello.md
wiki/pedagogy/a1/sounds-letters-and-hello.sources.yaml
wiki/.reviews/pedagogy/a1/sounds-letters-and-hello.json
```

The review report MUST contain: 4 per-dim entries (source_grounding, factual_accuracy, ukrainian_perspective, register), each with a score, verdict, findings list, fixes list. If any dim shows `verdict: ERROR` or the report is missing, STOP — we diagnose before Phase 1.

### Phase 1 · A1 full track (~4-5 hrs, 55 articles)

**Purpose:** prove at scale on the simplest domain (pedagogical briefs for beginner learners).

```bash
.venv/bin/python scripts/wiki/compile.py --track a1 --all --dim-review
```

**Why A1 first:** simplest prompts (`compile_pedagogy_brief.md`), fastest articles, most forgiving corpus alignment. Builds confidence in the pipeline before tackling harder tracks.

**Halt criteria:** if `grep -rl '"final_verdict": "ERROR"' wiki/.reviews/pedagogy/a1/` shows >10% of compiled articles → stop, diagnose, fix before continuing.

### Phase 2 · A2 → B1 → B2 sequential (~12-15 hrs, 256 articles)

```bash
.venv/bin/python scripts/wiki/compile.py --track a2 --all --dim-review
.venv/bin/python scripts/wiki/compile.py --track b1 --all --dim-review
.venv/bin/python scripts/wiki/compile.py --track b2 --all --dim-review
```

Grammar briefs (`compile_grammar_brief.md`) — shared prompt template across a2/b1/b2. Corpus: textbooks + ULP blogs + ULP YouTube.

### Phase 3 · C1 → C2 (~15-20 hrs, 242 articles)

```bash
.venv/bin/python scripts/wiki/compile.py --track c1 --all --dim-review
.venv/bin/python scripts/wiki/compile.py --track c2 --all --dim-review
```

Academic briefs (`compile_academic.md`) — historically the weakest tier (#1161 evidence). Phase 2 dim-review catches the per-dim failure patterns for the first time. Expect `register` + `factual_accuracy` to flag more here. **This is signal, not failure** — shadow mode is exactly for collecting it.

### Phase 4 · Seminars, history-rich first (~20+ hrs, 456 articles)

**If #1188 Diasporiana finished** — HIST/ISTORIO get Doroshenko's 600 pages in their corpus. Otherwise start with BIO.

```bash
.venv/bin/python scripts/wiki/compile.py --track hist --all --dim-review     # 140 — Realna Istoria + Doroshenko
.venv/bin/python scripts/wiki/compile.py --track bio --all --dim-review      # 180 — Realna Istoria + Wikipedia
.venv/bin/python scripts/wiki/compile.py --track istorio --all --dim-review  # 136 — Istoria-Movy + Doroshenko
```

### Phase 5 · LIT seminars (~30+ hrs, 435 articles across 9 sub-tracks)

```bash
for t in lit lit-essay lit-war lit-hist-fic lit-youth lit-fantastika lit-humor lit-drama; do
  .venv/bin/python scripts/wiki/compile.py --track $t --all --dim-review
done
```

Literary corpus (`data/sources.db::literary_content`) carries most of the source material. Expect `ukrainian_perspective` dim to be most active here (decolonization framing matters most in lit criticism).

### Phase 6 · OES + RUTH (~10 hrs, 217 articles)

```bash
.venv/bin/python scripts/wiki/compile.py --track oes --all --dim-review
.venv/bin/python scripts/wiki/compile.py --track ruth --all --dim-review
```

Thinnest corpus (specialized linguistics — history of Ukrainian language, Ruthenian). Lowest priority, last.

## Incremental audit protocol (Claude watches Monitor)

While user runs each phase, Claude watches the wiki build log in real time via the `Monitor` tool:

```python
Monitor(
    command="tail -f wiki/.state/build.log.jsonl | grep --line-buffered '\"event\": *\"dim_review\"'",
    description="Wiki dim-review event stream",
    persistent=True,
    timeout_ms=3600000,
)
```

### Per-article sanity checks Claude applies as each event fires

| Signal | Action |
|---|---|
| All 4 dims `verdict: PASS` or `REVISE` with score ≥ 7 | 👍 silent, let it run |
| Any dim `verdict: ERROR` (reviewer crashed / invalid JSON) | ⚠️ flag immediately — orchestrator or prompt bug |
| Same dim failing on 3+ consecutive articles | ⚠️ pause-worthy — systemic prompt issue |
| `AMBIGUOUS` conflicts dominating the merge report | ⚠️ prompts aren't teaching unique-find discipline |
| `final_verdict: ERROR` (all 4 dims errored) | 🛑 stop the phase — something structural is broken |
| Dim scores bunching at 10.0 across the board | ⚠️ sycophancy — reviewer isn't doing real work |
| Dim scores bunching at 6.0 across the board | ⚠️ hostile calibration — threshold will be wrong |

Claude reports back after articles 1, 3, 10, 25, 50 (roughly log-spaced) with a summary.

## Rules of engagement

1. **`--dim-review` never blocks the compile pipeline.** Shadow mode by design. Even if every article "fails" dim review, the `.md` + `.sources.yaml` still land. Reports accumulate in `wiki/.reviews/` for later calibration.

2. **Resume-safe.** `compile.py` skips already-compiled articles unless `--force`. Kill and restart any phase anytime — nothing corrupts.

3. **Pause between phases.** After each phase, review the pattern. Don't chain all 7 phases into a single command — the handoffs are where calibration happens.

4. **Do not flip `--hard-gate` before benchmark.** The orchestrator emits a prominent warning; heed it. Thresholds are `UNCALIBRATED_THRESHOLDS = 8` across all dims (placeholder). Real thresholds come from the Phase 3 benchmark run (see `docs/design/dimensional-review.md §7b`).

5. **Kill policy.** `Ctrl-C` during a track run is safe — compile writes incrementally, resume picks up where it stopped. `kill -9` on a Gemini CLI subprocess mid-compile may leave a partial `.md` without a sibling YAML; `scripts/wiki/state.py::is_compiled` self-heals such stale rows on next run.

## Post-rebuild: benchmark authoring + threshold calibration

After all phases complete:

1. **Author 5 seeded benchmark cases** (Claude-owned, 2-3 hrs) — pick 5 rebuilt articles spanning tracks. For each, hand-plant 2-3 defects (light) and 8-10 defects (heavy) per `scripts/wiki/benchmark_seed.py` format. Ground truth YAML generated automatically.

2. **Run the benchmark** (user-triggered, 1-2 nights) — 5 × 3 × 3 × 4 × 3 ≈ 540 calls:

   ```bash
   .venv/bin/python scripts/wiki/benchmark.py \
       --corpus benchmarks/wiki \
       --agents claude,gemini,codex \
       --reruns 3 \
       --out benchmarks/wiki/.results/$(date +%Y-%m-%d).json
   ```

3. **Derive real thresholds** (Claude-owned, 2 hrs) — replace `derive_thresholds()` stub with real score-distribution analysis. Per-dim threshold at clean-vs-defective separation point. Commit with `thresholds_calibrated: True`.

4. **Optional: Tetiana spot-check** — hand 2-3 real articles to teacher Tetiana for native-speaker annotation; cross-validate reviewer findings.

5. **Staged hard-gate promotion** — promote in order:
   1. Code gates (already deterministic)
   2. `source_grounding` (most tractable, clearest ground truth)
   3. `factual_accuracy` (MCP-backed, objective)
   4. `register` (MCP-backed)
   5. `ukrainian_perspective` (most subjective — last, possibly lower threshold)

## Estimated total time

| Phase | Articles | Hrs (at ~5 min/article) |
|---|---:|---:|
| 0 Smoke | 1 | 0.1 |
| 1 A1 | 55 | 4.5 |
| 2 A2→B2 | 256 | 21 |
| 3 C1→C2 | 242 | 20 |
| 4 HIST/BIO/ISTORIO | 456 | 38 |
| 5 LIT + sublits | 435 | 36 |
| 6 OES/RUTH | 217 | 18 |
| **Total** | **1,662** | **~138 hrs compile time** |

Wall-clock with 4-dim parallel review and pauses between phases: **2-3 weeks of intermittent runs**, not continuous.

Benchmark + calibration adds another 3-5 days on top.

## Quick reference — all commands

```bash
# Phase 0 smoke
.venv/bin/python scripts/wiki/compile.py --track a1 --slug sounds-letters-and-hello --dim-review

# Phase 1
.venv/bin/python scripts/wiki/compile.py --track a1 --all --dim-review

# Phase 2
.venv/bin/python scripts/wiki/compile.py --track a2 --all --dim-review
.venv/bin/python scripts/wiki/compile.py --track b1 --all --dim-review
.venv/bin/python scripts/wiki/compile.py --track b2 --all --dim-review

# Phase 3
.venv/bin/python scripts/wiki/compile.py --track c1 --all --dim-review
.venv/bin/python scripts/wiki/compile.py --track c2 --all --dim-review

# Phase 4 (wait for #1188 ideally)
.venv/bin/python scripts/wiki/compile.py --track hist --all --dim-review
.venv/bin/python scripts/wiki/compile.py --track bio --all --dim-review
.venv/bin/python scripts/wiki/compile.py --track istorio --all --dim-review

# Phase 5
for t in lit lit-essay lit-war lit-hist-fic lit-youth lit-fantastika lit-humor lit-drama; do
  .venv/bin/python scripts/wiki/compile.py --track $t --all --dim-review
done

# Phase 6
.venv/bin/python scripts/wiki/compile.py --track oes --all --dim-review
.venv/bin/python scripts/wiki/compile.py --track ruth --all --dim-review

# Post-rebuild benchmark
.venv/bin/python scripts/wiki/benchmark.py --corpus benchmarks/wiki --agents claude,gemini,codex --reruns 3 --out benchmarks/wiki/.results/$(date +%Y-%m-%d).json
```
