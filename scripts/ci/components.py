"""Conservative component inventory and explicit, independently callable commands.

This is a command wrapper, not CI selection or a certificate of independence.
Contract checks and prepared-artifact certification are reported separately.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

from scripts.ci import frontend_change_scope
from scripts.common.repo_root import project_interpreter
from scripts.deploy import auto_deploy_eligibility

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
    unresolved = manifest["unresolved_edges"]
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


def affected(paths: Sequence[str], manifest: dict) -> dict:
    """Select consumers transitively; shared or incomplete evidence selects all."""
    selected: set[str] = set()
    reasons = set()
    for path in paths:
        owners, reason = assign_path(path, manifest)
        selected.update(owners)
        if reason not in {"exact", "prefix"}:
            reasons.add(reason)
    if any(not edge.get("resolved", False) for edge in manifest["edges"]):
        reasons.add("dynamic-unresolved")
        selected.update(NODE_IDS)
    while True:
        before = selected.copy()
        if "shared-core" in selected:
            selected.update(NODE_IDS)
        selected.update(edge["consumer"] for edge in manifest["edges"] if edge["producer"] in selected)
        if before == selected:
            break
    return {"components": sorted(selected), "fallback_reasons": sorted(reasons), "changed_paths": len(paths)}


def parity_gaps(paths: Sequence[str], manifest: dict, root: Path = ROOT) -> list[str]:
    """Cross-check existing selector semantics without deriving them from the map."""
    patterns = frontend_change_scope.load_denominator(root / manifest["selector_contracts"]["frontend_denominator"])["paths"]
    fronts = set(manifest["selector_contracts"]["frontend_components"])
    gaps = []
    for path in paths:
        requires_front = frontend_change_scope.path_in_denominator(path, patterns)
        deploy = auto_deploy_eligibility.decide_auto_deploy([path]).deploy
        if (requires_front or deploy) and not fronts.issubset(affected([path], manifest)["components"]):
            gaps.append(path)
    return gaps


def inventory(manifest: dict, root: Path = ROOT) -> dict:
    """Count explicit coverage, separately from conservative fallback selection."""
    paths = tracked_paths(root)
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
    gaps = parity_gaps(paths, manifest, root)
    return {
        "inventory_source": "git ls-files -z (index; includes sparse paths)",
        "tracked_paths": len(paths), "node_path_counts": counts,
        "unassigned": len(missing["unmapped"]), "ambiguous": len(missing["ambiguous"]),
        "dynamic_unresolved": len(missing["dynamic-unresolved"]) + sum(not e.get("resolved", False) for e in manifest["edges"]),
        "unmapped_test_files": len(unmapped_tests), "selector_parity_gaps": len(gaps),
        "problems": missing, "parity_gaps": gaps,
    }


def test_files(component: str, manifest: dict, root: Path = ROOT) -> list[str]:
    """Expand declared file/prefix contract suites from the index, never glob cwd."""
    node = manifest["components"][component]
    files = set(node["test_files"])
    prefixes = tuple(node["test_prefixes"])
    if prefixes:
        files.update(path for path in tracked_paths(root) if path.startswith(prefixes)
                     and PurePosixPath(path).name.startswith("test_") and path.endswith(".py"))
    if not files:
        raise ValueError("node has no declared contract tests")
    if any(not (root / path).is_file() for path in files):
        raise ValueError("declared test file is absent; materialize its sparse tree")
    return sorted(files)


def collect_tests(files: Sequence[str], args: Sequence[str], root: Path = ROOT) -> tuple[list[str], int]:
    """Collect fresh IDs; any collection error is a full-selection obligation."""
    result = subprocess.run(
        [str(project_interpreter(root)), "-m", "pytest", "--collect-only", "--verbosity=-1", *files, *args],
        cwd=root, capture_output=True, text=True, timeout=180,
    )
    ids = sorted(line.strip() for line in result.stdout.splitlines() if line.startswith("tests/") and "::" in line)
    return ids, result.returncode if result.returncode else (0 if ids else 5)


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


def run_commands(commands: list[dict], root: Path, output_dir: Path | None,
                 members: dict[str, Path]) -> tuple[list[dict], int]:
    """Wait for every command in the foreground; skipped checks are not passes."""
    reports = []
    expanded = [(command, expand_command(command, root, output_dir, members)) for command in commands]
    for command, argv in expanded:
        with tempfile.TemporaryDirectory(prefix="component-check-") as scratch:
            junit = Path(scratch) / "junit.xml"
            is_pytest = "pytest" in argv
            executed = [*argv, f"--junitxml={junit}"] if is_pytest else argv
            result = subprocess.run(executed, cwd=root / command["cwd"], check=False,
                                    env=os.environ | {"PYTHON": str(project_interpreter(root))},
                                    stdout=sys.stderr, timeout=1800)
            skipped = 0
            if is_pytest and junit.is_file():
                tree = ET.parse(junit)
                skipped = len(tree.findall(".//testcase/skipped"))
            code = result.returncode or (3 if skipped else 0)
            reports.append({"argv": command["argv"], "cwd": command["cwd"], "scope": command["scope"],
                            "exit_code": result.returncode, "skipped": skipped,
                            "result": "pass" if code == 0 else "artifact-dependent" if skipped else "fail"})
            if code:
                return reports, code
    return reports, 0


def parser() -> argparse.ArgumentParser:
    """Expose the complete wrapper contract in root and subcommand help."""
    examples = (
        "Examples:\n  .venv/bin/python -m scripts.ci.components inventory --check\n"
        "  .venv/bin/python -m scripts.ci.components test --component atlas-data\n"
        "  .venv/bin/python -m scripts.ci.components build --component atlas-frontend "
        "--inputs inputs.json --output-dir site/dist\n"
        "Outputs: JSON on stdout; test processes; builds write declared outputs, curriculum producers "
        "write canonical worktree files. No CI/Pages selection, network preparation or publication.\n"
        "Exit codes: 0 checks passed; 1 inventory/command failure; 2 invalid arguments/input; "
        "3 skipped/artifact-dependent checks; collection/producer exits propagated.\n"
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
    subs = result.add_subparsers(dest="operation", required=True, help="Interface: list/test/build/verify/inventory/affected")
    for operation in ("list", "test", "build", "verify", "inventory", "affected"):
        sub = subs.add_parser(operation, help=f"{operation} component contracts", description=description,
                              epilog=examples, formatter_class=argparse.RawDescriptionHelpFormatter)
        if operation in {"test", "build", "verify", "inventory"}:
            sub.add_argument("--component", choices=NODE_IDS, required=operation in {"test", "build", "verify"},
                             help="Node ID, e.g. atlas-data; inventory default: all nodes")
        if operation in {"build", "verify"}:
            sub.add_argument("--inputs", type=Path, required=operation == "build",
                             help="Prepared component-inputs.v1 JSON (e.g. inputs.json); verify default: code-contract checks only")
            sub.add_argument("--output-dir", type=Path, required=operation == "build",
                             help="Build output directory (e.g. site/dist); verify default: no output directory")
        if operation == "inventory":
            sub.add_argument("--check", action="store_true", help="Fail on unassigned, ambiguous, unresolved or parity gaps; default: report only")
            sub.add_argument("--collect", action="store_true", help="Collect fresh contract-suite test IDs for --component (required); default: file census only")
            sub.add_argument("--identities", action="store_true", help="Include current input-binding identities for --component (required); default: omitted")
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
        elif args.operation == "inventory":
            report = inventory(manifest)
            if args.check and any(report[key] for key in ("unassigned", "ambiguous", "dynamic_unresolved", "unmapped_test_files", "selector_parity_gaps")):
                code = 1
            if args.collect or args.identities:
                if not args.component:
                    raise ValueError("--collect/--identities requires --component")
                if args.identities:
                    report["identities"] = current_identities(args.component, manifest)
                if args.collect:
                    report["test_ids"], collect_code = collect_tests(test_files(args.component, manifest), [])
                    if collect_code:
                        report["selection"] = list(NODE_IDS)
                        report["fallback_reason"] = "collection-error"
                        code = collect_code
        else:
            node = manifest["components"][args.component]
            members = verify_inputs(args.inputs, args.component, manifest) if getattr(args, "inputs", None) else {}
            if args.operation == "test":
                files = test_files(args.component, manifest)
                ids, code = collect_tests(files, node["test_args"])
                artifact_ids = []
                if not code and node["test_args"]:
                    all_ids, code = collect_tests(files, [])
                    artifact_ids = sorted(set(all_ids) - set(ids))
                if code:
                    report = {"component": args.component, "selection": list(NODE_IDS), "fallback_reason": "collection-error"}
                else:
                    commands = [{"argv": ["{python}", "-m", "pytest", "-q", *files, *node["test_args"]],
                                 "cwd": ".", "scope": "code-contract"}]
                    results, code = run_commands(commands, ROOT, None, {})
                    report = {"component": args.component, "test_ids": ids, "commands": results,
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
