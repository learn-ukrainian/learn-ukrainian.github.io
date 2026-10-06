"""SYNTHETIC-only WP1 accounting, citation, split and must-fail proofs."""

import csv
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest
import yaml

from scripts.projects.open_model_data.review_build import __main__ as cli
from scripts.projects.open_model_data.review_build import components, output
from scripts.projects.open_model_data.review_build.attribution import Resolver, SyntheticAdapter
from scripts.projects.open_model_data.review_build.build import artifacts
from scripts.projects.open_model_data.review_build.catalog import Catalog
from scripts.projects.open_model_data.review_build.components import (
    c1_ua_gec,
    c6a_calque,
    ua_gec_mutations,
    ua_gec_split,
)
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.gate import Gate
from scripts.projects.open_model_data.review_build.output import OutputGuard
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.conftest import catalog_data, register_data


class SyntheticAnnotation:
    def __init__(self, raw, edits):
        self.raw, self.edits = raw, edits

    def __str__(self):
        return self.raw

    def get_annotations(self):
        return self.edits


@pytest.fixture
def store(tmp_path, monkeypatch):
    root = tmp_path / "SYNTHETIC-corpus"
    root.mkdir()
    (root / "data").mkdir()
    fields = [
        "id",
        "author_id",
        "is_native",
        "region",
        "gender",
        "occupation",
        "submission_type",
        "source_language",
        "annotator_id",
        "partition",
        "is_sensitive",
    ]
    metadata = [
        dict(
            zip(
                fields,
                [
                    f"{i:04}",
                    f"SYNTHETIC-author-{i}",
                    "1",
                    "SYNTHETIC",
                    "SYNTHETIC",
                    "SYNTHETIC",
                    "essay",
                    "",
                    "1 2" if i == 1 else "1",
                    "train" if i <= 24 else "test",
                    "0",
                ],
                strict=True,
            )
        )
        for i in range(1, 27)
    ]
    metadata[20]["is_sensitive"] = "1"
    metadata[21].update(submission_type="translation", source_language="en")
    with (root / "data/metadata.csv").open("w") as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        writer.writerows(metadata)
    (root / "README.md").write_text("SYNTHETIC README")
    (root / "LICENSE").write_text("SYNTHETIC licence")
    (root / "python/ua_gec").mkdir(parents=True)
    documents = {}
    for layer in ua_gec_split.LAYERS:
        documents[layer] = []
        for row in metadata:
            source_sentences = [f"SYNTHETIC learner {row['id']} first.", f"SYNTHETIC learner {row['id']} second."]
            if row["id"] == "0025":
                source_sentences[0] = "SYNTHETIC learner 0020 first."
            source = "\n".join(source_sentences) + "\n"
            for annotator in row["annotator_id"].split():
                target_sentences = [source_sentences[0], f"SYNTHETIC correction {row['id']} annotator {annotator}."]
                target = "\n".join(target_sentences) + "\n"
                raw = f"SYNTHETIC annotation {row['id']} {annotator} {layer}\n"
                base = root / f"data/{layer}/{row['partition']}"
                for directory in ("annotated", "source-sentences", "target-sentences"):
                    (base / directory).mkdir(parents=True, exist_ok=True)
                (base / f"annotated/{row['id']}.a{annotator}.ann").write_text(raw)
                (base / f"source-sentences/{row['id']}.src.txt").write_text(source)
                (base / f"target-sentences/{row['id']}.a{annotator}.txt").write_text(target)
                start = len(source_sentences[0]) + 1
                edits = [
                    SimpleNamespace(
                        start=start,
                        end=start + 9,
                        meta={"error_type": "F/Calque" if layer == "gec-fluency" else "Grammar"},
                    )
                ]
                if row["id"] == "0019" and layer == "gec-fluency":
                    edits.append(SimpleNamespace(start=start + 10, end=start + 11, meta={"error_type": "Grammar"}))
                meta = SimpleNamespace(
                    doc_id=row["id"],
                    author_id=row["author_id"],
                    annotator_id=int(annotator),
                    partition=row["partition"],
                    is_sensitive=row["is_sensitive"] == "1",
                    submission_type=row["submission_type"],
                    source_language=row["source_language"],
                )
                documents[layer].append(
                    SimpleNamespace(
                        meta=meta,
                        source=source,
                        source_sentences=source_sentences,
                        target_sentences=target_sentences,
                        annotated=SyntheticAnnotation(raw, edits),
                    )
                )
    monkeypatch.setattr(ua_gec_split, "official_corpus", lambda _, layer: documents[layer])
    result = ua_gec_split.UaGecFileStore(root)
    result.synthetic_documents = documents
    return result


