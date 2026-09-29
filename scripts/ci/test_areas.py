"""Fail-open filtering of full-PR pytest files by declared test area."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from collections.abc import Iterable
from pathlib import Path

_MANIFEST = Path(__file__).with_name("test_areas.json")
AREA_NAMES = frozenset({"open_model_data", "atlas"})

# Exact expressions, keyed by tracked file and enclosing function. Each may
# occur once; a second computed path, even in the same function, must be audited.
AUDITED_COMPUTED_REPO_PATHS: dict[tuple[str, str], frozenset[str]] = {
    # Sparse-tree import analysis resolves literal imports from the test's AST.
    ("tests/conftest.py", "_resolve_module"): frozenset(
        {
            "_REPO_ROOT / rel.with_suffix('.py')",
            "_REPO_ROOT / rel",
        }
    ),
    # Collection supplies the current test file's repo-relative location.
    ("tests/conftest.py", "_analyze_test_module"): frozenset({"_REPO_ROOT / rel_path"}),
    # find_entry validates rel; the invariant checks each test marker's data path.
    ("tests/conftest.py", "pytest_runtest_setup"): frozenset({"DATA_ROOT / rel"}),
    # The invariant checks each area test's tree_absent argument at its call site.
    ("tests/sparse_trees.py", "tree_absent"): frozenset({"REPO_ROOT / normalized"}),
}


def load_areas(path: Path = _MANIFEST) -> dict[str, dict[str, list[str]]]:
    """Validate the small area manifest before it can affect CI selection."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != AREA_NAMES:
        raise ValueError(f"test area names must be exactly {sorted(AREA_NAMES)}")
    for area in raw.values():
        if not isinstance(area, dict) or set(area) != {"tests", "roots"}:
            raise ValueError("test area must declare tests and roots")
        for key in ("tests", "roots"):
            values = area[key]
            if not isinstance(values, list) or not values or len(values) != len(set(values)):
                raise ValueError(f"invalid {key} list")
            if any(
                not isinstance(value, str)
                or not value
                or value.startswith("/")
                or "\\" in value
                or ".." in value.split("/")
                for value in values
            ):
                raise ValueError(f"invalid {key} path")
        if any(not value.startswith("tests/") or not value.endswith(".py") for value in area["tests"]):
            raise ValueError("area tests must be Python files under tests/")
        if any("*" in value or "?" in value or "[" in value for value in area["roots"]):
            raise ValueError("area roots must be literal paths or directory prefixes")
    return raw


def matches_test(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def matches_root(path: str, roots: Iterable[str]) -> bool:
    return any(path.startswith(root) if root.endswith("/") else path == root for root in roots)


def filter_paths(
    paths: list[str], skipped: list[str], *, manifest: Path = _MANIFEST, repo: Path | None = None
) -> tuple[list[str], int]:
    """Keep unknown or repo_wide tests; invalid inputs preserve every file.

    A test listed by several areas is dropped only when every one of them is
    skipped: each area's roots prove only that area's reach.
    """
    try:
        areas = load_areas(manifest)
        if not isinstance(skipped, list) or any(name not in areas for name in skipped):
            raise ValueError("unknown skipped area")
        if len(skipped) != len(set(skipped)):
            raise ValueError("duplicate skipped area")
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return paths, 0
    patterns = [pattern for name in skipped for pattern in areas[name]["tests"]]
    selected = [pattern for name, area in areas.items() if name not in skipped for pattern in area["tests"]]
    repo = repo or Path.cwd()
    kept: list[str] = []
    dropped = 0
    for path in paths:
        if not matches_test(path, patterns) or matches_test(path, selected):
            kept.append(path)
            continue
        try:
            # CI's repo_wide leg must always receive every marked test file.
            marked = "pytest.mark.repo_wide" in (repo / path).read_text(encoding="utf-8")
        except OSError:
            marked = True
        if marked:
            kept.append(path)
        else:
            dropped += 1
    return kept, dropped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    filtering = commands.add_parser("filter", help="Filter newline-delimited test paths on stdin")
    filtering.add_argument("--skip", required=True, help="JSON list from Changes.skipped_areas")
    args = parser.parse_args()
    paths = sys.stdin.read().splitlines()
    try:
        skipped = json.loads(args.skip)
    except (ValueError, TypeError):
        skipped = None
    kept, _ = filter_paths(paths, skipped)
    if kept:
        sys.stdout.write("\n".join(kept) + "\n")


if __name__ == "__main__":
    main()
