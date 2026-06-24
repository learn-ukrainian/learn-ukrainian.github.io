from __future__ import annotations

import json

import yaml

from scripts.build import linear_pipeline, v7_build


def _fixture_plan() -> dict:
    return {
        "content_outline": [
            {
                "title": "Вступ",
                "words": 120,
                "points": ["Frame the topic.", "Name the first source."],
            },
            {
                "title": "Дискусія",
                "words": 180,
                "points": ["Compare interpretations.", "Reserve practice for the workbook."],
            },
        ],
        "level": "a1",
        "sequence": 1,
        "slug": "iterative-fixture",
        "title": "Iterative Fixture",
        "references": [
            {
                "title": "Course packet",
                "role": "textbook",
                "notes": "Used for deterministic assembly tests.",
            }
        ],
        "readings": [
            {
                "title": "Primary One",
                "reading_slug": "reading-one",
                "author": "Author A",
            }
        ],
        "activity_configs": [
            {
                "id": "act-perform",
                "type": "performance",
                "title": "Read aloud",
                "prompt": "Read the primary passage aloud.",
                "self_check": "I used the quoted passage.",
            },
            {
                "id": "act-workbook",
                "type": "quiz",
                "title": "Check meaning",
                "items": [],
            },
        ],
    }


def _section_response(
    section_id: str,
    markdown: str,
    *,
    citations: list[str] | None = None,
    readings: list[str] | None = None,
    vocab: list[dict] | None = None,
    activities: list[str] | None = None,
    claims: list[str] | None = None,
) -> str:
    metadata = {
        "section_id": section_id,
        "citations_used": citations or [],
        "primary_readings_used": readings or [],
        "vocab_candidates": vocab or [],
        "activity_refs": activities or [],
        "self_check": {
            "claims_made": claims or [f"claim-{section_id}"],
            "points_covered": True,
            "readings_embedded": True,
        },
    }
    return f"<!-- SECTION-ARTIFACT {json.dumps(metadata, ensure_ascii=False)} -->\n{markdown}"


def _stub_artifact(
    section_id: str,
    markdown: str,
    *,
    citations: list[str] | None = None,
    readings: list[str] | None = None,
    vocab: list[dict] | None = None,
    activities: list[str] | None = None,
) -> linear_pipeline.SectionArtifact:
    return linear_pipeline.SectionArtifact(
        section_id=section_id,
        markdown=markdown,
        citations_used=citations or [],
        primary_readings_used=readings or [],
        vocab_candidates=vocab or [],
        activity_refs=activities or [],
        self_check={
            "word_count": 20,
            "points_covered": [True],
            "readings_embedded": [True],
            "ok": True,
            "claims_made": [f"claim-{section_id}"],
        },
    )


def test_build_section_tasks_from_outline_and_assigns_readings() -> None:
    readings = [
        {
            "reading_id": "reading-one",
            "title": "Primary One",
            "author": "Author A",
            "verbatim_text": "Quote one",
            "chunk_id": "chunk-1",
            "verify_quote_conf": 0.99,
        },
        {
            "reading_id": "reading-two",
            "title": "Primary Two",
            "author": "Author B",
            "verbatim_text": "Quote two",
            "chunk_id": "chunk-2",
            "verify_quote_conf": 0.92,
        },
    ]

    tasks = linear_pipeline.build_section_tasks(
        _fixture_plan(),
        "Вступ evidence line.\nДискусія evidence line.",
        readings,
        reading_section_map={"reading-two": "s2"},
        framing_rules="shared rules",
    )

    assert [task.section_id for task in tasks] == ["s1", "s2"]
    assert [task.title for task in tasks] == ["Вступ", "Дискусія"]
    assert [task.word_budget for task in tasks] == [120, 180]
    assert tasks[0].points == ["Frame the topic.", "Name the first source."]
    assert [reading["reading_id"] for reading in tasks[0].assigned_readings] == ["reading-one"]
    assert [reading["reading_id"] for reading in tasks[1].assigned_readings] == ["reading-two"]
    assert "Вступ evidence line." in tasks[0].knowledge_slice
    assert "Дискусія evidence line." in tasks[1].knowledge_slice
    assert tasks[0].framing_rules == "shared rules"
    assert tasks[0].ledger == linear_pipeline.Ledger()


