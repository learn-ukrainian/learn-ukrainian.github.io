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
2. Freeze a text-free identity and allocated-byte inventory when private
   packages are bound.  Allocation is charged once per `(st_dev, st_ino)`;
   overlapping role roots retain all aliases but do not double-count blocks.
   The inventory records path-sum versus unique-inode totals and selected-link
   closure (`st_nlink`) separately.
3. Measure real capacity with `statvfs` (`f_bavail * f_frsize`) and enforce a
   10 GiB floor independently for compact and backup destinations when they are
   on separate filesystems.  A same-filesystem backup is charged together.
4. Publish a no-write forecast before writes.  For bound lanes it streams every
   unique content hash through the pinned zstd-3 executable and the exact same
   flags used by the writer, while retaining a full-size upper bound and a
   manifest allowance.  It charges each physical content blob once and never
   creates a second expanded tree or copies expanded trees to the workstation.
5. Keep retention unresolved until source-qualified held-out evaluation proof
   and `#7427` firewall reconciliation settle the disposition.  Missing proof
   is not evidence for `RETIRE_CYCLE007`.
6. Build the compact representation (content pack or non-content lineage pack)
   with exact identity proof and recoverable backup/restore proof.  While
   retention is unresolved, always build the lossless content pack so either
   later outcome remains possible; any deletion-auth request may target only
   the now-redundant expanded originals, never the compact custody copies.
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

Real mode binds packages, an optional independent `backup_root`, and the
absolute zstd executable only through mode-`0600` config
(`PHASE3_CYCLE007_STORAGE_CONFIG`) or absolute env vars. Receipts record only
safe zstd version/settings/executable hash; they never record its path or
argv. The operator-approved failure-domain token is accepted only from that
private mode-`0600` config and is stored only as a domain-separated hash. Argv
paths are refused outside `--fixture` mode
(`path_disclosure_refused`). A previous lane directory is never removed or
overwritten: reruns fail closed with `existing_lane_state`.

## Retention decision (adversarial)

`RETAIN_MINIMAL_EVALUATION_ASSET` is valid only when text-free
source/rights/adjudication metadata proves all of:

1. a concrete source-qualified held-out evaluation function
2. required fields and identities
3. a named consumer
4. that identity-lineage exclusion alone is insufficient (always true)
5. text-free source/rights/adjudication metadata presence
6. otherwise replacement firewall owner is `#7427`

Until that proof is present, the decision is
**`RETENTION_UNRESOLVED`** (`retention_outcome: null`).  The lane may still
complete the reversible universal content pack, independent backup, and
streaming restore proof. Those proofs permit an exact, retention-neutral
authorization request for removal of the expanded originals because every
selected content body and logical alias remains recoverable from the compact
pack. The request never authorizes deletion itself, and the compact pack plus
its independent backup remain protected while retention is unresolved. A
separately reconciled source-qualified decision may later select
`RETAIN_MINIMAL_EVALUATION_ASSET` or `RETIRE_CYCLE007`; the storage lane does
not infer retirement from an evaluation gap.

## Acceptance mapping

| Criterion | State |
| --- | --- |
| STOR-INVENTORY | Frozen on bound private package; unique inode allocation and all role aliases recorded |
| STOR-ROUNDTRIP | Streaming identity proof; no second expanded tree |
| STOR-BACKUP | Independent compact backup; every blob stream-decompressed and hashed without an expanded restore tree |
| STOR-AUTH | Exact deletion targets + reclaim forecast after lossless pack/backup proof; unresolved retention permits only retention-neutral expanded-original targets; link sets must be closed |
| STOR-DELETE | Not authorized; no originals deleted |

## Residual authorization request

1. Review the retention-neutral deletion-auth receipt (targets + reclaim
   forecast) after both compact copies and their restore proofs pass and every
   selected inode link set is closed.
2. Provide explicit operator authorization before any deletion, truncation,
   unlink, overwrite, or reclamation.
3. Keep the compact custody pack and independent backup until `#7427`
   separately reconciles the final retention outcome.

## Cross-host production stages

The production path is explicitly staged so the source host never needs a
third local filesystem. `primary_universal_pack_stage` freezes the exact
physical denominator, runs the pinned no-write zstd preflight, requires the
source 10 GiB floor before and after writing, and emits a self-hashed portable
receipt with a universal content pack. The operator transports only that
compact pack and receipt to the workstation.

`workstation_backup_admission_stage` accepts explicit private failure-domain
tokens, rejects equal domains, requires the destination to be absent, and
records a fresh pre-copy 10 GiB floor admission. After compact transport,
`workstation_backup_attestation_stage` requires that admission, rechecks the
post-copy floor, and fully streams every stored blob through decompression and
SHA-256 verification; it creates no expanded restoration tree. Finally,
`finalize_source_deletion_auth_stage` validates the imported attestation,
rescans source inode/link closure, checks the source floor again, and emits a
non-authorizing exact request. Any ENOSPC during a pack write fails promptly
and cleans only that newly created partial staging pack. No stage deletes,
unlinks, or truncates an original.

Allocated block counts are filesystem-local. The admission receipt binds the
source pack's measured allocation as its pre-copy forecast; attestation records
the workstation's actual allocation and its delta separately. It never
requires APFS, ext4, or a network filesystem to report identical `st_blocks`
for identical bytes. The full stored-hash plus stream-decompression proof and
the fresh post-copy 10 GiB floor remain the authoritative backup gates.

The staged surface is intentionally a Python API rather than path-bearing real
mode CLI arguments. The durable invocation/transport order is:

1. Load source `Bindings` from the private mode-`0600` config and call
   `primary_universal_pack_stage`. Keep the resulting primary-stage directory
   intact.
2. Transfer only `pack/`, `inventory.json`, `portable-export.json`, and their
   self-hashed receipts. Never transfer an expanded source tree.
3. On the workstation, call `workstation_backup_admission_stage` before the
   copy, using its separate mode-`0600` domain config. Transport the compact
   pack, then call `workstation_backup_attestation_stage`; it persists the
   independent full-stream proof.
4. Call `issue_finalization_challenge` on the source, transfer that one receipt
   to the workstation, and call `workstation_finalization_response_stage`.
   This re-proves the live backup against the single-use nonce.
5. Return the response and initial backup receipts to the source and call
   `finalize_source_deletion_auth_stage`. It freshly proves the primary pack,
   rescans source content/inodes/links, consumes the nonce response, and writes
   `deletion-auth-request.json` with `deletion_authorized: false`.

Both operator domain labels come from protected local configuration, while an
independent machine/filesystem fingerprint binds each label to the actual
storage root. Unequal labels on the same physical root are rejected.
