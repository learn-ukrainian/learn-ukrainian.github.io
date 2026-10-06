"""Synthetic-only WP6 source, packet, receipt, binding and accounting proofs."""

import copy
import json
import sqlite3
from dataclasses import replace

import pytest

from scripts.projects.open_model_data.review_build import output
from scripts.projects.open_model_data.review_build.attribution import Resolver, SyntheticAdapter
from scripts.projects.open_model_data.review_build.catalog import Catalog
from scripts.projects.open_model_data.review_build.components import ComponentContext, antonenko
from scripts.projects.open_model_data.review_build.components.antonenko import (
    BOOK_ADAPTER,
    MODELS,
    RECEIPTS,
    SOURCE,
    STORE,
    attestation_for,
    batches,
    book_locator,
    citation,
    validate_receipts,
    write_packets,
    write_reconciliation_packets,
)
from scripts.projects.open_model_data.review_build.components.c6b import BookCalqueComponent
from scripts.projects.open_model_data.review_build.contract import canonical, digest
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.gate import Gate
from scripts.projects.open_model_data.review_build.output import OutputGuard
from scripts.projects.open_model_data.review_build.snapshot import SnapshotReader
from tests.projects.open_model_data.review_build.conftest import STARTS, catalog_data, register_data


@pytest.fixture
def source(tmp_path, monkeypatch):
    monkeypatch.setattr(output, "filesystem", lambda p: "ext4")
    task_root = tmp_path / "SYNTHETIC-tasks"
    task_root.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(task_root))
    db = tmp_path / "SYNTHETIC-sources.db"
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
    receipt_root = tmp_path / "SYNTHETIC-receipts"
    with OutputGuard(receipt_root):
        pass
    return {"rows": rows, "db": db, "receipts": receipt_root}


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
            "task_id": f"SYNTHETIC-{seat}-task",
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
            write_attested(guard, f"{batch['batch_sha256']}.{seat}", receipt)
    return receipts


def write_attested(guard, prefix, receipt):
    raw = canonical(receipt)
    task = {
        "task_id": receipt["task_id"],
        "model": receipt["model"],
        "status": "done",
        "result_sha256": digest(raw),
        "finished_at": "2026-10-06T00:00:00Z",
    }
    # Malformed receipt fixtures still get dispatch metadata so the receipt validator decides.
    safe_id = receipt["task_id"] or "SYNTHETIC-empty"
    (antonenko.tasks_dir() / f"{safe_id}.json").write_bytes(canonical(task))
    (antonenko.tasks_dir() / f"{safe_id}.result").write_bytes(raw)
    guard.write(f"{prefix}.json", raw)
    guard.write(f"{prefix}.attestation.json", canonical(task))


def component_for(component, count=2):
    assert component == "C6b"
    obj = BookCalqueComponent()
    obj.spec = copy.deepcopy(obj.spec)
    obj.spec["operation_specs"][obj.spec["operations"][0]]["frozen_count"] = count
    return obj


def context(source):
    reader = SnapshotReader({"sources.db": source["db"]}, {STORE: RECEIPTS})
    return ComponentContext(reader, {"antonenko_receipts": str(source["receipts"])})


