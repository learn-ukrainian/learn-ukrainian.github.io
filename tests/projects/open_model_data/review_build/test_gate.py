import sqlite3
from dataclasses import replace

import pytest

from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.gate import evidence_id
from scripts.projects.open_model_data.review_build.roles import SourceRoles, sentence_hash
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.conftest import citation, run_gate, selector


def change_first(bundle, value=None, **candidate_changes):
    candidate = bundle["candidates"][0]
    if value is not None:
        candidate = replace(candidate, slots=(value,))
    bundle["candidates"][0] = replace(candidate, **candidate_changes)


def test_clean_build_and_authentic_duplicate_reporting(bundle):
    records, report = run_gate(bundle)
    assert len(records) == 12
    assert report["accounting"]["C1"]["accepted"] == report["accounting"]["C1"]["counted"] == 12
    assert report["metrics"]["C1.sentence_correction"]["status"] == "PASS"
    assert all(r["status"] == "review_only" and r["context"] == "" and r["tool_flags"] == [] for r in records)
    assert all(
        p["licence_ref"] == "permissions-register.yaml#synthetic; SYNTHETIC licence"
        and p["attribution"].startswith("SYNTHETIC source edition 1; SYNTHETIC row ")
        for r in records
        for p in r["provenance"].values()
    )
    # Twenty-four distinct source units with identical authentic source text
    # get two records per catalog line, reported without training-time dedup.
    repeated_rows = []
    for index in range(1, 25):
        repeated_rows.append(
            {
                **bundle["rows"][0],
                "id": index,
                "source_field": "SYNTHETIC repeated sentence",
                "target_field": "SYNTHETIC repeated target",
            }
        )
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute(
            "UPDATE units SET source_field=?,target_field=?",
            ("SYNTHETIC repeated sentence", "SYNTHETIC repeated target"),
        )
        for row in repeated_rows[12:]:
            writer.execute(
                "INSERT INTO units(id,source_field,target_field,source_file) VALUES(?,?,?,?)",
                (row["id"], row["source_field"], row["target_field"], row["source_file"]),
            )
    original = bundle["candidates"][0]
    bundle["candidates"] = [
        replace(
            original,
            unit_id=str(row["id"]),
            slots=(replace(original.slots[0], text=row["source_field"], citations=(citation(row),)),),
            response=(
                replace(original.response[0], text=row["target_field"], citations=(citation(row, "target_field"),)),
            ),
        )
        for row in repeated_rows
    ]
    bundle["spec"]["frozen_count"] = 24
    _, report = run_gate(bundle)
    assert report["accounting"]["C1"]["accepted"] == 24
    assert len(report["duplicate_groups"]) == 12
    assert all(len(group) == 2 for group in report["duplicate_groups"])


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("absent_quote", "quote_mismatch"),
        ("wrong_span", "quote_mismatch"),
        ("empty_locator", "empty_locator"),
        ("paraphrase", "unknown_transform"),
        ("reasoning", "reasoning_text"),
        ("missing_unit", "missing_unit"),
        ("duplicate_unit", "duplicate_unit"),
        ("frozen_count", "frozen_count"),
        ("empty_citations", "uncited_value"),
        ("uncited_rejection", "rejection_evidence"),
        ("unknown_reason", "reason_code"),
        ("unknown_operation", "operation"),
    ],
)
def test_must_fail_quotation_hygiene_accounting(bundle, mutation, code):
    value = bundle["candidates"][0].slots[0]
    if mutation == "absent_quote":
        change_first(bundle, replace(value, text="SYNTHETIC absent"))
    elif mutation == "wrong_span":
        change_first(bundle, replace(value, span=(0, 3)))
    elif mutation == "empty_locator":
        change_first(bundle, replace(value, citations=(replace(value.citations[0], locator=""),)))
    elif mutation == "paraphrase":
        change_first(bundle, replace(value, transform="SYNTHETIC paraphrase"))
    elif mutation == "reasoning":
        text = "SYNTHETIC <think>private reasoning</think>"
        with sqlite3.connect(bundle["db"]) as writer:
            writer.execute("UPDATE units SET source_field=? WHERE id=1", (text,))
        row = {**bundle["rows"][0], "source_field": text}
        change_first(bundle, replace(value, text=text, citations=(citation(row),)))
    elif mutation == "missing_unit":
        bundle["candidates"].pop()
    elif mutation == "duplicate_unit":
        bundle["candidates"].append(bundle["candidates"][0])
    elif mutation == "frozen_count":
        bundle["spec"]["frozen_count"] += 1
    elif mutation == "empty_citations":
        change_first(bundle, replace(value, citations=()))
    elif mutation == "uncited_rejection":
        change_first(bundle, outcome="rejected", reason="synthetic_error", evidence=("SYNTHETIC unsupported",))
    elif mutation == "unknown_reason":
        change_first(bundle, reason="SYNTHETIC unknown")
    else:
        change_first(bundle, operation="SYNTHETIC unknown")
    with pytest.raises(BuildError, match=code):
        run_gate(bundle)


