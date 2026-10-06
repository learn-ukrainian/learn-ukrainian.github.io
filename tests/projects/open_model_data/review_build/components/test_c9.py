"""C9 accept paths and adversarial fixtures: SYNTHETIC source text only."""

import copy
import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from scripts.projects.open_model_data.review_build import __main__ as cli
from scripts.projects.open_model_data.review_build import bindings, output
from scripts.projects.open_model_data.review_build.attribution import Resolver
from scripts.projects.open_model_data.review_build.catalog import Catalog
from scripts.projects.open_model_data.review_build.components import ComponentContext, load_components
from scripts.projects.open_model_data.review_build.components.c9 import (
    ALLOWLISTED_FILES,
    BINDING,
    FROZEN_COUNT,
    LINE_POLICY,
    SOURCE_SCHOOL,
    SOURCE_UNIVERSITY,
    TextbookAttribution,
    Textbooks,
    citation,
    compatibility,
    headings,
    identity,
    ocr_damaged,
    running_head_ambiguous,
    unit_id,
)
from scripts.projects.open_model_data.review_build.components.c9_queries import UNIT_QUERY
from scripts.projects.open_model_data.review_build.contract import digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.gate import Gate
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from scripts.projects.open_model_data.review_build.transforms import transform


def imprint(book="SYNTHETIC Book", grade="5 класу"):
    return f"{book}: підручник для {grade} / SYNTHETIC Author — SYNTHETIC City: SYNTHETIC Publisher, 2025."


def page(index, text, book="5-klas-SYNTHETIC-book", number=None):
    return {
        "section_id": index,
        "source_file": book,
        "grade": 0,
        "section_title": f"Сторінка {index}",
        "section_number": None,
        "page_start": index if number is None else number,
        "page_end": index if number is None else number,
        "chunk_count": 1,
        "full_text": text,
    }


def write_pages(path, pages):
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE textbook_sections (section_id INTEGER PRIMARY KEY, source_file TEXT, "
            "grade INTEGER, section_title TEXT, section_number TEXT, page_start INTEGER, "
            "page_end INTEGER, chunk_count INTEGER, full_text TEXT)"
        )
        for row in pages:
            connection.execute("INSERT INTO textbook_sections VALUES (?,?,?,?,?,?,?,?,?)", list(row.values()))


def component_for(pages):
    component = Textbooks()
    component.spec["compatibility"] = compatibility({p["source_file"] for p in pages})
    return component


@pytest.fixture
def source(tmp_path):
    pages = [
        page(1, imprint()),
        page(2, "§ 1. SYNTHETIC First\nSYNTHETIC first body\n2\n"),
        page(3, "SYNTHETIC continuation\n3\n"),
        page(4, "§ 2. SYNTHETIC Next\nSYNTHETIC next body\n4\n"),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    return path, pages


def gate_for(reader, pages, count):
    component = component_for(pages)
    spec = copy.deepcopy(component.spec)
    spec["operation_specs"]["verbatim_section"]["frozen_count"] = count
    root = Path(__file__).resolve().parents[5]
    catalog = Catalog(
        yaml.safe_load((root / "registry/projects/open_model_data/instruction_catalog.yaml").read_bytes())
    )
    register = {
        "sources": [
            {
                "id": source,
                "citation": {"form": TextbookAttribution.FORM},
                "terms": {"licence": {"name": "SYNTHETIC licence"}},
            }
            for source in (SOURCE_SCHOOL, SOURCE_UNIVERSITY)
        ]
    }
    return Gate(reader, catalog, Resolver(register, component.adapters), {"C9": spec})


def extract(reader, pages):
    return list(component_for(pages).iter_candidates(ComponentContext(reader, {"schema": "omd-review-request.v2"})))


def test_registered_component_and_frozen_spec():
    obj = load_components(["C9"])["C9"]
    assert isinstance(obj, Textbooks)
    assert obj.spec["operation_specs"]["verbatim_section"]["frozen_count"] == FROZEN_COUNT == 11099
    assert obj.spec["operation_specs"]["verbatim_section"]["unit_query"] == UNIT_QUERY
    assert len(ALLOWLISTED_FILES) == 184
    policies = obj.spec["compatibility"]
    assert policies == compatibility(ALLOWLISTED_FILES)
    assert [len(p["source_values"]) for p in policies] == [163, 21]
    assert all(p["sensitive"] is None and p["role"] == "textbook" for p in policies)
    assert "corpus" not in obj.spec


def test_accept_complete_multipage_body_and_gate(source):
    path, pages = source
    with SnapshotReader({"sources.db": path}) as reader:
        candidates = extract(reader, pages)
        assert {c.unit_id for c in candidates} == set(reader.units(UNIT_QUERY))
        assert [c.outcome for c in candidates] == ["accepted", "accepted"]
        assert [v.text for v in candidates[0].response] == ["\nSYNTHETIC first body\n", "SYNTHETIC continuation\n"]
        assert [v.text for v in candidates[0].slots] == ["SYNTHETIC Book", "5 класу", "§ 1. SYNTHETIC First"]
        records, report = gate_for(reader, pages, 2).run(candidates)
        assert len(records) == 2
        assert report["accounting"]["C9"]["accepted"] == 2
        assert report["metrics"]["C9.verbatim_section"]["status"] == "insufficient_evidence"
        assert "SYNTHETIC Publisher, 2025" in next(iter(records[0]["provenance"].values()))["attribution"]


@pytest.mark.parametrize(
    "title",
    [
        "§ 1. SYNTHETIC Title",
        "§2 SYNTHETIC Title",
        "Тема 3 SYNTHETIC Title",
        "РОЗДІЛ 12. SYNTHETIC Title",
        "  § 2. SYNTHETIC Title  ",
    ],
)
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""])
def test_heading_position_sql_independent_parity(tmp_path, title, ending):
    row = page(1, "SYNTHETIC preface\n" + title + ending + "\nSYNTHETIC body")
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, [row])
    with SnapshotReader({"sources.db": path}) as reader:
        assert reader.units(UNIT_QUERY) == [unit_id(headings(row)[0])]
        heading = headings(row)[0]
        assert row["full_text"][slice(*heading.span)] == title.strip()


