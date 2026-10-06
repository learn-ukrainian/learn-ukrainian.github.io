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
from scripts.projects.open_model_data.review_build.components.c9_profile_candidates import (
    candidates as profile_candidates,
)
from scripts.projects.open_model_data.review_build.components.c9_queries import UNIT_QUERY
from scripts.projects.open_model_data.review_build.contract import digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.gate import Gate
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from scripts.projects.open_model_data.review_build.transforms import transform


def imprint(book="SYNTHETIC Book", grade="5 класу"):
    return f"{book}: підручник для {grade} / SYNTHETIC prose Author — SYNTHETIC City: SYNTHETIC Publisher, 2025."


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
        "full_text": text
        if text.endswith(f"{index if number is None else number}\n")
        else text.rstrip("\n") + f"\n{index if number is None else number}\n",
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


def synthetic_profiles(pages):
    return {book: cs[0] for book, cs in profile_candidates(pages).items()}


@pytest.fixture(autouse=True)
def synthetic_profile_loader(monkeypatch):
    from scripts.projects.open_model_data.review_build.components import c9

    original = c9.load_profiles

    def load(reader):
        connection = reader.connections.get("sources.db")
        if connection is not None:
            rows = [dict(r) for r in connection.execute("SELECT * FROM textbook_sections ORDER BY page_start")]
            if rows and all("SYNTHETIC" in row["source_file"] for row in rows):
                return synthetic_profiles(rows)
        return original(reader)

    monkeypatch.setattr(c9, "load_profiles", load)


