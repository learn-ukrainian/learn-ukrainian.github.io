"""Deterministic OOM chunk splitting (#5230 PR1)."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from scripts.lexicon.runner.contracts import ChunkSpec, ChunkState, ErrorCode, OomSplitChildren


def child_chunk_id(parent_chunk_id: str, split_epoch: int, lemma_range: Sequence[str]) -> str:
    """``child_id = SHA256(parent_chunk_id, split_epoch, ordered_lemma_range)``."""
    payload = "\0".join([parent_chunk_id, str(split_epoch), *lemma_range])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def split_on_oom(
    parent: ChunkSpec,
    *,
    split_epoch: int | None = None,
) -> OomSplitChildren | tuple[ChunkSpec, str]:
    """Split a multi-lemma leaf deterministically, or mark single-lemma ``failed_oom``.

    Returns either :class:`OomSplitChildren` (parent → superseded) or
    ``(failed_chunk, error_code)`` when the leaf has exactly one lemma.
    """
    lemmas = list(parent.lemma_ids)
    if len(lemmas) == 0:
        raise ValueError("cannot split empty chunk")
    if len(lemmas) == 1:
        failed = ChunkSpec(
            chunk_id=parent.chunk_id,
            lemma_ids=lemmas,
            parent_chunk_id=parent.parent_chunk_id,
            split_epoch=parent.split_epoch,
            state=ChunkState.FAILED_TERMINAL,
        )
        return failed, ErrorCode.FAILED_OOM.value

    epoch = parent.split_epoch + 1 if split_epoch is None else split_epoch
    mid = len(lemmas) // 2
    left_ids = lemmas[:mid]
    right_ids = lemmas[mid:]
    left = ChunkSpec(
        chunk_id=child_chunk_id(parent.chunk_id, epoch, left_ids),
        lemma_ids=left_ids,
        parent_chunk_id=parent.chunk_id,
        split_epoch=epoch,
        state=ChunkState.PENDING,
    )
    right = ChunkSpec(
        chunk_id=child_chunk_id(parent.chunk_id, epoch, right_ids),
        lemma_ids=right_ids,
        parent_chunk_id=parent.chunk_id,
        split_epoch=epoch,
        state=ChunkState.PENDING,
    )
    return OomSplitChildren(
        parent_chunk_id=parent.chunk_id,
        left=left,
        right=right,
        split_epoch=epoch,
    )


def mark_parent_superseded(parent: ChunkSpec) -> ChunkSpec:
    return ChunkSpec(
        chunk_id=parent.chunk_id,
        lemma_ids=list(parent.lemma_ids),
        parent_chunk_id=parent.parent_chunk_id,
        split_epoch=parent.split_epoch,
        state=ChunkState.SUPERSEDED,
    )
