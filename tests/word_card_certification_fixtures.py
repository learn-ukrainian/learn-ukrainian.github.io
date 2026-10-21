"""Temporary synthetic authority. Never writes to repository review evidence."""

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.atlas import word_card_certification as cert
from scripts.atlas import word_card_golden_set as gold
from tests.test_word_card_golden_set import GoldFixture, write


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def dataset_files(card):
    metadata = {"version": "synthetic", "certified": True, "export_eligible": True, "draft_engineering": False}
    return metadata, [
        *({"path": path, "content": "Fixture attribution\n"} for path in ("README.md", "NOTICE.md", "ATTRIBUTION.md")),
        {"path": "dataset/_metadata.json", "content": json.dumps(metadata)},
        {"path": "dataset/default.jsonl", "content": json.dumps(card, ensure_ascii=False) + "\n"},
    ]


@pytest.fixture(name="certification")
def certification_fixture(tmp_path, monkeypatch):
    root = tmp_path / "authority"
    root.mkdir()
    schema = root / "schema.json"
    schema.write_bytes(cert.SCHEMA_PATH.read_bytes())
    code, rules, register = (root / name for name in ("implementation.py", "rules.md", "permissions.yaml"))
    code.write_text("synthetic implementation v1\n")
    rules.write_text("synthetic rules v1\n")
    register.write_text("synthetic permissions v1\n")
    ledger_path = root / "reviews.json"
    monkeypatch.setattr(cert, "PROJECT_ROOT", root)
    monkeypatch.setattr(cert, "SCHEMA_PATH", schema)
    monkeypatch.setattr(cert, "REVIEW_EVIDENCE_PATH", ledger_path)
    monkeypatch.setattr(cert, "PERMISSIONS_REGISTER_PATH", register)
    monkeypatch.setattr(cert, "IMPLEMENTATION_PATHS", (code,))
    monkeypatch.setattr(cert, "RULE_PATHS", (rules, schema))
    bindings, inputs, snapshots = {}, {}, {}
    for category, names in {"S": ["source"], "V": ["vesum"], "I": ["registry"],
                            "O": ["overlay", "suppressions"]}.items():
        bindings[category], inputs[category] = {}, {}
        for name in names:
            path = root / f"{category}-{name}.json"
            path.write_text('{"fixture":"original"}\n')
            snapshots[category, name] = path
            bindings[category][name] = {"path": path.name}
            inputs[category][name] = {"ref": path.name, "content_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    inputs["R"] = {"rules": {"ref": "rules.md", "version": "rules-v1"}, "normaliser": {"ref": "normaliser", "version": "norm-v1"},
                   "register": {"ref": "permissions.yaml", "content_sha256": hashlib.sha256(register.read_bytes()).hexdigest()}}
    card = {
        "schema_version": "1", "card_id": "wc_0123456789ab", "card_kind": "lexeme", "state": "active",
        "merged_into": None,
        "key_at_creation": {"spelling": "fixture", "pos": "noun"},
        "identity": {"confidence": "high", "method": "unique_match", "source_keys": []},
        "senses": [], "links": [], "fields": {}, "assertions": [],
        "quality": {"identity_confidence": "high", "linguistic_review": {
            "status": "reviewed", "record": "synthetic-only", "lane": "fixture",
            "approved_for": ["site", "dataset"]}, "practice_eligibility": []},
        "build": {"build_id": "synthetic", "rules_version": "rules-v1", "inputs": inputs},
    }
    card["build"]["card_version"] = "cv_" + sha({k: v for k, v in card.items() if k != "build"})[:24]
    ledger = {"schema_version": "word-card-review-evidence.v1", "snapshot_bindings": bindings,
              "approved_reviews": []}

    def approve_review(value):
        value["build"]["card_version"] = "cv_" + sha({k: v for k, v in value.items() if k != "build"})[:24]
        ledger["approved_reviews"] = [r for r in ledger["approved_reviews"] if r["card_id"] != value["card_id"]]
        ledger["approved_reviews"].append({
            "card_id": value["card_id"], "record": "synthetic-only", "lane": "fixture", "status": "active",
            "approved_for": ["dataset", "site"], "card_version": value["build"]["card_version"],
            "build_sha256": sha(value["build"]),
            "implementation_sha256": sha({code.name: hashlib.sha256(code.read_bytes()).hexdigest()}),
            "rules_sha256": sha({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (rules, schema)}),
        })
        ledger_path.write_text(json.dumps(ledger))

    authority = SimpleNamespace(card=card, ledger=ledger, ledger_path=ledger_path, root=root,
                                code=code, rules=rules, register=register, snapshots=snapshots,
                                approve_review=approve_review)

    def approve(value):
        approve_review(value)
        # Negative controls deliberately approve malformed or stale cards at the legacy gate.
        try:
            cert.frozen_artifact(cert.CertificationAuthority(), [value])
        except ValueError:
            return
        packet_root = root / f"phase5-{len(list(root.glob('phase5-*')))}"
        packet_root.mkdir()
        packet = CertificationFixture(packet_root, SimpleNamespace(card=value, approve_review=approve_review),
                                      populate_card=False)
        ledger["approved_reviews"][-1]["certification_receipt"] = packet.receipt()
        write(ledger_path, ledger)

    authority.approve = approve
    approve(card)
    return authority


