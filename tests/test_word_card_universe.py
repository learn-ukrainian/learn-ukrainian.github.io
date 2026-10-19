"""Source-free Phase 6 mechanics. No test certifies a real lexical universe."""

from __future__ import annotations

import copy
import hashlib
import sqlite3
from functools import cache
from pathlib import Path

import pytest
from jsonschema import validators

from scripts.atlas import word_card_assembly as assembly
from scripts.atlas import word_card_certification as cert
from scripts.atlas import word_card_golden_set as gold
from scripts.atlas import word_card_universe as universe
from tests.test_word_card_golden_set import write
from tests.word_card_certification_fixtures import CertificationFixture, certification_fixture


@pytest.fixture(scope="module")
def validation_cache():
    # Schema validation is pure. Reuse successful checks only for identical values and schemas.
    def cached(validate):
        accepted = set()

        def validate_once(value, schema, label):
            key = (gold.canonical(value), gold.canonical(schema))
            if key not in accepted:
                validate(value, schema, label)
                accepted.add(key)

        return validate_once

    unique_items = gold.VALIDATOR.VALIDATORS["uniqueItems"]

    def json_key(value):
        if isinstance(value, dict):
            return ("object", frozenset((key, json_key(item)) for key, item in value.items()))
        if isinstance(value, list):
            return ("array", tuple(map(json_key, value)))
        # JSON Schema distinguishes booleans from numbers, but equates 1 and 1.0.
        return ("boolean" if isinstance(value, bool) else "scalar", value)

    def unique_once(validator, enabled, instance, schema):
        # Hash nested JSON values instead of the library's quadratic pairwise comparisons.
        if (enabled and validator.is_type(instance, "array")
                and len({json_key(item) for item in instance}) != len(instance)):
            yield from unique_items(validator, enabled, instance, schema)

    account = gold.accounting.account
    accounting_cache = {}

    def account_once(paths, *, atlas_manifest=None):
        key = (tuple(sorted(paths.items())), atlas_manifest)
        if key in accounting_cache:
            files, result = accounting_cache[key]
            if all(path.is_file() and path.read_bytes() == raw for path, raw in files.items()):
                return copy.deepcopy(result)
        result = account(paths, atlas_manifest=atlas_manifest)
        # The accounting receipt enumerates every transitive source dependency.
        files = {path: path.read_bytes() for path in result[1]["_input_paths"]}
        accounting_cache[key] = files, copy.deepcopy(result)
        return result

    evaluate = cert.evaluate_certification
    evaluations = {}

    def evaluate_once(spec_path, spec_sha256, evaluation_path, evaluation_sha256):
        # These synthetic packets keep all certification dependencies under these roots.
        roots = (cert.PROJECT_ROOT, spec_path.parent)
        files = tuple((path, path.read_bytes()) for path in sorted({
            path for root in roots for path in root.rglob("*") if path.is_file()
        }))
        key = (spec_path, spec_sha256, evaluation_path, evaluation_sha256, files)
        if key not in evaluations:
            evaluations[key] = evaluate(spec_path, spec_sha256, evaluation_path, evaluation_sha256)
        return copy.deepcopy(evaluations[key])

    with pytest.MonkeyPatch.context() as patch:
        # This module never changes repository topology; keep all per-path containment checks.
        patch.setattr(assembly, "_checkouts", cache(assembly._checkouts))
        for module, name in ((gold, "VALIDATOR"), (gold.accounting, "EvidenceValidator")):
            patch.setattr(module, name, validators.extend(getattr(module, name), {"uniqueItems": unique_once}))
        patch.setattr(gold, "validate", cached(gold.validate))
        patch.setattr(gold.accounting, "_validate", cached(gold.accounting._validate))
        patch.setattr(gold.accounting, "account", account_once)
        patch.setattr(cert, "evaluate_certification", evaluate_once)
        yield


