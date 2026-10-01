"""English structural oracles; expectations never use production identity helpers."""

import copy
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.atlas import word_card_foundation as foundation

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs/sources/permissions-register.yaml"
BASIS = "sha256 canonical UTF-8 JSON of entire literal selected row, not whole database"


def sha(value):
    literal = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(literal).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def capture(source, table, raw, key=None, **extra):
    key = key or {"id": raw["id"]}
    locator = ("atlas0:enrichment:" + key["slug"] + "/" + key["section"] if table == "enrichment"
               else f'{source}:{table}:id:{raw["id"]}')
    return dict(source_id=source, table=table, row_key=key, locator=locator, raw_row=raw,
                snapshot_id="selected-row@sha256:" + sha(raw), content_sha256=sha(raw),
                content_fingerprint_basis=BASIS, source_content_sha256=raw.get("content_sha256"), **extra)


@pytest.fixture
def pilot(tmp_path):
    paths = {name: tmp_path / (name + ".db") for name in ("sources", "atlas", "vesum")}
    records, units = [], []
    with sqlite3.connect(paths["sources"]) as db:
        db.execute("CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, canonical_headword TEXT, "
                   "normalized_query TEXT, grammatical_label TEXT, homonym_index INTEGER, homonym_checked INTEGER, "
                   "status TEXT, parser_version TEXT, retrieved_at TEXT, content_sha256 TEXT, "
                   "raw_response_ref TEXT, register_position TEXT)")
        for number in range(150):
            raw = dict(id=number, canonical_headword="English", normalized_query="English", grammatical_label="structural",
                       homonym_index=number + 1, homonym_checked=1, status="ok", parser_version="fixture-v1",
                       retrieved_at="2026-01-01", content_sha256="a" * 64, raw_response_ref="sha256:" + "b" * 64,
                       register_position=str(number))
            db.execute("INSERT INTO ulif_dictua_entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", tuple(raw.values()))
            record = capture("ulif", "ulif_dictua_entries", raw)
            records.append(record)
            units.append(dict(unit_key=f"fixture:partition:{number}", anchor_locator=record["locator"],
                              source_record_keys=[record["locator"]], entry_type="lexeme_candidate",
                              atlas_slug=None if number >= 135 else "first" if number % 2 else "second",
                              counting_basis="English structural partition", supplementary_correspondence="unresolved",
                              cefr_basis="unknown", atlas_mapping_basis="explicit legacy inventory only"))
        payload = dict(rows=[["case", "form"], ["base", "English"]], raw_html="<table>literal</table>",
                       raw_response_ref="sha256:" + "b" * 64, sense_or_group_id="paradigm:1", source_order=0)
        raw = dict(id=1000, entry_id=0, kind="paradigm", payload_json=json.dumps(payload),
                   sense_or_group_id="paradigm:1", source_order=0)
        db.execute("CREATE TABLE ulif_dictua_sections (id INTEGER PRIMARY KEY, entry_id INTEGER, kind TEXT, "
                   "payload_json TEXT, sense_or_group_id TEXT, source_order INTEGER)")
        db.execute("INSERT INTO ulif_dictua_sections VALUES (?,?,?,?,?,?)", tuple(raw.values()))
        records.append(capture("ulif", "ulif_dictua_sections", raw))
    with sqlite3.connect(paths["atlas"]) as db:
        db.execute("CREATE TABLE articles (slug TEXT PRIMARY KEY, lemma TEXT, entry_type TEXT, pos TEXT, gloss TEXT)")
        db.executemany("INSERT INTO articles VALUES (?,?,?,?,?)", [
            ("first", "First", "lemma", "noun", "unused private gloss"),
            ("second", "Second", "multiword_term", "noun", "unused gloss")])
        db.execute("CREATE TABLE aliases (alias TEXT, kind TEXT, source TEXT, target_slug TEXT, visibility TEXT)")
        db.executemany("INSERT INTO aliases VALUES (?,?,?,?,?)", [
            ("shared", "canonical", "fixture", slug, "public") for slug in ("first", "second")])
        raw = dict(slug="first", section="stress", payload_json='{"form":"English","source":"ukrainian-word-stress"}',
                   source="ukrainian-word-stress", phase="fixture", filled_at="2026-01-01")
        db.execute("CREATE TABLE enrichment (slug TEXT, section TEXT, payload_json TEXT, source TEXT, "
                   "phase TEXT, filled_at TEXT)")
        db.execute("INSERT INTO enrichment VALUES (?,?,?,?,?,?)", tuple(raw.values()))
        records.append(capture("ukrainian_word_stress", "enrichment", raw, {"slug": "first", "section": "stress"},
                               database="atlas", lineage_status="unknown", lineage_basis="registered unknown lineage"))
    with sqlite3.connect(paths["vesum"]) as db:
        db.execute("CREATE TABLE forms_all (entry_id INTEGER, lemma TEXT, pos TEXT, tags TEXT)")
        db.execute("INSERT INTO forms_all VALUES (1,'First','noun','noun:inanim:m:v_naz')")
    units[0]["source_record_keys"] += [r["locator"] for r in records[-2:]]
    candidate = dict(schema_version="atlas-pilot-selection-candidate.v2", source_records=records, units=units,
                     denominator={"units": 150, "source_records": 152, "atlas_articles": 2},
                     source_register_sha256=hashlib.sha256(REGISTER.read_bytes()).hexdigest())
    selection, report, receipt = [tmp_path / x for x in ("source-candidate.json", "review.result",
                                                       "source-admission-receipt.json")]
    report.write_text("Independent English structural fixture admission: APPROVE\n")
    def admit():
        save(selection, candidate)
        save(receipt, dict(admission="APPROVE", candidate_sha256=hashlib.sha256(selection.read_bytes()).hexdigest(),
                           review_report_path=str(report), review_report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),
                           review_family="google", author_seat_distinct=True, denominator=candidate["denominator"]))
    admit()
    manifest, registry = tmp_path / "pilot.json", tmp_path / "registry.json"
    freeze = ["freeze", "--selection", str(selection), "--source-register", str(REGISTER), "--rules-version",
              "rules-v1-draft", "--normaliser-version", "norm-v1", "--output", str(manifest)]
    for name, path in paths.items():
        freeze += ["--" + name + "-db", str(path)]
    def operation(name, *extra):
        return foundation.main(freeze + list(extra) if name == "freeze" else
                               [name, "--manifest", str(manifest), "--registry", str(registry), *extra])
    return dict(operation=operation, candidate=candidate, paths=paths, manifest=manifest, registry=registry,
                admit=admit, receipt=receipt, report=report, root=tmp_path, freeze=freeze, selection=selection)


