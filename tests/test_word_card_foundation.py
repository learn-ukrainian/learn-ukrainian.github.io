"""English structural oracles; expectations never use production identity helpers."""

import copy
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from contextlib import nullcontext
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
def pilot(tmp_path, monkeypatch):
    monkeypatch.setattr(foundation, "main_checkout_root", lambda root: tmp_path)  # Test locks stay in tmp_path.
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


def rehash(manifest, selection=True):
    """Recompute admitted fingerprints so that only the gate under test sees the change."""
    if selection:
        literal = (json.dumps(manifest["selection"], ensure_ascii=False, indent=2) + "\n").encode()
        manifest["selection_file_sha256"] = manifest["admission"]["candidate_sha256"] = hashlib.sha256(literal).hexdigest()
        manifest["selection_content_sha256"] = sha(manifest["selection"])
    manifest["manifest_sha256"] = sha({k: v for k, v in manifest.items() if k != "manifest_sha256"})


def prepared(pilot):
    assert pilot["operation"]("freeze") == 0
    assert pilot["operation"]("allocate") == 0
    assert pilot["operation"]("verify") == 0
    return json.loads(pilot["manifest"].read_bytes()), json.loads(pilot["registry"].read_bytes())


def test_freeze_allocation_alias_oracles_replay_and_conservation(pilot, capsys):
    before = {k: p.read_bytes() for k, p in pilot["paths"].items()}
    manifest, registry = prepared(pilot)
    reports = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [r["foreign_build_events"] for r in reports] == [None, 0, 0]  # freeze, allocate, verify
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
    ("output_collision", "Output must be separate"), ("tuple_duplicate", "Duplicate intrinsic tuple"),
    ("metadata", "Invalid row snapshot"), ("version", "Unsupported selection schema"),
    ("admission", "Missing source admission"), ("admission_counts", "Require independent source admission"),
    ("relative", "Source DB must be an existing absolute file"), ("pos", "Unresolved source-backed coarse POS")])
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
    if fault == "metadata":
        del c["source_records"][0]["snapshot_id"]
    if fault == "version":
        c["schema_version"] = "atlas-pilot-selection-candidate.v1"
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
    if fault in {"authority", "admission", "admission_counts"}:
        receipt = json.loads(pilot["receipt"].read_bytes())
        receipt.update({"authority": {"author_seat_distinct": "claimed"}, "admission": {"admission": "REJECT"},
                        "admission_counts": {"denominator": dict(c["denominator"], units=149)}}[fault])
        save(pilot["receipt"], receipt)
    if fault == "output_collision":
        pilot["freeze"][pilot["freeze"].index("--output") + 1] = str(pilot["paths"]["atlas"])
    if fault == "relative":
        pilot["freeze"][pilot["freeze"].index("--sources-db") + 1] = os.path.relpath(pilot["paths"]["sources"])
    if fault == "pos":  # A legacy noun lemma without VESUM backing is never given a default POS.
        with sqlite3.connect(pilot["paths"]["vesum"]) as db:
            db.execute("DELETE FROM forms_all")
    assert pilot["operation"]("freeze") == 1
    assert reason in capsys.readouterr().err and not pilot["manifest"].exists()


@pytest.mark.parametrize("fault,reason", [
    ("card_swap", "Identity differs from original mint"), ("source_swap", "Identity differs from original mint"),
    ("kind", "Changed card mint provenance"), ("build", "Changed card mint provenance"),
    ("evidence", "Identity differs from original mint"), ("aliases", "Inconsistent source alias history"),
    ("partial", "Partial allocation"), ("history", "History references missing identity"),
    ("cycle", "Missing or cyclic identity reference"), ("key_shape", "Invalid card key_at_creation"),
    ("reused", "Reused identity"), ("duplicate_event", "Duplicate history event"),
    ("schema", "Invalid word-card-identity-registry-v1.schema.json"),
    ("creation_key", "Legacy creation evidence mismatch"), ("double_allocation", "Source row allocated twice"),
    ("excess", "Allocation history exceeds frozen pilot inventory"),
    ("correspondence", "Frozen-snapshot alias differs from its bound row"),
    ("alias_extra", "Frozen-snapshot alias differs from its bound row"),
    ("alias_altered", "Frozen-snapshot alias differs from its bound row"),
    ("alias_misplaced", "Frozen-snapshot alias differs from its bound row")])
