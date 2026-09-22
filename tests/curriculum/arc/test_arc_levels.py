"""Tests for the a2/b1/b2 arc generator modes and the immersion band mapping.

Issues #8424 / #8427. The arc documents docs/epics/fresh-build-{a2,b1,b2}-arc.md
are the reviewed source of truth; each curriculum/l2-uk-en/lesson-plans/<level>/_arc.yaml
must stay byte-identical to a fresh run of scripts/curriculum/arc/generate_arc.py.
Mutation tests run the generator against temporary copies of the documents —
the real documents and the committed YAML are never touched.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.arc import generate_arc, loader

pytestmark = [pytest.mark.reads_content]

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "curriculum/l2-uk-en/curriculum.yaml"

# count, first slug, last slug — quoted from the accepted arc documents
LEVELS = {
    "a2": (69, "a2-bridge", "a2-finale"),
    "b1": (94, "b1-baseline-past-present", "practice-exam"),
    "b2": (93, "passive-voice-system", "b2-final-exam"),
}
FIRST_BAND_KEY = {"a2": "a2-bridge", "b1": "b1-core", "b2": "b2+"}

A1_ARC_DOC = REPO_ROOT / "docs/epics/fresh-build-a1-arc.md"
A1_ARC_YAML = REPO_ROOT / "curriculum/l2-uk-en/lesson-plans/a1/_arc.yaml"
# sha256 of the committed A1 _arc.yaml from the "positions:" line to EOF.
# Pinned when `level: a1` was added (#8424): regenerating A1 may add that one
# key and nothing else — the positions block stays byte-identical.
A1_POSITIONS_BLOCK_SHA256 = "2796c271b06e6f8af7ffca50db611adc158e503c119981c815c9c0cd50aa6bdc"


def _doc(level: str) -> Path:
    return REPO_ROOT / f"docs/epics/fresh-build-{level}-arc.md"


def _records(level: str) -> list[dict]:
    return generate_arc.parse_positions(_doc(level).read_text(encoding="utf-8"), level)


def _mutated_doc(level: str, tmp_path: Path, old: str, new: str) -> Path:
    text = _doc(level).read_text(encoding="utf-8")
    assert old in text, f"mutation target not found in the {level} arc document: {old!r}"
    assert text.count(old) == 1, f"mutation target is not unique in the {level} arc document: {old!r}"
    mutated = tmp_path / f"arc-{level}.md"
    mutated.write_text(text.replace(old, new), encoding="utf-8")
    return mutated


@pytest.mark.parametrize("level", sorted(LEVELS))
def test_position_count_and_first_last_slug(level: str) -> None:
    count, first, last = LEVELS[level]
    records = _records(level)
    assert len(records) == count
    assert records[0]["slug"] == first
    assert records[-1]["slug"] == last
    assert [r["position"] for r in records] == list(range(1, count + 1))


@pytest.mark.parametrize("level", sorted(LEVELS))
def test_no_letters_and_null_inventory(level: str) -> None:
    for record in _records(level):
        assert "letters" not in record
        assert record["inventory_text"] is None


@pytest.mark.parametrize("level", sorted(LEVELS))
def test_every_position_has_band_key_with_full_coverage(level: str) -> None:
    data = yaml.safe_load(generate_arc.generate_yaml(_doc(level), level))
    count = LEVELS[level][0]
    covered: list[int] = []
    for band in data["immersion_bands"]:
        assert set(band) == {"start", "end", "band_key"}
        covered.extend(range(band["start"], band["end"] + 1))
    assert covered == list(range(1, count + 1))
    assert all(record["band_key"] for record in data["positions"])
    expanded = {p: band["band_key"] for band in data["immersion_bands"] for p in range(band["start"], band["end"] + 1)}
    assert {r["position"]: r["band_key"] for r in data["positions"]} == expanded


@pytest.mark.parametrize("level", sorted(LEVELS))
def test_check_green(level: str) -> None:
    assert generate_arc.main(["--level", level, "--check"]) == 0


def test_loader_band_keys() -> None:
    for level, band_key in FIRST_BAND_KEY.items():
        positions = loader.load_arc(level)
        assert positions[0].band_key == band_key
        assert all(p.band_key for p in positions)
    assert loader.load_arc("a2")[0].band_key == "a2-bridge"
    assert loader.load_arc("b1")[0].band_key == "b1-core"
    assert loader.load_arc("b2")[0].band_key == "b2+"
    assert loader.load_arc("a1")[0].band_key is None


def test_a1_arc_gains_only_the_level_key() -> None:
    text = A1_ARC_YAML.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    assert data["level"] == "a1"
    assert "immersion_bands" not in data
    assert all("band_key" not in record for record in data["positions"])
    block = text[text.index("positions:\n") :]
    assert hashlib.sha256(block.encode()).hexdigest() == A1_POSITIONS_BLOCK_SHA256


def test_a1_check_green_with_empty_manifest_list() -> None:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["levels"]["a1"]["modules"] == []
    assert generate_arc.main(["--level", "a1", "--check"]) == 0


def test_all_skills_expansion_follows_each_documents_legend() -> None:
    a2 = {r["position"]: r for r in _records("a2")}
    assert a2[69]["skills_text"] == "all"
    assert a2[69]["skills"] == ["W", "Li", "R"]
    b2 = {r["position"]: r for r in _records("b2")}
    assert b2[93]["skills_text"] == "all"
    assert b2[93]["skills"] == ["W", "Li", "R", "S"]
    assert "S" in b2[8]["skills"]


def test_mutation_duplicate_position_fails(tmp_path: Path) -> None:
    mutated = _mutated_doc("a2", tmp_path, "| 2 | `aspect-concept`", "| 1 | `aspect-concept`")
    with pytest.raises(generate_arc.ArcGenerationError, match="not contiguous"):
        generate_arc.generate_yaml(mutated, "a2")


def test_mutation_slug_not_in_manifest_fails(tmp_path: Path) -> None:
    mutated = _mutated_doc("a2", tmp_path, "`aspect-concept`", "`aspect-concept-x`")
    with pytest.raises(generate_arc.ArcGenerationError, match="manifest order"):
        generate_arc.generate_yaml(mutated, "a2")


def test_mutation_unknown_band_key_fails(tmp_path: Path) -> None:
    mutated = _mutated_doc("a2", tmp_path, "| 1–3 | `a2-bridge` |", "| 1–3 | `a2-unknown` |")
    with pytest.raises(generate_arc.ArcGenerationError, match="IMMERSION_POLICIES"):
        generate_arc.generate_yaml(mutated, "a2")


def test_mutation_position_missing_from_band_table_fails(tmp_path: Path) -> None:
    mutated = _mutated_doc("a2", tmp_path, "| 51–69 | `a2-m51-70` |", "| 51–68 | `a2-m51-70` |")
    with pytest.raises(generate_arc.ArcGenerationError, match="not covered"):
        generate_arc.generate_yaml(mutated, "a2")


def test_mutation_overlapping_band_range_fails(tmp_path: Path) -> None:
    mutated = _mutated_doc("a2", tmp_path, "| 4–7 | `a2-ramp` |", "| 3–7 | `a2-ramp` |")
    with pytest.raises(generate_arc.ArcGenerationError, match="more than one band range"):
        generate_arc.generate_yaml(mutated, "a2")


def test_mutation_letters_at_a2_fail(tmp_path: Path) -> None:
    mutated = _mutated_doc(
        "a2",
        tmp_path,
        "Notice that Ukrainian verbs come in pairs",
        "Notice that Ukrainian verbs come in pairs **3 letters**",
    )
    with pytest.raises(generate_arc.ArcGenerationError, match="no literacy inventory"):
        generate_arc.generate_yaml(mutated, "a2")


def test_literacy_table_at_a2_fails(tmp_path: Path) -> None:
    header = "| Pos | Slug | Phase | One-sentence job | Skills duty | L |"
    literacy_table = (
        "| Pos | Slug | Job | Inventory (letters / signs) | Est. lessons |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 1 | `letters` | Letters | **1 letters** А | 1 |\n\n"
    )
    mutated = _mutated_doc("a2", tmp_path, header, literacy_table + header)
    with pytest.raises(generate_arc.ArcGenerationError, match="no literacy phase"):
        generate_arc.generate_yaml(mutated, "a2")


def test_prose_only_section_7_fails(tmp_path: Path) -> None:
    mutated = _mutated_doc(
        "a2",
        tmp_path,
        "| Positions | Band key | Advisory Ukrainian share |\n| --- | --- | --- |\n",
        "",
    )
    with pytest.raises(generate_arc.ArcGenerationError, match="no immersion band table found in §7"):
        generate_arc.generate_yaml(mutated, "a2")


def test_en_dash_and_hyphen_ranges_parse_identically(tmp_path: Path) -> None:
    original = generate_arc.parse_immersion_bands(_doc("a2").read_text(encoding="utf-8"))
    mutated = _mutated_doc("a2", tmp_path, "| 1–3 | `a2-bridge` |", "| 1-3 | `a2-bridge` |")
    assert generate_arc.parse_immersion_bands(mutated.read_text(encoding="utf-8")) == original


def test_s_skill_code_fails_at_a2(tmp_path: Path) -> None:
    mutated = _mutated_doc("a2", tmp_path, "follow a Ukrainian explanation | Li, W |", "follow a Ukrainian explanation | S |")
    with pytest.raises(generate_arc.ArcGenerationError, match="skills-duty token"):
        generate_arc.generate_yaml(mutated, "a2")


def test_b1_b2_band_tables_are_single_range() -> None:
    for level in ("b1", "b2"):
        bands = generate_arc.parse_immersion_bands(_doc(level).read_text(encoding="utf-8"))
        count = LEVELS[level][0]
        assert bands == [{"start": 1, "end": count, "band_key": FIRST_BAND_KEY[level]}]