def test_build_section_tasks_without_map_assigns_all_readings_to_default_section() -> None:
    tasks = linear_pipeline.build_section_tasks(
        _fixture_plan(),
        "",
        [{"reading_id": "reading-one"}, {"reading_id": "reading-two"}],
        default_reading_section_id="s2",
    )

    assert tasks[0].assigned_readings == []
    assert [reading["reading_id"] for reading in tasks[1].assigned_readings] == [
        "reading-one",
        "reading-two",
    ]


def test_update_ledger_accumulates_artifact_state_without_mutating_input() -> None:
    ledger = linear_pipeline.Ledger(
        claims_made=["existing claim"],
        citations_consumed=["cite-old"],
        readings_consumed=["reading-old"],
        vocab_introduced=["слово"],
        activities_assigned=["act-old"],
        reserved_for_later=["later topic"],
    )
    artifact = _stub_artifact(
        "s1",
        "## Вступ\n\nA one-line gist.\n\n:::primary-reading\n> quote\n:::\n",
        citations=["cite-old", "cite-new"],
        readings=["reading-old", "reading-new"],
        vocab=[
            {"surface": "слово", "gloss": "word"},
            {"surface": "ранок", "gloss": "morning"},
        ],
        activities=["act-old", "act-new"],
    )

    updated = linear_pipeline.update_ledger(ledger, artifact)

    assert ledger.sections_done == []
    assert updated.sections_done == [
        {"section_id": "s1", "title": "Вступ", "one_line_gist": "A one-line gist."}
    ]
    assert updated.claims_made == ["existing claim", "claim-s1"]
    assert updated.citations_consumed == ["cite-old", "cite-new"]
    assert updated.readings_consumed == ["reading-old", "reading-new"]
    assert updated.vocab_introduced == ["слово", "ранок"]
    assert updated.activities_assigned == ["act-old", "act-new"]
    assert updated.reserved_for_later == ["later topic"]


def test_assemble_iterative_outputs_ordered_artifacts_and_valid_yaml() -> None:
    s1 = _stub_artifact(
        "s1",
        "\n".join(
            [
                "## Вступ",
                "Opening line.",
                ':::primary-reading reading="reading-one"',
                "> quoted source",
                ":::",
                "<!-- INJECT_ACTIVITY: act-perform -->",
            ]
        ),
        citations=["packet-1"],
        readings=["reading-one"],
        vocab=[
            {"surface": "ранок", "gloss": "morning", "note": "Used in the opening."},
            {"surface": "слово", "gloss": "word"},
        ],
        activities=["act-perform"],
    )
    s2 = _stub_artifact(
        "s2",
        "\n".join(
            [
                "## Дискусія",
                "Discussion line.",
                "<!-- INJECT_ACTIVITY: act-workbook -->",
            ]
        ),
        citations=["packet-2"],
        vocab=[
            {"surface": "Ранок", "gloss": "morning duplicate"},
            {"surface": "вечір", "gloss": "evening"},
        ],
        activities=["act-workbook"],
    )

    assembled = linear_pipeline.assemble_iterative([s2, s1], _fixture_plan())

    module_lines = assembled["module_md"].splitlines()
    assert module_lines[0] == "## Вступ"
    assert assembled["sidecar"]["s1"]["line_start"] == 1
    assert module_lines[assembled["sidecar"]["s2"]["line_start"] - 1] == "## Дискусія"
    assert assembled["sidecar"]["s1"] == {
        "line_start": 1,
        "line_end": 6,
        "reading_ids": ["reading-one"],
        "citation_keys": ["packet-1"],
        "vocab_surfaces": ["ранок", "слово"],
        "activity_ids": ["act-perform"],
        "self_check": {
            "word_count": 20,
            "points_covered": [True],
            "readings_embedded": [True],
            "ok": True,
            "claims_made": ["claim-s1"],
        },
    }
    assert assembled["sidecar"]["s2"]["citation_keys"] == ["packet-2"]

    vocabulary = yaml.safe_load(assembled["vocabulary_yaml"])
    assert [item["lemma"] for item in vocabulary] == ["ранок", "слово", "вечір"]
    linear_pipeline._validate_writer_json_artifact("vocabulary.yaml", vocabulary)

    activities = yaml.safe_load(assembled["activities_yaml"])
    assert isinstance(activities, list)
    assert activities[0]["type"] == "performance"
    assert activities[0]["self_check"] == ["I used the quoted passage."]
    linear_pipeline._validate_writer_json_artifact("activities.yaml", activities)
    assert assembled["sidecar"]["s2"]["line_start"] == 8
    assert module_lines[assembled["sidecar"]["s2"]["line_end"] - 1] == "<!-- INJECT_ACTIVITY: act-workbook -->"
    assert linear_pipeline._activity_schema_gate(activities)["passed"] is True

    resources = yaml.safe_load(assembled["resources_yaml"])
    assert {resource["title"] for resource in resources} == {"Course packet", "Primary One"}
    linear_pipeline._validate_writer_json_artifact("resources.yaml", resources)


