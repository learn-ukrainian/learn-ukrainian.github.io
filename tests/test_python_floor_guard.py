"""The declared Python floor matches the pinned interpreter and the tool targets (#10737).

``pyproject.toml`` ``requires-python`` is the supported minimum. The repo
already uses 3.12-only syntax (PEP 695 ``type`` aliases), so the floor must
equal the major.minor of ``.python-version`` and neither the ruff target nor
the mypy ``python_version`` may sit below it.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

Version = tuple[int, int]


def _parse_minor(text: str) -> Version:
    """``"3.12"``, ``"3.12.14"`` or ``"py312"`` -> ``(3, 12)``."""
    text = text.strip().removeprefix("py")
    if "." not in text:
        return int(text[0]), int(text[1:])
    major, minor, *_ = text.split(".")
    return int(major), int(minor)


def _floor_from_specifier(specifier: str) -> Version:
    """Lowest ``>=X.Y`` bound in a PEP 440 specifier set such as ``>=3.12,<4``."""
    bounds = [
        _parse_minor(part.strip().removeprefix(">="))
        for part in specifier.split(",")
        if part.strip().startswith(">=")
    ]
    if not bounds:
        raise ValueError(f"no '>=' lower bound in {specifier!r}")
    return max(bounds)


def _pyproject() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _pinned() -> Version:
    return _parse_minor((REPO_ROOT / ".python-version").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("specifier", "expected"),
    [
        (">=3.12", (3, 12)),
        (">=3.12,<4", (3, 12)),
        (">= 3.12 , < 4", (3, 12)),
        ("<4,>=3.12.1", (3, 12)),
    ],
)
def test_floor_specifier_shapes(specifier: str, expected: Version) -> None:
    assert _floor_from_specifier(specifier) == expected


def test_floor_specifier_without_lower_bound_is_rejected() -> None:
    with pytest.raises(ValueError):
        _floor_from_specifier("<4")


def test_requires_python_floor_equals_pinned_interpreter() -> None:
    floor = _floor_from_specifier(_pyproject()["project"]["requires-python"])
    assert floor == _pinned() == (3, 12)


def test_tool_targets_are_not_below_the_floor() -> None:
    data = _pyproject()
    floor = _floor_from_specifier(data["project"]["requires-python"])
    ruff_target = _parse_minor(data["tool"]["ruff"]["target-version"])
    mypy_target = _parse_minor(data["tool"]["mypy"]["python_version"])
    assert ruff_target >= floor
    assert mypy_target >= floor
