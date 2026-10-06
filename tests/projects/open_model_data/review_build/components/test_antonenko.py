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
    BOOK_REGISTER_FORM,
    MODELS,
    RECEIPTS,
    SOURCE,
    STORE,
    attestation_for,
    batches,
    book_locator,
    citation,
    filtered_pairs,
    identity_relation,
    inverse_identities,
    pair_identity,
    pin_dispatch_files,
    recommended_lookup,
    validate_receipts,
    write_packets,
    write_reconciliation_packets,
)
from scripts.projects.open_model_data.review_build.components.c6b import COMPATIBILITY, BookCalqueComponent
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
    vesum = tmp_path / "SYNTHETIC-vesum.db"
    with sqlite3.connect(vesum) as vesum_connection:
        vesum_connection.execute(
            "CREATE TABLE forms_all(id INTEGER PRIMARY KEY, word_form TEXT, word_form_folded TEXT, lemma TEXT)"
        )
        vesum_connection.executemany(
            "INSERT INTO forms_all VALUES (?, ?, ?, ?)",
            [
                (i, word, word.casefold(), word.casefold())
                for i, word in enumerate(("SYNTHETIC", "wrong", "right", "other", "better", "long", "target"), 1)
            ],
        )
    return {"rows": rows, "db": db, "receipts": receipt_root, "vesum": vesum}


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
    guard.write(f"dispatch/{safe_id}.json", canonical(task))
    guard.write(f"dispatch/{safe_id}.result", raw)
    hashes_path = guard.path / "dispatch/hashes.json"
    hashes = json.loads(guard.read("dispatch/hashes.json")) if hashes_path.exists() else {}
    hashes.update({f"dispatch/{safe_id}.json": digest(canonical(task)), f"dispatch/{safe_id}.result": digest(raw)})
    guard.write("dispatch/hashes.json", canonical(hashes))
    guard.write(f"{prefix}.json", raw)
    guard.write(f"{prefix}.attestation.json", canonical(task))


def component_for(component, count=2):
    assert component == "C6b"
    obj = BookCalqueComponent()
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
        reason = {
            "both_empty": "no_pair_named",
            "swapped": "inverse_pair_in_row",
            "different": "recommended_unattested",
            "single_empty": "adjudication_disagreement",
        }[mode]
        assert cs[0].outcome == "withheld" and cs[0].reason == reason
        report = gate(ctx, obj, component).run(cs)[1]
        assert report["accounting"][component]["reasons"][reason] == (2 if mode == "swapped" else 1)


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


@pytest.mark.parametrize(
    "page,section", [(3, "SYNTHETIC section"), (0, "SYNTHETIC section"), (None, "SYNTHETIC section")]
)
def test_attribution_maps_registered_form_without_inventing_edition(source, page, section):
    row = {**source["rows"][0], "source": "Антоненко-Давидович", "page": page, "section": section}
    result = BOOK_ADAPTER.resolve(BOOK_REGISTER_FORM, citation(row), row, None)
    assert result.mapped_form == BOOK_REGISTER_FORM
    assert "<" not in result.bibliography and "otherwise" not in result.bibliography
    assert str(page) in result.bibliography if page else section in result.bibliography
    assert BOOK_REGISTER_FORM.split(". С.")[0] in result.bibliography


@pytest.mark.parametrize(
    "mutation,code",
    [("source", "attribution_unresolved"), ("locator", "locator_unavailable"), ("store", "attribution_unresolved")],
)
def test_book_attribution_refuses_wrong_source_or_missing_locator(source, mutation, code):
    row = {**source["rows"][0], "source": "Антоненко-Давидович"}
    cited = citation(row)
    if mutation == "source":
        row["source"] = "SYNTHETIC wrong source"
    elif mutation == "locator":
        row.update(page=0, section="")
    else:
        cited = replace(cited, store="SYNTHETIC wrong store")
    with pytest.raises(BuildError, match=code):
        BOOK_ADAPTER.resolve(BOOK_REGISTER_FORM, cited, row, None)