def gate(ctx, obj, component):
    operation = obj.spec["operations"][0]
    data = catalog_data()
    data["components"] = {
        "C6": {
            "instructions": [
                {
                    "id": f"{component}.{operation}.{i}",
                    "operation": operation,
                    "template": start + " SYNTHETIC {expression}",
                    "slots": ["expression"],
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
    ]
    obj.spec["compatibility"] = compatibility
    resolver = Resolver(register_data(sources=tuple(obj.adapters)), {s: SyntheticAdapter() for s in obj.adapters})
    return Gate(ctx.reader, Catalog(data), resolver, {component: obj.spec})


@pytest.mark.parametrize("component", ["C6b"])
def test_accept_paths_and_complete_accounting(source, component):
    write_receipt(source)
    obj, ctx = component_for(component), context(source)
    with ctx.reader:
        candidates = list(obj.iter_candidates(ctx))
        records, report = gate(ctx, obj, component).run(candidates)
        assert len(records) == report["accounting"][component]["accepted"] == 2
        assert ctx.reader.file_hashes()[STORE]


@pytest.mark.parametrize("component", ["C6b"])
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


@pytest.mark.parametrize("component", ["C6b"])
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
        assert report["accounting"][component]["reasons"][reason] == (2 if mode in {"different", "swapped"} else 1)


@pytest.mark.parametrize("component", ["C6b"])
@pytest.mark.parametrize(
    "mutation,code",
    [
        ("quote", "quote_mismatch"),
        ("span", "quote_mismatch"),
        ("locator", "empty_locator"),
        ("missing", "missing_unit"),
        ("wrong_row", "quote_mismatch"),
        ("transform", "unknown_transform"),
    ],
)
def test_component_generic_must_fail_fixtures(source, component, mutation, code):
    write_receipt(source)
    ctx, obj = context(source), component_for(component)
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        c = cs[0]
        area = "slots"
        parts = list(getattr(c, area))
        index = next(i for i, v in enumerate(parts) if v.slot == "expression")
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


def test_no_receipt_root_never_approves_and_shared_store_does_not_leak_sessions(source):
    with SnapshotReader({"sources.db": source["db"]}, {STORE: RECEIPTS}) as reader:
        ctx = ComponentContext(reader, {})
        assert next(component_for("C6b").iter_candidates(ctx)).reason == "adjudication_pending"
        assert RECEIPTS.file_hashes() == {}
        assert len(RECEIPTS.all_rows("C6b")) == 2
        with pytest.raises(BuildError, match="row_unavailable"):
            RECEIPTS.row("C6b", "id=SYNTHETIC absent")


@pytest.mark.parametrize("component", ["C6b"])
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
    obj.adapters = {s: SyntheticAdapter() for s in obj.adapters}
    (tmp_path / "SYNTHETIC-catalog.yaml").write_text(yaml.safe_dump(catalog))
    (tmp_path / "SYNTHETIC-register.yaml").write_text(yaml.safe_dump(register_data(sources=tuple(obj.adapters))))
    request = {
        "schema": "omd-review-request.v2",
        "catalog": "SYNTHETIC-catalog.yaml",
        "register": "SYNTHETIC-register.yaml",
        "databases": {"sources.db": str(source["db"])},
        "ua_gec": {"root": "SYNTHETIC-unused"},
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


@pytest.mark.parametrize("component", ["C6b"])
def test_multiple_pairs_per_row_count_each_pair_and_emit_all_records(source, component):
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
        assert report["accounting"][component]["accepted"] == 3
        assert report["operation_accounting"][f"{component}.{obj.spec['operations'][0]}"]["records_counted"] == 3
        with pytest.raises(BuildError, match="duplicate_unit"):
            gate(ctx, obj, component).run([*cs, cs[0]])


@pytest.mark.parametrize("component", ["C6b"])
def test_same_quote_at_other_offset_does_not_replace_selected_span(source, component):
    row = source["rows"][0]
    row["text"] += " wrong"
    with sqlite3.connect(source["db"]) as c:
        c.execute("UPDATE style_guide SET text=? WHERE id=1", (row["text"],))
    write_receipt(source)
    ctx, obj = context(source), component_for(component)
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        area = "slots"
        parts = list(getattr(cs[0], area))
        i = next(i for i, v in enumerate(parts) if v.slot == "expression")
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


def test_receipt_store_refuses_unreviewed_unit_queries():
    with pytest.raises(BuildError, match="unit_query"):
        RECEIPTS.units({"kind": "SYNTHETIC-unreviewed-unit-query"})


def add_second_pair(source, receipts, *, both=True):
    row = source["rows"][0]
    pair = pair_for(row, "other", "better")
    receipts["sol"]["rows"][0]["pairs"].append(pair)
    if both:
        receipts["opus"]["rows"][0]["pairs"].append(copy.deepcopy(pair))


def expand_row(source):
    source["rows"][0]["text"] += " other better."
    with sqlite3.connect(source["db"]) as db:
        db.execute("UPDATE style_guide SET text=? WHERE id=1", (source["rows"][0]["text"],))


@pytest.mark.parametrize("component", ["C6b"])
def test_one_disputed_pair_preserves_agreed_sibling_and_union_denominator(source, component):
    expand_row(source)
    write_receipt(source, lambda r: add_second_pair(source, r, both=False))
    ctx, obj = context(source), component_for(component)
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        records, report = gate(ctx, obj, component).run(cs)
        assert len(records) == report["accounting"][component]["accepted"] == 2
        assert report["accounting"][component]["counted"] == 3
        assert report["accounting"][component]["reasons"] == {"adjudication_disagreement": 1, "agreed": 2}
        row_units = [c for c in cs if RECEIPTS.records[c.unit_id]["book_id"] == 1]
        assert len(row_units) == 2 and len({c.unit_id for c in row_units}) == 2


def reconciliation_receipts(source, decisions=None):
    pair = pair_for(source["rows"][0], "other", "better")
    batch = batches(source["rows"])[0]
    return {
        seat: {
            "schema": "antonenko-reconcile-receipt.v1",
            "model": model,
            "task_id": f"SYNTHETIC-reconcile-{seat}",
            "batch_sha256": batch["batch_sha256"],
            "pairs": [{"row_id": 1, **pair, "decision": (decisions or {}).get(seat, "accept")}],
        }
        for seat, model in MODELS.items()
    }


def write_reconciliation(source, receipts):
    sha = batches(source["rows"])[0]["batch_sha256"]
    with OutputGuard(source["receipts"]) as guard:
        for seat, receipt in receipts.items():
            write_attested(guard, f"{sha}.reconcile.{seat}", receipt)


@pytest.mark.parametrize("component", ["C6b"])
@pytest.mark.parametrize("decisions,accepted", [({}, 3), ({"sol": "reject"}, 2), ({"opus": "reject"}, 2)])
def test_reconciliation_requires_both_accepts(source, component, decisions, accepted):
    expand_row(source)
    write_receipt(source, lambda r: add_second_pair(source, r, both=False))
    write_reconciliation(source, reconciliation_receipts(source, decisions))
    ctx, obj = context(source), component_for(component)
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        records, report = gate(ctx, obj, component).run(cs)
        assert len(records) == report["accounting"][component]["accepted"] == accepted
        assert report["accounting"][component]["counted"] == 3
        assert report["accounting"][component]["withheld"] == 3 - accepted
        assert report["accounting"][component]["reasons"] == {
            "agreed": 2,
            "reconciled_accepted" if accepted == 3 else "reconciled_rejected": 1,
        }
        unit = next(u for u in RECEIPTS.records.values() if u["reason"].startswith("reconciled"))
        assert RECEIPTS.row("C6b", "id=" + unit["id"]) == unit
        assert next(iter(RECEIPTS.decisions.values()))["disputed"] == []
        assert any("reconcile" in name for name in RECEIPTS.file_hashes())


def test_reconciled_admission_cannot_be_relabelled_as_an_original_agreement(source):
    expand_row(source)
    write_receipt(source, lambda r: add_second_pair(source, r, both=False))
    write_reconciliation(source, reconciliation_receipts(source))
    ctx = context(source)
    with ctx.reader:
        list(component_for("C6b").iter_candidates(ctx))
        unit = next(u for u in RECEIPTS.records.values() if u["reason"] == "reconciled_accepted")
        unit["reason"] = "agreed"
        with pytest.raises(BuildError, match="adjudication_direction"):
            RECEIPTS.row("C6b", "id=" + unit["id"])


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("missing_seat", "adjudication_seats"),
        ("unknown_pair", "adjudication_pairs"),
        ("duplicate", "adjudication_pairs"),
        ("decision", "adjudication_decision"),
        ("missing_pair", "adjudication_pairs"),
        ("stale", "adjudication_stale"),
        ("wrong_model", "adjudication_provenance"),
    ],
)
def test_reconciliation_refuses_unbound_or_incomplete_decisions(source, mutation, code):
    expand_row(source)
    write_receipt(source, lambda r: add_second_pair(source, r, both=False))
    receipts = reconciliation_receipts(source)
    sol = receipts["sol"]
    if mutation == "missing_seat":
        receipts.pop("opus")
    elif mutation == "unknown_pair":
        sol["pairs"][0]["recommended"]["end"] -= 1
    elif mutation == "duplicate":
        sol["pairs"].append(copy.deepcopy(sol["pairs"][0]))
    elif mutation == "decision":
        sol["pairs"][0]["decision"] = "maybe"
    elif mutation == "missing_pair":
        sol["pairs"] = []
    elif mutation == "stale":
        sol["batch_sha256"] = "0" * 64
    else:
        sol["model"] = MODELS["opus"]
    write_reconciliation(source, receipts)
    ctx = context(source)
    with ctx.reader, pytest.raises(BuildError, match=code):
        list(component_for("C6b").iter_candidates(ctx))


@pytest.mark.parametrize("reconciliation", [False, True])
@pytest.mark.parametrize(
    "mutation,code",
    [
        ("missing", "adjudication_attestation"),
        ("status", "adjudication_provenance"),
        ("model", "adjudication_provenance"),
        ("task", "adjudication_provenance"),
        ("digest", "adjudication_provenance"),
        ("finished", "adjudication_provenance"),
        ("dispatch_status", "adjudication_provenance"),
        ("dispatch_model", "adjudication_provenance"),
        ("result", "adjudication_stale"),
        ("different_receipt", "adjudication_stale"),
    ],
)
def test_sidecar_binds_each_receipt_to_settled_dispatch(source, reconciliation, mutation, code):
    expand_row(source)
    write_receipt(source, lambda r: add_second_pair(source, r, both=False))
    if reconciliation:
        write_reconciliation(source, reconciliation_receipts(source))
    sha = batches(source["rows"])[0]["batch_sha256"]
    prefix = sha + (".reconcile" if reconciliation else "") + ".sol"
    sidecar_path = source["receipts"] / f"{prefix}.attestation.json"
    sidecar = json.loads(sidecar_path.read_bytes())
    task_path = antonenko.tasks_dir() / f"{sidecar['task_id']}.json"
    result_path = antonenko.tasks_dir() / f"{sidecar['task_id']}.result"
    if mutation == "missing":
        sidecar_path.unlink()
    elif mutation in {"dispatch_status", "dispatch_model"}:
        task = json.loads(task_path.read_bytes())
        task[mutation.removeprefix("dispatch_")] = "running" if mutation.endswith("status") else MODELS["opus"]
        task_path.write_bytes(canonical(task))
    elif mutation == "result":
        result_path.write_bytes(b"SYNTHETIC changed result")
    elif mutation == "different_receipt":
        receipt_path = source["receipts"] / f"{prefix}.json"
        receipt = json.loads(receipt_path.read_bytes())
        receipt["batch_sha256"] = "0" * 64
        receipt_path.write_bytes(canonical(receipt))
    else:
        key, value = {
            "status": ("status", "running"),
            "model": ("model", MODELS["opus"]),
            "task": ("task_id", "SYNTHETIC-other-task"),
            "digest": ("result_sha256", "0" * 64),
            "finished": ("finished_at", ""),
        }[mutation]
        sidecar[key] = value
        sidecar_path.write_bytes(canonical(sidecar))
    ctx = context(source)
    with ctx.reader, pytest.raises(BuildError, match=code):
        list(component_for("C6b").iter_candidates(ctx))


def test_sidecar_extractor_supports_fenced_result_and_refuses_multiple_payloads(source):
    batch = batches(source["rows"])[0]
    receipt = selection_receipts(batch)["sol"]
    raw = b"SYNTHETIC result\n```json\n" + canonical(receipt) + b"\n```\n"
    task = {
        "task_id": receipt["task_id"],
        "model": receipt["model"],
        "status": "done",
        "result_sha256": digest(raw),
        "finished_at": "2026-10-06T00:00:00Z",
    }
    assert attestation_for(receipt, task, raw)["result_sha256"] == digest(raw)
    duplicate = raw + raw
    task["result_sha256"] = digest(duplicate)
    with pytest.raises(BuildError, match="adjudication_receipt"):
        attestation_for(receipt, task, duplicate)


@pytest.mark.parametrize("matching_first", [False, True])
def test_sidecar_extractor_selects_matching_batch_from_two_blocks(source, matching_first):
    receipt = selection_receipts(batches(source["rows"])[0])["sol"]
    other = {**receipt, "batch_sha256": "0" * 64}
    payloads = [receipt, other] if matching_first else [other, receipt]
    raw = b"SYNTHETIC result\n" + b"\n".join(b"```json\n" + canonical(p) + b"\n```" for p in payloads)
    task = {
        "task_id": receipt["task_id"],
        "model": receipt["model"],
        "status": "done",
        "result_sha256": digest(raw),
        "finished_at": "2026-10-06T00:00:00Z",
    }
    assert attestation_for(receipt, task, raw) == task


@pytest.mark.parametrize("payload_kind", ["mismatched", "duplicate", "changed", "non_object"])
def test_sidecar_extractor_refuses_missing_ambiguous_or_changed_matching_block(source, payload_kind):
    receipt = selection_receipts(batches(source["rows"])[0])["sol"]
    other = {**receipt, "batch_sha256": "0" * 64}
    payloads = {
        "mismatched": [other, {**other, "batch_sha256": "1" * 64}],
        "duplicate": [receipt, other, receipt],
        "changed": [other, {**receipt, "rows": []}],
        "non_object": [[], None],
    }[payload_kind]
    raw = b"\n".join(b"```json\n" + canonical(p) + b"\n```" for p in payloads)
    task = {
        "task_id": receipt["task_id"],
        "model": receipt["model"],
        "status": "done",
        "result_sha256": digest(raw),
        "finished_at": "2026-10-06T00:00:00Z",
    }
    code = "adjudication_stale" if payload_kind == "changed" else "adjudication_receipt"
    with pytest.raises(BuildError, match=code):
        attestation_for(receipt, task, raw)


def test_sidecar_rechecked_and_pinned_after_candidate_extraction(source):
    write_receipt(source)
    ctx, obj = context(source), component_for("C6b")
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        path = next(source["receipts"].glob("*.sol.attestation.json"))
        path.write_bytes(path.read_bytes() + b"\n")
        with pytest.raises(BuildError, match="adjudication_stale"):
            gate(ctx, obj, "C6b").run(cs)


def test_reconciliation_packet_preserves_row_and_exact_disputed_span_texts(source, tmp_path):
    expand_row(source)
    write_receipt(source, lambda r: add_second_pair(source, r, both=False))
    root = tmp_path / "SYNTHETIC-reconcile-packets"
    assert write_reconciliation_packets(iter(source["rows"]), source["receipts"], root) == {"batches": 1, "pairs": 1}
    packet = json.loads(next(root.glob("*.json")).read_bytes())
    pair = packet["pairs"][0]
    assert pair["text"] == source["rows"][0]["text"]
    assert pair["rejected_text"] == "other" and pair["recommended_text"] == "better"
    assert pair["row_text_sha256"] == digest(pair["text"].encode())
    assert (root.stat().st_mode & 0o777) == 0o700
    with pytest.raises(BuildError, match="repository_output"):
        write_reconciliation_packets(source["rows"], source["receipts"], __file__)


def test_c6b_context_empty_book_row_only_in_provenance(source):
    write_receipt(source)
    ctx, obj = context(source), component_for("C6b")
    with ctx.reader:
        records, _ = gate(ctx, obj, "C6b").run(list(obj.iter_candidates(ctx)))
        assert all(r["context"] == "" for r in records)
        for record in records:
            assert all(v["slot"] not in {"passage", "author"} for v in record["values"])
            assert any(p["table"] == "style_guide" and p["field"] == "text" for p in record["provenance"].values())


def test_malformed_receipt_json_is_typed(source):
    write_receipt(source)
    path = next(source["receipts"].glob("*.sol.json"))
    path.write_bytes(b"{SYNTHETIC invalid JSON")
    ctx = context(source)
    with ctx.reader, pytest.raises(BuildError, match="adjudication_receipt"):
        list(component_for("C6b").iter_candidates(ctx))


def test_pair_expansion_does_not_relax_frozen_source_census(source):
    expand_row(source)
    write_receipt(source, lambda r: add_second_pair(source, r))
    ctx, obj = context(source), component_for("C6b", count=3)
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        assert len(cs) == 3
        with pytest.raises(BuildError, match="frozen_count"):
            gate(ctx, obj, "C6b").run(cs)


def test_missing_derived_pair_and_duplicate_unit_refuse_build(source):
    expand_row(source)
    write_receipt(source, lambda r: add_second_pair(source, r))
    ctx, obj = context(source), component_for("C6b")
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        with pytest.raises(BuildError, match="missing_unit"):
            gate(ctx, obj, "C6b").run(cs[1:])
        with pytest.raises(BuildError, match="duplicate_unit"):
            gate(ctx, obj, "C6b").run([*cs, cs[0]])


def test_dispatch_payload_binding_does_not_coerce_boolean_offsets(source):
    receipt = selection_receipts(batches(source["rows"])[0])["sol"]
    actual = copy.deepcopy(receipt)
    actual["rows"][0]["pairs"][0]["rejected"]["start"] = True
    receipt["rows"][0]["pairs"][0]["rejected"]["start"] = 1
    raw = canonical(actual)
    task = {
        "task_id": receipt["task_id"],
        "model": receipt["model"],
        "status": "done",
        "result_sha256": digest(raw),
        "finished_at": "2026-10-06T00:00:00Z",
    }
    with pytest.raises(BuildError, match="adjudication_stale"):
        attestation_for(receipt, task, raw)