def setup_gate(store, selected=("C1", "C6a")):
    modules = {"C1": c1_ua_gec, "C6a": c6a_calque}
    config = {
        "schema": "omd-review-request.v1",
        "catalog": "SYNTHETIC-catalog",
        "register": "SYNTHETIC-register",
        "databases": {},
        "components": {name: modules[name].spec() for name in selected},
        "compatibility": store.compatibility(),
        "corpus": ua_gec_split.CORPUS,
        "ua_gec": {"root": str(store.root)},
    }
    candidates = [c for name in selected for c in modules[name].extract(store)]
    for component in config["components"].values():
        component["frozen_count"] = len(store.units(component["unit_query"]))
    data = catalog_data()
    data["components"].update(catalog_data("C6", "calque_correction")["components"])
    resolver = Resolver(register_data(sources=("ua_gec",)), {"ua_gec": SyntheticAdapter()})
    reader = SnapshotReader({}, {"ua-gec": store})
    gate = Gate(reader, Catalog(data), resolver, config["components"], store.compatibility(), ua_gec_split.CORPUS)
    return gate, candidates, config, data


def admitted(store, component="C1"):
    module = c1_ua_gec if component == "C1" else c6a_calque
    return next(c for c in module.extract(store) if c.outcome == "accepted")


def test_accept_accounting_and_frozen_source_splits(store):
    gate, candidates, config, _ = setup_gate(store)
    records, report = gate.run(candidates)
    assert report["accounting"]["C1"]["counted"] == 50
    assert report["accounting"]["C6a"]["counted"] == 25
    assert all(
        sum(counts[k] for k in ("accepted", "rejected", "withheld", "excluded")) == counts["counted"]
        for counts in report["accounting"].values()
    )
    assert all(m["status"] == "PASS" for m in report["metrics"].values())
    assert len(gate.roles.dev_authors) == len(store.splits.dev_authors) == 3
    assert gate.roles.dev_documents == store.splits.dev_documents
    assert gate.roles.test_hashes == store.splits.test_hashes
    assert store.splits.counts()["overlap_sentences"] == 1
    assert all(p["span"] is not None for r in records for p in r["provenance"].values())
    assert len(json.loads(ua_gec_split.manifest_bytes(store))["files"]) > 0
    assert config["components"]["C1"]["parser_hashes"]


def test_unchanged_multiple_references_and_translation(store):
    candidates = c1_ua_gec.extract(store)
    assert any(c.slots[0].text == c.response[0].text for c in candidates if c.outcome == "accepted")
    references = [c for c in candidates if "0001.a" in c.unit_id]
    assert len(references) == 4 and len({c.unit_id for c in references}) == 4
    assert any(c.flags == ("translation:en",) for c in candidates)
    assert all(c.slots[0].citations[0].table == "data/gec-only" for c in candidates)
    assert all(c.slots[0].citations[0].table == "data/gec-fluency" for c in c6a_calque.extract(store))


@pytest.mark.parametrize("field", ["source_sentence", "target_sentence"])
@pytest.mark.parametrize("marker", ["Step 1", "<think>", "Reasoning:"])
def test_authentic_reasoning_markers_withhold_without_changing_source(store, field, marker):
    base = admitted(store)
    citation = base.slots[0].citations[0]
    row = store._rows[citation.table, citation.row_key]
    row[field] = "SYNTHETIC " + marker
    source_field = "source" if field == "source_sentence" else "target"
    row[source_field] = row[field]
    row[source_field + "_span"] = (0, len(row[field]))
    original = dict(row)
    gate, candidates, _, _ = setup_gate(store, ("C1",))
    changed = next(c for c in candidates if c.unit_id == base.unit_id)
    assert changed.outcome == "withheld" and changed.reason == "reasoning_marker_in_source"
    assert changed.evidence == ("reasoning_marker_in_source",)
    assert row == original
    _, report = gate.run(candidates)
    assert report["accounting"]["C1"]["counted"] == 50
    assert report["accounting"]["C1"]["reasons"]["reasoning_marker_in_source"] == 1