def test_receipt_attribution_uses_held_book_locator_and_checks_source(source):
    from types import SimpleNamespace

    book = {**source["rows"][0], "source": "Антоненко-Давидович"}
    row = {
        "book_id": book["id"],
        "source": book["source"],
        "pair": "id=1",
        "row_text_sha256": digest(book["text"].encode()),
    }
    observed = []

    def lookup(cited):
        observed.append(cited)
        return book

    reader = SimpleNamespace(row=lookup)
    cited = replace(citation(book), store=STORE, table="C6b")
    assert (
        BOOK_ADAPTER.resolve(BOOK_REGISTER_FORM, cited, row, reader).bibliography
        == BOOK_ADAPTER.resolve(BOOK_REGISTER_FORM, citation(book), book, reader).bibliography
    )
    assert observed[0].store == "sources.db" and observed[0].row_key == "id=1"
    assert observed[0].field_sha256 == digest(book["text"].encode())
    row["source"] = "SYNTHETIC wrong source"
    with pytest.raises(BuildError, match="attribution_unresolved"):
        BOOK_ADAPTER.resolve(BOOK_REGISTER_FORM, cited, row, reader)


def test_receipt_book_attribution_uses_real_snapshot_digest_validation(source):
    write_receipt(source)
    with sqlite3.connect(source["db"]) as writer:
        writer.execute("UPDATE style_guide SET source=?", (COMPATIBILITY[0]["source_values"][0],))
    ctx = context(source)
    with ctx.reader:
        candidates = list(component_for("C6b").iter_candidates(ctx))
        cited = candidates[0].slots[0].citations[1]
        row = ctx.reader.row(cited)
        result = BOOK_ADAPTER.resolve(BOOK_REGISTER_FORM, cited, row, ctx.reader)
        assert source["rows"][0]["section"] in result.bibliography
        row["row_text_sha256"] = "0" * 64
        with pytest.raises(BuildError, match="field_digest"):
            BOOK_ADAPTER.resolve(BOOK_REGISTER_FORM, cited, row, ctx.reader)


def test_c6b_policy_is_component_owned_and_detached_from_other_builds():
    first, second = BookCalqueComponent(), BookCalqueComponent()
    assert first.spec["compatibility"] == COMPATIBILITY
    assert {(r["store"], r["table"]) for r in COMPATIBILITY} == {("sources.db", "style_guide"), (STORE, "C6b")}
    first.spec["compatibility"][0]["source_values"].clear()
    assert second.spec["compatibility"] == COMPATIBILITY


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
    with SnapshotReader({"sources.db": source["db"], "vesum.db": source["vesum"]}, {STORE: RECEIPTS}) as reader:
        ctx = ComponentContext(reader, {})
        assert next(component_for("C6b").iter_candidates(ctx)).reason == "adjudication_pending"
        assert RECEIPTS.file_hashes() == {}
        assert len(RECEIPTS.all_rows("C6b")) == 2
        with pytest.raises(BuildError, match="row_unavailable"):
            RECEIPTS.row("C6b", "id=SYNTHETIC absent")