def prepared(pilot):
    assert pilot["operation"]("freeze") == 0
    assert pilot["operation"]("allocate") == 0
    assert pilot["operation"]("verify") == 0
    return json.loads(pilot["manifest"].read_bytes()), json.loads(pilot["registry"].read_bytes())


def test_freeze_allocation_alias_oracles_replay_and_conservation(pilot):
    before = {k: p.read_bytes() for k, p in pilot["paths"].items()}
    manifest, registry = prepared(pilot)
    assert manifest["counts"] == dict(units=150, source_records=152, atlas_articles=2, legacy_alias_rows=2)
    assert len(registry["events"]) == 154 and len(registry["source_records"]) == 152
    assert registry["entries"][0]["key_at_creation"] == {
        "spelling": "First", "pos": "noun", "source_keys": [{"source_id": "atlas0", "key": "atlas0:slug:first"}]}
    assert "gloss" not in manifest["legacy_articles"][0]["metadata"]
    assert len(manifest["legacy_articles"][0]["aliases"]) == 1
    assert registry["source_records"][0]["aliases"][0]["key"] == "ulif:record:English#English#structural"
    assert registry["source_records"][0]["aliases"][1]["key"] == "ulif:content:" + "a" * 64
    assert registry["source_records"][0]["aliases"][2]["key"] == "ulif:register:0"
    # Literal bytes are authored here, independently of the production tuple extractor.
    stress = b'{"form":"English","source":"ukrainian-word-stress"}'
    assert registry["source_records"][-1]["aliases"][0]["key"] == (
        "ukrainian_word_stress:record:stress:v1:sha256:" + hashlib.sha256(stress).hexdigest())
    parent = {"canonical_headword": "English", "content_sha256": "a" * 64, "grammatical_label": "structural",
              "homonym_index": 1, "normalized_query": "English"}
    payload = {"rows": [["case", "form"], ["base", "English"]], "raw_html": "<table>literal</table>",
               "raw_response_ref": "sha256:" + "b" * 64, "sense_or_group_id": "paradigm:1", "source_order": 0}
    assert registry["source_records"][-2]["aliases"][0]["key"] == (
        "ulif:record:paradigm:v1:sha256:" + sha({"parent": parent, "kind": "paradigm", "payload": payload}))
    empty_parent = copy.deepcopy(manifest["selection"]["source_records"])
    empty_parent[0]["raw_row"].update(canonical_headword="", grammatical_label="")
    parent.update(canonical_headword="", grammatical_label="")
    assert foundation.intrinsic(empty_parent[-2], empty_parent)[1] == (
        "ulif:record:paradigm:v1:sha256:" + sha({"parent": parent, "kind": "paradigm", "payload": payload}))
    empty_parent[0]["raw_row"]["content_sha256"] = None
    with pytest.raises(foundation.Refusal, match="Invalid paradigm parent"):
        foundation.intrinsic(empty_parent[-2], empty_parent)
    original = [p.read_bytes() for p in (pilot["manifest"], pilot["registry"])]
    assert pilot["operation"]("freeze") == pilot["operation"]("allocate") == 0
    assert original == [p.read_bytes() for p in (pilot["manifest"], pilot["registry"])]
    fresh = pilot["root"] / "fresh-manifest.json"
    command = [sys.executable, "-m", "scripts.atlas.word_card_foundation", *pilot["freeze"]]
    command[command.index("--output") + 1] = str(fresh)
    result = subprocess.run(command, cwd=ROOT, capture_output=True, check=False, timeout=60)
    assert result.returncode == 0 and fresh.read_bytes() == original[0], result.stderr
    assert {k: p.read_bytes() for k, p in pilot["paths"].items()} == before


