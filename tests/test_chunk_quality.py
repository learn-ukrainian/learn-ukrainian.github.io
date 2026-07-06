from __future__ import annotations

import pytest

from scripts.rag.chunk_quality import (
    apply_symbol_noise_gate,
    should_drop_for_symbol_noise,
    symbol_noise_density,
)


def test_clean_prose_passes_symbol_noise_gate() -> None:
    text = "Алгоритм працює так: input, output, 2024. Хімія? Так!"

    assert symbol_noise_density(text) == 0.0
    assert not should_drop_for_symbol_noise(text)


def test_formula_garbage_chunk_drops() -> None:
    text = "∑∫√≈≠≤≥÷×▯" * 8 + "xy12"

    assert symbol_noise_density(text) > 0.25
    assert should_drop_for_symbol_noise(text)


def test_symbol_noise_threshold_boundary_is_strictly_exceeds() -> None:
    assert symbol_noise_density("ааа#") == pytest.approx(0.25)
    assert not should_drop_for_symbol_noise("ааа#", threshold=0.25)
    assert should_drop_for_symbol_noise("аа##", threshold=0.25)


def test_apply_symbol_noise_gate_counts_per_book() -> None:
    chunks = [
        {"text": "Чистий український текст."},
        {"text": "∑∫√≈≠≤≥÷×▯"},
        {"text": "English variables x and y are fine."},
    ]

    kept, stats = apply_symbol_noise_gate(
        chunks,
        source_file="7-klas-fizyka-example-2024",
        warn=None,
    )

    assert kept == [chunks[0], chunks[2]]
    assert stats.manifest_record() == {
        "source_file": "7-klas-fizyka-example-2024",
        "chunks_kept": 2,
        "chunks_dropped_noise": 1,
        "drop_ratio": 0.333,
    }


def test_apply_symbol_noise_gate_warns_when_drop_ratio_is_loud() -> None:
    warnings = []

    apply_symbol_noise_gate(
        [
            {"text": "Чистий текст."},
            {"text": "∑∫√≈≠≤≥÷×▯"},
        ],
        source_file="book-with-layout-noise",
        warn=warnings.append,
    )

    assert len(warnings) == 1
    assert "WARNING: SYMBOL-NOISE gate dropped 1/2 chunks (50.0%)" in warnings[0]
    assert "book-with-layout-noise" in warnings[0]


def test_ukrainian_apostrophe_forms_are_not_noise():
    """мʼяч (U+02BC) and об'єкт (U+2019) are ordinary prose, not symbols."""

    prose = "Мʼяч підстрибнув, і об'єкт зупинився — учні записали висновок…"
    assert symbol_noise_density(prose) == 0.0