@pytest.mark.parametrize("component", ["C6b"])
@pytest.mark.parametrize("tamper", ["packet", "lemma", "new_analysis", "remove_analysis"])
def test_source_bound_packet_build_verify_and_tamper_refusal(source, component, tmp_path, tamper):
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
        "databases": {"sources.db": str(source["db"]), "vesum.db": str(source["vesum"])},
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
        if tamper == "packet":
            guard.write(packet_name, b"SYNTHETIC changed packet")
        else:
            with sqlite3.connect(source["vesum"]) as db:
                if tamper == "lemma":
                    db.execute("UPDATE forms_all SET lemma='SYNTHETIC changed lemma' WHERE word_form='wrong'")
                elif tamper == "new_analysis":
                    db.execute("INSERT INTO forms_all VALUES (99, 'wrong', 'wrong', 'SYNTHETIC alternative')")
                else:
                    db.execute("DELETE FROM forms_all WHERE word_form='wrong'")
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
    task_path = source["receipts"] / f"dispatch/{sidecar['task_id']}.json"
    result_path = source["receipts"] / f"dispatch/{sidecar['task_id']}.result"
    if mutation == "missing":
        sidecar_path.unlink()
    elif mutation in {"dispatch_status", "dispatch_model"}:
        task = json.loads(task_path.read_bytes())
        task[mutation.removeprefix("dispatch_")] = "running" if mutation.endswith("status") else MODELS["opus"]
        task_path.write_bytes(canonical(task))
        hashes_path = source["receipts"] / "dispatch/hashes.json"
        hashes = json.loads(hashes_path.read_bytes())
        hashes[f"dispatch/{sidecar['task_id']}.json"] = digest(canonical(task))
        hashes_path.write_bytes(canonical(hashes))
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


def test_receipt_reads_need_no_live_tasks_and_pinned_dispatch_tamper_refuses(source, monkeypatch):
    write_receipt(source)
    monkeypatch.setattr(antonenko, "tasks_dir", lambda: (_ for _ in ()).throw(AssertionError("live read")))
    ctx, obj = context(source), component_for("C6b")
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        assert len(gate(ctx, obj, "C6b").run(cs)[0]) == 2
        path = next((source["receipts"] / "dispatch").glob("*.result"))
        path.write_bytes(path.read_bytes() + b"changed")
        with pytest.raises(BuildError, match="adjudication_stale"):
            gate(ctx, obj, "C6b").run(cs)


def test_pin_dispatch_copies_once_and_reuses_hashes_without_live_store(source, monkeypatch):
    write_receipt(source)
    task_root = antonenko.tasks_dir()
    for path in (source["receipts"] / "dispatch").glob("*"):
        if path.name != "hashes.json":
            (task_root / path.name).write_bytes(path.read_bytes())
        path.unlink()
    assert pin_dispatch_files(source["receipts"]) == {"files": 4}
    monkeypatch.setattr(antonenko, "tasks_dir", lambda: (_ for _ in ()).throw(AssertionError("live read")))
    assert pin_dispatch_files(source["receipts"]) == {"files": 4}
    path = next((source["receipts"] / "dispatch").glob("*.result"))
    path.write_bytes(b"changed")
    with pytest.raises(BuildError, match="adjudication_stale"):
        pin_dispatch_files(source["receipts"])


def test_missing_source_row_fails_even_when_derived_query_and_candidates_agree(source):
    write_receipt(source)
    ctx, obj = context(source), component_for("C6b")
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        del RECEIPTS.records[cs[1].unit_id]
        with pytest.raises(BuildError, match="census_coverage"):
            gate(ctx, obj, "C6b").run(cs[:1])


def test_recommended_lookup_cites_each_token_and_preserves_missing_evidence(source):
    ctx = context(source)
    with ctx.reader:
        lookups = recommended_lookup("RIGHT, better; unknown.", ctx.reader)
        assert [x["token"] for x in lookups] == ["RIGHT", "better", "unknown"]
        assert [bool(x["citations"]) for x in lookups] == [True, True, False]
        assert [x["lemmas"] for x in lookups] == [["right"], ["better"], []]
        assert ctx.reader.snapshots()["vesum.db:forms_all"]


@pytest.fixture
def lexeme_source(source):
    # Synthetic morphology, with expectations separately asserted below. The
    # ambiguous analysis deliberately follows the first analysis in id order.
    forms = [
        ("alphas", "alpha"),
        ("alphal", "alpha"),
        ("betas", "beta"),
        ("betal", "beta"),
        ("ambiguous", "alpha"),
        ("ambiguous", "beta"),
        ("gammas", "gamma"),
        ("shared", "common"),
        ("shareds", "common"),
    ]
    with sqlite3.connect(source["vesum"]) as db:
        db.executemany(
            "INSERT INTO forms_all VALUES (?, ?, ?, ?)",
            [(i, form, form.casefold(), lemma) for i, (form, lemma) in enumerate(forms, 100)],
        )
    return source


