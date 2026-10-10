"""The router counts in the app-factory design doc and the router inventory must match `scripts/api/main.py` (#8522)."""

from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path

from tests.api.opsec_sweep.registry import FROZEN_HTTP_OPERATION_COUNT, FROZEN_WEBSOCKET_ROUTE_COUNT

REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_PY = REPO_ROOT / "scripts" / "api" / "main.py"
API_DIR = REPO_ROOT / "scripts" / "api"
DOC = REPO_ROOT / "docs" / "design" / "monitor-api-app-factory.md"
INVENTORY = REPO_ROOT / "docs" / "design" / "monitor-api-router-inventory.md"


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
    prefixes: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "include_router"
            and node.args
        ):
            prefixes.setdefault(ast.unparse(node.args[0]), []).extend(
                kw.value.value for kw in node.keywords if kw.arg == "prefix" and isinstance(kw.value, ast.Constant)
            )
    # Imported router modules: `from .<module> import router [as <alias>]`.
    imports = [
        (alias.asname or alias.name, node.module)
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
        if alias.name == "router"
    ]
    modules = sorted(module for _, module in imports)
    return {
        "router_module": dict(imports) | {"core_router": "main"},
        "prefixes": prefixes,
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
        names += re.findall(r"`([a-z_.]+)\.py`", scope)
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
    row = next(line for line in DOC.read_text(encoding="utf-8").splitlines() if line.startswith("| 12 |"))
    claimed = int(re.search(r"\((\d+) modules;", row).group(1))
    assert claimed == len(re.findall(r"`[a-z_.]+\.py`", row))


# --- docs/design/monitor-api-router-inventory.md -------------------------------------

_HTTP_VERB = r"(?:get|post|put|delete|patch|websocket|head|options)"


def _inventory_text() -> str:
    return INVENTORY.read_text(encoding="utf-8")


def _router_source(module: str) -> Path:
    """File that holds a mounted router's handlers.

    A single-file router is ``scripts/api/<module>.py``. A package router is
    imported as a dotted module whose file is ``router.py`` inside the package.
    """
    if module == "main":
        return MAIN_PY
    relative = Path(*module.split("."))
    file_path = (API_DIR / relative).with_suffix(".py")
    if file_path.is_file():
        return file_path
    package_router = API_DIR / relative / "router.py"
    if package_router.is_file():
        return package_router
    return file_path


def _router_repo_path(module: str) -> str:
    return _router_source(module).relative_to(REPO_ROOT).as_posix()


def _decorator_count(path: Path, variable: str = "router") -> int:
    """Route decorators on `variable`, plus those of routers it nests via `router.include_router`."""
    source = path.read_text(encoding="utf-8")
    total = len(re.findall(rf"^@{variable}\.{_HTTP_VERB}\(", source, re.MULTILINE))
    tree = ast.parse(source)
    child_modules = {
        (alias.asname or alias.name): node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
        if alias.name == "router"
    }
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "include_router"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == variable
            and node.args
            and ast.unparse(node.args[0]) in child_modules
        ):
            total += _decorator_count(API_DIR / f"{child_modules[ast.unparse(node.args[0])]}.py")
    return total


def _inventory_rows() -> dict[str, list[str]]:
    """Per-router inventory rows keyed by module stem; cells are the table columns after the module."""
    rows: dict[str, list[str]] = {}
    section = _inventory_text().split("## Per-router inventory", 1)[1].split("## Global OPSEC seams", 1)[0]
    for line in section.splitlines():
        match = re.match(r"^\| `([a-z_.]+)\.py`(?: \(`[a-z_]+`\))? \| (.+) \|$", line)
        if match:
            assert match.group(1) not in rows, f"duplicate inventory row for {match.group(1)}"
            rows[match.group(1)] = [cell.strip() for cell in match.group(2).split(" | ")]
    return rows


def _inventory_step_rows() -> list[tuple[str, list[str]]]:
    """(step label, router names) for each row of the proposed-migration-steps table."""
    section = _inventory_text().split("## Proposed migration steps", 1)[1].split("## Per-router inventory", 1)[0]
    rows = []
    for step, scope in re.findall(r"^\| \*\*(\w+)\*\* \| (.+?) \| [\d,]+ \|", section, re.MULTILINE):
        scope = re.sub(r"\([^)]*\)", "", scope)
        rows.append((step, re.findall(r"`([a-z_]+)`", scope)))
    return rows


def test_inventory_states_exact_router_counts() -> None:
    facts = _main_router_facts()
    text = re.sub(r"\s+", " ", _inventory_text())
    n_modules = len(facts["modules"])
    claim = (
        f"`main.py` makes **{facts['registrations']}** `include_router` calls registering "
        f"**{facts['distinct']} distinct router objects**: {n_modules} imported router modules "
        "plus `core_router`"
    )
    assert claim in text
    assert f"### Total router-module count — **{facts['distinct']}** distinct router objects" in text
    assert f"# {facts['registrations']} {facts['distinct']} ['docs_router']" in text
    assert "Only `docs_router` is registered twice" in text
    assert (
        f"| Distinct router objects ({n_modules} imported modules + `core_router`) | {facts['distinct']} |" in text
    )
    assert f"| Router registrations (`include_router` calls) | {facts['registrations']} |" in text


