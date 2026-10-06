"""Registry admission and CLI extraction proof using synthetic source rows only."""

import copy
import json
import sqlite3
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.projects.open_model_data.review_build import __main__ as cli
from scripts.projects.open_model_data.review_build import components, output
from scripts.projects.open_model_data.review_build.attribution import Resolver, SyntheticAdapter
from scripts.projects.open_model_data.review_build.build import execute
from scripts.projects.open_model_data.review_build.catalog import Catalog
from scripts.projects.open_model_data.review_build.contract import Value, canonical, digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.gate import Gate
from scripts.projects.open_model_data.review_build.output import OutputGuard
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.conftest import citation, save_bundle, selector


def test_registry_is_closed_lazy_and_reports_only_selected_missing_id(monkeypatch):
    assert {c: c.lower() for c in ("C1", "C2", "C3", "C4", "C5", "C6a", "C6b", "C7", "C9")} == components.REGISTRY
    calls = []
    obj = object()

    def load(target):
        calls.append(target)
        if target.endswith(".c1"):
            return SimpleNamespace(COMPONENT=obj)
        raise ModuleNotFoundError(name=target)

    monkeypatch.setattr(components, "import_module", load)
    assert components.load_components(["C1"]) == {"C1": obj}
    assert len(calls) == 1
    for unknown in ("C8", "C6", "socket", "../c1"):
        with pytest.raises(BuildError, match="unknown_component"):
            components.load_components([unknown])
    assert len(calls) == 1
    with pytest.raises(BuildError, match="component_unavailable") as error:
        components.load_components(["C9"])
    assert error.value.diagnostic()["component"] == "C9"
    assert components.load_components(["C1"], _test_overrides={"C1": obj}) == {"C1": obj}


def test_missing_component_dependency_is_not_reported_as_missing_component(monkeypatch):
    def load(target):
        raise ModuleNotFoundError(name="SYNTHETIC_dependency")

    monkeypatch.setattr(components, "import_module", load)
    with pytest.raises(ModuleNotFoundError):
        components.load_components(["C1"])
    monkeypatch.setattr(components, "import_module", lambda target: SimpleNamespace())
    with pytest.raises(BuildError, match="component_contract"):
        components.load_components(["C1"])


def test_adapter_conflicts_are_not_overwritten():
    adapter = SyntheticAdapter()
    assert components.merge_adapters({"source": adapter}, {"source": adapter}) == {"source": adapter}
    with pytest.raises(BuildError, match="adapter_conflict"):
        components.merge_adapters({"source": adapter}, {"source": SyntheticAdapter()})


@pytest.mark.parametrize("component", ["C1", "C6a", "C6b"])
def test_cli_registered_component_build_verify_and_mutations(bundle, monkeypatch, capsys, component):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    bundle["specs"] = {component: {}}
    bundle["config"]["synthetic_sources"] = []
    # A source id without the synthetic prefix proves CLI adapter plumbing.
    bundle["spec"]["compatibility"][0]["source_id"] = "component_source"
    bundle["register"]["sources"][0]["id"] = "component_source"
    catalog_component = "C6" if component.startswith("C6") else component
    bundle["catalog"]["components"] = {catalog_component: bundle["catalog"]["components"]["C1"]}
    spec = copy.deepcopy(bundle["spec"])
    spec["operation_specs"] = {
        "sentence_correction": {key: spec.pop(key) for key in ("binding", "unit_query", "unit_id", "frozen_count")}
    }
    save_bundle(bundle)
    calls = []

    class SyntheticComponent:
        def __init__(self):
            self.files = {}
            self.adapters = {"component_source": SyntheticAdapter()}
            self.spec = spec

        def iter_candidates(self, ctx):
            rows = ctx.reader.all_rows("sources.db", "units")
            calls.append(len(rows))
            for candidate, row in zip(bundle["candidates"], rows, strict=True):

                def source(value, row=row):
                    return replace(value, citations=(citation(row, value.citations[0].field, "component_source"),))

                yield replace(
                    candidate,
                    component=component,
                    slots=tuple(source(v) for v in candidate.slots),
                    response=tuple(source(v) for v in candidate.response),
                )

    obj = SyntheticComponent()
    out = bundle["root"] / "SYNTHETIC-cli-output"
    args = ["--config", str(bundle["root"] / "request.json"), "--out", str(out), "--components", component]
    for command in ("build", "verify"):
        assert cli.main([command, *args], _test_components={component: obj}) == 0
        assert json.loads(capsys.readouterr().out)["status"] == ("built" if command == "build" else "verified")
    assert calls == [12, 12]
    manifest = json.loads((out / "manifest.json").read_bytes())
    assert manifest["accounting"][component]["accepted"] == 12
    assert manifest["operation_accounting"][f"{component}.sentence_correction"]["counted"] == 12
    assert manifest["pins"]["component_specs"] == digest(canonical({component: spec}))
    expected_request = bundle["config"]
    assert manifest["pins"]["request"] == digest(canonical(expected_request))
    assert "components/__init__.py" in manifest["pins"]["code"]["files"]
    assert len(json.loads((out / "mutation-fixtures/results.json").read_bytes())) == 5
    (out / component / "records.jsonl").write_bytes(b"SYNTHETIC tamper\n")
    assert cli.main(["verify", *args], _test_components={component: obj}) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "artifact_mismatch"


