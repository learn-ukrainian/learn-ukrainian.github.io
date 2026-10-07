"""Conservative component inventory and explicit, independently callable commands.

This is a command wrapper, not CI selection or a certificate of independence.
Contract checks and prepared-artifact certification are reported separately.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import re
import signal
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter, deque
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path, PurePosixPath
from statistics import median

from scripts.ci import frontend_change_scope
from scripts.ci.junit_results import parse_junit
from scripts.common.jsonl import jsonl_lines
from scripts.common.repo_root import project_interpreter
from scripts.deploy import auto_deploy_eligibility
from scripts.storage.test_baseline import nodeid_to_junit_id

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "scripts/ci/components.json"
NODE_IDS = (
    "open-model-data", "atlas-data", "atlas-frontend", "practice-frontend",
    "curriculum-generation", "curriculum-display", "harness", "shared-core",
)


def repo_path(value: str) -> str:
    """Require a literal repository-relative POSIX path, preserving odd names."""
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise ValueError("expected a canonical repository-relative path")
    return value


def load_manifest(path: Path = MANIFEST) -> dict:
    """Validate structural safety before applying any ownership or command."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["schema_version"] != 1 or set(data["components"]) != set(NODE_IDS):
        raise ValueError("expected schema version 1 and the eight approved nodes")
    for pattern, owners in list(data["exact_paths"].items()) + [
        (entry["path"], entry["components"]) for entry in data["path_prefixes"]
    ]:
        repo_path(pattern.rstrip("/"))
        if not owners or len(owners) != len(set(owners)) or set(owners) - set(NODE_IDS):
            raise ValueError("invalid component ownership")
    if any(not entry["path"].endswith("/") for entry in data["path_prefixes"]):
        raise ValueError("prefix mappings must end with /")
    for node in data["components"].values():
        for name in node["test_files"]:
            repo_path(name)
            if "::" in name or not name.startswith("tests/") or not name.endswith(".py"):
                raise ValueError("declare test files, never persisted test IDs")
        for prefix in node["test_prefixes"]:
            repo_path(prefix.rstrip("/"))
            if not prefix.startswith("tests/") or not prefix.endswith("/"):
                raise ValueError("invalid test prefix")
        for command in node["build"] + node["verify"]:
            repo_path(command["cwd"]) if command["cwd"] != "." else None
            if not command["argv"] or not all(isinstance(arg, str) and arg for arg in command["argv"]):
                raise ValueError("commands require nonempty argv arrays")
    for edge in data["edges"]:
        if edge["producer"] not in NODE_IDS or edge["consumer"] not in NODE_IDS:
            raise ValueError("edge names an unknown node")
    return data


def tracked_paths(root: Path = ROOT) -> list[str]:
    """Use the complete index, including skip-worktree paths in sparse trees."""
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True, timeout=30,
    )
    return sorted(set(result.stdout.decode("utf-8", errors="surrogateescape").split("\0")) - {""})


def assign_path(path: str, manifest: dict) -> tuple[list[str], str]:
    """Exact overrides win; only the longest prefix establishes ownership."""
    try:
        repo_path(path)
    except ValueError:
        return list(NODE_IDS), "unmapped"
    unresolved = manifest.get("unresolved_edges", [])
    if any(path == edge["path"] or path.startswith(edge["path"].rstrip("/") + "/") for edge in unresolved):
        return list(NODE_IDS), "dynamic-unresolved"
    if path in manifest["exact_paths"]:
        return sorted(manifest["exact_paths"][path]), "exact"
    matches = [entry for entry in manifest["path_prefixes"] if path.startswith(entry["path"])]
    if not matches:
        return list(NODE_IDS), "unmapped"
    longest = max(len(entry["path"]) for entry in matches)
    candidates = {tuple(sorted(entry["components"])) for entry in matches if len(entry["path"]) == longest}
    if len(candidates) != 1:
        return list(NODE_IDS), "ambiguous"
    return list(candidates.pop()), "prefix"


def python_sources(root: Path = ROOT) -> dict[str, bytes]:
    """Read indexed blobs in one batch, overlaying only tracked worktree edits."""
    index = subprocess.run(["git", "ls-files", "-s", "-z"], cwd=root, check=True,
                           capture_output=True, timeout=30).stdout
    entries = {}
    for entry in index.decode("utf-8", errors="surrogateescape").split("\0"):
        if entry:
            meta, path = entry.split("\t", 1)
            _, sha, stage = meta.split()
            if stage != "0":
                raise ValueError("unmerged index cannot establish import closure")
            if path.endswith(".py"):
                entries[path] = sha
    changes = subprocess.run(["git", "diff", "--name-only", "-z"], cwd=root, check=True,
                             capture_output=True, timeout=30).stdout.decode().split("\0")
    overlays = tuple((path, (root / path).read_bytes() if (root / path).is_file() else b"")
                     for path in changes if path in entries)
    return indexed_python_sources(str(root), tuple(entries.items()), overlays)


@lru_cache(maxsize=2)
def indexed_python_sources(root: str, entries: tuple, overlays: tuple) -> dict[str, bytes]:
    """Cache by indexed blob identities and actual edited bytes, never by time."""
    result = subprocess.run(["git", "cat-file", "--batch"], cwd=root, check=True,
                            input="".join(sha + "\n" for _, sha in entries).encode(),
                            capture_output=True, timeout=60)
    sources = {}
    offset = 0
    for path, _ in entries:
        end = result.stdout.index(b"\n", offset)
        _, kind, size = result.stdout[offset:end].split()
        if kind != b"blob":
            raise ValueError("expected indexed source blob")
        offset = end + 1
        sources[path] = result.stdout[offset:offset + int(size)]
        offset += int(size) + 1
    sources.update(overlays)
    return sources


def literal_target(node: ast.AST, bindings: dict, file: str, seen: frozenset = frozenset()):
    """Evaluate only literal strings and pathlib composition; never execute code."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int)):
        return node.value
    if isinstance(node, ast.Name):
        if node.id == "__file__":
            return PurePosixPath(file)
        if node.id not in seen and len(bindings.get(node.id, [])) == 1:
            return literal_target(bindings[node.id][0], bindings, file, seen | {node.id})
    if isinstance(node, ast.BinOp):
        left = literal_target(node.left, bindings, file, seen)
        right = literal_target(node.right, bindings, file, seen)
        if isinstance(node.op, ast.Div) and isinstance(left, PurePosixPath) and isinstance(right, str):
            return left / right
        if isinstance(node.op, ast.Add) and isinstance(left, str) and isinstance(right, str):
            return left + right
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        base = literal_target(node.value, bindings, file, seen)
        if isinstance(base, PurePosixPath):
            return base.parent
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "parents":
        base = literal_target(node.value.value, bindings, file, seen)
        index = literal_target(node.slice, bindings, file, seen)
        if isinstance(base, PurePosixPath) and isinstance(index, int) and 0 <= index < len(base.parents):
            return base.parents[index]
    if isinstance(node, ast.Call):
        name = ast.unparse(node.func).split(".")[-1]
        if name in {"Path", "PurePosixPath", "_P", "str"} and len(node.args) == 1:
            value = literal_target(node.args[0], bindings, file, seen)
            if isinstance(value, (str, PurePosixPath)):
                return str(value) if name == "str" else PurePosixPath(value)
        if name in {"resolve", "absolute"} and isinstance(node.func, ast.Attribute) and not node.args:
            return literal_target(node.func.value, bindings, file, seen)
    return None


def call_name(node: ast.AST) -> str:
    """Read a dotted callee without serializing arbitrary call expressions."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = call_name(node.value)
        return f"{base}.{node.attr}" if base else ""
    return ""


