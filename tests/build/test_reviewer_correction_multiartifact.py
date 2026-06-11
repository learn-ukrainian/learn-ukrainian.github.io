from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.build import linear_pipeline

MODULE_TEXT = """\
# Календарна обрядовість

## Діалоги

This lesson text is clean and does not contain the activity typo.
"""

ACTIVITIES_TEXT = """\
- id: act-1
  type: fill-in
  title: Весняні пісні
  items:
  - sentence: "На уроці згадуємо гаівки."
    answer: "гаївки"
"""

VOCABULARY_TEXT = """\
- lemma: гаївка
  translation: spring ritual song
  pos: noun
  usage: "Гаївка звучить навесні."
"""

RESOURCES_TEXT = """\
- title: Весняні обряди
  role: textbook
"""


def _write_fixture(tmp_path: Path) -> Path:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text(MODULE_TEXT, encoding="utf-8")
    (module_dir / "activities.yaml").write_text(ACTIVITIES_TEXT, encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text(VOCABULARY_TEXT, encoding="utf-8")
    (module_dir / "resources.yaml").write_text(RESOURCES_TEXT, encoding="utf-8")
    return module_dir


def _reviewer_response(find: str, replace: str) -> str:
    return (
        "<fixes>\n"
        "<fix>\n"
        f"<find>{find}</find>\n"
        f"<replace>{replace}</replace>\n"
        "</fix>\n"
        "</fixes>"
    )


def _apply(
    module_dir: Path,
    plan_path: Path,
    *,
    gate: str,
    find: str,
    replace: str,
) -> tuple[frozenset[str], dict[str, Any]]:
    return linear_pipeline._apply_reviewer_correction(
        gate,
        {"passed": False, "missing": [find]},
        qg_report={"gates": {gate: {"passed": False}}},
        module_dir=module_dir,
        plan_path=plan_path,
        candidates=(),
        reviewer_corrector=lambda _context: _reviewer_response(find, replace),
        invoker=None,
    )


def _events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_vesum_reviewer_correction_patches_activities_yaml(tmp_path: Path) -> None:
    module_dir = _write_fixture(tmp_path)
    plan_path = tmp_path / "plan.yaml"
    module_before = (module_dir / "module.md").read_text(encoding="utf-8")

    unmatched, payload = _apply(
        module_dir,
        plan_path,
        gate="vesum_verified",
        find="гаівки",
        replace="гаївки",
    )

    activities = (module_dir / "activities.yaml").read_text(encoding="utf-8")
    assert "гаївки" in activities
    assert "гаівки" not in activities
    assert (module_dir / "module.md").read_text(encoding="utf-8") == module_before
    assert unmatched == frozenset()
    assert payload["unmatched_anchors"] == []


def test_reviewer_correction_rolls_back_invalid_yaml_artifact(tmp_path: Path) -> None:
    module_dir = _write_fixture(tmp_path)
    plan_path = tmp_path / "plan.yaml"
    activities_path = module_dir / "activities.yaml"
    activities_before = activities_path.read_text(encoding="utf-8")
    telemetry = tmp_path / "events.jsonl"

    with linear_pipeline.telemetry_event_sink(telemetry):
        unmatched, payload = _apply(
            module_dir,
            plan_path,
            gate="vesum_verified",
            find='sentence: "На уроці згадуємо гаівки."',
            replace="sentence: [На уроці згадуємо гаївки.",
        )

    assert activities_path.read_text(encoding="utf-8") == activities_before
    assert unmatched == frozenset()
    assert payload["unmatched_anchors"] == []
    events = _events(telemetry)
    assert events[-1]["event"] == "reviewer_correction_yaml_invalid"
    assert events[-1]["artifact"] == "activities.yaml"


def test_reviewer_correction_still_patches_module_md_anchor(tmp_path: Path) -> None:
    module_dir = _write_fixture(tmp_path)
    plan_path = tmp_path / "plan.yaml"
    module_path = module_dir / "module.md"
    activities_before = (module_dir / "activities.yaml").read_text(encoding="utf-8")
    module_path.write_text(MODULE_TEXT + "\nПожалуйста, compare the forms.\n", encoding="utf-8")

    unmatched, payload = _apply(
        module_dir,
        plan_path,
        gate="russianisms_clean",
        find="Пожалуйста",
        replace="Будь ласка",
    )

    assert "Будь ласка, compare the forms." in module_path.read_text(encoding="utf-8")
    assert (module_dir / "activities.yaml").read_text(encoding="utf-8") == activities_before
    assert unmatched == frozenset()
    assert payload["unmatched_anchors"] == []