class CertificationFixture:
    def __init__(self, root, authority, abstention=False, *, populate_card=True):
        self.root, self.authority = root, authority
        self.gold = GoldFixture(root)
        self.card = authority.card
        self.gold.cases["cases"][0]["expectations"] = []
        if populate_card:
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
        else:
            self.prepare_export_expectations()
        self.authority.approve_review(self.card)
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
        if not populate_card:
            self.spec["projections"] = {
                facet: {"gold_field": "identity" if facet == "abstention" else "synthetic_" + facet,
                        "card_pointer": pointer}
                for facet, pointer in zip(cert.FACETS, self.export_pointers, strict=True)
            }
        self.gold.spec["required_fields"] = [row["gold_field"] for row in self.spec["projections"].values()]
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

    def prepare_export_expectations(self):
        """Bind arbitrary export cards to source-free evidence without altering them."""
        self.export_pointers = (
            "/key_at_creation/spelling", "/schema_version", "/key_at_creation/pos",
            "/build/build_id", "/build/rules_version", "/merged_into",
        )
        values = {facet: gold.pointer_value(self.card, pointer)
                  for facet, pointer in zip(cert.FACETS, self.export_pointers, strict=True)}
        reference = write(self.root / "evidence" / "synthetic-projections.json", values)
        record = self.gold.source.docs["stage_evidence"]["records"][0]
        record["evidence"].append({**reference, "schema_version": "synthetic-projections.v1",
                                   "locator": "fixture:projections"})
        self.gold.source.save()
        self.gold.refs["stage_evidence"] = write(self.gold.source.paths["stage_evidence"],
                                                 self.gold.source.docs["stage_evidence"])
        self.gold.refresh_accounting()
        for facet, value in values.items():
            claim = {**copy.deepcopy(self.gold.claim), "reference": reference,
                     "pointer": "/" + facet, "value": value}
            if facet == "abstention":
                claim = copy.deepcopy(self.gold.claim)
            self.gold.cases["cases"][0]["expectations"].append({
                "field": "identity" if facet == "abstention" else "synthetic_" + facet,
                "state": "abstention" if facet == "abstention" else "value", "claims": [claim],
                "reason": "source-free export fixture, never linguistic evidence",
                "votes": [{"adjudicator_id": actor, "disposition": "abstain" if facet == "abstention" else "agree"}
                          for actor in ("judge-one", "judge-two")],
            })

    def add_control(self, name, key):
        card = copy.deepcopy(self.card)
        pointer = self.spec["projections"][cert.CONTROL_FACETS[name]]["card_pointer"]
        parent_pointer, _, leaf = pointer.rpartition("/")
        parent = gold.pointer_value(card, parent_pointer)
        parent[int(leaf) if isinstance(parent, list) else leaf] = "planted source-free wrong value"
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
                                   "reason": "literal fixture inspection", "source_claims_sha256": cert.digest(expectations[self.spec["projections"][facet]["gold_field"]]),
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
        self.authority.approve_review(self.card)
        self.authority.ledger["approved_reviews"][0]["certification_receipt"] = self.receipt()
        write(self.authority.ledger_path, self.authority.ledger)
