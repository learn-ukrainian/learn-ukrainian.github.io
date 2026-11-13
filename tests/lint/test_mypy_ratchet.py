"""Gate defects for the scripts/ mypy ratchet (#12642)."""

from __future__ import annotations

from pathlib import Path

from scripts.lint.mypy_ratchet import MypyError, collect_errors, evaluate, write_baseline

_CONFIG = """\
[tool.mypy]
python_version = "3.12"
show_error_codes = true
"""


def _tree(tmp_path: Path, source: str) -> tuple[Path, Path]:
    root = tmp_path / "tree"
    root.mkdir()
    (root / "pyproject.toml").write_text(_CONFIG, encoding="utf-8")
    (root / "mod.py").write_text(source, encoding="utf-8")
    return root, root / "baseline.json"


def _check(root: Path, baseline: Path) -> list[str]:
    return evaluate(
        root,
        baseline,
        ["mod.py"],
        config_file=root / "pyproject.toml",
        incremental=False,
    )


def test_new_type_error_does_not_pass_the_gate(tmp_path: Path) -> None:
    """A type error absent from the baseline fails the gate."""
    root, baseline = _tree(tmp_path, "def answer() -> str:\n    return 1\n")
    write_baseline(baseline, [])
    violations = _check(root, baseline)
    assert violations
    assert any(": new " in item for item in violations)


def test_fixed_error_left_in_the_baseline_does_not_pass(tmp_path: Path) -> None:
    """A baseline entry mypy no longer reports is stale and fails."""
    root, baseline = _tree(tmp_path, "def answer() -> str:\n    return 'ok'\n")
    write_baseline(baseline, [MypyError("mod.py", "return-value", "fixed error")])
    violations = _check(root, baseline)
    assert any("stale baseline" in item for item in violations)


def test_line_move_does_not_change_baseline_identity(tmp_path: Path) -> None:
    """Inserting lines above an error keeps the same identity, so the gate stays green."""
    root, baseline = _tree(tmp_path, "def answer() -> str:\n    return 1\n")
    before, before_fatal = collect_errors(
        root, ["mod.py"], config_file=root / "pyproject.toml", incremental=False
    )
    assert before_fatal == []
    assert [error.code for error in before] == ["return-value"]
    (root / "mod.py").write_text("\n\n\ndef answer() -> str:\n    return 1\n", encoding="utf-8")
    after, after_fatal = collect_errors(
        root, ["mod.py"], config_file=root / "pyproject.toml", incremental=False
    )
    assert after_fatal == []
    assert after == before
    write_baseline(baseline, after)
    assert _check(root, baseline) == []
