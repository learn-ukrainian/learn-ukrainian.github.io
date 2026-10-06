"""Synthetic regressions for heterogeneous operations and RB-1 component needs."""

import copy
import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.projects.open_model_data.review_build import __main__ as cli
from scripts.projects.open_model_data.review_build import bindings, output
from scripts.projects.open_model_data.review_build.attribution import Attribution, Resolver, SyntheticAdapter
from scripts.projects.open_model_data.review_build.build import execute
from scripts.projects.open_model_data.review_build.catalog import Catalog
from scripts.projects.open_model_data.review_build.contract import Value, canonical, digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.gate import Gate
from scripts.projects.open_model_data.review_build.output import OutputGuard
from scripts.projects.open_model_data.review_build.roles import SourceRoles
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.conftest import citation, run_gate, save_bundle, selector


def gate_for(bundle, reader):
    return Gate(
        reader,
        Catalog(bundle["catalog"]),
        Resolver(bundle["register"], {"synthetic": SyntheticAdapter()}),
        bundle["config"]["components"],
        bundle["config"]["compatibility"],
    )


def heterogeneous(bundle):
    """Two operations reuse numeric keys but have different primary tables."""
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute(
            "CREATE TABLE senses(id INTEGER PRIMARY KEY, source_field TEXT, target_field TEXT, source_file TEXT, entry_id INTEGER)"
        )
        writer.execute("INSERT INTO senses SELECT id,source_field,target_field,source_file,entry_id FROM units")
    original = bundle["spec"]
    second = copy.deepcopy(original)
    second["unit_query"]["sql"] = "SELECT id FROM senses"
    second["unit_id"]["primary"][0]["table"] = "senses"
    second["binding"]["rules"] = [
        {"op": "equal", "values": [selector(field="entry_id"), selector("response", "target", field="entry_id")]}
    ]
    bundle["config"]["components"] = {
        "C3": {
            "operations": ["synonyms", "sense_definition"],
            "reasons": original["reasons"],
            "operation_specs": {"synonyms": original, "sense_definition": second},
        }
    }
    first_stream = [replace(c, component="C3", operation="synonyms") for c in bundle["candidates"]]
    second_stream = [
        replace(
            c,
            component="C3",
            operation="sense_definition",
            slots=tuple(replace(v, citations=tuple(replace(q, table="senses") for q in v.citations)) for v in c.slots),
            response=tuple(
                replace(v, citations=tuple(replace(q, table="senses") for q in v.citations)) for v in c.response
            ),
        )
        for c in bundle["candidates"]
    ]
    bundle["candidates"] = first_stream + second_stream
    lines = bundle["catalog"]["components"].pop("C1")["instructions"]
    bundle["catalog"]["status"] = "rb1_approved"
    bundle["catalog"]["components"] = {
        "C3": {
            "instructions": [
                {**line, "id": f"C3.{op}.{i}", "operation": op}
                for op in ("synonyms", "sense_definition")
                for i, line in enumerate(lines)
            ]
        }
    }
    bundle["config"]["compatibility"].append({**bundle["config"]["compatibility"][0], "table": "senses"})


def test_operation_specific_tables_counts_bindings_and_verify(bundle, monkeypatch):
    heterogeneous(bundle)
    records, report = run_gate(bundle)
    assert len(records) == 24
    assert report["accounting"]["C3"]["counted"] == 24
    assert report["operation_accounting"]["C3.synonyms"]["counted"] == 12
    assert report["operation_accounting"]["C3.sense_definition"]["accepted"] == 12
    save_bundle(bundle)
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard)
        assert execute(bundle["root"] / "request.json", guard, verify=True)["status"] == "verified"


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("missing", "missing_unit"),
        ("count", "frozen_count"),
        ("identity", "unit_id_mismatch"),
        ("relationship", "binding_equal"),
        ("incomplete_spec", "operation_spec"),
    ],
)
def test_operation_specific_refusals(bundle, mutation, code):
    heterogeneous(bundle)
    if mutation == "missing":
        bundle["candidates"].pop()
    elif mutation == "count":
        bundle["config"]["components"]["C3"]["operation_specs"]["sense_definition"]["frozen_count"] = 13
    elif mutation == "identity":
        c = bundle["candidates"][-1]
        bundle["candidates"][-1] = replace(c, slots=(replace(c.slots[0], citations=(citation(bundle["rows"][-1]),)),))
    elif mutation == "relationship":
        c = bundle["candidates"][-1]
        bundle["candidates"][-1] = replace(c, response=bundle["candidates"][-2].response)
    else:
        del bundle["config"]["components"]["C3"]["operation_specs"]["sense_definition"]["binding"]
    with pytest.raises(BuildError, match=code):
        run_gate(bundle)


