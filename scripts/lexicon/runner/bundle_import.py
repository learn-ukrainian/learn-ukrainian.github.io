"""Phase 6 — bundle import (#5230 PR3).

Verify the outer bundle hash and every item hash before state changes.
Import is atomic per lemma; re-import of matching hashes is a no-op; stale
packet generations are rejected cleanly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from scripts.lexicon.runner.ledger import CasResult, CasStatus, Ledger
from scripts.lexicon.runner.transport import HashMismatchError, LoadedBundle, read_bundle


@dataclass
class BundleImportResult:
    bundle_id: str
    packet_generation: int
    committed: list[str] = field(default_factory=list)
    skipped_noop: list[str] = field(default_factory=list)
    rejected: list[tuple[str, str]] = field(default_factory=list)  # (lemma_id, detail)
    status: CasStatus = CasStatus.OK
    detail: str = ""


def import_bundle(
    ledger: Ledger,
    bundle_path: Path,
    *,
    owner: str,
    expected_fingerprint: str | None = None,
    expected_bundle_id: str | None = None,
    claim_units: bool = True,
    now: float | None = None,
    crash_after_items: int | None = None,
) -> BundleImportResult:
    """Import a verified bundle. Per-lemma transactions; crash-safe at item k.

    ``crash_after_items`` is a test hook: after successfully committing that many
    new items, raise ``RuntimeError("injected crash: import_killed_at_k")``.
    """
    try:
        loaded: LoadedBundle = read_bundle(bundle_path, expected_id=expected_bundle_id)
    except HashMismatchError as exc:
        return BundleImportResult(
            bundle_id=expected_bundle_id or Path(bundle_path).name,
            packet_generation=-1,
            status=CasStatus.INVALID_STATE,
            detail=f"hash verification failed: {exc}",
        )

    manifest = loaded.manifest
    run_id = str(manifest["run_id"])
    packet_generation = int(manifest["packet_generation"])
    fingerprint = str(manifest["fingerprint"])
    if expected_fingerprint is not None and fingerprint != expected_fingerprint:
        return BundleImportResult(
            bundle_id=loaded.artifact_id,
            packet_generation=packet_generation,
            status=CasStatus.FINGERPRINT_MISMATCH_REFUSED,
            detail="fingerprint_mismatch_refused",
        )

    # Reject whole bundle early if the packet generation was abandoned.
    if not ledger.packet_generation_active(run_id, packet_generation):
        return BundleImportResult(
            bundle_id=loaded.artifact_id,
            packet_generation=packet_generation,
            status=CasStatus.INVALID_STATE,
            detail="stale_packet_generation",
        )

    result = BundleImportResult(
        bundle_id=loaded.artifact_id,
        packet_generation=packet_generation,
    )
    new_commits = 0
    for item in loaded.items:
        lemma_id = str(item["lemma_id"])
        result_hash = str(item["result_hash"])
        request_key = str(item["request_key"])
        lease_generation = 0

        if claim_units:
            # Ensure unit exists then claim for fenced import.
            ledger.register_work_unit(
                run_id,
                lemma_id,
                unit_kind="lemma",
                phase="network_import",
                now=now,
            )
            claim = ledger.claim_unit(
                run_id,
                lemma_id,
                owner,
                phase="network_import",
                now=now,
            )
            if not claim.ok:
                # Already done with matching import is handled inside commit_import;
                # if claim fails because unit is already done, try commit as no-op path.
                unit = ledger.get_work_unit(run_id, lemma_id, phase="network_import")
                if unit is not None and str(unit.get("state")) == "done":
                    cas = ledger.commit_import(
                        run_id,
                        lemma_id,
                        owner,
                        int(unit.get("lease_generation") or 0),
                        packet_generation=packet_generation,
                        result_hash=result_hash,
                        expected_fingerprint=fingerprint,
                        expected_request_key=request_key,
                        phase="network_import",
                        now=now,
                    )
                    if cas.ok:
                        result.skipped_noop.append(lemma_id)
                        continue
                result.rejected.append((lemma_id, claim.detail or claim.status.value))
                continue
            lease_generation = int(claim.lease_generation or 0)
        else:
            unit = ledger.get_work_unit(run_id, lemma_id, phase="network_import")
            if unit is not None:
                lease_generation = int(unit.get("lease_generation") or 0)
                owner = str(unit.get("owner") or owner)

        cas: CasResult = ledger.commit_import(
            run_id,
            lemma_id,
            owner,
            lease_generation,
            packet_generation=packet_generation,
            result_hash=result_hash,
            expected_fingerprint=fingerprint,
            expected_request_key=request_key,
            phase="network_import",
            now=now,
        )
        if cas.status is CasStatus.OK:
            # Distinguish no-op re-import via events/import row age is unnecessary;
            # if unit was already done before this call, count as noop when not newly claimed.
            if lemma_id in result.committed or lemma_id in result.skipped_noop:
                continue
            # Check whether this was a first commit this pass.
            if claim_units and lease_generation > 0:
                result.committed.append(lemma_id)
                new_commits += 1
            else:
                result.committed.append(lemma_id)
                new_commits += 1
            if crash_after_items is not None and new_commits >= int(crash_after_items):
                raise RuntimeError("injected crash: import_killed_at_k")
        else:
            result.rejected.append((lemma_id, cas.detail or cas.status.value))

    if result.rejected and not result.committed and not result.skipped_noop:
        result.status = CasStatus.INVALID_STATE
        result.detail = "all items rejected"
    return result
