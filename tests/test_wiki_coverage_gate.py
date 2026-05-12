from __future__ import annotations

from scripts.audit.wiki_coverage_gate import check_wiki_coverage, parse_implementation_map


def _manifest() -> dict[str, object]:
    return {
        "slug": "fixture",
        "wiki_path": "wiki/pedagogy/a1/fixture.md",
        "sequence_steps": [
            {
                "id": "step-1",
                "heading": "Крок 1: Reflexive morning verbs",
                "step_num": 1,
                "required_claim": "Teach *прокидатися*, *вмиватися*, and *одягатися* as one routine pattern.",
                "source_lines": "10-12",
            }
        ],
        "l2_errors": [
            {
                "id": "err-1",
                "incorrect": "Я прокидаєшся.",
                "correct": "Я прокидаюся.",
                "why": "The person ending must match я.",
                "treatment": "contrast_pair",
                "source_lines": "20",
            }
        ],
        "phonetic_rules": [
            {
                "id": "phon-1",
                "written": "-шся",
                "spoken": "[с':а]",
                "treatment": "explicit_explanation",
                "source_lines": "30",
            }
        ],
        "decolonization_bans": [],
    }


def _implementation_map() -> dict[str, dict[str, str]]:
    return {
        "step-1": {
            "artifact": "module.md",
            "location": "Дієслова на -ся",
            "treatment": "sequence prose",
        },
        "err-1": {
            "artifact": "activities.yaml",
            "location": "act-1",
            "treatment": "contrast_pair in activity act-1",
        },
        "phon-1": {
            "artifact": "module.md",
            "location": "Дієслова на -ся",
            "treatment": "explicit explanation",
        },
    }


def test_parse_implementation_map_from_writer_output() -> None:
    raw = """<implementation_map>
- obligation_id: err-1
  artifact: activities.yaml
  location: act-1
  treatment: contrast_pair in activity act-1
</implementation_map>"""

    assert parse_implementation_map(raw) == {
        "err-1": {
            "obligation_id": "err-1",
            "artifact": "activities.yaml",
            "location": "act-1",
            "treatment": "contrast_pair in activity act-1",
        }
    }


def test_check_wiki_coverage_passes_when_claimed_evidence_exists() -> None:
    report = check_wiki_coverage(
        manifest=_manifest(),
        implementation_map=_implementation_map(),
        module_md=(
            "## Дієслова на -ся\n"
            "The morning pattern uses **прокидатися**, **вмиватися**, and **одягатися**. "
            "The written ending **-шся** is pronounced **[с':а]**."
        ),
        activities_yaml=(
            "- id: act-1\n"
            "  type: select\n"
            "  items:\n"
            "    - prompt: Choose the correct form.\n"
            "      options: [Я прокидаєшся., Я прокидаюся.]\n"
            "      answer: Я прокидаюся.\n"
        ),
        level="a1",
    )

    assert report["passed"] is True
    assert report["covered"] == 3


def test_check_wiki_coverage_fails_missing_implementation_map_entry() -> None:
    implementation_map = _implementation_map()
    implementation_map.pop("phon-1")

    report = check_wiki_coverage(
        manifest=_manifest(),
        implementation_map=implementation_map,
        module_md="## Дієслова на -ся\nпрокидатися вмиватися одягатися",
        activities_yaml="- id: act-1\n  type: select\n  items: []\n",
        level="a1",
    )

    assert report["passed"] is False
    assert any(item["reason"] == "implementation_map_missing" for item in report["obligations"])


def test_check_wiki_coverage_fails_contrast_pair_without_wrong_form() -> None:
    report = check_wiki_coverage(
        manifest=_manifest(),
        implementation_map=_implementation_map(),
        module_md=(
            "## Дієслова на -ся\n"
            "прокидатися вмиватися одягатися -шся [с':а]"
        ),
        activities_yaml=(
            "- id: act-1\n"
            "  type: select\n"
            "  items:\n"
            "    - prompt: Choose the correct form.\n"
            "      options: [Я прокидаюся.]\n"
            "      answer: Я прокидаюся.\n"
        ),
        level="a1",
    )

    assert report["passed"] is False
    assert any(item["reason"] == "missing_incorrect" for item in report["obligations"])


def test_check_wiki_coverage_fails_missing_phonetic_rule() -> None:
    report = check_wiki_coverage(
        manifest=_manifest(),
        implementation_map=_implementation_map(),
        module_md="## Дієслова на -ся\nпрокидатися вмиватися одягатися -шся",
        activities_yaml=(
            "- id: act-1\n"
            "  type: select\n"
            "  items:\n"
            "    - prompt: Choose the correct form.\n"
            "      options: [Я прокидаєшся., Я прокидаюся.]\n"
            "      answer: Я прокидаюся.\n"
        ),
        level="a1",
    )

    assert report["passed"] is False
    assert any(item["reason"] == "phonetic_rule_missing" for item in report["obligations"])

