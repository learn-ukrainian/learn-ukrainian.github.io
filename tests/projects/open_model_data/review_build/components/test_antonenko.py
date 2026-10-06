"""Synthetic-only WP6 source, packet, receipt, binding and accounting proofs."""

import copy
import json
import sqlite3
from dataclasses import replace

import pytest

from scripts.projects.open_model_data.review_build import output
from scripts.projects.open_model_data.review_build.attribution import Resolver, SyntheticAdapter
from scripts.projects.open_model_data.review_build.catalog import Catalog
from scripts.projects.open_model_data.review_build.components import ComponentContext
from scripts.projects.open_model_data.review_build.components.antonenko import (
    BOOK_ADAPTER,
    MODELS,
    RECEIPTS,
    SOURCE,
    STORE,
    batches,
    book_locator,
    citation,
    validate_receipts,
    write_packets,
)
from scripts.projects.open_model_data.review_build.components.c6b import BookCalqueComponent
from scripts.projects.open_model_data.review_build.components.c7 import ContrastComponent
from scripts.projects.open_model_data.review_build.contract import canonical, digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.gate import Gate
from scripts.projects.open_model_data.review_build.output import OutputGuard
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.conftest import STARTS, catalog_data, register_data


@pytest.fixture
def source(tmp_path, monkeypatch):
    monkeypatch.setattr(output, "filesystem", lambda p: "ext4")
    db, vesum = tmp_path / "SYNTHETIC-sources.db", tmp_path / "SYNTHETIC-vesum.db"
    rows = [
        dict(
            id=i,
            word="SYNTHETIC title",
            text=f"SYNTHETIC {left} {right}.",
            source="SYNTHETIC book",
            page=None,
            section=f"SYNTHETIC section {i}",
        )
        for i, (left, right) in enumerate((("wrong", "right"), ("other", "better")), 1)
    ]
    with sqlite3.connect(db) as c:
        c.execute(
            "CREATE TABLE style_guide(id INTEGER PRIMARY KEY,word TEXT,text TEXT,source TEXT,page INTEGER,section TEXT)"
        )
        c.executemany("INSERT INTO style_guide VALUES (:id,:word,:text,:source,:page,:section)", rows)
        c.execute(
            "CREATE TABLE sum11(id INTEGER PRIMARY KEY,word TEXT,source TEXT,sovietization_risk INTEGER,sovietization_keywords TEXT)"
        )
        c.executemany(
            "INSERT INTO sum11 VALUES (?,?,?,1,?)",
            [(1, "wrong", "SYNTHETIC sum11", "SYNTHETIC marker"), (2, "other", "SYNTHETIC sum11", "SYNTHETIC marker")],
        )
        c.execute(
            "CREATE TABLE ulif_dictua_entries(id INTEGER PRIMARY KEY,normalized_query TEXT,canonical_headword TEXT,homonym_checked INTEGER,status TEXT)"
        )
        c.executemany(
            "INSERT INTO ulif_dictua_entries VALUES (?,?,?,1,'ok')", [(1, "right", "right"), (2, "better", "better")]
        )
    with sqlite3.connect(vesum) as c:
        c.execute("CREATE TABLE forms_all(id INTEGER PRIMARY KEY,word_form TEXT,source_location TEXT)")
        c.executemany("INSERT INTO forms_all VALUES (?,?,'SYNTHETIC vesum')", [(1, "right"), (2, "better")])
    receipt_root = tmp_path / "SYNTHETIC-receipts"
    with OutputGuard(receipt_root):
        pass
    return {"rows": rows, "db": db, "vesum": vesum, "receipts": receipt_root}


def pair_for(row, left=None, right=None):
    words = row["text"].split()
    left, right = left or words[1], right or words[2].rstrip(".")
    return {
        role: {"start": row["text"].index(word), "end": row["text"].index(word) + len(word)}
        for role, word in (("rejected", left), ("recommended", right))
    }


