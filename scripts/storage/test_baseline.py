"""Capture and compare pytest test-ID baselines from CI JUnit XML.

Disposition files are JSON objects with optional ``renamed``, ``fixture``, and
``needs_artifact`` arrays. A rename row is ``{"job": "...", "old": "...",
"new": "..."}``; fixture rows require ``job``, ``id`` and ``fixture`` (a
committed fixture path); needs-artifact rows require ``job``, ``id`` and a
quoted ``host_run`` command/result. Every renamed ID must disappear/appear in
the stated job. Fixture IDs must pass in the new baseline. needs_artifact IDs
must be skipped in CI and carry a nonempty host-run quotation.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from pathlib import Path
from typing import Any

OUTCOMES = {"passed", "skipped", "failed", "error"}
_OUTCOME_CODE = {"passed": 0, "skipped": 1, "failed": 2, "error": 3}
_CODE_OUTCOME = {code: outcome for outcome, code in _OUTCOME_CODE.items()}


class BaselineError(ValueError):
    """Invalid baseline input or an undisposed test-ID change."""


def _test_id(case: ET.Element) -> str:
    name = case.get("name", "")
    classname = case.get("classname", "")
    if not name:
        raise BaselineError("JUnit testcase has no name")
    return f"{classname}::{name}" if classname else name


def _outcome(case: ET.Element) -> str:
    tags = {child.tag.rsplit("}", 1)[-1] for child in case}
    if "error" in tags:
        return "error"
    if "failure" in tags:
        return "failed"
    if "skipped" in tags:
        return "skipped"
    return "passed"


def _cases(root: ET.Element) -> Iterable[ET.Element]:
    tag = root.tag.rsplit("}", 1)[-1]
    if tag == "testcase":
        yield root
    else:
        yield from root.iter("testcase")


def capture_junit(
    inputs: list[tuple[str, Path]],
    *,
    source_sha: str | None = None,
    source_run: str | None = None,
    source_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    """Return a deterministic, per-job baseline for JUnit XML files."""
    jobs: dict[str, dict[str, Any]] = {}
    for job, path in inputs:
        if job in jobs:
            raise BaselineError(f"duplicate job name: {job}")
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError) as exc:
            raise BaselineError(f"cannot read JUnit XML {path}: {exc}") from exc
        outcomes: dict[str, str] = {}
        skip_reasons: dict[str, str] = {}
        for case in _cases(root):
            test_id = _test_id(case)
            if test_id in outcomes:
                raise BaselineError(f"duplicate test ID in {job}: {test_id}")
            outcomes[test_id] = _outcome(case)
            skipped = case.find("skipped")
            if skipped is not None:
                skip_reasons[test_id] = (skipped.get("message", "") + " " + (skipped.text or "")).strip()
        jobs[job] = {
            "collected": len(outcomes),
            "outcomes": dict(sorted(outcomes.items())),
            "skip_reasons": dict(sorted(skip_reasons.items())),
        }
    if not jobs:
        raise BaselineError("at least one JUnit input is required")
    result: dict[str, Any] = {"schema_version": 1, "jobs": dict(sorted(jobs.items()))}
    if source_sha:
        result["source_sha"] = source_sha
    if source_run:
        result["source_run"] = source_run
    if source_artifacts:
        result["source_artifacts"] = source_artifacts
    return result


def _load_baseline(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"cannot read baseline {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("jobs"), dict):
        raise BaselineError(f"invalid baseline structure in {path}; expected a jobs object")
    if value.get("schema_version") == 2:
        return _unpack_baseline(value)
    return value


def _pack_baseline(baseline: dict[str, Any]) -> dict[str, Any]:
    """Losslessly prefix-pack sorted IDs so the complete CI baseline stays reviewable in Git."""
    jobs = {}
    for job, body in baseline["jobs"].items():
        classes: dict[str, list[tuple[str, str]]] = {}
        for test_id, outcome in body["outcomes"].items():
            classname, separator, name = test_id.rpartition("::")
            classes.setdefault(classname if separator else "", []).append((name if separator else test_id, outcome))
        packed = {}
        for classname, items in sorted(classes.items()):
            previous = ""
            rows = []
            for name, outcome in sorted(items):
                prefix = len(os.path.commonprefix((previous, name)))
                rows.append([prefix, name[prefix:], _OUTCOME_CODE[outcome]])
                previous = name
            packed[classname] = rows
        jobs[job] = {
            "collected": body["collected"],
            "cases": packed,
            "skip_reasons": body.get("skip_reasons", {}),
        }
    return {**baseline, "schema_version": 2, "jobs": jobs}


def _unpack_baseline(packed: dict[str, Any]) -> dict[str, Any]:
    jobs = {}
    for job, body in packed["jobs"].items():
        outcomes: dict[str, str] = {}
        for classname, rows in body["cases"].items():
            previous = ""
            for prefix, suffix, code in rows:
                if not isinstance(prefix, int) or prefix < 0 or prefix > len(previous) or code not in _CODE_OUTCOME:
                    raise BaselineError(f"invalid packed test ID in job {job}")
                name = previous[:prefix] + suffix
                test_id = f"{classname}::{name}" if classname else name
                if test_id in outcomes:
                    raise BaselineError(f"duplicate packed test ID in job {job}")
                outcomes[test_id] = _CODE_OUTCOME[code]
                previous = name
        if len(outcomes) != body["collected"]:
            raise BaselineError(f"packed baseline count mismatch in job {job}")
        jobs[job] = {
            "collected": body["collected"],
            "outcomes": dict(sorted(outcomes.items())),
            "skip_reasons": body.get("skip_reasons", {}),
        }
    return {**packed, "schema_version": 1, "jobs": jobs}


def _safe_json(value: dict[str, Any]) -> str:
    """Preserve exact synthetic IDs while avoiding raw secret-pattern text in Git."""
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"))
    raw = re.sub(r"-{5}BEGIN [A-Z0-9 ]+PRIVATE KEY-{5}", lambda match: r"\u002d" + match.group()[1:], raw)

    def escape_private_ip(match: re.Match[str]) -> str:
        candidate = match.group()
        try:
            private = ipaddress.ip_address(candidate).is_private
        except ValueError:
            return candidate
        return candidate.replace(".", r"\u002e", 1) if private else candidate

    raw = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", escape_private_ip, raw)
    return raw + "\n"


def _disposition_rows(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    rows = data.get(key, [])
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise BaselineError(f"dispositions.{key} must be an array of objects")
    return rows


def _fixture_is_committed(repo_root: Path, fixture: str) -> bool:
    path = Path(fixture)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        return False
    try:
        subprocess.run(
            ["git", "cat-file", "-e", f"HEAD:{path.as_posix()}"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return True


def compare_baselines(
    old: dict[str, Any],
    new: dict[str, Any],
    dispositions: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> list[str]:
    """Validate every added, removed, or outcome-changed test ID."""
    errors: list[str] = []
    repo_root = (repo_root or Path.cwd()).resolve()
    old_jobs, new_jobs = old["jobs"], new["jobs"]
    changes: set[tuple[str, str, str | None, str | None]] = set()
    for job in sorted(set(old_jobs) | set(new_jobs)):
        before = old_jobs.get(job, {}).get("outcomes", {})
        after = new_jobs.get(job, {}).get("outcomes", {})
        for test_id in sorted(set(before) | set(after)):
            old_outcome, new_outcome = before.get(test_id), after.get(test_id)
            if old_outcome != new_outcome:
                changes.add((job, test_id, old_outcome, new_outcome))

    covered: set[tuple[str, str, str | None, str | None]] = set()
    renamed_old: set[tuple[str, str]] = set()
    renamed_new: set[tuple[str, str]] = set()
    for row in _disposition_rows(dispositions, "renamed"):
        job, old_id, new_id = row.get("job"), row.get("old"), row.get("new")
        if not all(isinstance(v, str) and v for v in (job, old_id, new_id)):
            errors.append("renamed disposition requires nonempty job, old, and new fields")
            continue
        old_outcome = old_jobs.get(job, {}).get("outcomes", {}).get(old_id)
        new_outcome = new_jobs.get(job, {}).get("outcomes", {}).get(new_id)
        if old_outcome is None or new_outcome is None:
            errors.append(f"rename {job}: {old_id} -> {new_id} must exist in old/new baseline respectively")
            continue
        renamed_old.add((job, old_id))
        renamed_new.add((job, new_id))
        covered.add((job, old_id, old_outcome, None))
        covered.add((job, new_id, None, new_outcome))

    for key in ("fixture", "needs_artifact"):
        for row in _disposition_rows(dispositions, key):
            job, test_id = row.get("job"), row.get("id")
            if not isinstance(job, str) or not isinstance(test_id, str) or not job or not test_id:
                errors.append(f"{key} disposition requires nonempty job and id fields")
                continue
            change = next((c for c in changes if c[:2] == (job, test_id)), None)
            if change is None:
                errors.append(f"{key} disposition does not name a changed ID: {job}::{test_id}")
                continue
            new_outcome = change[3]
            if key == "fixture":
                fixture = row.get("fixture")
                if new_outcome != "passed" or not isinstance(fixture, str) or not fixture:
                    errors.append(
                        f"fixture disposition for {job}::{test_id} requires a fixture path and a passing CI outcome"
                    )
                elif not _fixture_is_committed(repo_root, fixture):
                    errors.append(
                        f"fixture disposition for {job}::{test_id} names a fixture absent from HEAD: {fixture}"
                    )
            else:
                host_run = row.get("host_run")
                has_test_id = isinstance(host_run, str) and test_id in host_run
                passed_host_run = isinstance(host_run, str) and "passed" in host_run.casefold()
                reason = new_jobs.get(job, {}).get("skip_reasons", {}).get(test_id, "")
                if (
                    new_outcome != "skipped"
                    or "needs_artifact:" not in reason
                    or not has_test_id
                    or not passed_host_run
                ):
                    errors.append(
                        f"needs_artifact disposition for {job}::{test_id} requires a needs_artifact CI skip and quoted passing host_run naming the exact ID"
                    )
            covered.add(change)

    # A rename is only valid as a paired removal and addition. Both are represented
    # in changes; unchanged IDs cannot be consumed as either side of the mapping.
    for job, test_id in renamed_old:
        change = next((c for c in changes if c[:2] == (job, test_id)), None)
        if change is None or change[3] is not None:
            errors.append(f"renamed old ID is not removed: {job}::{test_id}")
    for job, test_id in renamed_new:
        change = next((c for c in changes if c[:2] == (job, test_id)), None)
        if change is None or change[2] is not None:
            errors.append(f"renamed new ID is not newly collected: {job}::{test_id}")

    for change in sorted(changes):
        if change not in covered:
            job, test_id, before, after = change
            errors.append(f"undisposed change {job}::{test_id}: {before or 'absent'} -> {after or 'absent'}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture and compare per-job CI pytest test-ID baselines from JUnit XML.\nUse at each migration phase; never infer missing CI outcomes from a local run.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.test_baseline capture --junit pytest.xml --job pytest-1 --source-sha abc123 --output baseline.json
  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.test_baseline compare --old old.json --new new.json --dispositions dispositions.json

Outputs: capture writes deterministic JSON with per-job collected IDs and outcomes.
Exit codes: 0 means captured or every changed ID is disposed; 1 means invalid input or missing disposition.
Related: issue #8809, spec v3.3 sections 5 and 8.4.
Disposition JSON keys: renamed [{job,old,new}], fixture [{job,id,fixture}],
needs_artifact [{job,id,host_run}].""",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("capture", help="capture collected IDs and outcomes from JUnit XML")
    capture.add_argument("--junit", action="append", type=Path, required=True, help="JUnit XML file (repeatable)")
    capture.add_argument("--job", action="append", required=True, help="job name paired by order with each --junit")
    capture.add_argument("--source-sha", help="CI source commit SHA, if known")
    capture.add_argument("--source-run", help="CI run ID, if known")
    capture.add_argument("--source-artifact", action="append", help="downloaded Actions artifact name (repeatable)")
    capture.add_argument("--output", type=Path, required=True, help="output JSON baseline path")
    compare = sub.add_parser("compare", help="enforce explicit dispositions for every changed test ID")
    compare.add_argument("--old", type=Path, required=True, help="previous phase baseline")
    compare.add_argument("--new", type=Path, required=True, help="current phase baseline")
    compare.add_argument("--dispositions", type=Path, required=True, help="JSON disposition file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "capture":
            if len(args.junit) != len(args.job):
                raise BaselineError("provide exactly one --job for each --junit, in matching order")
            baseline = capture_junit(
                list(zip(args.job, args.junit, strict=True)),
                source_sha=args.source_sha,
                source_run=args.source_run,
                source_artifacts=args.source_artifact,
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(_safe_json(_pack_baseline(baseline)), encoding="utf-8")
            print(
                f"captured {sum(job['collected'] for job in baseline['jobs'].values())} test IDs across {len(baseline['jobs'])} jobs to {args.output}"
            )
            return 0
        old, new = _load_baseline(args.old), _load_baseline(args.new)
        try:
            dispositions = json.loads(args.dispositions.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BaselineError(f"cannot read dispositions {args.dispositions}: {exc}") from exc
        if not isinstance(dispositions, dict):
            raise BaselineError("disposition file must be a JSON object")
        errors = compare_baselines(old, new, dispositions, repo_root=Path.cwd())
        if errors:
            print("baseline comparison failed:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print("baseline comparison passed: every changed ID has a valid disposition")
        return 0
    except BaselineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
