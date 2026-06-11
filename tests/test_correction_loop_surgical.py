from __future__ import annotations

import pytest
import yaml

from scripts.build import linear_pipeline


def test_vesum_correction_prompt_uses_token_surgical_instruction() -> None:
    prompt = linear_pipeline.render_writer_correction_prompt(
        gate="vesum_verified",
        gate_report={"passed": False, "missing": ["що́стій"], "missing_count": 1},
        module_text="## Діалоги\n\nЛіна прокидається о що́стій.\n",
    )

    assert "tokens FAILED VESUM verification" in prompt
    assert "що́стій" in prompt
    assert "wrap EVERY occurrence" in prompt
    assert "instead of inventing a VESUM-looking replacement" in prompt
    assert "Do NOT modify any other word" in prompt
    assert "Do NOT replace any word that is not explicitly listed" in prompt


def test_word_count_correction_prompt_is_append_only() -> None:
    prompt = linear_pipeline.render_writer_correction_prompt(
        gate="word_count",
        gate_report={
            "passed": False,
            "count": 1000,
            "target": 1200,
            "min_with_tolerance": 1104,
        },
        module_text="## Підсумок\n\nКороткий текст.\n",
    )

    assert "Current: 1000 words" in prompt
    assert "Delta to floor: 104 words" in prompt
    assert "one concise paragraph" in prompt
    assert "ONLY append" in prompt


def test_large_word_count_correction_prompt_uses_multi_paragraph_append() -> None:
    prompt = linear_pipeline.render_writer_correction_prompt(
        gate="word_count",
        gate_report={
            "passed": False,
            "count": 2847,
            "target": 4000,
            "min_with_tolerance": 3680,
        },
        module_text="## Підсумок\n\nКороткий текст.\n",
    )

    assert "Delta to floor: 833 words" in prompt
    assert "multiple short paragraphs" in prompt
    assert "within the module's level limit" in prompt
    assert "2-3 sentences" not in prompt


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


def test_plan_section_gate_accepts_a1_script_building_english_headings() -> None:
    plan = {
        "level": "A1",
        "sequence": 2,
        "content_outline": [
            {"section": "Склади", "words": 20},
            {"section": "Голосні літери", "words": 20},
            {"section": "Читання слів", "words": 20},
            {"section": "Підсумок", "words": 20},
        ],
    }
    report = linear_pipeline._section_gate(
        "# Reading Ukrainian\n\n"
        "## Syllables\n\nCount the vowel sounds first.\n\n"
        "## Vowel Letters\n\nRead the clean vowels aloud.\n\n"
        "## Reading Words\n\nBuild from syllables into words.\n\n"
        "## Textbook Check\n\nCheck that you can read the sample words.\n",
        plan,
    )

    assert report["passed"] is True
    assert report["missing_headings"] == []
    assert report["archetype"] == "a1-script-building"


def test_section_heading_key_preserves_falsy_non_none_titles() -> None:
    assert linear_pipeline._section_heading_key(0) == "0"


def test_plan_sections_correction_prompt_allows_duplicate_structural_edit() -> None:
    prompt = linear_pipeline.render_writer_correction_prompt(
        gate="plan_sections",
        gate_report={
            "passed": False,
            "missing_headings": [],
            "duplicate_headings": [
                {"section": "Діалоги", "headings": ["Діало́ги", "Діалоги"], "count": 2}
            ],
        },
        module_text="# Мій ранок\n\n## Діало́ги\n\nТекст.\n\n## Діалоги\n\nТекст.\n",
    )

    assert "Duplicate stress-equivalent H2 sections" in prompt
    assert "keep exactly one `##` heading" in prompt
    assert "demote supporting duplicate blocks to `###`" in prompt
    assert "delete an empty/redundant duplicate H2 block" in prompt
    assert "structural edit needed for the failed gate" in prompt
    assert "No gate-specific surgical playbook exists" not in prompt


def test_plan_sections_correction_prompt_directs_missing_heading_insert() -> None:
    prompt = linear_pipeline.render_writer_correction_prompt(
        gate="plan_sections",
        gate_report={
            "passed": False,
            "missing_headings": ["Підсумок"],
            "duplicate_headings": [],
        },
        module_text="# Мій ранок\n\n## Діалоги\n\nТекст.\n",
    )

    assert "Missing H2 sections: Підсумок" in prompt
    assert "Add each missing `## <section>` heading" in prompt
    assert "No gate-specific surgical playbook exists" not in prompt


def test_unhandled_correction_gate_uses_generic_surgical_fallback() -> None:
    prompt = linear_pipeline.render_writer_correction_prompt(
        gate="textbook_grounding",
        gate_report={"passed": False, "reason": "missing_quote"},
        module_text="## Джерела\n\nПоточний текст.\n",
    )

    assert "No gate-specific surgical playbook exists for this gate" in prompt
    assert "preserve previously-passing prose byte-for-byte" in prompt


@pytest.mark.parametrize(
    ("gate", "gate_report", "expected"),
    [
        (
            "vesum_verified",
            {"passed": False, "missing": ["що́стій"]},
            "tokens FAILED VESUM verification",
        ),
        (
            "word_count",
            {"passed": False, "count": 1000, "target": 1200, "min_with_tolerance": 1104},
            "ONLY append",
        ),
        (
            "engagement_floor",
            {"passed": False, "callout_count": 0, "callout_min": 1},
            "content-anchored mnemonic or cultural note",
        ),
        (
            "russianisms_strict",
            {"passed": False, "critical_findings": [{"text": "давайте попрактикуємо"}]},
            "Replace EXACTLY these spans",
        ),
        (
            "l2_exposure_floor",
            {
                "passed": False,
                "observed": {"uk_example_sentences": 8},
                "required": {"uk_example_sentences": 12},
            },
            "NEW gate-countable Ukrainian example bullets",
        ),
    ],
)
def test_fixable_gates_render_specific_surgical_instructions(
    gate: str,
    gate_report: dict[str, object],
    expected: str,
) -> None:
    prompt = linear_pipeline.render_writer_correction_prompt(
        gate=gate,
        gate_report=gate_report,
        module_text="## Підсумок\n\nТекст.\n",
    )

    assert expected in prompt


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


def test_wiki_coverage_yaml_replace_quotes_colon_scalar(tmp_path) -> None:
    module_dir = tmp_path
    activities_path = module_dir / "activities.yaml"
    activities_path.write_text(
        "- type: error-correction\n"
        "  items:\n"
        "  - sentence: Дівчина, читаюча роман, сиділа на лавці.\n"
        "    error: читаюча\n"
        "    correction: Дівчина, яка читала роман, сиділа на лавці.\n",
        encoding="utf-8",
    )

    applied = linear_pipeline._apply_wiki_coverage_fixes(
        module_dir=module_dir,
        artifact="activities.yaml",
        fixes=[
            {
                "find": "correction: Дівчина, яка читала роман, сиділа на лавці.",
                "replace": "correction: Дівчина, яка читала роман, сиділа на лавці. "
                "(Або: Читаючи роман, дівчина сиділа на лавці).",
            }
        ],
        phase="test",
        iteration=1,
        event_sink=None,
    )

    text = activities_path.read_text(encoding="utf-8")
    parsed = yaml.safe_load(text)
    assert applied == 1
    assert "correction: 'Дівчина, яка читала роман" in text
    assert parsed[0]["items"][0]["correction"] == (
        "Дівчина, яка читала роман, сиділа на лавці. "
        "(Або: Читаючи роман, дівчина сиділа на лавці)."
    )