def test_mint_binding_refusals(pilot, fault, reason, capsys):
    _manifest, registry = prepared(pilot)
    first, second = registry["source_records"][:2]
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
        first["aliases"].pop()
    if fault == "partial":
        registry["source_records"].pop()
        registry["events"].pop()
    if fault == "history":
        registry["events"][0]["cards"] = ["wc_000000000000"]
    if fault == "cycle":
        registry["entries"][0].update(state="redirected", merged_into=registry["entries"][0]["card_id"])
    if fault == "key_shape":
        registry["entries"][0]["key_at_creation"]["source_keys"] = ["atlas0:slug:first"]
    if fault == "reused":
        registry["entries"][1]["card_id"] = registry["entries"][0]["card_id"]
    if fault == "duplicate_event":
        registry["events"].append(registry["events"][0])
    if fault == "schema":
        del registry["registry_version"]
    if fault == "creation_key":
        registry["entries"][0]["key_at_creation"]["spelling"] = "Changed"
    if fault == "double_allocation":  # A second identity claims the same row under the same snapshot.
        second.update(aliases=first["aliases"], correspondence=first["correspondence"])
    if fault == "excess":  # A sense minted under this build is outside the frozen pilot inventory.
        registry["entries"][0]["senses"].append(dict(sense_id="ws_000000000000", order=1))
        registry["events"].append(dict(event_id="ie_9999", kind="sense_mint", build_id=registry["events"][0]["build_id"],
                                       to=["ws_000000000000"], evidence="fixture sense"))
    if fault == "correspondence":  # The record is no longer bound, yet keeps aliases under a frozen snapshot.
        first["correspondence"][0]["locator"] = "missing"
    if fault == "alias_extra":  # Another row's register alias under this record's own initial snapshot.
        first["aliases"].append(dict(second["aliases"][2], snapshot_id=first["aliases"][0]["snapshot_id"]))
    if fault == "alias_altered":
        first["aliases"].append(dict(first["aliases"][0], key=first["aliases"][0]["key"] + " "))
    if fault == "alias_misplaced":  # A genuine alias, but on a record bound to a different row.
        second["aliases"].append(first["aliases"][0])
    save(pilot["registry"], registry)
    original = pilot["registry"].read_bytes()
    assert pilot["operation"]("verify") == pilot["operation"]("allocate") == 1
    assert pilot["registry"].read_bytes() == original
    assert capsys.readouterr().err.count("REFUSED: " + reason) == 2


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


ADJUDICATIONS = ("split", "merge", "retire", "sense_split", "sense_merge")
SENSES = ("owned", "foreign", "minted", "paradigm", "mwe", "candidate")  # Variants naming one sense or held row.


def retained(registry, locator, reference):  # Foreign history: a sense on card 'second'; unrelated card, sense, row.
    card, owned, foreign, row = "wc_" + "f" * 12, "ws_" + "a" * 12, "ws_" + "b" * 12, "sr_" + "c" * 12
    creation = dict(paradigm=dict(paradigm_key=locator), mwe=dict(mwe_key=locator + "|english form")).get(reference, {})
    registry["entries"][1]["senses"].append(dict(sense_id=owned, order=1))
    registry["entries"].append(dict(card_id=card, card_kind="mwe", state="active", senses=[dict(sense_id=foreign, order=1)],
                                    created_in_build="foreign", key_at_creation=dict(spelling="Other", pos="noun", **creation)))
    held = dict(snapshot_id="s2", status="held", hold="conflict", candidates=[locator if reference == "candidate" else "s2:x"])
    registry["source_records"].append(dict(source_record_id=row, source_id="ulif", correspondence=[held],
                                           aliases=[dict(kind="content", key="ulif:content:s2", snapshot_id="s2")]))
    mints = [("mint", "cards", card), ("sense_mint", "to", owned), ("source_record_mint", "to", row), ("sense_mint", "to", foreign)]
    registry["events"] += [dict(event_id=f"ie_{9000 + n}", kind=kind, build_id="foreign", **{field: [target]},
                                evidence=locator if (reference, target) == ("minted", foreign) else f"Retained note {n}.")
                           for n, (kind, field, target) in enumerate(mints)]
    return owned, foreign, {"from": [dict(owned=owned, candidate=row).get(reference, foreign)]} if reference in SENSES else {}


@pytest.mark.parametrize("kind,reference", [(kind, ref) for kind in ADJUDICATIONS for ref in (None, "unit")] +
                         [("sense_split", ref) for ref in ("card", "locator", "source", "alias", "prose", "encoded")] +
                         [(kind, ref) for kind in ("sense_split", "sense_merge") for ref in SENSES])
def test_schema_valid_isolation_events(pilot, kind, reference, capsys):
    _manifest, registry = prepared(pilot)
    member, locator = pilot["root"] / "membership.json", pilot["candidate"]["source_records"][0]["locator"]
    _owned, foreign, endpoint = retained(registry, locator, reference)
    # Each variant reaches the held-out boundary through one gate only: no overlay_id, cards stay empty except
    # in the card variant, and only sense variants name one id. The escaped colon hides the locator from prose.
    evidence = dict(locator=locator, unit=pilot["candidate"]["units"][0]["unit_key"], alias="atlas0:slug:second",
                    source=registry["source_records"][0]["source_record_id"], prose=f"A reviewed note on ({locator}).",
                    encoded='{"reference":"' + locator.replace(":", "\\u003a") + '"}').get(reference, "Unrelated note.")
    registry["events"].append(dict(event_id="ie_9999", kind=kind, build_id="fixture-review", evidence=evidence,
                                   cards=[registry["entries"][1]["card_id"]] if reference == "card" else [], **endpoint))
    save(pilot["registry"], registry)
    assert pilot["operation"]("verify") == 0  # Schema, history and mint binding pass; four retained mints are foreign.
    assert '"foreign_build_events": 5, "heldout_isolation": "unverified"' in capsys.readouterr().out  # Sorted keys.
    save(member, dict(heldout=[locator], replay=[foreign] if reference == "foreign" else []))  # Replay-only sense.
    before, refused = pilot["registry"].read_bytes(), int(reference not in {None, "foreign"})
    assert pilot["operation"]("verify", "--heldout-manifest", str(member)) == refused
    assert pilot["operation"]("allocate", "--heldout-manifest", str(member)) == refused
    assert pilot["registry"].read_bytes() == before
    assert capsys.readouterr().err.count("REFUSED: Held-out adjudicated mapping touches") == 2 * refused


