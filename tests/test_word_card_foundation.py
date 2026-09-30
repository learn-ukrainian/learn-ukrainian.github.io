"""Independent English structural fixtures exercising the public operations."""

import hashlib
import json
import os
import sqlite3

import pytest

from scripts.atlas import word_card_foundation as foundation


def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


@pytest.fixture
def pilot(tmp_path):
    paths = {name: tmp_path / (name + ".db") for name in ("sources", "atlas", "vesum")}
    records, units = [], []
    with sqlite3.connect(paths["sources"]) as db:
        db.execute("CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, canonical_headword TEXT, normalized_query TEXT, grammatical_label TEXT, homonym_checked INTEGER, status TEXT, parser_version TEXT, retrieved_at TEXT, content_sha256 TEXT, raw_response_ref TEXT, register_position TEXT)")
        for number in range(150):
            raw = dict(id=number, canonical_headword="English", normalized_query="English", grammatical_label="structural", homonym_checked=1, status="ok", parser_version="fixture-v1", retrieved_at="2026-01-01", content_sha256="a" * 64, raw_response_ref="sha256:" + "b" * 64, register_position=str(number))
            db.execute("INSERT INTO ulif_dictua_entries VALUES (?,?,?,?,?,?,?,?,?,?,?)", tuple(raw.values()))
            locator = f"ulif:ulif_dictua_entries:id:{number}"
            records.append(dict(source_id="ulif", table="ulif_dictua_entries", row_key={"id": number}, locator=locator, raw_row=raw, snapshot_id="selected-row@sha256:" + sha(raw), content_sha256=sha(raw), content_fingerprint_basis="sha256 canonical UTF-8 JSON of entire literal selected row, not whole database", source_content_sha256="a" * 64))
            units.append(dict(unit_key=f"fixture:partition:{number}", anchor_locator=locator, source_record_keys=[locator], entry_type="mwe_candidate" if number >= 135 else "lexeme_candidate", atlas_slug=None if number >= 135 else "first" if number % 2 else "second", counting_basis="independent English structural partition", supplementary_correspondence="unresolved", cefr_basis="unknown", atlas_mapping_basis="explicit legacy inventory only"))
    with sqlite3.connect(paths["atlas"]) as db:
        db.execute("CREATE TABLE articles (slug TEXT PRIMARY KEY, entry_type TEXT)")
        db.executemany("INSERT INTO articles VALUES (?,?)", [("first", "lemma"), ("second", "multiword_term"), ("outside", "lemma")])
        db.execute("CREATE TABLE aliases (alias TEXT, kind TEXT, source TEXT, target_slug TEXT, visibility TEXT)")
        db.executemany("INSERT INTO aliases VALUES (?,?,?,?,?)", [("shared", "canonical", "fixture", slug, "public") for slug in ("first", "second")])
    sqlite3.connect(paths["vesum"]).close()
    candidate = dict(schema_version="atlas-pilot-selection-candidate.v2", source_records=records, units=units, denominator={"units": 150, "source_records": 150, "atlas_articles": 2}, source_register_sha256=hashlib.sha256(foundation.REGISTER.read_bytes()).hexdigest())
    selection = tmp_path / "source-candidate.json"
    report = tmp_path / "review.result"
    report.write_text("Independent fixture source review: APPROVE\n")
    receipt = tmp_path / "source-admission-receipt.json"
    def admit():
        save(selection, candidate)
        save(receipt, dict(admission="APPROVE", candidate_sha256=hashlib.sha256(selection.read_bytes()).hexdigest(), review_report_path=str(report), review_report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(), review_family="google", author_seat_distinct=True, denominator=candidate["denominator"]))
    admit()
    manifest, registry = tmp_path / "pilot.json", tmp_path / "registry.json"
    freeze = ["freeze", "--selection", str(selection), "--source-register", str(foundation.REGISTER), "--rules-version", "rules-v1-draft", "--normaliser-version", "norm-v1", "--output", str(manifest)]
    for name, path in paths.items():
        freeze += ["--" + name + "-db", str(path)]
    def operation(name, *extra):
        return foundation.main(freeze + list(extra) if name == "freeze" else [name, "--manifest", str(manifest), "--registry", str(registry), *extra])
    return dict(operation=operation, candidate=candidate, paths=paths, manifest=manifest, registry=registry, admit=admit, receipt=receipt, report=report, root=tmp_path, freeze=freeze)


