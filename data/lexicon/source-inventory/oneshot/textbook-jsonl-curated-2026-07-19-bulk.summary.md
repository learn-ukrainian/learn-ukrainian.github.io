# Textbook JSONL curated intake — summary (2026-07-19)

Regenerable bulk inventory for school textbooks (all subjects including STEM).

## Counts

| Metric | Value |
| --- | ---: |
| Text units mined | 48,996 |
| Unique tokens | 369,588 |
| freq ≥ 3 | 157,145 |
| SUM11 attested | 25,112 |
| Inventory rows (VESUM+SUM) | **24,682** |
| Already in Atlas | 7,429 |
| **Newly promoted** | **17,253** |
| Manifest after | **28,433** |

## Regeneration

```bash
.venv/bin/python -m scripts.lexicon.curated_textbook_jsonl_repromote \
  --from-db --min-freq 3 --write-inventory --write-decisions
```

Inventory + decisions YAML are committed for audit trail; raw textbook prose is not.
