# Runner PR1 equivalence fixture (hermetic)

## Command

```bash
.venv/bin/python scripts/lexicon/runner/generate_pr1_fixture.py --write-sealed
```

## What the baseline proves

Record-equivalent **CEFR band boundaries** (``_prepare_cefr_estimates`` cohort
quantiles) and **reciprocal relation closure**
(``_*_relations_by_headword``) for a frozen 500-lemma offline slice.

The PR1 sealed phases must reproduce these maps exactly (foundation for #5331).

## Baseline digest

`SHA256(baseline_enriched.json) = 7f6b845760c9aee40f3a69672315ca033b4034be2db6cee35c538d5525706f29`

- CEFR estimate keys: 450
- Synonym headwords with edges: 100
- Antonym headwords with edges: 50