@pytest.mark.parametrize(
    "text",
    [
        "Сторінка 3",
        "Reference 2",
        "Entry 3",
        "Private lesson SYNTHETIC",
        "1. SYNTHETIC exercise",
        "§ 0. SYNTHETIC invalid",
        "§ 1.",
        "§ 1A SYNTHETIC",
        "Розділ I SYNTHETIC",
        "§ 2 " + "X" * 181,
    ],
)
def test_ingester_labels_and_ambiguous_lines_are_not_headings(tmp_path, text):
    row = page(1, text)
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, [row])
    with SnapshotReader({"sources.db": path}) as reader:
        assert headings(row) == []
        assert reader.units(UNIT_QUERY) == []


@pytest.mark.parametrize("next_heading", ["§ 2. SYNTHETIC Same page", "  Тема 2. SYNTHETIC Same page"])
def test_same_page_boundary_includes_only_introduced_text(tmp_path, next_heading):
    pages = [page(1, imprint()), page(2, "§ 1. SYNTHETIC One\nSYNTHETIC A\n" + next_heading + "\nSYNTHETIC B")]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidates = extract(reader, pages)
        assert len(set(c.unit_id for c in candidates)) == 2
        assert "SYNTHETIC B" not in candidates[0].response[0].text
        assert len(gate_for(reader, pages, 2).run(candidates)[0]) == 2


def test_next_heading_midpage_includes_that_pages_prefix(tmp_path):
    pages = [
        page(1, imprint()),
        page(2, "§ 1. SYNTHETIC One\nSYNTHETIC A"),
        page(3, "SYNTHETIC continuation\n§ 2. SYNTHETIC Two\nSYNTHETIC B"),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidates = extract(reader, pages)
        assert len(candidates[0].response) == 2
        assert candidates[0].response[-1].text == "SYNTHETIC continuation\n"
        assert len(gate_for(reader, pages, 2).run(candidates)[0]) == 2


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("skip_page", "binding_set"),
        ("truncate", "binding_set"),
        ("other_heading", "binding_set"),
        ("reverse_pages", "binding_pages"),
        ("wrong_book", "binding_group"),
    ],
)
def test_must_fail_mismatched_or_incomplete_body(source, mutation, code):
    path, pages = source
    with SnapshotReader({"sources.db": path}) as reader:
        candidate = extract(reader, pages)[0]
        if mutation == "skip_page":
            candidate = replace(candidate, response=candidate.response[:-1])
        elif mutation == "truncate":
            part = candidate.response[0]
            candidate = replace(
                candidate,
                response=(
                    replace(part, text=part.text[:-1], span=(part.span[0], part.span[1] - 1)),
                    *candidate.response[1:],
                ),
            )
        elif mutation == "other_heading":
            candidate = replace(candidate, response=extract(reader, pages)[1].response)
        elif mutation == "reverse_pages":
            candidate = replace(candidate, response=tuple(reversed(candidate.response)))
        else:
            with pytest.raises(BuildError, match=code):
                wrong_pages = [{**p, "source_file": "6-klas-SYNTHETIC-other"} for p in pages]

                # The source role is derived from rows, not candidate metadata.
                class OtherReader:
                    def row(self, cited):
                        row = dict(reader.row(cited))
                        if cited == candidate.response[0].citations[0]:
                            row["source_file"] = wrong_pages[0]["source_file"]
                        return row

                bindings.check(candidate, BINDING, OtherReader(), {"line_excision@1": LINE_POLICY})
            return
        gate = gate_for(reader, pages, 2)
        gate.quote(candidate)  # authentic bytes alone are insufficient
        with pytest.raises(BuildError, match=code):
            bindings.check(candidate, BINDING, reader, {"line_excision@1": LINE_POLICY})


