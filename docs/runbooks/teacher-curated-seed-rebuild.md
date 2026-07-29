# Teacher Curated Seed Rebuild and Dual-Write

Issue #6022 rebuilds the teacher Practice seed after its ignored local
dual-write was lost. The original curated document table is the selection
authority. Historical source-inventory records, review decisions, and cloze
cards are evidence only: none may be used to infer missing seed lemmas.

## Package contract

The tracked generator is `scripts/atlas/rebuild_teacher_curated_seed.py`. It
creates the ignored local package root requested for the recovery:
`.claude/atlas-epic/plans/curated-seed/`.

The package has three JSONL surfaces, all empty while the original table is
missing:

| File | Required fields when populated | Current state |
| --- | --- | --- |
| `curated-seed.jsonl` | `seedRow`, `lemma`, `gloss`, `sentenceStatus`, `provenance`, `rights`, `admission` | Quarantined |
| `rights-ledger.jsonl` | `seedRow`, `sentenceStatus`, `rightsStatus`, `locator` | Quarantined |
| `practice-admission.jsonl` | `seedRow`, `practice`, `mode`, `reason` | Quarantined |

`source-recon.json` records safe aggregate counts. `package-manifest.json`
binds the schema and admission rule, and `receipt.json` records SHA-256 for
each package file and the Drive mirror destination. The generator refuses to
run without `--drive-root`, refuses to reuse an existing destination unless
`--replace-existing` is explicit, and verifies the copied checksums. A sole
local package is intentionally a failure.

## Run the recovery scaffold

Set the two machine-local paths before running the command. The first is the
synced Drive curriculum root to inventory; the second is a new, empty durable
Drive destination. The destination below is a per-recovery directory, so it
does not overwrite the prior incident backup.

```bash
DRIVE_CURRICULUM_ROOT="/absolute/path/to/My Drive/Projects/learn-ukrainian-data/private_curriculum"
DRIVE_RECOVERY_ROOT="/absolute/path/to/My Drive/Projects/learn-ukrainian-incident-recovery/2026-07-30/atlas-epic-dual-write/teacher-curated-seed"

.venv/bin/python -m scripts.atlas.rebuild_teacher_curated_seed \
  --package-root .claude/atlas-epic/plans/curated-seed \
  --drive-root "$DRIVE_RECOVERY_ROOT" \
  --drive-source-root "$DRIVE_CURRICULUM_ROOT"
```

The command creates both copies and prints the receipt JSON. Preserve that
exact output in the #6022 issue comment and in the handoff. Do not commit the
ignored package or its recovery receipt.

## Admission and rights gate

Track T connects to Practice only after every restored row has both a rights
ledger record and an explicit admission record. The existing admission helper
is `scripts/lexicon/curated_seed_atlas_admission.py`; it requires a real Atlas
route, an existing CEFR enrichment value, and an attested example plus
provenance for every cloze-eligible row. Rows without an approved sentence
rights status remain recognition-only or quarantined; weak/no-hit rows do not
become cloze cards.

Local smoke after a reviewed package exists:

```bash
CURATED_SEED_INPUT=.claude/atlas-epic/plans/curated-seed/curated-seed.jsonl \
  make practice-admit-curated-seed
```

The Make target runs the existing admission helper, candidate promotion,
enrichment, `generate_practice_deck.py`, API hydration, and Atlas runtime
export. Its learner-facing output is the per-level
`site/public/api/lexicon/practice-index.<level>.json` and
`practice-lexemes.<level>.json` path. The recovery scaffold intentionally
cannot pass this admission smoke: its zero rows are proof that the lost
selection has not been fabricated. Once the authoritative table is restored,
review its row count against the expected 1,018 rows before any Atlas or
Practice write.