def prepared(pilot):
    assert pilot["operation"]("freeze") == 0
    assert pilot["operation"]("allocate") == 0
    return json.loads(pilot["manifest"].read_bytes()), json.loads(pilot["registry"].read_bytes())


def test_freeze_allocation_collision_replay_and_conservation(pilot, capsys):
    before = {k: p.read_bytes() for k, p in pilot["paths"].items()}
    manifest, registry = prepared(pilot)
    assert manifest["counts"] == {"units": 150, "source_records": 150, "atlas_articles": 2, "legacy_alias_rows": 2}
    assert len(registry["entries"]) == 2 and len(registry["source_records"]) == 150 and len(registry["events"]) == 152
    assert {e["card_kind"] for e in registry["entries"]} == {"lexeme", "mwe"}
    assert all(e["senses"] == [] for e in registry["entries"])
    assert all(e["key_at_creation"]["aliases"][0]["alias"] == "shared" for e in registry["entries"])
    assert len({r["source_record_id"] for r in registry["source_records"]}) == 150
    assert len({r["aliases"][-1]["key"] for r in registry["source_records"]}) == 1
    original = pilot["registry"].read_bytes()
    assert pilot["operation"]("allocate") == pilot["operation"]("verify") == 0
    assert pilot["registry"].read_bytes() == original
    assert {k: p.read_bytes() for k, p in pilot["paths"].items()} == before
    assert '"heldout_isolation": "unverified"' in capsys.readouterr().out


@pytest.mark.parametrize("fault", ["bytes", "metadata", "duplicate", "registration", "counts", "reference", "version", "report", "admission", "admission_counts", "relative", "mutation", "live_row", "output_collision"])
def test_freeze_refuses_before_write(pilot, fault, monkeypatch, capsys):
    record = pilot["candidate"]["source_records"][0]
    if fault == "bytes":
        record["raw_row"]["status"] = "changed"
    if fault == "metadata":
        del record["snapshot_id"]
    if fault == "duplicate":
        pilot["candidate"]["source_records"].append(record)
    if fault == "registration":
        record["source_id"] = "unregistered"
    if fault == "counts":
        pilot["candidate"]["denominator"]["units"] = 149
    if fault == "reference":
        pilot["candidate"]["units"][0]["anchor_locator"] = "missing"
    if fault == "version":
        pilot["candidate"]["schema_version"] = "unknown"
    pilot["admit"]()
    if fault == "report":
        pilot["report"].write_text("changed")
    if fault in {"admission", "admission_counts"}:
        receipt = json.loads(pilot["receipt"].read_bytes())
        receipt["admission"] = "REJECT" if fault == "admission" else "APPROVE"
        receipt["denominator"]["units"] = 149
        save(pilot["receipt"], receipt)
    if fault == "relative":
        pilot["freeze"][pilot["freeze"].index("--sources-db") + 1] = os.path.relpath(pilot["paths"]["sources"])
    if fault == "live_row":
        with sqlite3.connect(pilot["paths"]["sources"]) as db:
            db.execute("UPDATE ulif_dictua_entries SET status='changed' WHERE id=0")
    if fault == "output_collision":
        pilot["freeze"][pilot["freeze"].index("--output") + 1] = str(pilot["paths"]["atlas"])
    if fault == "mutation":
        real = foundation.file_digest
        calls = 0
        def changing(path):
            nonlocal calls
            calls += path == pilot["paths"]["atlas"]
            return "f" * 64 if path == pilot["paths"]["atlas"] and calls > 1 else real(path)
        monkeypatch.setattr(foundation, "file_digest", changing)
    assert pilot["operation"]("freeze") == 1
    assert not pilot["manifest"].exists()
    assert "REFUSED:" in capsys.readouterr().err