class UniverseFixture:
    def __init__(self, root, authority):
        root.mkdir()
        self.root = root
        (root / "phase5").mkdir()
        self.phase5 = CertificationFixture(root / "phase5", authority)
        self.phase5.approve()
        self.card = self.phase5.card
        self.evidence = self.phase5.gold.opaque
        self.spec_path = root / "universe.json"
        self.inventory_path = root / "inventory.json"
        self.plan_path = root / "plan.json"
        self.resource_path = root / "resources.json"
        self.proof_path = root / "independent.json"
        self.checkpoint = root / "checkpoint.sqlite3"
        self.spec = {
            "schema_version": "word-card-universe-spec.v1",
            "author": {"id": "author", "family": "author-family"},
            "source_spec": {"path": str(self.phase5.gold.spec_path), "sha256": self.phase5.gold.spec_sha},
            "certifications": [self.phase5.receipt()],
            "limits": {"batch_units": 7, "max_card_bytes": 100_000, "min_free_bytes": 1},
            "runtime_sha256": universe.runtime_fingerprint(),
        }
        self.units = {}
        for source_range in self.phase5.gold.source.docs["source_manifest"]["ranges"]:
            for row in source_range["units"]:
                link = {"range_id": source_range["range_id"], "identity": row["identity"]}
                key = cert.digest(link)
                self.units[key] = {"source_unit": link, "sha256": row["sha256"], "members": [],
                                   "stratum": "ordinary" if source_range["range_id"] != "range-0" else "identity"}
        self.members = self.phase5.gold.source.docs["lexical_universe"]["members"]
        for member in self.members:
            for link in member["source_units"]:
                self.units[cert.digest(link)]["members"].append(member["member_id"])
        self.inventory = {
            "schema_version": "word-card-universe-inventory.v1",
            "accepted_by": {"id": "steward", "family": "steward-family"},
            "members": [{
                "member_id": member["member_id"], "spellings": ["literal shared head"],
                "lexemes": ["source:lexeme:" + str(index)] if index < 2 else [],
                "senses": ["source:sense:" + str(index)],
                "mwes": ["source:mwe:1"] if index == 2 else [], "forms": ["source:form:" + str(index)],
                "card_ids": [self.card["card_id"]] if index == 0 else [], "evidence": [self.evidence],
            } for index, member in enumerate(self.members)],
            "strata": [{"unit_key": key, "stratum": unit["stratum"]} for key, unit in self.units.items()],
        }
        first = cert.digest(self.members[0]["source_units"][0])
        self.plan = {"schema_version": "word-card-universe-plan.v1", "dispositions": []}
        for key in sorted(self.units):
            mapped = key == first
            self.plan["dispositions"].append({
                "unit_key": key, "status": "mapped" if mapped else "unresolved",
                "cards": [self.phase5.spec["cases"][0]["card"]] if mapped else [],
                "reason": "literal fixture mapping" if mapped else "missing independent source alignment",
                "owner": None if mapped else "open-model-data",
                "dependency": None if mapped else "source alignment evidence for this unit",
                "evidence": [self.evidence],
            })
        self.resources = {
            "schema_version": "word-card-universe-resources.v1",
            "source_unit_count": 144, "limits": self.spec["limits"],
            "accepted_by": {"id": "resource-reviewer", "family": "reviewer-family"},
            "peak_rss_bytes": 1024, "rss_budget_bytes": 2048, "interrupted_after": [1, 7, 143],
            "evidence": [self.evidence],
        }
        self.refresh()

    def refresh(self):
        self.spec["inventory"] = write(self.inventory_path, self.inventory)
        self.spec["plan"] = write(self.plan_path, self.plan)
        rows = [{**{key: row[key] for key in ("unit_key", "status", "reason", "owner", "dependency", "evidence")},
                 "source": self.units[row["unit_key"]],
                 "card_ids": [self.card["card_id"]] if row["cards"] else [],
                 "card_hashes": {self.card["card_id"]: cert.digest(self.card)} if row["cards"] else {}}
                for row in sorted(self.plan["dispositions"], key=lambda row: row["unit_key"]) if row["unit_key"] in self.units]
        self.output = b"".join(gold.canonical(row) for row in rows)
        for name in ("uninterrupted", "resumed"):
            path = self.root / (name + ".jsonl")
            path.write_bytes(self.output)
            self.resources[name] = {"path": str(path), "sha256": hashlib.sha256(self.output).hexdigest()}
        self.resources["inputs_sha256"] = universe.input_binding(self.spec)
        self.spec["resource_acceptance"] = write(self.resource_path, self.resources)
        self.pin = write(self.spec_path, self.spec)["sha256"]
        self.proof = {
            "schema_version": "word-card-universe-reconciliation.v1", "spec_sha256": self.pin,
            "source_unit_count": 144, "dispositions_sha256": hashlib.sha256(self.output).hexdigest(),
            "cards_sha256": hashlib.sha256(gold.canonical(self.card)).hexdigest(),
            "accepted_by": {"id": "held-out-reviewer", "family": "independent-family"},
            "inspections": [{"unit_key": key, "check": check, "verdict": "pass",
                             "reason": "source-free fixture inspection", "evidence": [self.evidence]}
                            for key in self.units for check in universe.CHECKS],
        }
        self.proof_ref = write(self.proof_path, self.proof)

    def freeze(self):
        return universe.freeze_inventory(self.spec_path, self.pin)

    def recertify_card(self):
        self.phase5.authority.approve_review(self.card)
        self.phase5.spec["cases"][0]["card"] = write(self.phase5.card_path, self.card)
        self.phase5.spec["controls"] = []
        for index, check in enumerate(cert.CONTROL_FACETS):
            self.phase5.add_control(check, f"control-{index}")
        self.phase5.mechanics["cards_sha256"] = cert.digest([self.card])
        self.phase5.spec["mechanics_receipt"] = write(self.phase5.mechanics_path, self.phase5.mechanics)
        self.phase5.save_spec()
        self.phase5.make_evaluation()
        self.phase5.approve()
        self.spec["certifications"] = [self.phase5.receipt()]
        mapped = next(row for row in self.plan["dispositions"] if row["status"] == "mapped")
        mapped["cards"] = [self.phase5.spec["cases"][0]["card"]]
        self.refresh()

    def build(self, **kwargs):
        return universe.build(self.spec_path, self.pin, self.checkpoint, **kwargs)

    def reconcile(self):
        self.proof_ref = write(self.proof_path, self.proof)
        return universe.reconcile(self.spec_path, self.pin, self.checkpoint, self.proof_ref, self.root)