def test_unbound_registered_store_refuses_reads():
    store = ua_gec_split.UaGecFileStore()
    for read in (
        lambda: store._read("README.md"),
        lambda: store.row("corpus", "SYNTHETIC"),
        lambda: store.all_rows("corpus"),
        lambda: store.units({}),
        store.file_hashes,
    ):
        with pytest.raises(BuildError, match="source_input_unavailable"):
            read()


def test_registered_reader_root_uses_shared_repository():
    from scripts.projects.open_model_data.review_build.components import ua_gec_component

    assert ua_gec_component.held_root() == cli.default_config().parents[2] / "data/ua-gec"


@pytest.mark.parametrize(
    "fault,code",
    [
        ("root", "component_input"),
        ("other_root", "component_input"),
        ("corpus", "component_corpus"),
        ("compatibility", "source_compatibility"),
    ],
)
def test_registered_inputs_refuse_unreviewed_mappings(store, monkeypatch, fault, code):
    from scripts.projects.open_model_data.review_build.components import ua_gec_component

    _, _, config, _ = setup_gate(store)
    if fault == "root":
        config["ua_gec"]["root"] = "SYNTHETIC-relative"
    elif fault == "other_root":
        config["ua_gec"]["root"] = str(store.root / "SYNTHETIC-untrusted-reader")
    elif fault == "corpus":
        config["corpus"] = {}
    else:
        config["compatibility"] = []
    monkeypatch.setattr(ua_gec_component, "UaGecFileStore", lambda _: store)
    monkeypatch.setattr(ua_gec_component, "held_root", lambda: store.root)
    obj = components.load_components(["C1"])["C1"]
    with SnapshotReader({}, obj.files) as reader:
        ctx = components.ComponentContext(reader, config)
        with pytest.raises(BuildError, match=code):
            list(obj.iter_candidates(ctx))


@pytest.mark.parametrize("component", ["C1", "C6a"])
@pytest.mark.parametrize(
    "mutation,expected",
    [
        ("absent_quote", "quote_mismatch"),
        ("wrong_span", "quote_span"),
        ("empty_locator", "empty_locator"),
        ("paraphrase", "unknown_transform"),
        ("wrong_reference", "binding_row"),
        ("wrong_sentence", "binding_equal"),
        ("missing_unit", "missing_unit"),
        ("reasoning", "reasoning_text"),
        ("swapped_unit", "unit_id_mismatch"),
    ],
)
def test_must_fail_component_gate(store, component, mutation, expected):
    gate, candidates, _, _ = setup_gate(store)
    base = admitted(store, component)
    index = candidates.index(base)
    value = base.slots[0]
    if mutation == "missing_unit":
        candidates.pop(index)
    elif mutation == "absent_quote":
        candidates[index] = replace(base, slots=(replace(value, text="SYNTHETIC absent quotation"),))
    elif mutation == "wrong_span":
        candidates[index] = replace(base, slots=(replace(value, span=(-1, 0)),))
    elif mutation == "empty_locator":
        candidates[index] = replace(base, slots=(replace(value, citations=(replace(value.citations[0], locator=""),)),))
    elif mutation == "paraphrase":
        candidates[index] = replace(base, slots=(replace(value, transform="SYNTHETIC-paraphrase"),))
    elif mutation == "wrong_reference":
        donor = next(c for c in candidates if c.component == component and c.unit_id != base.unit_id and c.response)
        candidates[index] = replace(base, response=donor.response)
    elif mutation == "wrong_sentence":
        row = store.row(value.citations[0].table, value.citations[0].row_key)
        store._rows[row["table"], row["row_key"]] = {**row, "source_sentence": "SYNTHETIC a different sentence"}
    elif mutation == "swapped_unit":
        donor = next(c for c in candidates if c.component == component and c.unit_id != base.unit_id)
        candidates[index] = replace(base, slots=donor.slots)
    elif mutation == "reasoning":
        row = store.row(value.citations[0].table, value.citations[0].row_key)
        text = "SYNTHETIC <think>"
        changed = {**row, "source": text, "source_sentence": text, "source_span": (0, len(text))}
        store._rows[row["table"], row["row_key"]] = changed
        candidates[index] = replace(base, slots=(ua_gec_split.cited_value(changed, "sentence", "source"),))
    with pytest.raises(BuildError, match=expected):
        gate.run(candidates)


