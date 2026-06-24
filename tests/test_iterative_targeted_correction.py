from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.build import linear_pipeline


def _plan() -> dict[str, Any]:
    return {
        "level": "folk",
        "sequence": 1,
        "module": 1,
        "slug": "targeted-correction",
        "title": "Targeted correction",
        "word_target": 10,
        "content_outline": [
            {"section": "Intro", "words": 6, "points": ["Open the topic."]},
            {"section": "Body", "words": 4, "points": ["Keep the body."]},
        ],
        "references": [{"title": "Reference"}],
    }


def _artifact(section_id: str, markdown: str) -> linear_pipeline.SectionArtifact:
    return linear_pipeline.SectionArtifact(
        section_id=section_id,
        markdown=markdown,
        citations_used=[],
        primary_readings_used=[],
        vocab_candidates=[],
        activity_refs=[],
        self_check={},
    )


def _section_response(section_id: str, markdown: str) -> str:
    metadata = {
        "section_id": section_id,
        "citations_used": [],
        "primary_readings_used": [],
        "vocab_candidates": [],
        "activity_refs": [],
        "self_check": {},
    }
    return (
        f"````markdown file=section.md\n{markdown}\n````\n"
        "```json file=section_artifact.json\n"
        f"{json.dumps(metadata)}\n"
        "```"
    )


def _write_iterative_module(module_dir: Path) -> None:
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.md").write_text(
        "## Intro\n"
        "one two three.\n"
        "\n"
        "## Body\n"
        "alpha beta gamma delta.\n",
        encoding="utf-8",
    )
    (module_dir / "iterative_writer_sidecar.json").write_text(
        json.dumps(
            {
                "s1": {"line_start": 1, "line_end": 2},
                "s2": {"line_start": 4, "line_end": 5},
            }
        ),
        encoding="utf-8",
    )


def test_iterative_mapper_maps_line_violation_to_sidecar_section() -> None:
    sidecar = {
        "s1": {"line_start": 1, "line_end": 5},
        "s2": {"line_start": 6, "line_end": 12},
    }
    gate_report = {"violations": [{"line": 8, "message": "bad line"}]}

    assert linear_pipeline._iterative_sections_for_gate_locations(gate_report, sidecar) == [
        "s2"
    ]


def test_word_count_selection_picks_only_under_target_sections() -> None:
    plan = _plan()
    artifacts = [
        _artifact("s1", "one two three four five six"),
        _artifact("s2", "alpha beta"),
    ]

    assert linear_pipeline._select_iterative_word_count_sections(plan, artifacts) == ["s2"]


def test_targeted_reinvoke_replaces_only_selected_section(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    plan = _plan()
    module_dir = tmp_path / "module"
    _write_iterative_module(module_dir)
    monkeypatch.setattr(linear_pipeline, "plan_check", lambda _path: plan)

    calls: list[str] = []

    def invoke_fn(prompt: str, writer: str, **_kwargs: Any) -> str:
        assert writer == "codex"
        calls.append(prompt)
        return _section_response(
            "s1",
            "one two three plus added grounded words for this intro section.",
        )

    handled, _unmatched, payload = (
        linear_pipeline._apply_iterative_targeted_section_correction(
            "word_count",
            {"gates": {"word_count": {"passed": False, "count": 7, "target": 10}}},
            module_dir=module_dir,
            plan_path=tmp_path / "plan.yaml",
            writer="codex",
            invoke_fn=invoke_fn,
            section_attempts={},
        )
    )

    module_md = (module_dir / "module.md").read_text(encoding="utf-8")
    assert handled is True
    assert payload["selected_section_ids"] == ["s1"]
    assert len(calls) == 1
    assert "Expand this section to at least 6 words" in calls[0]
    assert "one two three plus added grounded words" in module_md
    assert "alpha beta gamma delta." in module_md


def test_targeted_reinvoke_respects_retry_cap(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    plan = _plan()
    module_dir = tmp_path / "module"
    _write_iterative_module(module_dir)
    monkeypatch.setattr(linear_pipeline, "plan_check", lambda _path: plan)

    calls: list[str] = []

    handled, _unmatched, payload = (
        linear_pipeline._apply_iterative_targeted_section_correction(
            "word_count",
            {"gates": {"word_count": {"passed": False, "count": 7, "target": 10}}},
            module_dir=module_dir,
            plan_path=tmp_path / "plan.yaml",
            writer="codex",
            invoke_fn=lambda *args: calls.append("called") or "",
            section_attempts={"s1": 2},
        )
    )

    assert handled is False
    assert payload["reason"] == "retry_cap_reached"
    assert calls == []
