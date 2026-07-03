from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.audit.llm_qg_store import (
    current_payload_for_module,
    latest_llm_qg,
    record_llm_qg,
)


def _module(tmp_path: Path) -> Path:
    module_dir = tmp_path / "b1" / "aspect-in-imperatives"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("## Тест\n\nЧекайте на номер.\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    return module_dir


def _payload(score: float = 7.5) -> dict:
    return {
        "aggregate": {
            "verdict": "REVISE",
            "terminal_verdict": "PASS",
            "min_score": score,
            "min_dim": "naturalness",
            "failing_dims": ["naturalness"],
            "warning_dims": ["naturalness"],
        },
        "dimensions": {
            "naturalness": {
                "score": score,
                "verdict": "REVISE",
                "evidence": '"Чекайте номер"',
                "findings": [
                    {
                        "category": "government",
                        "severity": "warning",
                        "quote": "Чекайте номер",
                        "replacement": "Чекайте на номер",
                    }
                ],
            }
        },
    }


def test_record_and_read_current_llm_qg(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    db_path = tmp_path / "qg.db"

    stored = record_llm_qg(
        level="B1",
        slug="aspect-in-imperatives",
        module_dir=module_dir,
        payload=_payload(),
        gate_version="test.v1",
        reviewer_model="review-model",
        reviewer_family="reviewer-tools",
        source="test",
        path=db_path,
    )
    current = current_payload_for_module("b1", "aspect-in-imperatives", module_dir, path=db_path)

    assert stored.level == "b1"
    assert current is not None
    assert current["aggregate"]["min_dim"] == "naturalness"
    assert current["_store"]["gate_version"] == "test.v1"

    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT count(*) FROM llm_qg_findings").fetchone()[0]
    assert count == 1


def test_findings_index_uses_issue_id_when_category_is_absent(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    db_path = tmp_path / "qg.db"
    payload = _payload()
    payload["dimensions"]["naturalness"]["findings"] = [
        {
            "issue_id": "UNNATURAL_ANTHROPOMORPHISM",
            "severity": "high",
            "quote": "Застереження каже",
        }
    ]

    record_llm_qg(
        level="b1",
        slug="aspect-in-imperatives",
        module_dir=module_dir,
        payload=payload,
        gate_version="test.v1",
        path=db_path,
    )

    with sqlite3.connect(db_path) as conn:
        category = conn.execute("SELECT category FROM llm_qg_findings").fetchone()[0]
    assert category == "UNNATURAL_ANTHROPOMORPHISM"


def test_current_llm_qg_is_hash_bound_to_module_content(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    db_path = tmp_path / "qg.db"

    record_llm_qg(
        level="b1",
        slug="aspect-in-imperatives",
        module_dir=module_dir,
        payload=_payload(),
        gate_version="test.v1",
        path=db_path,
    )
    (module_dir / "module.md").write_text("## Тест\n\nЧекайте на свій номер.\n", encoding="utf-8")

    assert current_payload_for_module("b1", "aspect-in-imperatives", module_dir, path=db_path) is None
    assert latest_llm_qg("b1", "aspect-in-imperatives", path=db_path) is not None