@pytest.fixture(scope="module")
def universe_template(tmp_path_factory, validation_cache):
    root = tmp_path_factory.mktemp("universe-template")
    with pytest.MonkeyPatch.context() as patch:
        authority = certification_fixture.__wrapped__(root, patch)
        template = UniverseFixture(root / "universe", authority)
        bindings = {name: getattr(cert, name) for name in (
            "PROJECT_ROOT", "SCHEMA_PATH", "REVIEW_EVIDENCE_PATH", "PERMISSIONS_REGISTER_PATH",
            "IMPLEMENTATION_PATHS", "RULE_PATHS",
        )}
    files = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
    return template, bindings, files, copy.deepcopy(authority.ledger)


@pytest.fixture
def packet(universe_template, monkeypatch):
    template, bindings, files, ledger = universe_template
    # Preserve absolute paths and their pinned hashes, but restore every test's disk mutations.
    for path in template.root.parent.rglob("*"):
        if path.is_file() and path not in files:
            path.unlink()
    for path, raw in files.items():
        if not path.exists() or path.read_bytes() != raw:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    for name, value in bindings.items():
        monkeypatch.setattr(cert, name, value)
    # approve_review closes over this dictionary; keep that alias in the per-test copy.
    authority_ledger = template.phase5.authority.ledger
    authority_ledger.clear()
    authority_ledger.update(copy.deepcopy(ledger))
    # Source documents are read-only here; source corruption tests change their files.
    source = template.phase5.gold.source
    return copy.deepcopy(template, {id(authority_ledger): authority_ledger, id(source): source})


@pytest.mark.parametrize("value,valid", [
    ([{"a": [1, True]}, {"a": [True, 1]}], True),
    ([{"a": [1, True]}, {"a": [1.0, True]}], False),
    ([{"a": 1, "b": 2}, {"b": 2, "a": 1}], False),
    ([1, True, None, "1", False, 0], True),
    ([[], []], False),
    ([{"a": []}, {"a": {}}], True),
    ([], True),
])
def test_cached_validation_preserves_json_schema_uniqueness(validation_cache, value, valid):
    schema = {"uniqueItems": True}
    assert validators.Draft202012Validator(schema).is_valid(value) is valid
    assert gold.VALIDATOR(schema).is_valid(value) is valid