def test_lookup_uses_all_analyses_with_independent_expected_citations(lexeme_source):
    ctx = context(lexeme_source)
    with ctx.reader:
        lookup = recommended_lookup("AMBIGUOUS alphas missing", ctx.reader)
        assert [item["lemmas"] for item in lookup] == [["alpha", "beta"], ["alpha"], []]
        assert [[c["row_key"] for c in item["citations"]] for item in lookup] == [
            ["id=104", "id=105"],
            ["id=100"],
            [],
        ]
        assert [[c["field_sha256"] for c in item["lemma_citations"]] for item in lookup] == [
            [digest(b"alpha"), digest(b"beta")],
            [digest(b"alpha")],
            [],
        ]
        for item in lookup:
            for cited in item["citations"] + item["lemma_citations"]:
                assert ctx.reader.field(antonenko.Citation(**cited))[1] in {"ambiguous", "alphas", "alpha", "beta"}
        assert ctx.reader.reads[("vesum.db", "forms_all")] == {
            ("id=104", digest(b"ambiguous")),
            ("id=104", digest(b"alpha")),
            ("id=105", digest(b"ambiguous")),
            ("id=105", digest(b"beta")),
            ("id=100", digest(b"alphas")),
            ("id=100", digest(b"alpha")),
        }


@pytest.mark.parametrize(
    "forms,expected",
    [
        # Inflected inverse; ambiguous overlap must retain the second lemma.
        ([("alphas", "betas"), ("betal", "alphal")], ["inverse_pair_in_row"] * 2),
        ([("alphas", "ambiguous"), ("betal", "alphal")], ["inverse_pair_in_row"] * 2),
        ([("ALPHAS", "betas"), ("BETAL", "ALPHAL")], ["inverse_pair_in_row"] * 2),
        # Shared phrase lemmas cancel on both sides, regardless of inflection.
        ([("shared alphas", "shared betas"), ("shareds betal", "shareds alphal")], ["inverse_pair_in_row"] * 2),
        # A shared carrier alone cannot turn unrelated corrections into inverses.
        ([("shared alphas", "shared betas"), ("shareds gammas", "shareds alphal")], ["agreed"] * 2),
        ([("alphas", "betas"), ("gammas", "alphal")], ["agreed"] * 2),
        ([("alphas", "betas")], ["agreed"]),
        # Unknown rejected identity is ordinary for one-direction corrections.
        ([("missing", "betas")], ["agreed"]),
        ([("missing", "betas"), ("absent", "betal")], ["agreed"] * 2),
        # Half-proven inverse is unsafe; two unknown directions prove nothing.
        ([("alphas", "betas"), ("missing", "alphal")], ["inverse_pair_in_row"] * 2),
        ([("missing", "betas"), ("absent", "gammas")], ["agreed"] * 2),
        # Incomplete phrase identity is unknown rather than proven-different.
        ([("alphas", "betas"), ("missing gammas", "alphal")], ["inverse_pair_in_row"] * 2),
        # Empty phrase remainders cannot establish equality.
        ([("shared", "shareds"), ("shareds", "shared shareds")], ["agreed"] * 2),
        # Equal known single-word lemma sets do not establish two lexemes.
        ([("alphas", "alphal"), ("ALPHAL", "ALPHAS")], ["agreed"] * 2),
    ],
)
def test_lexeme_inverse_dispositions_and_gate(lexeme_source, forms, expected):
    row = lexeme_source["rows"][0]
    row["text"] = "SYNTHETIC " + "; ".join(f"{left} / {right}" for left, right in forms)
    spans = []
    cursor = len("SYNTHETIC ")
    for left, right in forms:
        spans.append(
            {
                "rejected": {"start": cursor, "end": cursor + len(left)},
                "recommended": {"start": cursor + len(left) + 3, "end": cursor + len(left) + 3 + len(right)},
            }
        )
        cursor += len(left) + len(right) + 5
    with sqlite3.connect(lexeme_source["db"]) as db:
        db.execute("UPDATE style_guide SET text=? WHERE id=1", (row["text"],))

    def select(receipts):
        for receipt in receipts.values():
            receipt["rows"][0]["pairs"] = spans

    write_receipt(lexeme_source, select)
    ctx, obj = context(lexeme_source), component_for("C6b")
    with ctx.reader:
        candidates = list(obj.iter_candidates(ctx))
        units = RECEIPTS.row_units(row)
        assert [unit["reason"] for unit in units] == expected
        assert all(
            unit["rejected_form"] == left and unit["recommended_form"] == right
            for unit, (left, right) in zip(units, forms, strict=True)
        )
        records, report = gate(ctx, obj, "C6b").run(candidates)
        assert report["accounting"]["C6b"]["counted"] == len(forms) + 1
        assert len(records) == 1 + expected.count("agreed")
        for unit in units:
            assert RECEIPTS.row("C6b", "id=" + unit["id"]) == unit
        if "inverse_pair_in_row" in expected:
            unit = units[0]
            unit.update(reason="agreed", eligible=True)
            with pytest.raises(BuildError, match="adjudication_direction"):
                RECEIPTS.row("C6b", "id=" + unit["id"])


