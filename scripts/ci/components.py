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
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path, PurePosixPath

from scripts.ci import frontend_change_scope
from scripts.ci.junit_results import parse_junit
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


def scan_imports(sources: dict[str, bytes]) -> dict:
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
        nodes = list(ast.walk(tree))
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
    graph = cached_import_scan(tuple(sources.items()))
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
def cached_import_scan(sources: tuple) -> dict:
    """Reuse an AST scan only when every indexed/current source byte is identical."""
    return scan_imports(dict(sources))


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
        for line in journal.read_text(encoding="utf-8").splitlines():
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
    rank = {"passed": 0, "skipped": 1, "failed": 2, "error": 3}
    for row in rows:
        # Parameter values containing dots and classes without a Test prefix
        # use pytest's own classname/name identity, not guessed file names.
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
                          **{key: len(value) for key, value in groups.items()},
                          "failing_test_ids": groups["failed"], "absent_test_ids": groups["absent"],
                          "skipped_test_ids": groups["skipped"]}
    report = {"schema": "component-junit-coverage.v1",
              "head_sha": subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                                         capture_output=True, text=True, timeout=30).stdout.strip(),
              "junit_inputs": [{"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                               for path in paths], "nodes": coverage}
    # Skips and absent IDs are evidence gaps, never passing proof.
    return report, 1 if any(row[key] for row in coverage.values() for key in ("failed", "skipped", "absent")) else 0


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
    subs = result.add_subparsers(dest="operation", required=True, help="Interface: list/test/build/verify/inventory/affected/junit")
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