@pytest.mark.parametrize(
    "body,reason",
    [
        ("ЗМІСТ\nSYNTHETIC .... 5", "table_of_contents"),
        ("Вправа 1\nSYNTHETIC prompt", "exercise_without_answer"),
        ("SYNTHETIC \ufffd damage", "ocr_damage"),
        ("SYNTHETIC \x00 damage", "ocr_damage"),
    ],
)
def test_detectors_withhold_positive_classes(tmp_path, body, reason):
    pages = [
        page(1, imprint()),
        page(2, "§ 1. SYNTHETIC Heading\n" + body),
        page(3, "SYNTHETIC continuation"),
        page(4, "SYNTHETIC continuation"),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidate = extract(reader, pages)[0]
        assert candidate.outcome == "withheld"
        assert candidate.reason == reason
        assert candidate.evidence
        assert gate_for(reader, pages, 1).run([candidate])[1]["accounting"]["C9"]["withheld"] == 1


def test_printed_answer_is_kept_and_no_hyphenation_is_invented(tmp_path):
    pages = [
        page(1, imprint()),
        page(2, "§ 1. SYNTHETIC Heading\nВправа 1\nSYNTHETIC hy-\nphen\nВідповідь\nSYNTHETIC printed answer"),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidate = extract(reader, pages)[0]
        assert candidate.outcome == "accepted"
        assert "hy-\nphen" in candidate.response[0].text
        assert len(gate_for(reader, pages, 1).run([candidate])[0]) == 1


@pytest.mark.parametrize("damaged,total,reason", [(3, 10, "ocr_damage"), (4, 10, "book_ocr_damage")])
def test_book_ocr_threshold_is_strictly_more_than_thirty_percent(tmp_path, damaged, total, reason):
    pages = [page(1, imprint())] + [
        page(i, "§ 1. SYNTHETIC Heading\n" if i == 2 else "SYNTHETIC body") for i in range(2, total + 1)
    ]
    for p in pages[1 : damaged + 1]:
        p["full_text"] += "SYNTHETIC \ufffd"
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        assert extract(reader, pages)[0].reason == reason


@pytest.mark.parametrize("missing", ["title", "authors", "publisher", "year", "grade"])
def test_missing_imprint_field_withholds_entire_book(tmp_path, missing):
    text = imprint()
    replacements = {
        "title": ("SYNTHETIC Book", ""),
        "authors": ("SYNTHETIC Author", ""),
        "publisher": ("SYNTHETIC Publisher", ""),
        "year": ("2025", ""),
        "grade": ("5 класу", ""),
    }
    before, after = replacements[missing]
    pages = [page(1, text.replace(before, after)), page(2, "§ 1. SYNTHETIC Heading\nSYNTHETIC body")]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        assert extract(reader, pages)[0].reason == "book_identity_unresolved"


def test_conflicting_imprint_and_running_head_withhold(tmp_path):
    pages = [page(1, imprint()), page(2, imprint("SYNTHETIC Other")), page(3, "§ 1. SYNTHETIC Heading\nSYNTHETIC body")]
    assert identity(pages) is None
    pages = [
        page(1, imprint()),
        page(2, "§ 1. SYNTHETIC Heading\nSYNTHETIC body"),
        page(3, "§ 1. SYNTHETIC Heading\nSYNTHETIC other body"),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        assert {c.reason for c in extract(reader, pages)} == {"repeated_heading"}


def test_missing_page_withholds_instead_of_shortening_response(tmp_path):
    pages = [page(1, imprint()), page(2, "§ 1. SYNTHETIC Heading\nSYNTHETIC body"), page(4, "SYNTHETIC continuation")]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        assert extract(reader, pages)[0].reason == "page_gap"


@pytest.mark.parametrize(
    "filename", ["0-klas-SYNTHETIC-private", "private-SYNTHETIC", "owned-SYNTHETIC", "teacher-SYNTHETIC"]
)
def test_nonallowlisted_rows_not_read_by_census_or_extractor(tmp_path, filename):
    pages = [
        page(1, imprint()),
        page(2, "§ 1. SYNTHETIC Heading\nSYNTHETIC body"),
        page(99, "§ 9. SYNTHETIC forbidden", book=filename),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidates = extract(reader, pages[:2])
        assert len(reader.units(UNIT_QUERY)) == len(candidates) == 1
        assert "99" not in candidates[0].unit_id


def test_exact_allowlist_cannot_silently_shrink_denominator(source):
    path, _pages = source
    with SnapshotReader({"sources.db": path}) as reader:
        with pytest.raises(BuildError, match="textbook_allowlist"):
            list(Textbooks().iter_candidates(ComponentContext(reader, {"schema": "omd-review-request.v2"})))


def test_university_grade_zero_admitted_from_filename_with_printed_level(tmp_path):
    pages = [
        page(1, imprint(grade="студентів"), book="uni-SYNTHETIC-book"),
        page(2, "§ 1. SYNTHETIC Heading\nSYNTHETIC body", book="uni-SYNTHETIC-book"),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidate = extract(reader, pages)[0]
        assert candidate.outcome == "accepted"
        assert candidate.slots[1].text == "студентів"
        assert candidate.slots[1].citations[0].source_id == SOURCE_UNIVERSITY
        assert len(gate_for(reader, pages, 1).run([candidate])[0]) == 1


@pytest.mark.parametrize(
    "form",
    [
        "Author(s), title, grade, publisher, year, page — for every quoted sentence.",
        "{authors}. {title}. {grade}. {publisher}, <year>.",
        "SYNTHETIC insert citation",
    ],
)
def test_instruction_style_or_unmapped_attribution_must_fail(source, form):
    path, pages = source
    with SnapshotReader({"sources.db": path}) as reader:
        with pytest.raises(BuildError, match="attribution_unresolved"):
            TextbookAttribution().resolve(form, citation(pages[1]), pages[1], reader)


def test_attribution_pins_imprint_and_all_required_fields(source):
    path, pages = source
    with SnapshotReader({"sources.db": path}) as reader:
        result = TextbookAttribution().resolve(TextbookAttribution.FORM, citation(pages[2]), pages[2], reader)
        assert result.bibliography == "SYNTHETIC Author. SYNTHETIC Book. 5 класу. SYNTHETIC Publisher, 2025."
        assert ("section_id=1", digest(pages[0]["full_text"].encode())) in reader.reads[
            ("sources.db", "textbook_sections")
        ]


def test_page_number_removal_has_exact_trace_and_preserves_other_lines():
    text = "SYNTHETIC top\n  23 \r\nSYNTHETIC 24\nSYNTHETIC hy-\nphen"
    result = transform("line_excision@1", text, LINE_POLICY)
    assert result.text == "SYNTHETIC top\nSYNTHETIC 24\nSYNTHETIC hy-\nphen"
    assert result.dropped_lines == ((2, 2),)
    assert not result.joins
    assert not ocr_damaged(result.text)


def test_ordinary_running_heads_withhold_without_guessing_deletions(tmp_path):
    pages = [page(1, imprint())] + [
        page(
            i,
            "SYNTHETIC running title\n" + ("§ 1. SYNTHETIC Heading\n" if i == 2 else "") + f"SYNTHETIC body {i}\n{i}\n",
        )
        for i in range(2, 6)
    ]
    assert running_head_ambiguous(pages)
    assert not running_head_ambiguous([page(i, f"{i}\nSYNTHETIC distinct {i}\n{i}") for i in range(1, 6)])
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        assert extract(reader, pages)[0].reason == "running_head_unresolved"


def test_imprint_wrong_field_span_must_fail_even_with_authentic_quote(source):
    path, pages = source
    with SnapshotReader({"sources.db": path}) as reader:
        candidate = extract(reader, pages)[0]
        item = identity(pages)
        title = candidate.slots[0]
        title = replace(title, text=item.text("publisher"), span=item.fields["publisher"])
        candidate = replace(candidate, slots=(title, *candidate.slots[1:]))
        gate_for(reader, pages, 2).quote(candidate)
        with pytest.raises(BuildError, match="binding_span"):
            bindings.check(candidate, BINDING, reader, {"line_excision@1": LINE_POLICY})


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("quote_absent", "quote_mismatch"),
        ("wrong_span", "quote_mismatch"),
        ("empty_locator", "empty_locator"),
        ("paraphrase", "unknown_transform"),
        ("missing_unit", "missing_unit"),
        ("swapped_citation", "unit_id_mismatch"),
    ],
)
def test_c9_generic_must_fail_fixtures(source, mutation, code):
    path, pages = source
    with SnapshotReader({"sources.db": path}) as reader:
        candidates = extract(reader, pages)
        candidate = candidates[0]
        part = candidate.response[0]
        if mutation == "missing_unit":
            candidates = candidates[1:]
        elif mutation == "swapped_citation":
            heading = candidate.slots[-1]
            heading = replace(heading, citations=candidates[1].slots[-1].citations)
            candidates[0] = replace(candidate, slots=(*candidate.slots[:-1], heading))
        else:
            if mutation == "quote_absent":
                part = replace(part, text=part.text + "SYNTHETIC invented")
            elif mutation == "wrong_span":
                part = replace(part, span=(part.span[0] + 1, part.span[1]))
            elif mutation == "empty_locator":
                part = replace(part, citations=(replace(part.citations[0], locator=""),))
            else:
                part = replace(part, transform="paraphrase@1")
            candidates[0] = replace(candidate, response=(part, *candidate.response[1:]))
        with pytest.raises(BuildError, match=code):
            gate_for(reader, pages, 2).run(candidates)


def test_c9_synthetic_cli_build_verify_and_real_catalog_metrics(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    pages = [page(1, imprint())] + [
        page(i + 2, f"§ {i + 1}. SYNTHETIC Heading {i}\nSYNTHETIC body {i}") for i in range(12)
    ]
    db = tmp_path / "SYNTHETIC.db"
    write_pages(db, pages)
    component = component_for(pages)
    component.spec["operation_specs"]["verbatim_section"]["frozen_count"] = 12
    root = Path(__file__).resolve().parents[5]
    register = {
        "sources": [
            {
                "id": source,
                "citation": {"form": TextbookAttribution.FORM},
                "terms": {"licence": {"name": "SYNTHETIC licence"}},
            }
            for source in (SOURCE_SCHOOL, SOURCE_UNIVERSITY)
        ]
    }
    register_path = tmp_path / "SYNTHETIC-register.yaml"
    register_path.write_text(yaml.safe_dump(register))
    request = {
        "schema": "omd-review-request.v2",
        "ua_gec": {"root": str(tmp_path / "SYNTHETIC-ua-gec")},
        "catalog": str(root / "registry/projects/open_model_data/instruction_catalog.yaml"),
        "register": str(register_path),
        "databases": {"sources.db": str(db)},
    }
    request_path = tmp_path / "SYNTHETIC-request.json"
    request_path.write_text(json.dumps(request))
    target = tmp_path / "SYNTHETIC-build"
    args = ["--config", str(request_path), "--out", str(target), "--components", "C9"]
    for command in ("build", "verify"):
        assert cli.main([command, *args], _test_components={"C9": component}) == 0
        assert json.loads(capsys.readouterr().out)["status"] == ("built" if command == "build" else "verified")
    manifest = json.loads((target / "manifest.json").read_bytes())
    assert manifest["accounting"]["C9"]["accepted"] == 12
    assert manifest["metrics"]["C9.verbatim_section"]["status"] == "PASS"
    assert len(json.loads((target / "mutation-fixtures/results.json").read_bytes())) == 5


@pytest.mark.parametrize("mutation", ["missing", "extra", "wrong_partition"])
def test_component_owned_allowlist_drift_refuses(source, mutation):
    path, pages = source
    component = component_for(pages)
    entry = component.spec["compatibility"][0]
    if mutation == "missing":
        entry["allowlisted_files"] = []
    elif mutation == "extra":
        entry["allowlisted_files"].append("6-klas-SYNTHETIC-absent")
    else:
        entry["source_id"] = SOURCE_UNIVERSITY
    with SnapshotReader({"sources.db": path}) as reader:
        if mutation == "wrong_partition":
            candidates = list(component.iter_candidates(ComponentContext(reader, {})))
            original = gate_for(reader, pages, len(candidates))
            component.spec["operation_specs"]["verbatim_section"]["frozen_count"] = len(candidates)
            gate = Gate(reader, original.catalog, original.resolver, {"C9": component.spec})
            with pytest.raises(BuildError, match="source_compatibility"):
                gate.run(candidates)
        else:
            with pytest.raises(BuildError, match="textbook_allowlist"):
                list(component.iter_candidates(ComponentContext(reader, {})))
