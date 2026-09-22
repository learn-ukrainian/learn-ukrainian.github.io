"""The level grammar registry and its --strict append-only check (Brief B).

``lesson-plans/<level>/_grammar.yaml`` is an append-only YAML list of records
``{ id, point, introduced_at: { position, lesson } }``, optionally carrying
``superseded_by: <id>`` (docs/epics/fresh-build-plan-schema.md §2a). Ids are
``G-<level>-<nnn>`` (three digits, as in the plan schema's grammarId pattern).
``introduced_at.lesson`` is the introducing lesson's **slug** — lesson slugs
are stable (§2) while lesson ``n`` is positional — and ``position`` is the
plan's arc position.

Always checked (every run, not only --strict): ids are unique and well-formed;
a plan may introduce only an id the registry assigns to that position and
lesson with the same ``point`` string; a plan may neither introduce nor use a
superseded id; ``superseded_by`` must name an existing, non-superseded id. A
plan that introduces grammar while the registry file does not exist fails with
a message saying how to add the record.

``--strict`` additionally compares the registry with the same file at
``git merge-base HEAD origin/main``: every record present there must still be
present, in the same order, with ``id``, ``point`` and ``introduced_at``
unchanged; new records come only after them; the single permitted change to an
existing record is adding ``superseded_by``. Edge cases per §2a: the file
absent at the merge base passes (every record is new); on ``main`` the merge
base is ``HEAD`` and the check passes; no computable merge base (a shallow
clone) fails with a message telling the reader to fetch full history. Every
git call goes through ``_git`` with an explicit timeout and no shell.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import codes
from .report import Outcome, Report

GIT_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class GrammarRecord:
    id: str
    point: str
    position: int
    lesson: str
    superseded_by: str | None


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """The single git entry point: no shell, an explicit timeout, never raises."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return subprocess.CompletedProcess(args=["git", *args], returncode=128, stdout="", stderr=str(error))


def registry_path_for(plan_path: Path) -> Path:
    return plan_path.parent / "_grammar.yaml"


def _parse_records(data: object, path: Path, level: str, failures: list[Outcome]) -> list[GrammarRecord] | None:
    """Shape-check the registry YAML; None when it cannot be read as records."""
    if not isinstance(data, list):
        failures.append(
            Outcome(
                codes.REGISTRY_MALFORMED,
                f"{path} is not a YAML list of {{ id, point, introduced_at: {{ position, lesson }} }} records (§2a)",
            )
        )
        return None
    records: list[GrammarRecord] = []
    id_pattern = re.compile(rf"^G-{re.escape(level)}-\d{{3}}$")
    for index, entry in enumerate(data):
        introduced_at = entry.get("introduced_at") if isinstance(entry, dict) else None
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("id"), str)
            or not isinstance(entry.get("point"), str)
            or not isinstance(introduced_at, dict)
            or not isinstance(introduced_at.get("position"), int)
            or not isinstance(introduced_at.get("lesson"), str)
            or ("superseded_by" in entry and not isinstance(entry["superseded_by"], str))
        ):
            failures.append(
                Outcome(
                    codes.REGISTRY_MALFORMED,
                    f"{path} record {index + 1} is not {{ id, point, introduced_at: {{ position, lesson }} }} "
                    f"with an optional string superseded_by: {entry!r} (§2a)",
                )
            )
            return None
        if not id_pattern.match(entry["id"]):
            failures.append(
                Outcome(
                    codes.REGISTRY_ID_MALFORMED,
                    f"{path} record {entry['id']!r} is not G-{level}-<nnn> (three digits) (§2a)",
                )
            )
        records.append(
            GrammarRecord(
                id=entry["id"],
                point=entry["point"],
                position=introduced_at["position"],
                lesson=introduced_at["lesson"],
                superseded_by=entry.get("superseded_by"),
            )
        )
    return records


