from __future__ import annotations

import yaml

from scripts.build import linear_pipeline


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
    assert linear_pipeline._activity_schema_gate(activities)["passed"] is True

    resources = yaml.safe_load(assembled["resources_yaml"])
    assert {resource["title"] for resource in resources} == {"Course packet", "Primary One"}
    linear_pipeline._validate_writer_json_artifact("resources.yaml", resources)