def test_cached_accounting_rechecks_transitive_source_bytes(packet):
    packet.freeze()
    source = packet.phase5.gold.source
    index = source.root / source.docs["source_manifest"]["ranges"][0]["index"]["path"]
    index.write_bytes(b"changed source index")
    with pytest.raises(ValueError):
        packet.freeze()


def test_frozen_denominator_and_independent_reconciliation(packet):
    frozen = packet.freeze()
    assert frozen["counts"] == {"source_units": 144, "lexical_members": 3, "spellings": 1,
                                "lexemes": 2, "senses": 3, "mwes": 1, "forms": 3, "cards": 1}
    assert packet.build() == {"status": "BUILT_UNRECONCILED", "spec_sha256": packet.pin,
                              "source_units": 144, "accounted_units": 144}
    result = packet.reconcile()
    assert result["partitions"] == {"mapped": 1, "unresolved": 143, "excluded": 0}
    assert sum(result["partitions"].values()) == result["counts"]["source_units"]
    assert result["missing_units"] == result["duplicate_units"] == 0
    assert result["dispositions_sha256"] == hashlib.sha256(packet.output).hexdigest()
    assert len(result["residuals"]) == 143
    assert all(row["owner"] == "open-model-data" and row["dependency"] for row in result["residuals"])
    assert result["programme_completion"] == "UNRESOLVED"
    assert result["export_authorized"] is False
    assert len(result["by_source"]) == 20
    assert result["by_source"]["range-0"]["source_units"] == 3
    assert result["by_stratum"]["identity"]["source_units"] == 3
    assert list(result["certifications"].values()) == [{packet.card["card_id"]: cert.digest(packet.card)}]


@pytest.mark.parametrize("point", [1, 7, 71, 143, 144, 145],
                         ids=["early", "batch-boundary", "middle", "last-partial", "complete", "past-completion"])
def test_resume_is_byte_identical_and_idempotent(packet, point):
    first = packet.build(max_units=point)
    assert first["accounted_units"] == min(point, 144)
    assert first["status"] == ("INTERRUPTED" if point < 144 else "BUILT_UNRECONCILED")
    assert packet.build()["accounted_units"] == 144
    receipt = packet.reconcile()
    assert packet.build()["accounted_units"] == 144
    assert packet.reconcile() == receipt
    with sqlite3.connect(packet.checkpoint) as connection:
        actual = b"".join(row[0] for row in connection.execute("SELECT payload FROM units ORDER BY unit_key"))
    assert actual == packet.output


def test_distinct_source_identities_never_collapse_to_spelling(packet):
    links = packet.members
    keys = {universe.unit_key(member["source_units"][0]) for member in links}
    assert len(keys) == 3
    assert {member["source_units"][0]["identity"]["key"] for member in links} == {"fixture-key"}
    for facet, value in [("homonym", "other"), ("sense", "other"), ("path", ["other"]), ("occurrence", 42)]:
        link = copy.deepcopy(links[0]["source_units"][0])
        original = universe.unit_key(link)
        link["identity"][facet] = value
        assert universe.unit_key(link) != original


def test_explicit_exclusion_retains_owner_and_dependency(packet):
    row = next(row for row in packet.plan["dispositions"] if row["status"] == "unresolved")
    row["status"] = "excluded"
    row["reason"] = "source-scoped nonlexical record"
    packet.refresh()
    packet.build()
    receipt = packet.reconcile()
    assert receipt["partitions"] == {"mapped": 1, "unresolved": 142, "excluded": 1}
    assert next(value for value in receipt["residuals"] if value["unit_key"] == row["unit_key"])["reason"] == row["reason"]


@pytest.mark.parametrize("fault", ["missing", "duplicate", "extra", "no-owner", "no-dependency", "residual-cards",
                                    "mapped-no-card", "duplicate-card", "wrong-card-mapping"])
