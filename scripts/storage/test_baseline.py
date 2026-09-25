"""Capture and compare pytest test-ID baselines from CI JUnit XML.

Disposition files are JSON objects with optional ``renamed``, ``fixture``, and
``needs_artifact`` arrays. Jobs are informational: test IDs are compared across
the whole run. Pure passing additions are reported automatically. A rename's
new ID must pass. A skipped ID that now passes is reported as an improvement;
a passing ID that becomes skipped still needs a disposition. Host-run evidence is a JUnit path or a pytest -rA transcript
with an exact passing summary and the named ID in its PASSES section.
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


def nodeid_to_junit_id(nodeid: str) -> str:
    """Convert a collected pytest node ID to pytest's JUnit classname/name ID."""
    module, separator, node = nodeid.partition(".py::")
    if not separator or not module or not node:
        raise BaselineError(f"invalid pytest node ID: {nodeid}")
    bare, bracket, parameters = node.partition("[")
    parts = bare.split("::")
    classname = ".".join((module.replace("/", "."), *parts[:-1]))
    name = parts[-1] + ("[" + parameters if bracket else "")
    return f"{classname}::{name}"


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


def _by_id(baseline: dict[str, Any]) -> dict[str, tuple[str, str, str]]:
    result = {}
    for job, body in baseline["jobs"].items():
        for test_id, outcome in body["outcomes"].items():
            if test_id in result:
                raise BaselineError(f"duplicate test ID across jobs: {test_id}")
            result[test_id] = (outcome, job, body.get("skip_reasons", {}).get(test_id, ""))
    return result


def _host_passed(host_run: Any, test_id: str, repo_root: Path) -> bool:
    if isinstance(host_run, dict) and isinstance(host_run.get("junit"), str):
        report = Path(host_run["junit"])
        if not report.is_absolute():
            report = repo_root / report
        try:
            root = ET.parse(report).getroot()
            cases = list(_cases(root))
        except (OSError, ET.ParseError):
            return False
        return (
            bool(cases)
            and all(
                node.get("failures", "0") == "0" and node.get("errors", "0") == "0"
                for node in root.iter()
                if node.tag.rsplit("}", 1)[-1] in {"testsuite", "testsuites"}
            )
            and all(_outcome(case) == "passed" for case in cases)
            and any(_test_id(case) == test_id for case in cases)
        )
    if not isinstance(host_run, str):
        return False
    summaries = list(re.finditer(r"(?m)^=+\s*(.*?)\s+in\s+[^\n]+?=+\s*$", host_run))
    if len(summaries) != 1:
        return False
    counts = {}
    for part in summaries[0][1].split(", "):
        match = re.fullmatch(r"(\d+) (passed|failed|errors?|skipped|deselected|xfailed|xpassed|warnings?)", part)
        if not match:
            return False
        counts[match[2]] = int(match[1])
    if counts.get("passed", 0) < 1 or any(counts.get(name, 0) for name in ("failed", "error", "errors")):
        return False
    return any(line.strip() == f"PASSED {test_id}" for line in host_run.splitlines())


