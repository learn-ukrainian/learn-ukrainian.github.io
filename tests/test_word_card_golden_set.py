"""Source-free mechanics and deliberate falsifiers, never independent gold proof."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.atlas import word_card_golden_set as gold
from scripts.projects.open_model_data import source_completeness_manifest as accounting
from tests.projects.open_model_data.test_source_completeness_manifest import Fixture


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


class GoldFixture:
    def __init__(self, root):
        self.root = root
        evidence = root / "evidence"
        evidence.mkdir()
        self.source = Fixture(evidence)
        self.atlas = evidence / "atlas.json"
        write(self.atlas, {"version": "0.1", "entries": [{"lemma": "fixture-key", "url_slug": "fixture-slug"}]})
        self.spec_path = root / "vault" / "spec.json"
        self.cases_path = root / "vault" / "cases.json"
        self.bundle = root / "vault" / "gold"
        self.isolation_path = root / "vault" / "isolation.json"
        self.opaque = write(root / "independent-proof.txt", {"fixture": "external authority proof placeholder"})
        self.refs = {name: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                     for name, path in self.source.paths.items()}
        self.refs["atlas_manifest"] = {"path": str(self.atlas), "sha256": hashlib.sha256(self.atlas.read_bytes()).hexdigest()}
        self.refs["development_membership"] = write(root / "dev-membership.json", {"protected_keys": ["old-development-only"]})
        self.spec = {
            "schema_version": "word-card-gold-spec.v1", "inputs": self.refs,
            "universe_count": 3, "candidate_entry_count": 1, "case_count": 1,
            "assembler_build_sha256": "a" * 64,
            "protected_root": str(root / "vault"),
            "strata": {"ordinary-control": 1}, "required_fields": ["identity", "source_note"],
            "roles": {
                "assembler": {"id": "assembler", "family": "author-family"},
                "steward": {"id": "steward", "family": "steward-family"},
                "adjudicators": [{"id": "judge-one", "family": "family-one", "qualification": self.opaque},
                                 {"id": "judge-two", "family": "family-two", "qualification": self.opaque}],
            },
            "selection": {"method": "fresh-source-side", "evidence": self.opaque, "assembler_outputs_seen": False},
        }
        source_range = self.source.docs["source_manifest"]["ranges"][0]
        source_ref = {"path": str(evidence / source_range["index"]["path"]),
                      "sha256": source_range["index"]["sha256"]}
        link = self.source.docs["lexical_universe"]["members"][0]["source_units"][0]
        self.claim = {"reference": source_ref, "source_unit": link, "scope": "literal source-free fixture evidence",
                      "pointer": "/units/0/identity", "value": link["identity"]}
        expectation = {"field": "identity", "state": "value", "claims": [self.claim], "reason": "literal fixture identity",
                       "votes": [{"adjudicator_id": "judge-one", "disposition": "agree"},
                                 {"adjudicator_id": "judge-two", "disposition": "agree"}]}
        note = copy.deepcopy(expectation)
        note.update(field="source_note", reason="literal fixture edition")
        note["claims"][0].update(pointer="/edition", value="literal-fixture-edition")
        self.cases = {"schema_version": "word-card-gold-cases.v1", "cases": [{
            "case_id": "case-001", "member_id": "fixture-member-0", "stratum": "ordinary-control",
            "source_keys": ["fixture-key"], "aliases": ["fixture-alias"], "related_source_keys": ["fixture-related"],
            "expectations": [expectation, note],
        }]}
        self.refresh_accounting()
        self.save()

    def refresh_accounting(self):
        outputs, receipt = accounting.account(self.source.paths, atlas_manifest=self.atlas)
        receipt.pop("_input_paths")
        directory = self.root / "accounting"
        directory.mkdir(exist_ok=True)
        for name, raw in outputs.items():
            (directory / name).write_bytes(raw)
        self.refs["accounting_receipt"] = write(directory / "manifest-receipt.json", receipt)
        self.refs["census"] = {"path": str(directory / "atlas-census.json"),
                               "sha256": hashlib.sha256(outputs["atlas-census.json"]).hexdigest()}
        clearance = {
            "schema_version": "word-card-complete-data.v1", "status": "COMPLETE_DATA_APPROVED",
            "phase1": "COMPLETE", "phase2": "COMPLETE", "candidate": "Candidate A Lexical Universe v1",
            "accounting_sha256": self.refs["accounting_receipt"]["sha256"],
            "census_sha256": self.refs["census"]["sha256"],
            "lexical_universe_sha256": self.refs["lexical_universe"]["sha256"],
            "approved_by": {"id": "source-authority", "family": "source-family"},
            "prerequisites": dict.fromkeys(("source_authority", "snapshot_boundary", "lexical_fidelity",
                                           "phase1_acceptance", "phase2_acceptance", "candidate_a_reconciliation"), self.opaque),
        }
        self.refs["complete_data_receipt"] = write(self.root / "clearance.json", clearance)

    def save(self):
        self.spec_sha = write(self.spec_path, self.spec)["sha256"]
        write(self.cases_path, self.cases)

    def seal(self):
        self.save()
        return gold.seal(self.spec_path, self.spec_sha, self.cases_path, self.bundle)

    def custody(self):
        assembler = self.root / "assembler-inputs"
        assembler.mkdir(exist_ok=True)
        source_input = write(assembler / "selection.json", {"source_records": [{"key": "unrelated-development"}]})
        self.isolation = {
            "schema_version": "word-card-gold-isolation.v1", "spec_sha256": self.spec_sha,
            "seal_sha256": hashlib.sha256((self.bundle / "seal.json").read_bytes()).hexdigest(),
            "assembler_build_sha256": "a" * 64,
            "verified_by": {"id": "custody-verifier", "family": "independent-family"},
            "custody_evidence": [self.opaque], "readable_roots": [str(assembler)], "writable_roots": [str(assembler)],
            "assembler_inputs": [{"role": "mutation", "reference": source_input}], "roots_complete": True, "log_complete": True,
            "alias_related_closure_checked": True, "adjudication_blind": True,
            "access_log": [{"actor_id": "assembler", "resource": resource, "operation": operation, "allowed": False}
                           for resource in ("membership", "answers", "aliases", "related")
                           for operation in ("read", "write")],
        }
        return self.save_custody()

    def save_custody(self):
        self.isolation_sha = write(self.isolation_path, self.isolation)["sha256"]
        return self.isolation_sha

    def verify(self):
        return gold.verify(self.spec_path, self.spec_sha, self.bundle, self.isolation_path, self.isolation_sha)


@pytest.fixture
def fixture(tmp_path):
    return GoldFixture(tmp_path)


def test_seal_and_verify_exact_bundle(fixture):
    result = fixture.seal()
    assert result["status"] == "SEALED_ISOLATION_UNVERIFIED"
    assert result["case_count"] == 1
    assert {p.name for p in fixture.bundle.iterdir()} == {"membership.json", "answers.json", "seal.json"}
    membership = json.loads((fixture.bundle / "membership.json").read_bytes())
    assert "expectations" not in membership["cases"][0]
    assert (fixture.bundle / "answers.json").stat().st_mode & 0o777 == 0o400
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in fixture.bundle.iterdir()}
    assert fixture.seal() == result
    assert before == {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in fixture.bundle.iterdir()}
    fixture.custody()
    verified = fixture.verify()
    assert verified == {"status": "VERIFIED_RECEIPTS", "case_count": 1, "expectation_count": 2,
                        "assembler_access_count": 0, "seal_sha256": result["seal_sha256"],
                        "assembler_build_sha256": "a" * 64}


@pytest.mark.parametrize("name", ["complete_data_receipt", "accounting_receipt", "census", "stage_evidence"])
def test_missing_gate_artifacts_publish_nothing(fixture, name):
    Path(fixture.refs[name]["path"]).unlink()
    with pytest.raises((gold.Refusal, OSError)):
        fixture.seal()
    assert not fixture.bundle.exists()


def test_structural_accounting_is_not_complete_data_clearance(fixture):
    ref = fixture.refs["complete_data_receipt"]
    fixture.refs["complete_data_receipt"] = write(Path(ref["path"]), json.loads(Path(fixture.refs["accounting_receipt"]["path"]).read_bytes()))
    with pytest.raises(gold.Refusal, match="complete-data receipt"):
        fixture.seal()


def test_valid_incomplete_accounting_cannot_admit_gold(fixture):
    fixture.source.docs["stage_evidence"]["records"] = []
    fixture.source.save()
    fixture.refs["stage_evidence"] = {"path": str(fixture.source.paths["stage_evidence"]),
                                      "sha256": hashlib.sha256(fixture.source.paths["stage_evidence"].read_bytes()).hexdigest()}
    fixture.refresh_accounting()
    with pytest.raises(gold.Refusal, match="unresolved gaps"):
        fixture.seal()
    assert not fixture.bundle.exists()


@pytest.mark.parametrize("field,value", [("universe_count", 2), ("candidate_entry_count", 2), ("case_count", 2),
                                         ("universe_count", True), ("universe_count", 3.0),
                                         ("strata", {"missing-stratum": 1}), ("required_fields", ["source_note"])])
def test_frozen_denominators_and_identity_coverage(fixture, field, value):
    fixture.spec[field] = value
    with pytest.raises(gold.Refusal):
        fixture.seal()


def test_trusted_pin_cannot_be_updated_by_input_drift(fixture):
    fixture.save()
    pinned = fixture.spec_sha
    fixture.spec["case_count"] = 2
    fixture.save()
    with pytest.raises(gold.Refusal, match="digest mismatch"):
        gold.seal(fixture.spec_path, pinned, fixture.cases_path, fixture.bundle)


@pytest.mark.parametrize("kind", ["receipt", "output", "census", "source", "clearance-binding", "prerequisite"])
def test_replay_and_transitive_evidence_tampering(fixture, kind):
    if kind == "receipt":
        path = Path(fixture.refs["accounting_receipt"]["path"])
        value = json.loads(path.read_bytes())
        value["supplied_unit_count"] += 1
        fixture.refs["accounting_receipt"] = write(path, value)
    elif kind == "output":
        path = Path(fixture.refs["accounting_receipt"]["path"]).parent / "SRC-ULIF.json"
        path.write_bytes(b"{}")
    elif kind == "census":
        path = Path(fixture.refs["census"]["path"])
        value = json.loads(path.read_bytes())
        value["entries"][0]["lemma"] = "wrong-census-entry"
        fixture.refs["census"] = write(path, value)
    elif kind == "source":
        fixture.source.raw.write_bytes(b"drifted source capture")
    elif kind == "clearance-binding":
        path = Path(fixture.refs["complete_data_receipt"]["path"])
        value = json.loads(path.read_bytes())
        value["census_sha256"] = "b" * 64
        fixture.refs["complete_data_receipt"] = write(path, value)
    else:
        Path(fixture.opaque["path"]).write_bytes(b"drifted independent proof")
    with pytest.raises((gold.Refusal, accounting.InvalidEvidence)):
        fixture.seal()


@pytest.mark.parametrize("kind", ["self-steward", "self-adjudicator", "same-family", "missing-judge", "not-blind",
                                 "unqualified", "duplicate-judge"])
def test_independent_roles_and_blind_selection(fixture, kind):
    roles = fixture.spec["roles"]
    if kind == "self-steward":
        roles["steward"] = roles["assembler"]
    elif kind == "self-adjudicator":
        roles["adjudicators"][0]["id"] = "assembler"
    elif kind == "same-family":
        roles["adjudicators"][0]["family"] = "author-family"
    elif kind == "missing-judge":
        roles["adjudicators"].pop()
    elif kind == "not-blind":
        fixture.spec["selection"]["assembler_outputs_seen"] = True
    elif kind == "unqualified":
        roles["adjudicators"][0]["qualification"] = {"path": "missing-qualification", "sha256": "0" * 64}
    else:
        fixture.cases["cases"][0]["expectations"][0]["votes"][1]["adjudicator_id"] = "judge-one"
    with pytest.raises((gold.Refusal, OSError)):
        fixture.seal()


@pytest.mark.parametrize("kind", ["outside-universe", "source-key", "old-case", "old-alias", "old-related",
                                 "duplicate-case", "missing-field", "wrong-value", "unbound-source", "wrong-unit",
                                 "unsupported-pointer", "hidden-disagreement", "hidden-abstention"])
def test_source_grounding_and_fresh_selection(fixture, kind):
    row = fixture.cases["cases"][0]
    claim = row["expectations"][0]["claims"][0]
    if kind == "outside-universe":
        row["member_id"] = "not-a-member"
    elif kind == "source-key":
        row["source_keys"] = ["another-key"]
    elif kind in {"old-case", "old-alias", "old-related"}:
        key = {"old-case": row["case_id"], "old-alias": row["aliases"][0], "old-related": row["related_source_keys"][0]}[kind]
        fixture.refs["development_membership"] = write(fixture.root / "dev-membership.json", {"protected_keys": [key]})
    elif kind == "duplicate-case":
        fixture.cases["cases"].append(copy.deepcopy(row))
        fixture.spec["case_count"] = 2
        fixture.spec["strata"]["ordinary-control"] = 2
    elif kind == "missing-field":
        row["expectations"].pop()
    elif kind == "wrong-value":
        claim["value"] = "invented-value"
    elif kind == "unbound-source":
        claim["reference"] = fixture.opaque
    elif kind == "wrong-unit":
        claim["source_unit"]["range_id"] = "range-1"
    elif kind == "unsupported-pointer":
        row["expectations"][1]["claims"][0]["pointer"] = "/units/00"
    else:
        row["expectations"][0]["votes"] = [
            {"adjudicator_id": "judge-one", "disposition": "disagree" if kind == "hidden-disagreement" else "abstain"},
            {"adjudicator_id": "judge-two", "disposition": "agree" if kind == "hidden-disagreement" else "abstain"},
        ]
    with pytest.raises((gold.Refusal, KeyError, IndexError)):
        fixture.seal()


@pytest.mark.parametrize("state", ["conflict", "abstention"])
def test_conflicts_and_abstentions_are_retained(fixture, state):
    expectation = fixture.cases["cases"][0]["expectations"][1]
    expectation["state"] = state
    expectation["votes"][0]["disposition"] = "disagree" if state == "conflict" else "abstain"
    if state == "conflict":
        claim = copy.deepcopy(expectation["claims"][0])
        claim.update(pointer="/snapshot", value="fixture-snapshot")
        expectation["claims"].append(claim)
    else:
        expectation["votes"][1]["disposition"] = "abstain"
    fixture.seal()
    fixture.custody()
    assert fixture.verify()["expectation_count"] == 2
    answers = json.loads((fixture.bundle / "answers.json").read_bytes())
    assert answers["cases"][0]["expectations"][1]["state"] == state


@pytest.mark.parametrize("kind", ["seal", "answers", "membership", "partial", "symlink"])
def test_immutable_seal_refuses_overwrite(fixture, kind):
    fixture.seal()
    if kind == "partial":
        (fixture.bundle / "seal.json").unlink()
    elif kind == "symlink":
        target = fixture.root / "alias-bundle"
        target.symlink_to(fixture.bundle, target_is_directory=True)
        fixture.bundle = target
    else:
        name = {"seal": "seal.json", "answers": "answers.json", "membership": "membership.json"}[kind]
        (fixture.bundle / name).chmod(0o600)
        (fixture.bundle / name).write_bytes(b"{}")
    with pytest.raises(gold.Refusal):
        fixture.seal()


@pytest.mark.parametrize("kind", ["self-verify", "stale-seal", "stale-spec", "stale-build", "unlogged", "incomplete-roots",
                                 "blindness", "missing-alias-closure", "allowed-read", "allowed-write", "missing-probe",
                                 "readable-gold", "writable-gold", "root-symlink", "outside-root", "proof-drift"])
def test_isolation_requires_independent_exact_artifact_access_proof(fixture, kind):
    fixture.seal()
    fixture.custody()
    proof = fixture.isolation
    if kind == "self-verify":
        proof["verified_by"]["id"] = "assembler"
    elif kind.startswith("stale-"):
        proof[{"stale-seal": "seal_sha256", "stale-spec": "spec_sha256", "stale-build": "assembler_build_sha256"}[kind]] = "b" * 64
    elif kind in {"unlogged", "incomplete-roots", "blindness", "missing-alias-closure"}:
        proof[{"unlogged": "log_complete", "incomplete-roots": "roots_complete", "blindness": "adjudication_blind",
               "missing-alias-closure": "alias_related_closure_checked"}[kind]] = False
    elif kind in {"allowed-read", "allowed-write"}:
        proof["access_log"][0 if kind == "allowed-read" else 1]["allowed"] = True
    elif kind == "missing-probe":
        proof["access_log"].pop()
    elif kind in {"readable-gold", "writable-gold"}:
        proof["readable_roots" if kind == "readable-gold" else "writable_roots"] = [str(fixture.root)]
    elif kind == "root-symlink":
        path = fixture.root / "alias-root"
        path.symlink_to(fixture.root, target_is_directory=True)
        proof["readable_roots"] = [str(path)]
    elif kind == "outside-root":
        proof["assembler_inputs"] = [{"role": "mutation", "reference": fixture.opaque}]
    else:
        Path(fixture.opaque["path"]).write_bytes(b"changed evidence")
    fixture.save_custody()
    with pytest.raises((gold.Refusal, OSError)):
        fixture.verify()


@pytest.mark.parametrize("leak", ["fixture-key", "fixture-alias", "fixture-related", "case-001", "fixture-member-0",
                                 {"expected_mapping": "answer"}, {"payload": '[{"key":"fixture-alias"}]'},
                                 {"fixture-related": "hidden in key"}, {"note": "adjudication for fixture-related"},
                                 '{"key":"fixture-alias","key":"unrelated"}'])
def test_assembler_inputs_reject_protected_identities_and_answers(fixture, leak):
    fixture.seal()
    fixture.custody()
    path = Path(fixture.isolation["assembler_inputs"][0]["reference"]["path"])
    fixture.isolation["assembler_inputs"] = [{"role": "mutation", "reference": write(path, {"rows": [leak]})}]
    fixture.save_custody()
    with pytest.raises(gold.Refusal):
        fixture.verify()


def test_verify_detects_answer_tampering(fixture):
    fixture.seal()
    fixture.custody()
    (fixture.bundle / "answers.json").chmod(0o600)
    (fixture.bundle / "answers.json").write_bytes(b'{}')
    with pytest.raises(gold.Refusal, match="digest mismatch"):
        fixture.verify()


def test_repository_storage_refused(fixture):
    fixture.bundle = Path(gold.__file__).resolve().parents[2] / "batch_state" / "reports" / "gold-fixture-forbidden"
    with pytest.raises(gold.Refusal, match="outside the repository"):
        fixture.seal()


@pytest.mark.parametrize("raw", [b'{"key":1,"key":2}', b'{"value":NaN}', b'{"value":"\\ud800"}', b'\xff',
                               '{"value":1}'.encode("utf-16")])
def test_strict_json_reader(tmp_path, raw):
    path = tmp_path / "invalid.json"
    path.write_bytes(raw)
    with pytest.raises((gold.Refusal, ValueError)):
        gold.read(path)


def test_cli_help_and_fail_closed_boundary(fixture, capsys):
    result = subprocess.run([sys.executable, "-m", "scripts.atlas.word_card_golden_set", "--help"],
                            capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode == 0
    assert all(text in result.stdout for text in ("Outputs:", "Exit codes:", "Related:", "--spec-sha256"))
    args = ["seal", "--spec", str(fixture.spec_path), "--spec-sha256", fixture.spec_sha, "--bundle", str(fixture.bundle)]
    assert gold.main(args) == 2
    assert "GOLD_REFUSED" in capsys.readouterr().err
    assert gold.main([*args, "--cases", str(fixture.cases_path)]) == 0
    fixture.custody()
    assert gold.main(["verify", "--spec", str(fixture.spec_path), "--spec-sha256", fixture.spec_sha,
                      "--bundle", str(fixture.bundle), "--isolation", str(fixture.isolation_path),
                      "--isolation-sha256", fixture.isolation_sha]) == 0
    output = capsys.readouterr().out
    assert "VERIFIED_RECEIPTS" in output
    assert "fixture-key" not in output
    assert gold.main(["verify", "--spec", str(fixture.spec_path), "--spec-sha256", fixture.spec_sha,
                      "--bundle", str(fixture.bundle)]) == 2


@pytest.mark.parametrize("kind", ["index", "capture"])
def test_assembler_can_read_full_authenticated_sources_without_gold_membership(fixture, kind):
    fixture.seal()
    fixture.custody()
    path = fixture.source.root / "index-0.json" if kind == "index" else fixture.source.raw
    fixture.isolation["readable_roots"].append(str(fixture.source.root))
    ref = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    fixture.isolation["assembler_inputs"].append({"role": "source", "reference": ref})
    fixture.save_custody()
    assert fixture.verify()["status"] == "VERIFIED_RECEIPTS"


def test_mutation_cannot_be_relabelled_as_source(fixture):
    fixture.seal()
    fixture.custody()
    fixture.isolation["assembler_inputs"][0]["role"] = "source"
    fixture.save_custody()
    with pytest.raises(gold.Refusal, match="approved source snapshot"):
        fixture.verify()


@pytest.mark.parametrize("kind", ["hardlink", "symlink", "extra-file", "missing-file"])
def test_verify_refuses_bundle_aliases_and_incomplete_inventory(fixture, kind):
    fixture.seal()
    fixture.custody()
    if kind == "hardlink":
        (fixture.root / "leaked-answer-link.json").hardlink_to(fixture.bundle / "answers.json")
    elif kind == "symlink":
        alias = fixture.root / "vault" / "alias-bundle"
        alias.symlink_to(fixture.bundle, target_is_directory=True)
        fixture.bundle = alias
    elif kind == "extra-file":
        (fixture.bundle / "extra.json").write_bytes(b"{}")
    else:
        (fixture.bundle / "answers.json").unlink()
    with pytest.raises(gold.Refusal):
        fixture.verify()


def test_replay_must_still_bind_the_pinned_inputs(fixture, monkeypatch):
    original = accounting.account

    def changed_input(*args, **kwargs):
        outputs, receipt = original(*args, **kwargs)
        receipt["inputs"]["lexical_universe"]["sha256"] = "b" * 64
        return outputs, receipt

    monkeypatch.setattr(accounting, "account", changed_input)
    with pytest.raises(gold.Refusal, match="input changed during replay"):
        fixture.seal()


def test_json_pointer_escaping_and_noncontainer_refusal():
    assert gold.pointer_value({"a/b": {"~": ["literal"]}}, "/a~1b/~0/0") == "literal"
    with pytest.raises(gold.Refusal):
        gold.pointer_value({"field": "literal"}, "/field/nested")
    with pytest.raises(gold.Refusal):
        gold.pointer_value({}, "/invalid~escape")