def test_invalid_dispositions_fail_before_checkpoint(packet, fault):
    rows = packet.plan["dispositions"]
    mapped = next(row for row in rows if row["status"] == "mapped")
    residual = next(row for row in rows if row["status"] == "unresolved")
    if fault == "missing":
        rows.pop()
    elif fault == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    elif fault == "extra":
        rows[0]["unit_key"] = "a" * 64
    elif fault == "no-owner":
        residual["owner"] = None
    elif fault == "no-dependency":
        residual["dependency"] = None
    elif fault == "residual-cards":
        residual["cards"] = mapped["cards"]
    elif fault == "mapped-no-card":
        mapped["cards"] = []
    elif fault == "duplicate-card":
        mapped["cards"].append(mapped["cards"][0])
    else:
        residual.update(status="mapped", cards=mapped["cards"], owner=None, dependency=None)
    packet.refresh()
    with pytest.raises(ValueError):
        packet.build()
    assert not packet.checkpoint.exists()


@pytest.mark.parametrize("fault", ["member-missing", "member-duplicate", "stratum-missing", "stratum-duplicate",
                                    "no-spelling", "self", "same-family", "card-unmapped"])
def test_inventory_cannot_hide_gaps(packet, fault):
    inventory = packet.inventory
    if fault == "member-missing":
        inventory["members"].pop()
    elif fault == "member-duplicate":
        inventory["members"].append(copy.deepcopy(inventory["members"][0]))
    elif fault == "stratum-missing":
        inventory["strata"].pop()
    elif fault == "stratum-duplicate":
        inventory["strata"].append(copy.deepcopy(inventory["strata"][0]))
    elif fault == "no-spelling":
        inventory["members"][0]["spellings"] = []
    elif fault == "card-unmapped":
        inventory["members"][2]["card_ids"] = ["wc_unevaluated"]
    else:
        inventory["accepted_by"]["id" if fault == "self" else "family"] = packet.spec["author"]["id" if fault == "self" else "family"]
    packet.refresh()
    with pytest.raises(ValueError):
        packet.freeze()


@pytest.mark.parametrize("fault", ["status-only", "changed-card", "withdrawn", "source-drift", "implementation-drift"])
def test_uncertified_and_stale_cards_refused_on_resume(packet, fault):
    packet.build(max_units=1)
    if fault == "status-only":
        write(Path(packet.spec["certifications"][0]["path"]), {"status": "CERTIFIED"})
    elif fault == "changed-card":
        packet.card["key_at_creation"]["spelling"] = "unreviewed"
        write(packet.phase5.card_path, packet.card)
    elif fault == "withdrawn":
        packet.phase5.authority.ledger["approved_reviews"][0]["status"] = "withdrawn"
        write(packet.phase5.authority.ledger_path, packet.phase5.authority.ledger)
    elif fault == "source-drift":
        packet.phase5.authority.snapshots["S", "source"].write_bytes(b"changed")
    else:
        packet.phase5.authority.code.write_bytes(b"changed implementation")
    with pytest.raises(ValueError):
        packet.build()
    with pytest.raises(ValueError):
        packet.reconcile()


@pytest.mark.parametrize("fault", ["unit-delete", "unit-corrupt", "unit-extra", "card-delete", "card-corrupt",
                                    "card-extra", "duplicate-unit", "metadata"])
def test_checkpoint_is_verified_against_source_not_its_own_totals(packet, fault):
    packet.build()
    with sqlite3.connect(packet.checkpoint) as connection:
        if fault == "unit-delete":
            connection.execute("DELETE FROM units WHERE unit_key = (SELECT unit_key FROM units LIMIT 1)")
        elif fault == "unit-corrupt":
            connection.execute("UPDATE units SET payload = ? WHERE unit_key = (SELECT unit_key FROM units LIMIT 1)", (b"{}",))
        elif fault == "unit-extra":
            connection.execute("INSERT INTO units VALUES (?, ?)", ("a" * 64, b"{}"))
        elif fault == "card-delete":
            connection.execute("DELETE FROM cards")
        elif fault == "card-corrupt":
            connection.execute("UPDATE cards SET payload = ?", (b"{}",))
        elif fault == "card-extra":
            connection.execute("INSERT INTO cards VALUES (?, ?)", ("wc_unknown", b"{}"))
        elif fault == "duplicate-unit":
            connection.execute("ALTER TABLE units RENAME TO old_units")
            connection.execute("CREATE TABLE units AS SELECT * FROM old_units")
            connection.execute("INSERT INTO units SELECT * FROM old_units LIMIT 1")
        else:
            connection.execute("UPDATE metadata SET spec_sha256 = ?", ("a" * 64,))
    with pytest.raises(ValueError):
        packet.reconcile()
    if fault != "unit-delete":
        with pytest.raises(ValueError):
            packet.build()
    else:
        assert packet.build()["accounted_units"] == 144