def test_component_context_detaches_and_freezes_nested_request():
    request = {"nested": [{"values": ["SYNTHETIC original"]}], "empty": {}, "flag": True}
    ctx = components.ComponentContext(None, request)
    request["nested"][0]["values"][0] = "SYNTHETIC changed"
    assert ctx.request["nested"][0]["values"] == ("SYNTHETIC original",)
    assert ctx.request["flag"] is True
    with pytest.raises(TypeError):
        ctx.request["empty"]["new"] = True


@pytest.mark.parametrize("verify", [False, True])
@pytest.mark.parametrize("mutation", ["request_policy", "request_list", "request_spec", "own_spec", "own_spec_replace"])
def test_extraction_cannot_mutate_admission_policy(bundle, monkeypatch, capsys, mutation, verify):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    original_spec = copy.deepcopy(bundle["spec"])
    active = False

    class MutatingComponent:
        def __init__(self):
            self.adapters = {"synthetic": SyntheticAdapter()}
            self.spec = copy.deepcopy(original_spec)

        def iter_candidates(self, ctx):
            if active:
                if mutation == "request_policy":
                    ctx.request["databases"]["sources.db"] = "SYNTHETIC changed"
                elif mutation == "request_list":
                    ctx.request["synthetic_sources"][0] = "SYNTHETIC changed"
                elif mutation == "request_spec":
                    ctx.request["catalog"] = "SYNTHETIC changed"
                elif mutation == "own_spec":
                    self.spec["binding"]["rules"].clear()
                    assert "components" not in ctx.request
                else:
                    self.spec = {**self.spec, "frozen_count": 0}
                    assert "compatibility" not in ctx.request
            yield from bundle["candidates"]

    obj = MutatingComponent()
    out = bundle["root"] / "SYNTHETIC-mutating-output"
    args = ["--config", str(bundle["root"] / "request.json"), "--out", str(out), "--components", "C1"]
    if verify:
        assert cli.main(["build", *args], _test_components={"C1": obj}) == 0
        capsys.readouterr()
    active = True
    assert cli.main(["verify" if verify else "build", *args], _test_components={"C1": obj}) == 1
    error = json.loads(capsys.readouterr().err)
    assert error["error"] == ("spec_mutated" if mutation.startswith("own_spec") else "build_failure")
    if not verify:
        assert not (out / "manifest.json").exists()
    if mutation.startswith("request"):
        assert "TypeError" in (out / "logs/failure.txt").read_text()
    assert json.loads((bundle["root"] / "request.json").read_bytes()) == bundle["config"]


def test_cli_conflicting_components_fail_before_extraction(bundle, monkeypatch, capsys):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    bundle["specs"]["C2"] = {}
    save_bundle(bundle)
    objects = {c: SimpleNamespace(adapters={"source": SyntheticAdapter()}) for c in ("C1", "C2")}
    args = [
        "build",
        "--config",
        str(bundle["root"] / "request.json"),
        "--out",
        str(bundle["root"] / "SYNTHETIC-out"),
        "--components",
        "C1",
        "C2",
    ]
    assert cli.main(args, _test_components=objects) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "adapter_conflict"


def test_cli_unavailable_unselected_component_does_not_poison_selected_build(bundle, monkeypatch, capsys):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    bundle["specs"]["C9"] = {}
    save_bundle(bundle)
    obj = SimpleNamespace(
        spec=bundle["spec"],
        adapters={"synthetic": SyntheticAdapter()},
        iter_candidates=lambda ctx: iter(bundle["candidates"]),
    )
    args = ["--config", str(bundle["root"] / "request.json"), "--out", str(bundle["root"] / "SYNTHETIC-out")]
    assert cli.main(["build", *args, "--components", "C1"], _test_components={"C1": obj}) == 0
    capsys.readouterr()
    assert cli.main(["build", *args, "--components", "C9"], _test_components={"C1": obj}) == 1
    error = json.loads(capsys.readouterr().err)
    assert error["error"] == "component_unavailable"
    assert error["component"] == "C9"


