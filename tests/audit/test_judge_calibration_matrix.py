from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from scripts.audit import judge_calibration_matrix as matrix
from scripts.audit._judge_eval_lib import aggregate, score_case


def test_cell_key_format() -> None:
    cell = matrix.Cell(
        family="anthropic",
        model="claude-opus-4-7",
        harness="hermes",
        effort="max",
        mcp_state="with_mcp",
    )

    assert matrix.cell_path(Path("audit/matrix"), cell) == Path(
        "audit/matrix/anthropic/claude-opus-4-7/hermes/max-with_mcp.json"
    )


def test_unsupported_effort_returns_n_a_not_fabricated(tmp_path: Path) -> None:
    cell = matrix.Cell(
        family="anthropic",
        model="claude-sonnet-4-6",
        harness="native_cli",
        effort="max",
        mcp_state="with_mcp",
    )
    called = False

    def runner(_cell: matrix.Cell, _prompt: str) -> matrix.HarnessCall:
        nonlocal called
        called = True
        raise AssertionError("unsupported cells must not call a harness")

    record = matrix.run_cell(out_dir=tmp_path, cell=cell, cases=[], harness_runner=runner)

    assert record["result"] == "n/a"
    assert "effort=max" in record["reason"]
    assert "scores" not in record
    assert called is False
    assert matrix.cell_path(tmp_path, cell).exists()


def test_resume_skips_existing_cells(tmp_path: Path) -> None:
    cell = matrix.Cell(
        family="openai",
        model="gpt-5.5",
        harness="native_cli",
        effort="medium",
        mcp_state="with_mcp",
    )
    existing = {"cell": asdict(cell), "scores": {"f1": 0.42}}
    matrix.write_json(matrix.cell_path(tmp_path, cell), existing)

    def runner(_cell: matrix.Cell, _prompt: str) -> matrix.HarnessCall:
        raise AssertionError("resume should skip complete cell JSON")

    records = matrix.run_cells(
        out_dir=tmp_path,
        cells=[cell],
        cases=[],
        resume=True,
        max_parallel=1,
        harness_runner=runner,
    )

    assert records == [existing]


def test_hermes_config_swap_is_atomic(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    original = "model:\n  default: gpt-5.5\nagent:\n  reasoning_effort: medium\n"
    config.write_text(original, encoding="utf-8")

    with pytest.raises(RuntimeError, match="boom"):
        with matrix.hermes_effort_swap(config, "xhigh") as previous:
            assert previous == "medium"
            assert "  reasoning_effort: xhigh\n" in config.read_text(encoding="utf-8")
            raise RuntimeError("boom")

    assert config.read_text(encoding="utf-8") == original
    assert not (tmp_path / "config.yaml.judge-calibration-backup").exists()


def test_score_calculation_matches_grok_baseline() -> None:
    judgments_path = Path("audit/2026-05-15-grok-4.3-judge-calibration-with-mcp/judgments.jsonl")
    scores = []
    for line in judgments_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        gold = {
            "expected_clean": row["expected_flags_count"] == 0,
            "expected_flags": [{}] * row["expected_flags_count"],
        }
        scores.append(score_case(row["raw"], gold))

    agg = aggregate(scores)

    assert agg["f1"] == 0.7586
    assert agg["case_acc"] == 0.9167
    assert agg["precision"] == 0.8462
    assert agg["recall"] == 0.6875


def test_leaderboard_sorted_by_f1_descending(tmp_path: Path) -> None:
    weak = matrix.Cell("openai", "gpt-5.4-mini", "native_cli", "medium", "with_mcp")
    strong = matrix.Cell("openai", "gpt-5.5", "hermes", "medium", "with_mcp")
    for cell, f1 in ((weak, 0.2), (strong, 0.9)):
        matrix.write_json(
            matrix.cell_path(tmp_path, cell),
            {
                "cell": asdict(cell),
                "duration_s": 1.0,
                "scores": {
                    "f1": f1,
                    "precision": f1,
                    "recall": f1,
                    "case_acc": f1,
                },
                "raw_telemetry": {"errors": []},
            },
        )

    report_md, _ = matrix.build_reports(tmp_path)
    text = report_md.read_text(encoding="utf-8")

    assert text.index("| openai | gpt-5.5 | hermes |") < text.index(
        "| openai | gpt-5.4-mini | native_cli |"
    )