@pytest.mark.parametrize("fault,reason", [(None, None), ("self_hash", "Changed manifest bytes/content"),
    ("rules", "Unapproved rules or normaliser version"), ("normaliser", "Unapproved rules or normaliser version"),
    ("register", "Register fingerprint mismatch"), ("content", "Selection content fingerprint mismatch"),
    ("file", "Admitted selection bytes changed"), ("version", "Unsupported selection schema"),
    ("capture", "Changed selected bytes"), ("metadata", "Changed legacy metadata projection")])
def test_frozen_manifest_faults_discriminate(pilot, fault, reason, capsys):
    manifest, _registry = prepared(pilot)
    capsys.readouterr()
    selection, before = manifest["selection"], pilot["registry"].read_bytes()
    changes = {"rules": (manifest, "rules_version", "rules-v2"), "normaliser": (manifest, "normaliser_version", "norm-v2"),
               "register": (selection, "source_register_sha256", "0" * 64),
               "version": (selection, "schema_version", "atlas-pilot-selection-candidate.v1"),
               "capture": (selection["source_records"][0]["raw_row"], "status", "changed"),
               "metadata": (manifest["legacy_articles"][0]["metadata"], "lemma", "Changed"),
               "content": (manifest, "selection_content_sha256", "0" * 64),
               "file": (manifest, "selection_file_sha256", "0" * 64), "self_hash": (manifest, "manifest_sha256", "0" * 64)}
    if fault in changes:
        target, key, value = changes[fault]
        target[key] = value
    if fault != "self_hash":  # Every other gate is reached with a consistent self-hash.
        rehash(manifest, selection=fault not in {"content", "file"})
    save(pilot["manifest"], manifest)
    assert pilot["operation"]("verify") == pilot["operation"]("allocate") == (0 if fault is None else 1)
    assert pilot["registry"].read_bytes() == before
    output = capsys.readouterr()
    assert output.err.count("REFUSED: " + reason) == 2 if fault else output.err == ""


@pytest.mark.parametrize("fault,reason", [(None, None), ("unknown", "Unresolved membership"),
    ("overlap", "must be disjoint"), ("closure", "overlap after conservative alias closure"),
    ("path", "Output must be separate"), ("sense", "overlap after conservative alias closure"),  # Sense vs owner key.
    ("prose", "Unresolved membership")])  # A retained mint's plain evidence is never a membership key.
def test_membership_resolution_and_output_paths(pilot, fault, reason, capsys):
    _manifest, registry = prepared(pilot)
    member = pilot["root"] / "membership.json"
    locators = [r["locator"] for r in pilot["candidate"]["source_records"]]
    owned = retained(registry, locators[0], fault)[0]
    save(pilot["registry"], registry)
    replay = {"overlap": [locators[0]], "closure": [locators[1]], "sense": ["atlas0:slug:second"]}.get(fault, [])
    heldout = {"unknown": "unknown", "sense": owned, "prose": "Retained note 0."}.get(fault, locators[0])
    save(member, dict(heldout=[heldout], replay=replay))
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
        rehash(manifest)
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
    assert len(list((pilot["root"] / "batch_state/locks/word-card-foundation").glob("*.lock"))) == 2
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


def test_committed_inputs_readonly_cli_guard(tmp_path, capsys):
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
    assert output["foreign_build_events"] == 0
    member, held = tmp_path / "membership.json", json.loads(paths[0].read_bytes())["selection"]["source_records"][0]
    save(member, dict(heldout=[held["locator"]], replay=[]))  # No committed owner carries an adjudication marker.
    assert foundation.main(["verify", "--manifest", str(paths[0]), "--registry", str(paths[1]),
                            "--heldout-manifest", str(member)]) == 0 and '"heldout_isolation": "checked"' in capsys.readouterr().out
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


@pytest.mark.parametrize("word,valid", [("<ID>1</ID>|English  phrase {{</fras>}} ", True), ("   ", False), (7, False)])
def test_phrase_dictionary_literal_word_key(pilot, word, valid, capsys):
    rows = [dict(id=n, word=word, definition="English gloss", text="<p>literal</p>", source="fixture") for n in (7, 8)]
    with sqlite3.connect(pilot["paths"]["sources"]) as db:
        db.execute("CREATE TABLE frazeolohichnyi (id INTEGER PRIMARY KEY, word, definition TEXT, text TEXT, source TEXT)")
        db.executemany("INSERT INTO frazeolohichnyi VALUES (?,?,?,?,?)", [tuple(r.values()) for r in rows])
    records = [capture("frazeolohichnyi", "frazeolohichnyi", raw) for raw in rows]
    pilot["candidate"]["source_records"] += records
    pilot["candidate"]["units"][0]["source_record_keys"] += [r["locator"] for r in records]
    pilot["candidate"]["denominator"]["source_records"] += 2
    pilot["admit"]()
    if not valid:
        assert pilot["operation"]("freeze") == 1
        assert "REFUSED: Invalid phrase-dictionary word" in capsys.readouterr().err
        assert not pilot["manifest"].exists() and not pilot["registry"].exists()
        return
    _manifest, registry = prepared(pilot)
    replay = pilot["registry"].read_bytes()
    assert pilot["operation"]("allocate") == 0 and pilot["registry"].read_bytes() == replay
    phrases = registry["source_records"][-2:]
    assert len({r["source_record_id"] for r in phrases}) == 2  # The repeated weak key is conserved, not merged.
    # Hand-written key: the untrimmed literal column, markup residue and doubled space included.
    key = "frazeolohichnyi:record:<ID>1</ID>|English  phrase {{</fras>}} "
    assert [r["aliases"] for r in phrases] == [[dict(kind="table_row", key=key, snapshot_id=r["snapshot_id"])]
                                               for r in records]


