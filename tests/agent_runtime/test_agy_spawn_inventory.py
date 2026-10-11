"""Static AGY start inventory; this does not certify native enforcement."""

from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
STATUSES = frozenset({"gated", "management-exempt", "probe-exempt", "ungated-residual-10442"})

# A site is its enclosing function plus a start ordinal, not a moving line number.
SPAWN_INVENTORY = {
    "scripts/launchers/gemini.sh::launcher_adapter_exec:1": "gated",
    "scripts/agent_runtime/adapters/agy.py::build_invocation:1": "gated",
    "scripts/agent_runtime/tool_config.py::_run_agy_mcp:1": "management-exempt",
    "scripts/agent_runtime/review_mcp.py::verify_agy_review_effective_mcp:1": "management-exempt",
    "scripts/agent_runtime/adapters/agy.py::_agy_version:1": "probe-exempt",
    "scripts/agent_runtime/attempt_boundary.py::verify_seat:1": "probe-exempt",
    "scripts/agent_runtime/adapters/acpx.py::_probe_participant_cli_version:1": "probe-exempt",
    "scripts/agent_runtime/adapters/acpx.py::_probe_cli_help:1": "probe-exempt",
    "scripts/ai_agent_bridge/_ui_agy.py::send:1": "ungated-residual-10442",
    "scripts/agent_runtime/acp_text_agent.mjs::runAgy:1": "ungated-residual-10442",
    "scripts/agent_runtime/acp_text_agent.mjs::runChild:1": "ungated-residual-10442",
    "scripts/ai_agent_bridge/openai_proxy.py::_run_backend_command:1": "ungated-residual-10442",
    "scripts/ai_agent_bridge/openai_proxy.py::_probe_cli:1": "probe-exempt",
    "scripts/api/subscription_usage.py::_probe_antigravity_native:1": "ungated-residual-10442",
    "scripts/agent_runtime/telemetry.py::_probe_version:1": "probe-exempt",
    "scripts/ai_agent_bridge/_model.py::check_model:1": "gated",
}


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _agy_value(node: ast.AST, names: set[str]) -> bool:
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str) and Path(node.value).name == "agy"
    if isinstance(node, ast.Name):
        return node.id in names or node.id.lower() in {"agy_bin", "agy_binary", "agy_cli"}
    if isinstance(node, (ast.List, ast.Tuple)):
        return bool(node.elts) and _agy_value(node.elts[0], names)
    if isinstance(node, ast.Call) and _call_name(node.func) in {"_agy_binary", "_agy_cli_bin"}:
        return True
    return any(_agy_value(child, names) for child in ast.iter_child_nodes(node))


def _local_nodes(scope: ast.AST):
    """Visit a scope without attributing a nested function's starts to it."""
    for child in ast.iter_child_nodes(scope):
        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            yield child
            yield from _local_nodes(child)


def _bound_names(target: ast.AST) -> set[str]:
    return {node.id for node in ast.walk(target) if isinstance(node, ast.Name)}