def test_inventory_route_counts_match_the_decorators_and_the_sweep_registry() -> None:
    facts = _main_router_facts()
    text = _inventory_text()
    expected = sum(
        _decorator_count(_router_source(module)) for module in facts["router_module"].values() if module != "main"
    ) + _decorator_count(MAIN_PY, "core_router")
    assert f"**{expected}** decorator sum" in text
    assert f"**{FROZEN_HTTP_OPERATION_COUNT}** OpenAPI HTTP ops + **{FROZEN_WEBSOCKET_ROUTE_COUNT}** WebSocket" in text
    assert f"| OpenAPI HTTP operations (sweep denominator) | {FROZEN_HTTP_OPERATION_COUNT} |" in text
    # The per-router rows must add up to the stated decorator sum.
    assert sum(int(cells[1]) for cells in _inventory_rows().values()) == expected


def test_inventory_has_exactly_one_row_per_mounted_router_module() -> None:
    facts = _main_router_facts()
    rows = _inventory_rows()
    expected = set(facts["modules"]) | {"main"}
    assert set(rows) == expected, (
        f"missing rows: {sorted(expected - set(rows))}; rows for modules that are not mounted: "
        f"{sorted(set(rows) - expected)}"
    )
    for stem in rows:
        assert _router_source(stem).is_file(), f"inventory row for a module that does not exist: {stem}"


def test_inventory_mount_prefixes_match_main() -> None:
    facts = _main_router_facts()
    rows = _inventory_rows()
    for router, module in facts["router_module"].items():
        prefix_cell = rows[module][0]
        prefixes = facts["prefixes"][router]
        if prefixes:
            missing = [prefix for prefix in prefixes if f"`{prefix}`" not in prefix_cell]
            assert not missing, f"{router}: prefixes {missing} not in the inventory row: {prefix_cell}"
            # No stale extra mount (e.g. the retired `/api/cost` and `/api/rag` mounts).
            stale = set(re.findall(r"`(/[^`]*)`", prefix_cell)) - set(prefixes)
            allowed_nested = {"/entire-context", "/workers/v1"}
            assert not (stale - allowed_nested), f"{router}: inventory names unmounted prefixes {sorted(stale)}"
        else:
            assert prefix_cell.startswith("(none"), f"{router} is mounted without a prefix: {prefix_cell}"


def test_inventory_step_table_lists_every_router_once_and_totals_the_distinct_count() -> None:
    facts = _main_router_facts()
    steps = _inventory_step_rows()
    listed = [name for _, names in steps for name in names]
    assert sorted(listed) == sorted(facts["router_module"]), (
        f"missing from steps: {sorted(set(facts['router_module']) - set(listed))}; "
        f"unexpected in steps: {sorted(set(listed) - set(facts['router_module']))}; "
        f"duplicates: {sorted(n for n, c in Counter(listed).items() if c > 1)}"
    )
    text = _inventory_text()
    per_step = {label: len(names) for label, names in steps}
    # Both copies of the arithmetic block (evidence preamble and summary accounting) match the table.
    expected_line = " + ".join(f"step {label} ({count})" for label, count in per_step.items())
    blocks = re.findall(r"^step 1 \(.*?router objects$", text, re.MULTILINE | re.DOTALL)
    assert len(blocks) == 2
    for block in blocks:
        collapsed = re.sub(r"\s*\n\+ ", " + ", block)
        assert collapsed == f"{expected_line} = {facts['distinct']} router objects"
    assert f"### Per-step module tally — sums to **{facts['distinct']}**" in text
    # `core_router` is the last mount, so it is in the last step with `batch_router` just before it.
    assert steps[-1][1] == ["batch_router", "core_router"]


def test_inventory_router_map_matches_main_and_names_no_missing_file() -> None:
    facts = _main_router_facts()
    block = re.search(r"ROUTER_MAP = (\{.*?\n\})", _inventory_text(), re.DOTALL)
    assert block, "ROUTER_MAP block not found in the inventory"
    router_map = ast.literal_eval(block.group(1))
    expected = {router: _router_repo_path(module) for router, module in facts["router_module"].items()}
    assert router_map == expected
    for path in router_map.values():
        assert (REPO_ROOT / path).is_file(), f"ROUTER_MAP names a file that does not exist: {path}"


def test_inventory_names_no_retired_rag_router_module() -> None:
    text = _inventory_text()
    assert not (API_DIR / "rag_router.py").exists()
    # The one allowed mention is the deviation row that records the rename.
    mentions = [line for line in text.splitlines() if "rag_router" in line]
    assert len(mentions) == 1 and mentions[0].startswith("| `rag_router.py` naming |"), mentions


def test_inventory_fleet_board_row_matches_merged_router() -> None:
    source = _router_source("fleet_board.router")
    cells = _inventory_rows()["fleet_board.router"]
    assert int(cells[1]) == _decorator_count(source)
    assert int(cells[2].replace(",", "")) == len(source.read_text().splitlines())