def scan_runtime_edges(path: str, nodes: Sequence[ast.AST], bindings: dict, known_paths: set[str]) -> tuple[set, set]:
    """Track file/subprocess dependencies; unprovable runtime edges stay all-node."""
    edges, unresolved = set(), set()
    aliases = {"sys": "sys", "subprocess": "subprocess", "os": "os", "asyncio": "asyncio"}
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"

    def canonical(node):
        name = call_name(node)
        first, _, rest = name.partition(".")
        return aliases.get(first, first) + ("." + rest if rest else "")

    def target(value, line, reason):
        if value is not None and str(value) in known_paths:
            edges.add((path, str(value)))
        else:
            unresolved.add((path, line, reason))

    for node in nodes:
        if isinstance(node, (ast.Attribute, ast.Name)) and canonical(node).startswith("sys.path"):
            # Even a literal path can change precedence or expose an external tree.
            unresolved.add((path, node.lineno, "sys-path"))
        if not isinstance(node, ast.Call):
            continue
        name = canonical(node.func)
        leaf = node.func.attr if isinstance(node.func, ast.Attribute) else name.split(".")[-1]
        if leaf in {"open", "read_text", "read_bytes"}:
            expression = (node.func.value if leaf in {"read_text", "read_bytes"}
                          and isinstance(node.func, ast.Attribute) else
                          node.args[0] if node.args else next(
                              (kw.value for kw in node.keywords if kw.arg in {"file", "path"}), None))
            # Path.open() reads its receiver; builtins.open() reads its argument.
            if leaf == "open" and isinstance(node.func, ast.Attribute) and name not in {"builtins.open", "io.open", "codecs.open"}:
                expression = node.func.value
            target(literal_target(expression, bindings, path), node.lineno, "unresolved-file-read")
        if name in {"subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_call",
                    "subprocess.check_output", "subprocess.getoutput", "subprocess.getstatusoutput",
                    "os.system", "os.popen", "asyncio.create_subprocess_exec", "asyncio.create_subprocess_shell"}:
            expression = node.args[0] if node.args else next(
                (kw.value for kw in node.keywords if kw.arg == "args"), None)
            if isinstance(expression, ast.Name) and len(bindings.get(expression.id, [])) == 1:
                expression = bindings[expression.id][0]
            shell = any(kw.arg == "shell" and not (
                isinstance(kw.value, ast.Constant) and kw.value.value is False) for kw in node.keywords)
            if shell or not isinstance(expression, (ast.List, ast.Tuple)):
                unresolved.add((path, node.lineno, "unresolved-subprocess"))
                continue
            values = [literal_target(arg, bindings, path) for arg in expression.elts]
            # Recognize only a closed Python module/script invocation. Other
            # executables and their input flags require explicit edge proof.
            interpreter = bool(expression.elts) and (
                canonical(expression.elts[0]) == "sys.executable"
                or values[0] in {"python", "python3"})
            if any(value is None for value in values[1:]):
                unresolved.add((path, node.lineno, "unresolved-subprocess"))
            if interpreter and len(values) > 2 and values[1] == "-m" and isinstance(values[2], str):
                value = values[2].replace(".", "/") + ".py"
            elif interpreter and len(values) > 1:
                value = values[1]
            else:
                value = None
            target(value, node.lineno, "unresolved-subprocess")
    return edges, unresolved


def dependency_nodes(tree: ast.AST) -> list[ast.AST]:
    """Keep dependency syntax in ast.walk order without walking terminal leaves.

    Parsed constants, import aliases, operators and contexts cannot contain
    dependencies. Retain every other subtree, including defaults and decorators.
    """
    relevant = {ast.Assign, ast.AnnAssign, ast.Import, ast.ImportFrom,
                ast.FunctionDef, ast.AsyncFunctionDef, ast.Call, ast.Attribute, ast.Name}
    pending = deque([tree])
    nodes = []
    while pending:
        node = pending.popleft()
        if type(node) in relevant:
            nodes.append(node)
        pending.extend(child for child in ast.iter_child_nodes(node)
                       if child._fields and not isinstance(child, (ast.Constant, ast.alias)))
    return nodes


def scan_imports(sources: dict[str, bytes], known_paths: set[str] | None = None) -> dict:
    """Compute local import/load edges, retaining each unprovable target."""
    modules = {path[:-3].replace("/", ".").removesuffix(".__init__"): path for path in sources}
    packages = {".".join(name.split(".")[:index]) for name in modules
                for index in range(1, len(name.split(".")))}
    edges = set()
    unresolved = set()
    bare_packages = {name.split(".")[1] for name in packages if name.startswith("scripts.")}

    def resolve(module):
        # Legacy sys.path entries expose scripts packages without scripts.*.
        return modules.get(module) or modules.get("scripts." + module)

    def add_import(importer, module, *, required, line):
        target = resolve(module)
        if target:
            edges.add((importer, target))
            # Python imports execute each regular parent package as well.
            canonical = target[:-3].replace("/", ".").removesuffix(".__init__")
            for index in range(1, len(canonical.split("."))):
                parent = modules.get(".".join(canonical.split(".")[:index]))
                if parent and parent.endswith("/__init__.py"):
                    edges.add((importer, parent))
        elif required and module not in packages and "scripts." + module not in packages and (
            module == "scripts" or module.startswith("scripts.")
            or "scripts." + module in packages
            or module.split(".")[0] in bare_packages
        ):
            unresolved.add((importer, line, "missing-local-import"))

    for path, source in sources.items():
        try:
            tree = ast.parse(source, filename=path)
        except (SyntaxError, ValueError):
            unresolved.add((path, 0, "parse-error"))
            continue
        bindings = {}
        nodes = dependency_nodes(tree)
        has_specs = b"spec_from_file_location" in source
        loaders = {"__import__": ("module", 0)}
        wrappers = set()
        for node in nodes:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and node.value is not None:
                        bindings.setdefault(target.id, []).append(node.value)
            if isinstance(node, ast.ImportFrom) and node.module in {"importlib", "importlib.util", "runpy"}:
                for alias in node.names:
                    if alias.name in {"import_module", "spec_from_file_location", "run_path", "run_module"}:
                        loaders[alias.asname or alias.name] = (
                            "file" if alias.name in {"spec_from_file_location", "run_path"} else "module",
                            1 if alias.name == "spec_from_file_location" else 0,
                        )
            if (has_specs
                and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
                and child.func.attr == "spec_from_file_location"
                for child in ast.walk(node)
            )):
                wrappers.add(node.name)
        runtime_edges, runtime_unresolved = scan_runtime_edges(
            path, nodes, bindings, known_paths if known_paths is not None else set(sources))
        edges.update(runtime_edges)
        unresolved.update(runtime_unresolved)
        for node in nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    add_import(path, alias.name, required=True, line=node.lineno)
            elif isinstance(node, ast.ImportFrom):
                package = path[:-3].replace("/", ".").split(".")[:-1]
                base = ".".join(package[:len(package) - node.level + 1]) if node.level else ""
                base = ".".join(filter(None, (base, node.module)))
                add_import(path, base, required=True, line=node.lineno)
                for alias in node.names:
                    add_import(path, base + "." + alias.name, required=False, line=node.lineno)
            if not isinstance(node, ast.Call):
                continue
            name = call_name(node.func)
            leaf = name.split(".")[-1]
            kind, index = loaders.get(name, (None, 0))
            if leaf in {"import_module", "spec_from_file_location", "run_path", "run_module"}:
                kind = "file" if leaf in {"spec_from_file_location", "run_path"} else "module"
                index = 1 if leaf == "spec_from_file_location" else 0
            if name in wrappers:
                kind = "file"
                index = 1
            if not kind:
                continue
            expression = node.args[index] if len(node.args) > index else next(
                (kw.value for kw in node.keywords if kw.arg == (
                    "location" if kind == "file" and index == 1 else
                    "path_name" if kind == "file" else "mod_name" if leaf == "run_module" else "name"
                )), None)
            value = literal_target(expression, bindings, path) if expression is not None else None
            target = resolve(str(value)) if kind == "module" and value is not None else str(value)
            if target in sources:
                if kind == "module":
                    add_import(path, str(value), required=True, line=node.lineno)
                else:
                    edges.add((path, target))
            elif value is None or kind == "file" or str(value).startswith("scripts."):
                unresolved.add((path, node.lineno, "nonliteral-or-missing-load"))
    return {"file_edges": sorted(edges), "unresolved_edges": [
        {"path": path, "line": line, "reason": reason} for path, line, reason in sorted(unresolved)
    ], "python_files": len(sources)}


def import_graph(manifest: dict, root: Path = ROOT) -> dict:
    """Lift discovered file dependencies to node edges; assert mandatory imports."""
    sources = python_sources(root)
    graph = cached_import_scan(tuple(sources.items()), tuple(tracked_paths(root)))
    pairs = {(producer, consumer) for importer, target in graph["file_edges"]
             for producer in assign_path(target, manifest)[0]
             for consumer in assign_path(importer, manifest)[0]}
    missing = [edge["id"] for edge in manifest["edges"]
               if edge["kind"] in {"import", "dynamic"}
               and (edge["producer"], edge["consumer"]) not in pairs]
    # Artifact/schema boundaries are explicit contracts, not Python imports.
    pairs.update((e["producer"], e["consumer"]) for e in manifest["edges"]
                 if e["kind"] not in {"import", "dynamic"})
    return graph | {"node_edges": sorted(pairs), "missing_mandatory_edges": missing}


@lru_cache(maxsize=32)
def cached_import_scan(sources: tuple, known_paths: tuple = ()) -> dict:
    """Reuse an AST scan only when every indexed/current source byte is identical."""
    return scan_imports(dict(sources), set(known_paths) if known_paths else None)


def affected(paths: Sequence[str], manifest: dict, graph: dict | None = None) -> dict:
    """Select consumers transitively; shared or incomplete evidence selects all."""
    selected: set[str] = set()
    reasons = set()
    graph = graph if graph is not None else import_graph(manifest)
    for path in paths:
        owners, reason = assign_path(path, manifest)
        selected.update(owners)
        if reason not in {"exact", "prefix"}:
            reasons.add(reason)
    if paths and (graph["unresolved_edges"] or graph["missing_mandatory_edges"]
                  or any(not edge.get("resolved", False) for edge in manifest["edges"])):
        reasons.add("dynamic-unresolved")
        selected.update(NODE_IDS)
    while True:
        before = selected.copy()
        if "shared-core" in selected:
            selected.update(NODE_IDS)
        selected.update(consumer for producer, consumer in graph["node_edges"] if producer in selected)
        if before == selected:
            break
    return {"components": sorted(selected), "fallback_reasons": sorted(reasons), "changed_paths": len(paths),
            "import_edges": len(graph["file_edges"]), "unresolved_edges": len(graph["unresolved_edges"])}


