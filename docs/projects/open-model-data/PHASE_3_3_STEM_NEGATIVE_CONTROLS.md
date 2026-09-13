# Phase 3.3 STEM Negative Controls (#8007)

Parent epic: #6321. Depends on Phase 3.0 (#8005) on `main`.
Operational plan: `CORPUS_GROUNDED_DECOLONIZATION_DATASET_PLAN.md` §3.1–3.2.

## What this ships

`python -m scripts.projects.open_model_data.v4_mine_stem_controls` mines train-only STEM textbook chunks and yields exactly **1,800** vetted `PRESERVE` SFT controls and **900** anti-hyper-purist `PRESERVE` DPO pairs.

Admission is entity-typed, not subject-tagged:

| Pair | `PRESERVE` | Not `PRESERVE` |
| --- | --- | --- |
| об'єм / обсяг | 3D physical volume (`об'єм піраміди`, `об'єм розчину`) | data, labour, economics (`об'єм даних` → `обсяг`) |
| рахувати | discrete counting | calculation → `обчислити`; opinion → `вважати` |
| відношення | mathematical / physical ratio | interpersonal → `ставлення` / `стосунки` |
| nomenclature | traditional trivial acids (`сірчана кислота`) | true calques (`вуглекислий газ`) |

Colloquial Ukrainian (`розм.`) that passes cleanliness is preserved: informal register is not treated as Russian interference.

## Cleanliness gate

A passage is admitted only after all three pass:

1. VESUM attestation of the target term and content words (`forms` / `forms_all`)
2. Style-guide collision check (static calque phrases + `style_guide` contrast quotes)
3. OCR sanity (length, mojibake, digit runs, broken lineation, Latin/Cyrillic mix)

Held-out Phase 3.0 chunk IDs and author+title held-out books are excluded before extraction.

## How to run

From the repository root, point roots at environment or cwd-relative paths. Do not bake host paths or SSH aliases into commands or receipts.

```bash
python -m scripts.projects.open_model_data.v4_mine_stem_controls \
  --sources-db "$SOURCES_DB" \
  --vesum-db "$VESUM_DB" \
  --output-dir "$STEM_CONTROLS_OUT"

python -m scripts.projects.open_model_data.v4_mine_stem_controls \
  --verify-only \
  --output-dir "$STEM_CONTROLS_OUT"
```

`--receipt-only` writes the public receipt and hash index without local research shards.

## Outputs and leakage rules

| File | Public? | Contents |
| --- | --- | --- |
| `stem_controls_receipt.json` | yes | counts, subject tallies, SHA-256, typing stats |
| `stem_controls_index.jsonl` | yes | passage SHA-256, chunk id, subject, entity type |
| `stem_preserve_sft_controls.jsonl` | no (train-only research partition) | full SFT trajectories |
| `stem_preserve_dpo_pairs.jsonl` | no (train-only research partition) | length-matched DPO pairs |

Public artifacts must not contain textbook passages, private home directories, or SSH host aliases. Schema: `data/projects/open_model_data/contracts/v1_stem_controls_receipt.schema.json`.

## Tests

```bash
python -m pytest tests/projects/open_model_data/test_v4_mine_stem_controls.py
```