@pytest.mark.parametrize("fault,reason", [
    ("bytes", "Changed selected bytes"), ("duplicate", "Duplicate selected rows"),
    ("registration", "Unregistered source"), ("reference", "Missing source reference"),
    ("counts", "Pilot denominator drift"), ("live_row", "Selected literal row mismatch"),
    ("report", "Admission report fingerprint mismatch"), ("authority", "Require independent source admission"),
    ("output_collision", "Output must be separate"), ("tuple_duplicate", "Duplicate intrinsic tuple")])
def test_admitted_freeze_faults_discriminate(pilot, fault, reason, capsys):
    assert pilot["operation"]("freeze") == 0  # Same valid admission and all unrelated gates pass.
    pilot["manifest"].unlink()
    c = pilot["candidate"]
    if fault == "bytes":
        c["source_records"][0]["raw_row"]["status"] = "changed"
    if fault == "duplicate":
        c["source_records"].append(c["source_records"][0])
    if fault == "registration":
        c["source_records"][0]["source_id"] = "unregistered"
    if fault == "reference":
        c["units"][0]["anchor_locator"] = "missing"
    if fault == "counts":
        c["denominator"]["units"] = 149
    if fault == "tuple_duplicate":
        record = copy.deepcopy(c["source_records"][-1])
        record["raw_row"]["slug"] = "second"
        record = capture("ukrainian_word_stress", "enrichment", record["raw_row"],
                         {"slug": "second", "section": "stress"}, database="atlas",
                         lineage_status="unknown", lineage_basis="registered unknown lineage")
        c["source_records"].append(record)
        c["units"][0]["source_record_keys"].append(record["locator"])
        c["denominator"]["source_records"] += 1
    pilot["admit"]()
    if fault == "live_row":
        with sqlite3.connect(pilot["paths"]["sources"]) as db:
            db.execute("UPDATE ulif_dictua_entries SET status='changed' WHERE id=0")
    if fault == "report":
        pilot["report"].write_text("changed")
    if fault == "authority":
        receipt = json.loads(pilot["receipt"].read_bytes())
        receipt["author_seat_distinct"] = "claimed"
        save(pilot["receipt"], receipt)
    if fault == "output_collision":
        pilot["freeze"][pilot["freeze"].index("--output") + 1] = str(pilot["paths"]["atlas"])
    assert pilot["operation"]("freeze") == 1
    assert reason in capsys.readouterr().err and not pilot["manifest"].exists()