def parity_gaps(paths: Sequence[str], manifest: dict, root: Path = ROOT, graph: dict | None = None) -> list[str]:
    """Cross-check existing selector semantics without deriving them from the map."""
    patterns = frontend_change_scope.load_denominator(root / manifest["selector_contracts"]["frontend_denominator"])["paths"]
    fronts = set(manifest["selector_contracts"]["frontend_components"])
    gaps = []
    graph = graph if graph is not None else import_graph(manifest, root)
    for path in paths:
        requires_front = frontend_change_scope.path_in_denominator(path, patterns)
        deploy = auto_deploy_eligibility.decide_auto_deploy([path]).deploy
        owners, _ = assign_path(path, manifest)
        # Check the declared boundary independently of all-node fallback.
        selected = set(owners)
        while True:
            before = selected.copy()
            selected.update(e["consumer"] for e in manifest["edges"] if e["producer"] in selected)
            if before == selected:
                break
        if (requires_front or deploy) and not fronts.issubset(selected):
            gaps.append(path)
    return gaps


def inventory(manifest: dict, root: Path = ROOT) -> dict:
    """Count explicit coverage, separately from conservative fallback selection."""
    paths = tracked_paths(root)
    graph = import_graph(manifest, root)
    missing = {kind: [] for kind in ("unmapped", "ambiguous", "dynamic-unresolved")}
    counts = dict.fromkeys(NODE_IDS, 0)
    unmapped_tests = []
    for path in paths:
        owners, reason = assign_path(path, manifest)
        if reason in missing:
            missing[reason].append(path)
            if path.startswith(("tests/", "site/tests/")):
                unmapped_tests.append(path)
        for owner in owners:
            counts[owner] += 1
    gaps = parity_gaps(paths, manifest, root, graph)
    return {
        "inventory_source": "git ls-files -z (index; includes sparse paths)",
        "tracked_paths": len(paths), "node_path_counts": counts,
        "unassigned": len(missing["unmapped"]), "ambiguous": len(missing["ambiguous"]),
        "dynamic_unresolved": len(graph["unresolved_edges"]) + len(missing["dynamic-unresolved"])
        + sum(not e.get("resolved", False) for e in manifest["edges"]),
        "unresolved_import_edges": len(graph["unresolved_edges"]),
        "import_graph": {key: value for key, value in graph.items() if key != "file_edges"},
        "import_edges": len(graph["file_edges"]),
        "unmapped_test_files": len(unmapped_tests), "selector_parity_gaps": len(gaps),
        "problems": missing, "parity_gaps": gaps,
    }


def test_files(component: str, manifest: dict, root: Path = ROOT) -> list[str]:
    """Resolve all mapped pytest files plus transitive source importers."""
    node = manifest["components"][component]
    files = set(node["test_files"])
    prefixes = tuple(node["test_prefixes"])
    paths = tracked_paths(root)
    tests = {path for path in paths if path.startswith("tests/")
             and PurePosixPath(path).name.startswith("test_") and path.endswith(".py")}
    files.update(path for path in tests if component in assign_path(path, manifest)[0]
                 or (prefixes and path.startswith(prefixes)))
    sources = {path for path in paths if not path.startswith("tests/")
               and component in assign_path(path, manifest)[0]}
    graph = import_graph(manifest, root)
    # Reverse traversal from *files*, rather than node SCCs, avoids treating
    # every test in a cyclic product pair as an importer of every source file.
    reverse = {}
    for importer, target in graph["file_edges"]:
        reverse.setdefault(target, set()).add(importer)
    # A non-literal loader can read any node's source. Its importers remain
    # obligations in every node's suite until the target is proven.
    sources.update(edge["path"] for edge in graph["unresolved_edges"])
    pending = list(sources)
    visited = set(sources)
    while pending:
        for importer in reverse.get(pending.pop(), ()):
            if importer not in visited:
                visited.add(importer)
                pending.append(importer)
    files.update(tests & visited)
    files.update(manifest.get("shared_integration_tests", []))
    if not files:
        raise ValueError("node has no declared contract tests")
    # Census is index-backed; collection, not sparse materialization, decides
    # whether the resolved set can execute in this worktree.
    return sorted(files)


def vitest_files(component: str, manifest: dict, root: Path = ROOT) -> list[str]:
    """Assign Vitest's configured test directories by the same path ownership."""
    return [path for path in tracked_paths(root)
            if path.startswith(("site/tests/unit/", "site/src/pages/__tests__/"))
            and re.search(r"\.(test|spec)\.tsx?$", path)
            and component in assign_path(path, manifest)[0]]


def node_test_commands(component: str, manifest: dict, files: list[str], front_files: list[str],
                       *, workers: int = 2, timeout: float | None = None) -> list[dict]:
    """Use pytest and existing site scripts; retain the built-output test tier."""
    commands = [{"argv": ["{python}", "-m", "pytest", "-q", "-n", str(workers), *files,
                           *manifest["components"][component]["test_args"]],
                 "cwd": ".", "scope": "complete-node-pytest", "timeout": timeout}]
    if front_files:
        built = set(manifest["vitest"]["built_output_files"])
        for script, subset in (("test:unit", sorted(set(front_files) - built)),
                               ("test:built-output", sorted(set(front_files) & built))):
            if subset:
                commands.append({"argv": ["npm", "run", script, "--", *(p.removeprefix("site/") for p in subset)],
                                 "cwd": "site", "scope": "complete-node-vitest", "timeout": timeout})
    return commands


def collect_tests(files: Sequence[str], args: Sequence[str], root: Path = ROOT) -> tuple[list[str], int]:
    """Collect fresh IDs; any collection error is a full-selection obligation."""
    result = subprocess.run(
        [str(project_interpreter(root)), "-m", "pytest", "--collect-only", "--verbosity=-1", *files, *args],
        cwd=root, capture_output=True, text=True, timeout=900,
    )
    ids = sorted(line.strip() for line in result.stdout.splitlines() if line.startswith("tests/") and "::" in line)
    return ids, result.returncode if result.returncode else (0 if ids else 5)


def collect_vitest(files: Sequence[str], root: Path = ROOT) -> tuple[list[dict], int]:
    """Collect Vitest IDs with its installed CLI, independently of pytest IDs."""
    if not files:
        return [], 0
    result = subprocess.run(["npm", "exec", "--", "vitest", "list", "--json",
                             *(path.removeprefix("site/") for path in files)],
                            cwd=root / "site", capture_output=True, text=True, timeout=180,
                            env=os.environ | {"npm_config_offline": "true"})
    if result.returncode:
        return [], result.returncode
    rows = json.loads(result.stdout)
    if not isinstance(rows, list) or not rows:
        return [], 5
    return rows, 0


def digest(value: object) -> str:
    """Hash canonical wrapper metadata, never log source bytes."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def current_identities(component: str, manifest: dict, root: Path = ROOT) -> dict[str, str]:
    """Bind source/config/lock identities to Git plus current tracked modifications.

    Sparse files use their indexed blob IDs; materialized modifications use Git's
    hash-object without writing objects. This never depends on a checkout census.
    """
    indexed = subprocess.run(["git", "ls-files", "-s", "-z"], cwd=root, capture_output=True, check=True, timeout=30)
    blobs = {}
    for entry in indexed.stdout.decode("utf-8", errors="surrogateescape").split("\0"):
        if entry:
            metadata, path = entry.split("\t", 1)
            mode, sha, stage = metadata.split()
            if stage != "0":
                raise ValueError("unmerged index cannot bind input identities")
            blobs[path] = [mode, sha]
    changed = subprocess.run(["git", "diff", "--name-only", "-z"], cwd=root,
                             capture_output=True, check=True, timeout=30).stdout.decode().split("\0")
    for path in filter(None, changed):
        if (root / path).is_file():
            sha = subprocess.run(["git", "hash-object", "--", path], cwd=root,
                                 capture_output=True, check=True, text=True, timeout=30).stdout.strip()
            blobs[path] = [blobs[path][0], sha]
        else:
            blobs[path] = ["deleted", ""]
    sources = {path: value for path, value in blobs.items() if component in assign_path(path, manifest)[0]}
    configs = {path: value for path, value in blobs.items()
               if path.startswith(("schemas/", "agents_extensions/", ".github/")) or path in {"pyproject.toml", "Makefile"}}
    locks = {path: value for path, value in blobs.items()
             if PurePosixPath(path).name in {"package-lock.json", "requirements-lock.txt", ".python-version", ".nvmrc"}}
    return {"source": digest(sources), "config": digest(configs), "lockfiles": digest(locks),
            "tools": digest({"node": manifest["components"][component], "manifest": manifest,
                             "runner": hashlib.sha256((root / "scripts/ci/components.py").read_bytes()).hexdigest()})}


def verify_inputs(path: Path, component: str, manifest: dict, root: Path = ROOT) -> dict[str, Path]:
    """Verify required families and every member before any output or subprocess.

    Existing family schemas/versions are declared rather than replaced here.
    These byte/identity checks do not grant publication or semantic approval.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "component-inputs.v1" or data.get("component") != component:
        raise ValueError("input wrapper schema/component mismatch")
    if data.get("identities") != current_identities(component, manifest, root):
        raise ValueError("stale source/tool/config/lockfile identities")
    required = set(manifest["components"][component]["input_families"])
    names = set()
    members: dict[str, Path] = {}
    for family in data["families"]:
        name = family["name"]
        if name in names or not family["schema"] or not family["version"] or not family["members"]:
            raise ValueError("duplicate or incomplete input family")
        names.add(name)
        for member in family["members"]:
            relative = repo_path(member["path"])
            target = (root / relative).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file():
                raise ValueError("missing or outside-worktree input member")
            if member["name"] in members or hashlib.sha256(target.read_bytes()).hexdigest() != member["sha256"]:
                raise ValueError("duplicate logical member or corrupt input bytes")
            members[member["name"]] = target
    if not required.issubset(names):
        raise ValueError("missing required input families")
    return members


