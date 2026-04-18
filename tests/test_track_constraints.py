from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.track_constraints import (
    build_writer_constraints_section,
    promote_track_constraints,
)


def _write_module_memory(root: Path, level: str, slug: str, constraint: dict) -> None:
    memory_path = root / level / "orchestration" / slug / "module-memory.yaml"
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(
        yaml.safe_dump(
            {
                "plan_hash": "plan",
                "plan_version": 1,
                "sources_hash": "sources",
                "constraints": [constraint],
                "history": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )


def test_promotion_threshold_respects_modules_levels_and_metrics(tmp_path: Path) -> None:
    constraint = {
        "id": "c_shared",
        "normalized_id": "nf_shared",
        "dimension": "linguistic_accuracy",
        "error_class": "register_drift",
        "directive": "Teacher uses formal register.",
        "status": "active",
        "conflicts_with_plan": False,
        "promotion_metrics": {
            "attempt0_pass_rate_up": True,
            "hard_floor_failures_down": True,
            "recurrence_down": True,
        },
    }
    for index in range(4):
        _write_module_memory(tmp_path, "a1", f"slug-a1-{index}", constraint)
        _write_module_memory(tmp_path, "a2", f"slug-a2-{index}", constraint)

    promoted = promote_track_constraints(tmp_path, min_modules=8, min_levels=2)

    assert promoted["constraints"][0]["normalized_id"] == "nf_shared"
    assert promoted["constraints"][0]["status"] == "promoted"


def test_override_precedence_in_writer_template_assembly(tmp_path: Path) -> None:
    (tmp_path / "learned-constraints-track.yaml").write_text(
        yaml.safe_dump(
            {
                "constraints": [
                    {
                        "id": "track_001",
                        "normalized_id": "nf_shared",
                        "dimension": "linguistic_accuracy",
                        "error_class": "register_drift",
                        "directive": "Track says use formal register.",
                        "status": "promoted",
                    }
                ]
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )
    _write_module_memory(
        tmp_path,
        "a1",
        "demo",
        {
            "id": "module_001",
            "normalized_id": "nf_shared",
            "dimension": "linguistic_accuracy",
            "error_class": "register_drift",
            "directive": "Module says peer dialogue stays informal.",
            "status": "active",
            "override_track_level": True,
            "scope": {"section_title": "Привіт!"},
        },
    )

    block = build_writer_constraints_section(curriculum_root=tmp_path, level="a1", slug="demo")

    assert "Module says peer dialogue stays informal." in block
    assert "Track says use formal register." not in block