NOTE = "Archived bulk batch remark."  # Plain prose reused by every unrelated provenance field below.
ENCODINGS = {  # name: (frozen text citing held-out key loc:h, independent decoder or None, cited?); last four: boundaries.
    "literal": ("loc:h", None, True), "delimited": ("Imported via (loc:h).", None, True),
    "value": (r'{"ref":"loc\u003ah"}', lambda t: json.loads(t)["ref"], True),  # Escapes hide the raw key.
    "key": (r'{"loc\u003ah":1}', lambda t: next(iter(json.loads(t))), True),
    "nested": (r'["{\"loc\\u003ah\":1}"]', lambda t: next(iter(json.loads(json.loads(t)[0]))), True),
    "overlap": ("Per ledger evidence ledger.", None, True), "plain": (NOTE, None, False),  # Bare alias in overlaps.
    "longer": ("Imported (loc:h0) and (xloc:h).", None, False), "unregistered": ("Imported via (loc:z).", None, False),
    "case": ("LOC:H", None, False), "fragment": (r'Imported {"ref":"loc\u003ah"} later.', None, False),
    "normalised": ("loc\uff1ah", None, False)}
OWNERS = dict(mint="wc_f", sense_mint="ws_f", sense_owner="wc_f", source_record_mint="sr_f", note="sr_f",
              matched_by="sr_f", hold="sr_f", match_note="wc_f", adjudication="ws_f", embedded="sr_e")  # Endpoint.


@pytest.mark.parametrize("field,encoding", [(field, encoding) for field in OWNERS for encoding in ENCODINGS])
def test_provenance_links_only_through_cited_known_keys(tmp_path, field, encoding):
    (text, decode, cited), owner, member = ENCODINGS[encoding], OWNERS[field], tmp_path / "membership.json"
    assert decode is None or (decode(text) == "loc:h" and "loc:h" not in text)  # Valid JSON hiding the key.
    assert not any(key in NOTE for key in ("sr_", "wc_", "ws_", "k:", "loc:h", "evidence", "ledger"))
    prose = dict.fromkeys(OWNERS, NOTE) | {field.replace("sense_owner", "sense_mint"): text}
    inputs = [dict(source_record_id="sr_h", aliases=[dict(key="loc:h"), dict(key="evidence")]),  # Held out.
              dict(card_id="wc_f", senses=[dict(sense_id="ws_f")],
                   key_at_creation=dict(source_keys=[dict(key="k:f", match_note=prose["match_note"])])),
              dict(source_record_id="sr_f", aliases=[dict(key="ledger evidence", note=prose["note"]),
                   dict(key="evidence ledger")], correspondence=[dict(matched_by=prose["matched_by"], hold=prose["hold"])]),
              *(dict(kind=kind, evidence=prose[kind], **{"cards" if kind == "mint" else "to": [OWNERS[kind]]})
                for kind in ("mint", "sense_mint", "source_record_mint")),
              dict(kind="source_record_mint", to=["sr_h"], evidence=NOTE),  # The held-out row reuses the note.
              # Row sr_e and its object-valued note exist only inside a decoded attribute string.
              dict(spelling=json.dumps(dict(source_record_id="sr_e", aliases=[dict(key="k:e", note={prose["embedded"]: 1})])))]
    save(member, dict(heldout=["sr_h"], replay=[owner]))  # Replay direction, before any adjudication exists.
    with pytest.raises(foundation.Refusal, match="overlap after") if cited and field != "adjudication" else nullcontext():
        assert foundation.isolation(inputs, member) == "checked"
    save(member, dict(heldout=["sr_h"], replay=[]))  # Endpoint-only adjudication; native field names never count.
    event = dict(event_id="ie_1", kind="sense_split", evidence=prose["adjudication"], **{"from": [owner]})
    inputs.append(event if field != "embedded" else dict(spelling=json.dumps(event)))  # Its decoded keys do count.
    with pytest.raises(foundation.Refusal, match="adjudicated mapping touches") if cited or field == "embedded" else nullcontext():
        assert foundation.isolation(inputs, member) == "checked"