@pytest.mark.parametrize("reason", ["test_source", "dev_source", "sensitive_source", "ruler_overlap"])
def test_must_fail_source_role(store, reason):
    gate, _, _, _ = setup_gate(store)
    row = next(
        r
        for r in store.all_rows("corpus")
        if r["layer"] == "gec-only" and ua_gec_split.exclusion(r, store.splits) == reason
    )
    candidate = replace(c1_ua_gec.candidate(row, store.splits), outcome="accepted", reason="aligned_pair", evidence=())
    with pytest.raises(BuildError, match=reason):
        gate.roles.check(candidate.slots[0].citations[0], candidate, set())


def test_mixed_edit_never_admitted(store):
    gate, candidates, _, _ = setup_gate(store)
    mixed = next(c for c in candidates if c.component == "C6a" and c.reason == "mixed_to_c1")
    assert mixed.outcome == "excluded"
    index = candidates.index(mixed)
    candidates[index] = replace(mixed, outcome="accepted", reason="calque_only", evidence=())
    with pytest.raises(BuildError, match="mixed_edit"):
        gate.run(candidates)


@pytest.mark.parametrize("module", [c1_ua_gec, c6a_calque])
@pytest.mark.parametrize("missing", ["alignment", "empty"])
def test_withhold_unsupported_pair(store, module, missing):
    base = admitted(store, "C1" if module is c1_ua_gec else "C6a")
    row = store.row(base.slots[0].citations[0].table, base.unit_id)
    row.update(aligned=missing != "alignment", target_sentence="" if missing == "empty" else row["target_sentence"])
    candidate = module.candidate(row, store.splits)
    assert candidate.outcome == "withheld" and candidate.reason == ("empty" if missing == "empty" else "unaligned")
    assert candidate.evidence


def test_annotation_alignment_uses_order_and_withholds_boundaries():
    def annotation(start, end, tag="F/Calque"):
        return SimpleNamespace(start=start, end=end, meta={"error_type": tag})

    edits, ambiguous = ua_gec_split.sentence_edits(
        "SYNTHETIC one. \n SYNTHETIC two.", ["SYNTHETIC one.", "SYNTHETIC two."], [annotation(0, 9), annotation(14, 16)]
    )
    assert edits == [["F/Calque", "F/Calque"], ["F/Calque"]] and ambiguous == {0, 1}
    with pytest.raises(BuildError, match="annotation_sentence_binding"):
        ua_gec_split.sentence_edits("SYNTHETIC one", ["SYNTHETIC other"], [])
    with pytest.raises(BuildError, match="annotation_sentence_binding"):
        ua_gec_split.sentence_edits("SYNTHETIC one extra", ["SYNTHETIC one"], [])
    with pytest.raises(BuildError, match="annotation_span"):
        ua_gec_split.sentence_edits("SYNTHETIC", ["SYNTHETIC"], [annotation(-1, 0)])
    with pytest.raises(BuildError, match="annotation_type"):
        ua_gec_split.sentence_edits("SYNTHETIC", ["SYNTHETIC"], [annotation(0, 1, None)])
    assert ua_gec_split.sentence_edits("SYNTHETIC", ["", "SYNTHETIC"], [annotation(1, 2)])[0] == [[], ["F/Calque"]]


def test_count_and_primary_identity_are_independent(store):
    gate, candidates, _, _ = setup_gate(store)
    gate.components["C1"]["frozen_count"] += 1
    with pytest.raises(BuildError, match="frozen_count"):
        gate.run(candidates)
    with pytest.raises(BuildError, match="row_unavailable"):
        store.row("SYNTHETIC missing", "id=0")
    with pytest.raises(BuildError, match="unit_query"):
        store.units({"kind": "SYNTHETIC", "store": "ua-gec"})
    with pytest.raises(BuildError, match="corpus_table"):
        store.all_rows("SYNTHETIC unknown")
    with pytest.raises(BuildError, match="sentence_file_binding"):
        ua_gec_split.line_spans("SYNTHETIC source", ["SYNTHETIC other"])


def test_file_changes_and_symlinks_refused(store):
    (store.root / "README.md").write_text("SYNTHETIC changed")
    with pytest.raises(BuildError, match="source_file_changed"):
        store.file_hashes()
    (store.root / "SYNTHETIC-link").symlink_to(store.root / "LICENSE")
    with pytest.raises(BuildError, match="source_file_path"):
        store._read("SYNTHETIC-link")
    with pytest.raises(BuildError, match="source_file_path"):
        store._read("../SYNTHETIC-outside")


