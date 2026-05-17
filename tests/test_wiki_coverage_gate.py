from __future__ import annotations

import json

import scripts.audit.wiki_coverage_gate as gate
from scripts.audit.wiki_coverage_gate import check_wiki_coverage, parse_implementation_map


def test_load_manifest_parses_json_blob_without_filesystem_access() -> None:
    """`_load_manifest` must detect a JSON-blob string and parse it
    directly, not pass it through `Path(...).exists()`.

    On macOS APFS, passing a multi-kB JSON string to `Path(...).exists()`
    raises `OSError: [Errno 63] ENAMETOOLONG` instead of returning False,
    crashing the wiki_coverage_gate before the gate logic runs. Linux
    returns False silently for the same input, which is why the bug
    only surfaced on darwin (2026-05-17 m20 build #12 — the first build
    to reach `wiki_coverage_gate` on a developer macOS workstation).

    A JSON blob starts with `{` or `[` after whitespace; that signature
    is the cheapest reliable discriminator.
    """
    # Realistic-shape wiki manifest as produced by build_wiki_manifest.
    manifest = {
        "slug": "my-morning",
        "wiki_path": "/Users/k/projects/learn-ukrainian/wiki/pedagogy/a1/my-morning.md",
        "sequence_steps": [
            {"id": f"step-{i}", "heading": f"Крок {i}: ..."} for i in range(1, 8)
        ],
        "l2_errors": [{"id": f"err-{i}", "incorrect": "X", "correct": "Y"} for i in range(1, 6)],
        "phonetic_rules": [
            {"id": "phon-1", "written": "-шся", "spoken": "[с':а]"}
        ],
        "decolonization_bans": [],
    }
    blob = json.dumps(manifest, ensure_ascii=False, indent=2)
    # Sanity: this blob would explode Path(...).exists() on macOS if not
    # short-circuited.
    assert len(blob) > 255, "fixture too small to reproduce the original bug"

    result = gate._load_manifest(blob)

    assert result == manifest


def test_load_manifest_short_json_blob_also_short_circuits() -> None:
    """Short JSON blobs (under 255 bytes) still take the JSON path so
    behavior is consistent regardless of payload size."""
    short_blob = '{"slug": "test", "sequence_steps": [], "l2_errors": [], "phonetic_rules": [], "decolonization_bans": []}'
    result = gate._load_manifest(short_blob)
    assert result["slug"] == "test"


def test_load_manifest_passes_through_mapping() -> None:
    """Mapping input returns unchanged (no path/JSON detour)."""
    payload = {"slug": "x", "sequence_steps": []}
    assert gate._load_manifest(payload) is payload


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


def test_check_wiki_coverage_hard_fails_missing_phonetic_spoken_target_when_advisory(
    monkeypatch,
) -> None:
    monkeypatch.setattr(gate, "WIKI_COVERAGE_HARD_FAIL", False)

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

    phonetic_failures = [
        item
        for item in report["obligations"]
        if item["category"] == "phonetic_rules" and item["status"] == "FAIL"
    ]
    assert report["passed"] is False
    assert report["hard_fail"] is True
    assert report["phonetic_hard_fail"] is True
    assert phonetic_failures[0]["spoken_target"] == "[с':а]"
    assert phonetic_failures[0]["spoken_present"] is False


def test_check_wiki_coverage_passes_phonetic_rule_with_one_manifest_example_pair() -> None:
    manifest = _manifest()
    manifest["phonetic_rules"][0]["example_pairs"] = [
        {"written": "смієшся", "spoken": "[с'м'ійес':а]"},
        {"written": "вітаєшся", "spoken": "[в'ітайес':а]"},
    ]

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=_implementation_map(),
        module_md=(
            "## Дієслова на -ся\n"
            "The morning pattern uses **прокидатися**, **вмиватися**, and **одягатися**. "
            "The written ending **-шся** is pronounced **[с':а]**. "
            "Example: **смієшся [с'м'ійес':а]**."
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

    phonetic_result = next(item for item in report["obligations"] if item["category"] == "phonetic_rules")
    assert report["passed"] is True
    assert phonetic_result["example_pairs_required"] is True
    assert phonetic_result["example_pairs_present"] is True
