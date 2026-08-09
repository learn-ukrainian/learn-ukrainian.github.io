"""Behavior proof for the all-family Phase 3 evaluation partition."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_evaluation_freeze as freeze
from scripts.projects.open_model_data import phase3_near_duplicate as near

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data/projects/open_model_data/contracts/phase3_evaluation_freeze_bundle_v1.schema.json"


def _text(family: str, ordinal: int) -> str:
    return " ".join(f"слово{family.replace('_', '')}{ordinal}а{token}" for token in range(24)) + ". Кінець."


def _rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family, count in freeze.TOTALS.items():
        for ordinal in range(count):
            if family == freeze.SCHOOL:
                document = f"doc.school.{ordinal % 168}"
            elif family == freeze.UA_GEC:
                document = f"doc.ua.{ordinal}"
            elif family == "calque_inventory":
                document = f"doc.calque.{ordinal % 3}"
            else:
                document = f"doc.{family}"
            text = _text(family, ordinal)
            record: dict[str, object] = {"text": text}
            if family == freeze.UA_GEC:
                record["partition"] = f"layer/{'test' if ordinal < 1159 else 'train'}"
            rows.append(
                {
                    "family_id": family,
                    "unit_id": f"unit.{family}.{ordinal}",
                    "unit_sha256": freeze.sha256_value([family, ordinal]),
                    "frozen_locator": {"kind": "fixture", "ordinal": ordinal},
                    "frozen_locator_sha256": freeze.sha256_value(["locator", family, ordinal]),
                    "document_or_edition_identity": document,
                    "source_text": text,
                    "source_record": record,
                    "source_text_sha256": freeze.sha256_bytes(text.encode("utf-8")),
                }
            )
    return rows


def _empty_external() -> dict[str, object]:
    return {
        "documents": set(),
        "units": set(),
        "exact": set(),
        "surfaces": [],
        "fingerprints": [],
        "token_index": {},
        "policy": near.policy_for_governed_use("ua_eval_exclusion"),
    }


def test_full_denominator_partition_is_label_blind_exact_and_share_bounded() -> None:
    rows = _rows()
    exposed = {("unit.ua_gec.0", freeze.sha256_value([freeze.UA_GEC, 0]))}
    result = freeze.partition(
        rows,
        cycle="phase3-v2-1-evaluation-cycle-001",
        exposed=exposed,
        external_index=_empty_external(),
    )
    assert sum(len(result[key]) for key in ("partition_rows", "clearance_rows", "quarantine_rows")) == 67041
    assert result["clean_candidate_count"] == 2000
    assert result["family_counts"][freeze.UA_GEC]["sealed_evaluation"] == 1158
    assert result["family_counts"]["antonenko_textbook_representation"]["sealed_evaluation"] == 0
    assert result["family_counts"]["other_normative_style_inventory"]["sealed_evaluation"] == 0
    for counts in result["family_counts"].values():
        assert counts["sealed_evaluation"] <= counts["family_total"] // 5
        assert counts["sealed_evaluation"] + counts["author_cleared"] + counts["quarantined"] == counts["family_total"]
    all_private_rows = [*result["partition_rows"], *result["clearance_rows"], *result["quarantine_rows"]]
    assert all("source_text" not in row and "source_record" not in row and "frozen_locator" not in row for row in all_private_rows)
    assert any(row["reason"] == "prior_exposure" and row["unit_id"] == "unit.ua_gec.0" for row in result["quarantine_rows"])


def test_heldout_neighbour_firewall_detects_exact_and_near_but_not_unrelated() -> None:
    sealed = [{"source_text": "питомий український вислів для точної перевірки"}]
    index = freeze._surface_index(sealed)
    assert freeze._heldout_neighbour({"source_text": sealed[0]["source_text"]}, index) is True
    assert freeze._heldout_neighbour(
        {"source_text": "питомий український вислів для точної перевірки!"}, index
    ) is True
    assert freeze._heldout_neighbour(
        {"source_text": "цілком інший матеріал без спільного формулювання"}, index
    ) is False


def test_public_schema_is_closed_and_contains_no_private_identity_fields() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    serialized = json.dumps(schema, ensure_ascii=False)
    assert "source_text" not in serialized
    assert "source_record" not in serialized
    assert "unit_id" not in serialized
    assert "document_or_edition_identity" not in serialized
    assert schema["additionalProperties"] is False
