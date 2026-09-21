"""Tests for the A1 arc generator, generated YAML, and loader (issue #8411).

The arc document docs/epics/fresh-build-a1-arc.md is the reviewed source of
truth; curriculum/l2-uk-en/arc/a1/_arc.yaml must stay byte-identical to a
fresh run of scripts/curriculum/arc/generate_arc.py. Mutation tests run the
generator against temporary copies of the document — the real document and
the committed YAML are never touched.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from scripts.curriculum.arc import generate_arc, loader

pytestmark = [pytest.mark.reads_content]

REPO_ROOT = Path(__file__).resolve().parents[3]
ARC_DOC = REPO_ROOT / "docs/epics/fresh-build-a1-arc.md"
ARC_YAML = REPO_ROOT / "curriculum/l2-uk-en/arc/a1/_arc.yaml"

ROLLUP_ROW = "| 1–4 | *(see §4)* | A1.1 | Literacy | Li, W (copying, own name) | 17 |"
POS1_ROW_FRAGMENT = "**13 letters**, primer part 1 order"
POS42_ROW = "| 42 | `hey-friend` | A1.7 | Address people by name: vocative | — | 2 |"
POS5_ROW = "| 5 | `who-am-i` | A1.1 | Introduce yourself and ask who someone is; common professions (`:485`) | Li | 3 |"


def _records(doc_path: Path = ARC_DOC) -> list[dict]:
    return generate_arc.parse_positions(doc_path.read_text(encoding="utf-8"))


def _mutated_doc(tmp_path: Path, old: str, new: str) -> Path:
    text = ARC_DOC.read_text(encoding="utf-8")
    assert old in text, f"mutation target not found in the arc document: {old!r}"
    assert text.count(old) == 1, f"mutation target is not unique in the arc document: {old!r}"
    mutated = tmp_path / "arc.md"
    mutated.write_text(text.replace(old, new), encoding="utf-8")
    return mutated


def test_check_passes_on_committed_file() -> None:
    assert generate_arc.main(["--level", "a1", "--check"]) == 0


def test_a1_has_55_contiguous_positions_with_unique_slugs() -> None:
    records = _records()
    assert [r["position"] for r in records] == list(range(1, 56))
    slugs = [r["slug"] for r in records]
    assert len(set(slugs)) == 55


def test_literacy_positions_letters_and_lessons() -> None:
    records = {r["position"]: r for r in _records()}
    assert records[1]["slug"] == "sounds-letters-and-hello"
    assert records[1]["est_lessons"] == 5
    assert len(records[1]["letters"]) == 13
    assert len(records[2]["letters"]) == 12
    assert len(records[3]["letters"]) == 8
    sets = [set(records[p]["letters"]) for p in (1, 2, 3)]
    assert sets[0].isdisjoint(sets[1]) and sets[0].isdisjoint(sets[2]) and sets[1].isdisjoint(sets[2])
    assert len(sets[0] | sets[1] | sets[2]) == 33


def test_position_1_letters_exact() -> None:
    records = {r["position"]: r for r in _records()}
    assert records[1]["letters"] == list("АОУИМІНВЛСКПР")
    assert records[3]["letters"][-1] == "ь"


def test_rollup_row_drives_literacy_positions_and_is_not_emitted() -> None:
    records = _records()
    for position in (1, 2, 3, 4):
        record = records[position - 1]
        assert record["phase"] == "A1.1"
        assert record["skills"] == ["Li", "W"]
        assert record["skills_text"] == "Li, W (copying, own name)"
    assert all(isinstance(r["position"], int) for r in records)
    assert not any("see §4" in r["slug"] or r["job"] == "Literacy" for r in records)


def test_standard_line_refs_parsing() -> None:
    records = {r["position"]: r for r in _records()}
    assert records[3]["standard_line_refs"] == [[571, 572]]
    assert records[4]["standard_line_refs"] == [[588, 588], [571, 571]]
    assert records[34]["standard_line_refs"] == [[523, 525], [361, 361]]
    assert records[28]["standard_line_refs"] == []


def test_mutation_one_slug_breaks_check(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, "`euphony`", "`euphony-x`")
    assert generate_arc.main(["--level", "a1", "--check", "--doc", str(mutated)]) == 1


def test_mutation_one_lesson_count_breaks_check(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS42_ROW, POS42_ROW.replace("| — | 2 |", "| — | 5 |"))
    assert generate_arc.main(["--level", "a1", "--check", "--doc", str(mutated)]) == 1


def test_mutation_deleted_row_breaks_check(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS42_ROW + "\n", "")
    assert generate_arc.main(["--level", "a1", "--check", "--doc", str(mutated)]) != 0


def test_bolded_count_mismatch_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS1_ROW_FRAGMENT, POS1_ROW_FRAGMENT.replace("**13 letters**", "**12 letters**"))
    with pytest.raises(generate_arc.ArcGenerationError):
        generate_arc.generate_yaml(mutated)


def test_rollup_total_mismatch_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, ROLLUP_ROW, ROLLUP_ROW.replace("| 17 |", "| 16 |"))
    with pytest.raises(generate_arc.ArcGenerationError):
        generate_arc.generate_yaml(mutated)


def test_unknown_skills_code_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS5_ROW, POS5_ROW.replace("| Li | 3 |", "| X | 3 |"))
    with pytest.raises(generate_arc.ArcGenerationError):
        generate_arc.generate_yaml(mutated)


def test_non_range_position_row_range_fails(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS42_ROW, POS42_ROW.replace("| 42 |", "| 42–43 |"))
    with pytest.raises(generate_arc.ArcGenerationError):
        generate_arc.generate_yaml(mutated)


def test_loader_roundtrip() -> None:
    positions = loader.load_arc("a1")
    assert len(positions) == 55
    first = positions[0]
    assert first.slug == "sounds-letters-and-hello"
    assert first.letters is not None and len(first.letters) == 13
    assert positions[27].slug == "euphony"
    assert positions[27].skills == []
    assert positions[27].letters is None
    assert positions[44].standard_line_refs == [(489, 493)]


def test_loader_raises_on_stale_source_sha256(tmp_path: Path) -> None:
    stale = tmp_path / "_arc.yaml"
    text = ARC_YAML.read_text(encoding="utf-8")
    text = re.sub(r"sha256: [0-9a-f]{64}", "sha256: " + "ab" * 32, text, count=1)
    stale.write_text(text, encoding="utf-8")
    with pytest.raises(loader.ArcStaleError, match="not regenerated"):
        loader.load_arc("a1", arc_path=stale)


def test_loader_raises_when_document_changed(tmp_path: Path) -> None:
    changed_doc = tmp_path / "arc.md"
    shutil.copy(ARC_DOC, changed_doc)
    with changed_doc.open("a", encoding="utf-8") as handle:
        handle.write("\n")
    with pytest.raises(loader.ArcStaleError):
        loader.load_arc("a1", doc_path=changed_doc)