def test_attribution_complete_or_withheld(store, monkeypatch):
    base = admitted(store)
    citation = base.slots[0].citations[0]
    row = store.row(citation.table, citation.row_key)
    metadata = """SYNTHETIC bibliography https://github.com/grammarly/ua-gec
@inproceedings{syvokon-etal-2023-ua,
author = "Syvokon, Oleksiy and Nahorna, Olena and Kuchmiichuk, Pavlo and Osidach, Nastasiia"
booktitle = "Proceedings of the Second Ukrainian Natural Language Processing Workshop (UNLP)"
year = "2023"
}
"""
    # The registered adapter resolves through the current snapshot, rather
    # than caching a store across build and verify invocations.
    adapter = ua_gec_split.UaGecAttribution()
    monkeypatch.setattr(
        store, "_read", lambda p: metadata if p == "README.md" else "SYNTHETIC Attribution 4.0 International"
    )
    reader = SnapshotReader({}, {"ua-gec": store})
    register = register_data(ua_gec_split.REGISTER_FORM, sources=("ua_gec",))
    resolver = Resolver(register, {"ua_gec": adapter})
    licence, attribution = resolver.resolve(citation, reader)
    assert "permissions-register.yaml#ua_gec" in licence and citation.locator in attribution
    for form in ("<author> <year>", "SYNTHETIC cite the author", "SYNTHETIC unknown"):
        with pytest.raises(BuildError, match="attribution_unresolved"):
            adapter.resolve(form, citation, row, reader)
    monkeypatch.setattr(store, "_read", lambda p: "SYNTHETIC incomplete")
    with pytest.raises(BuildError, match="attribution_unresolved"):
        adapter.resolve(ua_gec_split.REGISTER_FORM, citation, row, reader)


def test_framework_build_artifacts_with_real_component_specs(store):
    gate, candidates, config, _ = setup_gate(store)
    pins = {
        "register": "a" * 64,
        "catalog": "b" * 64,
        "candidates": "c" * 64,
        "spec": "d" * 64,
        "code": {"parser_sha256": "e" * 64, "code_sha": "f" * 40},
    }
    files = artifacts(config, candidates, gate.reader, gate.catalog, gate.resolver, pins)
    assert json.loads(files["accounting.json"])["C1"]["counted"] == 50
    assert b"gec-fluency" in files["README.md"] and b"Each annotator" in files["README.md"]


def test_component_verification_fixtures_are_host_only(store, tmp_path, monkeypatch):
    _, candidates, config, data = setup_gate(store)
    (tmp_path / "SYNTHETIC-catalog.yaml").write_text(yaml.safe_dump(data))
    (tmp_path / "SYNTHETIC-register.yaml").write_text(yaml.safe_dump(register_data(sources=("ua_gec",))))
    config.update(catalog=str(tmp_path / "SYNTHETIC-catalog.yaml"), register=str(tmp_path / "SYNTHETIC-register.yaml"))
    monkeypatch.setattr(output, "filesystem", lambda _: "ext4")
    monkeypatch.setattr(ua_gec_mutations, "UaGecAttribution", lambda _: SyntheticAdapter())
    with OutputGuard(tmp_path / "SYNTHETIC-output") as out:
        results = ua_gec_mutations.verify_component_mutations(config, candidates, store, out)
        assert results["mixed_edit"] == "mixed_edit" and results["test_source"] == "test_source"
        assert json.loads(out.read("mutation-fixtures/wp1-results.json")) == results


def test_official_reader_loader_preserves_environment(tmp_path, monkeypatch):
    root = tmp_path / "SYNTHETIC-official"
    package = root / "python/ua_gec"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        "class Corpus:\n    def __init__(self, partition, annotation_layer):\n        self.partition = partition\n        self.layer = annotation_layer\n"
    )
    import sys

    monkeypatch.delitem(sys.modules, "ua_gec", raising=False)
    try:
        corpus = ua_gec_split.official_corpus(root, "gec-only")
        assert corpus.partition == "all" and corpus._data_dir == root / "data/gec-only"
        assert ua_gec_split.official_corpus(root, "gec-fluency").layer == "gec-fluency"
        with pytest.raises(BuildError, match="reader_identity"):
            ua_gec_split.official_corpus(tmp_path / "SYNTHETIC-other", "gec-only")
    finally:
        sys.modules.pop("ua_gec", None)


def test_invalid_component_selection_is_refused(store):
    with pytest.raises(BuildError, match="unknown_component"):
        components.load_components(["C6"])