def selection_receipts(batch):
    return {
        seat: {
            "schema": "antonenko-span-receipt.v1",
            "model": model,
            "task_id": f"SYNTHETIC {seat} task",
            "batch_sha256": batch["batch_sha256"],
            "rows": [
                {
                    "row_id": row["row_id"],
                    "row_text_sha256": row["row_text_sha256"],
                    "pairs": [pair_for({"text": row["text"]})],
                }
                for row in batch["rows"]
            ],
        }
        for seat, model in MODELS.items()
    }


def write_receipt(source, mutate=None):
    batch = batches(source["rows"])[0]
    receipts = selection_receipts(batch)
    if mutate:
        mutate(receipts)
    with OutputGuard(source["receipts"]) as guard:
        for seat, receipt in receipts.items():
            guard.write(f"{batch['batch_sha256']}.{seat}.json", canonical(receipt))
    return receipts


def component_for(component, count=2):
    obj = BookCalqueComponent() if component == "C6b" else ContrastComponent()
    obj.spec = copy.deepcopy(obj.spec)
    obj.spec["operation_specs"][obj.spec["operations"][0]]["frozen_count"] = count
    return obj


def context(source):
    reader = SnapshotReader({"sources.db": source["db"], "vesum.db": source["vesum"]}, {STORE: RECEIPTS})
    return ComponentContext(reader, {"antonenko_receipts": str(source["receipts"])})


def gate(ctx, obj, component):
    operation = obj.spec["operations"][0]
    data = catalog_data()
    data["components"] = {
        "C6" if component == "C6b" else "C7": {
            "instructions": [
                {
                    "id": f"{component}.{operation}.{i}",
                    "operation": operation,
                    "template": start + (" SYNTHETIC {expression}" if component == "C6b" else " SYNTHETIC choose"),
                    "slots": ["expression"] if component == "C6b" else [],
                }
                for i, start in enumerate(STARTS)
            ]
        }
    }
    compatibility = [
        {
            "store": "sources.db",
            "table": "style_guide",
            "source_id": SOURCE,
            "role": "modern",
            "source_column": "source",
            "source_values": ["SYNTHETIC book"],
        },
        {
            "store": STORE,
            "table": component,
            "source_id": SOURCE,
            "role": "modern",
            "source_column": "source",
            "source_values": ["SYNTHETIC book"],
        },
        {
            "store": "sources.db",
            "table": "sum11",
            "source_id": "sum11",
            "role": "sum11",
            "source_column": "source",
            "source_values": ["SYNTHETIC sum11"],
        },
        {
            "store": "sources.db",
            "table": "ulif_dictua_entries",
            "source_id": "ulif",
            "role": "modern",
            "source_column": "status",
            "source_values": ["ok"],
        },
        {
            "store": "vesum.db",
            "table": "forms_all",
            "source_id": "vesum",
            "role": "modern",
            "source_column": "source_location",
            "source_values": ["SYNTHETIC vesum"],
        },
    ]
    resolver = Resolver(register_data(sources=tuple(obj.adapters)), {s: SyntheticAdapter() for s in obj.adapters})
    return Gate(ctx.reader, Catalog(data), resolver, {component: obj.spec}, compatibility)


@pytest.mark.parametrize("component", ["C6b", "C7"])
def test_accept_paths_and_complete_accounting(source, component):
    write_receipt(source)
    obj, ctx = component_for(component), context(source)
    with ctx.reader:
        candidates = list(obj.iter_candidates(ctx))
        records, report = gate(ctx, obj, component).run(candidates)
        assert len(records) == report["accounting"][component]["accepted"] == 2
        assert all("c7_opt_in" in r["flags"] for r in records) if component == "C7" else True
        if component == "C7":
            for r in records:
                pair = json.loads(r["context"])
                assert len(pair) == 2 and r["response"] in pair
                assert any(p["source_id"] == "sum11" and p["sovietization_risk"] == 1 for p in r["provenance"].values())
        assert ctx.reader.file_hashes()[STORE]


