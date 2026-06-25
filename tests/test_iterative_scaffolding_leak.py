from __future__ import annotations

from typing import Any

from scripts.build import linear_pipeline


def _plan() -> dict[str, Any]:
    return {
        "level": "folk",
        "sequence": 1,
        "module": 1,
        "slug": "vesnianky-hayivky",
        "title": "Веснянки й гаївки",
        "content_outline": [
            {
                "section": "Корпус і контекст",
                "words": 20,
                "points": ["Anchor analysis in attested spring-song lines."],
            }
        ],
    }


def _artifact(markdown: str) -> linear_pipeline.SectionArtifact:
    return linear_pipeline.SectionArtifact(
        section_id="s1",
        markdown=markdown,
        citations_used=[],
        primary_readings_used=[],
        vocab_candidates=[],
        activity_refs=[],
        self_check={},
    )


def test_assemble_iterative_strips_source_markers_and_metadata_lines() -> None:
    result = linear_pipeline.assemble_iterative(
        [
            _artifact(
                "\n".join(
                    [
                        "Веснянкова строфа подана як корпусний приклад [S4].",
                        'truth_source: "Сучасна фольклористика; vesnianky-hayivky.md [S4]"',
                        "У прозі лишається природна атрибуція до корпусу.",
                    ]
                )
            )
        ],
        _plan(),
        activities=[],
    )

    module_md = str(result["module_md"])

    assert "[S4]" not in module_md
    assert "truth_source:" not in module_md
    assert "Веснянкова строфа подана як корпусний приклад." in module_md
    assert "У прозі лишається природна атрибуція до корпусу." in module_md
    assert linear_pipeline._scaffolding_leak_gate(module_md)["passed"] is True


def test_assemble_iterative_strips_source_markers_inside_primary_reading_blocks() -> None:
    primary_reading = "\n".join(
        [
            ":::primary-reading",
            "> Ой весна, весна, днем красна... [S4]",
            'truth_source: "kept because this line is inside the quoted block"',
            ":::",
        ]
    )

    result = linear_pipeline.assemble_iterative(
        [_artifact(f"Пояснення має зайвий маркер [S3].\n\n{primary_reading}")],
        _plan(),
        activities=[],
    )

    module_md = str(result["module_md"])

    assert "> Ой весна, весна, днем красна..." in module_md
    assert 'truth_source: "kept because this line is inside the quoted block"' in module_md
    assert "[S4]" not in module_md
    assert "Пояснення має зайвий маркер." in module_md


def test_assemble_iterative_leaves_core_sections_unchanged() -> None:
    plan = _plan()
    plan["level"] = "a1"

    result = linear_pipeline.assemble_iterative(
        [
            _artifact(
                "\n".join(
                    [
                        "Core prose keeps its prior assembly behavior [S4].",
                        'truth_source: "unchanged outside seminar/FOLK"',
                    ]
                )
            )
        ],
        plan,
        activities=[],
    )

    module_md = str(result["module_md"])

    assert "[S4]" in module_md
    assert 'truth_source: "unchanged outside seminar/FOLK"' in module_md


def test_render_section_writer_prompt_marks_scaffolding_internal() -> None:
    task = linear_pipeline.SectionTask(
        section_id="s1",
        title="Корпус і контекст",
        word_budget=20,
        points=["Anchor analysis in attested spring-song lines."],
        assigned_readings=[],
        knowledge_slice="",
        framing_rules=":::primary-reading\n> Ой весна... [S4]\n:::",
        ledger=linear_pipeline.Ledger(),
    )

    prompt = linear_pipeline.render_section_writer_prompt(
        plan=_plan(),
        task=task,
        knowledge_packet="",
        readings=[],
    )

    assert "[S#]`/`[С#]` source markers" in prompt
    assert "Never print them in published `section.md` prose" in prompt
    assert "`truth_source:`" in prompt


def test_render_section_writer_prompt_leaves_core_prompt_unchanged() -> None:
    plan = _plan()
    plan["level"] = "a1"
    task = linear_pipeline.SectionTask(
        section_id="s1",
        title="Корпус і контекст",
        word_budget=20,
        points=["Anchor analysis in attested spring-song lines."],
        assigned_readings=[],
        knowledge_slice="",
        framing_rules="",
        ledger=linear_pipeline.Ledger(),
    )

    prompt = linear_pipeline.render_section_writer_prompt(
        plan=plan,
        task=task,
        knowledge_packet="",
        readings=[],
    )

    assert "[S#]`/`[С#]` source markers" not in prompt
