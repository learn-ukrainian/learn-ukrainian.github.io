"""Validate the source permissions register (#8979).

The register (`docs/sources/permissions-register.yaml`) records, per
(source, field, scale), the status of every use: acquire, store, transform,
display on the site, redistribute in the dataset / off-site Atlas export.
Build gates read it, so a malformed or incomplete register must fail here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTER_YAML = REPO_ROOT / "docs" / "sources" / "permissions-register.yaml"
REGISTER_MD = REPO_ROOT / "docs" / "sources" / "permissions-register.md"
SCHEMA = REPO_ROOT / "schemas" / "permissions-register.schema.json"

USES = ("acquire", "store", "transform", "display", "redistribute")
STATUSES = {"permitted", "assessed", "unknown", "refused"}

# The denominator named in the #8979 dispatch brief; more sources may be listed.
REQUIRED_SOURCES = {
    "ulif",
    "vesum",
    "sum20",
    "slovnyk_me",
    "grinchenko",
    "esum",
    "grac",
    "textbooks",
    "teacher_materials",
    "sum11",
    "ua_gec",
    "ukrajinet",
    "wiktionary",
    "goroh",
}


@pytest.fixture(scope="module")
def register() -> dict:
    return yaml.safe_load(REGISTER_YAML.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sources(register: dict) -> list[dict]:
    return register["sources"]


def test_register_matches_schema(register: dict) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(register), key=lambda e: list(e.absolute_path))
    assert not errors, "\n".join(f"{list(e.absolute_path)}: {e.message}" for e in errors)


def test_uses_and_statuses_are_the_closed_sets(register: dict) -> None:
    assert tuple(register["uses"]) == USES
    assert set(register["statuses"]) == STATUSES


def test_one_gate_for_dataset_and_atlas_export(register: dict) -> None:
    gates = register["gates"]
    assert gates["site_display"]["use"] == "display"
    assert gates["dataset_and_atlas_export"]["use"] == "redistribute"
    for gate in gates.values():
        assert "unknown" not in gate["publish_if"]
        assert "refused" not in gate["publish_if"]


def test_required_sources_present_and_ids_unique(sources: list[dict]) -> None:
    ids = [s["id"] for s in sources]
    assert len(ids) == len(set(ids)), "duplicate source id"
    missing = REQUIRED_SOURCES - set(ids)
    assert not missing, f"register is missing sources: {sorted(missing)}"


def test_every_row_states_every_use_with_an_allowed_status(sources: list[dict]) -> None:
    for source in sources:
        for row in source["permissions"]:
            assert tuple(row["uses"]) == USES, f"{source['id']}: uses out of order or incomplete"
            for use, entry in row["uses"].items():
                assert entry["status"] in STATUSES, f"{source['id']}.{use}: {entry['status']}"


def test_every_field_used_is_covered_and_rows_name_only_used_fields(sources: list[dict]) -> None:
    for source in sources:
        used = set(source["fields_used"])
        covered: set[str] = set()
        for row in source["permissions"]:
            stray = set(row["fields"]) - used
            assert not stray, f"{source['id']}: row names fields not in fields_used: {sorted(stray)}"
            covered |= set(row["fields"])
        assert covered == used, f"{source['id']}: fields without a permission row: {sorted(used - covered)}"


def test_field_scale_pairs_are_not_duplicated(sources: list[dict]) -> None:
    for source in sources:
        seen: set[tuple[str, str]] = set()
        for row in source["permissions"]:
            for field in row["fields"]:
                key = (field, row["scale"])
                assert key not in seen, f"{source['id']}: {key} has two rows"
                seen.add(key)


def test_terms_evidence_is_quoted_or_the_search_is_recorded(sources: list[dict]) -> None:
    for source in sources:
        terms = source["terms"]
        if terms["found"]:
            assert terms["quotes"], f"{source['id']}: terms found but nothing quoted"
        else:
            assert terms["searched"], f"{source['id']}: terms not found and no search recorded"


def test_permitted_uses_cite_the_rights_holders_quoted_terms(register: dict, sources: list[dict]) -> None:
    """Evidence rule #M-4: `permitted` rests on the rights holder's own quoted text.

    Statutory text (`legal_references`) can support `assessed`, never `permitted`.
    """
    legal_ids = {q["id"] for q in register["legal_references"]}
    assert len(legal_ids) == len(register["legal_references"]), "duplicate legal reference id"
    for source in sources:
        quote_ids = {q["id"] for q in source["terms"]["quotes"]}
        assert len(quote_ids) == len(source["terms"]["quotes"]), f"{source['id']}: duplicate quote id"
        assert not quote_ids & legal_ids, f"{source['id']}: quote id shadows a legal reference"
        for row in source["permissions"]:
            for use, entry in row["uses"].items():
                refs = set(entry.get("terms_refs", []))
                dangling = refs - quote_ids - legal_ids
                assert not dangling, f"{source['id']}.{use}: unknown terms_refs {sorted(dangling)}"
                if entry["status"] == "permitted":
                    assert refs & quote_ids, f"{source['id']}.{use}: permitted without the rights holder's quoted terms"


def test_sum11_is_never_published_as_modern_evidence(sources: list[dict]) -> None:
    """Rule #M-6: СУМ-11 fields are russification evidence only."""
    sum11 = next(s for s in sources if s["id"] == "sum11")
    assert all(field.startswith("russification_") for field in sum11["fields_used"])


def test_outreach_notes_exist(sources: list[dict]) -> None:
    for source in sources:
        note = source.get("outreach")
        if note:
            assert (REPO_ROOT / note).is_file(), f"{source['id']}: outreach note {note} missing"
    ulif = next(s for s in sources if s["id"] == "ulif")
    assert ulif.get("outreach"), "the ULIF outreach note is required (#8979)"


def test_markdown_twin_lists_every_source(sources: list[dict]) -> None:
    text = REGISTER_MD.read_text(encoding="utf-8")
    missing = [s["id"] for s in sources if f"`{s['id']}`" not in text]
    assert not missing, f"permissions-register.md does not list: {missing}"