def test_render_section_writer_prompt_includes_section_contract_and_ledger() -> None:
    task = linear_pipeline.build_section_tasks(
        _fixture_plan(),
        "Вступ evidence line.\nДискусія evidence line.",
        _fixture_plan()["readings"],
    )[0]
    task = linear_pipeline.SectionTask(
        section_id=task.section_id,
        title=task.title,
        word_budget=task.word_budget,
        points=task.points,
        assigned_readings=task.assigned_readings,
        knowledge_slice=task.knowledge_slice,
        framing_rules="Avoid repetition.",
        ledger=linear_pipeline.Ledger(
            sections_done=[
                {
                    "section_id": "s0",
                    "title": "Попереднє",
                    "one_line_gist": "Already covered section gist.",
                }
            ],
            claims_made=["prior claim"],
        ),
    )

    prompt = linear_pipeline.render_section_writer_prompt(
        plan=_fixture_plan(),
        task=task,
        knowledge_packet="Вступ evidence line.",
        readings=_fixture_plan()["readings"],
        writer="claude-tools",
    )

    assert "word_budget: 120" in prompt
    assert "Frame the topic." in prompt
    assert "reading-one" in prompt
    assert "Вступ evidence line." in prompt
    assert "Already covered section gist." in prompt
    assert "Anti-Repetition" in prompt
    assert "SELF-CHECK" in prompt
    assert "word floor" in prompt
    assert "points covered" in prompt
    assert "readings embedded" in prompt


def test_run_iterative_writer_uses_stub_writer_and_accumulates_ledger() -> None:
    prompts: list[str] = []

    def invoke_stub(prompt: str, writer: str, **kwargs: object) -> str:
        del writer, kwargs
        prompts.append(prompt)
        if "## Section\n- section_id: s1\n" in prompt:
            return _section_response(
                "s1",
                "\n".join(
                    [
                        "## Вступ",
                        "Opening gist for ledger.",
                        "reading-one is embedded here.",
                        "<!-- INJECT_ACTIVITY: act-perform -->",
                    ]
                ),
                citations=["packet-1"],
                readings=["reading-one"],
                vocab=[{"surface": "ранок", "gloss": "morning"}],
                activities=["act-perform"],
            )
        return _section_response(
            "s2",
            "\n".join(["## Дискусія", "Discussion follows the opening gist."]),
            citations=["packet-2"],
            vocab=[
                {"surface": "ранок", "gloss": "morning"},
                {"surface": "вечір", "gloss": "evening"},
            ],
            activities=["act-workbook"],
        )

    result = linear_pipeline.run_iterative_writer(
        _fixture_plan(),
        "Вступ evidence line.\nДискусія evidence line.",
        _fixture_plan()["readings"],
        writer="stub-writer",
        invoke_fn=invoke_stub,
    )

    assert len(prompts) == 2
    assert "Opening gist for ledger." in prompts[1]
    assert result["module_md"].index("## Вступ") < result["module_md"].index("## Дискусія")
    assert set(result) == {
        "module_md",
        "vocabulary_yaml",
        "activities_yaml",
        "resources_yaml",
        "sidecar",
    }
    assert result["sidecar"]["s1"]["self_check"]["precheck"]["word_floor"]["passed"] is False
    vocabulary = yaml.safe_load(result["vocabulary_yaml"])
    assert [item["lemma"] for item in vocabulary] == ["ранок", "вечір"]
    writer_artifacts = linear_pipeline.iterative_result_to_writer_artifacts(result)
    assert tuple(writer_artifacts) == linear_pipeline.WRITER_ARTIFACTS