def test_rejected_withheld_excluded_are_counted_and_rejection_is_cited(bundle):
    rejected = bundle["candidates"][0]
    change_first(
        bundle, outcome="rejected", reason="synthetic_error", evidence=(evidence_id(rejected.slots[0].citations[0]),)
    )
    for index, outcome, reason in ((1, "withheld", "synthetic_missing"), (2, "excluded", "synthetic_excluded")):
        bundle["candidates"][index] = replace(
            bundle["candidates"][index], outcome=outcome, reason=reason, evidence=(reason,)
        )
    records, report = run_gate(bundle)
    assert len(records) == 9
    assert report["accounting"]["C1"] == {
        "counted": 12,
        "accepted": 9,
        "rejected": 1,
        "withheld": 1,
        "excluded": 1,
        "reasons": {"ok": 9, "synthetic_error": 1, "synthetic_excluded": 1, "synthetic_missing": 1},
    }
    assert report["metrics"]["C1.sentence_correction"]["status"] == "insufficient_evidence"


@pytest.mark.parametrize("fixture", ["wrong_homonym", "wrong_paragraph"])
def test_genuine_quotes_wrong_relationship_fail(bundle, fixture):
    c = bundle["candidates"][0]
    other = bundle["candidates"][1].response[0]
    change_first(bundle, response=(other,))
    if fixture == "wrong_homonym":
        bundle["spec"]["binding"]["rules"] = [
            {"op": "equal", "values": [selector(field="entry_id"), selector("response", "target", field="entry_id")]}
        ]
        code = "binding_equal"
    else:
        code = "binding_row"
    with pytest.raises(BuildError, match=code):
        run_gate(bundle)


