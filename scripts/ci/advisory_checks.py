"""Exact advisory check names from ci.yml; unknown declarations grant no exemption.

CI Gate's ``needs`` includes scheduling-only jobs. Its scored set is the
``needs.<job>.result`` references in the gate, plus those jobs' dependencies.
An ordinary gate without ``always()`` also depends on every scheduling result.
Unsupported expressions or matrix shapes fail closed rather than guessing names.
"""

from __future__ import annotations

import itertools
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

CI_WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml"
_RESULT = re.compile(r"needs\.([\w-]+)\.result\b")
_EXPRESSION = re.compile(r"\$\{\{(.*?)\}\}", re.DOTALL)
_MATRIX_VALUE = re.compile(r"matrix\.([\w.-]+)\Z")
_LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class AdvisoryChecks:
    """A parsed allowlist, or an empty allowlist with a diagnostic reason."""

    names: frozenset[str] = frozenset()
    workflow: str = ""
    reason: str | None = None


def _needs(job: dict) -> list[str]:
    needs = job.get("needs", [])
    needs = [needs] if isinstance(needs, str) else needs
    if not isinstance(needs, list) or any(not isinstance(key, str) for key in needs):
        raise ValueError("invalid job dependencies")
    return needs


def _required_jobs(jobs: dict) -> set[str]:
    gates = [key for key, job in jobs.items() if job.get("name", key) == "CI Gate"]
    if len(gates) != 1:
        raise ValueError("expected one CI Gate")
    gate_id = gates[0]
    gate = jobs[gate_id]
    gate_needs = _needs(gate)
    # Do not treat the scheduling list as a scored list when an always() gate
    # explicitly checks results (as today's ci.yml does).
    body = yaml.safe_dump({key: value for key, value in gate.items() if key != "needs"})
    required = set(_RESULT.findall(body))
    for expression in _EXPRESSION.findall(body):
        if "needs" in expression and not re.fullmatch(
            r"\s*needs\.[\w-]+\.(?:result|outputs\.[\w-]+)\s*", expression
        ):
            raise ValueError("unsupported CI Gate needs expression")
    if not required or str(gate.get("if", "")).strip() not in {"always()", "${{ always() }}"}:
        required.update(gate_needs)
    required.add(gate_id)
    todo = list(required - {gate_id})
    while todo:
        key = todo.pop()
        if key not in jobs:
            raise ValueError("unknown CI Gate dependency")
        for dependency in _needs(jobs[key]):
            if dependency not in required:
                required.add(dependency)
                todo.append(dependency)
    return required


def _matrix_rows(matrix: object) -> list[dict]:
    if not isinstance(matrix, dict) or not matrix:
        raise ValueError("matrix must be a static mapping")
    axes = {key: value for key, value in matrix.items() if key not in {"include", "exclude"}}
    total = 1
    for values in axes.values():
        if not isinstance(values, list) or not values:
            raise ValueError("matrix axis must be a non-empty static list")
        total *= len(values)
    if total > 256 or "${{" in yaml.safe_dump(matrix):
        raise ValueError("dynamic or oversized matrix")
    original = [dict(zip(axes, values, strict=True)) for values in itertools.product(*axes.values())] if axes else []
    exclude = matrix.get("exclude", [])
    include = matrix.get("include", [])
    if any(not isinstance(entries, list) or any(not isinstance(row, dict) for row in entries)
           for entries in (include, exclude)):
        raise ValueError("invalid matrix include/exclude")
    original = [row for row in original if not any(
        all(row.get(key) == value for key, value in selector.items()) for selector in exclude
    )]
    rows = [dict(row) for row in original]
    extra = []
    for addition in include:
        matched = False
        for base, row in zip(original, rows, strict=True):
            if all(key not in base or base[key] == value for key, value in addition.items()):
                row.update(addition)
                matched = True
        if not matched:
            extra.append(dict(addition))
    rows.extend(extra)
    if not rows or len(rows) > 256:
        raise ValueError("empty or oversized matrix")
    return rows


def _scalar(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (str, int, float)):
        return str(value)
    raise ValueError("unsupported matrix name value")


def _job_names(key: str, job: dict) -> set[str]:
    name = job.get("name", key)
    if not isinstance(name, str) or not name.strip():
        raise ValueError("invalid job name")
    strategy = job.get("strategy", {})
    if not isinstance(strategy, dict):
        raise ValueError("invalid job strategy")
    matrix = strategy.get("matrix")
    if matrix is None:
        if "${{" in name:
            raise ValueError("dynamic job name")
        return {name}
    rows = _matrix_rows(matrix)
    if "name" not in job:
        return {f"{key} ({', '.join(_scalar(value) for value in row.values())})" for row in rows}
    if "${{" not in name:
        raise ValueError("matrix name must explicitly reference its values")

    def render(expression: re.Match, row: dict) -> str:
        match = _MATRIX_VALUE.fullmatch(expression[1].strip())
        if match is None:
            raise ValueError("unsupported matrix name expression")
        value = row
        for part in match[1].split("."):
            if not isinstance(value, dict) or part not in value:
                raise ValueError("missing matrix name value")
            value = value[part]
        return _scalar(value)

    return {_EXPRESSION.sub(lambda expression, row=row: render(expression, row), name) for row in rows}


def load_advisory_checks(path: Path | None = None) -> AdvisoryChecks:
    """Read current ci.yml, reporting failures without leaking file contents."""
    try:
        workflow = yaml.safe_load((path or CI_WORKFLOW_PATH).read_text(encoding="utf-8"))
        if not isinstance(workflow, dict) or not isinstance(workflow.get("jobs"), dict):
            raise ValueError("workflow jobs must be a mapping")
        jobs = workflow["jobs"]
        if any(not isinstance(key, str) or not isinstance(job, dict) for key, job in jobs.items()):
            raise ValueError("invalid workflow job")
        if any(dependency not in jobs for job in jobs.values() for dependency in _needs(job)):
            raise ValueError("unknown workflow dependency")
        workflow_name = workflow.get("name", ".github/workflows/ci.yml")
        if not isinstance(workflow_name, str) or not workflow_name or "${{" in workflow_name:
            raise ValueError("invalid workflow name")
        required = _required_jobs(jobs)
        blocking_names: set[str] = set()
        advisory_names: set[str] = set()
        for key, job in jobs.items():
            names = _job_names(key, job)
            target = advisory_names if job.get("continue-on-error") is True and key not in required else blocking_names
            target.update(names)
        return AdvisoryChecks(frozenset(advisory_names - blocking_names), workflow_name)
    except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
        detail = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        reason = f"ci.yml advisory checks unavailable: {detail}; all checks treated as blocking"
        _LOG.warning(reason)
        return AdvisoryChecks(reason=reason)


def is_advisory(name: str, *, workflow: str | None = None, policy: AdvisoryChecks | None = None) -> bool:
    """Exact name and workflow match only; missing workflow identity blocks."""
    policy = policy if policy is not None else load_advisory_checks()
    return name in policy.names and workflow is not None and workflow == policy.workflow
