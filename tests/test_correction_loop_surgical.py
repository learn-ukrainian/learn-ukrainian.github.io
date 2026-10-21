from __future__ import annotations

import yaml

from scripts.build import linear_pipeline


def test_plan_section_gate_matches_stressed_headings() -> None:
    plan = {"content_outline": [{"section": "Діалоги", "words": 20}]}
    report = linear_pipeline._section_gate(
        "# Мій ранок\n\n## Діало́ги\n\nЛіна прокидається рано. Потім вона вмивається.\n",
        plan,
    )

    assert report["passed"] is True
    assert report["missing_headings"] == []
    assert report["duplicate_headings"] == []
    assert report["word_budgets"][0]["count"] > 0


def test_plan_section_gate_rejects_stress_equivalent_duplicate_headings() -> None:
    plan = {"content_outline": [{"section": "Діалоги", "words": 20}]}
    report = linear_pipeline._section_gate(
        "# Мій ранок\n\n"
        "## Діало́ги\n\n"
        "Ліна прокидається рано.\n\n"
        "## Діалоги\n\n"
        "Настя прокидається пізно.\n",
        plan,
    )

    assert report["passed"] is False
    assert report["missing_headings"] == []
    assert report["duplicate_headings"] == [
        {"section": "Діалоги", "headings": ["Діало́ги", "Діалоги"], "count": 2}
    ]


def test_plan_section_gate_deduplicates_plan_section_diagnostics() -> None:
    plan = {
        "content_outline": [
            {"section": "Діалоги", "words": 20},
            {"section": "Діало́ги", "words": 20},
        ]
    }
    report = linear_pipeline._section_gate("# Мій ранок\n\n## Підсумок\n\nТекст.\n", plan)

    assert report["passed"] is False
    assert report["missing_headings"] == ["Діалоги"]
    assert report["duplicate_headings"] == []


def test_wiki_coverage_yaml_insert_starts_on_own_line(tmp_path) -> None:
    module_dir = tmp_path
    activities_path = module_dir / "activities.yaml"
    activities_path.write_text(
        "- type: error-correction\n"
        "  items:\n"
        "  - sentence: Виправ рядок.\n"
        "    error: Я мию себе.\n"
        "    correction: Я миюся. / Я вмиваюся.\n",
        encoding="utf-8",
    )

    applied = linear_pipeline._apply_wiki_coverage_fixes(
        module_dir=module_dir,
        artifact="activities.yaml",
        fixes=[
            {
                "insert_after": "    correction: Я миюся. / Я вмиваюся.",
                "text": "    implementation_map:\n"
                "    - obligation_id: err-4\n"
                "      artifact: activities.yaml\n"
                "      location: error-correction\n"
                "      treatment: contrast_pair",
            }
        ],
        phase="test",
        iteration=1,
        event_sink=None,
    )

    parsed = yaml.safe_load(activities_path.read_text(encoding="utf-8"))
    assert applied == 1
    assert parsed[0]["items"][0]["implementation_map"][0]["obligation_id"] == "err-4"


def test_wiki_coverage_yaml_insert_handles_ipa_apostrophe_anchor(tmp_path) -> None:
    module_dir = tmp_path
    activities_path = module_dir / "activities.yaml"
    anchor = (
        "  - sentence: Виправ вимову.\n"
        "    error: 'Вимова: [прокидайешся]'\n"
        "    correction: 'Вимова: [прокидайес'':а]'"
    )
    activities_path.write_text(
        "- type: error-correction\n"
        "  items:\n"
        f"{anchor}\n",
        encoding="utf-8",
    )

    applied = linear_pipeline._apply_wiki_coverage_fixes(
        module_dir=module_dir,
        artifact="activities.yaml",
        fixes=[
            {
                "insert_after": anchor,
                "text": "    implementation_map:\n"
                "    - obligation_id: err-2\n"
                "      artifact: activities.yaml\n"
                "      location: activities.yaml\n"
                "      treatment: contrast_pair",
            }
        ],
        phase="test",
        iteration=1,
        event_sink=None,
    )

    parsed = yaml.safe_load(activities_path.read_text(encoding="utf-8"))
    assert applied == 1
    assert parsed[0]["items"][0]["correction"] == "Вимова: [прокидайес':а]"
    assert parsed[0]["items"][0]["implementation_map"][0]["obligation_id"] == "err-2"
