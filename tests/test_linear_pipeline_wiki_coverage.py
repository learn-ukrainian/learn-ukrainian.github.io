from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build import linear_pipeline


def test_wiki_coverage_correction_attempt_is_written(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text("Original text.\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text("[]\n", encoding="utf-8")
    reports = [
        {
            "passed": False,
            "coverage_pct": 0.0,
            "fix_proposals": [
                {
                    "obligation_id": "obl-1",
                    "obligation_type": "concept",
                    "expected_treatment": {"artifact": "module.md"},
                    "surgical_diff_hint": "Add the missing wiki obligation.",
                }
            ],
        },
        {"passed": True, "coverage_pct": 1.0, "fix_proposals": []},
    ]

    def fake_gate(**_kwargs: object) -> dict[str, object]:
        return reports.pop(0)

    def fake_corrector(**_kwargs: object) -> str:
        return (
            "<fixes><fix><find>Original text.</find>"
            "<replace>Original text with wiki obligation.</replace></fix></fixes>"
        )

    monkeypatch.setattr(linear_pipeline, "run_wiki_coverage_gate", fake_gate)

    result = linear_pipeline.run_wiki_coverage_with_corrections(
        plan={"level": "a1", "sequence": 1, "slug": "my-morning", "word_target": 100},
        manifest={"slug": "my-morning"},
        writer_output="",
        module_dir=module_dir,
        batched_corrector=fake_corrector,
    )

    correction = json.loads(
        (module_dir / "wiki_coverage_correction_r1.json").read_text("utf-8")
    )
    assert result["passed"] is True
    assert correction["phase"] == "batched"
    assert correction["fixes_applied_total"] == 1
    assert "Wiki-Coverage Correction" in correction["attempts"][0]["prompt"]
