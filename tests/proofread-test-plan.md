# Proofreading Test Regime

All tracks, from A1 through seminar. Run when capacity is available.

## Track Inventory

| Track | Content Files | Index Total | Immersion | Status |
|-------|--------------|-------------|-----------|--------|
| a1 | 41 | 44 | 0-30% (bilingual) | Ready to test |
| a2 | 65 | 71 | 30-55% (bilingual) | Ready to test |
| b1 | 45 | 94 | 75-100% (1-5 bridge, 6+ immersed) | Ready to test |
| b2 | 34 | 95 | 100% | Ready to test |
| b2-hist | 27 | 140 | 100% Ukrainian | Ready to test |
| c1 | 1 | 108 | 100% | 1 module only |
| c1-hist | 3 | 136 | 100% Ukrainian | 3 modules |
| c1-bio | 4 | 172 | 100% Ukrainian | 4 modules |
| lit | 0 | 217 | 100% Ukrainian | No content yet |
| oes | 0 | 100 | 100% Ukrainian | No content yet |
| ruth | 0 | 100 | 100% Ukrainian | No content yet |

## Phase 1: Sample Test (5 modules per track, dry-run + evaluate)

Pick 5 diverse modules per track. Run dry-run to check issue quality, then evaluate for precision/rewrite quality/safety.

### A1 (bilingual, 0-30% Ukrainian)

```bash
for n in 2 10 17 30 42; do
  .venv/bin/python scripts/proofread.py a1 $n --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-a1-$(printf '%02d' $n).txt
done
```

Modules: 2 (cyrillic-code-ii), 10 (checkpoint-first-contact), 17 (numbers-and-money), 30 (prepositions), 42 (emergencies)

### A2 (bilingual, 30-55% Ukrainian)

```bash
for n in 5 15 25 40 55; do
  .venv/bin/python scripts/proofread.py a2 $n --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-a2-$(printf '%02d' $n).txt
done
```

Modules: 5, 15, 25, 40, 55 (spread across the level)

### B1 (bridge 1-5, immersed 6+)

```bash
# Bridge module (bilingual)
.venv/bin/python scripts/proofread.py b1 3 --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-b1-03.txt

# Immersed modules
for n in 7 15 25 40; do
  .venv/bin/python scripts/proofread.py b1 $n --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-b1-$(printf '%02d' $n).txt
done
```

Modules: 3 (bridge), 7, 15, 25, 40 (immersed)

### B2 (100% Ukrainian)

```bash
for n in 1 10 20 30 34; do
  .venv/bin/python scripts/proofread.py b2 $n --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-b2-$(printf '%02d' $n).txt
done
```

Modules: 1, 10, 20, 30, 34 (spread across available content)

### B2-HIST (seminar, 100% Ukrainian, history track)

```bash
for n in 1 5 10 15 20; do
  .venv/bin/python scripts/proofread.py b2-hist $n --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-b2hist-$(printf '%02d' $n).txt
done
```

Modules: 1 (trypillian), 5, 10, 15, 20

### C1 (1 module available)

```bash
.venv/bin/python scripts/proofread.py c1 1 --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-c1-01.txt
```

### C1-HIST (seminar, 3 modules)

```bash
for n in 1 2 3; do
  .venv/bin/python scripts/proofread.py c1-hist $n --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-c1hist-$(printf '%02d' $n).txt
done
```

### C1-BIO (seminar, 4 modules)

```bash
for n in 1 2 3 4; do
  .venv/bin/python scripts/proofread.py c1-bio $n --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-c1bio-$(printf '%02d' $n).txt
done
```

### LIT (no content yet — test when first module is built)

```bash
# Run after first lit module is built
.venv/bin/python scripts/proofread.py lit 1 --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-lit-01.txt
```

## Phase 2: Full Dry-Run (all modules per track)

After Phase 1 validates the prompt works for each track, run full coverage.