@pytest.mark.parametrize(
    "fixture,code",
    [
        ("sum11_alone", "sum11_role"),
        ("zno", "forbidden_source"),
        ("pogribny", "forbidden_source"),
        ("grade_zero", "textbook_grade"),
        ("private_textbook", "sensitive_source"),
        ("nonallowlisted_book", "textbook_allowlist"),
        ("test_sentence", "test_source"),
        ("test_overlap", "ruler_overlap"),
        ("dev_document", "dev_source"),
        ("mixed_c6", "mixed_edit"),
        ("compatibility", "source_compatibility"),
    ],
)
def test_must_fail_source_roles(bundle, fixture, code):
    role = bundle["spec"]["compatibility"][0]
    if fixture == "sum11_alone":
        role["role"] = "sum11"
    elif fixture in {"zno", "pogribny"}:
        source = "zno_SYNTHETIC" if fixture == "zno" else "pogribny_SYNTHETIC"
        role["source_id"] = source
        if fixture == "pogribny":
            role["role"] = "forbidden"
        bundle["register"]["sources"][0]["id"] = source
        bundle["candidates"] = [
            replace(
                c,
                slots=tuple(
                    replace(v, citations=tuple(replace(q, source_id=source) for q in v.citations)) for v in c.slots
                ),
                response=tuple(
                    replace(v, citations=tuple(replace(q, source_id=source) for q in v.citations)) for v in c.response
                ),
            )
            for c in bundle["candidates"]
        ]
    elif fixture in {"grade_zero", "private_textbook", "nonallowlisted_book"}:
        filename = "0-klas-SYNTHETIC" if fixture == "grade_zero" else "1-klas-SYNTHETIC"
        role.update(role="textbook", sensitive="is_sensitive", source_values=[filename], allowlisted_files=[filename])
        with sqlite3.connect(bundle["db"]) as writer:
            writer.execute("UPDATE units SET source_file=?", (filename,))
        if fixture != "nonallowlisted_book":
            with sqlite3.connect(bundle["db"]) as writer:
                writer.execute(
                    "UPDATE units SET " + ("grade=0" if fixture == "grade_zero" else "is_sensitive=1") + " WHERE id=1"
                )
        else:
            role["allowlisted_files"] = []
    elif fixture == "compatibility":
        role["table"] = "SYNTHETIC absent"
    else:
        role.update(
            role="ua_gec", split="split", document="document", text="source_field", layer="layer", edits="edits"
        )
        corpus = {
            "store": "sources.db",
            "table": "units",
            "split": "split",
            "document": "document",
            "author": "author",
            "layer": "layer",
            "text": "source_field",
        }
        bundle["spec"]["corpus"] = corpus
        with SnapshotReader({"sources.db": bundle["db"]}) as reader:
            dev = SourceRoles(reader, [role], corpus).dev_documents
        if fixture == "dev_document":
            selected = next(
                c for c, r in zip(bundle["candidates"], bundle["rows"], strict=True) if r["document"] in dev
            )
        else:
            selected = next(
                c for c, r in zip(bundle["candidates"], bundle["rows"], strict=True) if r["document"] not in dev
            )
        # Keep a full census, explicitly excluding other units.
        bundle["candidates"] = [
            c
            if c == selected
            else replace(c, outcome="excluded", reason="synthetic_excluded", evidence=("synthetic_excluded",))
            for c in bundle["candidates"]
        ]
        with sqlite3.connect(bundle["db"]) as writer:
            if fixture == "test_sentence":
                writer.execute("UPDATE units SET split='test' WHERE id=?", (int(selected.unit_id),))
            elif fixture == "test_overlap":
                other = next(c for c in bundle["candidates"] if c.unit_id != selected.unit_id)
                writer.execute(
                    "UPDATE units SET split='test',source_field=? WHERE id=?",
                    (selected.slots[0].text, int(other.unit_id)),
                )
                index = bundle["candidates"].index(other)
                v = other.slots[0]
                bundle["candidates"][index] = replace(
                    other,
                    slots=(
                        replace(
                            v,
                            citations=(
                                replace(v.citations[0], field_sha256=selected.slots[0].citations[0].field_sha256),
                            ),
                        ),
                    ),
                )
            elif fixture == "mixed_c6":
                writer.execute("UPDATE units SET layer='gec-fluency',edits='[\"F/Calque\",\"SYNTHETIC other edit\"]'")
        if fixture == "mixed_c6":
            bundle["candidates"] = [replace(c, component="C6") for c in bundle["candidates"]]
            bundle["specs"] = {"C6": bundle["spec"]}
            bundle["catalog"]["components"]["C6"] = bundle["catalog"]["components"].pop("C1")
    with pytest.raises(BuildError, match=code):
        run_gate(bundle)


def test_normalized_overlap_hash():
    assert sentence_hash("  SYNTHETIC\nText ") == sentence_hash("synthetic text")


def test_nonaccepted_candidates_still_require_citation_compatibility(bundle):
    candidate = bundle["candidates"][0]
    bad_value = replace(
        candidate.slots[0], citations=(replace(candidate.slots[0].citations[0], source_id="SYNTHETIC unknown"),)
    )
    for outcome, reason in (
        ("rejected", "synthetic_error"),
        ("withheld", "synthetic_missing"),
        ("excluded", "synthetic_excluded"),
    ):
        bundle["candidates"][0] = replace(
            candidate, slots=(bad_value,), outcome=outcome, reason=reason, evidence=(reason,)
        )
        with pytest.raises(BuildError, match="source_compatibility"):
            run_gate(bundle)