@pytest.mark.parametrize("selected", [["C1"], ["C6a"], ["C1", "C6a"]])
def test_registered_cli_build_verify_and_input_tamper(store, tmp_path, monkeypatch, capsys, selected):
    _, _, config, catalog = setup_gate(store, selected)
    catalog_path, register_path = tmp_path / "SYNTHETIC-catalog.yaml", tmp_path / "SYNTHETIC-register.yaml"
    catalog_path.write_text(yaml.safe_dump(catalog))
    register_path.write_text(yaml.safe_dump(register_data(sources=("ua_gec",))))
    config.update(catalog=str(catalog_path), register=str(register_path))
    config["components"] = {name: {} for name in selected}
    config_path = tmp_path / "request.json"
    config_path.write_text(json.dumps(config))
    from scripts.projects.open_model_data.review_build.components import ua_gec_component

    # Keep the real registry and component extraction, replacing only private
    # corpus I/O and attribution with the existing synthetic fixtures.
    opened = []

    def open_store(root):
        opened.append(root)
        return store

    monkeypatch.setattr(ua_gec_component, "UaGecFileStore", open_store)
    monkeypatch.setattr(ua_gec_component, "held_root", lambda: store.root)
    monkeypatch.setitem(ua_gec_component.ADAPTERS, "ua_gec", SyntheticAdapter())
    monkeypatch.setattr(c1_ua_gec, "FROZEN_COUNT", 50)
    monkeypatch.setattr(c6a_calque, "FROZEN_COUNT", 25)
    monkeypatch.setattr(output, "filesystem", lambda _: "ext4")
    out = tmp_path / "SYNTHETIC-build"
    args = ["--config", str(config_path), "--out", str(out), "--components", *selected]
    assert cli.main(["build", *args]) == 0
    built = json.loads(capsys.readouterr().out)
    assert cli.main(["verify", *args]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert len(opened) == 2  # Once per snapshot, even when both ids are selected.
    assert built["status"] == "built" and verified["status"] == "verified"
    assert built["build_sha256"] == verified["build_sha256"]
    manifest = json.loads((out / "manifest.json").read_bytes())
    assert set(manifest["accounting"]) == set(selected)
    assert manifest["pins"]["components"] == sorted(selected)
    assert set(json.loads((out / "mutation-fixtures/results.json").read_bytes())) == {
        "absent_quote",
        "wrong_span",
        "empty_locator",
        "missing_unit",
        "swapped_citation",
    }
    (out / "accounting.json").write_bytes(b"SYNTHETIC tamper")
    assert cli.main(["verify", *args]) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "artifact_mismatch"


def test_cli_privacy_help_and_error_logs(tmp_path, monkeypatch, capsys):
    with pytest.raises(SystemExit) as result:
        cli.main(["--help"])
    assert result.value.code == 0
    help_text = capsys.readouterr().out
    assert all(part in help_text for part in ("Examples:", "Outputs:", "Exit codes:", "Related:"))
    assert cli.main(["SYNTHETIC PRIVATE INPUT"]) == 2
    captured = capsys.readouterr()
    assert "SYNTHETIC PRIVATE INPUT" not in captured.out + captured.err
    assert json.loads(captured.err)["error"] == "cli_usage"
    monkeypatch.setattr(output, "filesystem", lambda _: "ext4")
    config = tmp_path / "SYNTHETIC-request.json"
    config.write_text(json.dumps({"components": {"C1": {}}}))
    monkeypatch.setattr(cli, "execute", lambda *args, **kwargs: {"status": "built", "count": 1})
    out = tmp_path / "SYNTHETIC-cli"
    args = ["build", "--config", str(config), "--out", str(out), "--components", "C1"]
    assert cli.main(args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "built"

    def fail(*args, **kwargs):
        raise ValueError("SYNTHETIC PRIVATE RECORD TEXT")

    monkeypatch.setattr(cli, "execute", fail)
    assert cli.main(args) == 1
    captured = capsys.readouterr()
    assert "SYNTHETIC PRIVATE RECORD TEXT" not in captured.out + captured.err
    assert str(out) not in captured.out + captured.err
    assert b"SYNTHETIC PRIVATE RECORD TEXT" in (out / "logs/failure.txt").read_bytes()
    monkeypatch.setattr(OutputGuard, "write", fail)
    assert cli.main(args) == 1
    captured = capsys.readouterr()
    assert "SYNTHETIC PRIVATE RECORD TEXT" not in captured.out + captured.err
    assert json.loads(captured.err)["error"] == "error_log_unavailable"
