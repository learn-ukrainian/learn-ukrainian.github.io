"""Applied #9609 register rows and RB-1 attribution contracts."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def rows():
    return {
        row["id"]: row
        for row in yaml.safe_load((ROOT / "docs/sources/permissions-register.yaml").read_text())["sources"]
    }


def test_all_pending_rows_are_applied():
    register = rows()
    assert {"zno_nmt", "pravopys_2019", "pohribnyi_1992", "textbooks_university"} <= register.keys()
    assert not (ROOT / "registry/projects/open_model_data/register_rows_pending.yaml").exists()


def test_pohribnyi_is_provenance_only_after_o7():
    row = rows()["pohribnyi_1992"]
    assert row["appears_in"] == ["internal"]
    assert row["fields_used"] == ["provenance"]
    assert "O7" in row["role"] and "no component or ruler" in row["role"]


def test_textbook_templates_request_bibliographic_fields_from_imprints():
    register = rows()
    for id, level in (("textbooks", "grade"), ("textbooks_university", "level")):
        form = register[id]["citation"]["form"]
        assert all("<" + field + ">" in form for field in ("author(s)", "title", level, "publisher", "year", "page"))
        assert "for every quoted sentence" not in form


def test_sum11_cites_held_headword_and_keeps_red_flag():
    row = rows()["sum11"]
    form = row["citation"]["form"]
    assert "<headword>" in form and "red-flagged" in form
    assert "<vol>" not in form and "<page>" not in form
    assert "never" in row["usage_restriction"].lower()


def test_phraseology_edition_is_applied_and_twin_is_current():
    row = rows()["frazeolohichnyi"]
    evidence = yaml.safe_load(
        (ROOT / "registry/projects/open_model_data/sources/frazeolohichnyi_edition.yaml").read_text()
    )
    assert evidence["verdict"] == "verified" and evidence["edition"]["volumes"] == 1
    assert evidence["edition"]["isbn"] in row["citation"]["form"]
    assert row["open_questions"] == []


def test_antonenko_records_unknown_edition_and_uses_section_locator():
    row = rows()["antonenko_style_guide"]
    assert "<section>" in row["citation"]["form"]
    assert "<page>" in row["citation"]["form"]
    assert "positive held page" in row["citation"]["form"]
    assert "page null or 0" in row["citation"]["form"]
    assert "unverified" in row["provenance"]["retrieved_evidence"]
    assert any("edition is unverified" in q for q in row["open_questions"])


def test_markdown_mirrors_each_added_or_amended_citation_exactly():
    md = (ROOT / "docs/sources/permissions-register.md").read_text()
    for id in (
        "zno_nmt",
        "pravopys_2019",
        "pohribnyi_1992",
        "textbooks_university",
        "textbooks",
        "sum11",
        "antonenko_style_guide",
        "frazeolohichnyi",
    ):
        assert rows()[id]["citation"]["form"] in md
    assert "probably «Словник фразеологізмів" not in md