def span_units(bundle, composite=False):
    candidate = bundle["candidates"][0]
    text = candidate.slots[0].text
    spans = [(0, 9), (10, len(text))]
    bundle["candidates"] = [
        replace(
            candidate,
            unit_id=canonical(
                [["sources.db", "units", "id=1", list(span)], *([["sources.db", "units", "id=2"]] if composite else [])]
            ).decode(),
            slots=(replace(candidate.slots[0], text=text[span[0] : span[1]], span=span),),
            context=(bundle["candidates"][1].slots[0],) if composite else (),
        )
        for span in spans
    ]
    part = {"selector": selector(), "store": "sources.db", "table": "units", "span": True}
    bundle["spec"]["unit_id"] = {"format": "citation.v1", "primary": [part]}
    if composite:
        bundle["spec"]["unit_id"]["primary"].append(
            {"selector": selector("context"), "store": "sources.db", "table": "units"}
        )
    bundle["spec"]["unit_query"]["sql"] = " UNION ALL ".join(
        "SELECT " + "'" + c.unit_id + "'" for c in bundle["candidates"]
    )
    bundle["spec"]["frozen_count"] = 2


@pytest.mark.parametrize("composite", [False, True])
def test_span_identity_distinguishes_two_headings_on_one_page_and_composites(bundle, composite, monkeypatch):
    span_units(bundle, composite)
    records, report = run_gate(bundle)
    assert len(records) == report["accounting"]["C1"]["accepted"] == 2
    assert len({c.unit_id for c in bundle["candidates"]}) == 2
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    save_bundle(bundle)
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard)
        assert execute(bundle["root"] / "request.json", guard, verify=True)["status"] == "verified"
    original = bundle["candidates"][0]
    bundle["candidates"][0] = replace(
        original, slots=(replace(original.slots[0], span=bundle["candidates"][1].slots[0].span),)
    )
    with pytest.raises(BuildError, match="unit_id_mismatch"):
        run_gate(bundle)


def test_composite_identity_authenticates_every_page_even_on_withheld_units(bundle):
    span_units(bundle, True)
    c = bundle["candidates"][0]
    bundle["candidates"][0] = replace(
        c,
        outcome="withheld",
        reason="synthetic_missing",
        evidence=("synthetic_missing",),
        context=(bundle["candidates"][1].slots[0],),
    )
    with pytest.raises(BuildError, match="unit_id_mismatch"):
        run_gate(bundle)


def test_variable_values_quantify_every_sense_article_and_page(bundle):
    candidate = bundle["candidates"][0]
    responses = tuple(replace(c.slots[0], slot="body") for c in bundle["candidates"][:3])
    candidate = replace(candidate, response=responses)
    multi = selector("response", "body", match="all", min=2, field="group_id")
    spec = {
        "schema": "binding-spec.v1",
        "rules": [
            {"op": "one_group", "values": [selector(field="group_id"), multi]},
            {
                "op": "contiguous_pages",
                "values": [selector("response", "body", match="all", min=2, field="id")],
                "first": 1,
                "next_heading": 4,
                "source_field": "source_file",
            },
        ],
    }
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        assert bindings.check(candidate, spec, reader, {}) == {"one_group", "contiguous_pages"}
        with pytest.raises(BuildError, match="binding_selector"):
            bindings.expand(candidate, {**multi, "min": 4})
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("UPDATE units SET group_id='SYNTHETIC other sense' WHERE id=3")
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        with pytest.raises(BuildError, match="binding_group"):
            bindings.check(candidate, spec, reader, {})


def test_variable_citations_all_checked_and_repeated_slots_do_not_alias_evidence(bundle):
    row = bundle["rows"][0]
    primary = bundle["candidates"][0].slots[0]
    supported = replace(primary, slot="body", citations=(citation(row), citation(row)))
    candidate = replace(bundle["candidates"][0], response=(supported, supported))
    spec = {
        "schema": "binding-spec.v1",
        "rules": [{"op": "equal", "values": [selector("response", "body", index=0, citation="all", citation_min=2)]}],
    }
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        with pytest.raises(BuildError, match="supporting_unbound"):
            bindings.check(candidate, spec, reader, {})
        spec["rules"][0]["values"] = [selector("response", "body", match="all", min=2, citation="all", citation_min=2)]
        assert bindings.check(candidate, spec, reader, {}) == {"equal"}
    # Every supporting citation is independently checked for sense membership.
    candidate = replace(
        candidate, response=(replace(supported, citations=(citation(row), citation(bundle["rows"][1]))),)
    )
    spec["rules"] = [{"op": "one_group", "values": [selector("response", "body", citation="all", field="entry_id")]}]
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        with pytest.raises(BuildError, match="binding_group"):
            bindings.check(candidate, spec, reader, {})


