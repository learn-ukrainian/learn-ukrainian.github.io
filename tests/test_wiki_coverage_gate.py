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


def test_parse_implementation_map_collects_all_blocks_and_inline_format() -> None:
    """The writer-prompt template nests `<implementation_map>` inside each
    `<plan_reasoning>` section block — typically 4 blocks per module.
    Parser MUST collect entries from ALL blocks, not just the first.

    AND the writer (notably claude-tools) commonly emits all fields on
    ONE line separated by `;`, not the prompt's example multi-line shape.
    Parser MUST accept BOTH the inline-semicolon and the multi-line
    bullet shape.

    Surfaced 2026-05-17 by a1/m20 build #14: writer correctly emitted
    4 implementation_map blocks with all 18 obligations covered, but the
    parser only saw the first block's 3 obligation_ids and dropped their
    artifact/location/treatment fields because they were inline on the
    same line. Result: 0/18 coverage, gate REJECT, despite a clean
    writer output.
    """
    raw = """
<plan_reasoning section="Діалоги">
<implementation_map>
- obligation_id: step-2; artifact: module.md; location: §Діалоги Dialog 1; treatment: reflexive verbs introduced in dialogue.
- obligation_id: err-1; artifact: module.md; location: §Діалоги closing; treatment: я prokidayusya vs ты prokidaeshsya contrast.
</implementation_map>
</plan_reasoning>

<plan_reasoning section="Дієслова на -ся">
<implementation_map>
- obligation_id: step-1; artifact: module.md; location: §Дієслова opening sentence; treatment: explicit I-conjugation endings.
- obligation_id: phon-1; artifact: module.md; location: §Дієслова IPA paragraph; treatment: -шся to [s:a] pair with example.
</implementation_map>
</plan_reasoning>

<plan_reasoning section="Підсумок">
<implementation_map>
- obligation_id: err-5
  artifact: module.md
  location: §Підсумок row 5
  treatment: дивюся to дивлюся with epenthetic l
</implementation_map>
</plan_reasoning>
"""
    result = parse_implementation_map(raw)

    # All 5 obligation_ids from across the 3 blocks must be present, each
    # with its artifact/location/treatment populated.
    assert set(result.keys()) == {"step-2", "err-1", "step-1", "phon-1", "err-5"}
    assert result["step-2"]["artifact"] == "module.md"
    assert result["step-2"]["location"] == "§Діалоги Dialog 1"
    assert "reflexive verbs" in result["step-2"]["treatment"]
    # Multi-line bullet shape (err-5) also parsed correctly.
    assert result["err-5"]["artifact"] == "module.md"
    assert result["err-5"]["location"] == "§Підсумок row 5"
    assert "epenthetic" in result["err-5"]["treatment"]


def test_parse_implementation_map_inline_field_order_independence() -> None:
    """Inline-format fields appear in any order on the line; parser must
    not assume `obligation_id` comes first or that `artifact` precedes
    `location`."""
    raw = """<implementation_map>
- artifact: activities.yaml; obligation_id: phon-3; treatment: phonetic explanation; location: act-3
- treatment: ban explanation; obligation_id: ban-1; location: §Підсумок; artifact: module.md
</implementation_map>"""

    result = parse_implementation_map(raw)

    assert result["phon-3"]["artifact"] == "activities.yaml"
    assert result["phon-3"]["location"] == "act-3"
    assert result["ban-1"]["artifact"] == "module.md"
    assert result["ban-1"]["location"] == "§Підсумок"


def test_parse_implementation_map_inline_pipe_separator_accepted() -> None:
    """Build-#9 a1/my-morning regression: the writer-prompt template
    describes the artifact field as `<module.md | activities.yaml | ...>`
    (pipes denote alternatives), and the writer copied the `|` pattern
    as a field separator across all four implementation_map fields:

        - obligation_id: step-1 | artifact: module.md | location: §... | treatment: ...

    Parser originally accepted only `;` as separator, so `artifact` ate
    the rest of the line and every obligation returned `unknown_artifact`
    with coverage stuck at 0/18. Accept pipe-with-spaces as alternative
    separator (alongside semicolons) so this writer shape parses cleanly."""
    raw = """<implementation_map>
- obligation_id: step-1 | artifact: module.md | location: §Дієслова на -ся | treatment: H3 step marker
- obligation_id: err-2 | artifact: activities.yaml | location: act-5 item 2 | treatment: contrast_pair
</implementation_map>"""

    result = parse_implementation_map(raw)

    assert result["step-1"]["artifact"] == "module.md"
    assert result["step-1"]["location"] == "§Дієслова на -ся"
    assert result["step-1"]["treatment"] == "H3 step marker"
    assert result["err-2"]["artifact"] == "activities.yaml"
    assert result["err-2"]["location"] == "act-5 item 2"
    assert result["err-2"]["treatment"] == "contrast_pair"


def test_parse_implementation_map_last_emission_wins() -> None:
    """If the writer restates an obligation in a later section block with
    a different artifact/location, the LATER claim wins. Mirrors writer
    intent — the second mention is usually a refinement."""
    raw = """<implementation_map>
- obligation_id: step-5; artifact: module.md; location: §Діалоги; treatment: initial mention
</implementation_map>

<implementation_map>
- obligation_id: step-5; artifact: module.md; location: §Мій ранок; treatment: full narrative coverage
</implementation_map>"""

    result = parse_implementation_map(raw)

    assert result["step-5"]["location"] == "§Мій ранок"
    assert result["step-5"]["treatment"] == "full narrative coverage"


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
