"""The practice engines use an explicitly passed VESUM path and report it when missing."""

from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

import pytest

ENGINES = {
    "adjective": "generate_deck",
    "adverb": "build_canonical_adverb_cards",
    "numeral": "build_canonical_numeral_cards",
    "verb": "build_canonical_verb_cards",
}
PATH_CONSUMERS = {"find_vesum_db", "verify_deck_with_vesum", "verify_distractors_with_vesum"}
REPO_ROOT = Path(__file__).resolve().parents[1]


def _engine(name: str):
    return importlib.import_module(f"scripts.practice.{name}_mechanics_engine")


def _verifiers(module) -> list:
    return [getattr(module, fn) for fn in sorted(PATH_CONSUMERS - {"find_vesum_db"}) if hasattr(module, fn)]


@pytest.mark.parametrize("name", sorted(ENGINES))
def test_find_vesum_db_returns_explicit_path_even_when_missing(name: str, tmp_path: Path) -> None:
    missing = tmp_path / "absent.db"
    assert _engine(name).find_vesum_db(missing) == missing


@pytest.mark.parametrize("name", sorted(ENGINES))
def test_missing_explicit_path_is_reported_not_verified(name: str, tmp_path: Path) -> None:
    module = _engine(name)
    cards = getattr(module, ENGINES[name])()
    missing = tmp_path / "absent.db"
    for verify in _verifiers(module):
        result = verify(cards, missing)
        assert result.get("verified") is not True
        assert result.get("vesum_verified") is not True
        diagnostic = " ".join(str(result.get(key, "")) for key in ("error", "message", "reason"))
        assert str(missing) in diagnostic, verify.__name__


@pytest.mark.parametrize("name", sorted(ENGINES))
def test_every_call_site_passes_a_path(name: str) -> None:
    source = REPO_ROOT / "scripts" / "practice" / f"{name}_mechanics_engine.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in PATH_CONSUMERS
    ]
    assert calls
    for call in calls:
        minimum = 1 if call.func.id == "find_vesum_db" else 2
        assert len(call.args) + len(call.keywords) >= minimum, f"{call.func.id} at line {call.lineno}"


@pytest.mark.parametrize("name", sorted(ENGINES))
def test_primary_checkout_vesum_is_found_from_nested_worktree(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A database present only in the primary checkout is found from a nested linked worktree."""
    from scripts.storage import topology

    module = _engine(name)
    primary = tmp_path / "primary"
    (primary / ".git" / "worktrees" / "task").mkdir(parents=True)
    worktree = primary / ".worktrees" / "dispatch" / "agent" / "task"
    (worktree / "scripts").mkdir(parents=True)
    (worktree / "AGENTS.md").write_text("", encoding="utf-8")
    (worktree / ".git").write_text(f"gitdir: {primary / '.git' / 'worktrees' / 'task'}\n", encoding="utf-8")
    vesum = primary / "data" / "vesum.db"
    vesum.parent.mkdir(parents=True)
    vesum.write_bytes(b"0" * 1_000_001)  # passes every engine's size gate
    monkeypatch.delenv(topology.ENV_VESUM_DB, raising=False)
    monkeypatch.setattr(topology, "_store_locality", lambda _path: "local")
    monkeypatch.setattr(module, "PROJECT_ROOT", worktree)

    assert module.find_vesum_db(None) == vesum.resolve()


@pytest.mark.parametrize("name", sorted(ENGINES))
def test_without_any_database_the_local_default_is_reported(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.storage import topology

    module = _engine(name)
    root = tmp_path / "checkout"
    (root / ".git").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "AGENTS.md").write_text("", encoding="utf-8")
    monkeypatch.delenv(topology.ENV_VESUM_DB, raising=False)
    monkeypatch.setattr(module, "PROJECT_ROOT", root)

    assert module.find_vesum_db(None) == root / "data" / "vesum.db"


def test_adjective_cli_prints_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.db"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.practice.adjective_mechanics_engine",
            "--verify-vesum",
            "--vesum-db",
            str(missing),
            "--deck-output",
            str(tmp_path / "deck.json"),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 1
    assert "VESUM verification FAILED" in proc.stdout
    assert str(missing) in proc.stdout
    assert "missing forms: []" not in proc.stdout
