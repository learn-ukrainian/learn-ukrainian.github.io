from __future__ import annotations

from scripts.build.linear_pipeline import _inject_activity_gate


def test_inject_activity_gate_rejects_uninjected_activities_by_default() -> None:
    activities = [{"id": "act-1"}, {"id": "act-2"}]

    result = _inject_activity_gate("Intro\n\n<!-- INJECT_ACTIVITY: act-1 -->", activities)

    assert result["passed"] is False
    assert result["unused"] == ["act-2"]
    assert result["workbook_only"] == []
    assert result["reason"] == "unused_activities_not_injected"


def test_inject_activity_gate_allows_v2_workbook_activities(tmp_path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "activities.yaml").write_text(
        """---
inline:
  - id: act-1
workbook:
  - id: act-2
  - id: act-3
""",
        encoding="utf-8",
    )
    activities = [{"id": "act-1"}, {"id": "act-2"}, {"id": "act-3"}]

    result = _inject_activity_gate(
        "Intro\n\n<!-- INJECT_ACTIVITY: act-1 -->",
        activities,
        module_dir=module_dir,
    )

    assert result["passed"] is True
    assert result["unused"] == []
    assert result["workbook_only"] == ["act-2", "act-3"]
    assert result["reason"] is None


def test_inject_activity_gate_allows_workbook_only_for_a1_first_contact() -> None:
    activities = [{"id": "act-1"}, {"id": "act-2"}]
    plan = {"level": "a1", "sequence": 1}

    result = _inject_activity_gate("Intro\n\n<!-- INJECT_ACTIVITY: act-1 -->", activities, plan)

    assert result["passed"] is True
    assert result["unused"] == []
    assert result["workbook_only"] == ["act-2"]
    assert result["reason"] is None


def test_inject_activity_gate_still_rejects_unknown_injected_ids_for_a1_first_contact() -> None:
    activities = [{"id": "act-1"}, {"id": "act-2"}]
    plan = {"level": "a1", "sequence": 1}

    result = _inject_activity_gate("Intro\n\n<!-- INJECT_ACTIVITY: missing -->", activities, plan)

    assert result["passed"] is False
    assert result["missing"] == ["missing"]
    assert result["workbook_only"] == ["act-1", "act-2"]
    assert result["reason"] == "missing_activity_ids"
