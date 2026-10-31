"""Run changed tests and guards, or mandatory marker-only repository invariants."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
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
TIMEOUT_SECONDS = 480
# Runner speed variance, measured from the committed record: across the recorded PR
# runs whose selection ran whole, the wall time reached at most 1.176 times the
# estimate (343.4 s estimated, 403.8 s wall), and an estimate of 464.9 s was killed
# at 480 s. The ratio rounds up to 1.18; the safe budget is the timeout divided by it.
VARIANCE_RATIO = 1.18
SAFE_SECONDS = math.floor(TIMEOUT_SECONDS / VARIANCE_RATIO)
BUDGET_REASON = "recorded estimate plus runner-variance margin exceeds 480 second pytest timeout"
GUARDS_REASON = "guards alone exceed the safe budget under the 480 second pytest timeout"
# Importing tests fill only half the room the guards and changed tests leave under
# the cap, and never past the pytest timeout: a selection estimated at the kill limit
# has no room for runner speed variance. Measured from the mandatory selection, not
# from zero, so a heavy guard list never starves every importing test.
FILL_SHARE = 0.5
TEST = re.compile(r"tests/(?:[^/]+/)*test_[^/]+\.py")


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


def importing_tests(targets: set[str], deleted: set[str], base: str, entries: dict[str, str]) -> list[str]:
    """Tests that directly import, load, read or run a changed file, by static scan.

    A test that loads a computed path also depends on every file under the
    directories its constants name (`components.directory_edges`).

    Direct edges only: the transitive closure spans most of the suite, which the
    merge group already runs. A deleted file has no edges in the candidate, so its
    surviving dependents come from a scan of the base tree.
    """
    from scripts.ci import components

    scan = components.scan_imports(components.python_sources(), set(components.tracked_paths()))
    edges, directories = scan["file_edges"], scan["directory_edges"]
    if deleted:
        tree = {}
        for row in git("ls-tree", "-rz", base).split(b"\0"):
            if row:
                meta, name = row.decode("utf-8").split("\t", 1)
                tree[name] = meta.split()
        blobs = tuple((name, meta[2]) for name, meta in tree.items() if name.endswith(".py") and meta[1] == "blob")
        sources = components.indexed_python_sources(str(components.ROOT), blobs, ())
        scan = components.scan_imports(sources, set(tree))
        edges = [*edges, *(edge for edge in scan["file_edges"] if edge[1] in deleted)]
        directories = [*directories, *scan["directory_edges"]]
    return sorted({
        importer for importer, target in edges
        if target in targets and TEST.fullmatch(importer) and entries.get(importer) in {"100644", "100755"}
    } | {
        importer for importer, directory in directories
        if any(target.startswith(directory + "/") for target in targets)
        and TEST.fullmatch(importer) and entries.get(importer) in {"100644", "100755"}
    })


def plan(base: str, candidate: str, *, importers: bool = True) -> dict:
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
    tests = sorted(p for p in changed if TEST.fullmatch(p) and p in entries)
    for name in set(guards) | set(tests):
        if not TEST.fullmatch(name) or entries.get(name) not in {"100644", "100755"}:
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
    # A file with no recorded time (new in this PR) is weighted like the median
    # recorded file, as split_tests does, and still runs. Dropping it here left
    # new tests unexecuted until merge-group CI.
    recorded = [v for v in durations.values() if type(v) in {int, float} and math.isfinite(v) and v >= 0]
    default = statistics.median(recorded) if recorded else 1.0
    # Sum serial times with a minute reserved for setup and collection.
    estimate = 60 + sum(durations.get(p, default) for p in selected)
    infrastructure = any(
        p in INFRA
        or Path(p).name == "conftest.py"
        or p.startswith(("scripts/ci/", "scripts/common/flake_quarantine", ".github/actions/python-ci-env/"))
        or p == "tests/flake_quarantine.yaml"
        for p in changed
    )
    guard_estimate = 60 + sum(durations.get(p, default) for p in guards)
    reason = (
        "pytest infrastructure changed"
        if infrastructure
        else "recorded estimate exceeds 600 second cap"
        if estimate > CAP_SECONDS
        else BUDGET_REASON
        if estimate > SAFE_SECONDS
        else None
    )
    run = set(guards) if reason else set(selected)
    if reason == BUDGET_REASON:
        # Over the safe budget: changed tests fill what the guards leave, cheapest
        # first, so the same rule bounds the mandatory selection and the importers.
        used = guard_estimate
        for p in sorted(set(tests) - set(guards), key=lambda p: (durations.get(p, default), p)):
            if used + durations.get(p, default) <= SAFE_SECONDS:
                run.add(p)
                used += durations.get(p, default)
    # Tests for changed code fill the fill budget, cheapest first; the
    # rest defer to merge-group pytest. Infrastructure changes run guards only.
    sources = {p for p in changed if not TEST.fullmatch(p)}
    deleted = {
        safe_path(p.decode("utf-8"))
        for p in git("diff", "--no-renames", "--diff-filter=D", "--name-only", "-z", base, candidate, "--").split(b"\0")
        if p
    } & sources
    imported = (
        [p for p in importing_tests(sources, deleted, base, entries) if p not in run]
        if importers and sources and not reason
        else []
    )
    unknown += [p for p in imported if p not in durations]
    for p in imported:
        value = durations.get(p, default)
        if type(value) not in {int, float} or not math.isfinite(value) or value < 0:
            raise ValueError("invalid recorded duration")
    budget = estimate
    fill_limit = min(estimate + (CAP_SECONDS - estimate) * FILL_SHARE, SAFE_SECONDS)
    for p in sorted(imported, key=lambda p: (durations.get(p, default), p)):
        if budget + durations.get(p, default) <= fill_limit:
            run.add(p)
            budget += durations.get(p, default)
    if set(imported) - run:
        reason = BUDGET_REASON if fill_limit == SAFE_SECONDS else "recorded estimate exceeds 600 second cap"
    run = sorted(run)
    return {
        "candidate": candidate,
        "base": base,
        "guards": guards,
        "changed_test_files": tests,
        "importing_test_files": imported,
        "run_files": run,
        "deferred_files": sorted((set(tests) | set(imported)) - set(run)),
        "reason": reason,
        "estimate_seconds": budget,
        "safe_budget_seconds": SAFE_SECONDS,
        "guards_exceed_safe_budget": guard_estimate > SAFE_SECONDS,
        "unknown_duration_files": unknown,
        "deleted_test_files": sorted(
            p for p in changed if p.startswith("tests/") and p.endswith(".py") and p not in entries
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run changed tests, tests that import changed files and guards, or marker-only\n"
        "repository invariants for a PR candidate. PR CI runs no pytest shards; merge-group CI runs the full suite.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: .venv/bin/python -m scripts.ci.pr_affected_tests\n"
        "Inputs: EVENT_NAME, GITHUB_EVENT_PATH, GITHUB_SHA, GITHUB_REF.\n"
        "Outputs: ci-artifacts/pr-affected.* or pr-repo-wide.* and GITHUB_STEP_SUMMARY.\n"
        "Exit codes: 0 required execution passed; 1 invalid proof or failed execution; 2 invalid arguments.\n"
        "Related: scripts/ci/pr-affected-guards.txt; docs/runbooks/ci-gate.md.",
    )
    parser.add_argument("--repo-wide", action="store_true", help="Run only repo_wide marked tests, independent of changed-file deferral.")
    args = parser.parse_args()
    stage, reason = "event_identity", "invalid_event_or_candidate"
    try:
        actual = git("rev-parse", "HEAD").decode().strip()
        payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        tier = event_tier(os.environ["EVENT_NAME"], payload, os.environ["GITHUB_SHA"], os.environ["GITHUB_REF"], actual)
        if tier != "admission":
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
        record = plan(base, actual, importers=not args.repo_wide)
        record["event_base"] = pr["base"]["sha"]
        marker = "not atlas_release and not slow and not site_toolchain"
        if args.repo_wide:
            # Keep nightly, release and frontend tests in their existing tiers.
            marker = "repo_wide and " + marker
        paths = ["tests"] if args.repo_wide else record["run_files"]
        # pytest excludes build/ by default; it contains registered invariants.
        collection = ["--override-ini=norecursedirs=.* node_modules"] if args.repo_wide else []
        timeout = 1500 if args.repo_wide else TIMEOUT_SECONDS
        record.update(selection=marker, requested_paths=paths, workers=2, timeout_seconds=timeout,
                      logical_cpus=os.cpu_count(), load_average=os.getloadavg())
        stage, reason = "fresh_report", "stale_or_unwritable_report"
        output = Path("ci-artifacts")
        output.mkdir(exist_ok=True)
        stem = "pr-repo-wide" if args.repo_wide else "pr-affected"
        junit = output / f"{stem}.xml"
        report = output / f"{stem}.json"
        if junit.exists():
            raise ValueError("stale PR pytest report")
        record.update(exit_code=None, reported_cases=None, skipped_cases=None, failed_cases=None,
                      deferred_case_count=None, execution_status="incomplete")
        report.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        if record["guards_exceed_safe_budget"] and not args.repo_wide:
            # Running them would end in the kill with no failed test; say so instead.
            stage, reason = "safe_budget", "guards_exceed_safe_budget"
            record["execution_status"] = "not_run_guards_exceed_safe_budget"
            report.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            raise ValueError(GUARDS_REASON + f" ({SAFE_SECONDS} s); refresh {DURATIONS} or trim the guard list")
        stage, reason = "pytest_execution", "execution_incomplete"
        started = time.monotonic()
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                *paths,
                *collection,
                "-n",
                "2",
                "--dist=worksteal",
                "--max-worker-restart=0",
                "--timeout=120",
                "--timeout-method=thread",
                "-m",
                marker,
                "--strict-markers",
                "--durations=25",
                "--junitxml=" + str(junit),
            ],
            check=False,
            timeout=timeout,
        )
        record["wall_seconds"] = round(time.monotonic() - started, 3)
        stage, reason = "pytest_report", "missing_or_invalid_junit"
        record["exit_code"] = result.returncode
        report.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
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
        report.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        summary = (
            "PR changed tests and guards: the full pytest suite runs in merge-group CI.\n"
            f"Candidate: {actual}\nMarker selection: {marker}\nRequested paths ({len(paths)}): "
            + ", ".join(paths)
            + "\n"
            + f"Wall seconds: {record['wall_seconds']}; workers: 2; subprocess timeout: {timeout}s.\n"
            + f"Reported cases: {len(cases)}; skipped: {record['skipped_cases']}; failed: {record['failed_cases']}; exit: {result.returncode}.\n"
            + f"Deferred changed files ({len(record['deferred_files'])}): "
            + (", ".join(record["deferred_files"]) or "none")
            + "\n"
            + f"Reason: {record['reason'] or 'none'}; deferred test-case count: UNKNOWN.\n"
            + f"Recorded estimate seconds: {record['estimate_seconds']}; unknown duration files: {len(record['unknown_duration_files'])}.\n"
            + f"Deleted test files: {len(record['deleted_test_files'])}. Full merge-group pytest remains required.\n"
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