@pytest.mark.parametrize("fault", ["subset", "inputs", "limits", "rss", "interrupt", "output", "self", "same-family"])
def test_full_scale_resource_acceptance_is_required(packet, fault):
    resource = packet.resources
    if fault == "subset":
        resource["source_unit_count"] = 3
    elif fault == "inputs":
        resource["inputs_sha256"] = "a" * 64
    elif fault == "limits":
        resource["limits"] = {**packet.spec["limits"], "batch_units": 1}
    elif fault == "rss":
        resource["peak_rss_bytes"] = 4096
    elif fault == "interrupt":
        resource["interrupted_after"] = [144]
    elif fault == "output":
        Path(resource["resumed"]["path"]).write_bytes(b"reduced output")
    else:
        resource["accepted_by"]["id" if fault == "self" else "family"] = packet.spec["author"]["id" if fault == "self" else "family"]
    packet.spec["resource_acceptance"] = write(packet.resource_path, resource)
    packet.pin = write(packet.spec_path, packet.spec)["sha256"]
    with pytest.raises(ValueError):
        packet.build()
    assert not packet.checkpoint.exists()


@pytest.mark.parametrize("fault", ["subset", "hash", "self", "same-family", "source-missing", "check-missing", "foreign-unit"])
def test_independent_inspection_covers_every_source_and_failure_stratum(packet, fault):
    packet.build()
    if fault == "subset":
        packet.proof["source_unit_count"] = 3
    elif fault == "hash":
        packet.proof["cards_sha256"] = "a" * 64
    elif fault in {"self", "same-family"}:
        key = "id" if fault == "self" else "family"
        packet.proof["accepted_by"][key] = packet.spec["author"][key]
    elif fault == "source-missing":
        packet.proof["inspections"] = [row for row in packet.proof["inspections"]
                                         if packet.units[row["unit_key"]]["source_unit"]["range_id"] != "range-1"]
    elif fault == "check-missing":
        packet.proof["inspections"] = [row for row in packet.proof["inspections"] if row["check"] != "citations"]
    else:
        packet.proof["inspections"][0]["unit_key"] = "a" * 64
    with pytest.raises(ValueError):
        packet.reconcile()


def test_incomplete_build_cannot_reconcile(packet):
    packet.build(max_units=1)
    with pytest.raises(ValueError, match="Incomplete checkpoint"):
        packet.reconcile()


def test_frozen_inventory_corruption_is_fail_closed(packet):
    packet.inventory_path.write_bytes(b"{}")
    with pytest.raises(ValueError, match="digest mismatch"):
        packet.build()
    assert not packet.checkpoint.exists()


@pytest.mark.parametrize("value", [True, 0, -1, 1.5])
def test_invalid_interruption_boundary(packet, value):
    with pytest.raises(ValueError, match="interruption limit"):
        packet.build(max_units=value)


def test_resource_limits_enforced_locally(packet, monkeypatch):
    monkeypatch.setattr(universe.shutil, "disk_usage", lambda _: type("Disk", (), {"free": 0})())
    with pytest.raises(ValueError, match="Insufficient checkpoint space"):
        packet.build()
    assert not packet.checkpoint.exists()


def test_card_size_limit_cannot_be_bypassed(packet):
    packet.spec["limits"]["max_card_bytes"] = 1
    packet.refresh()
    with pytest.raises(ValueError, match="Card exceeds resource limit"):
        packet.build()


def test_missing_checkpoint_read_does_not_create_database(packet):
    with pytest.raises(sqlite3.OperationalError):
        packet.reconcile()
    assert not packet.checkpoint.exists()