@pytest.mark.parametrize("fault", ["card_swap", "source_swap", "kind", "build", "evidence", "aliases",
                                  "partial", "history", "cycle", "key_shape"])
def test_mint_binding_refusals(pilot, fault, capsys):
    _manifest, registry = prepared(pilot)
    if fault in {"card_swap", "source_swap"}:
        inventory, field = (registry["entries"], "card_id") if fault == "card_swap" else (
            registry["source_records"], "source_record_id")
        inventory[0][field], inventory[1][field] = inventory[1][field], inventory[0][field]
    if fault == "kind":
        registry["entries"][0]["card_kind"] = "proper_name"
    if fault == "build":
        registry["entries"][0]["created_in_build"] = "arbitrary"
    if fault == "evidence":
        registry["events"][0]["evidence"] = "unrelated"
    if fault == "aliases":
        registry["source_records"][0]["aliases"].pop()
    if fault == "partial":
        registry["source_records"].pop()
        registry["events"].pop()
    if fault == "history":
        registry["events"][0]["cards"] = ["wc_000000000000"]
    if fault == "cycle":
        registry["entries"][0].update(state="redirected", merged_into=registry["entries"][0]["card_id"])
    if fault == "key_shape":
        registry["entries"][0]["key_at_creation"]["source_keys"] = ["atlas0:slug:first"]
    save(pilot["registry"], registry)
    original = pilot["registry"].read_bytes()
    assert pilot["operation"]("verify") == pilot["operation"]("allocate") == 1
    assert pilot["registry"].read_bytes() == original
    reasons = {"card_swap": "Identity differs from original mint", "source_swap": "Identity differs from original mint",
               "kind": "Changed card mint provenance", "build": "Changed card mint provenance",
               "evidence": "Identity differs from original mint", "aliases": "Inconsistent source alias history",
               "partial": "Partial allocation", "history": "History references missing identity",
               "cycle": "Missing or cyclic identity reference", "key_shape": "Invalid card key_at_creation"}
    assert reasons[fault] in capsys.readouterr().err


