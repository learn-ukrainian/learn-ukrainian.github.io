"""The declared Python floor is the documented one and admits the pinned interpreter (#10737).

``pyproject.toml`` ``requires-python`` is a full PEP 440 specifier set whose
constraints apply together, so it is read with ``packaging.specifiers`` rather
than by picking out ``>=`` parts. The invariants:

* the pinned interpreter in ``.python-version`` satisfies the whole set (this
  is what rejects ``>=3.14,<3.14.5`` and ``>=3.14,!=3.14.*`` for a 3.14.10 pin);
* the declared lower bound is exactly ``PROJECT_FLOOR``;
* neither the ruff target nor the mypy ``python_version`` is below it.

The pin may move ahead of the floor (e.g. 3.15.x against ``>=3.14``).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from packaging.specifiers import SpecifierSet
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parents[1]

MinorVersion = tuple[int, int]

# When the project floor moves, update this expectation with ``requires-python``,
# the Ruff target and the mypy ``python_version``.
PROJECT_FLOOR: MinorVersion = (3, 14)

# Operators that establish a lower bound on the interpreter version.
_LOWER_BOUND_OPERATORS = frozenset({">=", ">", "~=", "==", "==="})


def _parse_minor(text: str) -> MinorVersion:
    """``"3.14"``, ``"3.14.10"`` or ``"py314"`` -> ``(3, 14)``."""
    text = text.strip().removeprefix("py")
    if "." not in text:
        return int(text[0]), int(text[1:])
    major, minor, *_ = text.split(".")
    return int(major), int(minor)


def _declared_floor(specifiers: SpecifierSet) -> MinorVersion:
    """Highest lower-bound major.minor in the set (all constraints apply together)."""
    bounds = [
        _parse_minor(spec.version.removesuffix(".*"))
        for spec in specifiers
        if spec.operator in _LOWER_BOUND_OPERATORS
    ]
    if not bounds:
        raise AssertionError(f"requires-python {str(specifiers)!r} has no lower bound")
    return max(bounds)


def _check_floor_contract(requires_python: str, pinned: str, ruff_target: str, mypy_target: str) -> None:
    """Raise ``AssertionError`` unless the declared floor contract holds."""
    specifiers = SpecifierSet(requires_python)
    pinned_version = Version(pinned.strip())
    floor = _declared_floor(specifiers)
    assert floor == PROJECT_FLOOR, (
        f"requires-python {requires_python!r} has lower bound {floor}, not the documented floor {PROJECT_FLOOR}"
    )
    assert specifiers.contains(pinned_version, prereleases=True), (
        f"pinned interpreter {pinned_version} is rejected by requires-python {requires_python!r}"
    )
    assert _parse_minor(pinned) >= floor, f"pinned interpreter {pinned_version} is below the floor {floor}"
    assert _parse_minor(ruff_target) >= floor, f"ruff target-version {ruff_target!r} is below the floor {floor}"
    assert _parse_minor(mypy_target) >= floor, f"mypy python_version {mypy_target!r} is below the floor {floor}"


def _pyproject() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_repo_declares_documented_floor_and_admits_pinned_interpreter() -> None:
    data = _pyproject()
    _check_floor_contract(
        data["project"]["requires-python"],
        (REPO_ROOT / ".python-version").read_text(encoding="utf-8"),
        data["tool"]["ruff"]["target-version"],
        data["tool"]["mypy"]["python_version"],
    )


@pytest.mark.parametrize(
    ("requires_python", "pinned"),
    [
        (">=3.14", "3.14.10"),
        (">=3.14,<4", "3.14.10"),
        (">= 3.14 , < 4", "3.14.10"),
        ("<4,>=3.14.1", "3.14.10"),
        # The pin may run ahead of the floor (#10742).
        (">=3.14", "3.15.1"),
        (">=3.14", "3.14"),
    ],
)
def test_accepted_specifier_shapes(requires_python: str, pinned: str) -> None:
    _check_floor_contract(requires_python, pinned, "py314", "3.14")


@pytest.mark.parametrize(
    ("requires_python", "pinned", "message"),
    [
        # The whole set applies even when ``>=3.14`` is present.
        (">=3.14,>3.15", "3.14.10", "not the documented floor|rejected"),
        (">=3.14,!=3.14.*", "3.14.10", "rejected"),
        (">=3.14,<3.14.5", "3.14.10", "rejected"),
        # No lower bound at all.
        ("<4", "3.14.10", "no lower bound"),
        ("!=3.13.*", "3.14.10", "no lower bound"),
        # Lower bound is not the documented floor.
        (">=3.12", "3.14.10", "not the documented floor"),
        (">=3.13", "3.15.1", "not the documented floor"),
        # Pinned interpreter below the floor.
        (">=3.14", "3.13.9", "rejected"),
    ],
)
def test_rejected_specifier_shapes(requires_python: str, pinned: str, message: str) -> None:
    with pytest.raises(AssertionError, match=message):
        _check_floor_contract(requires_python, pinned, "py314", "3.14")


@pytest.mark.parametrize(
    ("ruff_target", "mypy_target", "message"),
    [
        ("py313", "3.14", "ruff target-version"),
        ("py314", "3.13", "mypy python_version"),
    ],
)
def test_tool_targets_below_floor_are_rejected(ruff_target: str, mypy_target: str, message: str) -> None:
    with pytest.raises(AssertionError, match=message):
        _check_floor_contract(">=3.14", "3.14.10", ruff_target, mypy_target)