@pytest.mark.parametrize("component", ["C6b", "C7"])
def test_pending_receipts_ship_no_records_and_packets_remain_source_bound(source, component):
    obj, ctx = component_for(component), context(source)
    with ctx.reader:
        candidates = list(obj.iter_candidates(ctx))
        records, report = gate(ctx, obj, component).run(candidates)
        assert records == []
        assert report["accounting"][component]["reasons"] == {"adjudication_pending": 2}
        files = obj.artifact_files(ctx)
        packets = [json.loads(v) for k, v in files.items() if "adjudication-packets" in k]
        assert len(packets) == 1
        for p in packets:
            sha = p.pop("batch_sha256")
            assert digest(canonical(p)) == sha
            assert [r["text"] for r in p["rows"]] == [r["text"] for r in source["rows"]]


@pytest.mark.parametrize(
    "page,section,expected",
    [
        (0, "SYNTHETIC section", "SYNTHETIC section"),
        (None, "SYNTHETIC section", "SYNTHETIC section"),
        (2, "", "page 2"),
        (0, "", ""),
    ],
)
def test_locator_never_uses_page_zero(page, section, expected):
    assert book_locator({"page": page, "section": section}) == expected


def test_missing_locator_is_withheld(source):
    with sqlite3.connect(source["db"]) as c:
        c.execute("UPDATE style_guide SET page=0,section='' WHERE id=1")
    obj, ctx = component_for("C6b"), context(source)
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        assert cs[0].reason == "locator_unavailable"
        assert gate(ctx, obj, "C6b").run(cs)[1]["accounting"]["C6b"]["counted"] == 2


@pytest.mark.parametrize(
    "change,code",
    [
        (lambda r: r["sol"].update(batch_sha256="0" * 64), "adjudication_stale"),
        (lambda r: r["opus"]["rows"][0].update(row_text_sha256="0" * 64), "adjudication_stale"),
        (lambda r: r["sol"]["rows"][0]["pairs"][0]["rejected"].update(start=-1), "adjudication_span"),
        (lambda r: r["sol"]["rows"][0]["pairs"][0]["recommended"].update(end=9999), "adjudication_span"),
        (lambda r: r["sol"]["rows"][0]["pairs"][0]["rejected"].update(start=True), "adjudication_span"),
        (lambda r: r["sol"].update(model=MODELS["opus"]), "adjudication_provenance"),
        (lambda r: r["sol"].update(task_id=""), "adjudication_provenance"),
        (lambda r: r["sol"].update(task_id=r["opus"]["task_id"]), "adjudication_provenance"),
        (lambda r: r.pop("opus"), "adjudication_seats"),
        (lambda r: r["sol"]["rows"].pop(), "adjudication_rows"),
        (lambda r: r["sol"]["rows"].append(r["sol"]["rows"][0]), "adjudication_rows"),
        (lambda r: r["sol"]["rows"][0]["pairs"][0].update(text="SYNTHETIC authored"), "adjudication_direction"),
    ],
)
def test_receipt_must_fail_authentication(source, change, code):
    write_receipt(source, change)
    ctx = context(source)
    with ctx.reader, pytest.raises(BuildError, match=code):
        list(component_for("C6b").iter_candidates(ctx))


@pytest.mark.parametrize("component", ["C6b", "C7"])
@pytest.mark.parametrize("mode", ["different", "swapped", "single_empty", "both_empty"])
def test_selection_disagreement_or_no_pair_withholds(source, component, mode):
    def change(receipts):
        pair = receipts["opus"]["rows"][0]["pairs"][0]
        if mode == "different":
            pair["recommended"]["end"] -= 1
        elif mode == "swapped":
            pair["rejected"], pair["recommended"] = pair["recommended"], pair["rejected"]
        else:
            receipts["opus"]["rows"][0]["pairs"] = []
            if mode == "both_empty":
                receipts["sol"]["rows"][0]["pairs"] = []

    write_receipt(source, change)
    ctx, obj = context(source), component_for(component)
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        reason = "no_pair_named" if mode == "both_empty" else "adjudication_disagreement"
        assert cs[0].outcome == "withheld" and cs[0].reason == reason
        report = gate(ctx, obj, component).run(cs)[1]
        assert report["accounting"][component]["reasons"][reason] == 1