MARK = json.dumps({"kind": "identity"})  # Decoded marker; may sit in any string field of an owner.
REVIEW = dict(review=dict(settled_by="loc:u"))  # Nested native marker citing only the unrelated chain's key.
POSITIONS = dict(  # family: (native nested marker, decoded marker); decoded ones sit in non-prose strings too.
    source=(lambda o: o["correspondence"][0].update(REVIEW["review"]), lambda o: o["aliases"][0].update(note=MARK)),
    card=(lambda o: o["key_at_creation"].update(REVIEW), lambda o: o["key_at_creation"].update(spelling=MARK)),
    mint=(lambda o: o.update(overlay_id="ov_1"), lambda o: o.update(evidence=MARK)),
    unit=(lambda o: o.update(REVIEW), lambda o: o.update(cefr_basis=MARK)),
    record=(lambda o: o["raw_row"].update(mapping="ov_1"), lambda o: o["raw_row"].update(definition=MARK)),
    legacy=(lambda o: o["metadata"].update(split_into=["wc_x"]), lambda o: o["metadata"].update(pos=MARK)))
EXTRA = ("split_fields", "embedded", "from_join", "pos_join", "unowned", "wrapper")  # Last two: unowned markers.


def owner_chain(s):  # Only the unit cites loc:<s>; the zero-alias legacy owner never cites any closure key.
    return dict(record=dict(source_id="frazeolohichnyi", table="frazeolohichnyi", locator=f"loc:{s}2", snapshot_id="s",
                            source_content_sha256=None, raw_row=dict(word=f"word {s}", definition="English")),
                unit=dict(unit_key=f"unit:{s}", anchor_locator=f"loc:{s}", source_record_keys=[f"loc:{s}", f"loc:{s}2"],
                          atlas_slug=s, counting_basis=json.dumps({"see": f"loc:{s}"})),  # Plain decoded reference.
                legacy=dict(metadata=dict(slug=s, lemma="English", pos="noun"), aliases=[], pos_review=None),
                source=dict(source_record_id=f"sr_{s}", aliases=[dict(key=f"frazeolohichnyi:record:word {s}", note=NOTE)],
                            correspondence=[dict(snapshot_id="old", status="missing")]),
                card=dict(card_id=f"wc_{s}", state="suppressed", senses=[dict(sense_id=f"ws_{s}", state="unsplit")],
                          key_at_creation=dict(spelling="English", source_keys=[dict(key=f"atlas0:slug:{s}")])),
                mint=dict(kind="sense_mint", to=[f"ws_{s}"], evidence=NOTE))


@pytest.mark.parametrize("case,side", [(c, s) for c in [*(f"{f}:{m}" for f in POSITIONS for m in ("native", "decoded")),
                                                        *EXTRA] for s in "hu"])
def test_function_level_marked_owner_isolation(tmp_path, case, side):
    """Function-level isolation() diagnostic only: never CLI admission or source certification."""
    assert json.loads(MARK) == {"kind": "identity"} and "loc:" not in MARK  # Genuinely decodes; cites nothing.
    chains, member = {s: owner_chain(s) for s in "hu"}, tmp_path / "membership.json"
    inputs = [dict(source_records=[c["record"] for c in chains.values()], units=[c["unit"] for c in chains.values()]),
              *(o for c in chains.values() for k, o in c.items() if k not in {"record", "unit"})]
    save(member, dict(heldout=["loc:h"], replay=["loc:u"]))  # The unrelated chain stays outside the closure.
    assert foundation.isolation(inputs, member) == "checked"  # Plain notes, decoded plain reference, lifecycle states.
    family, _, form = case.partition(":")
    if form:
        POSITIONS[family][form == "decoded"](chains[side][family])
    if case == "split_fields":  # Marker and literal reference in different fields of one otherwise unrelated owner.
        chains["u"]["card"].update(card_kind=f"loc:{side}", key_at_creation=dict(source_keys=[], **REVIEW))
    if case == "embedded":  # An unlinked decoded owner in a non-prose card string; its marker marks the card too.
        chains[side]["card"]["key_at_creation"]["spelling"] = json.dumps(dict(source_record_id="sr_e", aliases=[dict(
            key="k:e")], correspondence=[dict(settled_by="ov_1")]))
    if case in {"from_join", "pos_join"}:  # Only the D2 join links this marked card into a chain.
        join = dict(kind="sense_mint", to=["ws_n"], evidence=NOTE, **{"from": [f"ws_{side}"]}) if case == "from_join" \
            else dict(metadata=dict(slug="n"), aliases=[], pos_review=dict(anchor_locator=f"loc:{side}"))
        inputs += [join, dict(card_id="wc_n", senses=[dict(sense_id="ws_n")],
                              key_at_creation=dict(source_keys=[dict(key="atlas0:slug:n")], **REVIEW))]
    if case in {"unowned", "wrapper"}:  # A bare marker stays accepted; a wrapper's context cites its sibling reference.
        inputs.append(dict(settled_by="ov_1") if case == "unowned" else dict(decision=REVIEW, reference=f"loc:{side}"))
    reason = "a membership key" if case == "mint:native" else "a marked owner"  # A flat mint marks itself.
    reason = "its enclosing context" if case == "wrapper" else reason
    held = side == "h" and case != "unowned"
    with pytest.raises(foundation.Refusal, match="adjudicated mapping touches " + reason) if held else nullcontext():
        assert foundation.isolation(inputs, member) == "checked"