def expand_command(command: dict, root: Path, output_dir: Path | None, members: dict[str, Path]) -> list[str]:
    """Substitute fixed placeholders into argv; no shell or caller-provided argv."""
    argv = []
    for arg in command["argv"]:
        arg = arg.replace("{python}", str(project_interpreter(root)))
        if "{output_dir}" in arg:
            if output_dir is None:
                raise ValueError("command requires --output-dir")
            arg = arg.replace("{output_dir}", str(output_dir.resolve()))
        for name in re.findall(r"\{member:([^}]+)\}", arg):
            if name not in members:
                raise ValueError("missing named command input member")
            arg = arg.replace("{member:" + name + "}", str(members[name]))
        if "{" in arg or "}" in arg:
            raise ValueError("unresolved command placeholder")
        argv.append(arg)
    return argv


def pytest_runtest_logreport(report):
    """Journal completed pytest phases on the controller, surviving wall timeouts."""
    journal = os.environ.get("LU_COMPONENT_TEST_JOURNAL")
    if journal and not os.environ.get("PYTEST_XDIST_WORKER"):
        with Path(journal).open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"id": report.nodeid, "when": report.when,
                                     "outcome": report.outcome}) + "\n")


def partial_test_results(journal: Path) -> dict:
    """Count unique test outcomes; setup/teardown errors outrank call passes."""
    outcomes = {}
    if journal.is_file():
        for line in jsonl_lines(journal.read_text(encoding="utf-8")):
            if not line:
                continue
            row = json.loads(line)
            if row["outcome"] == "failed" or outcomes.get(row["id"]) == "failed":
                outcomes[row["id"]] = "failed"
            elif row["outcome"] == "skipped" or row["when"] == "call":
                outcomes[row["id"]] = row["outcome"]
    return {**{key: sum(value == key for value in outcomes.values())
               for key in ("passed", "failed", "skipped")},
            "failing_test_ids": sorted(key for key, value in outcomes.items() if value == "failed")}


def execute_command(argv: list[str], *, cwd: Path, env: dict, timeout: float | None) -> tuple[int, bool]:
    """Wait in the foreground and reap the process group on a wall timeout."""
    with subprocess.Popen(argv, cwd=cwd, env=env, stdout=sys.stderr, start_new_session=True) as process:
        try:
            return process.wait(timeout=timeout), False
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            return 124, True


def run_commands(commands: list[dict], root: Path, output_dir: Path | None,
                 members: dict[str, Path], *, keep_going: bool = False) -> tuple[list[dict], int]:
    """Wait for every command; report timeout and retain partial pytest evidence."""
    reports = []
    overall_code = 0
    expanded = [(command, expand_command(command, root, output_dir, members)) for command in commands]
    for command, argv in expanded:
        with tempfile.TemporaryDirectory(prefix="component-check-") as scratch:
            junit = Path(scratch) / "junit.xml"
            journal = Path(scratch) / "results.jsonl"
            is_pytest = "pytest" in argv
            executed = [*argv, "-p", "scripts.ci.components", f"--junitxml={junit}"] if is_pytest else argv
            timeout = command.get("timeout", None if command["scope"].startswith("complete-node-") else 1800)
            env = os.environ | {"PYTHON": str(project_interpreter(root))}
            if is_pytest:
                env["LU_COMPONENT_TEST_JOURNAL"] = str(journal)
            returncode, timed_out = execute_command(executed, cwd=root / command["cwd"], env=env, timeout=timeout)
            stats = partial_test_results(journal)
            # Existing verify commands also retain their JUnit totals when a
            # plugin was not loaded (e.g. a separately installed pytest).
            if is_pytest and junit.is_file():
                results = parse_junit([junit])
                stats = {**{key: sum(r.outcome == key or (key == "failed" and r.outcome == "error")
                                    for r in results) for key in ("passed", "failed", "skipped")},
                         "failing_test_ids": sorted(r.node_id for r in results if r.outcome in {"failed", "error"})}
            code = returncode or (3 if stats["skipped"] else 0)
            reports.append({"argv": command["argv"], "cwd": command["cwd"], "scope": command["scope"],
                            "exit_code": returncode, "timeout_seconds": timeout, **stats,
                            "partial_results": timed_out,
                            "result": "timeout" if timed_out else "fail" if returncode else
                            "artifact-dependent" if stats["skipped"] else "pass"})
            if code:
                overall_code = overall_code or code
                if not keep_going:
                    return reports, code
    return reports, overall_code


