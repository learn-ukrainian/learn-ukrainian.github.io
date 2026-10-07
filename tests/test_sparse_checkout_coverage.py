"""Sparse CI jobs must check out every scripts module they import.

Amendment 4 of the design in #9937, for the jobs in ``.github/workflows``:
a static ``sparse-checkout`` list has to contain the ``scripts.*`` import
closure of that job's Python entry point. The closure is
``scripts.ci.components.scan_imports``, which records imports inside
functions, so a module loaded only on a later call still has to be present.
``python -m`` also loads each parent package; those inits join the closure.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pathspec
import yaml

from scripts.ci.components import python_sources, scan_imports

ROOT = Path(__file__).resolve().parents[1]

# Jobs the audit has to keep seeing. A new sparse job is checked as well.
EXPECTED_JOBS = frozenset(
    {
        (".github/workflows/cache-hygiene.yml", "prune"),
        (".github/workflows/ci.yml", "freeze-durations"),
        (".github/workflows/ci.yml", "pytest-report"),
        (".github/workflows/ci.yml", "reuse"),
        (".github/workflows/pr-body-guard.yml", "closing-references"),
    }
)

_MODULE = re.compile(r"(?<![\w.-])python3?(?:\.\d+)?\s+-m\s+(scripts(?:\.[\w]+)+)")
_FILE = re.compile(r"(?<![\w.-])python3?(?:\.\d+)?\s+(scripts(?:/[\w.-]+)+\.py)")
_PYTHON = re.compile(r"(?<![\w.-])python3?(?:\.\d+)?\b")


@dataclass(frozen=True)
class Entry:
    """One Python program a job step runs."""

    path: str
    as_module: bool


@dataclass(frozen=True)
class SparseJob:
    workflow: str
    job: str
    patterns: tuple[str, ...]
    cone: bool
    script: str
    entries: tuple[Entry, ...]


def _patterns(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        lines = value.splitlines()
    elif isinstance(value, list):
        lines = [str(item) for item in value]
    else:
        raise AssertionError(f"sparse-checkout must be a string or list, not {type(value).__name__}")
    return tuple(line.strip() for line in lines if line.strip() and not line.strip().startswith("#"))


def _cone(value: object) -> bool:
    """actions/checkout defaults to cone mode when the flag is omitted."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "no", "0"}
    return True


def _entries(script: str) -> tuple[Entry, ...]:
    modules = [Entry(match.group(1).replace(".", "/") + ".py", True) for match in _MODULE.finditer(script)]
    files = [Entry(match.group(1), False) for match in _FILE.finditer(script)]
    return tuple(modules + files)


def sparse_jobs(root: Path = ROOT) -> list[SparseJob]:
    """Every workflow job that sets a static sparse-checkout list."""
    jobs: list[SparseJob] = []
    for path in sorted((root / ".github" / "workflows").glob("*.yml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise AssertionError(f"{path} did not parse to a mapping")
        for name, job in (document.get("jobs") or {}).items():
            patterns: list[tuple[str, ...]] = []
            cone: list[bool] = []
            runs: list[str] = []
            for step in job.get("steps") or []:
                options = step.get("with") or {}
                if "sparse-checkout" in options:
                    patterns.append(_patterns(options["sparse-checkout"]))
                    cone.append(_cone(options.get("sparse-checkout-cone-mode", True)))
                run = step.get("run")
                if isinstance(run, str):
                    runs.append(run)
            if not patterns:
                continue
            if len(patterns) != 1:
                raise AssertionError(f"{path.name} job {name} has {len(patterns)} sparse checkouts")
            script = "\n".join(runs)
            jobs.append(
                SparseJob(
                    str(path.relative_to(root)),
                    name,
                    patterns[0],
                    cone[0],
                    script,
                    _entries(script),
                )
            )
    return jobs


def _resolve(path: str, sources: dict[str, bytes]) -> str:
    if path in sources:
        return path
    package = path.removesuffix(".py") + "/__init__.py"
    if package in sources:
        return package
    raise AssertionError(f"{path} is not a tracked Python module")


def _ancestors(path: str, sources: dict[str, bytes]) -> list[str]:
    parts = path.split("/")
    return [init for index in range(1, len(parts)) if (init := "/".join(parts[:index]) + "/__init__.py") in sources]


def _closure(start: str, outgoing: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    stack = [start]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(outgoing[current])
    return {path for path in seen if path.startswith("scripts/")}


def _covers(patterns: tuple[str, ...], *, cone: bool) -> Callable[[str], bool]:
    if cone:
        prefixes = tuple(pattern.rstrip("/") for pattern in patterns)

        def covers(path: str) -> bool:
            return any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes)

        return covers
    spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
    return spec.match_file


def _required(job: SparseJob, sources: dict[str, bytes], outgoing: dict[str, set[str]]) -> set[str]:
    required: set[str] = set()
    for entry in job.entries:
        path = _resolve(entry.path, sources)
        required |= _closure(path, outgoing)
        if entry.as_module:
            for init in _ancestors(path, sources):
                required |= _closure(init, outgoing)
    return required


def missing_scripts(
    job: SparseJob,
    sources: dict[str, bytes],
    outgoing: dict[str, set[str]],
    unresolved: list[dict],
) -> list[str]:
    """Repo paths the job imports that its sparse-checkout patterns omit."""
    if not job.entries:
        if _PYTHON.search(job.script) and "scripts" in job.script:
            return [f"{job.workflow} job {job.job} runs scripts without a recognized entry point"]
        return []
    required = _required(job, sources, outgoing)
    covers = _covers(job.patterns, cone=job.cone)
    missing = sorted(path for path in required if not covers(path))
    missing.extend(
        f"{edge['path']}:{edge['line']} unresolved {edge['reason']}"
        for edge in unresolved
        if edge["path"] in required and edge["reason"] == "missing-local-import"
    )
    return missing


def import_graph(root: Path = ROOT) -> tuple[dict[str, bytes], dict[str, set[str]], list[dict]]:
    """Local import edges from the indexed tree, including uncommitted edits."""
    sources = python_sources(root)
    graph = scan_imports(sources)
    outgoing: dict[str, set[str]] = defaultdict(set)
    for importer, target in graph["file_edges"]:
        outgoing[importer].add(target)
    return sources, outgoing, graph["unresolved_edges"]


def test_sparse_checkout_covers_script_imports() -> None:
    sources, outgoing, unresolved = import_graph()
    jobs = sparse_jobs()
    found = {(job.workflow, job.job) for job in jobs}
    assert found >= EXPECTED_JOBS, sorted(EXPECTED_JOBS - found)
    gaps = [
        f"{job.workflow} job {job.job} does not check out {path}"
        for job in jobs
        for path in missing_scripts(job, sources, outgoing, unresolved)
    ]
    assert not gaps, "\n".join(gaps)