def test_unit_ids_recomputed_from_primary_cited_rows(bundle):
    first, second = bundle["candidates"][:2]
    bundle["candidates"][0] = replace(first, slots=second.slots)
    with pytest.raises(BuildError, match="unit_id_mismatch"):
        run_gate(bundle)


def test_unit_identity_can_bind_multiple_primary_keys_and_store_table(bundle):
    part = bundle["spec"]["unit_id"]["primary"][0]
    bundle["spec"]["unit_id"]["primary"] = [part, {**part, "selector": selector("response", "target")}]
    bundle["candidates"] = [replace(c, unit_id=f"{c.unit_id};{c.unit_id}") for c in bundle["candidates"]]
    bundle["spec"]["unit_query"]["sql"] = "SELECT id || ';' || id FROM units"
    assert len(run_gate(bundle)[0]) == 12
    part["table"] = "SYNTHETIC wrong table"
    with pytest.raises(BuildError, match="unit_id_mismatch"):
        run_gate(bundle)


@pytest.mark.parametrize("kind", ["missing_spec", "supporting", "missing_key"])
def test_unit_identity_spec_fails_closed(bundle, kind):
    if kind == "missing_spec":
        del bundle["spec"]["unit_id"]
    elif kind == "supporting":
        bundle["spec"]["unit_id"]["primary"][0]["selector"]["citation"] = 1
    else:
        bundle["spec"]["unit_id"]["primary"][0]["key"] = "SYNTHETIC absent"
    with pytest.raises(BuildError, match="unit_id_spec"):
        run_gate(bundle)


@pytest.mark.parametrize("role_name", ["ua_gec", "textbook"])
@pytest.mark.parametrize("kind", ["missing", "null"])
def test_sensitive_roles_require_a_present_known_sensitivity(bundle, role_name, kind):
    role = bundle["spec"]["compatibility"][0]
    role["role"] = role_name
    role["sensitive"] = "is_sensitive"
    if kind == "missing":
        role["sensitive"] = "SYNTHETIC missing"
    else:
        with sqlite3.connect(bundle["db"]) as writer:
            writer.execute("UPDATE units SET is_sensitive=NULL")
    with pytest.raises(BuildError, match="sensitivity_unavailable"):
        run_gate(bundle)


@pytest.mark.parametrize("kind", ["missing_column", "unexpected_value", "missing_mapping"])
def test_compatibility_requires_source_identity_from_the_row(bundle, kind):
    role = bundle["spec"]["compatibility"][0]
    if kind == "missing_column":
        role["source_column"] = "SYNTHETIC missing"
    elif kind == "unexpected_value":
        role["source_values"] = ["SYNTHETIC unrelated source"]
    else:
        del role["source_column"]
    with pytest.raises(BuildError, match="role_spec" if kind == "missing_mapping" else "source_compatibility"):
        run_gate(bundle)


def test_dev_carveout_excludes_fluency_only_documents_of_the_same_author(bundle):
    corpus = {
        "store": "sources.db",
        "table": "units",
        "split": "split",
        "document": "document",
        "author": "author",
        "layer": "layer",
        "text": "source_field",
    }
    role = bundle["spec"]["compatibility"][0]
    role.update(role="ua_gec", split="split", document="document", text="source_field", layer="layer", edits="edits")
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        carved = SourceRoles(reader, [role], corpus).dev_authors
    author = sorted(carved)[0]
    other = next(row for row in bundle["rows"] if row["author"] not in carved)
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("UPDATE units SET author=?, layer='gec-fluency' WHERE id=?", (author, other["id"]))
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        roles = SourceRoles(reader, [role], corpus)
        assert other["document"] in roles.dev_documents
        c = bundle["candidates"][other["id"] - 1]
        with pytest.raises(BuildError, match="dev_source"):
            roles.check(c.slots[0].citations[0], c, set())