@pytest.mark.parametrize("case,held", [(c, h) for c in ("settled_by", "note", "raw_row") for h in (True, False)])
def test_cli_marked_owner_refused_before_write(pilot, case, held, capsys):
    member, index = pilot["root"] / "membership.json", 2 if held else 140  # Unit 2 shares the held legacy closure.
    save(member, dict(heldout=[pilot["candidate"]["source_records"][0]["locator"]], replay=[]))
    if case == "raw_row":  # A literal column named like a marker marks its own row; captured and admitted unchanged.
        records, row = pilot["candidate"]["source_records"], dict(normalized_query="Other", content_sha256="c" * 64)
        records[index] = capture("ulif", "ulif_dictua_entries", dict(records[index]["raw_row"], **row))  # Own aliases.
        records.append(capture("frazeolohichnyi", "frazeolohichnyi", dict(id=7, word="English phrase", mapping="ov_1")))
        with sqlite3.connect(pilot["paths"]["sources"]) as db:
            db.execute("UPDATE ulif_dictua_entries SET normalized_query=?, content_sha256=? WHERE id=?", (*row.values(), index))
            db.execute("CREATE TABLE frazeolohichnyi (id INTEGER PRIMARY KEY, word TEXT, mapping TEXT)")
            db.execute("INSERT INTO frazeolohichnyi VALUES (7, 'English phrase', 'ov_1')")
        pilot["candidate"]["units"][index]["source_record_keys"].append("frazeolohichnyi:frazeolohichnyi:id:7")
        pilot["candidate"]["denominator"]["source_records"] += 1
        pilot["admit"]()
        assert pilot["operation"]("freeze", "--heldout-manifest", str(member)) == int(held)
        assert pilot["manifest"].exists() is not held and capsys.readouterr().err.count("a marked owner") == int(held)
        return
    _manifest, registry = prepared(pilot)
    retained(registry, pilot["candidate"]["source_records"][0]["locator"], None)  # Adds one unrelated foreign row.
    marker = dict(settled_by="ov_1") if case == "settled_by" else {}  # Historical correspondence or decoded note.
    record = registry["source_records"][index if held else -1]
    record["aliases"].append(dict(kind="content", key="ulif:content:old", snapshot_id="old",
                                  **({"note": json.dumps({"kind": "merge"})} if case == "note" else {})))
    record["correspondence"].append(dict(snapshot_id="old", status="missing", **marker))
    save(pilot["registry"], registry)
    before = pilot["registry"].read_bytes()
    assert pilot["operation"]("verify", "--heldout-manifest", str(member)) == int(held)
    assert pilot["operation"]("allocate", "--heldout-manifest", str(member)) == int(held)
    assert pilot["registry"].read_bytes() == before
    assert capsys.readouterr().err.count("REFUSED: Held-out adjudicated mapping touches a marked owner") == 2 * held


HELD, OTHER = "ulif:ulif_dictua_entries:id:140", "ulif:ulif_dictua_entries:id:0"  # Isolated held row; replay row.
CONTEXTS = {  # case: (marker beside subject s in candidate c or receipt fields r, outcome when s is held).
    "admission_wrapper": (lambda c, r, s: r.update(review_model=json.dumps(dict(d=dict(kind="identity"), ref=s))), True),
    "selection_wrapper": (lambda c, r, s: c.update(decision=dict(review=dict(settled_by="ov_1"), reference=s)), True),
    "deep": (lambda c, r, s: c.update(envelope=dict(reference=s, a=dict(b=dict(c=dict(kind="merge"))))), True),
    "double_encoded": (lambda c, r, s: c.update(envelope=dict(reference=s, a=json.dumps(MARK))), True),
    "siblings": (lambda c, r, s: c.update(one=dict(kind="variant"), two=dict(reference=s)), True),
    "admission_marker": (lambda c, r, s: (r.update(review_model=MARK), c.update(reference=s)), True),
    "decoy_array": (lambda c, r, s: c.update(legacy_articles=[dict(settled_by="ov_1"), dict(reference=s)]), True),
    "decoy_owner": (lambda c, r, s: c.update(decoy=[dict(settled_by="ov_1"), dict(source_record_id=s)]), True),
    "receipt_decoy": (lambda c, r, s: r.update(source_records=[dict(kind="merge"), dict(reference=s)]), True),
    "own_key": (lambda c, r, s: c.update(decision={"settled_by": "ov_1", s: 1}), True),
    "named_closed": (lambda c, r, s: c.update(admission={"kind": "merge", s: 1}), True),
    "unit_metadata": (lambda c, r, s: c["units"][0].update(metadata={"settled_by": "ov_1", s: 1}), True),
    "root_key": (lambda c, r, s: c.update({s: dict(kind="merge")}), True),
    "receipt_own_key": (lambda c, r, s: r.update(decision={"settled_by": "ov_1", s: 1}), True),
    "closed_values": (lambda c, r, s: r.update(review_model=MARK, review_harness=s), True),
    "pos_review": (lambda c, r, s: None, True),  # Set after freeze: an untyped value under a closed legacy item.
    "plain": (lambda c, r, s: c.update(reference=s), False), "key_only": (lambda c, r, s: c.update(decision={s: 1}), False),
    "marker_only": (lambda c, r, s: c.update(decision=dict(settled_by="ov_1")), False),
    "unit_marker": (lambda c, r, s: c["units"][0].update(review=dict(settled_by="ov_1")), False),
    "row_marker": (lambda c, r, s: c["source_records"][0].update(review=dict(kind="merge")), False),
    "receipt_marker": (lambda c, r, s: r.update(settled_by="ov_1"), False),
    "root_marker": (lambda c, r, s: c.update(settled_by="ov_1"), "a membership key")}  # Own arrays: earlier check.


