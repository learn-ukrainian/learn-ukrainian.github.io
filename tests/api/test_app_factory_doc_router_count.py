"""The router counts in the app-factory design doc must match `scripts/api/main.py` (#8522)."""

from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_PY = REPO_ROOT / "scripts" / "api" / "main.py"
DOC = REPO_ROOT / "docs" / "design" / "monitor-api-app-factory.md"


def _main_router_facts() -> dict:
    """Recompute the router inventory from the AST of `main.py`."""
    tree = ast.parse(MAIN_PY.read_text(encoding="utf-8"))
    registered = Counter(
        ast.unparse(node.args[0])
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "include_router"
        and node.args
    )
    # Imported router modules: `from .<module> import router [as <alias>]`.
    modules = sorted(
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.level == 1
        and any(alias.name == "router" for alias in node.names)
    )
    return {
        "registrations": sum(registered.values()),
        "distinct": len(registered),
        "double_mounted": sorted(name for name, count in registered.items() if count > 1),
        "modules": modules,
    }


def _doc_text() -> str:
    # Collapse line wraps so claims that span lines can be matched.
    return re.sub(r"\s+", " ", DOC.read_text(encoding="utf-8"))


def _step_table_modules() -> list[str]:
    """Module names listed in the §5.2 provisional step table (first column of scope)."""
    rows = re.findall(r"^\| (?:\d+) \| (.+?) \|", DOC.read_text(encoding="utf-8"), re.MULTILINE)
    names: list[str] = []
    for scope in rows:
        # Drop trailing parentheticals ("(20 modules; ...)", "(own step; ...)", "(mounted ...)").
        scope = re.sub(r"\([^)]*\)", "", scope)
        names += re.findall(r"`([a-z_]+)\.py`", scope)
    return names


def test_main_py_facts_are_sane() -> None:
    facts = _main_router_facts()
    assert facts["registrations"] >= facts["distinct"] >= len(facts["modules"])


def test_doc_states_exact_router_counts() -> None:
    facts = _main_router_facts()
    text = _doc_text()
    n_modules = len(facts["modules"])
    # `core_router` is defined inside main.py, so it is the one distinct object that is not a module.
    assert facts["distinct"] == n_modules + 1
    claim = (
        f"`main.py` makes {facts['registrations']} `include_router` calls registering "
        f"**{facts['distinct']} distinct router objects**: {n_modules} imported router modules "
        "plus `core_router`"
    )
    assert claim in text
    assert f"= **{n_modules} modules**" in text


def test_doc_names_exactly_the_double_mounted_routers() -> None:
    facts = _main_router_facts()
    text = _doc_text()
    assert facts["double_mounted"] == ["docs_router"]
    assert "Only `docs_router` is registered twice" in text


def test_step_table_lists_every_imported_router_module_once() -> None:
    facts = _main_router_facts()
    listed = _step_table_modules()
    assert sorted(listed) == facts["modules"], (
        f"missing from table: {sorted(set(facts['modules']) - set(listed))}; "
        f"unexpected in table: {sorted(set(listed) - set(facts['modules']))}; "
        f"duplicates: {sorted(n for n, c in Counter(listed).items() if c > 1)}"
    )


def test_step_12_module_count_matches_its_listing() -> None:
    row = next(
        line
        for line in DOC.read_text(encoding="utf-8").splitlines()
        if line.startswith("| 12 |")
    )
    claimed = int(re.search(r"\((\d+) modules;", row).group(1))
    assert claimed == len(re.findall(r"`[a-z_]+\.py`", row))
