"""Run literal changed PR test files and the checked-in guards on the PR candidate."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

from scripts.ci.gate import event_tier

GUARDS = Path("scripts/ci/pr-affected-guards.txt")
DURATIONS = Path("scripts/ci/pytest-file-durations.json")
INFRA = {
    ".github/workflows/ci.yml",
    "pyproject.toml",
    "pytest.ini",
    ".pytest.ini",
    "tox.ini",
    "setup.cfg",
    "uv.lock",
    "requirements.txt",
    "requirements-lock.txt",
    ".python-version",
}
CAP_SECONDS = 600


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], check=True, capture_output=True, timeout=30).stdout


def safe_path(name: str) -> str:
    path = PurePosixPath(name)
    if (
        not name
        or path.is_absolute()
        or str(path) != name
        or ".." in path.parts
        or "::" in name
        or "\\" in name
        or any(unicodedata.category(c).startswith("C") or c in "\u2028\u2029" for c in name)
    ):
        raise ValueError("unsafe repository path")
    return name


def plan(base: str, candidate: str) -> dict:
    """Use only the original base-to-candidate diff, never a current branch tip."""
    entries = {}
    for row in git("ls-tree", "-rz", candidate, "--", "tests").split(b"\0"):
        if row:
            meta, name = row.decode("utf-8").split("\t", 1)
            entries[name] = meta.split()[0]
    changed = [
        safe_path(p.decode("utf-8"))
        for p in git("diff", "--no-renames", "--name-only", "-z", base, candidate, "--").split(b"\0")
        if p
    ]
    guards = [safe_path(line) for line in GUARDS.read_text(encoding="utf-8").splitlines()]
    if not guards or len(set(guards)) != len(guards):
        raise ValueError("empty or duplicate guard list")
    tests = sorted(p for p in changed if re.fullmatch(r"tests/(?:[^/]+/)*test_[^/]+\.py", p) and p in entries)
    for name in set(guards) | set(tests):
        if not re.fullmatch(r"tests/(?:[^/]+/)*test_[^/]+\.py", name) or entries.get(name) not in {"100644", "100755"}:
            raise ValueError("test is not a tracked regular file")
        path = Path(name)
        if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("missing test or symlinked test path")
    durations = json.loads(DURATIONS.read_text(encoding="utf-8"))
    if not isinstance(durations, dict):
        raise ValueError("invalid duration record")
    selected = sorted(set(guards) | set(tests))
    unknown = [p for p in selected if p not in durations]
    for p in selected:
        value = durations.get(p)
        if p not in unknown and (type(value) not in {int, float} or not math.isfinite(value) or value < 0):
            raise ValueError("invalid recorded duration")
    # Sum recorded serial times with a minute reserved for setup and collection.
    estimate = None if unknown else 60 + sum(durations[p] for p in selected)
    infrastructure = any(
        p in INFRA
        or Path(p).name == "conftest.py"
        or p.startswith(("scripts/ci/", "scripts/common/flake_quarantine", ".github/actions/python-ci-env/"))
        or p == "tests/flake_quarantine.yaml"
        for p in changed
    )
    reason = (
        "pytest infrastructure changed"
        if infrastructure
        else "recorded duration unknown"
        if unknown
        else "recorded estimate exceeds 600 second cap"
        if estimate > CAP_SECONDS
        else None
    )
    run = sorted(set(guards) if reason else set(selected))
    return {
        "candidate": candidate,
        "base": base,
        "guards": guards,
        "changed_test_files": tests,
        "run_files": run,
        "deferred_files": sorted(set(tests) - set(run)),
        "reason": reason,
        "estimate_seconds": estimate,
        "unknown_duration_files": unknown,
        "deleted_test_files": sorted(
            p for p in changed if p.startswith("tests/") and p.endswith(".py") and p not in entries
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run changed test files and fixed guards for a PR candidate.\n"
        "Use in PR admission; approved-head and merge-group full pytest remain required.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: .venv/bin/python -m scripts.ci.pr_affected_tests\n"
        "Inputs: EVENT_NAME, GITHUB_EVENT_PATH, GITHUB_SHA, GITHUB_REF.\n"
        "Outputs: ci-artifacts/pr-affected.json, pr-affected.xml and GITHUB_STEP_SUMMARY.\n"
        "Exit codes: 0 required execution passed; 1 invalid proof or failed execution; 2 invalid arguments.\n"
        "Related: scripts/ci/pr-affected-guards.txt; docs/runbooks/ci-gate.md.",
    )
    parser.parse_args()
    stage, reason = "event_identity", "invalid_event_or_candidate"
    try:
        actual = git("rev-parse", "HEAD").decode().strip()
        payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        event = os.environ["EVENT_NAME"]
        event_tier(event, payload, os.environ["GITHUB_SHA"], os.environ["GITHUB_REF"], actual)
        if event != "pull_request":
            print("Full tier: required full-suite jobs provide pytest proof.")
            return 0
        pr = payload["pull_request"]
        # GitHub checkout pins the event's test merge. Its first parent is the
        # tested base, even when event metadata or fetched branches have moved.
        stage, reason = "merge_parents", "unexpected_merge_or_head"
        parents = git("show", "-s", "--format=%P", actual).decode().split()
        if len(parents) != 2 or parents[1] != pr["head"]["sha"]:
            raise ValueError("PR merge candidate must have two parents and match event head")
        base = parents[0]
        stage, reason = "clean_checkout", "dirty_checkout"
        subprocess.run(["git", "diff", "--quiet", actual, "--"], check=True, capture_output=True, timeout=30)
        stage, reason = "test_plan", "invalid_paths_tests_or_durations"
        record = plan(base, actual)
        record["event_base"] = pr["base"]["sha"]
        stage, reason = "fresh_report", "stale_or_unwritable_report"
        output = Path("ci-artifacts")
        output.mkdir(exist_ok=True)
        junit = output / "pr-affected.xml"
        if junit.exists():
            raise ValueError("stale PR pytest report")
        record.update(exit_code=None, reported_cases=None, skipped_cases=None, failed_cases=None,
                      deferred_case_count=None, execution_status="incomplete")
        (output / "pr-affected.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        stage, reason = "pytest_execution", "execution_incomplete"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                *record["run_files"],
                "-n",
                "2",
                "--dist=worksteal",
                "--max-worker-restart=0",
                "--timeout=120",
                "--timeout-method=thread",
                "-m",
                "not atlas_release and not slow and not site_toolchain",
                "--strict-markers",
                "--junitxml=" + str(junit),
            ],
            check=False,
            timeout=480,
        )
        stage, reason = "pytest_report", "missing_or_invalid_junit"
        record["exit_code"] = result.returncode
        (output / "pr-affected.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        cases = list(ET.parse(junit).getroot().iter("testcase"))
        record.update(
            exit_code=result.returncode,
            reported_cases=len(cases),
            skipped_cases=sum(c.find("skipped") is not None for c in cases),
            failed_cases=sum(c.find("failure") is not None or c.find("error") is not None for c in cases),
            deferred_case_count=None,
            execution_status="completed",
        )
        stage, reason = "proof_output", "proof_output_incomplete"
        (output / "pr-affected.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        summary = (
            "PR admission: full pytest was not run.\n"
            f"Candidate: {actual}\nRequested files ({len(record['run_files'])}): "
            + ", ".join(record["run_files"])
            + "\n"
            + f"Reported cases: {len(cases)}; skipped: {record['skipped_cases']}; failed: {record['failed_cases']}; exit: {result.returncode}.\n"
            + f"Deferred changed files ({len(record['deferred_files'])}): "
            + (", ".join(record["deferred_files"]) or "none")
            + "\n"
            + f"Reason: {record['reason'] or 'none'}; deferred test-case count: UNKNOWN.\n"
            + f"Recorded estimate seconds: {record['estimate_seconds']}; unknown duration files: {len(record['unknown_duration_files'])}.\n"
            + f"Deleted test files: {len(record['deleted_test_files'])}. Approved-head and merge-group full pytest remain required.\n"
        )
        print(summary)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
                stream.write(summary)
        return int(result.returncode != 0 or not cases)
    except (KeyError, TypeError, ValueError, OSError, UnicodeError, ET.ParseError, subprocess.SubprocessError) as exc:
        detail = f": {exc}" if type(exc) is ValueError else ""
        print(f"::error::PR affected proof incomplete: stage={stage}; reason={reason}; error={type(exc).__name__}{detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