def test_changed_snapshot_and_history_retention(pilot, capsys):
    _manifest, registry = prepared(pilot)
    registry["entries"][0]["state"] = "retired"
    registry["source_records"][0]["aliases"].append(
        dict(kind="query_headword_label", key="ulif:record:Older#Older#structural", snapshot_id="old"))
    registry["source_records"][0]["correspondence"].append(dict(snapshot_id="old", status="missing"))
    save(pilot["registry"], registry)
    before = pilot["registry"].read_bytes()
    assert pilot["operation"]("allocate") == pilot["operation"]("verify") == 0
    assert pilot["registry"].read_bytes() == before
    raw = pilot["candidate"]["source_records"][0]["raw_row"]
    raw["retrieved_at"] = "2026-02-01"
    pilot["candidate"]["source_records"][0] = capture("ulif", "ulif_dictua_entries", raw)
    with sqlite3.connect(pilot["paths"]["sources"]) as db:
        db.execute("UPDATE ulif_dictua_entries SET retrieved_at='2026-02-01' WHERE id=0")
    pilot["admit"]()
    assert pilot["operation"]("freeze") == 1
    assert "Immutable manifest" in capsys.readouterr().err
    pilot["manifest"].unlink()
    assert pilot["operation"]("freeze") == 0
    assert pilot["operation"]("allocate") == 1
    assert "requires correspondence" in capsys.readouterr().err
    assert pilot["registry"].read_bytes() == before


@pytest.mark.parametrize("reference", ["locator", "unit", "card", "source", "alias", "prose", "encoded"])
def test_schema_valid_isolation_events(pilot, reference, capsys):
    _manifest, registry = prepared(pilot)
    member = pilot["root"] / "membership.json"
    locator = pilot["candidate"]["source_records"][0]["locator"]
    unit = pilot["candidate"]["units"][0]
    card = registry["entries"][1]["card_id"]
    target = dict(locator=locator, unit=unit["unit_key"], card=card,
                  source=registry["source_records"][0]["source_record_id"], alias="atlas0:slug:second",
                  prose="A reviewed reference to (" + locator + ") in prose.",
                  encoded=json.dumps({"reference": locator}))[reference]
    registry["events"].append(dict(event_id="ie_9999", kind="retire", build_id="fixture-review", cards=[card],
                                   evidence=target, overlay_id="adjudication"))
    save(pilot["registry"], registry)
    assert pilot["operation"]("verify") == 0  # Schema, history and mint binding all pass.
    save(member, dict(heldout=[locator], replay=[]))
    assert pilot["operation"]("verify", "--heldout-manifest", str(member)) == 1
    assert "Held-out adjudicated mapping touches" in capsys.readouterr().err


@pytest.mark.parametrize("fault,reason", [(None, None), ("unknown", "Unresolved membership"),
    ("overlap", "must be disjoint"), ("closure", "overlap after conservative alias closure"),
    ("path", "Output must be separate")])
def test_membership_resolution_and_output_paths(pilot, fault, reason, capsys):
    prepared(pilot)
    member = pilot["root"] / "membership.json"
    locators = [r["locator"] for r in pilot["candidate"]["source_records"]]
    save(member, dict(heldout=["unknown" if fault == "unknown" else locators[0]],
                      replay=[locators[0] if fault == "overlap" else locators[1]] if fault in {"overlap", "closure"} else []))
    if fault == "path":
        pilot["freeze"][pilot["freeze"].index("--output") + 1] = str(member)
        assert pilot["operation"]("freeze", "--heldout-manifest", str(member)) == 1
    else:
        assert pilot["operation"]("verify", "--heldout-manifest", str(member)) == (0 if fault is None else 1)
    output = capsys.readouterr()
    assert reason in output.err if reason else '"heldout_isolation": "checked"' in output.out


@pytest.mark.parametrize("location", ["event", "receipt", "selection"])
def test_expectations_unconditionally_sealed(pilot, location, capsys):
    _manifest, registry = prepared(pilot)
    if location == "event":
        registry["events"].append(dict(event_id="ie_9999", kind="retire", build_id="fixture", cards=[],
                                       evidence='{"expected_mapping":{"fixture":"answer"}}'))
        save(pilot["registry"], registry)
        operation = "verify"
    else:
        if location == "receipt":
            receipt = json.loads(pilot["receipt"].read_bytes())
            receipt["adjudicated_answers"] = {"fixture": "answer"}
            save(pilot["receipt"], receipt)
        else:
            pilot["candidate"]["expected_answers"] = {"fixture": "answer"}
            pilot["admit"]()
        operation = "freeze"
    assert pilot["operation"](operation) == 1
    assert "expected answers are forbidden" in capsys.readouterr().err