@pytest.mark.parametrize("mutation", [None, "missing", "extra", "divergent", "unknown_normalizer"])
def test_set_query_equal_complete_variants(bundle, mutation):
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("CREATE TABLE forms(entry_id INTEGER, tags TEXT, form TEXT)")
        writer.execute("CREATE TABLE dictionary_forms(entry_id INTEGER, tags TEXT, form TEXT)")
        for table in ("forms", "dictionary_forms"):
            writer.executemany(
                f"INSERT INTO {table} VALUES(?,?,?)",
                [(1, "SYNTHETIC tags", v) for v in ("SYNTHETIC one", "SYNTHETIC two", "SYNTHETIC two")],
            )
        if mutation == "divergent":
            writer.execute("UPDATE dictionary_forms SET form='SYNTHETIC divergent' WHERE form='SYNTHETIC two'")
    variants = ["SYNTHETIC o\u0301ne", "SYNTHETIC two"]
    if mutation == "missing":
        variants.pop()
    elif mutation == "extra":
        variants.append("SYNTHETIC extra")
    candidate = replace(
        bundle["candidates"][0],
        response=tuple(Value("variant", v, (citation(bundle["rows"][0]),), None, "verbatim") for v in variants),
    )
    rule = {
        "op": "set_query_equal",
        "values": [selector("response", "variant", match="all", min=1)],
        "normalizer": "unstress_nfc" if mutation != "unknown_normalizer" else "SYNTHETIC arbitrary",
        "queries": [
            {
                "query": {
                    "kind": "sql",
                    "store": "sources.db",
                    "sql": f"SELECT form FROM {table} WHERE entry_id=? AND tags=?",
                },
                "parameters": [selector(field="entry_id"), selector(field="tags")],
            }
            for table in ("forms", "dictionary_forms")
        ],
    }
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        if mutation is None:
            assert bindings.check(candidate, {"schema": "binding-spec.v1", "rules": [rule]}, reader, {}) == {
                "set_query_equal"
            }
        else:
            with pytest.raises(
                BuildError, match="binding_normalizer" if mutation == "unknown_normalizer" else "binding_set"
            ):
                bindings.check(candidate, {"schema": "binding-spec.v1", "rules": [rule]}, reader, {})


@pytest.mark.parametrize("sql", ["DELETE FROM units", "WITH x AS (SELECT 1) DELETE FROM units"])
def test_set_queries_cannot_write_pinned_snapshot(bundle, sql):
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        with pytest.raises((BuildError, sqlite3.OperationalError)):
            reader.query_values({"kind": "sql", "store": "sources.db", "sql": sql})
        assert len(reader.units(bundle["spec"]["unit_query"])) == 12


def test_resolved_placeholder_and_repository_config_are_pinned(bundle, monkeypatch):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    config_name = "scripts/config/SYNTHETIC.lock.json"
    config_file = bundle["root"] / config_name
    config_file.parent.mkdir(parents=True)
    config_file.write_text('{"version":"1"}')
    form = "SYNTHETIC edition <version>"
    bundle["register"]["sources"][0]["citation"]["form"] = form
    bundle["config"]["synthetic_sources"] = []
    save_bundle(bundle)
    real_reader = SnapshotReader
    monkeypatch.setattr(
        "scripts.projects.open_model_data.review_build.build.SnapshotReader",
        lambda dbs, files: real_reader(dbs, files, repository_root=bundle["root"]),
    )

    class PinnedAdapter:
        def resolve(self, form, citation, row, reader):
            version = json.loads(reader.read_repository_config(config_name))["version"]
            return Attribution(form.replace("<version>", version), form)

    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard, adapters={"synthetic": PinnedAdapter()})
        manifest = json.loads(guard.read("manifest.json"))
        assert manifest["repository_configs"] == {config_name: digest(config_file.read_bytes())}
        assert (
            execute(bundle["root"] / "request.json", guard, verify=True, adapters={"synthetic": PinnedAdapter()})[
                "status"
            ]
            == "verified"
        )
        config_file.write_text('{"version":"2"}')
        with pytest.raises(BuildError, match="artifact_mismatch"):
            execute(bundle["root"] / "request.json", guard, verify=True, adapters={"synthetic": PinnedAdapter()})
    with real_reader({"sources.db": bundle["db"]}, repository_root=bundle["root"]) as reader:
        first = reader.read_repository_config(config_name)
        config_file.write_text('{"version":"3"}')
        assert reader.read_repository_config(config_name) == first
        assert reader.repository_config_hashes()[config_name] == digest(first)
        for path in ("../escape", str(config_file.resolve())):
            with pytest.raises(BuildError, match="repository_config"):
                reader.read_repository_config(path)
        (bundle["root"] / "SYNTHETIC-link").symlink_to(bundle["root"].parent)
        with pytest.raises(BuildError, match="repository_config"):
            reader.read_repository_config("SYNTHETIC-link/escape")


