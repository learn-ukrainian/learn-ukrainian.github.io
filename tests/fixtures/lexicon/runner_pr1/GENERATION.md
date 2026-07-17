# Runner PR1 equivalence fixture (hermetic)

## Command

```bash
.venv/bin/python scripts/lexicon/runner/generate_pr1_fixture.py
```

## What the baseline proves

Record-equivalent **CEFR band boundaries** (``_prepare_cefr_estimates`` cohort
quantiles) and **reciprocal relation closure**
(``_*_relations_by_headword``) for a frozen 500-lemma offline slice.

The PR1 sealed phases must reproduce these maps exactly (foundation for #5331).

## Baseline digest

`SHA256(baseline_enriched.json) = 0eda120f90579f5bf3f6eef8d8eebaf1427fb533cd7563e79dd6434a40e320fd`

- CEFR estimate keys: 450
- Synonym headwords with edges: 100
- Antonym headwords with edges: 50
