"""Phase 4 — request packet export (#5230 PR3).

Exports only unresolved network requests as a content-addressed ``.tar.zst``.
After export, transport is durable ``packet_exported`` (no live lease).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from scripts.lexicon.runner.ledger import CasResult, CasStatus, Ledger
from scripts.lexicon.runner.network_worker import NetworkWorkItem
from scripts.lexicon.runner.transport import ArtifactRef, PacketItem, build_packet


@dataclass(frozen=True, slots=True)
class PacketExportResult:
    artifact: ArtifactRef
    generation: int
    lemma_ids: list[str]
    ledger_status: CasStatus


def export_request_packet(
    ledger: Ledger,
    *,
    run_id: str,
    fingerprint: str,
    items: Sequence[NetworkWorkItem | PacketItem],
    output_dir: Path,
    generation: int | None = None,
    now: float | None = None,
) -> PacketExportResult:
    """Build packet, write content-addressed artifact, record ``packet_exported``."""
    packet_items: list[PacketItem] = []
    for item in items:
        if isinstance(item, PacketItem):
            packet_items.append(item)
        else:
            packet_items.append(item.as_packet_item())
    packet_items = sorted(packet_items, key=lambda p: p.lemma_id)

    gen = (
        int(generation)
        if generation is not None
        else ledger.next_packet_generation(run_id)
    )
    artifact = build_packet(
        run_id=run_id,
        fingerprint=fingerprint,
        generation=gen,
        items=packet_items,
        output_dir=output_dir,
    )
    rec = ledger.record_packet_exported(
        run_id,
        artifact.artifact_id,
        gen,
        content_hash=artifact.artifact_id,
        now=now,
    )
    if not rec.ok:
        return PacketExportResult(
            artifact=artifact,
            generation=gen,
            lemma_ids=[p.lemma_id for p in packet_items],
            ledger_status=rec.status,
        )
    # Register import work units (pending) so later bundle import can CAS-fence.
    for pkt in packet_items:
        ledger.register_work_unit(
            run_id,
            pkt.lemma_id,
            unit_kind="lemma",
            phase="network_import",
            now=now,
        )
        ledger.set_work_unit_packet_generation(
            run_id,
            pkt.lemma_id,
            gen,
            phase="network_import",
            request_key=pkt.request_key,
            now=now,
        )
    return PacketExportResult(
        artifact=artifact,
        generation=gen,
        lemma_ids=[p.lemma_id for p in packet_items],
        ledger_status=CasStatus.OK,
    )
