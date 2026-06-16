from __future__ import annotations

import json
from pathlib import Path

from scripts.build import linear_pipeline


def _events(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines()]


def _module_dir(tmp_path: Path) -> Path:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text(
        "## Morning\n\nAnchor sentence.\n",
        encoding="utf-8",
    )
    return module_dir


def test_reviewer_correction_without_fixes_block_emits_diagnostic(
    tmp_path: Path,
) -> None:
    telemetry = tmp_path / "events.jsonl"

    with linear_pipeline.telemetry_event_sink(telemetry):
        linear_pipeline._apply_reviewer_correction(
            "russianisms_clean",
            {"passed": False, "hits": ["bad form"]},
            qg_report={"gates": {}},
            module_dir=_module_dir(tmp_path),
            plan_path=tmp_path / "plan.yaml",
            candidates=(),
            reviewer_corrector=lambda _context: "REVISE: please fix the issue.",
            invoker=None,
        )

    events = _events(telemetry)
    assert [event["event"] for event in events] == ["reviewer_fixes_unparseable"]
    assert events[0]["gate"] == "russianisms_clean"
    assert events[0]["response_preview"] == "REVISE: please fix the issue."


def test_reviewer_correction_unmatched_anchor_emits_diagnostic(
    tmp_path: Path,
) -> None:
    telemetry = tmp_path / "events.jsonl"

    with linear_pipeline.telemetry_event_sink(telemetry):
        linear_pipeline._apply_reviewer_correction(
            "russianisms_clean",
            {"passed": False, "hits": ["bad form"]},
            qg_report={"gates": {}},
            module_dir=_module_dir(tmp_path),
            plan_path=tmp_path / "plan.yaml",
            candidates=(),
            reviewer_corrector=lambda _context: (
                "<fixes>\n"
                "- find: Missing anchor\n"
                "  replace: Replacement text\n"
                "</fixes>"
            ),
            invoker=None,
        )

    events = _events(telemetry)
    assert [event["event"] for event in events] == [
        "reviewer_fixes_anchor_unmatched"
    ]
    assert events[0]["gate"] == "russianisms_clean"
    assert events[0]["anchor_preview"] == "Missing anchor"


def test_reviewer_fix_whitespace_normalized_anchor_match_applies_once(
    tmp_path: Path,
) -> None:
    telemetry = tmp_path / "events.jsonl"
    text = "Before\n\nAlpha\n  beta   gamma\n\nAfter\n"

    with linear_pipeline.telemetry_event_sink(telemetry):
        result = linear_pipeline._apply_reviewer_fixes(
            text,
            [{"find": "Alpha beta gamma", "replace": "Alpha beta delta"}],
            gate="vesum_verified",
            module_dir=_module_dir(tmp_path),
            plan_path=tmp_path / "plan.yaml",
        )

    assert result.text == "Before\n\nAlpha beta delta\n\nAfter\n"
    assert result.unmatched_anchors == frozenset()
    events = _events(telemetry)
    assert [event["event"] for event in events] == [
        "reviewer_fix_anchor_normalized_match"
    ]
    assert events[0]["gate"] == "vesum_verified"
    assert events[0]["operation"] == "replace"
    assert events[0]["anchor_preview"] == "Alpha beta gamma"
    assert events[0]["matched_preview"] == "Alpha\n  beta   gamma"


def test_reviewer_fix_trailing_boundary_whitespace_is_not_replaced() -> None:
    result = linear_pipeline._apply_reviewer_fixes(
        "Intro: target\n\n- next item\n",
        [{"find": "target ", "replace": "FIXED"}],
    )

    assert result.text == "Intro: FIXED\n\n- next item\n"
    assert result.unmatched_anchors == frozenset()


def test_reviewer_fix_leading_boundary_whitespace_is_not_replaced() -> None:
    result = linear_pipeline._apply_reviewer_fixes(
        "Intro\n\ntarget",
        [{"find": " target", "replace": "FIXED"}],
    )

    assert result.text == "Intro\n\nFIXED"
    assert result.unmatched_anchors == frozenset()


def test_reviewer_insert_after_trailing_boundary_whitespace_inserts_before_run() -> None:
    result = linear_pipeline._apply_reviewer_fixes(
        "target\n\n- item",
        [{"insert_after": "target ", "text": "INSERTED"}],
    )

    assert result.text == "targetINSERTED\n\n- item"
    assert result.unmatched_anchors == frozenset()


def test_reviewer_fix_ambiguous_normalized_anchor_fails_closed(
    tmp_path: Path,
) -> None:
    telemetry = tmp_path / "events.jsonl"
    text = "One\n  two\nMiddle\nOne\t\t two\n"

    with linear_pipeline.telemetry_event_sink(telemetry):
        result = linear_pipeline._apply_reviewer_fixes(
            text,
            [{"find": "One two", "replace": "Changed"}],
            gate="vesum_verified",
            module_dir=_module_dir(tmp_path),
            plan_path=tmp_path / "plan.yaml",
        )

    assert result.text == text
    assert result.unmatched_anchors == frozenset({"One two"})
    events = _events(telemetry)
    assert [event["event"] for event in events] == [
        "reviewer_fixes_anchor_unmatched"
    ]
    assert "Changed" not in result.text


def test_reviewer_fix_genuine_no_match_stays_unmatched(
    tmp_path: Path,
) -> None:
    telemetry = tmp_path / "events.jsonl"
    text = "Alpha beta\n"

    with linear_pipeline.telemetry_event_sink(telemetry):
        result = linear_pipeline._apply_reviewer_fixes(
            text,
            [{"find": "Gamma delta", "replace": "Changed"}],
            gate="vesum_verified",
            module_dir=_module_dir(tmp_path),
            plan_path=tmp_path / "plan.yaml",
        )

    assert result.text == text
    assert result.unmatched_anchors == frozenset({"Gamma delta"})
    events = _events(telemetry)
    assert [event["event"] for event in events] == [
        "reviewer_fixes_anchor_unmatched"
    ]


def test_reviewer_fix_exact_match_fast_path_stays_silent(
    tmp_path: Path,
) -> None:
    telemetry = tmp_path / "events.jsonl"

    with linear_pipeline.telemetry_event_sink(telemetry):
        result = linear_pipeline._apply_reviewer_fixes(
            "Alpha beta\n",
            [{"find": "Alpha beta", "replace": "Changed"}],
            gate="vesum_verified",
            module_dir=_module_dir(tmp_path),
            plan_path=tmp_path / "plan.yaml",
        )

    assert result.text == "Changed\n"
    assert result.unmatched_anchors == frozenset()
    assert _events(telemetry) == []


def test_reviewer_fix_applicable_count_ignores_missing_replace() -> None:
    count = linear_pipeline._count_applicable_reviewer_fixes(
        "Alpha\n  beta\n",
        [{"find": "Alpha beta"}],
    )

    assert count == 0