@pytest.mark.parametrize(
    "bibliography,mapped,instruction",
    [
        ("SYNTHETIC <version>", True, False),
        ("SYNTHETIC resolved", False, False),
        ("SYNTHETIC fill the version", True, True),
    ],
)
def test_placeholder_fix_keeps_result_and_full_mapping_gates(bundle, bibliography, mapped, instruction):
    form = "SYNTHETIC <version>"
    bundle["register"]["sources"][0]["citation"]["form"] = form

    class Adapter:
        def resolve(self, form, *args):
            return Attribution(bibliography, form if mapped else "SYNTHETIC other", instruction)

    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        with pytest.raises(BuildError, match="attribution_unresolved"):
            Resolver(bundle["register"], {"synthetic": Adapter()}).resolve(
                bundle["candidates"][0].slots[0].citations[0], reader
            )


@pytest.mark.parametrize(
    "filename,admitted",
    [
        ("1-klas-SYNTHETIC", True),
        ("11-klas-SYNTHETIC", True),
        ("uni-SYNTHETIC", True),
        ("0-klas-SYNTHETIC", False),
        ("12-klas-SYNTHETIC", False),
        ("SYNTHETIC other", False),
    ],
)
def test_textbook_roles_derive_allowlist_admission_from_file_not_grade(bundle, filename, admitted):
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("UPDATE units SET source_file=?,grade=0,is_sensitive=NULL", (filename,))
    role = {
        **bundle["config"]["compatibility"][0],
        "role": "textbook",
        "sensitive": None,
        "source_values": [filename],
        "allowlisted_files": [filename],
    }
    c = bundle["candidates"][0]
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        roles = SourceRoles(reader, [role])
        if admitted:
            roles.check(c.slots[0].citations[0], c, set())
        else:
            with pytest.raises(BuildError, match="textbook_grade"):
                roles.check(c.slots[0].citations[0], c, set())
        role["allowlisted_files"] = []
        with pytest.raises(BuildError, match="textbook_allowlist"):
            roles.check(c.slots[0].citations[0], c, set())


def test_ua_gec_cannot_disable_sensitivity_and_dictionary_declares_none(bundle):
    role = bundle["config"]["compatibility"][0]
    role.update(role="ua_gec", sensitive=None)
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        with pytest.raises(BuildError, match="role_spec"):
            SourceRoles(reader, [role])
        role.update(role="modern", sensitive=None)
        assert SourceRoles(reader, [role]).compatibility


def test_cli_default_config_repeatable_selection_and_verify(bundle, monkeypatch, capsys):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    default = bundle["root"] / "request.json"
    monkeypatch.setattr(cli, "default_config", lambda: default)
    args = ["--out", str(bundle["root"] / "SYNTHETIC-out"), "--components", "C1", "--components", "C1"]
    for command in ("build", "verify"):
        assert cli.main([command, *args]) == 0
        assert json.loads(capsys.readouterr().out)["status"] == ("built" if command == "build" else "verified")
        with pytest.raises(SystemExit) as exc:
            cli.main([command, "--help"])
        assert exc.value.code == 0
        help_text = capsys.readouterr().out
        assert all(
            s in help_text for s in ("--components", "default:", "Examples:", "Outputs:", "Exit codes:", "Related:")
        )
    assert cli.main(["build", "--out", str(bundle["root"] / "SYNTHETIC-other"), "--components", "C9"]) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "component_selection"


def test_selection_filters_records_accounting_metrics_and_pins(bundle, monkeypatch):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    original = bundle["catalog"]["components"]["C1"]
    bundle["catalog"]["components"]["C9"] = copy.deepcopy(original)
    for line in bundle["catalog"]["components"]["C9"]["instructions"]:
        line["id"] = line["id"].replace("C1", "C9")
    bundle["config"]["components"]["C9"] = copy.deepcopy(bundle["spec"])
    bundle["candidates"] += [replace(c, component="C9") for c in bundle["candidates"]]
    save_bundle(bundle)
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        execute(bundle["root"] / "request.json", guard, components=["C9"])
        assert not (bundle["root"] / "SYNTHETIC-out/C1").exists()
        manifest = json.loads(guard.read("manifest.json"))
        assert manifest["pins"]["components"] == ["C9"]
        assert set(manifest["accounting"]) == {"C9"}
        assert set(manifest["metrics"]) == {"C9.sentence_correction"}
        assert execute(bundle["root"] / "request.json", guard, components=["C9"], verify=True)["status"] == "verified"
        with pytest.raises(BuildError, match="artifact_mismatch"):
            execute(bundle["root"] / "request.json", guard, components=["C1"], verify=True)


