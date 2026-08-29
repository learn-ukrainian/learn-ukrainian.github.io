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
3. Measure real capacity with `statvfs` (`f_bavail * f_frsize`).
4. Forecast peak temporary space while originals remain untouched.
5. Decide `RETAIN_MINIMAL_EVALUATION_ASSET` versus `RETIRE_CYCLE007` using only
   custody/evaluation necessity and text-free metrics.
6. Build a versioned compact pack (`phase3_cycle007_storage_pack_v1`) with exact
   byte round-trip.
7. Create a recoverable backup and restoration proof.
8. Emit an exact deletion-target list and reclaimed-byte forecast.
9. Stop at the operator authorization gate. Issue `#7434` is not deletion
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

## Retention decision

Chosen outcome: **`RETAIN_MINIMAL_EVALUATION_ASSET`**.

Rationale code: `evaluation_firewall_requires_identity_assets`.

Cycle007 identities remain required for the evaluation / lineage firewall.
Expansion-class objects may be proposed for later deletion only after compact
migration, recoverable backup, restoration proof, and a separate explicit
operator authorization. `RETIRE_CYCLE007` is reserved for the case where
evaluation necessity is explicitly false.

## Acceptance mapping

| Criterion | State on this workstation |
| --- | --- |
| STOR-INVENTORY | Tooling ready; production freeze blocked on `private_binding_unbound` |
| STOR-ROUNDTRIP | Proven on synthetic fixture packages (`fixture_roundtrip_ok=true`) |
| STOR-BACKUP | Proven on synthetic fixture packages (`fixture_backup_restore_ok=true`) |
| STOR-AUTH | Auth-request emitter ready; live targets require private binding |
| STOR-DELETE | Not authorized; no originals deleted |

## Residual authorization request

1. Bind private materialization and/or evidence packages through the approved
   env/config channel on the custody host.
2. Re-run `prepare-lane` to freeze production inventory, peak forecast, compact
   pack, backup, and exact deletion targets.
3. Provide explicit operator authorization before any deletion, truncation,
   unlink, overwrite, or reclamation.
