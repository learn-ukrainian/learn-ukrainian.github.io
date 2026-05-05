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