def load_registry(
    path: Path, level: str, failures: list[Outcome]
) -> tuple[list[GrammarRecord], dict[str, GrammarRecord]] | None:
    """Load and self-check the registry; None when the file is absent or unreadable.

    An absent file is not by itself a failure — the caller decides (a plan that
    introduces grammar without a registry fails REGISTRY_MISSING). Well-formedness
    failures (duplicate ids, dangling or self-superseding superseded_by) are
    appended for any registry that exists.
    """
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        failures.append(Outcome(codes.REGISTRY_YAML_INVALID, f"{path} is not valid YAML: {error}"))
        return None
    records = _parse_records(data, path, level, failures)
    if records is None:
        return None
    by_id: dict[str, GrammarRecord] = {}
    for record in records:
        if record.id in by_id:
            failures.append(Outcome(codes.REGISTRY_DUPLICATE_ID, f"{path}: grammar id {record.id} appears twice (§2a)"))
        by_id.setdefault(record.id, record)
    for record in records:
        if record.superseded_by is None:
            continue
        target = by_id.get(record.superseded_by)
        if target is None:
            failures.append(
                Outcome(
                    codes.SUPERSEDED_BY_UNKNOWN,
                    f"{path}: {record.id} is superseded_by {record.superseded_by}, "
                    "which does not exist in the registry (§2a)",
                )
            )
        elif target.superseded_by is not None:
            failures.append(
                Outcome(
                    codes.SUPERSEDED_BY_SUPERSEDED,
                    f"{path}: {record.id} is superseded_by {record.superseded_by}, which is itself superseded (§2a)",
                )
            )
    return records, by_id


def check_plan_against_registry(
    report: Report,
    plan: dict,
    plan_path: Path,
    registry: tuple[list[GrammarRecord], dict[str, GrammarRecord]] | None,
) -> None:
    """The plan-side registry rules of §2a: introduction assignment, point equality,
    and the ban on introducing or using a superseded id."""
    position = plan["arc_ref"]["position"]
    introduced: list[tuple[int, str, str, str]] = []  # (lesson n, lesson slug, id, point)
    used: list[tuple[int, str, str]] = []  # (lesson n, step id, id)
    for lesson in plan["lessons"]:
        if lesson["kind"] == "teach":
            for entry in lesson["inventory"].get("grammar") or []:
                introduced.append((lesson["n"], lesson["slug"], entry["id"], entry["point"]))
        for step in lesson["steps"]:
            for item in (step.get("uses") or {}).get("grammar") or []:
                used.append((lesson["n"], step["id"], item))

    if registry is None:
        if introduced:
            lesson_n, lesson_slug, grammar_id, point = introduced[0]
            report.failures.append(
                Outcome(
                    codes.REGISTRY_MISSING,
                    f"the plan introduces grammar ({grammar_id} in lesson {lesson_n}) but "
                    f"{registry_path_for(plan_path)} does not exist; create it as a YAML list and append "
                    f"{{ id: {grammar_id}, point: {point!r}, introduced_at: {{ position: {position}, "
                    f"lesson: {lesson_slug} }} }} (and one record per introduced id) (§2a)",
                    lesson=lesson_n,
                )
            )
        return

    _records, by_id = registry
    for lesson_n, lesson_slug, grammar_id, point in introduced:
        record = by_id.get(grammar_id)
        if record is None:
            report.failures.append(
                Outcome(
                    codes.GRAMMAR_ID_NOT_REGISTERED,
                    f"the plan introduces {grammar_id}, which the registry does not assign to any "
                    "position or lesson (§2a)",
                    lesson=lesson_n,
                )
            )
            continue
        if record.position != position or record.lesson != lesson_slug:
            report.failures.append(
                Outcome(
                    codes.GRAMMAR_ID_WRONG_POSITION,
                    f"the registry assigns {grammar_id} to position {record.position} lesson "
                    f"{record.lesson!r}, but this plan introduces it at position {position} lesson "
                    f"{lesson_slug!r} (§2a)",
                    lesson=lesson_n,
                )
            )
        if record.point != point:
            report.failures.append(
                Outcome(
                    codes.GRAMMAR_POINT_MISMATCH,
                    f"the plan's point for {grammar_id} is {point!r}, the registry records "
                    f"{record.point!r}; a merged point's wording is corrected by a new id and a "
                    "superseded_by marker, never by editing (§2a)",
                    lesson=lesson_n,
                )
            )
        if record.superseded_by is not None:
            report.failures.append(
                Outcome(
                    codes.SUPERSEDED_GRAMMAR_INTRODUCED,
                    f"the plan introduces {grammar_id}, which the registry marks superseded by "
                    f"{record.superseded_by} (§2a)",
                    lesson=lesson_n,
                )
            )
    for lesson_n, step_id, grammar_id in used:
        record = by_id.get(grammar_id)
        if record is not None and record.superseded_by is not None:
            report.failures.append(
                Outcome(
                    codes.SUPERSEDED_GRAMMAR_USED,
                    f"the step uses {grammar_id}, which the registry marks superseded by {record.superseded_by} (§2a)",
                    lesson=lesson_n,
                    step=step_id,
                )
            )