@pytest.mark.parametrize("after,committed", [(4, 0), (10, 7)])
def test_interrupted_transaction_rolls_back_whole_batch(packet, monkeypatch, after, committed):
    connect = sqlite3.connect

    class InterruptedConnection(sqlite3.Connection):
        inserted = 0

        def execute(self, sql, parameters=()):
            if sql.startswith("INSERT INTO units"):
                self.inserted += 1
                if self.inserted == after:
                    raise InterruptedError("simulated loss during batch")
            return super().execute(sql, parameters)

    with monkeypatch.context() as local:
        local.setattr(universe.sqlite3, "connect", lambda path: connect(path, factory=InterruptedConnection))
        with pytest.raises(InterruptedError):
            packet.build()
    with connect(packet.checkpoint) as connection:
        assert connection.execute("SELECT COUNT(*) FROM units").fetchone()[0] == committed
    assert packet.build()["accounted_units"] == 144
    assert packet.reconcile()["dispositions_sha256"] == hashlib.sha256(packet.output).hexdigest()


def test_changed_freeze_cannot_reuse_checkpoint(packet):
    packet.build(max_units=1)
    packet.plan["dispositions"][0]["reason"] += " changed"
    packet.refresh()
    with pytest.raises(ValueError, match="another freeze"):
        packet.build()


@pytest.mark.parametrize("field", ["source_unit_count", "peak_rss_bytes", "rss_budget_bytes"])
def test_boolean_is_not_a_resource_measurement(packet, field):
    packet.resources[field] = True
    packet.spec["resource_acceptance"] = write(packet.resource_path, packet.resources)
    packet.pin = write(packet.spec_path, packet.spec)["sha256"]
    with pytest.raises(ValueError, match="Invalid full-scale resource acceptance"):
        packet.build()


def test_one_card_cannot_collapse_distinct_homonyms(packet):
    packet.inventory["members"][1]["card_ids"] = [packet.card["card_id"]]
    packet.refresh()
    with pytest.raises(ValueError, match="Distinct lexical identities share a card"):
        packet.freeze()


@pytest.mark.parametrize("identities", ["lexemes", "mwes", "mixed"])
def test_duplicate_card_ids_cannot_collapse_supportable_identities(packet, monkeypatch, identities):
    row = packet.inventory["members"][0]
    row["lexemes"] = ["source:lexeme:0", "source:lexeme:1"] if identities == "lexemes" else []
    row["mwes"] = ["source:mwe:0", "source:mwe:1"] if identities == "mwes" else []
    if identities == "mixed":
        row["lexemes"] = ["source:lexeme:0"]
        row["mwes"] = ["source:mwe:0"]
    row["card_ids"] = [packet.card["card_id"], packet.card["card_id"]]
    # Isolate allocation validation from the schema's earlier uniqueItems rejection.
    monkeypatch.setattr(universe, "_document", lambda *args: packet.inventory)
    with pytest.raises(ValueError, match="Supportable lexical identities collapsed"):
        universe._inventory(packet.spec["inventory"], packet.root, packet.units,
                            {member["member_id"]: member for member in packet.members}, packet.spec["author"])


def test_unbound_checkpoint_rows_are_not_adopted(packet):
    with sqlite3.connect(packet.checkpoint) as connection:
        connection.execute("CREATE TABLE units (unit_key TEXT PRIMARY KEY, payload BLOB NOT NULL)")
        connection.execute("INSERT INTO units VALUES (?, ?)", ("a" * 64, b"{}"))
    with pytest.raises(ValueError, match="Unbound checkpoint data"):
        packet.build()


def test_independent_evidence_is_rehashed_on_reimport(packet):
    packet.build()
    packet.reconcile()
    Path(packet.evidence["path"]).write_bytes(b"changed witness")
    with pytest.raises(ValueError):
        packet.reconcile()


@pytest.mark.parametrize("fault", ["generator", "missing-locator"])
def test_even_certified_cards_must_be_cited_source_only(packet, fault):
    if fault == "generator":
        packet.card["assertions"][0]["producer"]["kind"] = "generator"
    else:
        packet.card["assertions"][0]["locator"] = ""
    packet.recertify_card()
    assert cert.load_certified_card_for_export(packet.card) == packet.card
    with pytest.raises(ValueError, match="Only cited source-extract assertions"):
        packet.build()


def test_mutated_source_inventory_cannot_keep_frozen_pin(packet):
    manifest = packet.phase5.gold.source.paths["source_manifest"]
    value = gold.decode(manifest.read_bytes())
    value["ranges"][0]["units"].pop()
    write(manifest, value)
    with pytest.raises(ValueError):
        packet.freeze()


