#!/usr/bin/env python3
"""Ratchet machinery-to-product imports under scripts/ (#12660).

Every top-level scripts/ directory and scripts/*.py module is classified
as machinery, product, or shared. A file inside a mixed package can carry
its own role. A machinery file may not gain an import of a product file.
Edges come from ``scripts.ci.components.scan_imports``: static imports,
imports nested in functions, relative imports, and literal dynamic loads.
One identity is one importer file plus one resolved target file, so a
second statement of the same target is the same identity, and dropping one
target never pays for a different one. Line numbers are not part of the
identity. A non-literal load is not an identity.

Once origin/main contains the baseline, the committed counts may only
shrink. Before that first landing there is no predecessor; the baseline
must still equal the census, so a stale entry fails.

Examples:
  .venv/bin/python -m scripts.lint.boundary_ratchet
  .venv/bin/python -m scripts.lint.boundary_ratchet scripts/api/main.py
  .venv/bin/python -m scripts.lint.boundary_ratchet --write-baseline

Outputs: one violation per new site, stale site, or unclassified name on
stderr, or a one-line pass message on stdout. Exit 0 is a pass or a
baseline written. Exit 1 is a violation or an unreadable tree.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from scripts.ci.components import scan_imports

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).with_name("boundary_baseline.json")
CONFIG_PATH = REPO_ROOT / "scripts" / "config" / "package_boundary.yaml"
SCHEMA = "boundary-ratchet-baseline.v1"
CONFIG_SCHEMA = "package-boundary.v1"
ROLES = frozenset({"machinery", "product", "shared"})
_GIT_TIMEOUT_SECONDS = 30
_SHRINK_REFS = ("HEAD", "HEAD^", "origin/main")
_SKIP_DIRS = frozenset({"__pycache__"})


@dataclass(frozen=True)
class Classified:
    """Roles for top-level scripts names and for files that do not inherit one."""

    packages: Mapping[str, str]
    modules: Mapping[str, str]
    reasons: Mapping[tuple[str, str], str]
    files: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, order=True)
class ImportSite:
    """One machinery import of one product module. Line number is absent."""

    path: str
    module: str


class _UniqueLoader(yaml.SafeLoader):
    """Safe loader that rejects a repeated mapping key."""


def _unique_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if key in mapping:
            raise ValueError(f"duplicate key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=True)
    return mapping


_UniqueLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _unique_mapping,
)


def _load_yaml(path: Path) -> object:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueLoader)


def _reason(entry: Mapping[str, object], where: str) -> str:
    reason = entry.get("reason", "")
    if reason is None:
        reason = ""
    if not isinstance(reason, str) or "\n" in reason:
        raise ValueError(f"{where}: reason must be one line")
    return reason.strip()


def _role_table(rows: object, kind: str, where: str) -> tuple[dict[str, str], dict[tuple[str, str], str]]:
    if not isinstance(rows, dict):
        raise ValueError(f"{where}: {kind} must be a mapping")
    roles: dict[str, str] = {}
    reasons: dict[tuple[str, str], str] = {}
    for name, entry in rows.items():
        if not isinstance(name, str) or not name or name in {".", ".."} or "/" in name:
            raise ValueError(f"{where}: bad {kind} name: {name!r}")
        if kind == "modules" and not name.endswith(".py"):
            raise ValueError(f"{where}: module name must end with .py: {name}")
        if not isinstance(entry, dict):
            raise ValueError(f"{where}: {kind}.{name} must be a mapping")
        role = entry.get("role")
        if role not in ROLES:
            raise ValueError(f"{where}: {kind}.{name} role must be machinery, product, or shared")
        reason = _reason(entry, f"{where}: {kind}.{name}")
        if role == "shared" and not reason:
            raise ValueError(f"{where}: {kind}.{name} shared entry needs a reason")
        roles[name] = str(role)
        if reason:
            reasons[(kind, name)] = reason
    return roles, reasons


def _file_table(rows: object, where: str) -> tuple[dict[str, str], dict[tuple[str, str], str]]:
    if rows is None:
        return {}, {}
    if not isinstance(rows, dict):
        raise ValueError(f"{where}: files must be a mapping")
    roles: dict[str, str] = {}
    reasons: dict[tuple[str, str], str] = {}
    for name, entry in rows.items():
        path = Path(name)
        if (
            not isinstance(name, str)
            or not name.startswith("scripts/")
            or not name.endswith(".py")
            or name.startswith(("/", "\\"))
            or ".." in path.parts
        ):
            raise ValueError(f"{where}: bad file name: {name!r}")
        if not isinstance(entry, dict):
            raise ValueError(f"{where}: files.{name} must be a mapping")
        role = entry.get("role")
        if role not in ROLES:
            raise ValueError(f"{where}: files.{name} role must be machinery, product, or shared")
        reason = _reason(entry, f"{where}: files.{name}")
        if role == "shared" and not reason:
            raise ValueError(f"{where}: files.{name} shared entry needs a reason")
        roles[name] = str(role)
        if reason:
            reasons[("files", name)] = reason
    return roles, reasons


def load_config(path: Path) -> Classified:
    """Load the package boundary. A shared entry without a reason fails."""

    payload = _load_yaml(path)
    where = str(path)
    if not isinstance(payload, dict) or payload.get("schema") != CONFIG_SCHEMA:
        raise ValueError(f"{where}: schema must be {CONFIG_SCHEMA}")
    packages, package_reasons = _role_table(payload.get("packages"), "packages", where)
    modules, module_reasons = _role_table(payload.get("modules"), "modules", where)
    files, file_reasons = _file_table(payload.get("files"), where)
    return Classified(
        packages,
        modules,
        {**package_reasons, **module_reasons, **file_reasons},
        files,
    )


def _scripts_dir(root: Path) -> Path:
    return root / "scripts"


def disk_names(root: Path) -> tuple[set[str], set[str]]:
    """Top-level directory names and top-level ``*.py`` file names."""

    scripts = _scripts_dir(root)
    packages: set[str] = set()
    modules: set[str] = set()
    if not scripts.is_dir():
        return packages, modules
    for child in scripts.iterdir():
        if child.name.startswith(".") or child.name in _SKIP_DIRS:
            continue
        if child.is_dir():
            packages.add(child.name)
        elif child.is_file() and child.suffix == ".py":
            modules.add(child.name)
    return packages, modules


def classification_violations(root: Path, config: Classified) -> list[str]:
    """Fail closed: every top-level name is classified, and the config has no ghost."""

    packages, modules = disk_names(root)
    violations: list[str] = []
    for name in sorted(packages - set(config.packages)):
        violations.append(f"scripts/{name}: unclassified package")
    for name in sorted(set(config.packages) - packages):
        violations.append(f"scripts/{name}: classified package is not in the tree")
    for name in sorted(modules - set(config.modules)):
        violations.append(f"scripts/{name}: unclassified module")
    for name in sorted(set(config.modules) - modules):
        violations.append(f"scripts/{name}: classified module is not in the tree")
    for name in sorted(config.files):
        if not (root / name).is_file():
            violations.append(f"{name}: classified file is not in the tree")
    return violations


def file_role(rel: str, config: Classified) -> str | None:
    """Role of one scripts file. A listed file wins; otherwise the package or module role."""

    override = config.files.get(rel)
    if override:
        return override
    path = Path(rel)
    if not path.parts or path.parts[0] != "scripts":
        return None
    return importer_role(Path(*path.parts[1:]), config)


def _module_of(path: str) -> str:
    name = path[:-3].replace("/", ".")
    suffix = ".__init__"
    if name.endswith(suffix):
        name = name[: -len(suffix)]
    return name


def importer_role(rel: Path, config: Classified) -> str | None:
    """Role of the file that contains the import."""

    if len(rel.parts) == 1:
        return config.modules.get(rel.name)
    return config.packages.get(rel.parts[0])


def _python_files(root: Path, targets: Sequence[str] | None) -> list[Path]:
    scripts = _scripts_dir(root)
    if targets is None:
        return sorted(
            path
            for path in scripts.rglob("*.py")
            if _SKIP_DIRS.isdisjoint(path.parts) and path.is_file()
        )
    files: list[Path] = []
    for target in targets:
        path = root / target
        if path.is_dir():
            files.extend(
                child
                for child in path.rglob("*.py")
                if _SKIP_DIRS.isdisjoint(child.parts) and child.is_file()
            )
        elif path.suffix == ".py" and path.is_file():
            files.append(path)
    return sorted(set(files))


def collect_import_counts(
    root: Path,
    config: Classified,
    targets: Sequence[str] | None = None,
) -> tuple[Counter[tuple[str, str]], list[str]]:
    """Count machinery-to-product identities from the shared dependency scanner.

    The scanner resolves names against the whole ``scripts/`` tree. ``targets``
    only chooses which importer files are counted.
    """

    fatal: list[str] = []
    sources: dict[str, bytes] = {}
    for path in _python_files(root, None):
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            fatal.append(f"{path}: outside the tree")
            continue
        try:
            sources[rel] = path.read_bytes()
        except OSError as exc:
            fatal.append(f"{rel}: cannot read imports: {exc}")
    if fatal:
        return Counter(), fatal
    graph = scan_imports(sources)
    for edge in graph["unresolved_edges"]:
        if edge["reason"] == "parse-error":
            fatal.append(f"{edge['path']}: cannot parse imports")
    if fatal:
        return Counter(), fatal
    scope = {path.relative_to(root).as_posix() for path in _python_files(root, targets)} if targets is not None else None
    counts: Counter[tuple[str, str]] = Counter()
    for importer, target in graph["file_edges"]:
        if scope is not None and importer not in scope:
            continue
        if file_role(importer, config) != "machinery":
            continue
        if file_role(target, config) != "product":
            continue
        module = _module_of(target)
        if not module.startswith("scripts."):
            continue
        counts[(importer, module)] += 1
    return counts, fatal


def _entries_from_rows(rows: object, where: str) -> Counter[tuple[str, str]]:
    if not isinstance(rows, list):
        raise ValueError(f"{where}: entries must be a list")
    counts: Counter[tuple[str, str]] = Counter()
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{where}: an entry is not an object")
        path = row.get("path")
        module = row.get("module")
        count = row.get("count")
        if (
            not isinstance(path, str)
            or not path.startswith("scripts/")
            or path.startswith(("/", "\\"))
            or ".." in Path(path).parts
            or not isinstance(module, str)
            or not module.startswith("scripts.")
            or not isinstance(count, int)
            or isinstance(count, bool)
            or count < 1
        ):
            raise ValueError(f"{where}: an entry needs a scripts path, scripts module, and count >= 1")
        key = (path, module)
        if key in seen:
            raise ValueError(f"{where}: duplicate entry {path} {module}")
        seen.add(key)
        counts[key] = count
    return counts


def load_baseline(path: Path) -> Counter[tuple[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise ValueError(f"{path}: schema must be {SCHEMA}")
    return _entries_from_rows(payload.get("entries"), str(path))


def write_baseline(path: Path, counts: Mapping[tuple[str, str], int]) -> None:
    entries = [
        {"path": item_path, "module": module, "count": counts[(item_path, module)]}
        for item_path, module in sorted(counts)
    ]
    payload = {"schema": SCHEMA, "entries": entries}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def compare(current: Mapping[tuple[str, str], int], baseline: Mapping[tuple[str, str], int]) -> list[str]:
    """A higher count is a new site. A lower count is a stale baseline entry."""

    violations: list[str] = []
    for key in sorted(set(current) | set(baseline)):
        path, module = key
        extra = current.get(key, 0) - baseline.get(key, 0)
        if extra > 0:
            violations.append(f"{path}: new machinery-to-product import {module} x{extra}")
        missing = baseline.get(key, 0) - current.get(key, 0)
        if missing > 0:
            violations.append(f"{path}: stale baseline {module} x{missing}")
    return violations


def _baseline_at(root: Path, ref: str, rel: str) -> Counter[tuple[str, str]] | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=_GIT_TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        return None
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise ValueError(f"{ref}:{rel}: schema must be {SCHEMA}")
    return _entries_from_rows(payload.get("entries"), f"{ref}:{rel}")


def _is_subset(current: Mapping[tuple[str, str], int], previous: Mapping[tuple[str, str], int]) -> bool:
    return all(count <= previous.get(key, 0) for key, count in current.items())


def shrink_violations(root: Path, baseline: Path, counts: Mapping[tuple[str, str], int]) -> list[str]:
    """Reject growth against a baseline that has already landed on origin/main."""

    if not (root / ".git").exists():
        return []
    try:
        rel = baseline.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return []
    if _baseline_at(root, "origin/main", rel) is None:
        return []
    violations: list[str] = []
    for ref in _SHRINK_REFS:
        try:
            previous = _baseline_at(root, ref, rel)
        except (json.JSONDecodeError, ValueError) as exc:
            return [f"{rel}: baseline at {ref} is unreadable: {exc}"]
        if previous is None:
            continue
        if not _is_subset(counts, previous):
            violations.append(f"{rel}: baseline may only shrink; freeze/growth differs from {ref}")
    return violations


def _normalize_targets(root: Path, paths: Sequence[str]) -> list[str]:
    targets: list[str] = []
    for raw in paths:
        path = Path(raw)
        if path.is_absolute():
            try:
                path = path.relative_to(root.resolve())
            except ValueError as exc:
                raise ValueError(f"path is outside the tree: {raw}") from exc
        text = path.as_posix()
        if text.startswith("./"):
            text = text[2:]
        if not text or text.startswith("../") or ".." in Path(text).parts:
            raise ValueError(f"path is outside the tree: {raw}")
        targets.append(text)
    return targets


def _scope(targets: Sequence[str] | None) -> list[str] | None:
    """Python files and scripts directories to census. None rechecks the whole tree.

    A baseline or boundary file alone rechecks every import, matching the mypy ratchet.
    """

    if not targets:
        return None
    selected: list[str] = []
    for target in targets:
        bare_dir = Path(target).suffix == "" and (target == "scripts" or target.startswith("scripts/"))
        if target.endswith(".py") or bare_dir:
            selected.append(target)
    return selected or None


def _in_scope(path: str, scope: Sequence[str]) -> bool:
    for target in scope:
        if target.endswith(".py"):
            if path == target:
                return True
            continue
        prefix = target.rstrip("/") + "/"
        if path == target or path.startswith(prefix):
            return True
    return False


def evaluate(
    root: Path,
    config_path: Path,
    baseline_path: Path,
    targets: Sequence[str] | None = None,
) -> list[str]:
    """Return violation strings. An empty list is a pass."""

    config = load_config(config_path)
    violations = classification_violations(root, config)
    scope = _scope(targets)
    current, fatal = collect_import_counts(root, config, scope)
    violations.extend(fatal)
    if fatal:
        return violations
    baseline = load_baseline(baseline_path)
    if scope is not None:
        baseline = Counter({key: count for key, count in baseline.items() if _in_scope(key[0], scope)})
        current = Counter({key: count for key, count in current.items() if _in_scope(key[0], scope)})
    violations.extend(compare(current, baseline))
    full_baseline = load_baseline(baseline_path)
    violations.extend(shrink_violations(root, baseline_path, full_baseline))
    return violations


def _summarize(counts: Mapping[tuple[str, str], int]) -> str:
    by_top: Counter[str] = Counter()
    for (_path, module), count in counts.items():
        by_top[module.split(".")[1]] += count
    total = sum(counts.values())
    detail = ", ".join(f"{name} {by_top[name]}" for name in sorted(by_top))
    return f"Wrote {total} machinery-to-product import sites ({detail})"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "paths",
        nargs="*",
        help="Python files to check (default: scripts/). Other paths recheck scripts/.",
    )
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH, help="Baseline JSON.")
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help="Package boundary YAML.",
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Repository root.")
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Rewrite the baseline from the current census and exit.",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    baseline = args.baseline if args.baseline.is_absolute() else root / args.baseline
    config_path = args.config if args.config.is_absolute() else root / args.config
    try:
        if args.write_baseline:
            config = load_config(config_path)
            violations = classification_violations(root, config)
            counts, fatal = collect_import_counts(root, config, None)
            violations.extend(fatal)
            if violations:
                print("\n".join(violations), file=sys.stderr)
                return 1
            write_baseline(baseline, counts)
            print(_summarize(counts))
            return 0
        targets = _normalize_targets(root, args.paths) if args.paths else None
        violations = evaluate(root, config_path, baseline, targets)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError, yaml.YAMLError) as exc:
        print(f"boundary ratchet could not run: {exc}", file=sys.stderr)
        return 1
    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1
    print("OK: package boundary ratchet matches the baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