def test_default_config_uses_shared_git_directory():
    default = cli.default_config()
    assert default.name == "request.json"
    assert default.parts[-3:] == ("batch_state", "review_build", "request.json")
    assert ".worktrees" not in default.parts
    assert (Path(cli.__file__).resolve().parents[4] / ".git").exists()


def test_composite_multi_selector_accounts_for_all_body_pages_and_order(bundle):
    candidate = bundle["candidates"][0]
    body = tuple(replace(c.response[0], slot="body") for c in bundle["candidates"][:3])
    parts = [
        {"selector": selector(), "store": "sources.db", "table": "units"},
        {"selector": selector("response", "body", match="all", min=2), "store": "sources.db", "table": "units"},
    ]
    bundle["spec"]["unit_id"] = {"format": "citation.v1", "primary": parts}
    bundle["spec"]["binding"]["rules"] = [
        {
            "op": "one_group",
            "values": [selector(field="group_id"), selector("response", "body", match="all", min=2, field="group_id")],
        },
        {
            "op": "contiguous_pages",
            "values": [selector("response", "body", match="all", min=2, field="id")],
            "first": 1,
            "next_heading": 4,
            "source_field": "source_file",
        },
    ]
    unit_id = canonical(
        [["sources.db", "units", "id=1"], *[["sources.db", "units", f"id={i}"] for i in range(1, 4)]]
    ).decode()
    bundle["candidates"] = [replace(candidate, unit_id=unit_id, response=body)]
    bundle["spec"]["unit_query"]["sql"] = "SELECT '" + unit_id + "'"
    bundle["spec"]["frozen_count"] = 1
    assert len(run_gate(bundle)[0]) == 1
    bundle["candidates"][0] = replace(bundle["candidates"][0], response=tuple(reversed(body)))
    with pytest.raises(BuildError, match="unit_id_mismatch"):
        run_gate(bundle)


def test_set_equality_is_exercised_by_full_admission_gate(bundle):
    bundle["spec"]["binding"]["rules"].append(
        {
            "op": "set_query_equal",
            "values": [selector("response", "target", match="all", min=1)],
            "normalizer": "identity",
            "queries": [
                {
                    "query": {
                        "kind": "sql",
                        "store": "sources.db",
                        "sql": "SELECT target_field FROM units WHERE entry_id=?",
                    },
                    "parameters": [selector(field="entry_id")],
                }
            ],
        }
    )
    records, report = run_gate(bundle)
    assert len(records) == report["accounting"]["C1"]["accepted"] == 12
    # The independent dictionary query returns a genuine extra variant.
    bundle["spec"]["binding"]["rules"][-1]["queries"][0]["query"]["sql"] += (
        " UNION ALL SELECT target_field FROM units WHERE id=2"
    )
    with pytest.raises(BuildError, match="binding_set"):
        run_gate(bundle)


@pytest.mark.parametrize("value", [None, 7])
def test_set_query_equal_refuses_non_text_source_variants(bundle, value):
    rule = {
        "op": "set_query_equal",
        "values": [selector("response", "target", match="all", min=1)],
        "normalizer": "identity",
        "queries": [
            {
                "query": {"kind": "sql", "store": "sources.db", "sql": "SELECT ?"},
                "parameters": [selector(field="grade")],
            }
        ],
    }
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("UPDATE units SET grade=? WHERE id=1", (value,))
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        with pytest.raises(BuildError, match="binding_set"):
            bindings.check(bundle["candidates"][0], {"schema": "binding-spec.v1", "rules": [rule]}, reader, {})


def test_unstress_normalization_handles_precomposed_and_decomposed_accents():
    assert bindings.normalize("SYNTHETIC caf\u00e9", "unstress_nfc") == "SYNTHETIC cafe"
    assert bindings.normalize("SYNTHETIC cafe\u0301", "unstress_nfc") == "SYNTHETIC cafe"
    assert bindings.normalize("SYNTHETIC cafe\u0301", "identity") == "SYNTHETIC cafe\u0301"