@pytest.mark.parametrize("case,subject", [(c, s) for c, (_, held) in CONTEXTS.items()
                                          for s in ((HELD, OTHER, "loc:unbound") if held is True else (HELD,))])
def test_cli_marker_context_refused_before_write(pilot, case, subject, capsys):
    records, member, fields = pilot["candidate"]["source_records"], pilot["root"] / "membership.json", {}
    records[140] = capture("ulif", "ulif_dictua_entries", dict(records[140]["raw_row"], normalized_query="Other",
                                                                content_sha256="c" * 64))  # Own aliases: unshared.
    with sqlite3.connect(pilot["paths"]["sources"]) as db:
        db.execute("UPDATE ulif_dictua_entries SET normalized_query='Other', content_sha256=? WHERE id=140", ("c" * 64,))
    CONTEXTS[case][0](pilot["candidate"], fields, subject)
    pilot["admit"]()
    save(pilot["receipt"], json.loads(pilot["receipt"].read_bytes()) | fields)
    save(member, dict(heldout=[HELD], replay=[OTHER]))
    held = CONTEXTS[case][1] if subject == HELD else False
    frozen, later = bool(held) and case != "pos_review", bool(held) and not case.startswith("receipt")
    assert pilot["operation"]("freeze", "--heldout-manifest", str(member)) == frozen
    assert pilot["manifest"].exists() is not frozen and pilot["operation"]("freeze") == 0  # Unverified freeze.
    if case == "pos_review":
        manifest = json.loads(pilot["manifest"].read_bytes())
        manifest["legacy_articles"][0]["pos_review"] = {"kind": "merge", subject: 1}
        rehash(manifest, selection=False)
        save(pilot["manifest"], manifest)
    assert pilot["operation"]("allocate", "--heldout-manifest", str(member)) == later  # Fresh; receipt: freeze only.
    assert pilot["registry"].exists() is not later and pilot["operation"]("allocate") == 0
    before = pilot["registry"].read_bytes()
    assert pilot["operation"]("allocate", "--heldout-manifest", str(member)) == later
    assert pilot["operation"]("verify", "--heldout-manifest", str(member)) == later
    reason = held if isinstance(held, str) else "its enclosing context"
    assert capsys.readouterr().err.count("REFUSED: Held-out adjudicated mapping touches " + reason) == frozen + 3 * later
    assert pilot["registry"].read_bytes() == before


@pytest.mark.parametrize("case,held", [("admission", False), ("registry_event", False), ("author_field", True),
                                       ("event_shaped", True)])  # Held weak aliases equal field names.
def test_cli_only_validator_fixed_field_sets_mask_keys(pilot, case, held, capsys):
    member = pilot["root"] / "membership.json"
    with sqlite3.connect(pilot["paths"]["atlas"]) as db:
        db.executemany("INSERT INTO aliases VALUES (?,'canonical','fixture','first','public')", [("counts",), ("evidence",)])
    pilot["candidate"].update({"author_field": dict(decision=dict(settled_by="ov_1", counts=1)),
                               "event_shaped": dict(decoy=dict(event_id="ie_1", kind="merge", build_id="x", evidence=NOTE))
                               }.get(case, {}))
    pilot["admit"]()
    save(pilot["receipt"], json.loads(pilot["receipt"].read_bytes()) | ({"review_model": MARK} if case == "admission" else {}))
    save(member, dict(heldout=["evidence"], replay=[]))
    assert pilot["operation"]("freeze", "--heldout-manifest", str(member)) == held
    assert pilot["manifest"].exists() is not held and pilot["operation"]("freeze") == pilot["operation"]("allocate") == 0
    registry = json.loads(pilot["registry"].read_bytes())
    if case == "registry_event":
        registry["events"].append(dict(event_id="ie_9999", kind="merge", build_id="fixture-review", evidence=NOTE, cards=[]))
    save(pilot["registry"], registry)
    before = pilot["registry"].read_bytes()
    assert pilot["operation"]("verify", "--heldout-manifest", str(member)) == held
    assert capsys.readouterr().err.count("its enclosing context") == 2 * held
    assert pilot["registry"].read_bytes() == before


