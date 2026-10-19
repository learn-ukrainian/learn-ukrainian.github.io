"""Synthetic Phase 5 mechanics. These fixtures never certify Ukrainian or real cards."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.atlas import word_card_certification as cert
from scripts.atlas import word_card_golden_set as gold
from tests.test_word_card_golden_set import GoldFixture, write
from tests.word_card_certification_fixtures import certification_fixture  # noqa: F401


class CertificationFixture:
    def __init__(self, root, authority, abstention=False):
        self.root, self.authority = root, authority
        self.gold = GoldFixture(root)
        self.card = authority.card
        self.gold.cases["cases"][0]["expectations"] = []
        self.card["assertions"] = []
        for index, facet in enumerate(cert.FACETS):
            claim = copy.deepcopy(self.gold.claim)
            if facet != "identity":
                claim.update(pointer="/edition", value="literal-fixture-edition")
            self.gold.cases["cases"][0]["expectations"].append({
                "field": facet, "state": "value", "claims": [claim], "reason": "literal fixture evidence",
                "votes": [{"adjudicator_id": "judge-one", "disposition": "agree"},
                          {"adjudicator_id": "judge-two", "disposition": "agree"}],
            })
            if abstention and facet == "abstention":
                expectation = self.gold.cases["cases"][0]["expectations"][-1]
                expectation["state"] = "abstention"
                for vote in expectation["votes"]:
                    vote["disposition"] = "abstain"
            self.card["assertions"].append({
                "assertion_id": "wa_" + f"{index:024x}", "subject": {"kind": "card", "id": self.card["card_id"]},
                "field": facet, "value": None if abstention and facet == "abstention" else claim["value"],
                "value_norm": "literal fixture",
                "source_id": "fixture", "snapshot_id": "fixture-v1", "locator": claim["pointer"],
                "extraction_version": "fixture-v1", "extraction_confidence": "high",
                "producer": {"kind": "source_extract", "name": "fixture"}, "review": {"status": "none"},
                "licence_ref": {"register_source_id": "fixture", "register_version": 1}, "status": "active",
            })
        self.authority.approve(self.card)
        self.spec_path = root / "certification-spec.json"
        self.evaluation_path = root / "evaluation.json"
        self.card_path = root / "card.json"
        self.mechanics_path = root / "mechanics.json"
        self.spec = {
            "schema_version": "word-card-certification-spec.v1",
            "author": {"id": "code-author", "family": "author-family"},
            "evaluators": copy.deepcopy(self.gold.spec["roles"]["adjudicators"]),
            "projections": {facet: {"gold_field": facet, "card_pointer": f"/assertions/{index}/value"}
                            for index, facet in enumerate(cert.FACETS)},
            "cases": [{"case_id": "case-001", "card": write(self.card_path, self.card)}], "controls": [],
        }
        self.gold.spec["required_fields"] = list(cert.FACETS)
        self.spec["frozen"] = cert.frozen_artifact(cert.CertificationAuthority(), [self.card])
        self.gold.spec["assembler_build_sha256"] = self.spec["frozen"]["implementation_sha256"]
        self.gold.seal()
        self.gold.custody()
        self.gold.isolation["assembler_build_sha256"] = self.spec["frozen"]["implementation_sha256"]
        self.gold.save_custody()
        self.spec.update(gold_spec={"path": str(self.gold.spec_path), "sha256": self.gold.spec_sha},
                         gold_seal={"path": str(self.gold.bundle / "seal.json"),
                                    "sha256": gold.sha((self.gold.bundle / "seal.json").read_bytes())},
                         isolation={"path": str(self.gold.isolation_path), "sha256": self.gold.isolation_sha},
                         complete_data_receipt=self.gold.refs["complete_data_receipt"])
        self.mechanics = {
            "schema_version": "word-card-mechanics-acceptance.v1", "status": "MECHANICS_ACCEPTED",
            "frozen": self.spec["frozen"], "cards_sha256": cert.digest([self.card]),
            "accepted_by": {"id": "mechanics-reviewer", "family": "independent-family"},
            "evidence": [self.gold.opaque],
        }
        self.spec["mechanics_receipt"] = write(self.mechanics_path, self.mechanics)
        for index, name in enumerate(cert.CONTROL_FACETS):
            self.add_control(name, f"control-{index}")
        self.save_spec()
        self.make_evaluation()

    def add_control(self, name, key):
        card = copy.deepcopy(self.card)
        index = cert.FACETS.index(cert.CONTROL_FACETS[name])
        card["assertions"][index]["value"] = "planted source-free wrong value"
        self.spec["controls"].append({"control_id": key, "case_id": "case-001", "class": name,
                                      "card": write(self.root / f"{key}.json", card)})

    def save_spec(self):
        self.spec_sha = write(self.spec_path, self.spec)["sha256"]

    def make_evaluation(self):
        expectations = {row["field"]: row for row in self.gold.cases["cases"][0]["expectations"]}
        reports = []
        for actor in self.spec["evaluators"]:
            items = []
            for key, card, control in [*( (row["case_id"], json.loads(Path(row["card"]["path"]).read_bytes()), None)
                                         for row in self.spec["cases"]),
                                       *( (row["control_id"], json.loads(Path(row["card"]["path"]).read_bytes()), row["class"])
                                          for row in self.spec["controls"])]:
                scores = []
                for facet in cert.FACETS:
                    failed = control is not None and cert.CONTROL_FACETS[control] == facet
                    scores.append({"facet": facet, "verdict": "fail" if failed else "pass",
                                   "reason": "literal fixture inspection", "source_claims_sha256": cert.digest(expectations[facet]),
                                   "findings": [{"code": "material", "owner": "fixture-repair",
                                                 "dependency": "replace unsupported source claim", "evidence": self.gold.opaque}]
                                   if failed else []})
                items.append({"item_id": key, "card_sha256": cert.digest(card), "inspected_complete_card": True,
                              "scores": scores})
            reports.append({"evaluator_id": actor["id"], "items": items})
        self.evaluation = {"schema_version": "word-card-language-evaluation.v1", "spec_sha256": self.spec_sha,
                           "reports": reports}
        self.save_evaluation()

    def save_evaluation(self):
        self.evaluation_sha = write(self.evaluation_path, self.evaluation)["sha256"]

    def evaluate(self):
        return cert.evaluate_certification(self.spec_path, self.spec_sha, self.evaluation_path, self.evaluation_sha)

    def receipt(self):
        return write(self.root / "receipt.json", self.evaluate())

    def approve(self):
        self.authority.approve(self.card)
        self.authority.ledger["approved_reviews"][0]["certification_receipt"] = self.receipt()
        write(self.authority.ledger_path, self.authority.ledger)


@pytest.fixture
def packet(tmp_path, certification):
    root = tmp_path / "phase5"
    root.mkdir()
    return CertificationFixture(root, certification)


def test_exact_receipt_and_export(packet):
    result = packet.evaluate()
    assert result["status"] == "CERTIFIED"
    assert result["case_count"] == 1
    assert result["strata"] == {"ordinary-control": 1}
    assert result["scores"] == {facet: {"passed": 2, "denominator": 2} for facet in cert.FACETS}
    assert result["controls"] == {name: {"detected": 2, "denominator": 2} for name in cert.CONTROL_FACETS}
    assert result["findings"] == []
    assert cert.verify_certification_receipt(packet.receipt(), packet.root) == result
    packet.approve()
    assert cert.load_certified_card_for_export(packet.card) == packet.card


@pytest.mark.parametrize("gate", ["complete_data_receipt", "mechanics_receipt", "gold_spec", "gold_seal", "isolation"])
def test_missing_prerequisite_refused(packet, gate):
    Path(packet.spec[gate]["path"]).unlink()
    with pytest.raises((ValueError, OSError)):
        packet.evaluate()


@pytest.mark.parametrize("gate", ["complete_data_receipt", "mechanics_receipt", "gold_spec", "gold_seal", "isolation"])
def test_pinned_prerequisite_drift_refused(packet, gate):
    Path(packet.spec[gate]["path"]).chmod(0o600)
    Path(packet.spec[gate]["path"]).write_bytes(b"{}")
    with pytest.raises(ValueError):
        packet.evaluate()


@pytest.mark.parametrize("fault", ["self", "same-family", "duplicate", "qualification", "one-family"])
def test_independent_qualified_evaluators_required(packet, fault):
    actors = packet.spec["evaluators"]
    if fault == "self":
        actors[0]["id"] = "code-author"
    elif fault == "same-family":
        actors[0]["family"] = "author-family"
    elif fault == "duplicate":
        actors[1]["id"] = actors[0]["id"]
    elif fault == "one-family":
        actors[1]["family"] = actors[0]["family"]
    else:
        actors[0]["qualification"]["sha256"] = "b" * 64
    packet.save_spec()
    with pytest.raises(ValueError):
        packet.evaluate()


@pytest.mark.parametrize("facet", cert.FACETS)
def test_each_semantic_facet_can_block_with_owned_findings(packet, facet):
    score = next(item for item in packet.evaluation["reports"][0]["items"][0]["scores"] if item["facet"] == facet)
    score.update(verdict="fail", findings=[{"code": "invented_ukrainian" if facet == "source_fidelity" else "material",
                                           "owner": "source-owner", "dependency": "new authenticated source evidence",
                                           "evidence": packet.gold.opaque}])
    packet.save_evaluation()
    result = packet.evaluate()
    assert result["status"] == "FAILED"
    assert result["scores"][facet] == {"passed": 1, "denominator": 2}
    assert result["findings"][0]["findings"][0]["owner"] == "source-owner"
    with pytest.raises(ValueError, match="Failed or stale"):
        cert.verify_certification_receipt(packet.receipt(), packet.root)


@pytest.mark.parametrize("name", cert.CONTROL_FACETS)
def test_missed_control_blocks_even_when_literal_comparator_detects_it(packet, name):
    index = next(i + 1 for i, row in enumerate(packet.spec["controls"]) if row["class"] == name)
    facet = cert.CONTROL_FACETS[name]
    score = next(row for row in packet.evaluation["reports"][0]["items"][index]["scores"] if row["facet"] == facet)
    score.update(verdict="pass", findings=[])
    packet.save_evaluation()
    result = packet.evaluate()
    assert result["status"] == "FAILED"
    assert result["controls"][name] == {"detected": 1, "denominator": 2}
    assert result["findings"][0]["findings"][0]["dependency"] == "repair missed planted control"


@pytest.mark.parametrize("fault", ["implementation", "rules", "parser", "source", "overlay", "suppression",
                                 "permissions", "gold", "evaluation", "card", "receipt", "spec"])
def test_exact_artifact_changes_invalidate_receipt(packet, fault, monkeypatch):
    ref = packet.receipt()
    if fault in {"implementation", "parser"}:
        packet.authority.code.write_text("changed parser or implementation")
    elif fault == "rules":
        packet.authority.rules.write_text("changed rules")
    elif fault == "permissions":
        packet.authority.register.write_text("changed register")
    elif fault in {"source", "overlay", "suppression"}:
        category, name = {"source": ("S", "source"), "overlay": ("O", "overlay"),
                          "suppression": ("O", "suppressions")}[fault]
        packet.authority.snapshots[category, name].write_text("changed input")
    elif fault == "gold":
        path = packet.gold.bundle / "answers.json"
        path.chmod(0o600)
        path.write_bytes(b"{}")
    else:
        path = {"evaluation": packet.evaluation_path, "card": packet.card_path,
                "receipt": Path(ref["path"]), "spec": packet.spec_path}[fault]
        path.write_bytes(b"{}")
    with pytest.raises((ValueError, KeyError)):
        cert.verify_certification_receipt(ref, packet.root)


@pytest.mark.parametrize("fault", ["case", "item", "evaluator", "facet", "claim", "card-hash", "spec-hash", "inspection",
                                 "owner", "hidden-finding"])
def test_denominator_and_evidence_omissions_refused(packet, fault):
    report = packet.evaluation["reports"][0]
    score = report["items"][0]["scores"][0]
    if fault == "case":
        packet.spec["cases"].clear()
        packet.save_spec()
    elif fault == "item":
        report["items"].pop()
    elif fault == "evaluator":
        packet.evaluation["reports"].pop()
    elif fault == "facet":
        report["items"][0]["scores"].pop()
    elif fault == "claim":
        score["source_claims_sha256"] = "b" * 64
    elif fault == "card-hash":
        report["items"][0]["card_sha256"] = "b" * 64
    elif fault == "spec-hash":
        packet.evaluation["spec_sha256"] = "b" * 64
    elif fault == "inspection":
        report["items"][0]["inspected_complete_card"] = False
    elif fault == "owner":
        score.update(verdict="fail", findings=[])
    else:
        score["findings"] = [{"code": "wrong_identity", "owner": "repair", "dependency": "identity correction",
                               "evidence": packet.gold.opaque}]
    packet.save_evaluation()
    with pytest.raises(ValueError):
        packet.evaluate()


def test_legacy_approval_without_phase5_receipt_cannot_unlock_export(certification):
    with pytest.raises(cert.UncertifiedCardRefusal, match="invalid certification authority"):
        cert.load_certified_card_for_export(certification.card)


def test_inventory_caches_receipt_only_within_one_run(packet, monkeypatch):
    packet.approve()
    original = cert.evaluate_certification
    calls = []

    def counted(*args):
        calls.append(True)
        return original(*args)

    monkeypatch.setattr(cert, "evaluate_certification", counted)
    with cert.certification_run():
        assert cert.load_certified_card_for_export(packet.card) == packet.card
        assert cert.load_certified_card_for_export(packet.card) == packet.card
    assert len(calls) == 1
    packet.authority.rules.write_text("changed after earlier run")
    with pytest.raises(cert.UncertifiedCardRefusal):
        cert.load_certified_card_for_export(packet.card)


@pytest.mark.parametrize("fault", ["missing-class", "unchanged", "foreign", "unrelated-change", "duplicate-id"])
def test_invalid_controls_refused(packet, fault):
    control = packet.spec["controls"][0]
    if fault == "missing-class":
        packet.spec["controls"].pop()
    elif fault == "duplicate-id":
        control["control_id"] = "case-001"
    else:
        card = json.loads(Path(control["card"]["path"]).read_bytes())
        if fault == "unchanged":
            card = packet.card
        elif fault == "foreign":
            card["card_id"] = "wc_abcdef012345"
        else:
            card["key_at_creation"]["spelling"] = "unrelated change"
        control["card"] = write(Path(control["card"]["path"]), card)
    packet.save_spec()
    with pytest.raises(ValueError):
        packet.evaluate()


@pytest.mark.parametrize("fault", ["status", "frozen", "cards", "author", "family", "evidence"])
def test_mechanics_acceptance_not_a_status_string(packet, fault):
    if fault == "status":
        packet.mechanics["status"] = "mechanics_only_uncertified"
    elif fault == "frozen":
        packet.mechanics["frozen"] = {**packet.mechanics["frozen"], "rules_sha256": "b" * 64}
    elif fault == "cards":
        packet.mechanics["cards_sha256"] = "b" * 64
    elif fault == "author":
        packet.mechanics["accepted_by"]["id"] = "code-author"
    elif fault == "family":
        packet.mechanics["accepted_by"]["family"] = "author-family"
    else:
        packet.mechanics["evidence"][0] = {"path": "missing-independent-proof", "sha256": "b" * 64}
    packet.spec["mechanics_receipt"] = write(packet.mechanics_path, packet.mechanics)
    packet.save_spec()
    with pytest.raises((ValueError, OSError)):
        packet.evaluate()


@pytest.mark.parametrize("fault", ["raw-source", "accounting-output", "qualification", "custody"])
def test_transitive_evidence_replayed(packet, fault):
    if fault == "raw-source":
        packet.gold.source.raw.write_bytes(b"modified source capture")
    elif fault == "accounting-output":
        path = Path(packet.gold.refs["accounting_receipt"]["path"]).parent / "SRC-ULIF.json"
        path.write_bytes(b"{}")
    elif fault == "custody":
        packet.gold.isolation["access_log"][0]["allowed"] = True
        packet.gold.save_custody()
        packet.spec["isolation"]["sha256"] = packet.gold.isolation_sha
        packet.save_spec()
    else:
        Path(packet.gold.opaque["path"]).write_bytes(b"modified proof")
    with pytest.raises(ValueError):
        packet.evaluate()


@pytest.mark.parametrize("fault", ["spec", "evaluation", "receipt"])
def test_copied_status_cannot_certify(packet, fault):
    if fault == "spec":
        packet.spec["frozen"]["implementation_sha256"] = "b" * 64
        packet.save_spec()
        with pytest.raises(ValueError):
            packet.evaluate()
    elif fault == "evaluation":
        packet.evaluation = {"schema_version": "word-card-language-evaluation.v1", "status": "CERTIFIED"}
        packet.save_evaluation()
        with pytest.raises(ValueError):
            packet.evaluate()
    else:
        ref = write(packet.root / "forged.json", {"schema_version": "word-card-certification-receipt.v1", "status": "CERTIFIED"})
        with pytest.raises((ValueError, KeyError)):
            cert.verify_certification_receipt(ref, packet.root)


def test_summary_publishes_counts_and_receipt_digest_without_private_content(packet):
    ref = packet.receipt()
    summary = cert.certification_summary(ref, packet.root)
    assert summary == {"schema_version": "word-card-certification-summary.v1", "status": "CERTIFIED",
                       "receipt_sha256": ref["sha256"], "case_count": 1, "evaluator_count": 2,
                       "scores": {facet: {"passed": 2, "denominator": 2} for facet in cert.FACETS},
                       "controls": {name: {"detected": 2, "denominator": 2} for name in cert.CONTROL_FACETS},
                       "finding_count": 0, "finding_codes": {}}
    assert all(value not in json.dumps(summary) for value in (str(packet.root), "case-001", "judge-one", "fixture-key"))


def test_failed_summary_retains_material_finding_counts(packet):
    score = packet.evaluation["reports"][0]["items"][0]["scores"][0]
    score.update(verdict="fail", findings=[{"code": "wrong_identity", "owner": "source-repair",
                                           "dependency": "correct attachment", "evidence": packet.gold.opaque}])
    packet.save_evaluation()
    summary = cert.certification_summary(packet.receipt(), packet.root)
    assert summary["status"] == "FAILED"
    assert summary["finding_count"] == 1
    assert summary["finding_codes"] == {"wrong_identity": 1}


def test_receipt_cannot_unlock_an_unevaluated_card(packet):
    packet.approve()
    other = copy.deepcopy(packet.card)
    other["card_id"] = "wc_abcdef012345"
    packet.authority.approve(other)
    packet.authority.ledger["approved_reviews"][-1]["certification_receipt"] = packet.receipt()
    write(packet.authority.ledger_path, packet.authority.ledger)
    with pytest.raises(cert.UncertifiedCardRefusal, match="outside exact-artifact"):
        cert.load_certified_card_for_export(other)


@pytest.mark.parametrize("fault", ["duplicate-item", "duplicate-facet", "duplicate-case", "missing-gold-field",
                                 "shared-projection", "shared-gold-field", "unscored-gold-field"])
def test_no_reduced_or_duplicated_denominators(packet, fault):
    if fault == "duplicate-item":
        row = copy.deepcopy(packet.evaluation["reports"][0]["items"][0])
        row["card_sha256"] = "b" * 64
        packet.evaluation["reports"][0]["items"].append(row)
    elif fault == "duplicate-facet":
        row = copy.deepcopy(packet.evaluation["reports"][0]["items"][0]["scores"][0])
        row["reason"] = "duplicate score"
        packet.evaluation["reports"][0]["items"][0]["scores"].append(row)
    elif fault == "duplicate-case":
        packet.spec["cases"].append(copy.deepcopy(packet.spec["cases"][0]))
    elif fault == "missing-gold-field":
        packet.spec["projections"]["stress"]["gold_field"] = "absent"
    elif fault == "shared-projection":
        packet.spec["projections"]["stress"]["card_pointer"] = packet.spec["projections"]["identity"]["card_pointer"]
    elif fault == "shared-gold-field":
        packet.spec["projections"]["stress"]["gold_field"] = "identity"
    else:
        packet.spec["projections"]["abstention"]["gold_field"] = "unscored"
    packet.save_spec()
    packet.evaluation["spec_sha256"] = packet.spec_sha
    packet.save_evaluation()
    with pytest.raises(ValueError):
        packet.evaluate()


def test_source_projection_mismatch_is_zero_tolerance_even_when_judges_pass(packet):
    packet.card["assertions"][1]["value"] = "invented fixture claim"
    packet.authority.approve(packet.card)
    packet.spec["cases"][0]["card"] = write(packet.card_path, packet.card)
    packet.mechanics["cards_sha256"] = cert.digest([packet.card])
    packet.spec["mechanics_receipt"] = write(packet.mechanics_path, packet.mechanics)
    # Keep controls derived from the same baseline, so this isolates an ordinary-case failure.
    for row in packet.spec["controls"]:
        card = copy.deepcopy(packet.card)
        index = cert.FACETS.index(cert.CONTROL_FACETS[row["class"]])
        card["assertions"][index]["value"] = "planted source-free wrong value"
        row["card"] = write(Path(row["card"]["path"]), card)
    packet.save_spec()
    packet.make_evaluation()
    result = packet.evaluate()
    assert result["status"] == "FAILED"
    assert result["scores"]["sense_binding"] == {"passed": 0, "denominator": 2}
    assert all(row["findings"][0]["owner"] == "open-model-data" for row in result["findings"])


def test_appropriate_abstention_preserves_missing_value(tmp_path, certification):
    root = tmp_path / "abstention"
    root.mkdir()
    packet = CertificationFixture(root, certification, abstention=True)
    assert packet.card["assertions"][-1]["value"] is None
    assert packet.evaluate()["scores"]["abstention"] == {"passed": 2, "denominator": 2}
    assert packet.evaluate()["status"] == "CERTIFIED"


@pytest.mark.parametrize("fault", ["version", "schema", "empty-sources", "missing-vesum", "missing-overlay",
                                 "stale-normaliser", "stale-rules", "stale-register"])
def test_frozen_inputs_fail_closed(packet, fault):
    card = copy.deepcopy(packet.card)
    inputs = card["build"]["inputs"]
    if fault == "version":
        card["build"]["card_version"] = "cv_" + "a" * 24
    elif fault == "schema":
        card["schema_version"] = "unknown"
    elif fault == "empty-sources":
        inputs["S"] = {}
    elif fault == "missing-vesum":
        inputs["V"]["other"] = inputs["V"].pop("vesum")
        packet.authority.ledger["snapshot_bindings"]["V"]["other"] = packet.authority.ledger["snapshot_bindings"]["V"]["vesum"]
        write(packet.authority.ledger_path, packet.authority.ledger)
    elif fault == "missing-overlay":
        inputs["O"].pop("overlay")
    elif fault == "stale-normaliser":
        inputs["R"]["normaliser"]["version"] = "changed"
    elif fault == "stale-rules":
        inputs["R"]["rules"]["version"] = "changed"
    else:
        inputs["R"]["register"]["content_sha256"] = "b" * 64
    with pytest.raises(ValueError):
        cert.frozen_artifact(cert.CertificationAuthority(), [card])


@pytest.mark.parametrize("raw", [b'{"status":1,"status":2}', b'{"unused":NaN}', b'{"unused":"\\ud800"}'])
def test_certification_uses_strict_json_reader(packet, raw):
    packet.spec_path.write_bytes(raw)
    packet.spec_sha = gold.sha(raw)
    with pytest.raises(ValueError):
        packet.evaluate()


@pytest.mark.parametrize("replacement", [True, 1.0])
def test_receipt_replay_is_type_exact(packet, replacement):
    receipt = packet.evaluate()
    receipt["case_count"] = replacement
    ref = write(packet.root / "type-forged-receipt.json", receipt)
    with pytest.raises(ValueError, match="Failed or stale"):
        cert.verify_certification_receipt(ref, packet.root)
    with pytest.raises(ValueError, match="Stale evaluation summary"):
        cert.certification_summary(ref, packet.root)


def test_control_cannot_hide_unrelated_numeric_type_change(packet):
    control = packet.spec["controls"][0]
    card = json.loads(Path(control["card"]["path"]).read_bytes())
    # Values allow any JSON type; Python equality treats integer 1 and float 1.0 as equal.
    packet.card["assertions"][-1]["value"] = 1
    card["assertions"][-1]["value"] = 1.0
    packet.authority.approve(packet.card)
    packet.spec["cases"][0]["card"] = write(packet.card_path, packet.card)
    packet.mechanics["cards_sha256"] = cert.digest([packet.card])
    packet.spec["mechanics_receipt"] = write(packet.mechanics_path, packet.mechanics)
    control["card"] = write(Path(control["card"]["path"]), card)
    packet.save_spec()
    with pytest.raises(ValueError, match="alter only its target facet"):
        packet.evaluate()