def _improvements(before: dict[str, tuple[str, str, str]], after: dict[str, tuple[str, str, str]]) -> list[str]:
    """Return IDs that were skipped before and pass now; they need no disposition."""
    return sorted(
        test_id
        for test_id, (outcome, _, _) in after.items()
        if outcome == "passed" and before.get(test_id, (None,))[0] == "skipped"
    )


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
    before, after = _by_id(old), _by_id(new)
    changes = {
        test_id
        for test_id in before.keys() | after.keys()
        if before.get(test_id, (None,))[0] != after.get(test_id, (None,))[0]
    }
    covered: set[str] = set()
    rename_nonpassed: set[str] = set()
    for row in _disposition_rows(dispositions, "renamed"):
        old_id, new_id = row.get("old"), row.get("new")
        if not all(isinstance(v, str) and v for v in (old_id, new_id)):
            errors.append("renamed disposition requires nonempty old and new fields")
            continue
        if old_id not in before or old_id in after or new_id not in after or new_id in before:
            errors.append(f"rename {old_id} -> {new_id} must be a paired removal and addition")
            continue
        covered.add(old_id)
        if after[new_id][0] == "passed":
            covered.add(new_id)
        else:
            rename_nonpassed.add(new_id)

    for key in ("fixture", "needs_artifact"):
        for row in _disposition_rows(dispositions, key):
            test_id = row.get("id")
            if not isinstance(test_id, str) or not test_id:
                errors.append(f"{key} disposition requires a nonempty id field")
                continue
            if test_id not in changes:
                errors.append(f"{key} disposition does not name a changed ID: {test_id}")
                continue
            new_outcome = after.get(test_id, (None,))[0]
            if key == "fixture":
                fixture = row.get("fixture")
                if new_outcome != "passed" or not isinstance(fixture, str) or not fixture:
                    errors.append(f"fixture disposition for {test_id} requires a fixture path and a passing CI outcome")
                elif not _fixture_is_committed(repo_root, fixture):
                    errors.append(f"fixture disposition for {test_id} names a fixture absent from HEAD: {fixture}")
                else:
                    covered.add(test_id)
            else:
                host_run = row.get("host_run")
                reason = after.get(test_id, (None, None, ""))[2]
                if (
                    new_outcome != "skipped"
                    or "needs_artifact:" not in reason
                    or not _host_passed(host_run, test_id, repo_root)
                ):
                    errors.append(
                        f"needs_artifact disposition for {test_id} requires a needs_artifact CI skip and structured passing host_run naming the exact ID"
                    )
                else:
                    covered.add(test_id)

    for test_id in sorted(rename_nonpassed - covered):
        errors.append(f"rename to {test_id} requires the new outcome passed or a corresponding disposition")

    covered.update(_improvements(before, after))
    for test_id in sorted(changes - covered):
        prior = before.get(test_id, (None,))[0]
        current = after.get(test_id, (None,))[0]
        if prior is None and current == "passed":
            continue
        errors.append(f"undisposed change {test_id}: {prior or 'absent'} -> {current or 'absent'}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture CI JUnit baselines and compare test IDs across jobs.\nUse at each migration phase; never infer missing CI outcomes from a local run.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.test_baseline capture --junit pytest.xml --job pytest-1 --source-sha abc123 --output baseline.json
  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.test_baseline compare --old old.json --new new.json --dispositions dispositions.json

Outputs: capture writes deterministic JSON with per-job IDs; compare reports passing additions
and skipped -> passed improvements (passed -> skipped still needs a disposition).
Exit codes: 0 means captured or every changed ID is disposed; 1 means invalid input or missing disposition.
Related: issue #8809, spec v3.3 sections 5 and 8.4.
Disposition JSON keys: renamed [{old,new}], fixture [{id,fixture}],
needs_artifact [{id,host_run}]. Jobs may be included for provenance.
host_run is a JUnit path object {junit:"path.xml"} or a pytest -rA transcript
with PASSED <exact ID> and a summary containing zero failures/errors.""",
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
        old_ids, new_ids = _by_id(old), _by_id(new)
        renamed = {row.get("new") for row in _disposition_rows(dispositions, "renamed")}
        additions = sorted(
            test_id
            for test_id in new_ids.keys() - old_ids.keys()
            if new_ids[test_id][0] == "passed" and test_id not in renamed
        )
        improvements = _improvements(old_ids, new_ids)
        print(f"baseline comparison passed: {len(additions)} passing addition(s), {len(improvements)} improvement(s)")
        for test_id in additions:
            print(f"ADDED passed {test_id} (job {new_ids[test_id][1]})")
        for test_id in improvements:
            print(f"IMPROVED skipped -> passed {test_id} (job {new_ids[test_id][1]})")
        return 0
    except BaselineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