def test_checkpoint_cannot_write_into_tracked_checkout(packet):
    target = Path(universe.__file__).parent / "universe-checkpoint.py"
    with pytest.raises(ValueError, match="host-only"):
        universe.build(packet.spec_path, packet.pin, target)
    assert not target.exists()


def test_resource_trial_can_measure_harness_but_cannot_claim_acceptance(packet):
    packet.spec["resource_acceptance"] = {"path": "not-yet-accepted.json", "sha256": "a" * 64}
    packet.pin = write(packet.spec_path, packet.spec)["sha256"]
    assert packet.build(resource_trial=True, max_units=7)["status"] == "RESOURCE_TRIAL_INTERRUPTED"
    assert packet.build(resource_trial=True)["status"] == "RESOURCE_TRIAL_BUILT_UNRECONCILED"
    with pytest.raises(OSError):
        packet.freeze()
    with pytest.raises(OSError):
        packet.reconcile()
    with pytest.raises(OSError):
        packet.build()


def test_resource_trial_still_requires_current_exact_certification(packet):
    packet.phase5.authority.ledger["approved_reviews"][0]["status"] = "withdrawn"
    write(packet.phase5.authority.ledger_path, packet.phase5.authority.ledger)
    with pytest.raises(cert.UncertifiedCardRefusal):
        packet.build(resource_trial=True)
    assert not packet.checkpoint.exists()


def test_changed_runtime_invalidates_resource_proof(packet, monkeypatch):
    monkeypatch.setattr(universe, "runtime_fingerprint", lambda: "a" * 64)
    with pytest.raises(ValueError, match="Resource runtime changed"):
        packet.build()


@pytest.mark.parametrize("changed_file", [
    "scripts/atlas/word_card_universe.py",
    "scripts/atlas/word_card_certification.py",
    "scripts/atlas/word_card_golden_set.py",
    "scripts/atlas/word_card_assembly.py",
    "scripts/projects/open_model_data/source_completeness_manifest.py",
])
def test_changed_implementation_invalidates_resource_proof(packet, monkeypatch, tmp_path, changed_file):
    packet.build(max_units=1)
    root = tmp_path / "runtime"
    paths = []
    for source in universe.IMPLEMENTATION_PATHS:
        target = root / source.relative_to(universe.PROJECT_ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        paths.append(target)
    monkeypatch.setattr(universe, "PROJECT_ROOT", root)
    monkeypatch.setattr(universe, "IMPLEMENTATION_PATHS", tuple(paths))
    assert universe.runtime_fingerprint() == packet.spec["runtime_sha256"]
    changed = root / changed_file
    changed.write_bytes(changed.read_bytes() + b"\n# changed implementation\n")
    assert universe.runtime_fingerprint() != packet.spec["runtime_sha256"]
    with pytest.raises(ValueError, match="Resource runtime changed"):
        packet.build()
    with pytest.raises(ValueError, match="Resource runtime changed"):
        universe._resources(packet.spec, packet.root, 144, hashlib.sha256(packet.output).hexdigest())


@pytest.mark.parametrize("stride", [2, 3, 5])
def test_partition_conservation_with_mixed_dispositions(packet, stride):
    for ordinal, row in enumerate(packet.plan["dispositions"]):
        if row["status"] == "unresolved" and ordinal % stride == 0:
            row["status"] = "excluded"
    excluded = sum(row["status"] == "excluded" for row in packet.plan["dispositions"])
    packet.refresh()
    packet.build()
    partitions = packet.reconcile()["partitions"]
    assert partitions == {"mapped": 1, "unresolved": 143 - excluded, "excluded": excluded}
    assert sum(partitions.values()) == 144


@pytest.mark.parametrize("operation", ["freeze", "build", "reconcile"])
def test_outer_export_context_cannot_conceal_current_withdrawal(packet, operation):
    packet.build()
    with cert.certification_run():
        cert.load_certified_card_for_export(packet.card)
        packet.phase5.authority.ledger["approved_reviews"][0]["status"] = "withdrawn"
        write(packet.phase5.authority.ledger_path, packet.phase5.authority.ledger)
        with pytest.raises(cert.UncertifiedCardRefusal, match="withdrawn"):
            getattr(packet, operation)()