def test_component_file_store_is_installed_before_extraction_and_conflicts_refuse(bundle, monkeypatch):
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")
    bundle["config"]["databases"] = {}
    save_bundle(bundle)

    class Store:
        def row(self, table, row_key):
            return bundle["rows"][int(row_key.partition("=")[2]) - 1]

        def units(self, query):
            return [str(row["id"]) for row in bundle["rows"]]

        def all_rows(self, table):
            return [{**row, "row_key": f"id={row['id']}"} for row in bundle["rows"]]

        def file_hashes(self):
            return {"SYNTHETIC.source": digest(b"SYNTHETIC pinned input")}

    store = Store()
    seen = []

    def candidates(ctx):
        seen.append(len(ctx.reader.all_rows("sources.db", "units")))
        return iter(bundle["candidates"])

    obj = SimpleNamespace(
        spec=bundle["spec"],
        adapters={"synthetic": SyntheticAdapter()},
        files={"sources.db": store},
        iter_candidates=candidates,
    )
    with OutputGuard(bundle["root"] / "SYNTHETIC-out") as guard:
        for verify in (False, True):
            assert execute(bundle["root"] / "request.json", guard, component_objects={"C1": obj}, verify=verify)[
                "status"
            ] == ("verified" if verify else "built")
        with pytest.raises(BuildError, match="file_store_conflict"):
            execute(
                bundle["root"] / "request.json", guard, component_objects={"C1": obj}, files={"sources.db": Store()}
            )
    assert seen == [12, 12]


@pytest.fixture
def real_catalog():
    path = Path(__file__).resolve().parents[4] / "registry/projects/open_model_data/instruction_catalog.yaml"
    return Catalog(yaml.safe_load(path.read_bytes()))


@pytest.mark.parametrize("variant", ["with_sense", "without_sense"])
def test_real_c2_variants_accept_and_must_fail(bundle, real_catalog, variant):
    candidate = bundle["candidates"][0]
    value = candidate.slots[0]
    slots = tuple(replace(value, slot=s, text="SYNTHETIC " + s) for s in ("lemma", "slot"))
    sense = replace(value, slot="sense", text="SYNTHETIC sense" if variant == "with_sense" else " ")
    candidate = replace(candidate, component="C2", operation="agreed_form", slots=(*slots, sense))
    ids = real_catalog.applicable(candidate, variants={variant})
    assert len(ids) == 12
    assert {real_catalog.lines[i][1]["sense_variant"] for i in ids} == {variant}
    with pytest.raises(BuildError, match="catalog_inapplicable"):
        real_catalog.applicable(candidate)
    other = "without_sense" if variant == "with_sense" else "with_sense"
    with pytest.raises(BuildError, match="catalog_inapplicable"):
        real_catalog.applicable(candidate, variants={other})
    with pytest.raises(BuildError, match="catalog_inapplicable"):
        real_catalog.applicable(replace(candidate, slots=slots), variants={variant})
    spec = copy.deepcopy(bundle["spec"])
    spec["applicability"] = {v: [[selector(slot="lemma", field="grade"), 1]] for v in (variant, other)}
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        gate = Gate(
            reader,
            real_catalog,
            Resolver(bundle["register"], {"synthetic": SyntheticAdapter()}),
            {"C2": spec},
        )
        assert gate.applicable(candidate) == ids
        spec["applicability"][variant][0][1] = 0
        with pytest.raises(BuildError, match="catalog_inapplicable"):
            gate.applicable(candidate)