@pytest.mark.parametrize("fault", ["list", "duplicate_json", "invalid_json", "deep", "surrogate", "nan",
                                  "unknown_field", "boolean", "selector", "yaml"])
def test_malformed_privacy_safe_refusal(pilot, fault, capsys, monkeypatch):
    manifest, _registry = prepared(pilot)
    if fault == "list":
        manifest = []
    if fault == "unknown_field":
        manifest["private_host"] = "private-fixture"
    if fault == "boolean":
        manifest["admission"]["author_seat_distinct"] = "claimed"
    if fault == "selector":
        manifest["selection"]["source_records"][0]["row_key"] = []
    if isinstance(manifest, dict):
        selection_bytes = (json.dumps(manifest["selection"], ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
        manifest["selection_file_sha256"] = hashlib.sha256(selection_bytes).hexdigest()
        manifest["admission"]["candidate_sha256"] = manifest["selection_file_sha256"]
        manifest["selection_content_sha256"] = sha(manifest["selection"])
        manifest["manifest_sha256"] = sha({k: v for k, v in manifest.items() if k != "manifest_sha256"})
    save(pilot["manifest"], manifest)
    raw = {"duplicate_json": '{"x":1,"x":2}', "invalid_json": "{", "deep": "[" * 2000 + "]" * 2000,
           "surrogate": '{"x":"\\ud800"}', "nan": '{"x":NaN}'}
    if fault in raw:
        pilot["manifest"].write_text(raw[fault])
    if fault == "yaml":
        register = pilot["root"] / "bad.yaml"
        register.write_text("[unclosed")
        monkeypatch.setattr(foundation, "REGISTER", register)
    assert pilot["operation"]("verify") == 1
    error = capsys.readouterr().err
    assert "REFUSED:" in error and "Traceback" not in error and "private-fixture" not in error


def test_atomic_failure_identifier_reuse_and_lock_location(pilot, monkeypatch):
    assert pilot["operation"]("freeze") == 0
    save(pilot["registry"], dict(schema_version="1", registry_version=1, entries=[], source_records=[], events=[]))
    before = pilot["registry"].read_bytes()
    def fail(*args):
        raise OSError("injected replace failure")
    with monkeypatch.context() as context:
        context.setattr("os.replace", fail)
        assert pilot["operation"]("allocate") == 1
    assert pilot["registry"].read_bytes() == before
    assert not list(pilot["root"].glob(".registry.json.*")) and not pilot["registry"].with_suffix(".lock").exists()
    monkeypatch.setattr(foundation.secrets, "choice", lambda alphabet: "0")
    assert pilot["operation"]("allocate") == 1 and pilot["registry"].read_bytes() == before


def test_wal_capture_and_mutation_refusal(pilot, monkeypatch, capsys):
    db = sqlite3.connect(pilot["paths"]["sources"])
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("UPDATE ulif_dictua_entries SET retrieved_at='2026-03-01' WHERE id=0")
    db.commit()
    raw = pilot["candidate"]["source_records"][0]["raw_row"]
    raw["retrieved_at"] = "2026-03-01"
    pilot["candidate"]["source_records"][0] = capture("ulif", "ulif_dictua_entries", raw)
    pilot["admit"]()
    assert pilot["operation"]("freeze") == 0
    manifest = json.loads(pilot["manifest"].read_bytes())
    assert manifest["database_wal_sha256"]["sources"] == hashlib.sha256(
        Path(str(pilot["paths"]["sources"]) + "-wal").read_bytes()).hexdigest()
    pilot["manifest"].unlink()
    original = foundation.fingerprints
    calls = 0
    def mutate(paths):
        nonlocal calls
        calls += 1
        if calls == 2:
            db.execute("UPDATE ulif_dictua_entries SET status='changed' WHERE id=1")
            db.commit()
        return original(paths)
    monkeypatch.setattr(foundation, "fingerprints", mutate)
    assert pilot["operation"]("freeze") == 1
    assert "Source file/WAL mutation" in capsys.readouterr().err and not pilot["manifest"].exists()
    db.close()


def test_committed_inputs_readonly_cli_guard():
    paths = [ROOT / "registry/atlas/pilot/pilot-v1.json", ROOT / "registry/atlas/identity/registry.json"]
    before = [p.read_bytes() for p in paths]
    result = subprocess.run([sys.executable, "-m", "scripts.atlas.word_card_foundation", "verify",
                             "--manifest", str(paths[0]), "--registry", str(paths[1])],
                            cwd=ROOT, capture_output=True, text=True, check=False, timeout=60)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["counts"] == dict(units=150, source_records=272, atlas_articles=114, legacy_alias_rows=140)
    registry = json.loads(paths[1].read_bytes())
    assert [len(registry[k]) for k in ("entries", "source_records", "events")] == [114, 272, 386]
    assert len(output["unresolved_card_mappings"]) == 22 and output["heldout_isolation"] == "unverified"
    assert before == [p.read_bytes() for p in paths]


def test_help_and_evaluation_refusal(pilot, capsys):
    prepared(pilot)
    assert pilot["operation"]("verify", "--for-evaluation") == 1
    assert "authenticated operator authority" in capsys.readouterr().err
    for command in ([], ["freeze"], ["allocate"], ["verify"]):
        with pytest.raises(SystemExit) as error:
            foundation.main([*command, "--help"])
        assert error.value.code == 0
    assert "Exit codes:" in capsys.readouterr().out


@pytest.mark.parametrize("fault,reason", [("duplicate_keys", "Duplicate JSON key"),
    ("extra", "Invalid object fields"), ("empty", "Invalid stress tuple"),
    ("parent", "exactly one admitted parent"), ("order_bool", "Invalid paradigm discriminator"),
    ("matrix", "Invalid paradigm matrix"), ("digest", "Invalid paradigm discriminator"),
    ("null", "Invalid paradigm discriminator")])
def test_tuple_faults_have_passing_controls(pilot, fault, reason, capsys):
    prepared(pilot)
    pilot["manifest"].unlink()
    records = pilot["candidate"]["source_records"]
    index = -1 if fault in {"duplicate_keys", "extra", "empty"} else -2
    record = records[index]
    raw = record["raw_row"]
    payload = json.loads(raw["payload_json"])
    if fault == "extra":
        payload["unknown"] = "fixture"
    if fault == "empty":
        payload["form"] = ""
    if fault == "parent":
        raw["entry_id"] = 9999
    if fault == "order_bool":
        payload["source_order"] = False
    if fault == "matrix":
        payload["rows"] = [["English"], ["English", "second"]]
    if fault in {"digest", "null"}:
        payload["raw_response_ref"] = "wrong" if fault == "digest" else None
    raw["payload_json"] = json.dumps(payload) if fault != "duplicate_keys" else '{"form":"a","form":"b"}'
    records[index] = capture(record["source_id"], record["table"], raw, record["row_key"],
                             **{k: record[k] for k in ("database", "lineage_status", "lineage_basis") if k in record})
    pilot["admit"]()
    assert pilot["operation"]("freeze") == 1
    error = capsys.readouterr().err
    assert reason in error if fault != "null" else "REFUSED:" in error
    assert not pilot["manifest"].exists()


def test_literal_tuple_variants_and_simulated_collision(pilot, monkeypatch, capsys):
    _manifest, registry = prepared(pilot)
    key = registry["source_records"][-1]["aliases"][0]["key"]
    pilot["manifest"].unlink()
    records = pilot["candidate"]["source_records"]
    raw = dict(records[-1]["raw_row"], slug="second", phase="renamed", filled_at="later")
    extra = dict(database="atlas", lineage_status="unknown", lineage_basis="registered unknown lineage")
    added = capture("ukrainian_word_stress", "enrichment", raw, {"slug": "second", "section": "stress"}, **extra)
    records.append(added)
    pilot["candidate"]["denominator"]["source_records"] += 1
    pilot["candidate"]["units"][0]["source_record_keys"].append(added["locator"])
    pilot["admit"]()
    assert pilot["operation"]("freeze") == 1  # Renamed locator/time never differentiates complete tuples.
    assert "Duplicate intrinsic tuple" in capsys.readouterr().err
    raw["payload_json"] = '{"form":"Englísh ","source":"ukrainian-word-stress"}'
    records[-1] = capture("ukrainian_word_stress", "enrichment", raw, added["row_key"], **extra)
    pilot["admit"]()
    with sqlite3.connect(pilot["paths"]["atlas"]) as db:
        db.execute("INSERT INTO enrichment VALUES (?,?,?,?,?,?)", tuple(raw.values()))
    original = foundation.digest
    with monkeypatch.context() as patch:
        patch.setattr(foundation, "digest", lambda v: key.rsplit(":", 1)[1] if isinstance(v, dict) and
                      set(v) == {"form", "source"} else original(v))
        assert pilot["operation"]("freeze") == 1
    assert "Duplicate intrinsic tuple" in capsys.readouterr().err
    assert pilot["operation"]("freeze") == 0
    pilot["registry"] = pilot["root"] / "fresh-registry.json"
    assert foundation.main(["allocate", "--manifest", str(pilot["manifest"]),
                            "--registry", str(pilot["registry"])]) == 0
    registry = json.loads(pilot["registry"].read_bytes())
    literal = '{"form":"Englísh ","source":"ukrainian-word-stress"}'.encode()
    assert registry["source_records"][-1]["aliases"][0]["key"] == (
        "ukrainian_word_stress:record:stress:v1:sha256:" + hashlib.sha256(literal).hexdigest())


@pytest.mark.parametrize("change", ["rename", "homonym", "html"])
def test_paradigm_parent_join_and_literal_changes(pilot, change):
    _manifest, registry = prepared(pilot)
    original_key = registry["source_records"][-2]["aliases"][0]["key"]
    records = pilot["candidate"]["source_records"]
    parent, section = records[0]["raw_row"], records[-2]["raw_row"]
    parent["id" if change == "rename" else "homonym_index"] = 2000 if change == "rename" else 2
    if change == "rename":
        section["entry_id"] = 2000
    if change == "html":
        parent["homonym_index"] = 1
        payload = json.loads(section["payload_json"])
        payload["raw_html"] += " "
        section["payload_json"] = json.dumps(payload)
    records[0] = capture("ulif", "ulif_dictua_entries", parent)
    records[-2] = capture("ulif", "ulif_dictua_sections", section)
    pilot["candidate"]["units"][0]["anchor_locator"] = records[0]["locator"]
    pilot["candidate"]["units"][0]["source_record_keys"][0] = records[0]["locator"]
    with sqlite3.connect(pilot["paths"]["sources"]) as db:
        db.execute("UPDATE ulif_dictua_entries SET id=?,homonym_index=? WHERE id=0",
                   (parent["id"], parent["homonym_index"]))
        db.execute("UPDATE ulif_dictua_sections SET entry_id=?,payload_json=? WHERE id=1000",
                   (section["entry_id"], section["payload_json"]))
    pilot["admit"]()
    pilot["manifest"].unlink()
    assert pilot["operation"]("freeze") == 0
    fresh = pilot["root"] / "fresh.json"
    assert foundation.main(["allocate", "--manifest", str(pilot["manifest"]), "--registry", str(fresh)]) == 0
    key = json.loads(fresh.read_bytes())["source_records"][-2]["aliases"][0]["key"]
    assert key == original_key if change == "rename" else key != original_key