```bash
# Core tracks
.venv/bin/python scripts/proofread.py a1 --all --dry-run 2>&1 | tee tests/proofread-results/full-a1.txt
.venv/bin/python scripts/proofread.py a2 --all --dry-run 2>&1 | tee tests/proofread-results/full-a2.txt
.venv/bin/python scripts/proofread.py b1 --all --dry-run 2>&1 | tee tests/proofread-results/full-b1.txt
.venv/bin/python scripts/proofread.py b2 --all --dry-run 2>&1 | tee tests/proofread-results/full-b2.txt

# Seminar tracks
.venv/bin/python scripts/proofread.py b2-hist --all --dry-run 2>&1 | tee tests/proofread-results/full-b2hist.txt
.venv/bin/python scripts/proofread.py c1-hist --all --dry-run 2>&1 | tee tests/proofread-results/full-c1hist.txt
.venv/bin/python scripts/proofread.py c1-bio --all --dry-run 2>&1 | tee tests/proofread-results/full-c1bio.txt
```

## Phase 3: Full Evaluate (sample per track)

Run `--evaluate` on a subset of Phase 2 results to get quality metrics.

```bash
# 10 modules per large track, all modules for small tracks
.venv/bin/python scripts/proofread.py a1 --range 1-10 --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-a1-batch.txt
.venv/bin/python scripts/proofread.py a2 --range 1-10 --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-a2-batch.txt
.venv/bin/python scripts/proofread.py b1 --range 6-15 --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-b1-batch.txt
.venv/bin/python scripts/proofread.py b2 --range 1-10 --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-b2-batch.txt
.venv/bin/python scripts/proofread.py b2-hist --range 1-5 --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-b2hist-batch.txt
.venv/bin/python scripts/proofread.py c1-hist --all --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-c1hist-batch.txt
.venv/bin/python scripts/proofread.py c1-bio --all --dry-run --evaluate 2>&1 | tee tests/proofread-results/eval-c1bio-batch.txt
```

## Phase 4: Fix Application

After quality metrics are validated (precision >80%, rewrite quality >70%, safety >90%):

```bash
# Apply fixes track by track, re-audit after each
.venv/bin/python scripts/proofread.py a1 --all --fix 2>&1 | tee tests/proofread-results/fix-a1.txt
.venv/bin/python scripts/proofread.py a2 --all --fix 2>&1 | tee tests/proofread-results/fix-a2.txt
# ... etc for each track
```

## Quality Thresholds

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Precision | >80% | Both evaluators agree the issue is real |
| Rewrite quality | >70% | Both evaluators agree the rewrite should be applied |
| Safety | >90% | Both evaluators agree no new errors introduced |
| False positives | <20% | At least one evaluator says not a real issue |

## Expected Issue Distribution by Track Type

| Track Type | Expected Issues/Module | Top Issue Types |
|------------|----------------------|-----------------|
| A1/A2 (bilingual) | 5-15 | RUSSIANISM, LLM_FILLER, WORD_SALAD |
| B1 bridge (1-5) | 5-10 | LLM_FILLER, WORD_SALAD |
| B1 immersed (6+) | 3-8 | LLM_FILLER, LANGUAGE_BLENDER (if English leaks) |
| B2 core | 3-8 | LLM_FILLER, WORD_SALAD |
| B2-HIST seminar | 2-6 | RUSSIANISM, WORD_SALAD, SOURCE_VERIFICATION |
| C1/C1-HIST/C1-BIO | 2-5 | WORD_SALAD, SOURCE_VERIFICATION, HISTORICAL_INTEGRITY |
| LIT | 2-5 | SOURCE_VERIFICATION, WORD_SALAD |

## Notes

- OES and RUTH tracks have no content yet — add to test plan when modules are built
- LIT track needs first module built before testing
- All tests use Gemini 3.1 Pro (default) for proofreading
- Evaluation uses both Gemini Pro + Claude Opus (when Opus capacity is available)
- Results stored in `tests/proofread-results/`