@pytest.mark.parametrize("fault", ["reused", "history", "partial", "aliases", "correspondence", "cycle", "duplicate_event", "schema", "changed_manifest", "changed_capture"])
def test_verify_refuses_inconsistent_state(pilot, fault):
    manifest, registry = prepared(pilot)
    if fault == "reused":
        registry["entries"][1]["card_id"] = registry["entries"][0]["card_id"]
    if fault == "history":
        registry["events"][0]["cards"] = ["wc_000000000000"]
    if fault == "partial":
        registry["source_records"].pop()
        registry["events"].pop()
    if fault == "aliases":
        registry["source_records"][0]["aliases"].pop()
    if fault == "correspondence":
        registry["source_records"][0]["correspondence"][0]["locator"] = "missing"
    if fault == "cycle":
        registry["entries"][0].update(state="redirected", merged_into=registry["entries"][0]["card_id"])
    if fault == "duplicate_event":
        registry["events"].append(registry["events"][0])
    if fault == "schema":
        del registry["registry_version"]
    if fault == "changed_manifest":
        manifest["rules_version"] = "changed"
    if fault == "changed_capture":
        manifest["selection"]["source_records"][0]["raw_row"]["status"] = "changed"
        manifest["selection_content_sha256"] = sha(manifest["selection"])
        manifest["manifest_sha256"] = sha({k: v for k, v in manifest.items() if k != "manifest_sha256"})
    save(pilot["registry"], registry)
    save(pilot["manifest"], manifest)
    assert pilot["operation"]("verify") == 1
    assert pilot["operation"]("allocate") == 1


def test_partial_write_and_random_reuse_are_atomic(pilot, monkeypatch):
    assert pilot["operation"]("freeze") == 0
    baseline = dict(schema_version="1", registry_version=1, entries=[], source_records=[], events=[])
    save(pilot["registry"], baseline)
    before = pilot["registry"].read_bytes()
    def fail(*args):
        raise OSError("injected replace failure")
    with monkeypatch.context() as context:
        context.setattr("os.replace", fail)
        assert pilot["operation"]("allocate") == 1
    assert pilot["registry"].read_bytes() == before and not list(pilot["root"].glob(".registry.json.*"))
    monkeypatch.setattr(foundation.secrets, "choice", lambda alphabet: "0")
    assert pilot["operation"]("allocate") == 1
    assert pilot["registry"].read_bytes() == before


def test_retained_history_replay(pilot):
    _manifest, registry = prepared(pilot)
    registry["entries"][0]["state"] = "retired"
    registry["source_records"][0]["aliases"].append({"kind": "table_row", "key": "historical:key", "snapshot_id": "historical"})
    registry["source_records"][0]["correspondence"].append({"snapshot_id": "historical", "status": "missing"})
    save(pilot["registry"], registry)
    before = pilot["registry"].read_bytes()
    assert pilot["operation"]("allocate") == pilot["operation"]("verify") == 0
    assert pilot["registry"].read_bytes() == before


@pytest.mark.parametrize("fault", [None, "direct", "indirect", "encoded", "receipt", "overlap"])
def test_all_input_heldout_boundary(pilot, fault, capsys):
    _manifest, registry = prepared(pilot)
    locator = pilot["candidate"]["source_records"][0]["locator"]
    member = pilot["root"] / "membership.json"
    save(member, {"heldout": [locator], "replay": [locator] if fault == "overlap" else []})
    if fault == "direct":
        registry["events"][0].update(kind="merge", evidence=locator, overlay_id="adjudication")
    if fault == "indirect":
        registry["events"][-1].update(overlay_id="adjudication", to=[registry["source_records"][0]["source_record_id"]])
    if fault == "encoded":
        registry["events"][0]["evidence"] = json.dumps({"expected_mapping": {locator: "card"}})
    if fault == "receipt":
        receipt = json.loads(pilot["receipt"].read_bytes())
        receipt["expected_mapping"] = {locator: "card"}
        save(pilot["receipt"], receipt)
        pilot["manifest"].unlink()
        assert pilot["operation"]("freeze", "--heldout-manifest", str(member)) == 1
        assert not pilot["manifest"].exists()
        return
    save(pilot["registry"], registry)
    assert pilot["operation"]("verify", "--heldout-manifest", str(member)) == (0 if fault is None else 1)
    if fault is None:
        assert '"heldout_isolation": "checked"' in capsys.readouterr().out
        assert pilot["operation"]("verify", "--heldout-manifest", str(member), "--for-evaluation") == 1


def test_duplicate_json_invalid_input_and_help(pilot, capsys):
    pilot["manifest"].write_text('{"schema_version":1,"schema_version":2}')
    assert pilot["operation"]("verify") == 1
    pilot["manifest"].write_text("{")
    assert pilot["operation"]("verify") == 1
    for command in ([], ["freeze"], ["allocate"], ["verify"]):
        with pytest.raises(SystemExit) as error:
            foundation.main([*command, "--help"])
        assert error.value.code == 0
    assert "Exit codes:" in capsys.readouterr().out