@pytest.mark.parametrize("component", ["C6b", "C7"])
@pytest.mark.parametrize(
    "mutation,code",
    [
        ("quote", "quote_mismatch"),
        ("span", "quote_mismatch"),
        ("locator", "empty_locator"),
        ("missing", "missing_unit"),
        ("wrong_row", "unit_id_mismatch"),
        ("transform", "unknown_transform"),
    ],
)
def test_component_generic_must_fail_fixtures(source, component, mutation, code):
    write_receipt(source)
    ctx, obj = context(source), component_for(component)
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        c = cs[0]
        area = "slots" if component == "C6b" else "context"
        parts = list(getattr(c, area))
        index = next(i for i, v in enumerate(parts) if v.slot in {"expression", "rejected"})
        v = parts[index]
        if mutation == "quote":
            v = replace(v, text="SYNTHETIC absent")
        elif mutation == "span":
            v = replace(v, span=(0, 9))
        elif mutation == "locator":
            v = replace(v, citations=(replace(v.citations[0], locator=""), *v.citations[1:]))
        elif mutation == "wrong_row":
            v = replace(v, citations=(citation(source["rows"][1]), *v.citations[1:]))
        elif mutation == "transform":
            v = replace(v, transform="SYNTHETIC paraphrase")
        if mutation == "missing":
            cs.pop()
        else:
            parts[index] = v
            cs[0] = replace(c, **{area: tuple(parts)})
        with pytest.raises(BuildError, match=code):
            gate(ctx, obj, component).run(cs)


def test_swapped_recommendation_and_sum11_alone_fail(source):
    write_receipt(source)
    ctx, obj = context(source), component_for("C7")
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        c = cs[0]
        rejected = next(v for v in c.context if v.slot == "rejected")
        cs[0] = replace(c, response=(replace(rejected, slot="modern_form", citations=(rejected.citations[0],)),))
        with pytest.raises(BuildError, match="binding_contrast"):
            gate(ctx, obj, "C7").run(cs)
        cs[0] = replace(
            c,
            context=tuple(
                replace(v, citations=(v.citations[0], v.citations[-1])) if v.slot == "recommended" else v
                for v in c.context
            ),
        )
        with pytest.raises(BuildError, match="binding_selector"):
            gate(ctx, obj, "C7").run(cs)


@pytest.mark.parametrize(
    "form", ["SYNTHETIC <edition> <year>", "SYNTHETIC cite the title per source", "SYNTHETIC unresolved"]
)
def test_attribution_never_guesses_held_metadata(source, form):
    row = source["rows"][0]
    with pytest.raises(BuildError, match="attribution_unresolved"):
        BOOK_ADAPTER.resolve(form, citation(row), row, None)


def test_attribution_maps_only_complete_held_bibliography(source):
    row = {
        **source["rows"][0],
        "bibliography": "SYNTHETIC author title edition 1 year 2000",
        "bibliography_evidence": "SYNTHETIC holdings receipt",
    }
    assert BOOK_ADAPTER.resolve(row["bibliography"], citation(row), row, None).bibliography == row["bibliography"]


def test_packet_writer_batches_only_located_rows_and_keeps_unicode_offsets(source, tmp_path):
    rows = [{**source["rows"][0], "id": i, "text": "SYNTHETIC α wrong right."} for i in range(43)]
    rows[-1]["section"] = ""
    stats = write_packets(rows, tmp_path / "SYNTHETIC-packets")
    assert stats == {"batches": 3, "rows": 42}
    for batch in batches(rows):
        receipts = selection_receipts(batch)
        for receipt in receipts.values():
            for item in receipt["rows"]:
                item["pairs"] = [pair_for({"text": rows[0]["text"]}, "wrong", "right")]
        assert all(r["reason"] == "ok" for r in validate_receipts(batch, receipts).values())
    with pytest.raises(BuildError, match="adjudication_batch_size"):
        batches(rows, 0)


