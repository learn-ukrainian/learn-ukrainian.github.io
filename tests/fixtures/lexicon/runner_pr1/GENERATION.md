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

`SHA256(baseline_enriched.json) = 11ae5cdf31a71b25eb206bbc5d67038a6def8f8a14a370e829dc05f507647ed2`

- CEFR estimate keys: 450
- Synonym headwords with edges: 0
- Antonym headwords with edges: 0