def junit_coverage(paths: list[Path], manifest: dict, components: Sequence[str], root: Path = ROOT) -> tuple[dict, int]:
    """Compare freshly collected node IDs with full-run pytest JUnit outcomes."""
    if not paths:
        raise ValueError("JUnit input is required")
    rows = parse_junit(paths)
    if not rows:
        raise ValueError("JUnit input has no test cases")
    outcomes = {}
    module_outcomes = {}
    rank = {"passed": 0, "skipped": 1, "failed": 2, "error": 3}
    for row in rows:
        # Parameter values containing dots and classes without a Test prefix
        # use pytest's own classname/name identity, not guessed file names.
        if "::" not in row.node_id:
            if row.outcome not in {"skipped", "failed", "error"}:
                raise ValueError("module result has no test identity")
            if rank[row.outcome] >= rank.get(module_outcomes.get(row.node_id), -1):
                module_outcomes[row.node_id] = row.outcome
            continue
        identity = nodeid_to_junit_id(row.node_id)
        if rank[row.outcome] >= rank.get(outcomes.get(identity), -1):
            outcomes[identity] = row.outcome
    files = {node: test_files(node, manifest, root) for node in components}
    collected = {}
    for node in components:
        args = tuple(manifest["components"][node]["test_args"])
        if args not in collected:
            union = sorted({file for other in components
                            if tuple(manifest["components"][other]["test_args"]) == args
                            for file in files[other]})
            ids, code = collect_tests(union, args, root)
            if code:
                return {"selection": list(NODE_IDS), "fallback_reason": "collection-error",
                        "pytest_collection_exit": code}, code
            collected[args] = ids
    coverage = {}
    for node in components:
        selected_files = set(files[node])
        ids = sorted({id for id in collected[tuple(manifest["components"][node]["test_args"])]
                      if id.split("::", 1)[0] in selected_files})
        groups = {key: [] for key in ("passed", "failed", "skipped", "absent")}
        for id in ids:
            outcome = outcomes.get(nodeid_to_junit_id(id), "absent")
            groups["failed" if outcome == "error" else outcome].append(id)
        coverage[node] = {"collected": len(ids), "pytest_files": len(selected_files),
                          "module_results": {file: outcome for file, outcome in module_outcomes.items() if file in selected_files},
                          **{key: len(value) for key, value in groups.items()},
                          "failing_test_ids": groups["failed"], "absent_test_ids": groups["absent"],
                          "skipped_test_ids": groups["skipped"]}
    report = {"schema": "component-junit-coverage.v1",
              "head_sha": subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                                         capture_output=True, text=True, timeout=30).stdout.strip(),
              "junit_inputs": [{"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                               for path in paths], "nodes": coverage}
    # Skips and absent IDs are evidence gaps, never passing proof.
    return report, 1 if any(row[key] for row in coverage.values() for key in ("failed", "skipped", "absent", "module_results")) else 0


# Stage-1 reports only: no selector, shadow or execution path calls these helpers.
REPORT_FOLDING_RULES = (
    "Repository-relative string literals without '..' or absolute paths; integer literals only as parent indexes.",
    "Path/PurePosixPath from unshadowed module-level pathlib imports, with one literal/path argument; Path(__file__).",
    "Lexical .parent and .parents[n] with a nonnegative literal index within the repository; no filesystem traversal.",
    "Path / literal-string and os.path.join of accepted paths/strings from an unshadowed module-level os import.",
    "Single unconditional module-level constants defined before use, recursively built only from these forms; no other binding anywhere in the module.",
    "Reject computed strings, environment/argument/parameter/conditional/local/shadowed bindings, resolve/absolute, '..', unknown calls and module invocations.",
    "Every scanner site sharing file:line:reason must prove the same target; sys.path directories remain unresolved unless the target itself is tracked at both SHAs.",
)
REPORT_UNSOUND_CLASSES = (
    "resolve-identity", "absolute-identity", "single-binding-parameter",
    "single-binding-conditional", "single-binding-shadowed", "dropped-import-module",
    "subprocess-missing-parent-init", "pytest-plugins", "unseen-rglob", "unseen-glob",
    "unseen-iterdir", "unseen-sqlite-connect", "unseen-os-walk", "unseen-shutil-copy",
)


class ReportFolder:
    """A deliberately smaller lexical evaluator than the production scanner.

    Reject a symbol globally on any second definition, parameter, mutation or
    local/conditional binding. This sacrifices folds rather than guess scope.
    Paths are repository-root-relative; never consult cwd, symlinks or disk.
    """

    def __init__(self, tree: ast.Module, path: str):
        self.path = path
        self.nodes = list(ast.walk(tree))
        self.bindings = {}
        self.aliases = {}
        counts = Counter()
        for node in self.nodes:
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                counts[node.id] += 1
            elif isinstance(node, ast.arg):
                counts[node.arg] += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                counts[node.name] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    counts[alias.asname or alias.name.split('.')[0]] += 1
            elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name:
                counts[node.name] += 1
            elif isinstance(node, (ast.Global, ast.Nonlocal)):
                counts.update(node.names)
            if isinstance(node, (ast.Attribute, ast.Subscript)) and isinstance(node.ctx, (ast.Store, ast.Del)):
                base = node.value
                while isinstance(base, (ast.Attribute, ast.Subscript)):
                    base = base.value
                if isinstance(base, ast.Name):
                    counts[base.id] += 2
        self.counts = counts
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and counts[target.id] == 1:
                        self.bindings[target.id] = node.value
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    local = alias.asname or alias.name.split('.')[0]
                    if counts[local] == 1 and not getattr(node, 'level', 0):
                        qualified = (f'{node.module}.{alias.name}' if isinstance(node, ast.ImportFrom)
                                     else alias.name if alias.asname else local)
                        self.aliases[local] = (qualified, node.lineno)

    def canonical(self, node: ast.AST) -> str:
        """Only imports established before this use can identify a callable."""
        name = call_name(node)
        first, _, rest = name.partition('.')
        imported, line = self.aliases.get(first, ('', 0))
        if imported and line < node.lineno:
            return imported + ('.' + rest if rest else '')
        return name if first == 'open' and not self.counts[first] else ''

    def value(self, node: ast.AST | None, seen: frozenset = frozenset()):
        """Return a string/path/integer only for the documented closed grammar."""
        if isinstance(node, ast.Constant) and type(node.value) in {str, int}:
            if isinstance(node.value, str) and (PurePosixPath(node.value).is_absolute()
                                              or '..' in PurePosixPath(node.value).parts):
                return None
            return node.value
        if isinstance(node, ast.Name):
            if node.id == '__file__':
                return PurePosixPath(self.path) if not self.counts[node.id] else None
            expression = self.bindings.get(node.id)
            if expression is not None and node.id not in seen and expression.lineno < node.lineno:
                return self.value(expression, seen | {node.id})
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            left, right = self.value(node.left, seen), self.value(node.right, seen)
            if isinstance(left, PurePosixPath) and isinstance(right, str):
                return left / right
        if isinstance(node, ast.Attribute) and node.attr == 'parent':
            base = self.value(node.value, seen)
            if isinstance(base, PurePosixPath) and base != PurePosixPath('.'):
                return base.parent
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == 'parents':
            base = self.value(node.value.value, seen)
            index = node.slice.value if isinstance(node.slice, ast.Constant) else None
            if isinstance(base, PurePosixPath) and type(index) is int and 0 <= index < len(base.parents):
                return base.parents[index]
        if isinstance(node, ast.Call) and not node.keywords:
            name = self.canonical(node.func)
            if name in {'pathlib.Path', 'pathlib.PurePosixPath'} and len(node.args) == 1:
                value = self.value(node.args[0], seen)
                if isinstance(value, (str, PurePosixPath)):
                    return PurePosixPath(value)
            if name == 'os.path.join' and node.args:
                values = [self.value(arg, seen) for arg in node.args]
                if all(isinstance(value, (str, PurePosixPath)) for value in values):
                    return str(PurePosixPath(*values))
        return None

    def target(self, expression: ast.AST | None) -> str | None:
        """Integers and empty strings cannot prove file targets."""
        value = self.value(expression)
        return str(value) if isinstance(value, (str, PurePosixPath)) and str(value) else None


def report_sites(tree: ast.Module, *, legacy_wrappers: bool = False) -> list[tuple]:
    """Locate scanner dependency expressions without changing its scanner.

    Match its leaf-based reads/loaders and aliases. Unknown wrapper calls stay
    not-foldable. sys.path is a target only for append/insert with exact arity.
    Subprocess module invocations stay unproven (parent initializers are omitted).
    """
    aliases = {}
    wrappers = {node.name for node in ast.walk(tree)
                if legacy_wrappers and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and any(isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
                        and child.func.attr == 'spec_from_file_location' for child in ast.walk(node))}
    for node in dependency_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                aliases[alias.asname or alias.name] = (f'{node.module}.{alias.name}'
                                                      if isinstance(node, ast.ImportFrom) else alias.name)
    sites = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node.func)
        first, _, rest = name.partition('.')
        name = aliases.get(first, first) + ('.' + rest if rest else '')
        leaf = node.func.attr if isinstance(node.func, ast.Attribute) else name.split('.')[-1]
        expression = None
        reason = None
        if leaf in {'open', 'read_text', 'read_bytes'}:
            reason = 'unresolved-file-read'
            expression = (node.func.value if isinstance(node.func, ast.Attribute)
                          and (leaf != 'open' or name not in {'builtins.open', 'io.open', 'codecs.open'})
                          else node.args[0] if node.args else next(
                              (kw.value for kw in node.keywords if kw.arg in {'file', 'path'}), None))
        elif name in {'subprocess.run', 'subprocess.Popen', 'subprocess.call', 'subprocess.check_call',
                      'subprocess.check_output', 'subprocess.getoutput', 'subprocess.getstatusoutput',
                      'os.system', 'os.popen', 'asyncio.create_subprocess_exec', 'asyncio.create_subprocess_shell'}:
            reason = 'unresolved-subprocess'
            expression = node.args[0] if node.args else next((kw.value for kw in node.keywords if kw.arg == 'args'), None)
        elif leaf in {'spec_from_file_location', 'run_path', 'import_module', 'run_module'} or name == '__import__':
            reason = 'nonliteral-or-missing-load'
            index = 1 if leaf == 'spec_from_file_location' else 0
            expression = node.args[index] if len(node.args) > index else next(
                (kw.value for kw in node.keywords if kw.arg == (
                    'location' if index else 'path_name' if leaf == 'run_path' else
                    'mod_name' if leaf == 'run_module' else 'name')), None)
        elif name in {'sys.path.append', 'sys.path.insert'}:
            reason = 'sys-path'
            if not node.keywords and len(node.args) == (2 if name.endswith('insert') else 1):
                expression = node.args[-1]
        elif name in wrappers:
            reason = 'nonliteral-or-missing-load'
            expression = node.args[1] if len(node.args) > 1 else next((kw.value for kw in node.keywords if kw.arg == 'location'), None)
        if reason:
            sites.append((node, name, reason, expression))
    return sites


def report_site_target(folder: ReportFolder, site: tuple) -> str | None:
    """Prove only direct file loads/reads and closed, two-argument Python scripts."""
    node, _name, reason, expression = site
    if reason == 'nonliteral-or-missing-load' and folder.canonical(node.func) not in {'importlib.util.spec_from_file_location', 'runpy.run_path'}:
        return None
    if reason == 'unresolved-subprocess':
        if any(kw.arg not in {'shell'} or not isinstance(kw.value, ast.Constant) or kw.value.value is not False
               for kw in node.keywords):
            return None
        if not isinstance(expression, (ast.List, ast.Tuple)) or len(expression.elts) != 2:
            return None
        command, target = expression.elts
        if folder.value(command) not in {'python', 'python3'} and folder.canonical(command) != 'sys.executable':
            return None
        return folder.target(target)
    return folder.target(expression)


def report_edge_folds(sources: dict[str, bytes], unresolved: list[dict]) -> list[dict]:
    """Classify every recorded edge; a merged scanner line needs unanimous proof."""
    by_path = {}
    for edge in unresolved:
        by_path.setdefault(edge['path'], []).append(edge)
    result = []
    for path, edges in sorted(by_path.items()):
        candidates = {}
        try:
            tree = ast.parse(sources[path])
            folder = ReportFolder(tree, path)
            for site in report_sites(tree):
                candidates.setdefault((site[0].lineno, site[2]), []).append(report_site_target(folder, site))
        except (SyntaxError, ValueError, KeyError):
            pass
        for edge in edges:
            values = candidates.get((edge['line'], edge['reason']), [])
            target = values[0] if values and values[0] is not None and len(set(values)) == 1 else None
            result.append(edge | {'classification': 'constant-foldable' if target is not None else 'not-foldable',
                                  'folded_target': target})
    return sorted(result, key=lambda edge: (edge['path'], edge['line'], edge['reason']))


def report_unsound_sites(path: str, source: bytes, modules: set[str], sources: dict[str, bytes]) -> set:
    """Locate the requested legacy unsafe forms in one Python source."""
    found = set()
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return found
    nodes = dependency_nodes(tree)
    bindings = {}
    assignments = {}
    for node in nodes:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
                if isinstance(target, ast.Name):
                    bindings.setdefault(target.id, []).append(node.value)
                    assignments.setdefault(target.id, []).append(node)
    folder = ReportFolder(tree, path)
    parameters = {node.arg for node in ast.walk(tree) if isinstance(node, ast.arg)}
    aliases = {alias.asname or alias.name: (f'{item.module}.{alias.name}'
               if isinstance(item, ast.ImportFrom) else alias.name)
               for item in nodes if isinstance(item, (ast.Import, ast.ImportFrom)) for alias in item.names}

    def add(kind, node):
        found.add((kind, path, node.lineno, node.col_offset))

    def legacy_folds(expression, seen=frozenset()):
        if expression is None:
            return
        for node in ast.walk(expression):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in {'resolve', 'absolute'} and literal_target(node, bindings, path) is not None):
                add(node.func.attr + '-identity', node)
            if isinstance(node, ast.Name) and node.id not in seen and len(bindings.get(node.id, [])) == 1:
                if literal_target(node, bindings, path) is None:
                    continue
                binding = assignments[node.id][0]
                if node.id in parameters:
                    add('single-binding-parameter', node)
                # Assignments under if/loop/try/with/match, not function locals.
                parents = parent_nodes.get(binding, [])
                if any(isinstance(parent, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try,
                                           ast.TryStar, ast.With, ast.AsyncWith, ast.Match)) for parent in parents):
                    add('single-binding-conditional', node)
                if folder.counts[node.id] > 1 and node.id not in parameters:
                    add('single-binding-shadowed', node)
                legacy_folds(bindings[node.id][0], seen | {node.id})

    parent_nodes = {}

    def ancestors(node, parents):
        parent_nodes[node] = parents
        for child in ast.iter_child_nodes(node):
            ancestors(child, [*parents, node])

    ancestors(tree, [])
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == 'pytest_plugins' for target in targets):
                add('pytest-plugins', node)
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node.func)
        # Legacy aliases include local/conditional imports, just as the scanner does.
        first, _, rest = name.partition('.')
        name = aliases.get(first, first) + ('.' + rest if rest else '')
        leaf = node.func.attr if isinstance(node.func, ast.Attribute) else name.split('.')[-1]
        if leaf in {'rglob', 'glob', 'iterdir'}:
            add('unseen-' + leaf, node)
        if name == 'sqlite3.connect':
            add('unseen-sqlite-connect', node)
        if name == 'os.walk':
            add('unseen-os-walk', node)
        if name in {'shutil.copy', 'shutil.copy2', 'shutil.copyfile', 'shutil.copytree', 'shutil.copyfileobj'}:
            add('unseen-shutil-copy', node)
    for site in report_sites(tree, legacy_wrappers=True):
        node, name, reason, expression = site
        legacy_folds(expression)
        if name.split('.')[-1] == 'import_module':
            value = literal_target(expression, bindings, path)
            if isinstance(value, str) and not value.startswith('scripts.') and value not in modules and 'scripts.' + value not in modules:
                add('dropped-import-module', node)
        if reason == 'unresolved-subprocess':
            argv = bindings.get(expression.id, [None])[0] if isinstance(expression, ast.Name) and len(bindings.get(expression.id, [])) == 1 else expression
            if not isinstance(argv, (ast.List, ast.Tuple)):
                continue
            values = [literal_target(arg, bindings, path) for arg in argv.elts]
            command = call_name(argv.elts[0]) if argv.elts else ''
            first, _, rest = command.partition('.')
            command = aliases.get(first, first) + ('.' + rest if rest else '')
            if (len(values) > 2 and (values[0] in {'python', 'python3'} or command == 'sys.executable')
                and values[1] == '-m' and isinstance(values[2], str) and values[2].replace('.', '/') + '.py' in sources):
                add('subprocess-missing-parent-init', node)
    return found


