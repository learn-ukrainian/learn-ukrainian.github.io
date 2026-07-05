"""Tests for the #4364 contested-calque sidecar flagger.

The flagger delegates attestation to the canonical
``scripts.lexicon.heritage_classifier`` (its correctness is covered by its own
suite); these tests cover the flagger's RULE mapping and sidecar mechanics
with an injected classifier stub — no real 1GB databases.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.audit.flag_contested_calque_gold import contested_entry, process_fixture

NATIVE_STATUS: dict[str, Any] = {
    "classification": "standard",
    "attestations": [
        {"source": "VESUM", "ref": "вішалка", "detail": "word_form match (1 form analysis)"}
    ],
    "is_russianism": False,
    "russian_shadow": False,
    "calque_warning": None,
}

SHADOW_STATUS: dict[str, Any] = {
    "classification": "unknown",
    "attestations": [],
    "is_russianism": False,
    "russian_shadow": True,
    "calque_warning": {"replacement": "вгору"},
}


def _stub_classifier(mapping: dict[str, dict[str, Any]]):
    def classify(form: str, *, db_path=None, vesum_db_path=None) -> dict[str, Any]:
        return mapping[form]

    return classify


def _write_gold(tmp_path: Path) -> Path:
    gold = {
        "items": [
            {"id": "g-001", "tag": "F/Calque", "error": "вішалкою", "correction": "вішаком"},
            {"id": "g-002", "tag": "F/Calque", "error": "запрокинув", "correction": "закинув"},
            {"id": "g-003", "tag": "F/Calque", "error": "пронзаючими очами", "correction": "х"},
            {"id": "g-004", "tag": "G/Case", "error": "чогось", "correction": "чогось"},
        ]
    }
    path = tmp_path / "gold.json"
    path.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_rule_mapping_native_contested_shadow_not(tmp_path: Path) -> None:
    gold_path = _write_gold(tmp_path)
    before = gold_path.read_bytes()

    sidecar = process_fixture(
        gold_path,
        classify=_stub_classifier({"вішалкою": NATIVE_STATUS, "запрокинув": SHADOW_STATUS}),
    )

    # Attested-native form → contested, evidence carried from the classifier.
    assert sidecar["g-001"]["contested"] is True
    assert sidecar["g-001"]["basis"] == "heritage_classifier"
    assert sidecar["g-001"]["evidence"] == [
        {"source": "VESUM", "ref": "вішалка", "detail": "word_form match (1 form analysis)"}
    ]
    # Russian-shadow + calque-warning form → not contested.
    assert sidecar["g-002"]["contested"] is False
    assert sidecar["g-002"]["russian_shadow"] is True
    assert sidecar["g-002"]["calque_warning"] is True
    # Multi-word error forms are never evaluated.
    assert sidecar["g-003"] == {
        "contested": False,
        "basis": "multiword_not_evaluated",
        "evidence": [],
    }
    # Non-F/Calque items get a complete-mapping entry, never a classifier call.
    assert sidecar["g-004"] == {
        "contested": False,
        "basis": "non_calque_tag",
        "evidence": [],
    }
    # Gold file byte-unchanged.
    assert gold_path.read_bytes() == before


def test_contested_requires_all_four_conditions() -> None:
    assert contested_entry(dict(NATIVE_STATUS))["contested"] is True
    for override in (
        {"classification": "unknown"},
        {"is_russianism": True},
        {"russian_shadow": True},
        {"calque_warning": {"replacement": "x"}},
    ):
        status = {**NATIVE_STATUS, **override}
        assert contested_entry(status)["contested"] is False, override


def test_sidecar_idempotent_and_stably_ordered(tmp_path: Path) -> None:
    gold_path = _write_gold(tmp_path)
    classify = _stub_classifier({"вішалкою": NATIVE_STATUS, "запрокинув": SHADOW_STATUS})

    first = process_fixture(gold_path, classify=classify)
    second = process_fixture(gold_path, classify=classify)

    assert list(first.keys()) == sorted(first.keys())
    assert json.dumps(first, ensure_ascii=False, sort_keys=True) == json.dumps(
        second, ensure_ascii=False, sort_keys=True
    )


def test_evidence_is_sorted_for_byte_identical_reruns() -> None:
    status = {
        **NATIVE_STATUS,
        "attestations": [
            {"source": "grinchenko", "ref": "б", "detail": ""},
            {"source": "VESUM", "ref": "а", "detail": ""},
            {"source": "VESUM", "ref": "a", "detail": ""},
        ],
    }
    evidence = contested_entry(status)["evidence"]
    assert evidence == sorted(evidence, key=lambda ev: (ev["source"], ev["ref"], ev["detail"]))