@pytest.mark.parametrize(
    "table,mutation,reason",
    [
        ("ulif_dictua_entries", "status='quarantined'", "ulif_unattested"),
        ("ulif_dictua_entries", "homonym_checked=0", "ulif_unattested"),
        ("forms_all", "word_form='SYNTHETIC mismatch'", "vesum_unattested"),
        ("sum11", "sovietization_keywords=NULL", "sum11_markers_unavailable"),
    ],
)
def test_missing_or_ineligible_attestation_withholds(source, table, mutation, reason):
    write_receipt(source)
    path = source["vesum"] if table == "forms_all" else source["db"]
    with sqlite3.connect(path) as c:
        c.execute(f"UPDATE {table} SET {mutation} WHERE id=1")
    ctx, obj = context(source), component_for("C7")
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        assert cs[0].reason == reason
        assert cs[0].outcome == "withheld"
        records, report = gate(ctx, obj, "C7").run(cs)
        assert len(records) == 1
        assert report["accounting"]["C7"]["reasons"][reason] == 1


def test_changed_pair_form_keys_fail_independent_gate(source):
    write_receipt(source)
    ctx, obj = context(source), component_for("C7")
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        rec = next(v for v in cs[0].context if v.slot == "recommended")
        stored = ctx.reader.row(rec.citations[3])
        stored["recommended_key"] = "SYNTHETIC unrelated key"
        RECEIPTS.records[stored["id"]] = stored
        with pytest.raises(BuildError, match="binding_contrast"):
            gate(ctx, obj, "C7").run(cs)


def test_no_receipt_root_never_approves_and_shared_store_does_not_leak_sessions(source):
    with SnapshotReader({"sources.db": source["db"]}, {STORE: RECEIPTS}) as reader:
        ctx = ComponentContext(reader, {})
        assert next(component_for("C6b").iter_candidates(ctx)).reason == "adjudication_pending"
        assert RECEIPTS.file_hashes() == {}
        assert RECEIPTS.all_rows("C6b") == []
        with pytest.raises(BuildError, match="row_unavailable"):
            RECEIPTS.row("C6b", "id=SYNTHETIC absent")


@pytest.mark.parametrize("component", ["C6b", "C7"])
def test_source_bound_packet_build_verify_and_tamper_refusal(source, component, tmp_path):
    import yaml

    from scripts.projects.open_model_data.review_build.build import execute

    write_receipt(source)
    obj = component_for(component)
    ctx = context(source)
    with ctx.reader:
        list(obj.iter_candidates(ctx))
        g = gate(ctx, obj, component)
        catalog = g.catalog.data
        compatibility = list(g.roles.compatibility.values())
    obj.adapters = {s: SyntheticAdapter() for s in obj.adapters}
    (tmp_path / "SYNTHETIC-catalog.yaml").write_text(yaml.safe_dump(catalog))
    (tmp_path / "SYNTHETIC-register.yaml").write_text(yaml.safe_dump(register_data(sources=tuple(obj.adapters))))
    request = {
        "schema": "omd-review-request.v1",
        "catalog": "SYNTHETIC-catalog.yaml",
        "register": "SYNTHETIC-register.yaml",
        "components": {component: {}},
        "databases": {"sources.db": str(source["db"]), "vesum.db": str(source["vesum"])},
        "compatibility": compatibility,
        "antonenko_receipts": str(source["receipts"]),
    }
    config = tmp_path / "SYNTHETIC-request.json"
    config.write_bytes(canonical(request))
    with OutputGuard(tmp_path / "SYNTHETIC-build") as guard:
        execute(config, guard, component_objects={component: obj})
        assert execute(config, guard, verify=True, component_objects={component: obj})["status"] == "verified"
        manifest = json.loads(guard.read("manifest.json"))
        packet_name = next(n for n in manifest["files"] if "adjudication-packets" in n)
        guard.write(packet_name, b"SYNTHETIC changed packet")
        with pytest.raises(BuildError, match="artifact_mismatch"):
            execute(config, guard, verify=True, component_objects={component: obj})