@pytest.mark.parametrize("changed_token", ["wrong", "other"])
def test_lookup_changes_cannot_change_receipt_admission(lexeme_source, monkeypatch, changed_token):
    expand_row(lexeme_source)
    write_receipt(lexeme_source, lambda receipts: add_second_pair(lexeme_source, receipts))
    ctx, obj = context(lexeme_source), component_for("C6b")
    with ctx.reader:
        list(obj.iter_candidates(ctx))
        unit = RECEIPTS.row_units(lexeme_source["rows"][0])[0]
        original = ctx.reader.query_values

        def changed_lookup(query):
            return [] if query.get("parameters") == [changed_token] else original(query)

        monkeypatch.setattr(ctx.reader, "query_values", changed_lookup)
        with pytest.raises(BuildError, match="adjudication_stale"):
            RECEIPTS.row("C6b", "id=" + unit["id"])


def test_identity_unknown_and_distinctness_controls():
    assert identity_relation((set(), True), (set(), True)) == "unknown"
    assert identity_relation(({"alpha"}, True), ({"beta"}, False)) == "unknown"
    assert identity_relation(({"alpha"}, True), ({"beta"}, True)) == "different"
    assert identity_relation(({"alpha"}, False), ({"alpha", "beta"}, True)) == "shared"
    assert pair_identity({"rejected": [], "recommended": []}) == ((set(), False), (set(), False))
    assert not inverse_identities(None, (({"alpha"}, True), ({"beta"}, True)))


@pytest.mark.parametrize(
    "decision", ["agreed", "reconciled_accepted", "reconciled_rejected", "adjudication_disagreement"]
)
def test_nested_pair_is_subsumed_regardless_of_reconciliation(decision):
    text = "long wrong long right"
    big, small = ((0, 10), (11, 21)), ((5, 10), (16, 21))
    pairs = [(*big, "agreed"), (*small, decision)]
    lookups = {
        pair: {side: [{"citations": ["SYNTHETIC witness"], "lemmas": []}] for side in ("rejected", "recommended")}
        for pair in (big, small)
    }
    assert filtered_pairs(pairs, text, lookups) == {big: "agreed", small: "subsumed_span"}


