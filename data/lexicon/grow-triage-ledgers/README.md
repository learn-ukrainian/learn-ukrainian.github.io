# Grow triage ledgers (atlas-intake #4220 arc)

Free-form triage/adjudication ledgers from the Atlas **grow** arc
(`kind: atlas_grow_automerge_triage_ledger`, `kind: atlas_grow_automerge_deferred_adjudication`, …).

These are **NOT** publish-queue decision files. They deliberately do not conform to the
`atlas_source_inventory_review_decisions` schema and therefore MUST NOT live in
`data/lexicon/source-inventory-review-decisions/` — that directory is schema-validated by
`scripts/audit/source_inventory_review_decisions.py` and pinned by
`tests/test_source_inventory_review_decisions.py::test_default_committed_decision_files_validate`
(every committed file there must validate; a non-conforming file turns main red for every
subsequent code PR — see #4888/#4889 → the 2026-07-10 incident).

No script consumes these ledgers yet. If they become machine-read inputs, give them their own
versioned schema + validation test first (the `kind:` field is already present for dispatch).