@pytest.mark.parametrize("component", ["C6b", "C7"])
def test_multiple_pairs_per_row_preserve_row_denominator_and_all_records(source, component):
    row = source["rows"][0]
    row["text"] += " other better."
    with sqlite3.connect(source["db"]) as c:
        c.execute("UPDATE style_guide SET text=? WHERE id=1", (row["text"],))

    def add_pair(receipts):
        for seat in MODELS:
            receipts[seat]["rows"][0]["pairs"].append(pair_for(row, "other", "better"))
        receipts["opus"]["rows"][0]["pairs"].reverse()

    write_receipt(source, add_pair)
    ctx, obj = context(source), component_for(component)
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        records, report = gate(ctx, obj, component).run(cs)
        assert len(records) == 3
        assert report["accounting"][component]["accepted"] == 2
        assert report["operation_accounting"][f"{component}.{obj.spec['operations'][0]}"]["records_counted"] == 3
        with pytest.raises(BuildError, match="duplicate_record"):
            gate(ctx, obj, component).run([*cs, cs[0]])


@pytest.mark.parametrize("component", ["C6b", "C7"])
def test_same_quote_at_other_offset_does_not_replace_selected_span(source, component):
    row = source["rows"][0]
    row["text"] += " wrong"
    with sqlite3.connect(source["db"]) as c:
        c.execute("UPDATE style_guide SET text=? WHERE id=1", (row["text"],))
    write_receipt(source)
    ctx, obj = context(source), component_for(component)
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        area = "slots" if component == "C6b" else "context"
        parts = list(getattr(cs[0], area))
        i = next(i for i, v in enumerate(parts) if v.slot in {"expression", "rejected"})
        parts[i] = replace(parts[i], span=(row["text"].rindex("wrong"), len(row["text"])))
        cs[0] = replace(cs[0], **{area: tuple(parts)})
        with pytest.raises(BuildError, match="binding_span"):
            gate(ctx, obj, component).run(cs)


@pytest.mark.parametrize("seat", ["sol", "opus"])
def test_binding_rechecks_each_raw_receipt_digest(source, seat):
    write_receipt(source)
    ctx, obj = context(source), component_for("C6b")
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        sha = next(iter(RECEIPTS.documents))
        RECEIPTS.documents[sha][1][seat] += b"\n"
        with pytest.raises(BuildError, match="adjudication_stale"):
            gate(ctx, obj, "C6b").run(cs)


def test_packet_digest_refuses_changed_batch():
    row = {"id": 1, "text": "SYNTHETIC wrong right.", "section": "SYNTHETIC section"}
    batch = batches([row])[0]
    receipts = selection_receipts(batch)
    batch["rows"][0]["text"] += " changed"
    with pytest.raises(BuildError, match="adjudication_stale"):
        validate_receipts(batch, receipts)


def test_pending_c7_never_queries_headword_inventory(source, monkeypatch):
    ctx = context(source)
    with ctx.reader:
        monkeypatch.setattr(
            ctx.reader, "query_values", lambda q: pytest.fail("unexpected witness query before adjudication")
        )
        assert [c.reason for c in component_for("C7").iter_candidates(ctx)] == ["adjudication_pending"] * 2


def test_non_headword_pair_is_c6b_record_but_excluded_from_c7(source):
    write_receipt(source)
    with sqlite3.connect(source["db"]) as c:
        c.execute("DELETE FROM sum11 WHERE id=1")
    ctx = context(source)
    with ctx.reader:
        assert next(component_for("C6b").iter_candidates(ctx)).outcome == "accepted"
        assert next(component_for("C7").iter_candidates(ctx)).reason == "not_sum11_headword"


def test_c7_unstresses_comparison_without_changing_cited_text(source):
    row = source["rows"][0]
    row["text"] = "SYNTHETIC wro\u0301ng right."
    with sqlite3.connect(source["db"]) as c:
        c.execute("UPDATE style_guide SET text=? WHERE id=1", (row["text"],))
        c.execute("UPDATE sum11 SET word='wróng' WHERE id=1")
    write_receipt(source)
    ctx, obj = context(source), component_for("C7")
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        assert cs[0].outcome == "accepted"
        assert next(v.text for v in cs[0].context if v.slot == "rejected") == "wróng"
        assert len(gate(ctx, obj, "C7").run(cs)[0]) == 2


def test_receipt_store_refuses_unreviewed_unit_queries():
    with pytest.raises(BuildError, match="unit_query"):
        RECEIPTS.units({"kind": "antonenko_candidate_headwords.v1"})