def _python_sites(source: str) -> list[str]:
    tree = ast.parse(source)
    scopes = [tree, *(node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))]
    functions = {node.name: node for node in scopes[1:]}
    names_by_scope = {id(scope): set() for scope in scopes}
    nodes_by_scope = {
        id(scope): sorted(_local_nodes(scope), key=lambda node: getattr(node, "lineno", 0)) for scope in scopes
    }
    for scope in scopes[1:]:
        params = {arg.arg for arg in scope.args.args + scope.args.kwonlyargs}
        names_by_scope[id(scope)].update(name for name in params if "agy" in name.lower())
        # Generic helpers can accept AGY as well as other binaries. Seed their
        # binary parameter from an AGY branch, then follow local helper calls.
        mentions_agy = any(
            (isinstance(node, ast.Constant) and node.value == "agy")
            or (isinstance(node, ast.ImportFrom) and (node.module or "").endswith(".agy"))
            or (isinstance(node, ast.Name) and node.id.startswith("verify_agy_"))
            or (isinstance(node, ast.alias) and node.name.startswith("verify_agy_"))
            for node in nodes_by_scope[id(scope)]
        )
        if mentions_agy:
            names_by_scope[id(scope)].update(params & {"binary", "cmd"})
        for param, default in zip(scope.args.args[::-1], scope.args.defaults[::-1], strict=False):
            if _agy_value(default, set()):
                names_by_scope[id(scope)].add(param.arg)

    changed = True
    while changed:
        before = {key: frozenset(value) for key, value in names_by_scope.items()}
        for scope in scopes:
            names = names_by_scope[id(scope)]
            if scope is not tree:
                names.update(names_by_scope[id(tree)])
            for node in nodes_by_scope[id(scope)]:
                if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value and _agy_value(node.value, names):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        names.update(_bound_names(target))
                if isinstance(node, ast.Call) and (callee := functions.get(_call_name(node.func))):
                    for param, value in zip(callee.args.args, node.args, strict=False):
                        if not isinstance(value, ast.Constant) and _agy_value(value, names):
                            names_by_scope[id(callee)].add(param.arg)
                    for keyword in node.keywords:
                        if keyword.arg and _agy_value(keyword.value, names):
                            names_by_scope[id(callee)].add(keyword.arg)
        changed = before != {key: frozenset(value) for key, value in names_by_scope.items()}

    sites = []
    runners = {
        "run",
        "Popen",
        "call",
        "check_call",
        "check_output",
        "create_subprocess_exec",
        "InvocationPlan",
        "run_version_probe",
        "_ORIGINAL_SUBPROCESS_POPEN",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            runners.update(alias.asname or alias.name for alias in node.names if alias.name in runners)
    for scope in scopes:
        names = names_by_scope[id(scope)]
        ordinal = 0
        for node in nodes_by_scope[id(scope)]:
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node.func)
            if name not in runners:
                continue
            argv = [
                *node.args,
                *(keyword.value for keyword in node.keywords if keyword.arg in {"args", "cmd", "executable"}),
            ]
            if any(_agy_value(value, names) for value in argv):
                ordinal += 1
                sites.append(f"{getattr(scope, 'name', '<module>')}:{ordinal}")
    return sites


def _text_sites(source: str, suffix: str) -> list[str]:
    if suffix == ".sh":
        headers = list(re.finditer(r"(?m)^\s*([\w]+)\(\)\s*\{", source))
        pattern = r"\b\w+=\(\s*agy\b|(?m:^\s*(?:exec\s+|command\s+)?agy(?:\s|$))"
    else:
        headers = list(re.finditer(r"(?m)^(?:async\s+)?function\s+(\w+)\s*\(", source))
        pattern = r"\bspawn\(\s*(?:binary|agy_bin|['\"]agy['\"])\s*,|\brunChild\(\s*options\.binary\s*,"
    sites = []
    prefix = source[: headers[0].start()] if headers else source
    sites.extend(f"<module>:{ordinal}" for ordinal, _ in enumerate(re.finditer(pattern, prefix), 1))
    for index, header in enumerate(headers):
        body = source[header.end() : headers[index + 1].start() if index + 1 < len(headers) else len(source)]
        for ordinal, _ in enumerate(re.finditer(pattern, body), 1):
            if suffix == ".mjs" and "agy" not in header[1].lower() and not re.search(r"\bspawn\(", body):
                continue
            sites.append(f"{header[1]}:{ordinal}")
    return sites


