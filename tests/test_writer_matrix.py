"""Unit tests for the V7 writer-bench v0 telemetry parser.

The parser is the load-bearing seam between v7_build.py's JSONL stream
and the bench's per-cell record.  When v7_build.py changes event names
or shapes, these tests are the canary.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# scripts/ is namespace-package + scripts/bench/ ships its own __init__.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from bench.writer_matrix import (
    WRITER_DEFAULTS,
    _parse_telemetry,
    _resolve_writer_defaults,
)


def _write_jsonl(path: Path, events: list[dict]) -> None:
    """Helper — write one JSONL line per dict event."""
    path.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n",
        encoding="utf-8",
    )


def test_writer_defaults_pinned_matrix() -> None:
    """The pinned matrix must list exactly the 6 writers v0 measures.

    If WRITER_DEFAULTS drifts from PR #2221 §2.3 without an explicit
    bench-design update, this fails so the deviation gets a code
    review instead of slipping into a silent N=1 measurement.
    """
    assert set(WRITER_DEFAULTS.keys()) == {
        "claude-tools",
        "gemini-tools",
        "codex-tools",
        "deepseek-tools",
        "qwen-tools",
        "agy-tools",
    }
    # Every entry must carry both fields — the bench reads them.
    for writer, defaults in WRITER_DEFAULTS.items():
        assert "model" in defaults, f"{writer} missing model"
        assert "effort" in defaults, f"{writer} missing effort"


def test_resolve_writer_defaults_known(tmp_path: Path) -> None:
    model, effort = _resolve_writer_defaults("codex-tools")
    assert model == "gpt-5.5"
    assert effort == "high"


def test_resolve_writer_defaults_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown writer"):
        _resolve_writer_defaults("nonexistent-tools")


def test_parse_telemetry_missing_file(tmp_path: Path) -> None:
    state = _parse_telemetry(tmp_path / "missing.jsonl")
    assert state["failure_class"] == "no_telemetry"
    assert state["phase_reached"] == "<start>"
    assert state["writer_passed"] is False
    assert state["python_qg_passed"] is False


def test_parse_telemetry_writer_phase_completes(tmp_path: Path) -> None:
    """Writer phase finished but no python_qg yet — `writer_passed_qg_unreached`."""
    tele = tmp_path / "t.jsonl"
    _write_jsonl(
        tele,
        [
            {"event": "module_start", "level": "a1", "slug": "my-morning"},
            {"event": "phase_done", "phase": "plan"},
            {"event": "phase_done", "phase": "knowledge_packet"},
            {"event": "phase_done", "phase": "writer"},
        ],
    )
    state = _parse_telemetry(tele)
    assert state["phase_reached"] == "writer"
    assert state["writer_passed"] is True
    assert state["python_qg_passed"] is False
    assert state["failure_class"] == "writer_passed_qg_unreached"


def test_parse_telemetry_writer_trace_isolation_fail(tmp_path: Path) -> None:
    """Writer ran but tripped the trace-isolation post-check."""
    tele = tmp_path / "t.jsonl"
    _write_jsonl(
        tele,
        [
            {"event": "phase_done", "phase": "plan"},
            {"event": "phase_done", "phase": "knowledge_packet"},
            {"event": "phase_done", "phase": "writer"},
            {
                "event": "writer_trace_isolation_failed",
                "gate": "writer_trace_isolation",
                "sub_class": "wrong_tool_family",
                "evidence": {"offending_tool_calls": [{"name": "exec_command"}]},
            },
        ],
    )
    state = _parse_telemetry(tele)
    assert state["failure_class"] == "writer_trace_isolation_fail"
    assert state["writer_passed"] is False  # trace-isolation overrides
    assert state["failure_detail"]["sub_class"] == "wrong_tool_family"


def test_parse_telemetry_python_qg_passed_via_artifact(tmp_path: Path) -> None:
    """python_qg gates parsed from the artifact JSON, not the event."""
    tele = tmp_path / "t.jsonl"
    log = tmp_path / "build.log"
    worktree = tmp_path / "build-worktree"
    module_dir = worktree / "curriculum" / "l2-uk-en" / "a1" / "my-morning"
    module_dir.mkdir(parents=True)

    log.write_text(
        f"some chatter\nBUILD_WORKTREE={worktree}\n",
        encoding="utf-8",
    )
    (module_dir / "python_qg.json").write_text(
        json.dumps(
            {
                "gates": {
                    "passed": True,
                    "results": {
                        "vesum_verified": {"passed": True},
                        "word_count": {"passed": True},
                        "engagement_floor": {"passed": True},
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        tele,
        [
            {"event": "phase_done", "phase": "plan"},
            {"event": "phase_done", "phase": "knowledge_packet"},
            {"event": "phase_done", "phase": "writer"},
            {"event": "phase_done", "phase": "python_qg"},
        ],
    )

    state = _parse_telemetry(tele, log_path=log, level="a1", slug="my-morning")
    assert state["phase_reached"] == "python_qg"
    assert state["python_qg_passed"] is True
    assert state["writer_passed"] is True
    assert sorted(state["gates_passed"]) == [
        "engagement_floor",
        "vesum_verified",
        "word_count",
    ]
    assert state["gates_failed"] == []
    assert state["failure_class"] == "ok"


def test_parse_telemetry_python_qg_failed_via_artifact(tmp_path: Path) -> None:
    """python_qg ran but gates.passed=False → `python_qg_fail`."""
    tele = tmp_path / "t.jsonl"
    log = tmp_path / "build.log"
    worktree = tmp_path / "wt"
    module_dir = worktree / "curriculum" / "l2-uk-en" / "a1" / "my-morning"
    module_dir.mkdir(parents=True)
    log.write_text(f"BUILD_WORKTREE={worktree}\n", encoding="utf-8")
    (module_dir / "python_qg.json").write_text(
        json.dumps(
            {
                "gates": {
                    "passed": False,
                    "results": {
                        "vesum_verified": {"passed": False},
                        "word_count": {"passed": True},
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    _write_jsonl(
        tele,
        [
            {"event": "phase_done", "phase": "writer"},
            {"event": "phase_done", "phase": "python_qg"},
        ],
    )

    state = _parse_telemetry(tele, log_path=log, level="a1", slug="my-morning")
    assert state["python_qg_passed"] is False
    assert state["failure_class"] == "python_qg_fail"
    assert state["gates_failed"] == ["vesum_verified"]
    assert state["gates_passed"] == ["word_count"]


def test_parse_telemetry_module_done_emitted(tmp_path: Path) -> None:
    """Full pipeline success — module_done event advances phase_reached."""
    tele = tmp_path / "t.jsonl"
    _write_jsonl(
        tele,
        [
            {"event": "phase_done", "phase": "writer"},
            {"event": "phase_done", "phase": "python_qg"},
            {"event": "phase_done", "phase": "module_done"},
            {"event": "module_done"},
        ],
    )
    state = _parse_telemetry(tele)
    assert state["phase_reached"] == "module_done"


def test_parse_telemetry_tolerates_malformed_lines(tmp_path: Path) -> None:
    """JSON decode errors and non-JSON lines must not crash the parser."""
    tele = tmp_path / "t.jsonl"
    tele.write_text(
        "\n".join(
            [
                "Some pre-banner log line",
                json.dumps({"event": "phase_done", "phase": "plan"}),
                "Ambiguous textbook source_file ...",  # noise
                "{partial json broken",
                json.dumps({"event": "phase_done", "phase": "writer"}),
                "",
            ]
        ),
        encoding="utf-8",
    )
    state = _parse_telemetry(tele)
    assert state["phase_reached"] == "writer"
    assert state["writer_passed"] is True
