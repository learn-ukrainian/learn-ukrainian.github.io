from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.build import linear_pipeline, v7_build


def _folk_plan() -> dict[str, Any]:
    return {
        "level": "folk",
        "sequence": 1,
        "module": 1,
        "slug": "vesnianky-hayivky",
        "title": "Веснянки й гаївки",
        "word_target": 120,
        "content_outline": [
            {
                "section": "Корпус і контекст",
                "words": 80,
                "points": ["Anchor the analysis in attested spring-song lines."],
            },
            {
                "section": "Поетика",
                "words": 40,
                "points": ["Discuss formula and performance cues."],
            },
        ],
        "readings": [
            {
                "reading_id": "vesnianky",
                "title": "ВЕРБАТИМ примірники",
                "text": "Ой весна, весна, днем красна... [S1]",
            }
        ],
        "reading_section_map": {"vesnianky": "s1"},
        "references": [{"id": "S1", "title": "Folk corpus"}],
    }


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
        "## Корпус і контекст\n"
        "one two three.\n"
        "\n"
        "## Поетика\n"
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


def test_v7_iterative_writer_passes_folk_framing_rules(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    captured: dict[str, str] = {}

    def fake_run_iterative_writer(*_args: Any, **kwargs: Any) -> dict[str, Any]:
        captured["framing_rules"] = kwargs["framing_rules"]
        return {"sidecar": {}}

    monkeypatch.setattr(linear_pipeline, "run_iterative_writer", fake_run_iterative_writer)
    monkeypatch.setattr(linear_pipeline, "iterative_result_to_writer_artifacts", lambda _result: {})
    monkeypatch.setattr(linear_pipeline, "render_writer_artifacts_output", lambda _artifacts: "")

    v7_build._run_writer_mode(
        writer_mode="iterative",
        plan=_folk_plan(),
        plan_content="",
        knowledge_packet="",
        wiki_manifest={},
        implementation_map={},
        writer="codex",
        module_dir=tmp_path,
    )

    assert captured["framing_rules"]
    assert ":::primary-reading" in captured["framing_rules"]
    assert "quote verbatim, never normalize archaic forms" in captured["framing_rules"]
    assert v7_build._iterative_writer_framing_rules(_folk_plan(), "single_shot") == ""


def test_iterative_folk_section_prompt_includes_primary_reading_rules() -> None:
    plan = _folk_plan()
    framing_rules = v7_build._iterative_writer_framing_rules(plan, "iterative")
    tasks = linear_pipeline.build_section_tasks(
        plan,
        "knowledge packet",
        plan["readings"],
        reading_section_map=plan["reading_section_map"],
        framing_rules=framing_rules,
    )

    prompt = linear_pipeline.render_section_writer_prompt(
        plan=plan,
        task=tasks[0],
        knowledge_packet="knowledge packet",
        readings=plan["readings"],
    )

    assert ":::primary-reading" in prompt
    assert "quote verbatim" in prompt
    assert "never normalize archaic forms" in prompt


def test_targeted_correction_rebuilds_tasks_with_folk_framing_rules(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    plan = _folk_plan()
    plan["content_outline"][1]["words"] = 4
    framing_rules = v7_build._iterative_writer_framing_rules(plan, "iterative")
    module_dir = tmp_path / "module"
    _write_iterative_module(module_dir)
    captured_rules: list[str] = []
    prompts: list[str] = []
    original_build_section_tasks = linear_pipeline.build_section_tasks

    def spy_build_section_tasks(*args: Any, **kwargs: Any) -> list[linear_pipeline.SectionTask]:
        captured_rules.append(kwargs.get("framing_rules", ""))
        return original_build_section_tasks(*args, **kwargs)

    def invoke_fn(prompt: str, writer: str, **_kwargs: Any) -> str:
        assert writer == "codex"
        prompts.append(prompt)
        return _section_response(
            "s1",
            "one two three four five six seven eight nine ten eleven twelve.",
        )

    monkeypatch.setattr(linear_pipeline, "plan_check", lambda _path: plan)
    monkeypatch.setattr(linear_pipeline, "build_section_tasks", spy_build_section_tasks)

    handled, _unmatched, payload = linear_pipeline._apply_iterative_targeted_section_correction(
        "word_count",
        {"gates": {"word_count": {"passed": False, "count": 7, "target": 120}}},
        module_dir=module_dir,
        plan_path=tmp_path / "plan.yaml",
        writer="codex",
        invoke_fn=invoke_fn,
        section_attempts={},
        framing_rules=framing_rules,
    )

    assert handled is True
    assert payload["selected_section_ids"] == ["s1"]
    assert captured_rules == [framing_rules]
    assert captured_rules[0]
    assert ":::primary-reading" in prompts[0]
    assert "never normalize archaic forms" in prompts[0]
