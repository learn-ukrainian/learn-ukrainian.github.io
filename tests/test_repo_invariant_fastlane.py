"""Keep repo-wide invariant tests reachable from the PR-tier fastlane.

The detector is deliberately coarse: a test that resolves the real checkout
and walks a ``scripts/`` or ``tests/`` tree, or parses files discovered there,
must be listed in the fastlane manifest or carry an explicit exemption. The
adjudication table is intentionally local and reasoned so a new exception is
visible in the same review as the scope change.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.repo_invariant

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_ROOT = REPO_ROOT / "tests"
FASTLANE_MANIFEST = REPO_ROOT / "scripts" / "ci" / "fastlane_always_tests.txt"

_ROOT_IDENTIFIERS = frozenset(
    {
        "REPO_ROOT",
        "_REPO_ROOT",
        "PROJECT_ROOT",
        "_PROJECT_ROOT",
        "TESTS_ROOT",
        "_TESTS_ROOT",
        "SCRIPTS_ROOT",
        "_SCRIPTS_ROOT",
        "CI_WORKFLOW",
    }
)
_ROOTISH_PARAMETERS = frozenset({"root", "repo_root", "project_root", "tests_root", "scripts_root"})
_TREE_SEGMENTS = frozenset({"scripts", "tests", ".github"})
_DISCOVERY_METHODS = frozenset({"glob", "rglob", "walk"})
_SCANNER_PACKAGES = ("scripts.hygiene", "scripts.lint", "scripts.ci", "scripts.audit")
_SCANNER_NAME_PREFIXES = ("find_", "lint_")
_SCANNER_ROOT_PARAMETERS = _ROOTISH_PARAMETERS | {"primary_root", "repo"}
_SCANNER_DISCOVERY_METHODS = _DISCOVERY_METHODS | {"iterdir"}

# Every named adjudication from the #7250 critique is recorded here, including
# positive decisions, so adding a candidate cannot silently become an omission.
# The reason is one line by policy; it is also rendered in a failure below.
ADJUDICATIONS: dict[str, tuple[str, str]] = {
    "tests/orchestration/test_reap_worktrees.py": (
        "exempt",
        "marked slow and performs a broad production deletion-call-site scan",
    ),
    "tests/test_ask_opencode.py": (
        "listed",
        "cheap deterministic scan of the script-path bridge package",
    ),
    "tests/test_ci_queue_starvation.py": (
        "listed",
        "pins workflow structure and queue starvation mitigations",
    ),
    "tests/test_work_privacy.py": (
        "exempt",
        "private-boundary canary sweep stays out of the public PR fastlane",
    ),
    "tests/test_research_registry.py": (
        "exempt",
        "committed-registry checks use fixed inputs plus synthetic temporary projects",
    ),
    "tests/test_research_registry_api.py": (
        "exempt",
        "static dependency check parses two fixed modules, not a discovered tree",
    ),
    "tests/test_python_qg_correction_loop.py": (
        "exempt",
        "parses inspect.getsource and synthetic QG output rather than repository files",
    ),
    "tests/test_llm_reviewer_dispatch.py": (
        "exempt",
        "large review-bakeoff and fixture scan is outside the PR-tier budget",
    ),
    "tests/test_gemini_adapter_auth.py": (
        "exempt",
        "large adapter/auth suite parses one imported module and uses live-lane setup",
    ),
    "tests/test_atlas_conformance.py": (
        "exempt",
        "socket-guard test is intentionally landing-tier-only per #7248",
    ),
    "tests/test_agent_fleet_tooling_guardrails.py": (
        "exempt",
        "global and private guidance-surface audit belongs to the fleet tooling lane",
    ),
    "tests/test_fleet_comms_launcher_awareness.py": (
        "exempt",
        "cross-plane launcher audit requires fleet-comms surfaces outside the public PR tier",
    ),
    "tests/test_launcher_contract.py": (
        "exempt",
        "launcher lifecycle and subprocess contract suite is an integration-heavy fleet lane",
    ),
    "tests/test_lint_prompts.py": (
        "exempt",
        "prompt-template and retired-template inventory is a documentation policy lane",
    ),
    "tests/api/test_release_snapshot.py": (
        "exempt",
        "release snapshot service and subprocess integration suite is outside the PR-tier budget",
    ),
    "tests/orchestration/test_thread_restart_e2e.py": (
        "exempt",
        "subprocess-heavy restart fixture bootstrap is outside the PR-tier budget",
    ),
    "tests/test_dashboards.py": (
        "exempt",
        "dashboard and API-surface checks cover fixed product assets, not the whole checkout",
    ),
    "tests/test_layerb_candidates.py": (
        "exempt",
        "candidate replay checks are fixture-bound and belong with the Layer-B evaluation lane",
    ),
    "tests/test_paths_filter_fail_open.py": (
        "exempt",
        "fixed action/workflow fail-open checks are covered by the workflow policy lane",
    ),
    "tests/test_prompt_template_render.py": (
        "exempt",
        "single fixed prompt-phase template sweep is not a whole-repository invariant",
    ),
    "tests/test_workflow_head_concurrency.py": (
        "exempt",
        "fixed workflow concurrency expectations are covered by the workflow policy lane",
    ),
}

_EXEMPTIONS = {path for path, (disposition, _reason) in ADJUDICATIONS.items() if disposition == "exempt"}


def _manifest() -> list[str]:
    return [
        line.strip()
        for line in FASTLANE_MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _target_names(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        return {item.id for item in node.elts if isinstance(item, ast.Name)}
    return set()


def _has_tree_segment(node: ast.AST | None) -> bool:
    if node is None:
        return False
    return any(
        isinstance(descendant, ast.Constant)
        and isinstance(descendant.value, str)
        and (
            descendant.value in _TREE_SEGMENTS
            or any(descendant.value.startswith(f"{segment}/") for segment in _TREE_SEGMENTS)
        )
        for descendant in ast.walk(node)
    )


def _is_root_path(node: ast.AST | None, root_aliases: set[str]) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Name):
        return node.id in root_aliases or node.id in _ROOT_IDENTIFIERS
    if isinstance(node, ast.Call):
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "Path"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "__file__"
        ):
            return True
        return isinstance(node.func, ast.Attribute) and node.func.attr in {"absolute", "joinpath", "resolve"} and _is_root_path(
            node.func.value, root_aliases
        )
    if isinstance(node, ast.Attribute):
        return node.attr in {"parent", "parents"} and _is_root_path(node.value, root_aliases)
    if isinstance(node, ast.Subscript):
        return _is_root_path(node.value, root_aliases)
    return False


def _is_tree_path(node: ast.AST | None, root_aliases: set[str], tree_aliases: set[str]) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Name):
        return node.id in tree_aliases or node.id in root_aliases
    if isinstance(node, ast.Call):
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "Path"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "__file__"
        ):
            return True
        if isinstance(node.func, ast.Name) and node.func.id == "sorted" and node.args:
            return _is_tree_path(node.args[0], root_aliases, tree_aliases)
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"absolute", "joinpath", "resolve"}:
            return _is_tree_path(node.func.value, root_aliases, tree_aliases)
        return False
    if isinstance(node, ast.Attribute):
        return node.attr in {"parent", "parents"} and _is_tree_path(node.value, root_aliases, tree_aliases)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left_is_root = (
            _is_root_path(node.left, root_aliases)
            or _is_tree_path(node.left, root_aliases, tree_aliases)
            or (isinstance(node.left, ast.Name) and node.left.id in _ROOTISH_PARAMETERS)
        )
        return left_is_root and _has_tree_segment(node)
    if isinstance(node, ast.Subscript):
        return _is_tree_path(node.value, root_aliases, tree_aliases)
    if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        return any(_is_tree_path(item, root_aliases, tree_aliases) for item in node.elts)
    return False


def _repo_tree_aliases(tree: ast.AST) -> tuple[set[str], set[str]]:
    root_aliases = set(_ROOT_IDENTIFIERS)
    tree_aliases: set[str] = set()

    for _ in range(8):
        changed = False
        for statement in ast.walk(tree):
            if isinstance(statement, ast.Assign):
                value = statement.value
                targets = statement.targets
            elif isinstance(statement, ast.AnnAssign):
                value = statement.value
                targets = [statement.target]
            else:
                continue
            names = {name for target in targets for name in _target_names(target)}
            if not names:
                continue
            if _is_root_path(value, root_aliases) and not names <= root_aliases:
                root_aliases.update(names)
                changed = True
            if _is_tree_path(value, root_aliases, tree_aliases) and not names <= tree_aliases:
                tree_aliases.update(names)
                changed = True

        for statement in ast.walk(tree):
            if not isinstance(statement, ast.For) or not _is_tree_path(statement.iter, root_aliases, tree_aliases):
                continue
            names = _target_names(statement.target)
            if not names <= tree_aliases:
                tree_aliases.update(names)
                changed = True
        if not changed:
            break

    return root_aliases, tree_aliases


def _contains_tree_path(node: ast.AST | None, root_aliases: set[str], tree_aliases: set[str]) -> bool:
    if node is None:
        return False
    return any(_is_tree_path(descendant, root_aliases, tree_aliases) for descendant in ast.walk(node))


def _is_discovered_path(node: ast.AST | None, root_aliases: set[str], tree_aliases: set[str]) -> bool:
    """Use aliases or literal scripts/tests segments for high-recall discovery."""
    return _contains_tree_path(node, root_aliases, tree_aliases) or _has_tree_segment(node)


def _dotted_name(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else None
    return None


def _is_scanner_package(module: str) -> bool:
    return any(module == package or module.startswith(f"{package}.") for package in _SCANNER_PACKAGES)


def _module_source_path(module: str) -> Path | None:
    candidate = REPO_ROOT / f"{module.replace('.', '/')}.py"
    return candidate if candidate.is_file() else None


def _function_parameters(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    arguments = node.args
    return {
        argument.arg
        for argument in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs)
    }


def _function_calls(node: ast.AST) -> set[str]:
    called: set[str] = set()
    for descendant in ast.walk(node):
        if not isinstance(descendant, ast.Call):
            continue
        if isinstance(descendant.func, ast.Name):
            called.add(descendant.func.id)
    return called


def _function_reaches_directory_discovery(
    function_name: str,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    visiting: set[str] | None = None,
) -> bool:
    """Follow local helper calls to recognize imported directory scanners."""
    function = functions.get(function_name)
    if function is None:
        return False
    active = set() if visiting is None else set(visiting)
    if function_name in active:
        return False
    active.add(function_name)

    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr in _SCANNER_DISCOVERY_METHODS:
            return True
        if isinstance(node.func, ast.Name) and node.func.id == "glob":
            return True

    return any(
        _function_reaches_directory_discovery(callee, functions, active)
        for callee in _function_calls(function)
        if callee in functions
    )


def _module_exposes_repo_scanner(module: str, helper_name: str) -> bool:
    if not helper_name.startswith(_SCANNER_NAME_PREFIXES):
        return False
    source_path = _module_source_path(module)
    if source_path is None:
        return False
    try:
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    except SyntaxError:
        return False
    if not _has_tree_segment(tree):
        return False
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    function = functions.get(helper_name)
    return bool(
        function
        and _function_parameters(function) & _SCANNER_ROOT_PARAMETERS
        and _function_reaches_directory_discovery(helper_name, functions)
    )


def _imported_scanner_bindings(tree: ast.AST) -> dict[str, tuple[str, str | None]]:
    bindings: dict[str, tuple[str, str | None]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and _is_scanner_package(node.module):
            for alias in node.names:
                if alias.name != "*":
                    bindings[alias.asname or alias.name] = (node.module, alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if _is_scanner_package(alias.name) and alias.asname:
                    bindings[alias.asname] = (alias.name, None)
    return bindings


def _references_imported_repo_scanner(tree: ast.AST) -> bool:
    bindings = _imported_scanner_bindings(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            binding = bindings.get(node.func.id)
            if binding:
                module, imported_name = binding
                if imported_name and _module_exposes_repo_scanner(module, imported_name):
                    return True
            continue

        if not isinstance(node.func, ast.Attribute):
            continue
        receiver = _dotted_name(node.func.value)
        binding = bindings.get(receiver or "")
        if not binding:
            continue
        module, imported_name = binding
        imported_module = module if imported_name is None else f"{module}.{imported_name}"
        if _module_exposes_repo_scanner(imported_module, node.func.attr):
            return True
    return False


def _references_repo_tree(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return False

    if _references_imported_repo_scanner(tree):
        return True

    root_aliases, tree_aliases = _repo_tree_aliases(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in _DISCOVERY_METHODS
            and _is_discovered_path(node.func.value, root_aliases, tree_aliases)
        ):
            return True
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "glob"
            and node.func.attr == "glob"
            and node.args
            and _is_discovered_path(node.args[0], root_aliases, tree_aliases)
        ):
            return True
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "glob"
            and node.args
            and _is_discovered_path(node.args[0], root_aliases, tree_aliases)
        ):
            return True
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os"
            and node.func.attr == "walk"
            and node.args
            and _is_discovered_path(node.args[0], root_aliases, tree_aliases)
        ):
            return True
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "ast"
            and node.func.attr == "parse"
            and node.args
            and _is_discovered_path(node.args[0], root_aliases, tree_aliases)
        ):
            return True

    # Helpers can read a real tree into a string before passing it to ast.parse.
    return bool(tree_aliases and "read_text" in path.read_text(encoding="utf-8") and any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "ast"
        and node.func.attr == "parse"
        for node in ast.walk(tree)
    ))


def _pytest_marks(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and node.attr in {"repo_invariant", "slow", "atlas_release"}
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "mark"
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "pytest"
    }


def test_repo_tree_invariants_are_listed_or_explicitly_exempted() -> None:
    manifest = set(_manifest())
    candidates = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in sorted(TESTS_ROOT.rglob("test_*.py"))
        if _references_repo_tree(path)
    }
    uncovered = sorted(candidates - manifest - _EXEMPTIONS)
    assert not uncovered, (
        "repo-tree test modules are absent from fastlane_always_tests.txt and the exemption table: "
        + ", ".join(uncovered)
    )


def test_imported_repo_scanner_is_a_repo_tree_candidate() -> None:
    assert _references_repo_tree(REPO_ROOT / "tests" / "test_path_safety.py")


def test_fastlane_manifest_entries_are_fast_and_marked() -> None:
    manifest = _manifest()
    assert manifest == sorted(set(manifest)), "fastlane manifest must be sorted and duplicate-free"
    assert manifest, "fastlane manifest must not be empty"
    for entry in manifest:
        path = REPO_ROOT / entry
        assert path.is_file(), f"fastlane manifest entry does not exist: {entry}"
        marks = _pytest_marks(path)
        assert "repo_invariant" in marks, f"fastlane entry lacks repo_invariant marker: {entry}"
        assert "slow" not in marks, f"fastlane entry carries deselected slow mark: {entry}"
        assert "atlas_release" not in marks, f"fastlane entry carries deselected atlas_release mark: {entry}"


def test_named_candidate_adjudications_are_explicit() -> None:
    manifest = set(_manifest())
    required = {
        "tests/orchestration/test_reap_worktrees.py",
        "tests/test_ask_opencode.py",
        "tests/test_work_privacy.py",
        "tests/test_research_registry.py",
        "tests/test_research_registry_api.py",
        "tests/test_python_qg_correction_loop.py",
        "tests/test_llm_reviewer_dispatch.py",
        "tests/test_gemini_adapter_auth.py",
        "tests/test_atlas_conformance.py",
    }
    assert required <= ADJUDICATIONS.keys()
    for path, (disposition, reason) in ADJUDICATIONS.items():
        assert reason.strip(), f"missing adjudication reason: {path}"
        assert disposition in {"listed", "exempt"}, f"invalid adjudication: {path}"
        if disposition == "listed":
            assert path in manifest, f"adjudicated listed module is absent from fastlane: {path}"
        else:
            assert path not in manifest, f"adjudicated exemption is listed in fastlane: {path}"
