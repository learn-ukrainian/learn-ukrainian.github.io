"""Tests for the accepted-decisions record generator (#8397, #8430).

The committed curriculum/l2-uk-en/lesson-plans/<level>/_decisions.yaml files are pinned to a
fresh run of scripts/curriculum/arc/generate_decisions.py. Boundary and --check tests run on
fixture documents in tmp_path — the real docs/epics files are never edited.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.curriculum.arc import generate_decisions as gd

pytestmark = [pytest.mark.reads_content]

REPO_ROOT = Path(__file__).resolve().parents[3]
LEVELS = gd.SUPPORTED_LEVELS


def _committed(level: str) -> Path:
    return REPO_ROOT / gd.OUT_REL.format(level=level)


def _real_sources() -> dict:
    return gd.load_sources(REPO_ROOT / gd.SOURCES_REL)


def _generator_sha() -> str:
    return hashlib.sha256((REPO_ROOT / gd.GENERATOR_REL).read_bytes()).hexdigest()


def _fresh(level: str) -> str:
    return gd.render_record(level, _real_sources(), _generator_sha())


# ---- the committed records ------------------------------------------------------------


@pytest.mark.parametrize("level", LEVELS)
def test_committed_record_equals_fresh_generation(level: str) -> None:
    assert _committed(level).read_bytes() == _fresh(level).encode("utf-8"), (
        f"{_committed(level)} is stale; run generate_decisions.py --all"
    )


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("record_kind", ("committed", "fresh"))
def test_shared_accepted_sections_preserve_historical_text(level: str, record_kind: str) -> None:
    # Independent #10104 reconciliation pins the accepted text, not current document hashes.
    expected = {
        "docs/epics/fresh-build-plan-schema.md": "5b306454965ee1efc321d932bbd8b009eb7ada6582a7a09bb2afd20c652a6646",
        "docs/epics/fresh-build-writer-contract.md": "285057bde594a5026ec9901179aa5df53c902268668b80e5945489336187a2b4",
        "docs/epics/fresh-build-build-program.md": "39008f5f0ec488a77da91d6b5eb5dfcaac2444564632dba42c761b9f49aa68fa",
    }
    text = _committed(level).read_text(encoding="utf-8") if record_kind == "committed" else _fresh(level)
    record = yaml.safe_load(text)
    for doc, digest in expected.items():
        sections = [source for source in record["sources"] if source["doc"] == doc]
        assert len(sections) == 1, f"{level}/{record_kind}: expected one accepted section from {doc}"
        assert sections[0]["section_sha256"] == digest, (
            f"{level}/{record_kind}/{doc}: accepted section is historical; record revisions outside it"
        )


def test_generation_is_deterministic() -> None:
    assert _fresh("a2") == _fresh("a2")


@pytest.mark.parametrize("level", LEVELS)
def test_record_is_verbatim_copy_of_named_sections(level: str) -> None:
    record = yaml.safe_load(_committed(level).read_text(encoding="utf-8"))
    sources = _real_sources()
    assert record["level"] == level
    assert [(s["doc"], s["heading"]) for s in record["sources"]] == [
        (e["doc"], e["heading"]) for e in sources["levels"][level] + sources["shared"]
    ]
    for source in record["sources"]:
        doc_text = (REPO_ROOT / source["doc"]).read_text(encoding="utf-8")
        assert source["text"].startswith(source["heading"] + "\n")
        assert source["text"] in doc_text
        assert hashlib.sha256(source["text"].encode("utf-8")).hexdigest() == source["section_sha256"]
        assert hashlib.sha256((REPO_ROOT / source["doc"]).read_bytes()).hexdigest() == source["doc_sha256"]
        assert source["accepted"] in source["accepted_evidence"]["line"]


def test_every_level_carries_its_arc_sections_and_the_shared_ones() -> None:
    a1 = yaml.safe_load(_committed("a1").read_text(encoding="utf-8"))
    headings = [s["heading"] for s in a1["sources"]]
    assert headings[0] == "## 2. Decisions"
    assert headings[1].startswith("## 6. Decisions on the six open questions")
    assert headings[2] == "## 8. Revision r4 (#10108)"
    assert headings[3] == "## 9. Revision r3.1: A1 practical recap (#10105)"
    assert len(headings) == 7
    for level in ("a2", "b1", "b2"):
        record = yaml.safe_load(_committed(level).read_text(encoding="utf-8"))
        assert record["sources"][1]["heading"].startswith("## 8. Decisions on the five open questions")
        assert [s["doc"] for s in record["sources"][2:]] == [s["doc"] for s in a1["sources"][4:]]


# ---- section boundaries on fixture documents ------------------------------------------

FIXTURE = (
    "# Title\n"
    "\n"
    "> Status: accepted 2026-01-02.\n"
    "\n"
    "## 1. Intro\n"
    "intro body\n"
    "\n"
    "## 2. Decisions\n"
    "decision body\n"
    "\n"
    "### 2.1 Sub decision\n"
    "sub body\n"
    "\n"
    "```\n"
    "## not a heading (fenced)\n"
    "```\n"
    "\n"
    "## 3. After\n"
    "after body\n"
)


def _write_fixture(tmp_path: Path, text: str = FIXTURE, name: str = "doc.md") -> Path:
    path = tmp_path / name
    path.write_bytes(text.encode("utf-8"))
    return path


def _sources_map(tmp_path: Path, doc: Path, heading: str = "## 2. Decisions") -> Path:
    entry = {
        "doc": str(doc),
        "heading": heading,
        "accepted": "2026-01-02",
        "accepted_evidence": {"doc": str(doc), "line": "> Status: accepted 2026-01-02."},
    }
    path = tmp_path / "sources.yaml"
    path.write_text(yaml.safe_dump({"schema": 1, "levels": {level: [entry] for level in LEVELS}, "shared": []}))
    return path


def _render(tmp_path: Path, text: str, heading: str = "## 2. Decisions") -> str:
    doc = _write_fixture(tmp_path, text)
    sources = gd.load_sources(_sources_map(tmp_path, doc, heading))
    return gd.render_record("a1", sources, "0" * 64)


def test_section_runs_to_next_same_level_heading_and_includes_subsections(tmp_path: Path) -> None:
    body = yaml.safe_load(_render(tmp_path, FIXTURE))["sources"][0]["text"]
    assert body == FIXTURE[FIXTURE.index("## 2. Decisions") : FIXTURE.index("## 3. After")]
    assert "### 2.1 Sub decision" in body
    assert "## not a heading (fenced)" in body
    assert "after body" not in body


def test_section_runs_to_a_higher_level_heading(tmp_path: Path) -> None:
    text = FIXTURE.replace("## 3. After", "# Part two")
    body = yaml.safe_load(_render(tmp_path, text))["sources"][0]["text"]
    assert body.endswith("```\n\n")
    assert "Part two" not in body


def test_last_section_runs_to_end_of_file(tmp_path: Path) -> None:
    body = yaml.safe_load(_render(tmp_path, FIXTURE, "## 3. After"))["sources"][0]["text"]
    assert body == "## 3. After\nafter body\n"


def test_crlf_is_normalised_to_lf_and_nothing_else(tmp_path: Path) -> None:
    body = yaml.safe_load(_render(tmp_path, FIXTURE.replace("\n", "\r\n")))["sources"][0]["text"]
    assert body == FIXTURE[FIXTURE.index("## 2. Decisions") : FIXTURE.index("## 3. After")]


def test_missing_heading_is_a_named_error(tmp_path: Path) -> None:
    with pytest.raises(gd.DecisionsGenerationError, match=r"matches no line"):
        _render(tmp_path, FIXTURE.replace("## 2. Decisions", "## 2. Other"))


def test_duplicated_heading_is_a_named_error(tmp_path: Path) -> None:
    with pytest.raises(gd.DecisionsGenerationError, match=r"ambiguous .* lines 8, 21"):
        _render(tmp_path, FIXTURE + "\n## 2. Decisions\nagain\n")


def test_heading_only_inside_a_fence_does_not_count(tmp_path: Path) -> None:
    with pytest.raises(gd.DecisionsGenerationError, match=r"matches no line"):
        _render(tmp_path, FIXTURE, "## not a heading (fenced)")


def test_evidence_line_must_exist_exactly_once(tmp_path: Path) -> None:
    with pytest.raises(gd.DecisionsGenerationError, match=r"occurs 0 times"):
        _render(tmp_path, FIXTURE.replace("> Status: accepted 2026-01-02.", "> Status: draft."))
    with pytest.raises(gd.DecisionsGenerationError, match=r"occurs 2 times"):
        _render(tmp_path, FIXTURE + "\n> Status: accepted 2026-01-02.\n")


def test_evidence_line_must_state_the_accepted_date(tmp_path: Path) -> None:
    doc = _write_fixture(tmp_path)
    sources = gd.load_sources(_sources_map(tmp_path, doc))
    sources["levels"]["a1"][0]["accepted"] = "2026-03-04"
    with pytest.raises(gd.DecisionsGenerationError, match=r"does not state the date 2026-03-04"):
        gd.render_record("a1", sources, "0" * 64)


# ---- CLI ------------------------------------------------------------------------------


def test_check_exits_1_after_a_one_byte_doc_change(tmp_path: Path) -> None:
    out = tmp_path / "_decisions.yaml"
    assert gd.main(["--level", "a2", "--output", str(out)]) == 0
    assert gd.main(["--level", "a2", "--output", str(out), "--check"]) == 0

    doc_rel = "docs/epics/fresh-build-a2-arc.md"
    mutated = tmp_path / "a2-arc.md"
    mutated.write_bytes((REPO_ROOT / doc_rel).read_bytes().replace(b"**D0 ", b"**D9 ", 1))
    assert gd.main(["--level", "a2", "--output", str(out), "--check", "--doc", f"{doc_rel}={mutated}"]) == 1

    untouched = tmp_path / "a2-arc-copy.md"
    shutil.copyfile(REPO_ROOT / doc_rel, untouched)
    assert gd.main(["--level", "a2", "--output", str(out), "--check", "--doc", f"{doc_rel}={untouched}"]) == 0


def test_trailing_whitespace_in_a_section_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(gd.DecisionsGenerationError, match=r"literal block"):
        _render(tmp_path, FIXTURE.replace("decision body\n", "decision body \n"))


def test_check_exits_1_when_the_file_is_missing(tmp_path: Path) -> None:
    assert gd.main(["--level", "a2", "--output", str(tmp_path / "absent.yaml"), "--check"]) == 1


def test_check_writes_nothing(tmp_path: Path) -> None:
    out = tmp_path / "_decisions.yaml"
    gd.main(["--level", "a2", "--output", str(out), "--check"])
    assert not out.exists()


def test_generation_error_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    doc = _write_fixture(tmp_path, FIXTURE.replace("## 2. Decisions", "## 2. Other"))
    sources = _sources_map(tmp_path, doc)
    assert gd.main(["--level", "a1", "--sources", str(sources), "--output", str(tmp_path / "out.yaml")]) == 2
    assert "matches no line" in capsys.readouterr().err
    assert not (tmp_path / "out.yaml").exists()


def test_output_override_is_rejected_with_all(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        gd.main(["--all", "--output", str(tmp_path / "x.yaml")])
    assert excinfo.value.code == 2


def test_generated_output_validates_against_the_schema(tmp_path: Path) -> None:
    schema = json.loads((REPO_ROOT / gd.SCHEMA_REL).read_text(encoding="utf-8"))
    for level in LEVELS:
        record = yaml.safe_load(_committed(level).read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(record)
        record["sources"][0]["extra"] = 1
        assert not Draft202012Validator(schema).is_valid(record)


HISTORICAL_DECISION_FINGERPRINTS = {'a1': ['a79567a8566da45fadebde07910bca80b07ef0a81c8c16e6a055c89a28f68b2f', '554a5273e017037992ce6420bb312ca5fff36212b100b839afb6c4473969eabf', '4c99a23c7b9c2cbf8311cb2d78a62bbd066304b2789ce8bdfbd82bb73f735288', '121cb31144b358f196c89f133953051b1fe60be4b17c3088b274f2b96b1bebd4', '90cb697a77b3d09efbf04a7ded7526eb3eec6e99380a00457266abb6f9bf8da6'], 'a2': ['10837479e21806aea2a4dc7ffb241b26d7fbc4fef2b832e23f12c7288c2a8c1b', '81391cf5326e3ec9bb2b2240d730f0b26fdb548464b0e594cf3f2accb78cb366', '4c99a23c7b9c2cbf8311cb2d78a62bbd066304b2789ce8bdfbd82bb73f735288', '121cb31144b358f196c89f133953051b1fe60be4b17c3088b274f2b96b1bebd4', '90cb697a77b3d09efbf04a7ded7526eb3eec6e99380a00457266abb6f9bf8da6'], 'b1': ['e6b6ce23fc13899a932529edc94ae1f2d59a35afc4798ff18af848a436a2dbf5', 'eaecdf557f588f834a3405993320aca1b556365b9a0317267719d403b04a802e', '4c99a23c7b9c2cbf8311cb2d78a62bbd066304b2789ce8bdfbd82bb73f735288', '121cb31144b358f196c89f133953051b1fe60be4b17c3088b274f2b96b1bebd4', '90cb697a77b3d09efbf04a7ded7526eb3eec6e99380a00457266abb6f9bf8da6'], 'b2': ['da8ba8ffcc36ba98e205b0794fa3d393cd43a56f13bb1b7374830e4e55c4540e', '84818067a0627df48cfe43f557c4291784dbbe1810fc40ccaa59e6268c2616c5', '4c99a23c7b9c2cbf8311cb2d78a62bbd066304b2789ce8bdfbd82bb73f735288', '121cb31144b358f196c89f133953051b1fe60be4b17c3088b274f2b96b1bebd4', '90cb697a77b3d09efbf04a7ded7526eb3eec6e99380a00457266abb6f9bf8da6']}

def test_historical_accepted_sections_and_non_a1_semantics_stay_identical():
    import json

    for level, expected in HISTORICAL_DECISION_FINGERPRINTS.items():
        record = yaml.safe_load(_committed(level).read_text())
        sources = record["sources"]
        if level == "a1":
            revision = sources[2]
            assert revision["accepted"] == "2026-10-08"
            assert revision["accepted_evidence"]["line"] == "Accepted: 2026-10-08 (designated approval: Sol 6.1 and Opus 5.5; #10108)"
            assert revision["text"].count(revision["accepted_evidence"]["line"]) == 1
            recap = sources[3]
            assert recap["heading"] == "## 9. Revision r3.1: A1 practical recap (#10105)"
            assert recap["accepted"] == "2026-10-08"
            assert recap["accepted_evidence"]["line"] == "Accepted: 2026-10-08 (designated approval: Sol 6.1 and Opus 5.5; #10105)"
            assert recap["text"].count(recap["accepted_evidence"]["line"]) == 1
            assert "a1_recap_migration_required" in recap["text"]
            sources = sources[:2] + sources[4:]
        actual = [hashlib.sha256(json.dumps({k: v for k, v in entry.items() if k != "doc_sha256"}, ensure_ascii=False, sort_keys=True).encode()).hexdigest() for entry in sources]
        assert actual == expected, level