def report_unsound_census(sources: dict[str, bytes]) -> dict:
    """Inventory specified legacy assumptions and unobserved syntax, never fix them.

    Count distinct (class,file,line,column) occurrences. For legacy folds follow
    the scanner's actual single-binding evaluator, including constant references.
    File APIs/plugin declarations are syntactic blind spots, not resolved edges.
    """
    found = set()
    modules = {p[:-3].replace('/', '.').removesuffix('.__init__') for p in sources}
    for path, source in sorted(sources.items()):
        found.update(report_unsound_sites(path, source, modules, sources))
    occurrences = [{'class': kind, 'path': path, 'line': line, 'column': column, 'location': f'{path}:{line}'}
                   for kind, path, line, column in sorted(found)]
    return {'count': len(occurrences), 'by_class': {kind: sum(row['class'] == kind for row in occurrences)
                                                  for kind in REPORT_UNSOUND_CLASSES},
            'occurrences': occurrences,
            'basis': 'legacy evaluator fold sites plus specified syntactic blind spots; not a completeness proof'}


def report_census(manifest: dict, root: Path = ROOT) -> dict:
    """Emit every edge, class/component counts, folds, top sources and blind spots."""
    graph = import_graph(manifest, root)
    sources = python_sources(root)
    edges = report_edge_folds(sources, graph['unresolved_edges'])
    for edge in edges:
        edge['source_components'] = sorted(assign_path(edge['path'], manifest)[0])
    missing = [edge | {'reason': 'missing-mandatory-edge', 'source_components': [edge['consumer']],
                       'classification': 'not-foldable', 'folded_target': None}
               for edge in manifest['edges'] if edge['id'] in graph['missing_mandatory_edges']]
    classes = sorted({edge['reason'] for edge in edges + missing})
    counts = {kind: {component: sum(edge['reason'] == kind and component in edge['source_components']
                                  for edge in edges + missing) for component in NODE_IDS} for kind in classes}
    top_files = {}
    for kind in classes:
        files = Counter(edge['path'] for edge in edges if edge['reason'] == kind)
        top_files[kind] = [{'path': path, 'count': count} for path, count in sorted(files.items(), key=lambda item: (-item[1], item[0]))[:20]]
    return {'schema': 'component-edge-census.v1', 'report_only': True, 'folding_rules': REPORT_FOLDING_RULES,
            'unresolved_edge_count': len(edges), 'missing_mandatory_edge_count': len(missing),
            'folding_counts': dict(sorted(Counter(edge['classification'] for edge in edges).items())),
            'by_class': dict(sorted(Counter(edge['reason'] for edge in edges + missing).items())),
            'by_class_component': counts, 'component_counts_overlap': True, 'top_20_source_files': top_files,
            'unresolved_edges': edges, 'missing_mandatory_edges': missing,
            'known_unsound_resolutions': report_unsound_census(sources),
            'graph_digest': digest(graph), 'source_digest': digest([(path, hashlib.sha256(content).hexdigest()) for path, content in sorted(sources.items())])}


def report_tracked_at(sha: str, root: Path = ROOT) -> frozenset[str]:
    """Commit-tree oracle only: includes ignored and sparse files, never the index."""
    raw = subprocess.run(['git', 'ls-tree', '-r', '-z', '--name-only', sha], cwd=root,
                         check=True, capture_output=True, timeout=30).stdout
    return frozenset(raw.decode('utf-8', errors='surrogateescape').split('\0')) - {''}


def report_merge_paths(sha: str, root: Path = ROOT) -> tuple[str, list[str]]:
    """First-parent diff with NUL-safe rename/copy records and both sides retained."""
    from scripts.ci import dependency_change_scope

    parent = subprocess.run(['git', 'rev-parse', '--verify', sha + '^1'], cwd=root,
                            check=True, capture_output=True, timeout=30).stdout.decode().strip()
    raw = subprocess.run(['git', '-c', 'core.quotePath=false', 'diff', '--no-ext-diff',
                          '--name-status', '-M', '-C', '-z', parent, sha], cwd=root,
                         check=True, capture_output=True, timeout=30).stdout
    return parent, dependency_change_scope._parse_name_status_z(raw)


def report_closure(paths: Sequence[str], manifest: dict, graph: dict, extra_edges: Sequence[tuple] = (), *, force: bool = False) -> list[str]:
    """Hypothetical report closure; no global scanner-unresolved trigger."""
    selected = {owner for path in paths for owner in assign_path(path, manifest)[0]}
    pairs = set(graph['node_edges']) | {(producer, consumer) for importer, target in extra_edges
                                       for producer in assign_path(target, manifest)[0]
                                       for consumer in assign_path(importer, manifest)[0]}
    if paths and (force or graph['missing_mandatory_edges'] or any(not edge.get('resolved', False) for edge in manifest['edges'])):
        selected.update(NODE_IDS)
    while True:
        before = selected.copy()
        if 'shared-core' in selected:
            selected.update(NODE_IDS)
        selected.update(consumer for producer, consumer in pairs if producer in selected)
        if selected == before:
            return sorted(selected)


