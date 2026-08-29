# Cycle007 storage custody (compact / reclaim prep)

Status: reversible preparation for issue `#7434` under epic `#7423`.
Cycle007 remains evaluation-only. Labeling remains OFF. This page is text-free:
counts, hashes, booleans, filesystem totals, and safe failure codes only.

Controlling outcome SHA-256:
`890498103f96a7b8f27fd52bc14418d8752e5b73a72ed8774dd0f52eb3160a47`.

## Scope

Own the reversible storage lane end-to-end:

1. Reconcile public predecessor handoff counts with private binding state without
   disclosing private topology.
2. Freeze a text-free identity and allocated-byte inventory (`st_blocks * 512`)
   when private packages are bound.
3. Measure real capacity with `statvfs` (`f_bavail * f_frsize`) and enforce a
   10 GiB floor on the admitted write destination.
4. Publish peak compact+backup+hash/index forecast before writes. Never create a
   second expanded tree; never copy expanded trees to the workstation.
5. Decide `RETAIN_MINIMAL_EVALUATION_ASSET` versus `RETIRE_CYCLE007` adversarially.
6. Build the compact representation (content pack or non-content lineage pack)
   with exact identity proof and recoverable backup/restore proof.
7. Emit an exact deletion-target list and reclaimed-byte forecast.
8. Stop at the operator authorization gate. Issue `#7434` is not deletion
   authorization.

## Implementation

- Module: `scripts/projects/open_model_data/phase3_cycle007_storage_custody.py`
- Tests: `tests/test_phase3_cycle007_storage_custody.py`
- Public summary schema:
  `data/projects/open_model_data/contracts/phase3_cycle007_storage_public_summary_v1.schema.json`
- Public summary receipt:
  `data/projects/open_model_data/reference/phase3_cycle007_storage_public_summary_v1.json`

Real mode binds packages only through mode-`0600` config
(`PHASE3_CYCLE007_STORAGE_CONFIG`) or absolute env vars. Argv paths are refused
outside `--fixture` mode (`path_disclosure_refused`).

## Retention decision (adversarial)

`RETAIN_MINIMAL_EVALUATION_ASSET` is valid only when text-free
source/rights/adjudication metadata proves all of:

1. a concrete source-qualified held-out evaluation function
2. required fields and identities
3. a named consumer
4. that identity-lineage exclusion alone is insufficient (always true)
5. text-free source/rights/adjudication metadata presence
6. otherwise replacement firewall owner is `#7427`

Identity-lineage exclusion alone supports only minimal non-content deny hashes
and forces `RETIRE_CYCLE007`, binding `#7427` as owner of the replacement
held-out denominator/firewall.

Chosen outcome: **`RETIRE_CYCLE007`**.

Rationale code: `identity_lineage_exclusion_only_retire`.

Pack kind under retirement: `non_content_lineage_hashes` (no content bodies).

## Acceptance mapping

| Criterion | State |
| --- | --- |
| STOR-INVENTORY | Frozen on bound private package when lane completes |
| STOR-ROUNDTRIP | Streaming identity proof; no second expanded tree |
| STOR-BACKUP | Compact/lineage pack backup with byte-identity restore proof |
| STOR-AUTH | Exact deletion targets + reclaim forecast; gate open |
| STOR-DELETE | Not authorized; no originals deleted |

## Residual authorization request

1. Review deletion-auth receipt (targets + reclaim forecast).
2. Provide explicit operator authorization before any deletion, truncation,
   unlink, overwrite, or reclamation.
3. `#7427` owns the replacement held-out denominator/firewall under
   `RETIRE_CYCLE007`.