def test_inverse_union_includes_nonadmitted_inverse_and_duplicates_keep_first():
    text = "wrong right wrong right"
    first, repeated, inverse = ((0, 5), (6, 11)), ((12, 17), (18, 23)), ((6, 11), (0, 5))
    lookups = {
        pair: {side: [{"citations": ["SYNTHETIC witness"], "lemmas": []}] for side in ("rejected", "recommended")}
        for pair in (first, repeated, inverse)
    }
    pairs = [(*repeated, "agreed"), (*first, "agreed")]
    assert filtered_pairs(pairs, text, lookups) == {first: "agreed", repeated: "duplicate_in_row"}
    pairs.append((*inverse, "reconciled_rejected"))
    assert set(filtered_pairs(pairs, text, lookups).values()) == {"inverse_pair_in_row"}


def test_unattested_recommended_pair_withholds_and_cannot_bypass_receipt_gate(source):
    source["rows"][0]["text"] = "SYNTHETIC wrong unknown."
    with sqlite3.connect(source["db"]) as db:
        db.execute("UPDATE style_guide SET text=? WHERE id=1", (source["rows"][0]["text"],))
    write_receipt(source)
    ctx, obj = context(source), component_for("C6b")
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        records, report = gate(ctx, obj, "C6b").run(cs)
        assert len(records) == 1
        assert report["accounting"]["C6b"]["reasons"] == {"agreed": 1, "recommended_unattested": 1}
        unit = next(u for u in RECEIPTS.records.values() if u["reason"] == "recommended_unattested")
        assert RECEIPTS.lookups[unit["id"]]["recommended"][0]["citations"] == []
        unit["reason"] = "agreed"
        with pytest.raises(BuildError, match="adjudication_direction"):
            RECEIPTS.row("C6b", "id=" + unit["id"])


def test_all_filter_fixtures_reject_actual_forced_candidates(source):
    source["rows"][1]["text"] = "SYNTHETIC wrong right. wrong right."
    source["rows"] += [
        {**source["rows"][0], "id": 3, "text": "SYNTHETIC long wrong long right."},
        {**source["rows"][0], "id": 4, "text": "SYNTHETIC wrong unknown."},
    ]
    with sqlite3.connect(source["db"]) as db:
        db.executemany(
            "INSERT OR REPLACE INTO style_guide VALUES (:id,:word,:text,:source,:page,:section)", source["rows"]
        )

    def select(receipts):
        for receipt in receipts.values():
            row = receipt["rows"][0]
            pair = row["pairs"][0]
            row["pairs"].append({"rejected": pair["recommended"], "recommended": pair["rejected"]})
            text = source["rows"][1]["text"]
            receipt["rows"][1]["pairs"] = [
                pair_for(source["rows"][1], "wrong", "right"),
                {
                    role: {"start": text.rindex(word), "end": text.rindex(word) + len(word)}
                    for role, word in (("rejected", "wrong"), ("recommended", "right"))
                },
            ]
            receipt["rows"][2]["pairs"] = [
                pair_for(source["rows"][2], "long wrong", "long right"),
                pair_for(source["rows"][2], "wrong", "right"),
            ]

    write_receipt(source, select)
    ctx, obj = context(source), component_for("C6b", count=4)
    with ctx.reader:
        cs = list(obj.iter_candidates(ctx))
        g = gate(ctx, obj, "C6b")
        records, report = g.run(cs)
        assert len(records) == 2
        assert report["accounting"]["C6b"]["reasons"] == {
            "agreed": 2,
            "inverse_pair_in_row": 2,
            "duplicate_in_row": 1,
            "subsumed_span": 1,
            "recommended_unattested": 1,
        }
        fixtures = list(obj.mutation_fixtures(ctx, cs, g))
        assert len(fixtures) == 5
        for fixture in fixtures:
            with pytest.raises(BuildError, match=fixture.expected_code):
                fixture.check()
        restored = g.run(cs)[1]
        assert restored["accounting"] == report["accounting"]
        assert restored["metrics"] == report["metrics"]