def test_writer_mode_flag_defaults_to_single_shot() -> None:
    assert v7_build._writer_mode_from_env({}) == "single_shot"
    assert v7_build._writer_mode_from_env({"WRITER_MODE": "single-shot"}) == "single_shot"
    assert v7_build._writer_mode_from_env({"WRITER_MODE": "iterative"}) == "iterative"


def test_v7_single_shot_writer_mode_uses_existing_invoke(monkeypatch, tmp_path) -> None:
    calls: list[tuple[str, str]] = []

    def prompt_stub(**kwargs: object) -> str:
        del kwargs
        return "single-shot prompt"

    def invoke_stub(prompt: str, writer: str, **kwargs: object) -> str:
        del kwargs
        calls.append((prompt, writer))
        return "single-shot output"

    monkeypatch.setattr(v7_build, "_writer_prompt", prompt_stub)
    monkeypatch.setattr(linear_pipeline, "invoke_writer", invoke_stub)

    prompt, writer_output, iterative_result = v7_build._run_writer_mode(
        writer_mode="single_shot",
        plan=_fixture_plan(),
        plan_content="plan content",
        knowledge_packet="knowledge",
        wiki_manifest="{}",
        implementation_map={},
        writer="claude-tools",
        module_dir=tmp_path,
    )

    assert prompt == "single-shot prompt"
    assert writer_output == "single-shot output"
    assert iterative_result is None
    assert calls == [("single-shot prompt", "claude-tools")]


def test_v7_iterative_writer_mode_reaches_run_iterative_writer(monkeypatch, tmp_path) -> None:
    calls: list[dict[str, object]] = []

    def iterative_stub(
        plan: dict,
        knowledge_packet: str,
        readings: list[dict],
        **kwargs: object,
    ) -> dict:
        calls.append(
            {
                "plan": plan,
                "knowledge_packet": knowledge_packet,
                "readings": readings,
                "writer": kwargs["writer"],
            }
        )
        return {
            "module_md": "## Вступ\n\nBody\n",
            "vocabulary_yaml": "[]\n",
            "activities_yaml": "[]\n",
            "resources_yaml": "[]\n",
            "sidecar": {
                "s1": {
                    "line_start": 1,
                    "line_end": 3,
                    "self_check": {},
                }
            },
        }

    monkeypatch.setattr(linear_pipeline, "run_iterative_writer", iterative_stub)

    prompt, writer_output, iterative_result = v7_build._run_writer_mode(
        writer_mode="iterative",
        plan=_fixture_plan(),
        plan_content="plan content",
        knowledge_packet="knowledge",
        wiki_manifest="{}",
        implementation_map={},
        writer="claude-tools",
        module_dir=tmp_path,
    )

    assert calls and calls[0]["writer"] == "claude-tools"
    assert iterative_result is not None
    assert iterative_result["sidecar"]["s1"]["line_start"] == 1
    assert "render_section_writer_prompt" in prompt
    assert "```markdown file=module.md" in writer_output
