from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts.build import linear_pipeline

PLAN = {
    "level": "a1",
    "sequence": 20,
    "slug": "fixture",
    "word_target": 600,
}


def _write_artifacts(module_dir: Path, *, module_text: str = "old text\n") -> None:
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.md").write_text(module_text, encoding="utf-8")
    (module_dir / "activities.yaml").write_text(
        "- id: act-1\n  type: select\n  prompt: old activity\n",
        encoding="utf-8",
    )


def _proposal(
    obligation_id: str = "step-1",
    obligation_type: str = "sequence_step",
    *,
    artifact: str | None = "module.md",
    find: str = "old text",
    replace: str = "new text",
    manifest_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    treatment: dict[str, Any] = {"shape": f"{artifact or 'module.md'} local patch"}
    if artifact is not None:
        treatment["artifact"] = artifact
    return {
        "obligation_id": obligation_id,
        "obligation_type": obligation_type,
        "failure_reason": "missing",
        "current_artifact_state": find,
        "expected_treatment": treatment,
        "surgical_diff_hint": f"replace {find!r} with {replace!r}",
        "manifest_payload": manifest_payload or {"required_claim": replace},
    }


def _gate(
    *,
    passed: bool,
    coverage_pct: float,
    proposals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "passed": passed,
        "coverage_pct": coverage_pct,
        "obligations": [],
    }
    if proposals is not None:
        report["fix_proposals"] = proposals
    return report


def _install_gate(
    monkeypatch: pytest.MonkeyPatch,
    reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_gate(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        index = min(len(calls) - 1, len(reports) - 1)
        return reports[index]

    monkeypatch.setattr(linear_pipeline, "run_wiki_coverage_gate", fake_gate)
    return calls


def _fix(find: str, replace: str, obligation_id: str = "step-1") -> str:
    return (
        "<fixes>"
        f"<fix obligation_id=\"{obligation_id}\">"
        f"<find>{find}</find>"
        f"<replace>{replace}</replace>"
        "</fix>"
        "</fixes>"
    )


def _run(
    module_dir: Path,
    *,
    batched_corrector: Any | None = None,
    narrow_corrector: Any | None = None,
    invoker: Any | None = None,
    events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    event_log = events if events is not None else []

    def sink(event: str, **fields: Any) -> None:
        event_log.append({"event": event, **fields})

    return linear_pipeline.run_wiki_coverage_with_corrections(
        plan=PLAN,
        manifest={"slug": "fixture"},
        writer_output="<implementation_map></implementation_map>",
        module_dir=module_dir,
        level="a1",
        batched_corrector=batched_corrector,
        narrow_corrector=narrow_corrector,
        invoker=invoker,
        event_sink=sink,
    )


def test_initial_pass_short_circuits_without_corrector_or_events(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_artifacts(tmp_path)
    _install_gate(monkeypatch, [_gate(passed=True, coverage_pct=1.0)])
    events: list[dict[str, Any]] = []

    def corrector(**_: Any) -> str:
        raise AssertionError("corrector should not be called")

    result = _run(tmp_path, batched_corrector=corrector, events=events)

    assert result["passed"] is True
    assert events == []


def test_single_batched_pass_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_artifacts(tmp_path)
    proposal = _proposal(find="old text", replace="new text")
    _install_gate(
        monkeypatch,
        [
            _gate(passed=False, coverage_pct=0.4, proposals=[proposal]),
            _gate(passed=True, coverage_pct=1.0),
        ],
    )
    calls: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []

    def corrector(**kwargs: Any) -> str:
        calls.append(kwargs)
        return _fix("old text", "new text")

    result = _run(tmp_path, batched_corrector=corrector, events=events)

    assert result["passed"] is True
    assert "new text" in (tmp_path / "module.md").read_text(encoding="utf-8")
    assert len(calls) == 1
    done = next(
        event for event in events if event["event"] == "wiki_coverage_correction_pass_done"
    )
    assert done["coverage_pct_after"] > done["coverage_pct_before"]


def test_batched_plateau_falls_through_to_narrow_loop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_artifacts(tmp_path, module_text="batch one\nbatch two\nnarrow old\n")
    p1 = _proposal("step-1", find="batch one", replace="batch one fixed")
    p2 = _proposal("step-2", find="batch two", replace="batch two fixed")
    p3 = _proposal("step-3", find="narrow old", replace="narrow fixed")
    _install_gate(
        monkeypatch,
        [
            _gate(passed=False, coverage_pct=0.2, proposals=[p1]),
            _gate(passed=False, coverage_pct=0.4, proposals=[p2]),
            _gate(passed=False, coverage_pct=0.4, proposals=[p3]),
            _gate(passed=True, coverage_pct=1.0),
        ],
    )
    batched_calls: list[dict[str, Any]] = []
    narrow_calls: list[dict[str, Any]] = []

    def batched(**kwargs: Any) -> str:
        batched_calls.append(kwargs)
        if len(batched_calls) == 1:
            return _fix("batch one", "batch one fixed", "step-1")
        return _fix("batch two", "batch two fixed", "step-2")

    def narrow(**kwargs: Any) -> str:
        narrow_calls.append(kwargs)
        return _fix("narrow old", "narrow fixed", "step-3")

    result = _run(tmp_path, batched_corrector=batched, narrow_corrector=narrow)

    assert result["passed"] is True
    assert len(batched_calls) == 2
    assert len(narrow_calls) == 1


def test_narrow_loop_exhausted_emits_plan_revision_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_artifacts(tmp_path)
    proposal = _proposal()
    _install_gate(
        monkeypatch,
        [
            _gate(passed=False, coverage_pct=0.1, proposals=[proposal]),
            _gate(passed=False, coverage_pct=0.2, proposals=[proposal]),
            _gate(passed=False, coverage_pct=0.3, proposals=[proposal]),
            _gate(passed=False, coverage_pct=0.3, proposals=[proposal]),
            _gate(passed=False, coverage_pct=0.3, proposals=[proposal]),
        ],
    )
    events: list[dict[str, Any]] = []

    result = _run(
        tmp_path,
        batched_corrector=lambda **_: "no fixes",
        narrow_corrector=lambda **_: "no fixes",
        events=events,
    )

    assert result["passed"] is False
    terminal = events[-1]
    assert terminal["event"] == "wiki_coverage_plan_revision_request"
    assert terminal["coverage_pct_final"] == 0.3
    assert terminal["remaining_failures"] == [proposal]
    assert terminal["total_iterations"] == 4
    assert terminal["iterations_exhausted"] is True


def test_batched_regression_rolls_back_then_enters_narrow_loop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_artifacts(tmp_path, module_text="safe text\n")
    proposal = _proposal(find="safe text", replace="bad text")
    _install_gate(
        monkeypatch,
        [
            _gate(passed=False, coverage_pct=0.5, proposals=[proposal]),
            _gate(passed=False, coverage_pct=0.4, proposals=[proposal]),
            _gate(passed=False, coverage_pct=0.5, proposals=[proposal]),
            _gate(passed=True, coverage_pct=1.0),
        ],
    )
    events: list[dict[str, Any]] = []

    result = _run(
        tmp_path,
        batched_corrector=lambda **_: _fix("safe text", "bad text"),
        narrow_corrector=lambda **_: _fix("safe text", "good text"),
        events=events,
    )

    assert result["passed"] is True
    assert "good text" in (tmp_path / "module.md").read_text(encoding="utf-8")
    regression = next(
        event
        for event in events
        if event["event"] == "wiki_coverage_correction_regression"
    )
    assert regression["phase"] == "batched"


def test_narrow_regression_rolls_back_and_stops_remaining_narrow_iterations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_artifacts(tmp_path, module_text="safe text\n")
    proposal = _proposal(find="safe text", replace="bad text")
    _install_gate(
        monkeypatch,
        [
            _gate(passed=False, coverage_pct=0.5, proposals=[proposal]),
            _gate(passed=False, coverage_pct=0.5, proposals=[proposal]),
            _gate(passed=False, coverage_pct=0.4, proposals=[proposal]),
            _gate(passed=False, coverage_pct=0.5, proposals=[proposal]),
        ],
    )
    narrow_calls: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []

    def narrow(**kwargs: Any) -> str:
        narrow_calls.append(kwargs)
        return _fix("safe text", "bad text")

    result = _run(
        tmp_path,
        batched_corrector=lambda **_: "no fixes",
        narrow_corrector=narrow,
        events=events,
    )

    assert result["passed"] is False
    assert (tmp_path / "module.md").read_text(encoding="utf-8") == "safe text\n"
    assert len(narrow_calls) == 1
    regression = next(
        event
        for event in events
        if event["event"] == "wiki_coverage_correction_regression"
    )
    assert regression["phase"] == "narrow"


def test_unparseable_batched_response_continues_to_next_group(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_artifacts(tmp_path)
    p1 = _proposal("step-1", artifact="module.md", find="old text")
    p2 = _proposal(
        "err-1",
        "l2_error",
        artifact="activities.yaml",
        find="old activity",
        replace="new activity",
    )
    _install_gate(
        monkeypatch,
        [
            _gate(passed=False, coverage_pct=0.4, proposals=[p1, p2]),
            _gate(passed=True, coverage_pct=1.0),
        ],
    )
    events: list[dict[str, Any]] = []

    def corrector(**kwargs: Any) -> str:
        if "module.md" in kwargs["group_key"]:
            return "not parseable"
        return _fix("old activity", "new activity", "err-1")

    result = _run(tmp_path, batched_corrector=corrector, events=events)

    assert result["passed"] is True
    assert "new activity" in (tmp_path / "activities.yaml").read_text(
        encoding="utf-8"
    )
    unparseable = next(
        event
        for event in events
        if event["event"] == "wiki_coverage_correction_unparseable"
    )
    assert unparseable["phase"] == "batched"
    assert unparseable["group_key"] == "(artifact=module.md, obligation_type=sequence_step)"


def test_yaml_invalid_fix_rolls_back_artifact_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_artifacts(tmp_path)
    original = (tmp_path / "activities.yaml").read_text(encoding="utf-8")
    proposal = _proposal(
        "err-1",
        "l2_error",
        artifact="activities.yaml",
        find=original,
        replace="not: a list\n",
    )
    _install_gate(
        monkeypatch,
        [
            _gate(passed=False, coverage_pct=0.4, proposals=[proposal]),
            _gate(passed=True, coverage_pct=1.0),
        ],
    )
    events: list[dict[str, Any]] = []

    result = _run(
        tmp_path,
        batched_corrector=lambda **_: _fix(original, "not: a list\n", "err-1"),
        events=events,
    )

    assert result["passed"] is True
    assert (tmp_path / "activities.yaml").read_text(encoding="utf-8") == original
    invalid = next(
        event
        for event in events
        if event["event"] == "wiki_coverage_correction_yaml_invalid"
    )
    assert invalid["artifact"] == "activities.yaml"
