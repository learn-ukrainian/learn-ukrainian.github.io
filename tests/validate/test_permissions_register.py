"""Validate the source citation and provenance register (#8979).

The register (`docs/sources/permissions-register.yaml`) records, per source, the
rights holder, what we use, where it comes from, the terms as found, the citation
we show and the removal route (a GitHub issue). Operator decisions 2026-09-27 make
it a citation record that supports removal on request, not a publication gate.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTER_YAML = REPO_ROOT / "docs" / "sources" / "permissions-register.yaml"
REGISTER_MD = REPO_ROOT / "docs" / "sources" / "permissions-register.md"
SCHEMA = REPO_ROOT / "schemas" / "permissions-register.schema.json"

ISSUES_URL = "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues"

PERMISSION_STATUSES = {
    "open-licence",
    "public-domain",
    "granted",
    "verbal-granted-written-pending",
    "pending-expert-contact",
    "none",
    "unknown",
}

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

# Fields of the v1 register that made it a publication gate (removed by the
# operator decisions of 2026-09-27).
GATE_KEYS = {"gates", "statuses", "uses", "scales", "permissions", "publish_if", "outreach", "contact"}


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def _all_keys(node: object) -> set[str]:
    if isinstance(node, dict):
        return set(node) | {k for v in node.values() for k in _all_keys(v)}
    if isinstance(node, list):
        return {k for v in node for k in _all_keys(v)}
    return set()


@pytest.fixture(scope="module")
def register() -> dict:
    return yaml.safe_load(REGISTER_YAML.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sources(register: dict) -> list[dict]:
    return register["sources"]


def test_register_matches_schema(register: dict) -> None:
    errors = sorted(_validator().iter_errors(register), key=lambda e: list(e.absolute_path))
    assert not errors, "\n".join(f"{list(e.absolute_path)}: {e.message}" for e in errors)


def test_schema_rejects_an_entry_missing_provenance(register: dict) -> None:
    broken = copy.deepcopy(register)
    del broken["sources"][0]["provenance"]
    messages = [e.message for e in _validator().iter_errors(broken)]
    assert any("'provenance' is a required property" in m for m in messages), messages


def test_schema_rejects_an_entry_missing_its_citation_form(register: dict) -> None:
    broken = copy.deepcopy(register)
    del broken["sources"][0]["citation"]["form"]
    messages = [e.message for e in _validator().iter_errors(broken)]
    assert any("'form' is a required property" in m for m in messages), messages


def test_schema_rejects_an_entry_missing_its_removal_route(register: dict) -> None:
    broken = copy.deepcopy(register)
    del broken["sources"][0]["removal"]["route"]
    messages = [e.message for e in _validator().iter_errors(broken)]
    assert any("'route' is a required property" in m for m in messages), messages


def test_schema_rejects_a_removal_route_that_is_not_a_github_issue(register: dict) -> None:
    broken = copy.deepcopy(register)
    broken["sources"][0]["removal"]["route"] = "mailto:takedown@example.org"
    assert list(_validator().iter_errors(broken))


def test_no_publication_gate_fields_remain(register: dict) -> None:
    leftovers = _all_keys(register) & GATE_KEYS
    assert not leftovers, f"publication-gate fields still present: {sorted(leftovers)}"


def test_operator_decisions_are_recorded(register: dict) -> None:
    decisions = {d["id"]: d for d in register["operator_decisions"]}
    assert len(decisions) == len(register["operator_decisions"])
    assert {key: d["date"] for key, d in decisions.items()} == {
        "d1_content_stays": "2026-09-27",
        "d2_teacher_consent": "2026-09-27",
        "d3_takedown_via_issues": "2026-09-27",
        "d4_no_outreach": "2026-09-27",
        "o1_verbatim_use": "2026-10-03",
        "o3_textbooks_used": "2026-10-03",
        "d5_permissions_sought": "2026-10-06",
    }
    for key in ("o1_verbatim_use", "o3_textbooks_used", "d5_permissions_sought"):
        assert decisions[key]["url"] == f"{ISSUES_URL}/6321"
    update = decisions["d5_permissions_sought"]["decision"]
    assert "d4_no_outreach only for these permissions" in update
    assert "verbal permission in 2026-10" in update
    assert "written confirmation pending" in update


def test_every_source_has_a_valid_permission_status(sources: list[dict]) -> None:
    for source in sources:
        assert source["permission_status"] in PERMISSION_STATUSES, source["id"]


def test_schema_rejects_an_invalid_permission_status(register: dict) -> None:
    broken = copy.deepcopy(register)
    broken["sources"][0]["permission_status"] = "approved-for-export"
    errors = list(_validator().iter_errors(broken))
    assert any(list(e.absolute_path) == ["sources", 0, "permission_status"] for e in errors)


def test_schema_requires_permission_status(register: dict) -> None:
    broken = copy.deepcopy(register)
    del broken["sources"][0]["permission_status"]
    messages = [e.message for e in _validator().iter_errors(broken)]
    assert any("'permission_status' is a required property" in m for m in messages), messages


def test_schema_rejects_an_empty_permission_note(register: dict) -> None:
    broken = copy.deepcopy(register)
    broken["sources"][0]["permission_note"] = ""
    errors = list(_validator().iter_errors(broken))
    assert any(list(e.absolute_path) == ["sources", 0, "permission_note"] for e in errors)


def test_stress_data_follows_ulif_permission_and_provenance(sources: list[dict]) -> None:
    by_id = {s["id"]: s for s in sources}
    stress = by_id["ukrainian_word_stress"]
    assert stress["permission_status"] == by_id["ulif"]["permission_status"] == "verbal-granted-written-pending"
    assert "written confirmation pending" in stress["permission_note"]
    assert "MIT licence covers only the code" in stress["permission_note"]
    assert stress["terms"]["licence"]["spdx"] is None  # No MIT grant for the data.
    assert "no licence in the stress data repository" in stress["terms"]["licence"]["name"]
    quotes = {q["id"]: q for q in stress["terms"]["quotes"]}
    assert "by ULIF" in quotes["uws_ulif_provenance"]["quote"]
    assert quotes["uws_ulif_provenance"]["url"].endswith("/CONTRIBUTING.md")
    assert 'на основі "Словників України"' in quotes["uws_dictionary_provenance"]["quote"]
    assert not stress["open_questions"]


def test_puls_licence_is_cc_by_nc_sa_4(sources: list[dict]) -> None:
    puls = next(s for s in sources if s["id"] == "puls")
    licence = puls["terms"]["licence"]
    assert licence["name"] == "CC BY-NC-SA 4.0"
    assert licence["spdx"] == "CC-BY-NC-SA-4.0"
    assert puls["permission_status"] == "open-licence"
    assert puls["terms"]["conditions"]["share_alike"] is True
    assert puls["terms"]["conditions"]["non_commercial"] is True
    quotes = {q["id"]: q for q in puls["terms"]["quotes"]}
    verbatim = quotes[licence["verbatim_quote"]]
    assert "PULS data are distributed under" in verbatim["quote"]
    assert "(CC BY-NC-SA 4.0)" in verbatim["quote"]
    assert verbatim["url"] == "https://puls.peremova.org/terms"
    assert verbatim["read_on"] == "2026-10-06"
    assert quotes["puls_footer"]["quote"] == "© 2026 ПУЛЬС."


def test_textbook_dataset_use_does_not_decide_dataset_licence(register: dict, sources: list[dict]) -> None:
    textbooks = next(s for s in sources if s["id"] == "textbooks")
    assert "dataset" in textbooks["appears_in"]
    assert "C9" in textbooks["appears_note"]
    assert "#6321" in textbooks["appears_note"]
    assert textbooks["permission_status"] == "none"
    question = register["open_questions"][0]
    assert "Not decided" in question
    assert "O1/O3" in question and "decided use, not the dataset's licence" in question
    assert "E6 (dataset licence choice) remains an operator decision" in question


def test_dbnary_licence_question_is_resolved(sources: list[dict]) -> None:
    source = next(s for s in sources if s["id"] == "dmklinger")
    quote = next(q for q in source["terms"]["quotes"] if q["id"] == "dbnary_licence")
    assert "Creative Commons Attribution-ShareAlike 3.0" in quote["quote"]
    assert quote["url"] == "https://kaiko.getalp.org/about-dbnary/"
    assert quote["read_on"] == "2026-10-06"
    assert not source["open_questions"]


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


def test_vesum_licence_is_quoted_verbatim_from_dict_uk(sources: list[dict]) -> None:
    vesum = next(s for s in sources if s["id"] == "vesum")
    quotes = {q["id"]: q for q in vesum["terms"]["quotes"]}
    verbatim = quotes[vesum["terms"]["licence"]["verbatim_quote"]]
    assert "github.com/brown-uk/dict_uk" in verbatim["url"]
    assert "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License" in verbatim["quote"]


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


def test_teacher_consent_covers_site_and_dataset(sources: list[dict]) -> None:
    teacher = next(s for s in sources if s["id"] == "teacher_materials")
    assert {"site", "dataset"} <= set(teacher["appears_in"])


def test_outreach_drafts_are_gone() -> None:
    assert not (REGISTER_YAML.parent / "outreach").exists()


def test_markdown_twin_lists_every_source(sources: list[dict]) -> None:
    text = REGISTER_MD.read_text(encoding="utf-8")
    missing = [s["id"] for s in sources if f"`{s['id']}`" not in text]
    assert not missing, f"permissions-register.md does not list: {missing}"


def test_markdown_twin_records_each_permission_status(sources: list[dict]) -> None:
    text = REGISTER_MD.read_text(encoding="utf-8")
    sections = text.split("\n### ")[1:]
    assert len(sections) == len(sources)
    for source in sources:
        section = next(s for s in sections if s.splitlines()[0].endswith(f"`{source['id']}`"))
        assert f"**Permission status:** `{source['permission_status']}`" in section
        if "permission_note" in source:
            assert source["permission_note"] in section