def component_for(pages):
    component = Textbooks(synthetic_profiles(pages))
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
                "citation": {"form": TextbookAttribution.FORMS[source]},
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
    assert obj.spec["operation_specs"]["verbatim_section"]["frozen_count"] == FROZEN_COUNT
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
        assert [c.outcome for c in candidates] == ["accepted", "withheld"]
        assert candidates[-1].reason == "next_heading_unresolved"
        assert [v.text for v in candidates[0].response] == ["\nSYNTHETIC first body\n", "SYNTHETIC continuation\n"]
        assert [v.text for v in candidates[0].slots] == ["SYNTHETIC Book", "5 класу", "§ 1. SYNTHETIC First"]
        records, report = gate_for(reader, pages, 2).run(candidates)
        assert len(records) == 1
        assert report["accounting"]["C9"]["accepted"] == 1
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
        "Розділ I SYNTHETIC",
        "Розділ ІІІ SYNTHETIC",
        "ТЕМА 2 SYNTHETIC",
        "§ 2–3. SYNTHETIC Title",
        "§ 5\nSYNTHETIC TITLE",
        "§ 5\nSYNTHETIC Mixed title",
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
    pages = [
        page(1, imprint()),
        page(2, "§ 1. SYNTHETIC One\nSYNTHETIC prose A\n" + next_heading + "\nSYNTHETIC prose B"),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidates = extract(reader, pages)
        assert len(set(c.unit_id for c in candidates)) == 2
        assert "SYNTHETIC prose B" not in candidates[0].response[0].text
        assert len(gate_for(reader, pages, 2).run(candidates)[0]) == 1


def test_next_heading_midpage_includes_that_pages_prefix(tmp_path):
    pages = [
        page(1, imprint()),
        page(2, "§ 1. SYNTHETIC One\nSYNTHETIC prose A"),
        page(3, "SYNTHETIC continuation\n§ 2. SYNTHETIC Two\nSYNTHETIC prose B"),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidates = extract(reader, pages)
        assert len(candidates[0].response) == 2
        assert candidates[0].response[-1].text == "SYNTHETIC continuation\n"
        assert len(gate_for(reader, pages, 2).run(candidates)[0]) == 1


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
    pages[-1]["full_text"] += "§ 2. SYNTHETIC Next\nSYNTHETIC final prose\n2\n"
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidate = extract(reader, pages)[0]
        assert candidate.outcome == "accepted"
        assert "hy-\nphen" in candidate.response[0].text
        assert len(gate_for(reader, pages, 2).run(extract(reader, pages))[0]) == 1


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
        "authors": ("SYNTHETIC prose Author", ""),
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
    assert identity(pages, synthetic_profiles(pages)).text("title") == "SYNTHETIC Book"
    assert identity(pages, {}) is None
    pages = [
        page(1, imprint()),
        page(2, "SYNTHETIC preface\n§ 1. SYNTHETIC Heading\nSYNTHETIC body"),
        page(3, "SYNTHETIC preface\n§ 1. SYNTHETIC Heading\nSYNTHETIC other body"),
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
            list(
                Textbooks(synthetic_profiles(_pages)).iter_candidates(
                    ComponentContext(reader, {"schema": "omd-review-request.v2"})
                )
            )


def test_university_grade_zero_admitted_from_filename_with_printed_level(tmp_path):
    pages = [
        page(1, imprint(grade="студентів"), book="uni-SYNTHETIC-book"),
        page(2, "§ 1. SYNTHETIC Heading\nSYNTHETIC body", book="uni-SYNTHETIC-book"),
    ]
    pages[-1]["full_text"] += "§ 2. SYNTHETIC Next\nSYNTHETIC final prose\n2\n"
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidate = extract(reader, pages)[0]
        assert candidate.outcome == "accepted"
        assert candidate.slots[1].text == "студентів"
        assert candidate.slots[1].citations[0].source_id == SOURCE_UNIVERSITY
        assert len(gate_for(reader, pages, 2).run(extract(reader, pages))[0]) == 1


@pytest.mark.parametrize(
    "form",
    [
        "Author(s), title, grade, publisher, year, page — for every quoted sentence.",
        "{authors}. {title}. {grade}. {publisher}, <year>.",
        "SYNTHETIC insert citation",
        "{authors}. {title}. {grade}. {publisher}, {year}.",
        "<author(s)>. <title>. <level>. <publisher>, <year>. С. <page>.",
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
        form = TextbookAttribution.FORMS[SOURCE_SCHOOL]
        result = TextbookAttribution().resolve(form, citation(pages[2]), pages[2], reader)
        assert result.mapped_form == form
        assert (
            result.bibliography == "SYNTHETIC prose Author. SYNTHETIC Book. 5 класу. SYNTHETIC Publisher, 2025. С. 3."
        )
        assert ("section_id=1", digest(pages[0]["full_text"].encode())) in reader.reads[
            ("sources.db", "textbook_sections")
        ]


@pytest.mark.parametrize(
    "book,level,source_id,form",
    [
        (
            "5-klas-SYNTHETIC-book",
            "5 класу",
            "textbooks",
            "<author(s)>. <title>. <grade>. <publisher>, <year>. С. <page>.",
        ),
        (
            "uni-SYNTHETIC-book",
            "студентів",
            "textbooks_university",
            "<author(s)>. <title>. <level>. <publisher>, <year>. С. <page>.",
        ),
    ],
)
def test_register_forms_resolve_every_cited_page(tmp_path, book, level, source_id, form):
    pages = [page(1, imprint(grade=level), book)] + [
        page(i, f"§ {i}. SYNTHETIC Heading\nSYNTHETIC body", book) for i in (2, 3)
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    root = Path(__file__).resolve().parents[5]
    register = yaml.safe_load((root / "docs/sources/permissions-register.yaml").read_bytes())
    entry = next(entry for entry in register["sources"] if entry["id"] == source_id)
    assert entry["citation"]["form"] == form
    with SnapshotReader({"sources.db": path}) as reader:
        resolver = Resolver(register, component_for(pages).adapters)
        for row in pages:
            licence, attribution = resolver.resolve(citation(row), reader)
            assert f"permissions-register.yaml#{source_id};" in licence
            assert attribution == (
                f"SYNTHETIC prose Author. SYNTHETIC Book. {level}. SYNTHETIC Publisher, 2025. "
                f"С. {row['page_start']}.; printed page {row['page_start']}"
            )
        with pytest.raises(BuildError, match="attribution_unresolved"):
            TextbookAttribution().resolve(form, replace(citation(pages[1]), source_id="obsolete"), pages[1], reader)


@pytest.mark.parametrize("number", [None, -1, "3", True])
def test_attribution_refuses_unresolved_page(source, number):
    path, pages = source
    with SnapshotReader({"sources.db": path}) as reader:
        with pytest.raises(BuildError, match="attribution_unresolved"):
            TextbookAttribution().resolve(
                TextbookAttribution.FORMS[SOURCE_SCHOOL], citation(pages[2]), {**pages[2], "page_start": number}, reader
            )


@pytest.mark.parametrize("area", ["heading", "body", "imprint"])
def test_source_reasoning_markers_withhold_without_rewriting(tmp_path, area):
    pages = [
        page(1, imprint(book="SYNTHETIC Step 1 Book" if area == "imprint" else "SYNTHETIC Book")),
        page(
            2,
            "§ 1. SYNTHETIC Heading"
            + (" Step 1" if area == "heading" else "")
            + "\nSYNTHETIC body"
            + (" Step 1" if area == "body" else ""),
        ),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidate = extract(reader, pages)[0]
        assert candidate.outcome == "withheld"
        expected = "table_of_contents" if area in {"heading", "body"} else "next_heading_unresolved"
        assert candidate.reason == expected
        assert candidate.evidence
        assert candidate.response[0].text.endswith("\n")
        assert "2\n" not in candidate.response[0].text
        records, report = gate_for(reader, pages, 1).run([candidate])
        assert records == []
        assert report["accounting"]["C9"]["reasons"] == {expected: 1}
        with pytest.raises(BuildError, match="reasoning_text"):
            gate_for(reader, pages, 1).run(
                [replace(candidate, outcome="accepted", reason="printed_heading", evidence=())]
            )


def test_page_number_removal_has_exact_trace_and_preserves_other_lines():
    text = "SYNTHETIC top\n  23 \r\nSYNTHETIC 24\nSYNTHETIC hy-\nphen"
    result = transform("line_excision@1", text, {"patterns": LINE_POLICY["patterns"]})
    assert result.text == "SYNTHETIC top\nSYNTHETIC 24\nSYNTHETIC hy-\nphen"
    assert result.dropped_lines == ((2, 2),)
    assert not result.joins
    assert not ocr_damaged(result.text)


def test_ordinary_running_heads_are_excised_with_exact_trace(tmp_path):
    pages = [page(1, imprint())] + [
        page(
            i,
            "SYNTHETIC running title\n"
            + ("§ 1. SYNTHETIC Heading\n" if i == 2 else "")
            + f"SYNTHETIC body {i} prose\n{i}\n",
        )
        for i in range(2, 6)
    ]
    assert running_head_ambiguous(pages)
    assert not running_head_ambiguous([page(i, f"{i}\nSYNTHETIC distinct {i}\n{i}") for i in range(1, 6)])
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidate = extract(reader, pages)[0]
        assert all("SYNTHETIC running title" not in part.text for part in candidate.response)
        assert candidate.reason == "next_heading_unresolved"


def test_imprint_wrong_field_span_must_fail_even_with_authentic_quote(source):
    path, pages = source
    with SnapshotReader({"sources.db": path}) as reader:
        candidate = extract(reader, pages)[0]
        item = identity(pages, synthetic_profiles(pages))
        title = candidate.slots[0]
        title = replace(title, text=item.text("publisher"), span=item.fields["publisher"])
        candidate = replace(candidate, slots=(title, *candidate.slots[1:]))
        gate_for(reader, pages, 2).quote(candidate)
        with pytest.raises(BuildError, match="binding_set"):
            bindings.check(
                candidate,
                component_for(pages).spec["operation_specs"]["verbatim_section"]["binding"],
                reader,
                {"line_excision@1": LINE_POLICY},
            )


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
        page(i + 2, f"§ {i + 1}. SYNTHETIC Heading {i} text\nSYNTHETIC body {i} prose") for i in range(12)
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
                "citation": {"form": TextbookAttribution.FORMS[source]},
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
    assert manifest["accounting"]["C9"]["accepted"] == 11
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


@pytest.mark.parametrize("position", ["top", "bottom"])
def test_later_edge_heading_is_excised_not_counted(tmp_path, position):
    title = "§ 1. SYNTHETIC Heading"
    later = (
        f"  3\n  {title}  \nSYNTHETIC continuation\n"
        if position == "top"
        else f"SYNTHETIC continuation\n  {title}  \n3\n"
    )
    pages = [
        page(1, imprint()),
        page(2, title + "\nSYNTHETIC body\n2\n"),
        page(3, later),
        page(4, "§ 2. SYNTHETIC Next\nSYNTHETIC next body\n"),
    ]
    db = tmp_path / "SYNTHETIC.db"
    write_pages(db, pages)
    with SnapshotReader({"sources.db": db}) as reader:
        candidates = extract(reader, pages)
        assert len(candidates) == 2
        assert {c.unit_id for c in candidates} == set(reader.units(UNIT_QUERY))
        records, _ = gate_for(reader, pages, 2).run(candidates)
        assert len(records) == 1
        assert candidates[0].response[1].text == "SYNTHETIC continuation\n"
        trace = transform("line_excision@1", later, LINE_POLICY, reader, citation(pages[2]))
        assert trace.dropped_lines == (((1, 1), (2, 2)) if position == "top" else ((2, 2), (3, 3)))
        assert title == candidates[0].slots[-1].text
        # Restoring a running head remains an authentic quote of the wrong transform.
        damaged = replace(candidates[0].response[1], text=title + "\nSYNTHETIC continuation\n")
        with pytest.raises(BuildError, match="quote_mismatch"):
            gate_for(reader, pages, 2).quote(replace(candidates[0], response=(candidates[0].response[0], damaged)))


def test_contents_occurrence_does_not_remove_real_section_opening(tmp_path):
    title = "§ 1. SYNTHETIC Heading"
    pages = [
        page(1, imprint()),
        page(2, "ЗМІСТ\n" + title + "\nSYNTHETIC ... 3\n"),
        page(3, title + "\nSYNTHETIC body\n"),
        page(4, title + "\nSYNTHETIC continuation\n"),
    ]
    db = tmp_path / "SYNTHETIC.db"
    write_pages(db, pages)
    with SnapshotReader({"sources.db": db}) as reader:
        candidates = extract(reader, pages)
        assert [c.reason for c in candidates] == ["table_of_contents", "next_heading_unresolved"]
        assert len(reader.units(UNIT_QUERY)) == 2
        assert len(gate_for(reader, pages, 2).run(candidates)[0]) == 0


@pytest.mark.parametrize("dash", ["—", "–", "-"])
@pytest.mark.parametrize("level", ["5 кл.", "5 класу"])
def test_printed_imprint_abbreviations_and_dash_variants(tmp_path, dash, level):
    pages = [
        page(1, imprint(grade=level).replace(" — ", f" {dash} ").replace("підручник", "підручн.")),
        page(2, "§ 1. SYNTHETIC Heading\nSYNTHETIC body"),
    ]
    pages[-1]["full_text"] += "§ 2. SYNTHETIC Next\nSYNTHETIC final prose\n2\n"
    db = tmp_path / "SYNTHETIC.db"
    write_pages(db, pages)
    with SnapshotReader({"sources.db": db}) as reader:
        candidates = extract(reader, pages)
        assert candidates[0].outcome == "accepted"
        assert candidates[0].slots[1].text == level
        assert len(gate_for(reader, pages, 2).run(candidates)[0]) == 1


def test_row_scoped_excision_requires_authenticated_citation(source):
    db, pages = source
    with SnapshotReader({"sources.db": db}) as reader:
        with pytest.raises(BuildError, match="transform_policy"):
            transform("line_excision@1", pages[1]["full_text"], LINE_POLICY, reader)
        with pytest.raises(BuildError, match="transform_policy"):
            transform(
                "line_excision@1",
                pages[1]["full_text"],
                LINE_POLICY,
                reader,
                replace(citation(pages[1]), table="other"),
            )


def test_same_text_in_different_books_keeps_both_first_occurrences(tmp_path):
    pages = [
        page(1, imprint()),
        page(2, "§ 1. SYNTHETIC Heading\nSYNTHETIC body"),
        page(3, imprint(), book="6-klas-SYNTHETIC-other"),
        page(4, "§ 1. SYNTHETIC Heading\nSYNTHETIC other body", book="6-klas-SYNTHETIC-other"),
    ]
    db = tmp_path / "SYNTHETIC.db"
    write_pages(db, pages)
    with SnapshotReader({"sources.db": db}) as reader:
        candidates = extract(reader, pages)
        assert len(candidates) == len(reader.units(UNIT_QUERY)) == 2
        assert len(gate_for(reader, pages, 2).run(candidates)[0]) == 0


def test_identical_interior_bodies_are_not_ambiguous(tmp_path):
    body = "SYNTHETIC body\nSYNTHETIC next prefix\n"
    pages = [
        page(1, imprint()),
        page(2, "SYNTHETIC prefix\n§ 1. SYNTHETIC Heading\n" + body),
        page(3, "§ 2. SYNTHETIC Next\nSYNTHETIC divider\nSYNTHETIC prefix\n§ 1. SYNTHETIC Heading\n" + body),
    ]
    db = tmp_path / "SYNTHETIC.db"
    write_pages(db, pages)
    with SnapshotReader({"sources.db": db}) as reader:
        candidates = extract(reader, pages)
        repeated = [c for c in candidates if c.slots[-1].text == "§ 1. SYNTHETIC Heading"]
        assert len(repeated) == 2
        assert {c.reason for c in repeated} == {"printed_heading", "next_heading_unresolved"}
        assert len(gate_for(reader, pages, 3).run(candidates)[0]) == 2


def test_manifest_records_running_head_occurrences_even_when_withheld(tmp_path, source):
    from scripts.projects.open_model_data.review_build.build import artifacts

    _db, original = source
    pages = [original[0], original[1], page(3, "§ 1. SYNTHETIC First\nSYNTHETIC continuation\n3\n"), original[3]]
    write_pages(tmp_path / "SYNTHETIC-running.db", pages)
    with SnapshotReader({"sources.db": tmp_path / "SYNTHETIC-running.db"}) as reader:
        gate = gate_for(reader, pages, 2)
        candidates = extract(reader, pages)
        # The real host's unresolved register similarly withholds extraction successes.
        gate.resolver.entries = {}
        pins = {
            "register": "a" * 64,
            "catalog": "b" * 64,
            "code": {"code_sha": "c" * 40, "parser_sha256": "d" * 64},
            "candidates": "e" * 64,
            "spec": "f" * 64,
        }
        files = artifacts({"components": gate.components}, candidates, reader, gate.catalog, gate.resolver, pins)
        manifest = json.loads(files["manifest.json"])
        assert [
            r for r in manifest["excisions"]["C9"] if r["row_key"] == "section_id=3" and r["line_ranges"] == [[1, 1]]
        ] == [
            {
                "kind": "running_head_occurrence",
                "row_key": "section_id=3",
                "line_ranges": [[1, 1]],
                "store": "sources.db",
                "table": "textbook_sections",
                "field": "full_text",
                "field_sha256": digest(pages[2]["full_text"].encode()),
            }
        ]


def test_decimal_line_is_not_a_contents_page(tmp_path):
    title = "§ 1. SYNTHETIC Heading"
    pages = [
        page(1, imprint()),
        page(2, title + "\nSYNTHETIC body\n"),
        page(3, title + "\nSYNTHETIC ... 1.2\nSYNTHETIC continuation\n"),
    ]
    db = tmp_path / "SYNTHETIC.db"
    write_pages(db, pages)
    with SnapshotReader({"sources.db": db}) as reader:
        candidates = extract(reader, pages)
        assert len(candidates) == len(reader.units(UNIT_QUERY)) == 1
        assert len(gate_for(reader, pages, 1).run(candidates)[0]) == 0


def test_ambiguous_repeat_does_not_withhold_unrelated_title(tmp_path):
    title = "§ 1. SYNTHETIC Heading"
    pages = [
        page(1, imprint()),
        page(2, "SYNTHETIC prefix\n" + title + "\nSYNTHETIC body\n"),
        page(3, "SYNTHETIC prefix\n" + title + "\nSYNTHETIC other body\n"),
        page(4, "§ 2. SYNTHETIC Next\nSYNTHETIC unrelated body\n"),
    ]
    db = tmp_path / "SYNTHETIC.db"
    write_pages(db, pages)
    with SnapshotReader({"sources.db": db}) as reader:
        candidates = extract(reader, pages)
        assert [c.reason for c in candidates] == ["repeated_heading", "repeated_heading", "next_heading_unresolved"]
        assert len(gate_for(reader, pages, 3).run(candidates)[0]) == 0


def test_running_head_only_page_is_pinned_with_original_range(tmp_path):
    from scripts.projects.open_model_data.review_build.transforms import line_excision_records

    title = "§ 1. SYNTHETIC Heading"
    pages = [page(1, imprint()), page(2, title + "\nSYNTHETIC body\n"), page(3, title + "\n3\n")]
    db = tmp_path / "SYNTHETIC.db"
    write_pages(db, pages)
    with SnapshotReader({"sources.db": db}) as reader:
        candidates = extract(reader, pages)
        assert len(candidates) == len(reader.units(UNIT_QUERY)) == 1
        assert candidates[0].reason == "next_heading_unresolved"
        assert candidates[0].response[-1].text == ""
        assert candidates[0].response[-1].span is None
        assert len(gate_for(reader, pages, 1).run(candidates)[0]) == 0
        records = line_excision_records(LINE_POLICY, reader)
        records = [r for r in records if r["row_key"] == "section_id=3"]
        assert records[0]["line_ranges"] == [[1, 1]]
        expected_hash = digest(pages[2]["full_text"].encode())
        assert records[0]["field_sha256"] == expected_hash
        assert ("section_id=3", expected_hash) in reader.reads[("sources.db", "textbook_sections")]


def test_excision_query_results_cannot_forge_source_field(source):
    from scripts.projects.open_model_data.review_build.transforms import queried_lines

    db, _pages = source
    policy = {
        **LINE_POLICY,
        "line_query": {
            "kind": "sql",
            "store": "sources.db",
            "sql": "SELECT json_array('section_id=2',1,'SYNTHETIC forged field')",
            "parameters": [],
        },
    }
    with SnapshotReader({"sources.db": db}) as reader:
        with pytest.raises(BuildError, match="field_digest"):
            queried_lines(policy, reader)


def test_first_page_top_opening_and_later_interior_body_are_ambiguous(tmp_path):
    # The first occurrence is the real opening, even when it is at page top.
    # The later interior occurrence cannot be classified as a running head.
    title = "§ 1. SYNTHETIC Heading"
    pages = [
        page(1, imprint()),
        page(2, title + "\nSYNTHETIC body\n"),
        page(3, "SYNTHETIC prefix\n" + title + "\nSYNTHETIC other body\n"),
    ]
    db = tmp_path / "SYNTHETIC.db"
    write_pages(db, pages)
    with SnapshotReader({"sources.db": db}) as reader:
        candidates = extract(reader, pages)
        assert len(candidates) == len(reader.units(UNIT_QUERY)) == 2
        assert {c.reason for c in candidates} == {"repeated_heading"}


@pytest.mark.parametrize(
    "body,reason",
    [
        ("SYNTHETIC title . . . . 33", "table_of_contents"),
        ("SYNTHETIC title 33", "table_of_contents"),
        ("116. Прочитайте SYNTHETIC prose", "exercise_without_answer"),
        ("3. Перепишіть SYNTHETIC prose", "exercise_without_answer"),
        ("Питання\nSYNTHETIC question", "exercise_without_answer"),
        (
            "Вправа 1\nSYNTHETIC question\nВідповідь\nSYNTHETIC answer\nВправа 2\nSYNTHETIC question",
            "exercise_without_answer",
        ),
        ("SYNTHETIC \uf8eb damage", "ocr_damage"),
        ("SYNTHETIC \U000f0000 damage", "ocr_damage"),
        ("§ 7X SYNTHETIC unparsed heading", "unparsed_heading_in_body"),
        ("Урок 2. SYNTHETIC missed heading", "unparsed_heading_in_body"),
        pytest.param("SYNTHETIC prose " * 2000, "body_size_bound", id="size-bound"),
    ],
)
def test_round4_must_fail_screens(tmp_path, body, reason):
    pages = [
        page(1, imprint()),
        page(2, "§ 1. SYNTHETIC Heading\n" + body),
        page(3, "§ 2. SYNTHETIC Next\nSYNTHETIC final prose"),
        page(4, "SYNTHETIC distinct final prose"),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidate = extract(reader, pages)[0]
        assert candidate.outcome == "withheld"
        assert candidate.reason == reason


@pytest.mark.parametrize("field", ["title", "authors", "grade", "publisher", "year"])
@pytest.mark.parametrize("drift", ["text", "lines", "columns", "offsets"])
def test_profile_field_drift_refuses(field, drift):
    pages = [page(1, imprint()), page(2, "§ 1. SYNTHETIC Heading\nSYNTHETIC body")]
    profiles = synthetic_profiles(pages)
    profile = profiles[pages[0]["source_file"]]
    if drift == "text":
        profile["fields"][field]["text"] += "invented"
    elif drift in {"lines", "columns"}:
        profile["fields"][field][drift][0] += 1
    else:
        profile["field_offsets"][field][0] += 1
    assert identity(pages, profiles) is None


def test_no_profile_never_discovers_footnote_or_bibliography_identity(tmp_path):
    pages = [
        page(1, "SYNTHETIC title page without identity"),
        page(2, "§ 1. SYNTHETIC Heading\nSYNTHETIC body\n1. " + imprint("SYNTHETIC Other Book")),
        page(3, "§ 2. SYNTHETIC Next\nSYNTHETIC body"),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    component = Textbooks({})
    component.spec["compatibility"] = compatibility({pages[0]["source_file"]})
    with SnapshotReader({"sources.db": path}) as reader:
        assert {c.reason for c in component.iter_candidates(ComponentContext(reader, {}))} == {
            "book_identity_unresolved"
        }


@pytest.mark.parametrize("code", ["З-380", "Б63", "І11", "Щ96", "Г 87", "З-3310"])
def test_catalogue_code_is_stripped_by_rule(code):
    pages = [page(1, imprint(book=code + " SYNTHETIC Book"))]
    item = identity(pages, synthetic_profiles(pages))
    assert item.text("title") == "SYNTHETIC Book"
    assert pages[0]["full_text"][slice(*item.fields["title"])] == "SYNTHETIC Book"


def test_multiline_identity_is_reverified_verbatim():
    pages = [page(1, imprint(book="SYNTHETIC wrapped\nBook"))]
    profiles = synthetic_profiles(pages)
    from scripts.projects.open_model_data.review_build.components.c9_profile_candidates import locator

    profile = profiles[pages[0]["source_file"]]
    start, end = 0, profile["field_offsets"]["title"][1]
    profile["fields"]["title"], profile["field_offsets"]["title"] = locator(pages[0]["full_text"], start, end)
    assert identity(pages, profiles).text("title") == "SYNTHETIC wrapped\nBook"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("45\nSYNTHETIC prose", 45),
        ("SYNTHETIC prose\n45", 45),
        ("45SYNTHETIC running head\nSYNTHETIC prose", 45),
        ("SYNTHETIC prose\nSYNTHETIChead45", 45),
        ("SYNTHETIC prose\nnumber inside 45\nSYNTHETIC prose", None),
        ("45\nSYNTHETIC prose\n46", None),
    ],
)
def test_printed_page_is_derived_only_from_unique_edge_number(text, expected):
    from scripts.projects.open_model_data.review_build.components.c9 import printed_page

    assert printed_page({"full_text": text, "page_start": 999}) == expected


def test_printed_page_unresolved_withholds_unit(tmp_path):
    pages = [
        page(1, imprint()),
        page(2, "§ 1. SYNTHETIC Heading\nSYNTHETIC body"),
        page(3, "§ 2. SYNTHETIC Next\nSYNTHETIC final prose"),
    ]
    pages[1]["full_text"] = "§ 1. SYNTHETIC Heading\nSYNTHETIC body"
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        assert extract(reader, pages)[0].reason == "printed_page_unresolved"


def test_attribution_uses_printed_page_and_single_full_stops(source):
    path, pages = source
    profiles = synthetic_profiles(pages)
    profiles[pages[0]["source_file"]]["fields"]["authors"]["text"] = "SYNTHETIC Author"
    # Existing source span includes punctuation in a separate fixture below.
    with SnapshotReader({"sources.db": path}) as reader:
        row = dict(pages[1])
        row["full_text"] = "SYNTHETIC prose\n47\n"
        result = TextbookAttribution().resolve(TextbookAttribution.FORMS[SOURCE_SCHOOL], citation(row), row, reader)
        assert "С. 47." in result.bibliography
        assert ".." not in result.bibliography


def test_fused_chapter_running_heads_are_excised_and_interior_survivor_withholds(tmp_path):
    pages = [
        page(1, imprint()),
        page(2, "12SYNTHETIC chapter\n§ 1. SYNTHETIC Heading\nSYNTHETIC body", number=12),
        page(3, "13SYNTHETIC chapter\nSYNTHETIC prose\nSYNTHETIC chapter\nSYNTHETIC tail", number=13),
        page(4, "§ 2. SYNTHETIC Next\nSYNTHETIC final prose", number=14),
    ]
    # The first/last actual lines carry fused numbers, no second numeric footer.
    for p in pages[1:3]:
        p["full_text"] = p["full_text"].rsplit("\n", 2)[0]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidate = extract(reader, pages)[0]
        assert candidate.reason == "running_head_unresolved"
        assert "12SYNTHETIC" not in candidate.response[0].text
        assert "13SYNTHETIC" not in candidate.response[1].text
        assert "SYNTHETIC chapter" in candidate.response[1].text


def test_line_excision_counts_lf_not_unicode_line_separators():
    result = transform("line_excision@1", "SYNTHETIC\u2028prose\n3\nSYNTHETIC tail", {"patterns": [r"3"]})
    assert result.text == "SYNTHETIC\u2028prose\nSYNTHETIC tail"
    assert result.dropped_lines == ((2, 2),)


@pytest.mark.parametrize("continuation", ["SYNTHETIC CHAPTER", "SYNTHETIC DIFFERENT"])
def test_multiline_running_head_uses_complete_title_for_identity(tmp_path, continuation):
    pages = [
        page(1, imprint()),
        page(2, "§ 1\nSYNTHETIC CHAPTER\nSYNTHETIC body"),
        page(3, "§ 1\n" + continuation + "\nSYNTHETIC continuation prose"),
        page(4, "§ 2. SYNTHETIC Next\nSYNTHETIC final prose"),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidates = extract(reader, pages)
        assert {c.unit_id for c in candidates} == set(reader.units(UNIT_QUERY))
        assert len(candidates) == (2 if continuation == "SYNTHETIC CHAPTER" else 3)


def test_interior_number_does_not_make_ordinary_numeric_tail_a_toc_page(tmp_path):
    pages = [
        page(1, imprint()),
        page(2, "§ 1. SYNTHETIC Heading\nSYNTHETIC sentence number 1, next 2. 3"),
        page(3, "§ 1. SYNTHETIC Heading\nSYNTHETIC continuation prose"),
        page(4, "§ 2. SYNTHETIC Next\nSYNTHETIC final prose"),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        candidates = extract(reader, pages)
        assert len(candidates) == 2
        assert {c.unit_id for c in candidates} == set(reader.units(UNIT_QUERY))
        assert len(gate_for(reader, pages, 2).run(candidates)[0]) == 1


def test_profile_candidate_cli_readonly_input_and_exclusive_output(tmp_path, capsys):
    from scripts.projects.open_model_data.review_build.components.c9_profile_candidates import main

    database = tmp_path / "SYNTHETIC.db"
    write_pages(database, [page(1, imprint())])
    before = database.read_bytes()
    out = tmp_path / "SYNTHETIC.json"
    main(["--database", str(database), "--out", str(out)])
    assert json.loads(capsys.readouterr().out) == {"candidate_books": 1}
    assert database.read_bytes() == before
    assert out.stat().st_mode & 0o777 == 0o600
    assert json.loads(out.read_text())["schema"] == "c9-profile-candidates.v1"
    with pytest.raises(FileExistsError):
        main(["--database", str(database), "--out", str(out)])
    with pytest.raises(SystemExit) as exc:
        main(["--database", "SYNTHETIC.db", "--out", str(out)])
    assert exc.value.code == 2


@pytest.mark.parametrize(
    "body,is_toc",
    [
        ("SYNTHETIC title π 2", True),
        ("SYNTHETIC title æ 3", True),
        ("SYNTHETIC title τ 1", True),
        ("SYNTHETIC title . . . . 12345", True),
        ("SYNTHETIC prose number 12345", False),
        ("SYNTHETIC prose number 2. 3", False),
    ],
)
def test_toc_shape_sql_parity_with_unicode_and_numeric_tail(tmp_path, body, is_toc):
    from scripts.projects.open_model_data.review_build.components.c9 import contents_page
    from scripts.projects.open_model_data.review_build.components.c9_queries import CTE

    pages = [page(1, body)]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    sql = CTE + "SELECT contents FROM page_flags"
    with SnapshotReader({"sources.db": path}) as reader:
        assert bool(reader.connections["sources.db"].execute(sql).fetchone()[0]) == is_toc
    assert contents_page(pages[0]["full_text"]) is is_toc


@pytest.mark.parametrize("label", ["ПАРАГРАФ", "ТЕМА«", "РОЗДІЛ\t", "УРОК"])
def test_bare_marker_does_not_join_heading_like_uppercase_line(tmp_path, label):
    pages = [page(1, "§ 1\n" + label + " SYNTHETIC HEADING\nSYNTHETIC body")]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    assert headings(pages[0]) == []
    with SnapshotReader({"sources.db": path}) as reader:
        assert reader.units(UNIT_QUERY) == []


@pytest.mark.parametrize(
    "verb",
    ["Поцікавтеся", "Поділіться", "Ознайомтеся", "Зверніться", "Переконайтеся",
     "Проаналізуйте", "Відредагуйте", "Презентуйте", "Перекажіть", "Опишіть",
     "Розкажіть", "Сформулюйте", "Поставте", "Продовжте", "Виберіть", "Уявіть",
     "Одягніть", "Зафіксуйте", "Закручуйте", "Обгорніть", "Протягніть",
     "Напишіть", "Обґрунтуйте", "Наведіть", "Схарактеризуйте"],
)
def test_numbered_verified_imperatives_require_their_own_printed_answer(tmp_path, verb):
    from scripts.projects.open_model_data.review_build.components.c9 import exercise_without_answer

    assert exercise_without_answer("12. " + verb + " SYNTHETIC prompt")
    assert not exercise_without_answer("12. " + verb + " SYNTHETIC prompt\nВідповідь\nSYNTHETIC answer")
    pages = [
        page(1, imprint()),
        page(2, "§ 1. SYNTHETIC Heading\n12. " + verb + " SYNTHETIC prompt"),
        page(3, "§ 2. SYNTHETIC Next\nSYNTHETIC final prose"),
    ]
    path = tmp_path / "SYNTHETIC.db"
    write_pages(path, pages)
    with SnapshotReader({"sources.db": path}) as reader:
        assert extract(reader, pages)[0].reason == "exercise_without_answer"