def _find_sites(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    if path.suffix == ".py" and "agy" not in source.lower():
        return []
    return _python_sites(source) if path.suffix == ".py" else _text_sites(source, path.suffix)


def _assert_inventory(found: Counter, inventory: dict[str, str]) -> None:
    assert set(inventory.values()) <= STATUSES
    expected = Counter(inventory.keys())
    assert found == expected, (
        f"unaccounted starts: {sorted((found - expected).elements())}; "
        f"disappeared sites: {sorted((expected - found).elements())}"
    )


@pytest.mark.repo_wide
def test_every_agy_start_has_a_current_inventory_row():
    found = Counter(
        f"{path.relative_to(ROOT).as_posix()}::{site}"
        for path in sorted((ROOT / "scripts").rglob("*"))
        if path.is_file() and path.suffix in {".py", ".sh", ".mjs"}
        for site in _find_sites(path)
    )
    assert set(SPAWN_INVENTORY.values()) == STATUSES
    _assert_inventory(found, SPAWN_INVENTORY)


@pytest.mark.parametrize("removed", [False, True])
def test_inventory_refuses_added_or_disappeared_start(tmp_path, removed):
    path = tmp_path / "probe.py"
    path.write_text('def probe(agy_bin):\n subprocess.run([agy_bin, "--version"])\n', encoding="utf-8")
    sites = Counter(_find_sites(path))
    assert sites == Counter({"probe:1": 1})
    with pytest.raises(AssertionError, match="disappeared sites" if removed else "unaccounted starts"):
        _assert_inventory(Counter() if removed else sites, {"probe:1": "probe-exempt"} if removed else {})


def test_inventory_refuses_unknown_status():
    with pytest.raises(AssertionError):
        _assert_inventory(Counter({"probe:1": 1}), {"probe:1": "unknown"})


@pytest.mark.parametrize(
    "source,expected",
    [
        ('def direct():\n subprocess.run(["agy", "-p", prompt])', ["direct:1"]),
        ('from subprocess import run as launch\nlaunch(["agy", "--help"])', ["<module>:1"]),
        ('BINARY = shutil.which("agy")\ndef bound():\n subprocess.run([BINARY, "--help"])', ["bound:1"]),
        ('def bound():\n argv = ["agy", "-p", prompt]\n runner.run(argv)', ["bound:1"]),
        ('def parameter(agy_bin):\n subprocess.Popen([agy_bin, "-p", prompt])', ["parameter:1"]),
        ('def parameter(binary):\n if agent == "agy":\n  subprocess.run([binary, "-p", prompt])', ["parameter:1"]),
        (
            'def launch(binary):\n subprocess.run([binary, "--help"])\ndef caller():\n launch(binary=shutil.which("agy"))',
            ["launch:1"],
        ),
        ('def alias():\n binary = shutil.which("agy")\n argv = [binary, "-p", prompt]\n runner.run(argv)', ["alias:1"]),
        ('def seat(cmd):\n if agent == "agy":\n  argv = [cmd[0], "--version"]\n  subprocess.run(argv)', ["seat:1"]),
        (
            'def seat(cmd):\n if agent == "agy":\n  argv, env = wrap([cmd[0], "--version"])\n  subprocess.run(argv)',
            ["seat:1"],
        ),
        ('def unrelated():\n subprocess.run(["other-cli", "--help"])', []),
        ('def data():\n names = ["agy", "other"]\n consume(names)', []),
        (
            'def twice():\n subprocess.run(["agy", "--help"])\n subprocess.run(["agy", "--version"])',
            ["twice:1", "twice:2"],
        ),
    ],
)
def test_python_finder_recognizes_command_shapes(source, expected):
    assert _python_sites(source) == expected


@pytest.mark.parametrize(
    "source,suffix,expected",
    [
        ('launch() {\n local cmd=(agy --model "$MODEL")\n exec "${cmd[@]}"\n}', ".sh", ["launch:1"]),
        ("function start(binary) {\n const child = spawn(binary, args);\n}", ".mjs", ["start:1"]),
        ("async function runAgy() {\n return runChild(options.binary, args);\n}", ".mjs", ["runAgy:1"]),
        ("const child = spawn('agy', args);", ".mjs", ["<module>:1"]),
        ('cmd=(agy -p "$PROMPT")', ".sh", ["<module>:1"]),
        ('agy -p "$PROMPT"', ".sh", ["<module>:1"]),
    ],
)
def test_text_finder_recognizes_command_shapes(source, suffix, expected):
    assert _text_sites(source, suffix) == expected