def report_test_files(component: str, manifest: dict, paths: Sequence[str], graph: dict, unresolved: Sequence[dict], extra_edges: Sequence[tuple] = ()) -> list[str]:
    """test_files semantics with this rule's unresolved set; never call affected."""
    node = manifest['components'][component]
    tests = {path for path in paths if path.startswith('tests/') and PurePosixPath(path).name.startswith('test_') and path.endswith('.py')}
    prefixes = tuple(node['test_prefixes'])
    files = set(node['test_files']) | {path for path in tests if component in assign_path(path, manifest)[0]
                                     or (prefixes and path.startswith(prefixes))}
    visited = {path for path in paths if not path.startswith('tests/') and component in assign_path(path, manifest)[0]}
    visited.update(edge['path'] for edge in unresolved)
    reverse = {}
    for importer, target in list(graph['file_edges']) + list(extra_edges):
        reverse.setdefault(target, set()).add(importer)
    pending = list(visited)
    while pending:
        for importer in reverse.get(pending.pop(), ()):
            if importer not in visited:
                visited.add(importer)
                pending.append(importer)
    files.update(tests & visited)
    files.update(manifest.get('shared_integration_tests', []))
    if not files:
        raise ValueError('node has no declared contract tests')
    return sorted(files)


def report_price(selected: Sequence[str], manifest: dict, paths: Sequence[str], graph: dict, unresolved: Sequence[dict], durations: dict, extra_edges: Sequence[tuple] = ()) -> dict:
    """Price deselected tracked pytest files; missing durations stay unpriced."""
    tests = {path for path in paths if path.startswith('tests/') and PurePosixPath(path).name.startswith('test_') and path.endswith('.py')}
    chosen = {path for component in selected for path in report_test_files(component, manifest, paths, graph, unresolved, extra_edges)}
    skipped = tests - chosen
    unpriced = sorted(tests - durations.keys())
    return {'would_skip_seconds': round(sum(durations[path] for path in sorted(skipped) if path in durations), 6),
            'would_skip_test_files': sorted(skipped), 'unpriced_test_files': unpriced,
            'would_skip_unpriced_test_files': sorted(skipped & set(unpriced)), 'unresolved_edge_count': len(unresolved)}


def report_what_if(prs_file: Path, manifest: dict, root: Path = ROOT) -> dict:
    """Measure a fixed current-tree graph against commit diffs, never CI results."""
    raw = prs_file.read_bytes()
    records = []
    for line in raw.decode('utf-8').splitlines():
        fields = line.split()
        if len(fields) != 3 or not fields[0].isdigit() or not re.fullmatch('[0-9a-f]{7,40}', fields[1]):
            raise ValueError('expected PR number, unambiguous merge SHA and merged-at timestamp')
        records.append((int(fields[0]), fields[1], fields[2]))
    if not records or len({pr for pr, _, _ in records}) != len(records):
        raise ValueError('expected nonempty distinct PR records')
    records.sort()
    graph = import_graph(manifest, root)
    folded = report_edge_folds(python_sources(root), graph['unresolved_edges'])
    paths = tracked_paths(root)
    duration_bytes = (root / 'scripts/ci/pytest-file-durations.json').read_bytes()
    durations = json.loads(duration_bytes)
    if any(not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 for value in durations.values()):
        raise ValueError('expected finite nonnegative file durations')
    unresolved = graph['unresolved_edges']
    all_sources = {edge['path'] for edge in unresolved}
    source_blocks = {path for path in all_sources if 'shared-core' in report_closure([path], manifest, graph)}
    blocking_counts = Counter()
    rows = []
    tree_cache = {}
    price_cache = {}
    block_cache = {}
    for pr, sha, merged_at in records:
        supplied_sha = sha
        sha = subprocess.run(['git', 'rev-parse', '--verify', sha + '^{commit}'], cwd=root,
                             check=True, capture_output=True, timeout=30).stdout.decode().strip()
        parent, changed = report_merge_paths(sha, root)
        for commit in (parent, sha):
            if commit not in tree_cache:
                tree_cache[commit] = report_tracked_at(commit, root)
        both = tree_cache[parent] & tree_cache[sha]
        sound = [edge for edge in folded if edge['folded_target'] in both]
        retired = {(edge['path'], edge['line'], edge['reason']) for edge in sound}
        r2 = [edge for edge in unresolved if (edge['path'], edge['line'], edge['reason']) not in retired]
        extra = sorted({(edge['path'], edge['folded_target']) for edge in sound})
        extra_key = tuple(extra)
        if extra_key not in block_cache:
            block_cache[extra_key] = {path for path in all_sources if 'shared-core' in report_closure([path], manifest, graph, extra)}
        blockers = {edge['path'] for edge in r2} & block_cache[extra_key]
        blocking_counts.update((edge['path'], edge['line'], edge['reason']) for edge in r2 if edge['path'] in blockers)
        r3 = [edge for edge in r2 if edge['path'] not in blockers]
        r0 = affected(changed, manifest, graph)
        baseline = report_closure(changed, manifest, graph, force=bool(unresolved))
        if baseline != r0['components']:
            raise ValueError('R0 does not equal affected')
        rules = {}
        for rule, remaining, additions in [('R0', unresolved, []), ('R1', unresolved, []), ('R2', r2, extra), ('R3', r3, extra)]:
            selected = baseline if rule == 'R0' else report_closure(sorted(set(changed) | {edge['path'] for edge in remaining}), manifest, graph, additions)
            key = (tuple(selected), tuple((edge['path'], edge['line'], edge['reason']) for edge in remaining), tuple(additions))
            if key not in price_cache:
                price_cache[key] = report_price(selected, manifest, paths, graph, remaining, durations, additions)
            rules[rule] = {'components': selected, 'narrowed': len(selected) < len(NODE_IDS), **price_cache[key]}
        rows.append({'pr': pr, 'supplied_merge_sha': supplied_sha, 'merge_sha': sha, 'first_parent': parent, 'merged_at': merged_at,
                     'changed_path_count': len(changed), 'changed_paths': changed, 'R0_equals_affected': True,
                     'sound_fold_count': len(sound), 'R2_blocking_edge_count': sum(edge['path'] in blockers for edge in r2), 'rules': rules})
    blocking = []
    for edge in unresolved:
        key = (edge['path'], edge['line'], edge['reason'])
        if edge['path'] in source_blocks or blocking_counts[key]:
            blocking.append(edge | {'location': f"{edge['path']}:{edge['line']}",
                                    'R1': edge['path'] in source_blocks, 'R2_pr_count': blocking_counts[key]})
    aggregate = {}
    for rule in ('R0', 'R1', 'R2', 'R3'):
        values = [row['rules'][rule] for row in rows]
        count = sum(value['narrowed'] for value in values)
        aggregate[rule] = {'narrowed_pr_count': count, 'pr_count': len(rows), 'share_narrowed': count / len(rows),
                           'total_would_skip_seconds': round(sum(value['would_skip_seconds'] for value in values), 6),
                           'median_would_skip_seconds': median(value['would_skip_seconds'] for value in values)}
    return {'schema': 'component-what-if.v1', 'report_only': True, 'hypothetical': ['R1', 'R2', 'R3'],
            'rule_labels': {'R0': "Today's affected (equality asserted)", 'R1': 'HYPOTHETICAL unresolved readers as changes',
                            'R2': 'HYPOTHETICAL R1 with proven folds tracked in both commit trees',
                            'R3': 'HYPOTHETICAL ABLATION: UPPER BOUND, NOT ACHIEVABLE WITHOUT PROOF'},
            'prs_sha256': hashlib.sha256(raw).hexdigest(), 'pr_count': len(rows), 'folding_rules': REPORT_FOLDING_RULES,
            'graph_digest': digest(graph), 'pricing_basis': 'current indexed tracked pytest files; rule-specific unresolved obligations; no affected calls in pricing',
            'node_edges': graph['node_edges'], 'missing_mandatory_edges': graph['missing_mandatory_edges'],
            'unresolved_manifest_edges': [edge['id'] for edge in manifest['edges'] if not edge.get('resolved', False)],
            'durations_sha256': hashlib.sha256(duration_bytes).hexdigest(), 'aggregate': aggregate,
            'blocking_set': sorted(blocking, key=lambda edge: (edge['reason'], edge['path'], edge['line'])),
            'blocking_set_counts': {'R1': sum(edge['R1'] for edge in blocking),
                                    'R2_union': sum(edge['R2_pr_count'] > 0 for edge in blocking)}, 'prs': rows}