def check_append_only(report: Report, registry_path: Path, current_records: list[GrammarRecord]) -> None:
    """The --strict append-only comparison against git merge-base HEAD origin/main."""
    toplevel = _git(["rev-parse", "--show-toplevel"], registry_path.parent)
    if toplevel.returncode != 0:
        report.failures.append(
            Outcome(
                codes.MERGE_BASE_UNAVAILABLE,
                f"{registry_path} is not inside a git repository ({toplevel.stderr.strip()}); "
                "--strict needs git history — fetch the full repository",
            )
        )
        return
    root = Path(toplevel.stdout.strip())
    try:
        relative = registry_path.resolve().relative_to(root)
    except ValueError:
        report.failures.append(
            Outcome(
                codes.MERGE_BASE_UNAVAILABLE,
                f"{registry_path} lies outside the git top level {root}; cannot compute a merge-base path",
            )
        )
        return
    merge_base = _git(["merge-base", "HEAD", "origin/main"], root)
    base_sha = merge_base.stdout.strip()
    if merge_base.returncode != 0 or not base_sha:
        report.failures.append(
            Outcome(
                codes.MERGE_BASE_UNAVAILABLE,
                "no merge base between HEAD and origin/main can be computed — this is a shallow "
                "clone or a repository without origin/main; fetch full history "
                "(git fetch --unshallow, or actions/checkout with fetch-depth: 0) (§2a)",
            )
        )
        return
    show = _git(["show", f"{base_sha}:{relative.as_posix()}"], root)
    if show.returncode != 0:
        return  # the file does not exist at the merge base: every record is new, pass
    try:
        base_data = yaml.safe_load(show.stdout)
    except yaml.YAMLError as error:
        report.failures.append(
            Outcome(
                codes.REGISTRY_APPEND_ONLY_VIOLATION,
                f"the registry at merge base {base_sha[:12]}… is not valid YAML ({error}); "
                "append-only cannot be verified (§2a)",
            )
        )
        return
    shape_failures: list[Outcome] = []
    base_records = _parse_records(base_data, registry_path, report.level, shape_failures)
    if base_records is None:
        report.failures.append(
            Outcome(
                codes.REGISTRY_APPEND_ONLY_VIOLATION,
                f"the registry at merge base {base_sha[:12]}… is malformed "
                f"({shape_failures[0].message}); append-only cannot be verified (§2a)",
            )
        )
        return

    def violation(message: str) -> None:
        report.failures.append(Outcome(codes.REGISTRY_APPEND_ONLY_VIOLATION, message + " (§2a)"))

    if len(current_records) < len(base_records):
        violation(
            f"the registry shrank from {len(base_records)} records at merge base {base_sha[:12]}… "
            f"to {len(current_records)}; records are never removed or renumbered"
        )
        return
    for index, base in enumerate(base_records):
        current = current_records[index]
        if current.id != base.id:
            violation(
                f"record {index + 1} at merge base {base_sha[:12]}… is {base.id} but the current "
                f"record there is {current.id}; records keep their order and new records come only "
                "after the existing ones (nothing is removed, reordered or inserted in the middle)"
            )
            return
        for key, base_value, current_value in (
            ("point", base.point, current.point),
            (
                "introduced_at",
                {"position": base.position, "lesson": base.lesson},
                {"position": current.position, "lesson": current.lesson},
            ),
        ):
            if current_value != base_value:
                violation(
                    f"record {current.id} had {key} {base_value!r} at merge base {base_sha[:12]}… "
                    f"and now has {current_value!r}; a merged record's wording is corrected by a new "
                    "id and a superseded_by marker, never by editing"
                )
                return
        if base.superseded_by is not None and current.superseded_by != base.superseded_by:
            violation(
                f"record {current.id} was superseded_by {base.superseded_by} at merge base "
                f"{base_sha[:12]}… and is now superseded_by {current.superseded_by}; the single "
                "permitted change to an existing record is adding superseded_by"
            )
            return