PARENT, CHILD = "ulif:ulif_dictua_entries:id:76793", "ulif:ulif_dictua_sections:id:96933"  # The one real admitted pair.
OWNER, OVERLAP = "a marked owner's closure or text", "Heldout/replay overlap after conservative alias closure"
B03 = {  # case: (child moved from unit 141 to source-only unit 35, marked row, marker cites parent, held, replay,
         # refusal reason or None)
    "baseline": (False, None, False, PARENT, None, None), "original_unit": (False, CHILD, False, PARENT, None, OWNER),
    "moved": (True, CHILD, False, PARENT, None, OWNER), "moved_plain": (True, None, False, PARENT, None, None),
    "moved_direct": (True, CHILD, True, PARENT, None, OWNER), "reverse": (True, PARENT, False, CHILD, None, OWNER),
    "split_parent": (True, None, False, PARENT, CHILD, OVERLAP),
    "split_child": (True, None, False, CHILD, PARENT, OVERLAP)}


@pytest.mark.parametrize("case", B03)
def test_b03_real_paradigm_parent_is_a_closure_dependency(tmp_path, case, capsys):
    """Regression only: real rows conserved; admission fingerprints and build ids are rebound, never re-admitted."""
    moved, marked, direct, held, replay, reason = B03[case]
    committed = [ROOT / "registry/atlas/pilot/pilot-v1.json", ROOT / "registry/atlas/identity/registry.json"]
    before = [p.read_bytes() for p in committed]
    manifest = json.loads(before[0])
    units = manifest["selection"]["units"]
    assert units[141]["anchor_locator"] == PARENT and CHILD in units[141]["source_record_keys"]
    assert units[35]["atlas_slug"] is None and CHILD not in units[35]["source_record_keys"]
    if moved:
        units[141]["source_record_keys"].remove(CHILD)
        units[35]["source_record_keys"].append(CHILD)
    for record in manifest["selection"]["source_records"]:
        if record["locator"] == marked:
            record["review"] = dict(decision=dict(kind="merge"), **({"reference": PARENT} if direct else {}))
    build = "pilot@sha256:" + manifest["manifest_sha256"]
    rehash(manifest)
    paths = [tmp_path / name for name in ("pilot.json", "registry.json", "membership.json")]
    paths[0].write_text(json.dumps(manifest, ensure_ascii=False))  # Insertion order keeps the admitted selection bytes.
    paths[1].write_text(before[1].decode().replace(build, "pilot@sha256:" + manifest["manifest_sha256"]))
    save(paths[2], dict(heldout=[held], replay=[replay] if replay else []))
    assert foundation.main(["verify", "--manifest", str(paths[0]), "--registry", str(paths[1]),
                            "--heldout-manifest", str(paths[2])]) == (reason is not None)
    output = capsys.readouterr()
    assert reason in output.err if reason else '"heldout_isolation": "checked"' in output.out
    assert before == [p.read_bytes() for p in committed]


@pytest.mark.parametrize("op", ["freeze", "fresh", "replay", "verify"])
@pytest.mark.parametrize("marked", [150, -1])  # The moved paradigm child; a non-paradigm row with an equal entry_id.
def test_moved_paradigm_child_refused_in_every_operation(pilot, op, marked, capsys):
    records, units, member = pilot["candidate"]["source_records"], pilot["candidate"]["units"], pilot["root"] / "m.json"
    with sqlite3.connect(pilot["paths"]["sources"]) as db:
        for number, query in ((140, "Other"), (141, "Third")):  # Own aliases: parent and destination unit unshared.
            records[number] = capture("ulif", "ulif_dictua_entries", dict(records[number]["raw_row"],
                                      normalized_query=query, content_sha256=sha(query)))
            db.execute("UPDATE ulif_dictua_entries SET normalized_query=?, content_sha256=? WHERE id=?",
                       (query, sha(query), number))
        db.execute("UPDATE ulif_dictua_sections SET entry_id=140 WHERE id=1000")
        db.execute("CREATE TABLE frazeolohichnyi (id INTEGER PRIMARY KEY, word TEXT, entry_id INTEGER)")
        db.execute("INSERT INTO frazeolohichnyi VALUES (7, 'English phrase', 140)")
    records[150] = capture("ulif", "ulif_dictua_sections", dict(records[150]["raw_row"], entry_id=140))
    records.append(capture("frazeolohichnyi", "frazeolohichnyi", dict(id=7, word="English phrase", entry_id=140)))
    units[0]["source_record_keys"].remove(records[150]["locator"])
    units[141]["source_record_keys"].append(records[150]["locator"])  # Moved off its parent's unit 140.
    units[142]["source_record_keys"].append(records[-1]["locator"])
    pilot["candidate"]["denominator"]["source_records"] += 1
    records[marked]["review"] = dict(decision=dict(kind="merge"))
    pilot["admit"]()
    save(member, dict(heldout=["ulif:ulif_dictua_entries:id:140"], replay=[]))
    held = marked == 150
    if op == "freeze":
        assert pilot["operation"]("freeze", "--heldout-manifest", str(member)) == held
        assert pilot["manifest"].exists() is not held
    else:
        assert pilot["operation"]("freeze") == 0 and (op == "fresh" or pilot["operation"]("allocate") == 0)
        before = pilot["registry"].read_bytes() if op != "fresh" else None
        assert pilot["operation"]("verify" if op == "verify" else "allocate", "--heldout-manifest", str(member)) == held
        assert pilot["registry"].exists() is not (held and op == "fresh")
        assert op == "fresh" or pilot["registry"].read_bytes() == before
    assert capsys.readouterr().err.count("REFUSED: Held-out adjudicated mapping touches a marked owner") == held