def parser() -> argparse.ArgumentParser:
    """Expose the complete wrapper contract in root and subcommand help."""
    examples = (
        "Examples:\n  .venv/bin/python -m scripts.ci.components inventory --check\n"
        "  .venv/bin/python -m scripts.ci.components test --component atlas-data --workers 2\n"
        "  .venv/bin/python -m scripts.ci.components junit --junit artifacts/pytest-shard-1.xml\n"
        "  .venv/bin/python -m scripts.ci.components test --component atlas-frontend --list\n"
        "  .venv/bin/python -m scripts.ci.components build --component atlas-frontend "
        "--inputs inputs.json --output-dir site/dist\n"
        "Defaults: complete-node pytest uses two workers; collection has a 15-minute timeout, "
        "complete-node commands no wall timeout (pytest per-test timeouts apply), other commands 30 minutes.\n"
        "Outputs: JSON on stdout; test processes; builds write declared outputs, curriculum producers "
        "write canonical worktree files. No CI/Pages selection, network preparation or publication.\n"
        "Exit codes: 0 checks passed; 1 inventory/command failure or JUnit failed/skipped/absent IDs; 2 invalid arguments/input; "
        "3 skipped/artifact-dependent checks; 124 wall timeout with partial results; collection/producer exits propagated.\n"
        "Input wrapper: schema=component-inputs.v1, component=ID, identities=the identities object from\n"
        "inventory --component ID --identities, families=[{name, schema, version, members}]. Each member\n"
        "has a unique logical name, repository-relative path and sha256. Required families and exact\n"
        "build argv are exposed by list. Verify without --inputs runs code contracts only; an exit 0\n"
        "does not certify artifact readiness, independence or learner behavior.\n"
        "Related: scripts/ci/components.json; plans/component-separation-9721.md v2; #9884."
    )
    description = (
        "Inventory tracked paths and run explicit component contract suites/consumer commands.\n"
        "Use for local checks with prepared inputs; do not use as CI selection or learner certification."
    )
    result = argparse.ArgumentParser(description=description, epilog=examples,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    subs = result.add_subparsers(dest="operation", required=True, help="Interface: list/test/build/verify/inventory/affected/junit; report-only census/what-if")
    for operation in ("list", "test", "build", "verify", "inventory", "affected", "junit"):
        sub = subs.add_parser(operation, help=f"{operation} component contracts", description=description,
                              epilog=examples, formatter_class=argparse.RawDescriptionHelpFormatter)
        if operation in {"test", "build", "verify", "inventory", "junit"}:
            sub.add_argument("--component", choices=NODE_IDS, required=operation in {"test", "build", "verify"},
                             help="Node ID, e.g. atlas-data; inventory/junit default: all nodes")
        if operation in {"build", "verify"}:
            sub.add_argument("--inputs", type=Path, required=operation == "build",
                             help="Prepared component-inputs.v1 JSON (e.g. inputs.json); verify default: code-contract checks only")
            sub.add_argument("--output-dir", type=Path, required=operation == "build",
                             help="Build output directory (e.g. site/dist); verify default: no output directory")
        if operation == "inventory":
            sub.add_argument("--check", action="store_true", help="Fail on unassigned/ambiguous paths, unmapped tests, parity gaps or missing mandatory edges; unresolved imports are reported and all-select; default: report only")
            sub.add_argument("--collect", action="store_true", help="Collect fresh contract-suite test IDs for --component (required); default: file census only")
            sub.add_argument("--identities", action="store_true", help="Include current input-binding identities for --component (required); default: omitted")
        if operation == "junit":
            sub.add_argument("--junit", nargs="+", type=Path, required=True,
                             help="Full CI pytest JUnit XML paths, e.g. artifacts/shard-1.xml; required")
        if operation == "test":
            sub.add_argument("--workers", type=int, default=2,
                             help="Pytest worker count, e.g. 2; default: 2 (dispatch caps still apply)")
            sub.add_argument("--timeout", type=float,
                             help="Positive wall timeout in seconds, e.g. 7200; default: none (pytest per-test timeouts apply)")
            sub.add_argument("--list", action="store_true", help="List complete resolved pytest/Vitest file sets and counts without execution; default: run all")
        if operation == "affected":
            sub.add_argument("paths", nargs="*", help="Changed repository-relative paths, e.g. scripts/config.py; default: empty set")
            sub.add_argument("--paths-file", type=Path, help="NUL-delimited git diff path list, e.g. changed.z; default: positional paths only")
    report_examples = (
        "Examples:\n  .venv/bin/python -m scripts.ci.components census > census.json\n"
        "  .venv/bin/python -m scripts.ci.components what-if --prs frozen-prs.txt > what-if.json\n"
        "Outputs: deterministic JSON on stdout; read-only Git/source analysis; no tests, CI reads or selection changes.\n"
        "Exit codes: 0 report complete; 2 invalid/unavailable inputs.\n"
        "Related: #9929 stage 1; #9721; docs/runbooks/ci-gate.md.\n"
        "Folding: " + "\n".join(REPORT_FOLDING_RULES)
    )
    for operation in ("census", "what-if"):
        sub = subs.add_parser(operation, help="Report-only edge measurement" if operation == "census" else "Hypothetical R0-R3 measurement, never CI selection",
                              description="Report unresolved edges and legacy scanner blind spots.\nUse for stage-1 measurement only; R1-R3 are hypothetical, R3 is UPPER BOUND, NOT ACHIEVABLE WITHOUT PROOF.",
                              epilog=report_examples, formatter_class=argparse.RawDescriptionHelpFormatter)
        if operation == "what-if":
            sub.add_argument("--prs", type=Path, required=True,
                             help="Frozen PR file, each line: <pr> <7-40 hex merge_sha> <merged_at>; short SHAs must resolve uniquely; e.g. frozen-prs.txt (required)")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """Run one interface and emit a privacy-safe structural result."""
    args = parser().parse_args(argv)
    try:
        manifest = load_manifest()
        code = 0
        if args.operation == "list":
            report = {"schema_version": 1, "components": manifest["components"], "residual_commands": manifest["residual_commands"]}
        elif args.operation == "affected":
            paths = args.paths
            if args.paths_file:
                paths += [path for path in args.paths_file.read_bytes().decode("utf-8", errors="surrogateescape").split("\0") if path]
            report = affected(paths, manifest)
        elif args.operation == "census":
            report = report_census(manifest)
        elif args.operation == "what-if":
            report = report_what_if(args.prs, manifest)
        elif args.operation == "junit":
            report, code = junit_coverage(args.junit, manifest, [args.component] if args.component else NODE_IDS)
        elif args.operation == "inventory":
            report = inventory(manifest)
            if args.check and any(report[key] for key in ("unassigned", "ambiguous", "unmapped_test_files", "selector_parity_gaps")):
                code = 1
            if args.check and report.get("import_graph", {}).get("missing_mandatory_edges"):
                code = 1
            if args.collect or args.identities:
                if not args.component:
                    raise ValueError("--collect/--identities requires --component")
                if args.identities:
                    report["identities"] = current_identities(args.component, manifest)
                if args.collect:
                    report["test_ids"], collect_code = collect_tests(test_files(args.component, manifest), [])
                    report["vitest_ids"], vitest_code = collect_vitest(vitest_files(args.component, manifest))
                    collect_code = collect_code or vitest_code
                    if collect_code:
                        report["selection"] = list(NODE_IDS)
                        report["fallback_reason"] = "collection-error"
                        code = collect_code
        else:
            node = manifest["components"][args.component]
            members = verify_inputs(args.inputs, args.component, manifest) if getattr(args, "inputs", None) else {}
            if args.operation == "test":
                if args.workers < 1 or (args.timeout is not None and (args.timeout <= 0 or not math.isfinite(args.timeout))):
                    raise ValueError("workers and timeout must be positive")
                files = test_files(args.component, manifest)
                front_files = vitest_files(args.component, manifest)
                census = {"test_files": files + front_files, "test_file_count": len(files) + len(front_files),
                          "pytest_file_count": len(files), "vitest_file_count": len(front_files)}
                if args.list:
                    print(json.dumps({"component": args.component, **census}, indent=2))
                    return 0
                ids, code = collect_tests(files, node["test_args"])
                front_ids, front_code = collect_vitest(front_files)
                code = code or front_code
                artifact_ids = []
                if not code and node["test_args"]:
                    all_ids, code = collect_tests(files, [])
                    artifact_ids = sorted(set(all_ids) - set(ids))
                if code:
                    report = {"component": args.component, **census, "selection": list(NODE_IDS),
                              "fallback_reason": "collection-error", "pytest_collection_exit": code,
                              "vitest_collection_exit": front_code}
                else:
                    commands = node_test_commands(args.component, manifest, files, front_files, workers=args.workers, timeout=args.timeout)
                    results, code = run_commands(commands, ROOT, None, {}, keep_going=True)
                    report = {"component": args.component, **census, "test_ids": ids, "vitest_ids": front_ids, "commands": results,
                              "artifact_dependent_test_ids": artifact_ids,
                              "artifact_owner_slice": 5 if artifact_ids else None,
                              "data_tier": "needs_artifact cases remain artifact-dependent; see residual_commands"}
            else:
                commands = node[args.operation]
                if not commands:
                    raise ValueError("harness/shared-core are test/verification nodes, not product builds")
                # Pre-expand everything before a producer can write a partial output.
                for command in commands:
                    expand_command(command, ROOT, args.output_dir, members)
                if args.operation == "build":
                    args.output_dir.mkdir(parents=True, exist_ok=True)
                results, code = run_commands(commands, ROOT, args.output_dir, members)
                report = {"component": args.component, "commands": results,
                          "build_scope": node.get("build_scope") if args.operation == "build" else None,
                          "input_bytes_verified": bool(getattr(args, "inputs", None)),
                          "artifact_certification": "not_certified (owning slices 3-5 and 8)",
                          "residual_commands": [entry for entry in manifest["residual_commands"] if entry["component"] == args.component]}
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return code
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, ET.ParseError):
        # Errors may contain host paths or input content; never echo them.
        print(json.dumps({"result": "error", "reason": "invalid_or_unavailable_contract_input_or_command",
                          "selection": list(NODE_IDS)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
