from __future__ import annotations

from pathlib import Path

from scripts.audit import llm_qg_store, qg_tier2_disarm, qg_workflow


def _write_module(tmp_path: Path) -> Path:
    module_dir = tmp_path / "b1" / "disarm-module"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("# Модуль\n\nКороткий текст.\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "resources.yaml").write_text("[]\n", encoding="utf-8")
    return module_dir


def test_disarm_helper_invalidates_only_requested_gate_version(tmp_path: Path) -> None:
    module_dir = _write_module(tmp_path)
    db_path = tmp_path / "qg.db"
    payload = qg_workflow._payload_from_findings([])

    llm_qg_store.record_llm_qg(
        level="b1",
        slug="disarm-module",
        module_dir=module_dir,
        payload=payload,
        gate_version="qg_workflow.v2",
        reviewer_model="test-reviewer",
        path=db_path,
    )
    llm_qg_store.record_llm_qg(
        level="b1",
        slug="disarm-module",
        module_dir=module_dir,
        payload=payload,
        gate_version=qg_workflow.DEFAULT_GATE_VERSION,
        reviewer_model="test-reviewer",
        path=db_path,
    )

    deleted = qg_tier2_disarm.invalidate_gate_version_cache(
        db_path=db_path,
        gate_version=qg_workflow.DEFAULT_GATE_VERSION,
    )

    assert deleted == 1
    assert (
        llm_qg_store.latest_llm_qg(
            "b1",
            "disarm-module",
            gate_version=qg_workflow.DEFAULT_GATE_VERSION,
            path=db_path,
        )
        is None
    )
    assert (
        llm_qg_store.latest_llm_qg(
            "b1",
            "disarm-module",
            gate_version="qg_workflow.v2",
            path=db_path,
        )
        is not None
    )
