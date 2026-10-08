"""Tests for the A1 arc generator, generated YAML, and loader (issue #8411).

The arc document docs/epics/fresh-build-a1-arc.md is the reviewed source of
truth; curriculum/l2-uk-en/lesson-plans/a1/_arc.yaml must stay byte-identical
to a fresh run of scripts/curriculum/arc/generate_arc.py. Mutation tests run
the generator against temporary copies of the document — the real document
and the committed YAML are never touched.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.arc import generate_arc, loader

pytestmark = [pytest.mark.reads_content]

REPO_ROOT = Path(__file__).resolve().parents[3]
ARC_DOC = REPO_ROOT / "docs/epics/fresh-build-a1-arc.md"
ARC_YAML = REPO_ROOT / "curriculum/l2-uk-en/lesson-plans/a1/_arc.yaml"


POS1_ROW_FRAGMENT = "**12 letters**: А Е И І О М Н В П Р Т Я"
POS42_ROW = "| 42 | `hey-friend` | A1.7 | Address people by name: vocative | — | 2 |"
POS5_ROW = next(line for line in ARC_DOC.read_text().splitlines() if line.startswith("| 3 |"))
STATED_TOTAL_ANCHOR = "orientation only and total 162"
STATED_TOTAL_SENTENCE = "The lesson counts above are estimates for\norientation only and total 162."


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
    records = _records()
    assert records[0]["slug"] == "introduction-to-ukrainian"
    assert records[0]["letters"] == []
    assert [r["est_lessons"] for r in records[:7]] == [2, 5, 4, 4, 5, 3, 2]
    letters = [letter for record in records[1:5] for letter in record["letters"]]
    assert len(letters) == len(set(letters)) == 33
    assert set(letters) == set("АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩьЮЯ")


def test_position_2_letters_exact() -> None:
    records = _records()
    assert records[1]["letters"] == list("АЕИІОМНВПРТЯ")
    assert "ь" in records[2]["letters"]


def test_opening_rows_own_phase_and_skills() -> None:
    records = _records()
    assert records[0]["skills"] == []
    for record in records[1:7]:
        assert {"Li", "S"} <= set(record["skills"])
    assert records[4]["skills"] == ["Li", "S", "R", "W"]
    assert records[-1]["skills"] == ["W", "Li", "R", "S"]
    assert all(isinstance(r["position"], int) for r in records)


def test_standard_line_refs_parsing() -> None:
    records = {r["position"]: r for r in _records()}
    assert records[3]["standard_line_refs"] == [[485, 485]]
    assert records[5]["standard_line_refs"] == [[571, 572]]
    assert records[34]["standard_line_refs"] == [[523, 525], [361, 361]]
    assert records[28]["standard_line_refs"] == []


#: A Standard source-line reference in any spelling: `:361`, `:489-493`, (`:549-551`), :531–533.
#: A clock time (10:30) is not one: the colon must not follow a digit.
JOB_SOURCE_LINE_REF_RE = re.compile(r"(?<!\d):\d+(?:[-–]\d+)?")


@pytest.mark.parametrize(
    "text, leaks",
    [
        ("weight and volume (`:531-533`)", True),
        ("address an envelope `:361`", True),
        ("at the border :523–525", True),
        ("meet at 10:30 for coffee", False),
        ("Ask and tell the time", False),
    ],
)
def test_job_source_line_ref_pattern(text: str, leaks: bool) -> None:
    assert bool(JOB_SOURCE_LINE_REF_RE.search(text)) is leaks


def test_job_text_has_no_leaked_source_line_reference() -> None:
    """`job` is rendered verbatim on the arc landing (ArcLanding.tsx, ArcModule.tsx); a
    source citation like ``(`:489-493`)`` leaking into it is learner-facing noise, not a
    citation — the reference belongs in a non-learner-facing field (skills duty) or prose."""
    for record in _records():
        assert not JOB_SOURCE_LINE_REF_RE.search(record["job"]), (
            f"position {record['position']} ({record['slug']}) job leaks a source line reference: {record['job']!r}"
        )


def test_mutation_one_slug_breaks_check(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, "`euphony`", "`euphony-x`")
    assert generate_arc.main(["--level", "a1", "--check", "--doc", str(mutated)]) == 1


def test_mutation_one_lesson_count_fails_stated_total_check(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS42_ROW, POS42_ROW.replace("| — | 2 |", "| — | 5 |"))
    with pytest.raises(generate_arc.ArcGenerationError, match="stated lesson total"):
        generate_arc.generate_yaml(mutated)


def test_mutation_deleted_row_breaks_check(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS42_ROW + "\n", "")
    assert generate_arc.main(["--level", "a1", "--check", "--doc", str(mutated)]) != 0


def test_bolded_count_mismatch_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS1_ROW_FRAGMENT, POS1_ROW_FRAGMENT.replace("**12 letters**", "**11 letters**"))
    with pytest.raises(generate_arc.ArcGenerationError):
        generate_arc.generate_yaml(mutated)


def test_literacy_row_missing_cell_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS5_ROW, POS5_ROW.rsplit("|", 2)[0] + "|")
    with pytest.raises(generate_arc.ArcGenerationError, match="cells"):
        generate_arc.generate_yaml(mutated)


def test_est_lessons_total_emitted_and_matches_stated_total() -> None:
    data = yaml.safe_load(generate_arc.generate_yaml(ARC_DOC))
    assert data["est_lessons_total"] == 162
    assert data["est_lessons_total"] == sum(r["est_lessons"] for r in data["positions"])


def test_stated_total_mismatch_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, STATED_TOTAL_ANCHOR, "orientation only and total 161")
    with pytest.raises(generate_arc.ArcGenerationError, match="stated lesson total"):
        generate_arc.generate_yaml(mutated)


def test_stated_total_sentence_removed_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, STATED_TOTAL_SENTENCE + " ", "")
    with pytest.raises(generate_arc.ArcGenerationError, match="no stated lesson total"):
        generate_arc.generate_yaml(mutated)


def test_unknown_skills_code_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS5_ROW, POS5_ROW.replace("| Li, S, W (`:485`) | 4 |", "| X | 3 |"))
    with pytest.raises(generate_arc.ArcGenerationError):
        generate_arc.generate_yaml(mutated)


def test_skills_trailing_comma_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS5_ROW, POS5_ROW.replace("| Li, S, W (`:485`) | 4 |", "| Li, | 3 |"))
    with pytest.raises(generate_arc.ArcGenerationError, match="empty skill token"):
        generate_arc.generate_yaml(mutated)


def test_skills_double_comma_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS5_ROW, POS5_ROW.replace("| Li, S, W (`:485`) | 4 |", "| Li,, W | 3 |"))
    with pytest.raises(generate_arc.ArcGenerationError, match="empty skill token"):
        generate_arc.generate_yaml(mutated)


def test_skills_duplicate_code_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS5_ROW, POS5_ROW.replace("| Li, S, W (`:485`) | 4 |", "| Li, Li | 3 |"))
    with pytest.raises(generate_arc.ArcGenerationError, match="repeats skill code"):
        generate_arc.generate_yaml(mutated)


def test_unbackticked_line_ref_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, "(`:485`)", "(:485)")
    with pytest.raises(generate_arc.ArcGenerationError, match="must be backticked"):
        generate_arc.generate_yaml(mutated)


def test_backticked_ref_en_dash_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, "`:571-572`", "`:571–572`")
    with pytest.raises(generate_arc.ArcGenerationError, match="ASCII hyphen"):
        generate_arc.generate_yaml(mutated)


def test_inverted_line_ref_range_fails_generation(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, "`:571-572`", "`:572-571`")
    with pytest.raises(generate_arc.ArcGenerationError, match="inverted range"):
        generate_arc.generate_yaml(mutated)


def test_non_range_position_row_range_fails(tmp_path: Path) -> None:
    mutated = _mutated_doc(tmp_path, POS42_ROW, POS42_ROW.replace("| 42 |", "| 42–43 |"))
    with pytest.raises(generate_arc.ArcGenerationError):
        generate_arc.generate_yaml(mutated)


def test_loader_roundtrip() -> None:
    positions = loader.load_arc("a1")
    assert len(positions) == 55
    first = positions[0]
    assert first.slug == "introduction-to-ukrainian"
    assert first.letters == []
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


def test_loader_raises_on_schema_invalid_yaml(tmp_path: Path) -> None:
    data = yaml.safe_load(ARC_YAML.read_text(encoding="utf-8"))
    data["bogus_key"] = 1
    invalid = tmp_path / "_arc.yaml"
    invalid.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError, match="bogus_key"):
        loader.load_arc("a1", arc_path=invalid)


def test_loader_raises_on_inverted_line_ref_range(tmp_path: Path) -> None:
    """The schema cannot express start <= end with prefixItems; the loader checks it."""
    data = yaml.safe_load(ARC_YAML.read_text(encoding="utf-8"))
    refs = data["positions"][4]["standard_line_refs"]
    assert refs == [[571, 572]]
    refs[0] = [572, 571]
    inverted = tmp_path / "_arc.yaml"
    inverted.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError, match="inverted standard_line_refs range"):
        loader.load_arc("a1", arc_path=inverted)


def test_loader_refuses_arc_path_under_plans() -> None:
    with pytest.raises(ValueError, match="lesson-plans/"):
        loader.load_arc("a1", arc_path=REPO_ROOT / "curriculum/l2-uk-en/plans/a1/_arc.yaml")


def test_loader_never_reads_plans_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An _arc.yaml under plans/<level>/ is invisible to load_arc.

    Scoping rule (fresh-build-plan-schema.md §1): load_arc resolves only
    curriculum/l2-uk-en/lesson-plans/<level>/_arc.yaml and never searches or
    falls back to plans/. With a repo root that has the arc only under
    plans/a1/, load_arc must fail with FileNotFoundError.
    """
    root = tmp_path / "repo"
    (root / "schemas").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "schemas/arc.schema.json", root / "schemas/arc.schema.json")
    plans_dir = root / "curriculum/l2-uk-en/plans/a1"
    plans_dir.mkdir(parents=True)
    shutil.copy(ARC_YAML, plans_dir / "_arc.yaml")
    monkeypatch.setattr(loader, "REPO_ROOT", root)
    with pytest.raises(FileNotFoundError):
        loader.load_arc("a1")


def test_positions_11_to_55_retain_semantic_identity():
    import hashlib
    import json

    later = _records()[10:]
    assert hashlib.sha256(json.dumps(later, ensure_ascii=False, sort_keys=True).encode()).hexdigest() == 'd4ccdd35f7898ae57947ffba177277cb2d396a85280cfb48b20d492ba54d5673'
