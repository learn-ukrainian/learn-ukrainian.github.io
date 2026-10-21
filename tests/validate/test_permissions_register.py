"""Validate the source citation and provenance register (#8979).

The register (`docs/sources/permissions-register.yaml`) records, per source, the
rights holder, what we use, where it comes from, the terms as found, the citation
we show and the removal route (a GitHub issue). Operator decisions 2026-09-27 make
it a citation record that supports removal on request, not a publication gate.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTER_YAML = REPO_ROOT / "docs" / "sources" / "permissions-register.yaml"
SCHEMA = REPO_ROOT / "schemas" / "permissions-register.schema.json"

ISSUES_URL = "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues"

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


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


@pytest.fixture(scope="module")
def register() -> dict:
    return yaml.safe_load(REGISTER_YAML.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sources(register: dict) -> list[dict]:
    return register["sources"]


def test_register_matches_schema(register: dict) -> None:
    errors = sorted(_validator().iter_errors(register), key=lambda e: list(e.absolute_path))
    assert not errors, "\n".join(f"{list(e.absolute_path)}: {e.message}" for e in errors)


def test_required_sources_present_and_ids_unique(sources: list[dict]) -> None:
    ids = [s["id"] for s in sources]
    assert len(ids) == len(set(ids)), "duplicate source id"
    missing = REQUIRED_SOURCES - set(ids)
    assert not missing, f"register is missing sources: {sorted(missing)}"


def test_every_source_has_a_citation_form_and_the_github_removal_route(register: dict, sources: list[dict]) -> None:
    assert register["removal_route"]["url"] == ISSUES_URL
    for source in sources:
        assert source["citation"]["form"].strip(), f"{source['id']}: no citation form"
        assert source["removal"]["route"] == ISSUES_URL, f"{source['id']}: removal route is not the GitHub issues"


def test_every_source_records_provenance(sources: list[dict]) -> None:
    for source in sources:
        prov = source["provenance"]
        assert prov["urls"], f"{source['id']}: no origin URL"
        assert prov["retrieved_evidence"].strip(), f"{source['id']}: retrieval date neither given nor explained"


def test_terms_evidence_is_quoted_or_the_search_is_recorded(sources: list[dict]) -> None:
    for source in sources:
        terms = source["terms"]
        if terms["found"]:
            assert terms["quotes"], f"{source['id']}: terms found but nothing quoted"
        else:
            assert terms["searched"], f"{source['id']}: terms not found and no search recorded"


def test_quote_and_legal_reference_ids_resolve(register: dict, sources: list[dict]) -> None:
    legal_ids = {q["id"] for q in register["legal_references"]}
    assert len(legal_ids) == len(register["legal_references"]), "duplicate legal reference id"
    cited: set[str] = set()
    for source in sources:
        terms = source["terms"]
        quote_ids = {q["id"] for q in terms["quotes"]}
        assert len(quote_ids) == len(terms["quotes"]), f"{source['id']}: duplicate quote id"
        verbatim = terms["licence"]["verbatim_quote"]
        if verbatim is not None:
            assert verbatim in quote_ids, f"{source['id']}: verbatim_quote {verbatim} is not one of its quotes"
        refs = set(terms.get("legal_refs", []))
        assert refs <= legal_ids, f"{source['id']}: unknown legal_refs {sorted(refs - legal_ids)}"
        cited |= refs
    assert legal_ids <= cited, f"legal references cited by no source: {sorted(legal_ids - cited)}"


def test_openly_licensed_sources_carry_their_licence_text_verbatim(sources: list[dict]) -> None:
    for source in sources:
        licence = source["terms"]["licence"]
        if licence["spdx"]:
            assert licence["verbatim_quote"], f"{source['id']}: {licence['spdx']} without its licence text quoted"


def test_sum11_register_entry_is_russification_evidence_only(sources: list[dict]) -> None:
    """Register-wording check only (rule #M-6).

    This does not inspect learner cards. Atlas migration and runtime export
    reject a СУМ-11 citation outside soviet_colonization_context and a citation
    that lacks a russification marker on the same card.
    """
    sum11 = next(s for s in sources if s["id"] == "sum11")
    assert all(field.startswith("russification_") for field in sum11["fields_used"])
    restriction = sum11["usage_restriction"]
    assert "red-flagged" in restriction and "never" in restriction.lower()
