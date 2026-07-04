from __future__ import annotations

from scripts.audit import fix_internal_register_leakage as fix


def test_chunk_jargon_swapped_to_phrase() -> None:
    text = "Learn it in small chunks. Treat it as one whole chunk. | Chunk | Meaning |"
    out, n = fix.transform_text(text)
    assert "chunk" not in out.lower()
    assert out == "Learn it in small phrases. Treat it as one whole phrase. | Phrase | Meaning |"
    assert n == 3


def test_provenance_keys_are_never_touched() -> None:
    """chunk_id / source_chunk carry an adjacent word char, so \\bchunk\\b can't match."""
    text = "  chunk_id: 1-klas-bukvar_s0023\n  packet_chunk_id: x\n  ref: source_chunk_id"
    out, n = fix.transform_text(text)
    assert out == text
    assert n == 0


def test_learner_facing_prefix_removed_and_recapitalised() -> None:
    text = 'notes: "Learner-facing support for Ukrainian holidays."'
    out, _ = fix.transform_text(text)
    assert out == 'notes: "Support for Ukrainian holidays."'


def test_residual_chunk_id_prose_is_reported_not_provenance_key() -> None:
    text = (
        "  chunk_id: 1-klas_s0023\n"
        "  notes: retrieved via search_text because plan notes include no literal chunk_id\n"
    )
    hits = fix.residual_prose_hits(text)
    # The bare key line (line 1) is excluded; the prose mention (line 2) is reported.
    assert [line_no for line_no, _ in hits] == [2]
