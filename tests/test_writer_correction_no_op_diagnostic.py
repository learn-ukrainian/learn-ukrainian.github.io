from __future__ import annotations

import json
from pathlib import Path

from scripts.build import linear_pipeline


def _events(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines()]


def test_writer_correction_unparseable_response_emits_diagnostic(tmp_path: Path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text("## Morning\n\nTest module.\n", encoding="utf-8")
    telemetry = tmp_path / "events.jsonl"

    with linear_pipeline.telemetry_event_sink(telemetry):
        linear_pipeline._apply_writer_correction(
            "word_count",
            {"passed": False, "minimum": 100, "actual": 20},
            qg_report={"gates": {}},
            module_dir=module_dir,
            plan_path=tmp_path / "plan.yaml",
            writer_corrector=lambda _context: "I fixed the prose but emitted no artifacts.",
            writer="codex-tools",
            invoker=None,
        )

    events = _events(telemetry)
    assert [event["event"] for event in events] == ["writer_correction_unparseable"]
    assert events[0]["gate"] == "word_count"
    assert events[0]["response_preview"] == "I fixed the prose but emitted no artifacts."
