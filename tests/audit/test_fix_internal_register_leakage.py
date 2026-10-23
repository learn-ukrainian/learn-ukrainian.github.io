from __future__ import annotations

from scripts.audit import fix_internal_register_leakage as fix


def test_provenance_keys_are_never_touched() -> None:
    """chunk_id / source_chunk carry an adjacent word char, so \\bchunk\\b can't match."""
    text = "  chunk_id: 1-klas-bukvar_s0023\n  packet_chunk_id: x\n  ref: source_chunk_id"
    out, n = fix.transform_text(text)
    assert out == text
    assert n == 0


def test_learner_facing_midsentence_keeps_lowercase() -> None:
    """A2 regression: a lead-in word before the phrase means it was NOT sentence-
    initial, so the following word keeps running-text case ("Short overview", not
    "Short Overview"). The old unconditional .upper() produced the miscapitalisation."""
    for lead in ("Short", "Catalogued", "Public", "Optional", "Core", "Additional"):
        text = f'notes: "{lead} learner-facing practice for aspect."'
        out, _ = fix.transform_text(text)
        assert out == f'notes: "{lead} practice for aspect."', out
