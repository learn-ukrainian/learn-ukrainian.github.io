"""Fail-closed tests for the audited Literary Poltava executable entry points."""

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

WORKTREE_ROOT = Path(__file__).parents[1]
CANDIDATE_JSONL = (
    WORKTREE_ROOT
    / "data/datasets/hramatka_literary_poltava_v1/hramatka_literary_poltava_v1.jsonl"
)
CANDIDATE_README = WORKTREE_ROOT / "data/datasets/hramatka_literary_poltava_v1/README.md"
EXPECTED_CANDIDATE_SHA256 = "06923700a0f5a6bbb077221325b8b7cc2b5e0a094100569494af32acd52c3424"
EXPECTED_README_SHA256 = "148bcab45f02790bbe5cb012ad5e9d96babb2ef3b452cab07677345b997b45b0"


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, WORKTREE_ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


EXPORTER = load_module("literary_exporter", "scripts/dataset/export_literary_poltava_dataset.py")
TRAINER = load_module("literary_trainer", "scripts/dataset/train_gemma_huggingface.py")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_exporter_refuses_before_database_or_output_access(monkeypatch: pytest.MonkeyPatch) -> None:
    before = (sha256(CANDIDATE_JSONL), sha256(CANDIDATE_README))
    with monkeypatch.context() as guarded:
        guarded.setattr(Path, "mkdir", pytest.fail)
        guarded.setattr(Path, "open", pytest.fail)
        guarded.setattr(Path, "write_text", pytest.fail)
        with pytest.raises(EXPORTER.LiteraryCandidateSafetyError, match=r"#6058.*rebuild_required"):
            EXPORTER.export_literary_dataset()
    assert before == (EXPECTED_CANDIDATE_SHA256, EXPECTED_README_SHA256)
    assert before == (sha256(CANDIDATE_JSONL), sha256(CANDIDATE_README))


def test_training_refuses_candidate_before_loading_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    before = (sha256(CANDIDATE_JSONL), sha256(CANDIDATE_README))
    monkeypatch.setattr(sys, "argv", ["train_gemma_huggingface.py"])
    with pytest.raises(TRAINER.LiteraryCandidateSafetyError, match=r"#6058.*rebuild_required"):
        TRAINER.train()
    assert before == (sha256(CANDIDATE_JSONL), sha256(CANDIDATE_README))


def test_explicit_unrelated_dataset_is_not_reclassified(tmp_path: Path) -> None:
    unrelated = tmp_path / "hramatka_literary_poltava_v1.jsonl"
    unrelated.write_text('{"text": "safe test fixture"}\n', encoding="utf-8")
    assert TRAINER.refuse_rebuild_required_candidate(str(unrelated)) == unrelated.resolve()
