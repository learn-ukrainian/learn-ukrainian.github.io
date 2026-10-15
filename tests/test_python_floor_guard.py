"""The declared Python floor is the documented one and admits the pinned interpreter (#10737).

``pyproject.toml`` ``requires-python`` is a full PEP 440 specifier set whose
constraints apply together, so it is read with ``packaging.specifiers`` rather
than by picking out ``>=`` parts. The invariants:

* the pinned interpreter in ``.python-version`` satisfies the whole set (this
  is what rejects ``>=3.12,>3.13`` and ``>=3.12,!=3.12.*``);
* the declared lower bound is exactly ``PROJECT_FLOOR``;
* neither the ruff target nor the mypy ``python_version`` is below it, nor
  ahead of the pinned interpreter (the tools may not target a Python the
  project does not run on).

The floor is deliberately *not* required to equal the pinned interpreter: the
pin may move ahead of the floor (e.g. 3.14.x against ``>=3.12``), so the
invariant is floor <= tool targets <= pinned and pinned contained in the set.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from packaging.specifiers import SpecifierSet
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parents[1]

MinorVersion = tuple[int, int]

# The documented project floor (the code uses 3.12-only syntax such as PEP 695
# ``type`` aliases). Raising it is a deliberate edit to this constant together
# with ``requires-python``, the ruff target and the mypy ``python_version``.
PROJECT_FLOOR: MinorVersion = (3, 12)

# Operators that establish a lower bound on the interpreter version.
_LOWER_BOUND_OPERATORS = frozenset({">=", ">", "~=", "==", "==="})


def _parse_minor(text: str) -> MinorVersion:
    """``"3.12"``, ``"3.12.14"`` or ``"py312"`` -> ``(3, 12)``."""
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
    pinned_minor = _parse_minor(pinned)
    assert _parse_minor(ruff_target) <= pinned_minor, (
        f"ruff target-version {ruff_target!r} is ahead of the pinned interpreter {pinned_version}"
    )
    assert _parse_minor(mypy_target) <= pinned_minor, (
        f"mypy python_version {mypy_target!r} is ahead of the pinned interpreter {pinned_version}"
    )


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
        (">=3.12", "3.12.14"),
        (">=3.12,<4", "3.12.14"),
        (">= 3.12 , < 4", "3.12.14"),
        ("<4,>=3.12.1", "3.12.14"),
        # The pin may run ahead of the floor (#10742): patch-level pin, floor 3.12.
        (">=3.12", "3.14.8"),
        (">=3.12", "3.12"),
    ],
)
def test_accepted_specifier_shapes(requires_python: str, pinned: str) -> None:
    _check_floor_contract(requires_python, pinned, "py312", "3.12")


@pytest.mark.parametrize(
    ("requires_python", "pinned", "message"),
    [
        # Reviewer probes: both reject the pinned 3.12.14 although ``>=3.12`` is present.
        (">=3.12,>3.13", "3.12.14", "not the documented floor|rejected"),
        (">=3.12,!=3.12.*", "3.12.14", "rejected"),
        (">=3.12,<3.12.5", "3.12.14", "rejected"),
        # No lower bound at all.
        ("<4", "3.12.14", "no lower bound"),
        ("!=3.11.*", "3.12.14", "no lower bound"),
        # Lower bound is not the documented floor.
        (">=3.11", "3.12.14", "not the documented floor"),
        (">=3.13", "3.14.8", "not the documented floor"),
        # Pinned interpreter below the floor.
        (">=3.12", "3.11.9", "rejected"),
    ],
)
def test_rejected_specifier_shapes(requires_python: str, pinned: str, message: str) -> None:
    with pytest.raises(AssertionError, match=message):
        _check_floor_contract(requires_python, pinned, "py312", "3.12")


@pytest.mark.parametrize(
    ("ruff_target", "mypy_target", "message"),
    [
        ("py311", "3.12", "ruff target-version"),
        ("py312", "3.11", "mypy python_version"),
    ],
)
def test_tool_targets_below_floor_are_rejected(ruff_target: str, mypy_target: str, message: str) -> None:
    with pytest.raises(AssertionError, match=message):
        _check_floor_contract(">=3.12", "3.12.14", ruff_target, mypy_target)


@pytest.mark.parametrize(
    ("ruff_target", "mypy_target", "message"),
    [
        ("py315", "3.14", "ruff target-version .* ahead of the pinned"),
        ("py314", "3.15", "mypy python_version .* ahead of the pinned"),
        ("py313", "3.15", "mypy python_version .* ahead of the pinned"),
    ],
)
def test_tool_targets_ahead_of_pin_are_rejected(ruff_target: str, mypy_target: str, message: str) -> None:
    with pytest.raises(AssertionError, match=message):
        _check_floor_contract(">=3.12", "3.14.8", ruff_target, mypy_target)


@pytest.mark.parametrize(
    ("ruff_target", "mypy_target", "pinned"),
    [
        ("py314", "3.14", "3.14.8"),
        ("py312", "3.14", "3.14.8"),
        ("py312", "3.12", "3.12.14"),
        ("py312", "3.12", "3.14.8"),
    ],
)
def test_tool_targets_between_floor_and_pin_are_accepted(ruff_target: str, mypy_target: str, pinned: str) -> None:
    _check_floor_contract(">=3.12", pinned, ruff_target, mypy_target)
