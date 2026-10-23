"""Timeout contracts for the six remaining CLI subprocess sites (#7213 slice 20)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.usefixtures("github_command_boundary")

from scripts.bench import writer_matrix


@pytest.mark.parametrize("sep", ["\u0085", "\u2028", "\u2029"], ids=["NEL", "LS", "PS"])
def test_writer_matrix_resume_preserves_unicode_separators(tmp_path, sep):
    import json
    from dataclasses import asdict

    cell = writer_matrix.BenchCell(
        writer="fixture",
        level="a1",
        slug="fixture",
        effort=None,
        started_at="fixture",
        wall_clock_s=1.0,
        exit_code=0,
        phase_reached="module_done",
        writer_passed=True,
        python_qg_passed=True,
        notes=f"a{sep}b",
    )
    path = tmp_path / "cells.jsonl"
    path.write_text(json.dumps(asdict(cell), ensure_ascii=False) + "\n", encoding="utf-8")
    assert writer_matrix._load_existing_cells(path) == [cell]
