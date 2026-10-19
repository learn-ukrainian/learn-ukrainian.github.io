"""Temporary synthetic authority. Never writes to repository review evidence."""

import hashlib
import json
from types import SimpleNamespace

import pytest

from scripts.atlas import word_card_certification as certification_mod


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
    schema.write_bytes(certification_mod.SCHEMA_PATH.read_bytes())
    code, rules, register = (root / name for name in ("implementation.py", "rules.md", "permissions.yaml"))
    code.write_text("synthetic implementation v1\n")
    rules.write_text("synthetic rules v1\n")
    register.write_text("synthetic permissions v1\n")
    ledger_path = root / "reviews.json"
    monkeypatch.setattr(certification_mod, "PROJECT_ROOT", root)
    monkeypatch.setattr(certification_mod, "SCHEMA_PATH", schema)
    monkeypatch.setattr(certification_mod, "REVIEW_EVIDENCE_PATH", ledger_path)
    monkeypatch.setattr(certification_mod, "PERMISSIONS_REGISTER_PATH", register)
    monkeypatch.setattr(certification_mod, "IMPLEMENTATION_PATHS", (code,))
    monkeypatch.setattr(certification_mod, "RULE_PATHS", (rules, schema))
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

    def approve(value):
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

    approve(card)
    return SimpleNamespace(card=card, ledger=ledger, ledger_path=ledger_path, root=root,
                           code=code, rules=rules, register=register, snapshots=snapshots, approve=approve)