@pytest.mark.parametrize("variant", ["single_sense", "with_citations"])
def test_real_c3_variants_use_source_queries_accept_and_must_fail(bundle, real_catalog, variant):
    candidate = bundle["candidates"][0]
    candidate = replace(
        candidate, component="C3", operation="sense_definition", slots=(replace(candidate.slots[0], slot="headword"),)
    )
    # Real catalog, synthetic article/sense and citation holdings. Another
    # article's citations must never make this selected sense applicable.
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("CREATE TABLE senses(id INTEGER PRIMARY KEY, article_id INTEGER, quarantined INTEGER)")
        writer.execute("CREATE TABLE citations(id INTEGER PRIMARY KEY, sense_id INTEGER, quotation TEXT)")
        writer.execute("INSERT INTO senses VALUES(1,1,0)")
        writer.execute("INSERT INTO senses VALUES(2,2,0)")
        writer.execute("INSERT INTO citations VALUES(99,2,'SYNTHETIC other-sense citation')")
        if variant == "with_citations":
            writer.execute("INSERT INTO citations VALUES(1,1,'SYNTHETIC own-sense citation')")
            row = {"id": 1, "quotation": "SYNTHETIC own-sense citation"}
            candidate = replace(
                candidate,
                context=(
                    Value(
                        "sense_citations",
                        row["quotation"],
                        (citation(row, "quotation", table="citations"),),
                        None,
                        "verbatim",
                    ),
                ),
            )
    spec = copy.deepcopy(bundle["spec"])
    param = selector(slot="headword", field="entry_id")

    def predicate(sql, expected):
        return {
            "query": {"kind": "sql", "store": "sources.db", "sql": sql},
            "parameters": [param],
            "expected": [expected],
        }

    sense_count = (
        "SELECT count(*) FROM senses WHERE article_id=(SELECT article_id FROM senses WHERE id=?) AND quarantined=0"
    )
    own_citations = "SELECT count(*) > 0 FROM citations WHERE sense_id=?"
    spec["applicability"] = {
        "single_sense": [predicate(sense_count, 1), predicate(own_citations, 0)],
        "with_citations": [
            predicate(own_citations, 1),
            {
                "query": {
                    "kind": "sql",
                    "store": "sources.db",
                    "sql": "SELECT count(*) FROM citations WHERE id=? AND sense_id=?",
                },
                "parameters": [selector("context", "sense_citations", field="id"), param],
                "expected": [1],
            },
        ],
    }

    def check(expected_variant=None):
        with SnapshotReader({"sources.db": bundle["db"]}) as reader:
            gate = Gate(
                reader,
                real_catalog,
                Resolver(bundle["register"], {"synthetic": SyntheticAdapter()}),
                {"C3": spec},
            )
            if expected_variant is None:
                with pytest.raises(BuildError, match="catalog_inapplicable"):
                    gate.applicable(candidate)
            else:
                ids = gate.applicable(candidate)
                assert len(ids) == 12
                assert {real_catalog.lines[i][1]["sense_variant"] for i in ids} == {expected_variant}

    check(variant)
    if variant == "with_citations":
        own_context = candidate.context
        candidate = replace(candidate, context=())
        with SnapshotReader({"sources.db": bundle["db"]}) as reader:
            gate = Gate(
                reader,
                real_catalog,
                Resolver(bundle["register"], {"synthetic": SyntheticAdapter()}),
                {"C3": spec},
            )
            with pytest.raises(BuildError, match="binding_selector"):
                gate.applicable(candidate)
        other_row = {"id": 99, "quotation": "SYNTHETIC other-sense citation"}
        candidate = replace(
            candidate,
            context=(
                replace(
                    own_context[0],
                    text=other_row["quotation"],
                    citations=(citation(other_row, "quotation", table="citations"),),
                ),
            ),
        )
        check()
        candidate = replace(candidate, context=own_context)
    with sqlite3.connect(bundle["db"]) as writer:
        writer.execute("INSERT INTO senses VALUES(3,1,0)")
        writer.execute("DELETE FROM citations WHERE sense_id=1")
    check()  # Multisense article without own citations; other-sense donor remains.
    del spec["applicability"][variant]
    with SnapshotReader({"sources.db": bundle["db"]}) as reader:
        gate = Gate(
            reader,
            real_catalog,
            Resolver(bundle["register"], {"synthetic": SyntheticAdapter()}),
            {"C3": spec},
        )
        with pytest.raises(BuildError, match="applicability_spec"):
            gate.applicable(candidate)


def test_variant_names_are_data_not_a_framework_enum(bundle):
    data = copy.deepcopy(bundle["catalog"])
    lines = data["components"]["C1"]["instructions"][:2]
    for i, line in enumerate(lines):
        line["sense_variant"] = f"SYNTHETIC_variant_{i}"
    data["components"]["C1"]["instructions"] = lines
    catalog = Catalog(data)
    candidate = bundle["candidates"][0]
    assert catalog.applicable(candidate, variants={"SYNTHETIC_variant_1"}) == (lines[1]["id"],)
    with pytest.raises(BuildError, match="catalog_inapplicable"):
        catalog.applicable(candidate, variants={"SYNTHETIC_variant_0", "SYNTHETIC_variant_1"})


def test_real_catalog_version_and_split_component_diagnostics_are_admitted(real_catalog):
    from scripts.projects.open_model_data.review_build.manifest import private_manifest

    assert (
        private_manifest(
            {
                "hashes": {},
                "counts": {"C6a.counted": 1, "C6b.counted": 2},
                "versions": {"catalog": real_catalog.version},
                "code_sha": "a" * 40,
                "reason_code_tallies": {},
            }
        )["versions"]["catalog"]
        == real_catalog.version
    )
    for component in ("C6a", "C6b"):
        assert BuildError("component_unavailable", component=component).diagnostic()["component"] == component
